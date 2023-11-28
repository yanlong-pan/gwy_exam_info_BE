from functools import wraps
import os
from typing import Callable, List
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

from utilities.constant import TEST_ENV

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

def iterate_over_web_elements(
    driver: webdriver.Chrome,
    selector_value: str,
    selector: str = By.CSS_SELECTOR,
    filter: Callable[[WebElement], bool] = lambda _: True,
    stop: Callable[[WebElement], bool] = lambda _: False
):
    """
     Decorator to iterate over web elements. The function will be called with a list of WebElements that match the selector_value
     
     Args:
     	 driver: WebDriver instance to be used for finding the elements
     	 selector_value: Value of the selector to be used for finding the elements
     	 selector: CSS Selector to be used for finding the elements
     
     Returns: 
     	 None
    """
    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            """
             Inner function to find elements and pass them to the function that is called in sequence.
            """
            num_of_elements = len(driver.find_elements(selector, selector_value))
            if os.environ.get('RUNNING_ENV') == TEST_ENV:
                num_of_elements = min(num_of_elements, 2)
            # Find elements in the driver and call func.
            for i in range(num_of_elements):
                elements: List[WebElement] = driver.find_elements(selector, selector_value)
                element = elements[i]
                if stop(element):
                    break
                elif filter(element):
                    kwargs['web_element'] = elements[i]
                    func(*args, **kwargs)
        return inner_wrapper
    return outer_wrapper


def operate_in_new_window(
    driver: webdriver.Chrome,
    initial_page: str,
):
    """
     Decorator for clicking an element and open a new window. It is used to execute function in new window
     
     Args:
     	 driver: WebDriver object to work with
     	 initial_page: Page to switch to after clicking
     
     Returns: 
     	 None
    """
    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, web_element, **kwargs):
            """
             Inner function for clicking an element and open a new window. It is used to execute function in new window
            """
            web_element.click()
            

            switch_to_lastest_window(driver)
            # Execute operation in new window 
            func(*args, **kwargs)
            
            # close the current window and switch back to the initial page
            driver.close()
            driver.switch_to.window(initial_page)

        return inner_wrapper
    return outer_wrapper
