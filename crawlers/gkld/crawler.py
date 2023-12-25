from datetime import datetime
import uuid
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
from search_engine.meilisearch.articles import Article, article_manager
from utilities import constant, flow, timeutil

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
    
    def is_date_invalid(e: WebElement, start_dt: datetime, end_dt: datetime):
        date_str = e.find_element(By.XPATH, './/time').text
        date_time: datetime = dateparser.parse(date_str) if '前' in date_str else datetime.strptime(date_str, constant.HYPHEN_JOINED_DATE_FORMAT)
        # 检查
        if start_dt.tzinfo.zone == end_dt.tzinfo.zone == timeutil.get_tz().zone:
            is_within_range = start_dt <= timeutil.localize_native_dt(date_time)<= end_dt
            return not is_within_range
        else:
            raise Exception('Inconsistent TZ')

    @flow.iterate_over_web_elements(
        driver = driver,
        selector_value = '.notice-list li',
        stop = partial(is_date_invalid, start_dt=start_dt, end_dt=end_dt)
    )
    @flow.operate_in_new_window(
        driver = driver,
        initial_page = province_page_with_pagination,
    )
    def save_notices():
        date = driver.find_element(By.CLASS_NAME, 'date').get_attribute('innerHTML')
        match = re.search(constant.HYPHEN_JOINED_DATE_REGEX, date)
        date: str = match.group()
        apply_deadline = None
        # extract application deadline if possible
        try:
            job_info = driver.find_element(By.XPATH, '//div[@class="jobinfo-list"]//li[contains(., "报名时间")]')
            apply_dt = timeutil.extract_dates(job_info.text)
            apply_deadline = apply_dt['end_time']
        except:
            pass
        # extract main body
        article: WebElement = driver.find_element(By.XPATH, '//div[@class="article-detail"]/article')
        article_title = get_article_title(driver).replace('/', '|')
        if article_manager.index.get_documents({'filter': [f'title="{article_title}"']}).total == 0:
            # TODO: replace attachments' link
            content = article.get_attribute('innerHTML')
            soup = BeautifulSoup(content, 'html.parser')

            # 找到包含 "公考雷达" 字样的p元素并移除
            elements_to_remove = soup.find_all(lambda tag: '公考雷达' in tag.text)
            for element in elements_to_remove:
                element.extract()

            content = str(soup)

            article_manager.index.add_documents(documents=[{**Article(
                id=str(uuid.uuid4()),
                title=article_title,
                province=province_name,
                exam_type=exam_type,
                info_type=info_type,
                # set the parsed time to local timezone and then convert it to UTC timestamp
                collect_date=timeutil.local_dt_str_to_utc_ts(date),
                apply_deadline=apply_deadline,
                html_content=content
            ).model_dump()}])
            
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
        end_dt: datetime = timeutil.localize_native_dt(datetime.now())

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