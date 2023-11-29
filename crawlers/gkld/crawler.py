import datetime
import dateparser
from functools import partial
import os
import re
import time
from typing import List
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from dateutil.relativedelta import relativedelta 
from utilities import constant, fileIO, flow, timeutil

def process_province_page(driver: webdriver.Chrome, province_name, exam_type, article_type, page_num, start_date: datetime.date, end_date: datetime.date):
    #  Jump to specific page number
    url = driver.current_url.split('?')[0] + f'?page={page_num}'
    driver.execute_script(f"window.open('{url}');")
    province_page_with_pagination = flow.switch_to_lastest_window(driver)
    
    def is_date_invalid(e: WebElement, start_date: datetime.date, end_date: datetime.date):
        date_str = e.find_element(By.XPATH, './/time').text
        # convert human read time to datetime string
        if '前' in date_str:
            date_str = dateparser.parse(date_str).strftime(constant.HYPHEN_JOINED_DATE_FORMAT)
        return not timeutil.is_date_within_range(date_str, start_date, end_date)

    @flow.iterate_over_web_elements(
        driver = driver,
        selector_value = '.notice-list li',
        stop = partial(is_date_invalid, start_date=start_date, end_date=end_date)
    )
    @flow.operate_in_new_window(
        driver = driver,
        initial_page = province_page_with_pagination,
    )
    def save_notices():
        date = driver.find_element(By.CLASS_NAME, 'date').get_attribute('innerHTML')
        match = re.search(constant.HYPHEN_JOINED_DATE_REGEX, date)
        date = match.group().replace('-', '_') if match else 'unknown_date'

        content = driver.find_element(By.CLASS_NAME, 'article-detail').get_attribute('innerHTML')
        download_dir = os.getenv('DOWNLOAD_ARTICLES_DIR', './articles')
        fileIO.write_content_to_file(f'{download_dir}/{province_name}/{exam_type}/{article_type}/{date}', f'{driver.title}.html', content)

    save_notices()
    # 关闭省份页面 
    driver.close()

def scrape_website():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)

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
            
            article_types: List[str] = driver.find_element(By.XPATH, '//dt[contains(text(),"资讯类型")]/following-sibling::dd/ul').text.split()
            num_of_article_types = len(article_types)
            exam_types: List[str] = driver.find_element(By.XPATH, '//dt[contains(text(),"考试类型")]/following-sibling::dd/ul').text.split()
            num_of_exam_types = len(exam_types)

            for a_i in range(num_of_article_types):
                _click_checkbox(article_types[a_i])
                if a_i > 0:
                    _click_checkbox(exam_types[-1], checked=True)
                    _click_checkbox(article_types[a_i-1], checked=True)

                for i in range(num_of_exam_types):
                    download_dir = os.path.join(os.getenv('DOWNLOAD_ARTICLES_DIR'), f'./{province_name}/{exam_types[i]}/{article_types[a_i]}')
                    fileIO.make_dir_if_not_exists(download_dir)
                    subdirectories = fileIO.get_subdirectories(depth=2, path=download_dir)
                    end_date: datetime.date = timeutil.get_current_date_in_timezone()
                    start_date: datetime.date= timeutil.extract_max_date(subdirectories) or end_date - relativedelta(months=1)
                    _click_checkbox(exam_types[i])
                    
                    if i > 0:
                        _click_checkbox(exam_types[i-1], checked=True)

                    # Get the total number of pages
                    try:
                        totalPages = int(driver.find_element(By.XPATH, '//li[a[text()="下一页"]]/preceding-sibling::li[1]').text)
                    except NoSuchElementException:
                        totalPages = 1
                    if os.environ.get('RUNNING_ENV') == constant.TEST_ENV:
                        totalPages = min(totalPages, 2)
                    # 处理每个分页
                    for j in range(1, totalPages + 1):
                        process_province_page(driver, province_name, exam_types[i], article_types[a_i], j, start_date, end_date)
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