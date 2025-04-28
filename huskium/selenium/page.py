# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

import logging
from typing import Any, cast, Iterable, Literal, Self, Type

from selenium.common.exceptions import TimeoutException
from selenium.types import WaitExcTypes
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.fedcm.dialog import Dialog
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.remote.fedcm import FedCM
from selenium.webdriver.remote.script_key import ScriptKey
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver

from ..logging import LogConfig, PageElementLoggerAdapter
from ..wait import Wait


LOGGER = logging.getLogger(__name__)
LOGGER.addFilter(LogConfig.PREFIX_FILTER)


class GenericPage[WD: WebDriver, WE: WebElement]:

    def __init__(
        self,
        driver: WD,
        timeout: int | float = 10,
        reraise: bool = True,
        remark: str = 'Page'
    ) -> None:
        """
        Args:
            driver: The WebDriver object of Selenium or Appium.
            timeout: Maximum wait time in seconds.
            reraise: The behavior when timed out.
                `True` to raise `TimeoutException`,
                `False` to return `False`.
            remark: Custom remark for identification or logging.
        """
        self._verify_data(driver, timeout, reraise, remark)
        self._driver = driver
        self._timeout = timeout
        self._reraise = reraise
        self._remark = remark
        self._wait = Wait(driver, timeout)
        self._action = ActionChains(driver)
        self._logger = PageElementLoggerAdapter(LOGGER, self)

    def _verify_data(
        self,
        driver: WD,
        timeout: int | float,
        reraise: bool,
        remark: str
    ) -> None:
        self._verify_driver(driver)
        self._verify_timeout(timeout)
        self._verify_reraise(reraise)
        self._verify_remark(remark)

    def _verify_driver(self, driver: Any) -> None:
        if not isinstance(driver, WebDriver):
            raise TypeError(f'The "driver" must be "selenium WebDriver", got {type(driver).__name__}.')
        if isinstance(driver, AppiumWebDriver):
            raise TypeError('The "driver" must be "selenium WebDriver", got "appium WebDriver".')

    def _verify_timeout(self, timeout: Any) -> None:
        if not isinstance(timeout, int | float):
            raise TypeError(f'The "timeout" must be "int" or "float", got {type(timeout).__name__}.')

    def _verify_reraise(self, reraise: Any) -> None:
        if not isinstance(reraise, bool):
            raise TypeError(f'The "reraise" must be "bool", got {type(reraise).__name__}.')

    def _verify_remark(self, remark: Any) -> None:
        if not isinstance(remark, str):
            raise TypeError(f'The "remark" must be "str", got {type(remark).__name__}.')

    @property
    def driver(self) -> WD:
        """The WebDriver instance."""
        return self._driver

    @property
    def timeout(self) -> int | float:
        """The page timeout."""
        return self._timeout

    @property
    def reraise(self) -> bool:
        """The timeout reraise state."""
        return self._reraise

    @property
    def remark(self) -> str:
        """The page remark."""
        return self._remark

    @property
    def wait(self) -> Wait:
        """The current WebDriverWait instance."""
        return self._wait

    def waiting(
        self,
        timeout: int | float | None = None,
        ignored_exceptions: Type[Exception] | Iterable[Type[Exception]] | None = None
    ) -> Wait:
        """The final WebDriverWait instance."""
        self._wait.timeout = timeout
        self._wait.ignored_exceptions = ignored_exceptions
        return self._wait

    @property
    def action(self) -> ActionChains:
        """The ActionChains instance."""
        return self._action

    def reset_action(self, driver: WD, duration: int = 250) -> None:
        """
        Reset the ActionChains instance.

        Args:
            driver: The WebDriver instance.
            duration: override the default 250 msecs of PointerInput.
        """
        self._verify_driver(driver)
        self._action = ActionChains(driver, duration)

    @property
    def logger(self) -> PageElementLoggerAdapter:
        """The page logger."""
        return self._logger

    def _timeout_reraise(self, reraise: bool | None) -> bool:
        """
        The final reraise state when a timeout occurs.
        If reraise is None, use page reraise state.
        """
        return self.reraise if reraise is None else reraise

    def _timeout_process(
        self,
        status: str,
        exc: TimeoutException,
        reraise: bool | None
    ) -> Literal[False]:
        """Handling a TimeoutException after it occurs."""
        exc.msg = status
        if self._timeout_reraise(reraise):
            raise exc
        return False

    @property
    def log_types(self) -> Any:
        """
        Gets a list of the available log types.
        This only works with w3c compliant browsers.
        """
        return self.driver.log_types

    def get_log(self, log_type: Any) -> Any:
        """
        Gets the log for a given log type.

        Args:
            log_type: Type of log that which will be returned.

        Examples:
            ::

                page.get_log('browser')
                page.get_log('driver')
                page.get_log('client')
                page.get_log('server')

        """
        return self.driver.get_log(log_type)

    def get_downloadable_files(self) -> list:
        """
        Retrieves the downloadable files as a map of file names and
        their corresponding URLs.
        """
        return self.driver.get_downloadable_files()

    def download_file(self, file_name: str, target_directory: str) -> None:
        """
        Downloads a file with the specified file name to the target directory.

        Args:
            file_name: The name of the file to download.
            target_directory: The path to the directory to
                save the downloaded file.
        """
        self.driver.download_file(file_name, target_directory)

    def delete_downloadable_files(self) -> None:
        """Deletes all downloadable files."""
        self.driver.delete_downloadable_files()

    @property
    def fedcm(self) -> FedCM:
        """
        Returns an object providing access to all
        Federated Credential Management (FedCM) dialog commands.

        Examples:
            ::

                title = page.fedcm.title
                subtitle = page.fedcm.subtitle
                dialog_type = page.fedcm.dialog_type
                accounts = page.fedcm.account_list
                page.fedcm.select_account(0)
                page.fedcm.accept()
                page.fedcm.dismiss()
                page.fedcm.enable_delay()
                page.fedcm.disable_delay()
                page.fedcm.reset_cooldown()

        """
        return self.driver.fedcm

    @property
    def supports_fedcm(self) -> bool:
        """Returns whether the browser supports FedCM capabilities."""
        return self.driver.supports_fedcm

    @property
    def dialog(self) -> Dialog:
        """Returns the FedCM dialog object for interaction."""
        return self.driver.dialog

    def fedcm_dialog(
        self,
        timeout: float = 5,
        poll_frequency: float = 0.5,
        ignored_exceptions: WaitExcTypes | None = None
    ) -> Dialog | None:
        """
        Waits for and returns the FedCM dialog.

        Args:
            timeout: How long to wait for the dialog.
            poll_frequency: How frequently to poll.
            ignored_exceptions: Exceptions to ignore while waiting.

        Returns:
            Dialog:
                The FedCM dialog object if found.

        Raises:
            TimeoutException: If dialog doesn't appear.
            WebDriverException: If FedCM not supported.
        """
        return self.driver.fedcm_dialog(timeout, poll_frequency, ignored_exceptions)

    @property
    def name(self) -> str:
        """Returns the name of the underlying browser for this instance."""
        return self.driver.name

    def get(self, url: str) -> None:
        """Loads a web page in the current browser session."""
        self.driver.get(url)

    @property
    def source(self) -> str:
        """The source of the current page."""
        return self.driver.page_source

    @property
    def url(self) -> str:
        """The URL of the current page."""
        return self.driver.current_url

    def url_is(
        self,
        url: str,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """An expectation for checking the current url."""
        try:
            return self.waiting(timeout).until(ec.url_to_be(url))
        except TimeoutException as exc:
            current_url = self.driver.current_url
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for url to be "{url}". '
                f'The current url is "{current_url}".'
            )
            return self._timeout_process(status, exc, reraise)

    def url_contains(
        self,
        url: str,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        An expectation for checking that the current url contains a
        case-sensitive substring.
        """
        try:
            return self.waiting(timeout).until(ec.url_contains(url))
        except TimeoutException as exc:
            current_url = self.driver.current_url
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for url contains "{url}". '
                f'The current url is "{current_url}".'
            )
            return self._timeout_process(status, exc, reraise)

    def url_matches(
        self,
        pattern: str,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """An expectation for checking the current url."""
        try:
            return self.waiting(timeout).until(ec.url_matches(pattern))
        except TimeoutException as exc:
            current_url = self.driver.current_url
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for url matches pattern "{pattern}". '
                f'The current url is "{current_url}".'
            )
            return self._timeout_process(status, exc, reraise)

    def url_changes(
        self,
        url: str,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        An expectation for checking the current url is different
        than a given string.
        """
        try:
            return self.waiting(timeout).until(ec.url_changes(url))
        except TimeoutException as exc:
            current_url = self.driver.current_url
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for url changes. '
                f'The current url is still "{current_url}".'
            )
            return self._timeout_process(status, exc, reraise)

    @property
    def title(self) -> str:
        """The title of the current page."""
        return self.driver.title

    def title_is(
        self,
        title: str,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """An expectation for checking the title of a page."""
        try:
            return self.waiting(timeout).until(ec.title_is(title))
        except TimeoutException as exc:
            current_title = self.driver.title
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for title to be "{title}". '
                f'The current title is "{current_title}".'
            )
            return self._timeout_process(status, exc, reraise)

    def title_contains(
        self,
        title: str,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        An expectation for checking that the title contains a
        case-sensitive substring.
        """
        try:
            return self.waiting(timeout).until(ec.title_contains(title))
        except TimeoutException as exc:
            current_title = self.driver.title
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for title contains "{title}". '
                f'The current title is "{current_title}".'
            )
            return self._timeout_process(status, exc, reraise)

    def refresh(self) -> None:
        """Refreshes the current page."""
        self.driver.refresh()

    def back(self) -> None:
        """Goes one step backward in the browser history."""
        self.driver.back()

    def forward(self) -> None:
        """Goes one step forward in the browser history."""
        self.driver.forward()

    def close(self) -> None:
        """Closes the current window."""
        self.driver.close()

    def quit(self) -> None:
        """Quits the driver and closes every associated window."""
        self.driver.quit()

    @property
    def current_window_handle(self) -> str:
        """The handle of the current window."""
        return self.driver.current_window_handle

    @property
    def window_handles(self) -> list[str]:
        """The handles of all windows within the current session."""
        return self.driver.window_handles

    def maximize_window(self) -> None:
        """Maximizes the current window that webdriver is using."""
        self.driver.maximize_window()

    def fullscreen_window(self) -> None:
        """Invokes the window manager-specific 'full screen' operation."""
        self.driver.fullscreen_window()

    def minimize_window(self) -> None:
        """Invokes the window manager-specific 'minimize' operation."""
        self.driver.minimize_window()

    def set_window_rect(
        self,
        x: int | None = None,
        y: int | None = None,
        width: int | None = None,
        height: int | None = None
    ) -> dict | None:
        """
        Sets the x, y coordinates of the window
        as well as height and width of the current window.
        This method is only supported for W3C compatible browsers;
        other browsers should use set_window_position and set_window_size.

        Examples:
            ::

                page.set_window_rect(x=10, y=10)
                page.set_window_rect(width=100, height=200)
                page.set_window_rect(x=10, y=10, width=100, height=200)

        """
        if all(v is None for v in (x, y, width, height)):
            self.driver.maximize_window()
            return None
        return self.driver.set_window_rect(x, y, width, height)

    def get_window_rect(self) -> dict:
        """
        Gets the x, y coordinates of the window
        as well as height and width of the current window.
        For example: `{'x': 0, 'y': 0, 'width': 500, 'height': 250}`.
        """
        rect = self.driver.get_window_rect()
        # rearragged
        return {
            'x': rect['x'],
            'y': rect['y'],
            'width': rect['width'],
            'height': rect['height']
        }

    def set_window_position(
        self,
        x: int = 0,
        y: int = 0,
        windowHandle: str = 'current'
    ) -> dict:
        """Sets the (x, y) position of the current window. (window.moveTo)"""
        return self.driver.set_window_position(x, y, windowHandle)

    def get_window_position(self, windowHandle: str = "current") -> dict:
        """
        Gets the (x, y) coordinates of the window.
        For example: `{'x': 0, 'y': 0}`.
        """
        return self.driver.get_window_position(windowHandle)

    def set_window_size(
        self,
        width: int | None = None,
        height: int | None = None,
        windowHandle: str = 'current'
    ) -> None:
        """Sets the width and height of the current window."""
        if width is None and height is None:
            self.driver.maximize_window()
        else:
            self.driver.set_window_size(width, height, windowHandle)

    def get_window_size(self, windowHandle: str = 'current') -> dict:
        """
        Gets the width and height of the current window.
        For example: `{'width': 430, 'height': 920}`.
        """
        return self.driver.get_window_size(windowHandle)

    def get_window_border(self) -> dict[str, int]:
        """
        window border: {'left': int, 'right': int, 'top': int, 'bottom': int}
        """
        rect = self.driver.get_window_rect()
        return {
            'left': int(rect['x']),
            'right': int(rect['x'] + rect['width']),
            'top': int(rect['y']),
            'bottom': int(rect['y'] + rect['height'])
        }

    def get_window_center(self) -> dict[str, int]:
        """window center: {'x': int, 'y': int}"""
        rect = self.driver.get_window_rect()
        return {
            'x': int(rect['x'] + rect['width'] / 2),
            'y': int(rect['y'] + rect['height'] / 2)
        }

    def number_of_windows_to_be(
        self,
        num_windows: int,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """An expectation for the number of windows to be a certain value."""
        try:
            return self.waiting(timeout).until(ec.number_of_windows_to_be(num_windows))
        except TimeoutException as exc:
            current_num_windows = len(self.driver.window_handles)
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for number of windows to be "{num_windows}". '
                f'The current number of windows is "{current_num_windows}".'
            )
            return self._timeout_process(status, exc, reraise)

    def new_window_is_opened(
        self,
        current_handles: list[str],
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """An expectation for the number of windows to be a certain value."""
        try:
            return self.waiting(timeout).until(ec.new_window_is_opened(current_handles))
        except TimeoutException as exc:
            current_num_windows = len(self.driver.window_handles)
            status = (
                f'Timed out waiting {self.wait.timeout} seconds for new window is opened. '
                f'The current number of windows is "{current_num_windows}".'
            )
            return self._timeout_process(status, exc, reraise)

    def print_page(self, print_options: PrintOptions | None = None) -> str:
        """Takes PDF of the current page."""
        return self.driver.print_page(print_options)

    def pin_script(self, script: str, script_key: Any | None = None) -> ScriptKey:
        """
        Store common javascript scripts to be executed later
        by a unique hashable ID.
        """
        return self.driver.pin_script(script, script_key)

    def unpin(self, script_key: ScriptKey) -> None:
        """Remove a pinned script from storage."""
        self.driver.unpin(script_key)

    @property
    def pinned_scripts(self) -> dict:
        """Get pinned scripts as dict from storage."""
        return self.driver.pinned_scripts

    @property
    def list_pinned_scripts(self) -> list[str]:
        """Get listed pinned scripts from storage."""
        return self.driver.get_pinned_scripts()

    def execute_script(self, script: str, *args) -> Any:
        """
        Synchronously Executes JavaScript in the current window or frame.

        Args:
            script: The JavaScript to execute.
            *args: Any applicable arguments for your JavaScript.

        Examples:
            ::

                page.execute_script('return document.title;')

        """
        return self.driver.execute_script(script, *args)

    def execute_async_script(self, script: str, *args) -> Any:
        """
        Asynchronously Executes JavaScript in the current window/frame.

        Args:
            script: The JavaScript to execute.
            *args: Any applicable arguments for your JavaScript.

        Example:
        ::

            script = (
                "var callback = arguments[arguments.length - 1]; "
                "window.setTimeout(function(){ callback('timeout') }, 3000);"
            )
            page.execute_async_script(script)

        """
        return self.driver.execute_async_script(script, *args)

    def perform(self) -> None:
        """
        ActionChains API.
        Performs all stored actions.
        Once called, it will execute all stored actions in page.

        Examples:
            ::

                # Perform all saved actions:
                page.element1.scroll_to_element().clicks()
                page.element2.drag_and_drop(page.element3)
                page.perform()

        """
        self.action.perform()

    def reset_actions(self) -> None:
        """
        ActionChains API.
        Clears actions that are already stored in object of Page.
        Once called, it will reset all stored actions in page.

        Examples:
            ::

                # Reset all saved actions:
                page.element1.scroll_to_element().clicks()
                page.element2.drag_and_drop(page.element3)
                page.reset_actions()

        """
        self.action.reset_actions()

    def click(self) -> Self:
        """
        ActionChains API.
        Clicks on current mouse position.

        Examples:
            ::

                page.move_by_offset(100, 200).click().perform()

        """
        self.action.click()
        return self

    def click_and_hold(self) -> Self:
        """
        ActionChains API.
        Holds down the left mouse button on current mouse position.

        Examples:
            ::

                page.move_by_offset().click_and_hold().perform()

        """
        self.action.click_and_hold()
        return self

    def context_click(self) -> Self:
        """
        ActionChains API.
        Performs a context-click (right click) on current mouse position.

        Examples:
            ::

                page.move_by_offset().context_click().perform()

        """
        self.action.context_click()
        return self

    def double_click(self) -> Self:
        """
        ActionChains API.
        Double-clicks on current mouse position.

        Examples:
            ::

                page.move_by_offset().double_click().perform()

        """
        self.action.double_click()
        return self

    def send_hotkey(self, *keys: str) -> Self:
        """
        ActionChains API.
        Sends hotkey to the page.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.send_hotkey(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        # key_down: The first to the second last key.
        for key in keys[:-1]:
            self.action.key_down(key)
        # send_keys: The last key.
        self.action.send_keys(keys[-1])
        # key_up: The second last key to the first key.
        for key in keys[-2::-1]:
            self.action.key_up(key)
        return self

    def key_down(self, key: str) -> Self:
        """
        ActionChains API.
        Sends a modifier key press only to the page, without releasing it.

        If you want to perform a combination key action, such as copying,
        it is recommended to use `send_hotkey()` instead.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.key_down(Key.CONTROL).send_keys('a').key_up(Key.CONTROL)\
                .key_down(Key.CONTROL).send_keys('c').key_up(Key.CONTROL).perform()

                # or using send_hotkey()
                page.send_hotkey(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        self.action.key_down(key)
        return self

    def key_up(self, key: str) -> Self:
        """
        ActionChains API.
        Releases a modifier key on a page.

        If you want to perform a combination key action, such as copying,
        it is recommended to use `send_hotkey()` instead.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.key_down(Key.CONTROL).send_keys('a').key_up(Key.CONTROL)\
                .key_down(Key.CONTROL).send_keys('c').key_up(Key.CONTROL).perform()

                # or using send_hotkey()
                page.send_hotkey(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        self.action.key_up(key)
        return self

    def move_by_offset(self, xoffset: int, yoffset: int) -> Self:
        """
        ActionChains API.
        Moving the mouse to an offset from current mouse position.

        Args:
            xoffset: X offset to move to, as a positive or negative integer.
            yoffset: Y offset to move to, as a positive or negative integer.

        Examples:
            ::

                page.move_by_offset(100, 200).perform()

        """
        self.action.move_by_offset(xoffset, yoffset)
        return self

    def pause(self, seconds: int | float) -> Self:
        """
        ActionChains API.
        Pause all inputs for the specified duration in seconds.
        """
        self.action.pause(seconds)
        return self

    def release(self) -> Self:
        """
        ActionChains API.
        Releasing a held mouse button on current mouse position.

        Examples:
            ::

                page.click_and_hold().release().perform()

        """
        self.action.release()
        return self

    def send_keys(self, *keys: str) -> Self:
        """
        ActionChains API.
        Sends keys to current focused position.

        Examples:
            ::

                # combine with key_down and key_up
                page.key_down(Key.CONTROL).send_keys('a').key_up(Key.CONTROL)

        """
        self.action.send_keys(*keys)
        return self

    def scroll_by_amount(self, delta_x: int, delta_y: int) -> Self:
        """
        ActionChains API.
        Scrolls by provided amounts with the origin
        in the top left corner of the viewport.

        Args:
            delta_x: Distance along X axis to scroll using the wheel.
                A negative value scrolls left.
            delta_y: Distance along Y axis to scroll using the wheel.
                A negative value scrolls up.

        Examples:
            ::

                page.scroll_by_amount(100, 200).perform()

        """
        self.action.scroll_by_amount(delta_x, delta_y)
        return self

    def scroll_from_origin(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        delta_x: int = 0,
        delta_y: int = 0,
    ) -> Self:
        """
        ActionChains API.
        Scrolls by provided amount based on a provided origin.
        The scroll origin is the upper left of the viewport plus any offsets.

        Args:
            x_offset: from origin viewport, a negative value offset left.
            y_offset: from origin viewport, a negative value offset up.
            delta_x: Distance along X axis to scroll using the wheel.
                A negative value scrolls left.
            delta_y: Distance along Y axis to scroll using the wheel.
                A negative value scrolls up.

        Raises:
            MoveTargetOutOfBoundsException: If the origin with offset is
                outside the viewport.

        Examples:
            ::

                page.scroll_from_origin(150, 100, 100, 200).perform()

        """
        scroll_origin = ScrollOrigin.from_viewport(x_offset, y_offset)
        self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        return self

    def switch_to_active_element(self) -> WE:
        """Returns the element with focus, or BODY if nothing has focus."""
        return cast(WE, self.driver.switch_to.active_element)

    def switch_to_alert(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> Alert | Literal[False]:
        """Switch to alert."""
        try:
            return self.waiting(timeout).until(ec.alert_is_present())
        except TimeoutException as exc:
            status = f'Timed out waiting {self.wait.timeout} seconds for alert to be present.'
            return self._timeout_process(status, exc, reraise)

    def switch_to_default_content(self) -> None:
        """Switch focus to the default frame."""
        self.driver.switch_to.default_content()

    def switch_to_new_window(self, type_hint: str | None) -> None:
        """
        Switches to a new top-level browsing context.
        The type hint can be one of "tab" or "window".
        If not specified the browser will automatically select it.
        """
        self.driver.switch_to.new_window(type_hint)

    def switch_to_parent_frame(self) -> None:
        """
        Switches focus to the parent context.
        If the current context is the top level browsing context,
        the context remains unchanged.
        """
        self.driver.switch_to.parent_frame()

    def switch_to_window(self, window: str | int = 0) -> None:
        """
        Switches focus to the specified window.

        Args:
            window: `str` for Window name; `int` for Window index.

        Examples:
            ::

                page.switch_to_window('main')
                page.switch_to_window(1)

        """
        if isinstance(window, int):
            window = self.driver.window_handles[window]
        self.driver.switch_to.window(window)

    def save_screenshot(self, filename: Any) -> bool:
        """
        Saves a screenshot of the current window to a PNG image file.
        Returns False if there is any IOError, else returns True.
        Use full paths in your filename.

        Args:
            filename: The **full path** you wish to save your screenshot to.
                This should end with a `.png` extension.

        Examples:
            ::

                driver.save_screenshot('/Screenshots/foo.png')

        """
        return self.driver.save_screenshot(filename)

    def switch_to_frame(self, reference: str | int) -> None:
        """
        Switches focus to the specified frame by name or index.
        If you want to switch to an iframe WebElement,
        use `xxx_page.my_element.switch_to_frame()` instead.

        Args:
            reference: The name of the window to switch to,
                or an integer representing the index.

        Examples:
            ::

                xxx_page.switch_to_frame('name')
                xxx_page.switch_to_frame(1)

        """
        self.driver.switch_to.frame(reference)

    def get_cookies(self) -> list[dict]:
        """
        Returns a set of dictionaries,
        corresponding to cookies visible in the current session.
        """
        return self.driver.get_cookies()

    def get_cookie(self, name: Any) -> dict | None:
        """
        Get a single cookie by name. Returns the cookie if found, None if not.
        """
        return self.driver.get_cookie(name)

    def add_cookie(self, cookie: dict) -> None:
        """
        Adds a cookie to your current session.

        Args:
            cookie: A dictionary object.
                Required keys: "name" and "value";
                optional keys: "path", "domain", "secure", "httpOnly",
                "expiry", "sameSite".

        Examples:
            ::

                page.add_cookie({'name': 'foo', 'value': 'bar'})
                page.add_cookie({'name': 'foo', 'value': 'bar', 'path': '/'})
                page.add_cookie({'name': 'foo', 'value': 'bar', 'path': '/', 'secure': True})
                page.add_cookie({'name': 'foo', 'value': 'bar', 'sameSite': 'Strict'})

        """
        self.driver.add_cookie(cookie)

    def add_cookies(self, cookies: list[dict]) -> None:
        """
        Adds cookies to your current session.

        Args:
            cookies: list[dict]

        Examples:
            ::

                cookies = [
                    {'name' : 'foo', 'value' : 'bar'},
                    {'name' : 'foo', 'value' : 'bar', 'path' : '/', 'secure' : True}},
                    ...
                ]
                page.add_cookies(cookies)

        """
        if not isinstance(cookies, list):
            raise TypeError('Cookies should be a list.')
        for cookie in cookies:
            if not isinstance(cookie, dict):
                raise TypeError('Each cookie in cookies should be a dict.')
            self.driver.add_cookie(cookie)

    def delete_cookie(self, name) -> None:
        """Deletes a single cookie with the given name."""
        self.driver.delete_cookie(name)

    def delete_all_cookies(self) -> None:
        """
        Delete all cookies in the scope of the session.

        Examples:
            ::

                self.delete_all_cookies()

        """
        self.driver.delete_all_cookies()

    def accept_alert(self) -> None:
        """Accept an alert."""
        self.driver.switch_to.alert.accept()

    def dismiss_alert(self) -> None:
        """Dismisses an alert."""
        self.driver.switch_to.alert.dismiss()

    @property
    def alert_text(self) -> str:
        """Gets the text of the Alert."""
        return self.driver.switch_to.alert.text

    def implicitly_wait(self, timeout: int | float = 30) -> None:
        """implicitly wait"""
        self.driver.implicitly_wait(timeout)

    def set_script_timeout(self, time_to_wait: int | float) -> None:
        """
        Set the amount of time that the script should wait during
        an execute_async_script call before throwing an error.

        Examples:
            ::

                page.set_script_timeout(30)

        """
        self.driver.set_script_timeout(time_to_wait)

    def set_page_load_timeout(self, time_to_wait: int | float) -> None:
        """
        Set the amount of time to wait for a page load to complete
        before throwing an error.

        Examples:
            ::

                page.set_page_load_timeout(30)

        """
        self.driver.set_page_load_timeout(time_to_wait)


class Page(GenericPage[WebDriver, WebElement]):
    pass
