# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..generic import Page as GenericPage


class Page(GenericPage[WebDriver, WebElement]):
    # Delegate "_verify_driver" to "GenericPage" to allow users to combine 
    # "AppiumPage" with "SeleniumElement", which is useful in mobile web contexts. 
    # If "SeleniumElement" is already defined in "WebPage",
    # it can be reused in "AppiumPage" via a class like "MyPage(WebPage, AppiumPage)", 
    # without needing to redefine "SeleniumElement".
    pass
