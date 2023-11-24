import os
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from utilities import constant, fileIO, flow

def process_province_page(driver: webdriver.Chrome, province_name, page_num):
    #  Jump to specific page number
    url = driver.current_url.split('?')[0] + f'?page={page_num}'
    driver.execute_script(f"window.open('{url}');")
    province_page_with_pagination = flow.switch_to_lastest_window(driver)

    @flow.iterate_over_web_elements(
        driver = driver,
        selector_value = '.notice-list li a'
    )
    @flow.operate_in_new_window(
        driver = driver,
        initial_page = province_page_with_pagination,
    )
    def save_notices():
        date = driver.find_element(By.CLASS_NAME, 'date').get_attribute('innerHTML')
        pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(pattern, date)
        date = match.group().replace('-', '_') if match else 'unknown_date'

        content = driver.find_element(By.CLASS_NAME, 'article-detail').get_attribute('innerHTML')
        download_dir = os.getenv('DOWNLOAD_ARTICLES_DIR', './articles')
        fileIO.write_content_to_file(f'{download_dir}/{province_name}/{date}', f'{driver.title}.html', content)

    save_notices()
    # 关闭省份页面 
    driver.close()

def scrape_website():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)

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

            # 点击“公务员”前的icon-check
            driver.find_element(By.XPATH, '//i[contains(@class, "icon-check")]/following-sibling::a[contains(text(), "公务员")]').click()

            # Get the total number of pages
            totalPages = int(driver.find_element(By.XPATH, '//li[a[text()="下一页"]]/preceding-sibling::li[1]').text)
            if os.environ.get('RUNNING_ENV') == constant.TEST_ENV:
                totalPages = min(totalPages, 2)
            # 处理每个分页
            for i in range(1, totalPages + 1):
                process_province_page(driver, province_name, i)
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