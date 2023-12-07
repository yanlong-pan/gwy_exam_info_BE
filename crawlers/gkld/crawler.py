from datetime import datetime
from bs4 import BeautifulSoup
import dateparser
from functools import partial
import os
import re
import time
from typing import List
from dotenv import load_dotenv
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from dateutil.relativedelta import relativedelta
from search_engine.meilisearch.articles import article_manager 
from utilities import constant, fileIO, flow

def _create_chrome_web_driver(headless: bool = False):
    chrome_options = Options()
    if headless.lower() == "true":
        chrome_options.add_argument('--headless')  # 启用headless模式

    # 创建Chrome WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def process_province_page(driver: webdriver.Chrome, province_name, exam_type, info_type, page_num, start_dt: datetime, end_dt: datetime):
    #  Jump to specific page number
    url = driver.current_url.split('?')[0] + f'?page={page_num}'
    driver.execute_script(f"window.open('{url}');")
    province_page_with_pagination = flow.switch_to_lastest_window(driver)
    
    def get_article_title(driver: webdriver.Chrome):
        h1_element = driver.find_element(By.XPATH, './/div[@class="article-title"]/h1')
        # 使用BeautifulSoup解析<h1>元素的HTML内容
        soup = BeautifulSoup(h1_element.get_attribute("outerHTML"), "html.parser")
        # 剔除<a>元素内的文本内容
        for a in soup.find_all("a"):
            a.extract()
        # 获取<h1>元素的纯文本内容并输出
        return soup.get_text().strip()
    
    def is_date_invalid(e: WebElement, start: datetime, end: datetime):
        date_str = e.find_element(By.XPATH, './/time').text
        date_time: datetime = dateparser.parse(date_str) if '前' in date_str else datetime.strptime(date_str, constant.HYPHEN_JOINED_DATE_FORMAT)
        # 统一时区再比较。若datetime对象未设置Timezone，调用astimezone方法默认会先转换本地时区
        return not start.astimezone(pytz.utc) <= date_time.astimezone(pytz.utc) <= end.astimezone(pytz.utc)
       
    @flow.iterate_over_web_elements(
        driver = driver,
        selector_value = '.notice-list li',
        stop = partial(is_date_invalid, start=start_dt, end=end_dt)
    )
    @flow.operate_in_new_window(
        driver = driver,
        initial_page = province_page_with_pagination,
    )
    def save_notices():
        date = driver.find_element(By.CLASS_NAME, 'date').get_attribute('innerHTML')
        match = re.search(constant.HYPHEN_JOINED_DATE_REGEX, date)
        date = match.group().replace('-', '_') if match else 'unknown_date'

        article: WebElement = driver.find_element(By.CLASS_NAME, 'article-detail')
        download_dir = os.getenv('DOWNLOAD_ARTICLES_DIR', './articles') + f'/{province_name}/{exam_type}/{info_type}/{date}'
        file_name = (get_article_title(driver) + '.html').replace('/', '|')
        try:
            attachments = map(
                lambda e: (e.get_attribute('href'), e.text), 
                article.find_elements(
                    By.XPATH, 
                    './/a[contains(@href, "file") or contains(@href, "attach")][string-length(normalize-space(text())) > 0][@target="_blank"]'
                )
            )
            mapping = {}
            for (download_url, attachment_name) in attachments:
                fileIO.download_file_from_url(download_url, download_dir, attachment_name)
                if file_name not in mapping:
                    mapping[file_name] = []
                mapping[file_name].append(attachment_name)
            if mapping:
                fileIO.add_mapping_between_attachments_and_article(download_dir, mapping)
        finally:
            content = article.get_attribute('innerHTML')
            fileIO.write_content_to_file(download_dir, file_name, content)

    save_notices()
    # 关闭省份页面
    if driver.current_window_handle == province_page_with_pagination:
        driver.close()

def scrape_website():
    driver = _create_chrome_web_driver(headless=os.getenv('HEADLESS_MODE'))

    def _click_checkbox(text, checked=False, interval=3):
        i_class = 'icon-oncheck' if checked else 'icon-check'
        driver.find_element(By.XPATH, f'//i[contains(@class, "{i_class}")]/following-sibling::a[contains(text(), "{text}")]').click()
        time.sleep(interval)
    
    try:
        driver.get('https://www.gongkaoleida.com/')
        homepage = driver.current_window_handle

        # Iterate over all the provinces
        @flow.iterate_over_web_elements(
            driver = driver,
            selector_value = '.province-name'
        )
        def iterate_over_all_provinces(web_element: WebElement):
            province_name = web_element.text
            web_element.click()

            # switch to the province detail page
            province_page = flow.switch_to_lastest_window(driver)
            
            info_types: List[str] = driver.find_element(By.XPATH, '//dt[contains(text(),"资讯类型")]/following-sibling::dd/ul').text.split()
            num_of_info_types = len(info_types)
            exam_types: List[str] = driver.find_element(By.XPATH, '//dt[contains(text(),"考试类型")]/following-sibling::dd/ul').text.split()
            num_of_exam_types = len(exam_types)

            for a_i in range(num_of_info_types):
                _click_checkbox(info_types[a_i])
                if a_i > 0:
                    _click_checkbox(exam_types[-1], checked=True)
                    _click_checkbox(info_types[a_i-1], checked=True)

                for i in range(num_of_exam_types):
                    end_dt: datetime = datetime.utcnow()
                    filters={
                        'province': province_name,
                        'exam_type': exam_types[i],
                        'info_type': info_types[a_i],
                    }
                    start_dt: datetime = article_manager.get_max_collect_date(filters) or end_dt - relativedelta(months=1)
                    _click_checkbox(exam_types[i])
                    
                    if i > 0:
                        _click_checkbox(exam_types[i-1], checked=True)

                    # Get the total number of pages
                    try:
                        totalPages = int(driver.find_element(By.XPATH, '//li[a[text()="下一页"]]/preceding-sibling::li[1]').text)
                    except NoSuchElementException:
                        totalPages = 1
                    if os.getenv('RUNNING_ENV') == constant.TEST_ENV:
                        totalPages = min(totalPages, 2)
                    # 处理每个分页
                    for j in range(1, totalPages + 1):
                        process_province_page(driver, province_name, exam_types[i], info_types[a_i], j, start_dt, end_dt)
                        driver.switch_to.window(province_page)
                    
            # 关闭新窗口并切换回原始窗口
            driver.close()
            driver.switch_to.window(homepage)
        
        iterate_over_all_provinces()

    finally:
        driver.quit()

if __name__ == "__main__":
    load_dotenv()
    scrape_website()