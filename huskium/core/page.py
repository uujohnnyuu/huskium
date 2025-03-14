# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

import logging
from typing import Any, cast, Literal, Self

from selenium.common.exceptions import TimeoutException
from selenium.types import WaitExcTypes
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.fedcm.dialog import Dialog
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.remote.fedcm import FedCM
from selenium.webdriver.remote.mobile import Mobile
from selenium.webdriver.remote.script_key import ScriptKey
from selenium.webdriver.support import expected_conditions as ec

from ..logging import LogConfig, PageElementLoggerAdapter
from ..types import WebDriver, WebElement, TupleCoordinate, Coordinate
from . import ec_extension as ecex
from .wait import Wait
from .common import _Verify, Offset, Area


LOGGER = logging.getLogger(__name__)
LOGGER.addFilter(LogConfig.PREFIX_FILTER)


class Page:

    def __init__(
        self,
        driver: WebDriver,
        timeout: int | float = 30,
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
        _Verify.page(driver, timeout, reraise, remark)
        self._driver = driver
        self._timeout = timeout
        self._reraise = reraise
        self._remark = remark
        self._wait = Wait(driver, timeout)
        self._action = ActionChains(driver)
        self._logger = PageElementLoggerAdapter(LOGGER, self)

    @property
    def driver(self) -> WebDriver:
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
        ignored_exceptions: WaitExcTypes | None = None
    ) -> Wait:
        """The final WebDriverWait instance."""
        self._wait.timeout = timeout
        self._wait.ignored_exceptions = ignored_exceptions
        return self._wait

    @property
    def action(self) -> ActionChains:
        """The ActionChains instance."""
        return self._action

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

    def get_downloadable_files(self) -> dict:
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
    def mobile(self) -> Mobile:
        """Return Mobile object."""
        return self.driver.mobile

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
        ActionChains API. Performs all stored actions.
        once called, it will execute all stored actions in page.

        Examples:
            ::

                # Perform all saved actions:
                my_page.my_element1.scroll_to_element().action_click()
                my_page.my_element2.drag_and_drop(my_page.element3)
                my_page.perform()

        """
        self.action.perform()

    def reset_actions(self) -> None:
        """
        ActionChains API.
        Clears actions that are already stored in object of Page.
        once called, it will reset all stored actions in page.

        Examples:
            ::

                # Reset all saved actions:
                my_page.my_element1.scroll_to_element().action_click()
                my_page.my_element2.drag_and_drop(my_page.element3)
                my_page.reset_actions()

        """
        self.action.reset_actions()

    def click(self) -> Self:
        """ActionChains API. Clicks on current mouse position."""
        self.action.click()
        return self

    def click_and_hold(self) -> Self:
        """
        ActionChains API.
        Holds down the left mouse button on current mouse position.
        """
        self.action.click_and_hold()
        return self

    def context_click(self) -> Self:
        """
        ActionChains API.
        Performs a context-click (right click) on current mouse position.
        """
        self.action.context_click()
        return self

    def double_click(self) -> Self:
        """ActionChains API. Double-clicks on current mouse position."""
        self.action.double_click()
        return self

    def key_down(self, value: str) -> Self:
        """
        ActionChains API.
        Sends a key press only to a focused element, without releasing it.
        Should only be used with modifier keys (Control, Alt and Shift).

        Args:
            value: The modifier key to send. Values are defined in Keys class.
        """
        self.action.key_down(value)
        return self

    def key_up(self, value: str) -> Self:
        """
        ActionChains API.
        Releases a modifier key on a focused element.

        Args:
            value: The modifier key to send. Values are defined in Keys class.
        """
        self.action.key_up(value)
        return self

    def move_by_offset(self, xoffset: int, yoffset: int) -> Self:
        """
        ActionChains API.
        Moving the mouse to an offset from current mouse position.

        Args:
            xoffset: X offset to move to, as a positive or negative integer.
            yoffset: Y offset to move to, as a positive or negative integer.
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
        """
        self.action.release()
        return self

    def send_keys(self, *keys_to_send: str) -> Self:
        """
        ActionChains API.
        Sends keys to current focused element.
        """
        self.action.send_keys(*keys_to_send)
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
        """
        scroll_origin = ScrollOrigin.from_viewport(x_offset, y_offset)
        self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        return self

    def tap(
        self,
        positions: list[tuple[int, int]],
        duration: int | None = None
    ) -> Self:
        """
        Appium API.
        Taps on an particular place with up to five fingers,
        holding for a certain time.

        Args:
            positions: an array of tuples representing the x/y coordinates of
                the fingers to tap. Length can be up to five.
            duration: length of time to tap, in ms. Default value is 100 ms.

        Examples:
            ::

                page.tap([(100, 20), (100, 60), (100, 100)], 500)

        """
        self.driver.tap(positions, duration)  # type: ignore[attr-defined]
        return self

    def tap_window_center(self, duration: int | None = None) -> Self:
        """
        Tap window center coordination.

        Args:
            duration: length of time to tap, in ms. Default value is 100 ms.
        """
        window_center = [tuple(self.get_window_center().values())]
        self.driver.tap(window_center, duration)  # type: ignore[attr-defined]
        return self

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 0
    ) -> Self:
        """
        Swipe from one point to another point, for an optional duration.

        Args:
            start_x: x-coordinate at which to start
            start_y: y-coordinate at which to start
            end_x: x-coordinate at which to stop
            end_y: y-coordinate at which to stop
            duration: defines the swipe speed as time taken
                to swipe from point a to point b, in ms,
                note that default set to 250 by ActionBuilder.

        Examples:
            ::

                page.swipe(100, 100, 100, 400)

        """
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)  # type: ignore[attr-defined]
        return self

    def swipe_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        duration: int = 1000,
        times: int = 1
    ) -> Self:
        """
        Swipe from one point to another,
        allowing customization of the offset and border settings.

        Args:
            offset: Please refer to the Examples.
            area: Please refer to the Examples.
            duration: Defines the swipe speed as the time
                taken to swipe from point A to point B, in milliseconds.
                The default is set to 250 by ActionBuilder.
            times: The number of times to perform the swipe.

        Examples:
            ::

                # Swipe parameters. Refer to the Class notes for details.
                from huskium import Offset, Area

                # Swipe down.
                my_page.swipe_by(Offset.DOWN)

                # Swipe to the right.
                my_page.swipe_by(Offset.RIGHT)

                # Swipe to the upper left.
                my_page.swipe_by(Offset.UPPER_LEFT)

                # Default is swiping up.
                # offset = Offset.UP = (0.5, 0.75, 0.5, 0.25)
                # area = Area.FULL = (0.0, 0.0, 1.0, 1.0)
                # offset x: Fixed 0.5 of current window width.
                # offset y: From 0.75 to 0.25 of current window height.
                my_page.swipe_by()

                # Swipe within a swipeable range.
                area = my_page.scrollable_element.rect
                my_page.swipe_by((0.3, 0.85, 0.5, 0.35), area)

                # Swipe with customize absolute offset.
                my_page.swipe_by((250, 300, 400, 700))

                # Swipe with customize relative offset of current window size.
                my_page.swipe_by((0.3, 0.85, 0.5, 0.35))

                # Swipe with customize relative offset of customize relative area.
                # The area is relative to current window rect, for example:
                # current window rect = (10, 20, 500, 1000)
                # area = (0.1, 0.2, 0.6, 0.7)
                # area_x = 10 + 500 x 0.1 = 60
                # area_y = 20 + 1000 x 0.2 = 220
                # area_width = 500 x 0.6 = 300
                # area_height = 1000 x 0.7 = 700
                my_page.swipe_by((0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7))

                # Swipe with customize relative offset of customize absolute area.
                my_page.swipe_by((0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700))

        """
        area = self._get_area(area)
        offset = self._get_offset(offset, area)
        for _ in range(times):
            self.driver.swipe(*offset, duration)  # type: ignore[attr-defined]
        return self

    def flick(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int
    ) -> Self:
        """
        Appium API.
        Flick from one point to another point.

        Args:
            start_x: x-coordinate at which to start
            start_y: y-coordinate at which to start
            end_x: x-coordinate at which to stop
            end_y: y-coordinate at which to stop

        Examples:
            ::

                page.flick(100, 100, 100, 400)

        """
        self.driver.flick(start_x, start_y, end_x, end_y)  # type: ignore[attr-defined]
        return self

    def flick_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        times: int = 1
    ) -> Self:
        """
        Flick from one point to another,
        allowing customization of the offset and border settings.

        Args:
            offset: Please refer to the Examples.
            area: Please refer to the Examples.
            times: The number of times to perform the flick.

        Examples:
            ::

                # Swipe parameters. Refer to the Class notes for details.
                from huskium import Offset, Area

                # Flick down.
                my_page.flick_by(Offset.DOWN)

                # Flick to the right.
                my_page.flick_by(Offset.RIGHT)

                # Flick to the upper left.
                my_page.flick_by(Offset.UPPER_LEFT)

                # Default is flicking up.
                # offset = Offset.UP = (0.5, 0.5, 0.5, 0.25)
                # area = Area.FULL = (0.0, 0.0, 1.0, 1.0)
                # offset x: Fixed 0.5 of current window width.
                # offset y: From 0.75 to 0.25 of current window height.
                my_page.flick_by()

                # Flick within a swipeable range.
                area = my_page.scrollable_element.rect
                my_page.flick_by((0.3, 0.85, 0.5, 0.35), area)

                # Flick with customize absolute offset.
                my_page.flick_by((250, 300, 400, 700))

                # Flick with customize relative offset of current window size.
                my_page.target_element.flick_by((0.3, 0.85, 0.5, 0.35))

                # Flick with customize relative offset of customize relative area.
                # The area is relative to current window rect, for example:
                # current window rect = (10, 20, 500, 1000)
                # area = (0.1, 0.2, 0.6, 0.7)
                # area_x = 10 + 500 x 0.1 = 60
                # area_y = 20 + 1000 x 0.2 = 220
                # area_width = 500 x 0.6 = 300
                # area_height = 1000 x 0.7 = 700
                my_page.flick_by((0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7))

                # Flick with customize relative offset of customize absolute area.
                my_page.flick_by((0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700))

        """
        area = self._get_area(area)
        offset = self._get_offset(offset, area)
        for _ in range(times):
            self.driver.flick(*offset)  # type: ignore[attr-defined]
        return self

    def _get_coordinate(
        self,
        coordinate: Coordinate,
        name: str
    ) -> TupleCoordinate:

        # Check coordinate type.
        if not isinstance(coordinate, (dict, tuple)):
            raise TypeError(f'"{name}" should be dict or tuple.')
        if isinstance(coordinate, dict):
            coordinate = cast(TupleCoordinate, tuple(coordinate.values()))

        # Check all values in coordinate should be int or float.
        all_int = all(isinstance(c, int) for c in coordinate)
        all_float = all(isinstance(c, float) for c in coordinate)
        invalid_type = not (all_int or all_float)
        if invalid_type:
            raise TypeError(f'All "{name}" values in the tuple must be "all int" or "all float".')

        # If float, all should be (0 <= x <= 1).
        all_unit = all(0 <= abs(c) <= 1 for c in coordinate)
        invalid_float_value = all_float and not all_unit
        if invalid_float_value:
            raise ValueError(f'All "{name}" values are floats and should be between "0.0" and "1.0".')

        self.logger.debug(f'{name} origin: {coordinate}')
        return coordinate

    def _get_area(self, area: Coordinate) -> tuple[int, int, int, int]:

        area_x, area_y, area_width, area_height = self._get_coordinate(area, 'area')

        if isinstance(area_x, float):
            window_x, window_y, window_width, window_height = self.get_window_rect().values()
            area_x = int(window_x + window_width * area_x)
            area_y = int(window_y + window_height * area_y)
            area_width = int(window_width * area_width)
            area_height = int(window_height * area_height)

        area = (area_x, area_y, area_width, area_height)
        self.logger.debug(f'AREA(x, y, w, h) = {area}')
        return cast(tuple[int, int, int, int], area)

    def _get_offset(
        self,
        offset: Coordinate,
        area: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int]:

        start_x, start_y, end_x, end_y = self._get_coordinate(offset, 'offset')

        if isinstance(start_x, float):
            area_x, area_y, area_width, area_height = area
            start_x = int(area_x + area_width * start_x)
            start_y = int(area_y + area_height * start_y)
            end_x = int(area_x + area_width * end_x)
            end_y = int(area_y + area_height * end_y)

        offset = (start_x, start_y, end_x, end_y)
        self.logger.debug(f'OFFSET(sx, sy, ex, ey) = {offset}\n')
        return cast(tuple[int, int, int, int], offset)

    def draw_lines(
        self,
        dots: list[dict[str, int]] | list[tuple[int, int]],
        duration: int = 1000
    ) -> None:
        """
        Appium 2.0 API. Draw lines by dots in given order.

        Args:
            dots: A list of coordinates for the target dots,
                e.g., [{'x': 100, 'y': 100}, {'x': 200, 'y': 200}, ...].
            duration: The time taken to draw between two points.
        """
        self.logger.debug(f'origin dots: {dots}')
        if isinstance(dots, list) and all(isinstance(dot, dict) for dot in dots):
            dots = [(dot["x"], dot["y"]) for dot in dots]  # type: ignore[call-overload]
        self.logger.debug(f'tuple dots: {dots}')

        touch_input = PointerInput(interaction.POINTER_TOUCH, 'touch')
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(self.driver, mouse=touch_input)

        # Press first dot, the first action can be executed without duration.
        self.logger.debug(f'Start drawing {len(dots)} dots.')
        dot1 = dots[0]
        actions.w3c_actions.pointer_action.move_to_location(*dot1)
        actions.w3c_actions.pointer_action.pointer_down()
        self.logger.debug(f'dot1 = {dot1}')

        # Start drawing.
        if duration < 250:
            duration = 250  # Follow by ActionBuilder duration default value.
        actions.w3c_actions = ActionBuilder(self.driver, mouse=touch_input, duration=duration)
        for index, dot in enumerate(dots[1:], 2):
            actions.w3c_actions.pointer_action.move_to_location(*dot)
            self.logger.debug(f'dot{index} = {dot}')
        self.logger.debug('Drawing done.\n')

        # relase = pointer_up, lift fingers off the screen.
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def draw_gesture(
        self,
        dots: list[dict[str, int]] | list[tuple[int, int]],
        gesture: str,
        duration: int = 1000
    ) -> None:
        """
        Appium 2.0 API. Nine-box Gesture Drawing.

        Args:
            dots: Define dots in order [1, 2, 3, …, 9],
                e.g., [{'x': 100, 'y': 100}, {'x': 200, 'y': 100}, ...].
                If dots are elements, use `page.elements.centers`.
            gesture: A string containing the actual positions of the nine dots,
                such as '1235789' for drawing a Z shape.
        """
        self.logger.debug(f'origin dots: {dots}')
        if isinstance(dots, list) and all(isinstance(dot, dict) for dot in dots):
            dots = [(dot["x"], dot["y"]) for dot in dots]  # type: ignore[call-overload]
        self.logger.debug(f'tuple dots: {dots}')
        self.logger.debug(f'gesture: {gesture}')

        touch_input = PointerInput(interaction.POINTER_TOUCH, 'touch')
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(self.driver, mouse=touch_input)

        # Press first dot, the first action can be executed without duration.
        self.logger.debug(f'Start drawing {len(gesture)} dots.')
        indexes = [(int(i) - 1) for i in gesture]
        press = indexes[0]
        dot1 = dots[press]
        actions.w3c_actions.pointer_action.move_to_location(*dot1)
        actions.w3c_actions.pointer_action.pointer_down()
        self.logger.debug(f'dot1 = {dot1}')

        # Start drawing.
        if duration < 250:
            duration = 250  # Follow by ActionBuilder duration default value.
        actions.w3c_actions = ActionBuilder(self.driver, mouse=touch_input, duration=duration)
        for index, draw in enumerate(indexes[1:], 2):
            dot = dots[draw]
            actions.w3c_actions.pointer_action.move_to_location(*dot)
            self.logger.debug(f'dot{index} = {dot}')
        self.logger.debug('Drawing done.\n')

        # relase = pointerup, lift fingers off the screen.
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def switch_to_active_element(self) -> WebElement:
        """Returns the element with focus, or BODY if nothing has focus."""
        return self.driver.switch_to.active_element

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

    def get_status(self) -> dict:
        """
        Appium API. Get the Appium server status.

        Examples:
            ::

                page.get_status()

        """
        return self.driver.get_status()  # type: ignore[attr-defined]

    @property
    def contexts(self) -> Any | list[str]:
        """Appium API. Get current all contexts."""
        return self.driver.contexts  # type: ignore[attr-defined]

    def switch_to_context(self, context) -> Self:
        """Appium API. Switch to NATIVE_APP or WEBVIEW."""
        self.driver.switch_to.context(context)  # type: ignore[attr-defined]
        return self

    def switch_to_webview(
        self,
        switch: bool = True,
        index: int = -1,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[str] | Literal[False]:
        """
        Appium API.
        Wait for the webview is present and determine whether switch to it.

        Args:
            switch: If True, switches to WEBVIEW when it becomes available.
            index: Defaulting to `-1` which targets the latest WEBVIEW.
            timeout: The timeout duration in seconds for explicit wait.
            reraise: If True, re-raises a TimeoutException upon timeout;
                if False, returns False upon timeout.

        Returns:
            (list | False):
                `list` for `['NATIVE_APP', 'WEBVIEW_XXX', ...]`;
                `False` for no any WEBVIEW in contexts.
        """
        try:
            return self.waiting(timeout).until(ecex.webview_is_present(switch, index))
        except TimeoutException as exc:
            status = f'Timed out waiting {self.wait.timeout} seconds for WEBVIEW to be present.'
            return self._timeout_process(status, exc, reraise)

    def switch_to_app(self) -> Any | str:
        """
        Appium API. Switch to native app.
        Return the current context after judging whether to switch.
        """
        if self.driver.current_context != 'NATIVE_APP':  # type: ignore[attr-defined]
            self.driver.switch_to.context('NATIVE_APP')  # type: ignore[attr-defined]
        return self.driver.current_context  # type: ignore[attr-defined]

    def terminate_app(self, app_id: str, **options: Any) -> bool:
        """
        Appium API. Terminates the application if it is running.

        Args:
            app_id: the application id to be terminates.
            **options: timeout (int), [Android only]
                how much time to wait for the uninstall to complete.
                500ms by default.

        Returns:
            bool:
                `True` if the app has been successfully terminated.
        """
        return self.driver.terminate_app(app_id, **options)  # type: ignore[attr-defined]

    def activate_app(self, app_id: str) -> Self:
        """
        Appium API.
        Activates the application if it is not running
        or is running in the background.

        Args:
            app_id: The application id to be activated.
        """
        self.driver.activate_app(app_id)  # type: ignore[attr-defined]
        return self

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

    def switch_to_flutter(self) -> Self:
        """Appium API. Switch to flutter app."""
        if self.driver.current_context != "FLUTTER":  # type: ignore[attr-defined]
            self.driver.switch_to.context('FLUTTER')  # type: ignore[attr-defined]
        return self

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
