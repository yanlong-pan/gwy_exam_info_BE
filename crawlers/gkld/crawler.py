from selenium import webdriver
from selenium.webdriver.common.by import By

from utilities import fileIO, flow

def process_province_page(driver: webdriver.Chrome, province_name, page_num):
    #  Jump to specific page number
    url = driver.current_url.split('?')[0] + f'?page={page_num}'
    driver.execute_script(f"window.open('{url}');")
    province_page_with_pagination = flow.switch_to_lastest_window(driver)

    @flow.iterate_over_new_windows(
        driver = driver,
        initial_page = province_page_with_pagination,
        selector_value = '.notice-list li a'
    )
    def save_notices():
        # extract article and save to a file
        content = driver.find_element(By.CLASS_NAME, 'article-detail').get_attribute('innerHTML')
        fileIO.write_content_to_file(f'./articles/{province_name}', f'{driver.title}.html', content)

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
        num_of_provinces = len(driver.find_elements(By.CLASS_NAME, 'province-name'))
        for i in range(num_of_provinces):
            # 重新定位省份元素, avoid StaleElementReferenceError
            provinces = driver.find_elements(By.CLASS_NAME, 'province-name')
            province = provinces[i]
            province_name = province.text
            province.click()

            # switch to the province detail page
            province_page = flow.switch_to_lastest_window(driver)

            # 点击“公务员”前的icon-check
            driver.find_element(By.XPATH, '//i[contains(@class, "icon-check")]/following-sibling::a[contains(text(), "公务员")]').click()

            # Explicitly wait
            # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'notice-list')))

            # Get the total number of pages
            totalPages = int(driver.find_element(By.XPATH, '//li[a[text()="下一页"]]/preceding-sibling::li[1]').text)

            # 处理每个分页
            for i in range(1, totalPages + 1):
                process_province_page(driver, province_name, i)
                driver.switch_to.window(province_page)
            
            # 关闭新窗口并切换回原始窗口
            driver.close()
            driver.switch_to.window(homepage)

    finally:
        driver.quit()
