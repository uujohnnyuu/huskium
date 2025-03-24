# huskium

## Table of Contents
- [Overview](#overview)
- [Usage](#usage)
- [Page Object and Test Script](#page-object-and-test-script)
- [Timeout Value Settings](#timeout-value-settings)
- [Timeout Reraise Settings](#timeout-reraise-settings)
- [Element Cache Settings](#element-cache-settings)
- [Log Settings](#log-settings)
- [Wait Actions](#wait-actions)
- [Appium Extended Actions](#appium-extended-actions)
- [Action Chains](#action-chains)
- [Select Actions](#select-actions)
- [Inheritance](#inheritance)
- [TODO](#todo)

---

## Copyright
### Developer: Johnny Chou

---

## Overview
- **huskium** is a Page Object framework built on Selenium and Appium.
- It utilizes Python’s data descriptors to enhance UI automation.
- Currently tracking Appium v4.5.0 (released on 2025/01/22).
- Sphinx documentation: https://uujohnnyuu.github.io/huskium/

---

## Usage
Easily **build page objects** and **write test scripts**, 
greatly improving stability and performance.

---

## Page Object and Test Script

The core of huskium is to quickly build a **page object** and utilize it to write **test scripts**.  
Unless specified otherwise, `Element` refers to both `Element` and `Elements`.

### 1. Page Object

Create a simple page object (e.g., `my_page.py`) by defining `Element` instances.

```python
# my_page.py

from huskium import Page, Element, Elements

class MyPage(Page):

    # Standard way to define an element.
    search_field = Element(By.NAME, 'q', remark='Search input box')
    search_results = Elements(By.TAG_NAME, 'h3', remark='All search results')
    search_result1 = Element(By.XPATH, '(//h3)[1]', remark='First search result')
```

### 2. Test Script

After defining the page object, you can easily write test scripts (e.g., `test_my_page.py`).

Initialize the page object with a driver, 
then use the `page.method()` or `page.element.method()` pattern.

```python
# test_my_page.py

from selenium import webdriver
from my_page import MyPage

driver = webdriver.Chrome()
my_page = MyPage(driver)

my_page.get("https://google.com")

# Perform actions with automatic explicit waits.
my_page.search_field.send_keys("Selenium").submit()
my_page.search_results.wait_all_visible()
my_page.save_screenshot("screenshot.png")

assert "Selenium" in my_page.search_result1.text
my_page.search_result1.click()

my_page.close()
```

---

## Advanced Dynamic Element

Most page objects, as described in the previous section, are called **static element**.  
In contrast, **dynamic element** are defined at runtime within the test script.

Dynamic element is useful when element locators can't be known beforehand. 
For example, in dev environments without stable attributes, or when locators frequently change.

Avoid using dynamic elements unless necessary. If needed, here are three recommended approaches.  
No matter which method you choose, the final usage will still follow the `page.element.method()` pattern.

### 1. Dynamic Decorator

**Pros:** Simple and intuitive; this is the recommended approach.  
**Cons:** Cannot statically store element info (though the performance impact is minimal).

```python
# my_page.py
from huskium import Page, Element, By, dynamic

class MyPage(Page):

    @dynamic
    def search_result(self, order: int = 1):
        return Element(By.XPATH, f'(//h3)[{order}]', remark=f'Search result no.{order}')
```

Test script still uses `page.element.method()`, but the element is now a function.
```python
# test_my_page.py
my_page.search_result(3).click()
```

### 2. Dynamic Instance Method

**Pros:** Once executed, the dynamic element is saved as a static element for reuse.  
**Cons:** Slightly more verbose; requires a corresponding static and dynamic element.

```python
# my_page.py
from huskium import Page, Element, By

class MyPage(Page):

    # Define a static element first.
    static_search_result = Element()

    # Use `dynamic()` to configure the static element.
    def dynamic_search_result(self, order: int = 1):
        return self.static_search_result.dynamic(By.XPATH, f'(//h3)[{order}]', remark=f'NO.{order}')
```

Once set, you can reuse the static element:
```python
# test_my_page.py
my_page.dynamic_search_result(3).wait_present()
my_page.static_search_result.click()
```

### 3. Data Descriptor Set Method

**Pros:** Stores dynamic results in a static element using proper data descriptor mechanics.  
**Cons:** Less intuitive and requires understanding Python data descriptor behavior.

```python
# my_page.py
from huskium import Page, Element, By

class MyPage(Page):

    # Define a static element first.
    static_search_result = Element()

    # Use the descriptor's __set__ method by reassigning the element.
    def dynamic_search_result(self, order: int = 1):
        self.static_search_result = Element(By.XPATH, f'(//h3)[{order}]', remark=f'NO.{order}')
        return self.static_search_result
```

Once set, you can reuse the static element:
```python
# test_my_page.py
my_page.dynamic_search_result(3).wait_present()
my_page.static_search_result.click()
```

---

## Timeout Value Settings

The timeout value defines the maximum time in seconds allowed to 
successfully complete a WebDriver or WebElement operation.

There are three types of timeout value settings, with the following priority:
- **P1**: Method Level
- **P2**: Element Level
- **P3**: Page Level

### P1. Method Level of Timeout Value 
Defines the timeout for a specific method call.  
This **temporarily** overrides both the `Page` and `Element(s)` timeout settings.
```python
my_page = MyPage(driver, timeout=10)
my_page.url_is('https://...', timeout=30)  # 30 seconds for this call only.
my_page.my_element.wait_visible(timeout=5)  # 5 seconds for this call only.

```

### P2. Element Level of Timeout Value 
Sets a specific default timeout for an `Element`.
This **permanently** overrides the `Page` timeout settings. 
```python
my_element = Element(..., timeout=20, ...)
```
Or reset element timeout during test execution.
```python
my_page.my_element.reset_timeout(7)
```

### P3. Page Level of Timeout Value 
Sets the default timeout for the `Page` and all `Element` objects within it.
```python
my_page = MyPage(driver, timeout=10)
```

---

## Timeout Reraise Settings

The reraise parameter controls whether a TimeoutException is raised when a timeout occurs.
- **True**: the process raises `TimeoutException` on timeout.
- **False**: the process returns `False` on timeout.

There are two types of timeout reraise settings, with the following priority:
- **P1**: Method Level
- **P2**: Page Level

### P1. Method Level of Timeout Reraise
Defines the default reraise behavior for Page and Element methods that accept the reraise parameter.
If not set, the Page’s reraise state is used.
```python
my_page = MyPage(driver, timeout=30, reraise=True)

# Page methods.
my_page.url_is()  # Raises TimeoutException on timeout.
my_page.url_is(reraise=False)  # Returns False on timeout.

# Element methods.
my_page.my_element.wait_present()  # Raises TimeoutException on timeout.
my_page.my_element.wait_present(reraise=False)  # Returns False on timeout.
```

### P2. Page Level of Timeout Reraise

If a timeout-related method does not explicitly set the reraise behavior, 
the page-level reraise setting will be used.

Notice that WebElement methods will **always raise a TimeoutException** on timeout 
because returning `False` would result in meaningless `AttributeError`.

```python
my_page = MyPage(driver, timeout=30, reraise=False)

# Both returns False on timeout.
my_page.url_is()
my_page.my_element.wait_present()

# WebElement methods always raise a TimeoutException on timeout.
my_page.my_element.text
my_page.my_element.click()
```

---

## Element Cache Settings

This method **only applies to** `Element`, **not** `Elements`!

It controls whether to cache the found WebElement object for reuse.  
The benefit is that if the same element is accessed multiple times,  
the already located WebElement will be reused to save the time of re-locating, speeding up the process.

Additionally, it will automatically handle recovery when `InvalidSessionIdException` or `StaleElementReferenceException` occurs,  
so you don't have to worry about element reference issues.

By default, the `Element` class uses the caching mechanism.  
However, if your testing environment is highly unstable,  
you can simply disable this cache setting to ensure stability by re-locating the element each time.

Notice that `Elements` does not support this setting because the state of multiple elements tends to be more volatile.  
Even if caching were enabled, it would not guarantee the cached elements are the same as the previous ones.  
Thus, it follows the official explicit wait strategy by re-locating the elements each time.

Again, this method **only applies to** `Element`, **not** `Elements`!
- **True**: Cache the found WebElement object to reuse.
- **False**: Refind element for each process.

There are two types of element cache settings
- **P1**: Element Object Level
- **P2**: Element Global Level

### P1. Element Object Level of Cache
Sets whether the `Element` object caches, overriding the global setting.
```python
my_element = Element(..., cache=None, ...)  # Use global setting
my_element = Element(..., cache=True, ...)  # my_element caches
my_element = Element(..., cache=False, ...)  # my_element does not cache
```
Or reset during test execution.
```python
my_page.my_element.unset_cache()  # Use global setting
my_page.my_element.enable_cache()  # my_element caches
my_page.my_element.disable_cache()  # my_element does not cache
```

### P2. Element Global Level of Cache
Sets whether `Element` globally caches by default. 
```python
Element.enable_default_cache()  # Enable global default cache
Element.disable_default_cache()  # Disable global default cache
Element.default_cache()  # Current global default cache setting
```

### Element Cache Example
A common scenario where we validate the element’s text before clicking:
- If the assertion passes, **my_element will cache the WebElement object** in the inner attribute.
- When calling `click()`, **the cached WebElement will be used directly**.
- There's no need to refetch the element or store it in a separate variable.
- Even if the WebElement reference becomes stale in between, it will automatically recover and refetch as needed.
```python
assert my_page.my_element.text == 'some text'
my_page.my_element.click()
```

---

## Log Settings

### 1. Debug Log Configuration
```python
from huskium import LogConfig

# Capture log messages from frames where the name starts with 'test'.
# Set to None to disable filtering.
LogConfig.PREFIX_FILTER.reset_prefix('test')

# Set to True for case-insensitive filtering.
LogConfig.PREFIX_FILTER.reset_islower(True)

# Specify whether to filter logs by function name.
# If False, filtering is based on file (module) name instead.
LogConfig.PREFIX_FILTER.reset_isfunc(True)

# Whether to record current frame info in the record (LogRecord) object.
# This is useful for assert exception messages for quicker debugging.
LogConfig.PREFIX_FILTER.reset_torecord(True)
record = LogConfig.PREFIX_FILTER.record
assert condition, (record.filename, record.lineno, record.funcName)
```

### 2. Debug Log Display Example

When `LogConfig.PREFIX_FILTER.prefix = None`, logging behaves normally, 
showing the first frame (stacklevel = 1).
```log
2025-02-11 11:13:08 | DEBUG | element.py:574 | wait_clickable | Element(logout_button): Some message.
```

When `LogConfig.PREFIX_FILTER.prefix = 'test'`, 
logs display the first frame with a name starting with 'test' (stacklevel >= 1).
This helps quickly trace the module and line where the issue occurs.
```log
2025-02-11 11:13:22 | DEBUG | test_game.py:64 | test_game_flow | Element(logout_button): Some message.
```

### 3. Customize Log Filter

You can apply the provided filters to your own logging as follows.
```python
from huskium import PrefixFilter, FuncPrefixFilter, FilePrefixFilter

# PrefixFilter includes both FuncPrefixFilter and FilePrefixFilter.
prefix_filter = PrefixFilter('test')
logging.getLogger().addFilter(prefix_filter)
```

If you want to display only module frames, use `FilePrefixFilter`.
```python
run_module_filter = FilePrefixFilter('run')
logging.getLogger().addFilter(run_module_filter)
```

If you want to display only function frames, use `FuncPrefixFilter`.
```python
test_func_filter = FuncPrefixFilter('test')
logging.getLogger().addFilter(test_func_filter)
```

You can reset the filter attributes during testing.
```python
xxx_filter.reset_prefix('run')
xxx_filter.reset_islower(False)
xxx_filter.reset_torecord(True)

# This is only for PrefixFilter.
# True for FuncPrefixFilter; False for FilePrefixFilter.
prefix_filter.reset_isfunc(False)  
```

---

## Wait Actions

### 1. Basic Element Status
```python
# Single Element
page.element.wait_present()
page.element.wait_absent()
page.element.wait_visible()
page.element.wait_invisible()
page.element.wait_clickable()
page.element.wait_unclickable()
page.element.wait_selected()
page.element.wait_unselected()

# Multiple Elements
page.elements.wait_all_present()
page.elements.wait_all_absent()
page.elements.wait_all_visible()
page.elements.wait_any_visible()
```

### 2. Reverse Element States with Presence Check
```python
# For invisible and unclickable elements, absence is allowed by setting present=False:
page.element.wait_invisible(present=False)  # Can be either absent or invisible
page.element.wait_unclickable(present=False)  # Can be either absent or unclickable
```

---

## Appium Extended Actions

### Appium 2.0+ Usage
```python
from huskium import Offset, Area

# Page swipe or flick.
page.swipe_by()  # Default Offset.UP, Area.FULL
page.flick_by()  # Default Offset.UP, Area.FULL
page.swipe_by(Offset.UPPER_RIGHT, Area.FULL)
page.flick_by(Offset.LOWER_LEFT)

# Element swipe or flick until visible.
page.element.swipe_by()  # Default Offset.UP, Area.FULL
page.element.flick_by()  # Default Offset.UP, Area.FULL
page.element.swipe_by(Offset.UPPER_RIGHT)
page.element.flick_by(Offset.LOWER_LEFT, Area.FULL)

# Drawing gestures (e.g., "9875321" for reverse Z)
dots = page.elements.locations
page.draw_gesture(dots, "9875321")

# Drawing lines between dots
dots = page.elements.locations
page.draw_lines(dots)
```

---

## Action Chains
```python
page.element.move_to_element().drag_and_drop().perform()
page.scroll_from_origin().double_click().perform()

# or
page.element.move_to_element().drag_and_drop()
page.scroll_from_origin().double_click()
...  # do something
page.perform()  # perform all actions
```

---

## Select Actions
```python
page.element.options
page.element.select_by_value("option_value")
```

---

## Inheritance

```python
from huskium import Page as HuskyPage, Element as HuskyElement

class Page(HuskyPage):
    def extended_func(self, par):
        ...

class Element(HuskyElement):
    def extended_func(self, par):
        ...
```

---

## TODO
Continue tracking Appium version updates.
