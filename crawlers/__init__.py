from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Crawler(ABC):

    def _create_chrome_web_driver(self, headless: bool = False):
        chrome_options = Options()
        if headless.lower() == "true":
            chrome_options.add_argument('--headless')  # 启用headless模式
            chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小
        # 创建Chrome WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver

    @abstractmethod
    def scrape_website(self):
        pass

