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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from dateutil.relativedelta import relativedelta
from crawlers import Crawler
from crawlers.gkld import Trace
from db.mongodb.articles import UnicloudDBArticleManager
from models.article import Article, ArticleManager
# from search_engine.meilisearch.articles import MeiliSearchArticleManager
from utilities import Singleton, constant, flow, loggers, timeutil
from selenium.common.exceptions import WebDriverException

@Singleton
class GkldCrawler(Crawler):
    
    def __init__(self, trace: Trace):
        self.trace = trace

    def extract_article_title(self, driver: webdriver.Chrome):
        h1_element = driver.find_element(By.XPATH, './/div[@class="article-title"]/h1')
        # 使用BeautifulSoup解析<h1>元素的HTML内容
        soup = BeautifulSoup(h1_element.get_attribute("outerHTML"), "html.parser")
        # 剔除<a>元素内的文本内容
        for a in soup.find_all("a"):
            a.extract()
        # 获取<h1>元素的纯文本内容并输出
        return soup.get_text().strip()
    
    def is_date_invalid(self, e: WebElement, start_dt: datetime, end_dt: datetime):
        date_str = e.find_element(By.XPATH, './/time').text
        date_time: datetime = dateparser.parse(date_str) if '前' in date_str else datetime.strptime(date_str, constant.HYPHEN_JOINED_DATE_FORMAT)
        # 检查
        if start_dt.tzinfo.zone == end_dt.tzinfo.zone == timeutil.get_tz().zone:
            is_within_range = start_dt <= timeutil.localize_native_dt(date_time) <= end_dt
            return not is_within_range
        else:
            raise Exception('Inconsistent TZ')

    def extract_collect_date(self, driver: webdriver.Chrome):
        date = driver.find_element(By.CLASS_NAME, 'date').get_attribute('innerHTML')
        match = re.search(constant.HYPHEN_JOINED_DATE_REGEX, date)
        date: str = match.group()
        return date

    def extract_apply_deadline(self, driver: webdriver.Chrome, collect_date_str: str):
        deadline = None
        try:
            job_info = driver.find_element(By.XPATH, '//div[@class="jobinfo-list"]//li[contains(., "报名时间")]')
            res = timeutil.extract_end_datetime(job_info.text, collect_date_str)
            deadline = res if res else re.sub(r"报名时间[：:]", '', job_info.text)
        except:
            pass
        return deadline

    def replace_sensitive_text(self, input_text):
        # 定义替换规则
        replacements = {
            r'公考雷达': os.getenv('APP_NAME', '公考营地'),
        }

        # 生成正则表达式模式
        pattern = re.compile('|'.join(re.escape(key) for key in replacements.keys()))

        # 使用正则表达式替换文本
        output_text = pattern.sub(lambda x: replacements[x.group(0)], input_text)

        return output_text

    def extract_article_content(self, driver: webdriver.Chrome):
        def _should_remove(tag):
            if '公考雷达' in tag.text:
                return True
            if tag.name == 'a' and tag.get('href') and 'www.gongkaoleida.com/search' in tag.get('href'):
                return True
            return False

        article: WebElement = driver.find_element(By.XPATH, '//div[@class="article-detail"]/article')
        # TODO: replace attachments' link
        content = article.get_attribute('innerHTML')
        soup = BeautifulSoup(content, 'html.parser')

        # 过滤
        elements_to_remove = soup.find_all(_should_remove)
        for element in elements_to_remove:
            element.extract()

        # 替换敏感信息
        content = self.replace_sensitive_text(str(soup))
        return content

    def process_province_page(self, article_manager: ArticleManager, driver: webdriver.Chrome, province_name, exam_type, info_type, page_num, end_dt: datetime):
        filters={
            'province': province_name,
            'exam_type': exam_type,
            'info_type': info_type,
        }
        start_dt: datetime = article_manager.get_max_collect_date(filters) or end_dt - relativedelta(months=3)
        #  Jump to specific page number
        url = driver.current_url.split('?')[0] + f'?page={page_num}'
        driver.execute_script(f"window.open('{url}');")
        province_page_with_pagination = flow.switch_to_lastest_window(driver)

        @flow.iterate_over_web_elements(
            driver = driver,
            selector_value = '.notice-list li',
            stop = partial(self.is_date_invalid, start_dt=start_dt, end_dt=end_dt)
        )
        @flow.operate_in_new_window(
            driver = driver,
            initial_page = province_page_with_pagination,
        )
        def save_notices():
            try:
                article_title = self.extract_article_title(driver).replace('/', '|')
                if article_manager.check_article_existence_by_title(article_title):
                    collect_date_str = self.extract_collect_date(driver)
                    article = Article(
                        id=str(uuid.uuid4()),
                        title=article_title,
                        province=province_name,
                        exam_type=exam_type,
                        info_type=info_type,
                        # set the parsed time to local timezone and then convert it to UTC timestamp
                        collect_date=timeutil.local_dt_str_to_utc_ts(collect_date_str),
                        apply_deadline=self.extract_apply_deadline(driver, collect_date_str),
                        html_content=self.extract_article_content(driver)
                    )
                    article_manager.insert_article(article)
                    self.trace.scraped_articles += 1
            # 页面采集失败，可能是404页面，也可能是非标准结构
            except NoSuchElementException as e:
                loggers.error_file_logger.error(f"URL: {driver.current_url} - {e.msg}")

        save_notices()
        # 关闭省份页面
        if driver.current_window_handle == province_page_with_pagination:
            driver.close()

    def scrape_website(self):
        driver = self._create_chrome_web_driver(headless=os.getenv('HEADLESS_MODE'))

        def _find_checkbox(i_class, text):
            return driver.find_element(By.XPATH, f'//i[contains(@class, "{i_class}")]/following-sibling::a[contains(text(), "{text}")]')
            
        def _click_checkbox(text, checked=False, interval=3):
            # checked: False 代表当前应当处于未点击状态，将执行tick操作， True代表当前应当处于已被点击状态，将执行untick操作
            try:
                checkbox = _find_checkbox('icon-oncheck' if checked else 'icon-check', text)
                checkbox.click()
                time.sleep(interval)
            except NoSuchElementException as e1:
                try:
                    _find_checkbox('icon-check' if checked else 'icon-oncheck', text)
                    loggers.debug_file_logger.debug(f'选项框 {text} 已经处于{"未" if checked else "已被"}点击状态， 无需额外操作')
                except Exception as e2:
                    loggers.error_file_logger.error(f'选项框 {text} 找不到, {e2.msg}')            

        try:
            driver.get('https://www.gongkaoleida.com/')
            homepage = driver.current_window_handle
            end_dt: datetime = timeutil.localize_native_dt(datetime.now())

            # Iterate over all the provinces
            @flow.iterate_over_web_elements(
                driver = driver,
                selector_value = '.province-name',
                filter = lambda e: e.text not in self.trace.province if self.trace.scrape_times > 1 else True # 重启后略过已经爬过的省份
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
                    current_info_type = info_types[a_i]
                    if self.trace.scrape_times > 1 and self.trace.info_type and a_i < info_types.index(self.trace.info_type):
                        loggers.debug_file_logger.debug(f"跳过资讯类型: {current_info_type}")
                        continue
                    else:
                        # 记录 info_type
                        self.trace.info_type = current_info_type

                    _click_checkbox(current_info_type)
                    # 取消勾选上个循环遗留下的checkboxes
                    if a_i > 0:
                        _click_checkbox(exam_types[-1], checked=True)
                        _click_checkbox(info_types[a_i-1], checked=True)

                    for i in range(num_of_exam_types):
                        current_exam_type = exam_types[i]
                        if self.trace.scrape_times > 1 and self.trace.exam_type and i < exam_types.index(self.trace.exam_type):
                            loggers.debug_file_logger.debug(f"跳过考试类型: {current_exam_type}")
                            continue
                        else:
                            # 记录 exam_type
                            self.trace.exam_type = current_exam_type
                            # 重置 exam_type 以防止下个info_type循环跳过最后一个exam_type之前的所有exam_type
                            if i == num_of_exam_types - 1:
                                self.trace.exam_type = ''

                        _click_checkbox(current_exam_type)
                        # 取消勾选上个循环遗留下的checkbox
                        if i > 0:
                            _click_checkbox(exam_types[i-1], checked=True)

                        # Get the total number of pages
                        try:
                            totalPages = int(driver.find_element(By.XPATH, '//li[a[text()="下一页"]]/preceding-sibling::li[1]').text)
                        except NoSuchElementException:
                            totalPages = 1
                        if os.getenv('RUNNING_ENV') == constant.TEST_ENV:
                            totalPages = min(totalPages, 3)
                        # 处理每个分页
                        for j in range(1, totalPages + 1):
                            self.process_province_page(UnicloudDBArticleManager(), driver, province_name, current_exam_type, current_info_type, j, end_dt)
                            driver.switch_to.window(province_page)

                # 记录已经爬过的省份
                self.trace.province.add(province_name)
                # 关闭新窗口并切换回原始窗口
                driver.close()
                driver.switch_to.window(homepage)
            
            iterate_over_all_provinces()
            loggers.debug_file_logger.debug(f"成功完成本次爬取任务! 总共爬取了{self.trace.scrape_times}个文章")
        except WebDriverException as e:
            if self.trace.scrape_times <= 3 and "no such execution context" in e.msg:
                self.trace.scrape_times += 1
                loggers.error_file_logger.error(f"{e}, 即将开始第{self.trace.scrape_times}次爬取..., 当前trace: {self.trace}")
                self.scrape_website()
            else:
                loggers.error_file_logger.error(f"{e.msg}, 当前trace: {self.trace}, 异常退出")
        except Exception as e:
            loggers.error_file_logger.error(f"{e.msg}, 当前trace: {self.trace}, 异常退出")
        finally:
            driver.quit()

if __name__ == "__main__":
    load_dotenv()
    # trace = Trace(province={'国家', '安徽'}, exam_type='银行', info_type='招考公告', scrape_times=2)
    trace = Trace()
    GkldCrawler(trace).scrape_website()