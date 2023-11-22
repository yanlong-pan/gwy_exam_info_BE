from functools import wraps
from typing import List
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

def switch_to_lastest_window(driver: webdriver.Chrome):
    """
     Switch to the last window in the browser.
     
     Args:
     	 driver: Selenium instance to work with. Must be connected to a web page.
     
     Returns: 
     	 The handle of the last window in the browser or None if there are no windows on the page. Note that this does not change the focus
    """
    latest_window = driver.window_handles[-1]
    driver.switch_to.window(latest_window)
    return latest_window

def iterate_over_new_windows(
    driver: webdriver.Chrome,
    initial_page: str,
    selector_value: str,
    selector: str = By.CSS_SELECTOR,
):
    """
        Iterate over new windows and execute function. This is a wrapper for functions that need to be executed in order to click on elements in new windows

        Args:
            driver: WebDriver instance of current session.
            initial_page: Page to switch back after operations on the new page.
            selector_value: Value of the selector to search for.
            selector: selector type of elements. Default is By. CSS_SELECTOR.
        
        Returns: 
            Function that takes as input function and returns result of that function.
    """
    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            """
             Inner function for clicking on elements and open new window. It is used to execute function in new window
             
             
             Returns: 
             	 result of function execute
            """
            num_of_elements = len(driver.find_elements(selector, selector_value))
            for i in range(num_of_elements):
                # Click on the element, open a new window
                elements: List[WebElement] = driver.find_elements(selector, selector_value)
                elements[i].click()
                
                switch_to_lastest_window(driver)
                # Execute operation in new window 
                result = func(*args, **kwargs)
                
                # close the current window and switch back to the initial page
                driver.close()
                driver.switch_to.window(initial_page)

            return result
        return inner_wrapper
    return outer_wrapper