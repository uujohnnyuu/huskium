# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import Any, cast, Literal, Self

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement

from ..common import Area, Offset
from ..selenium import GenericPage
from ..types import Coordinate, TupleCoordinate
from .ecex import ECEX


class Page(GenericPage[WebDriver, WebElement]):

    def _verify_driver(self, driver: Any) -> None:
        if not isinstance(driver, WebDriver):
            raise TypeError(f'The "driver" must be "appium WebDriver", got {type(driver).__name__}.')

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
        self.driver.tap(positions, duration)
        return self

    def tap_window_center(self, duration: int | None = None) -> Self:
        """
        Tap window center coordination.

        Args:
            duration: length of time to tap, in ms. Default value is 100 ms.
        """
        center = cast(list[tuple[int, int]], [tuple(self.get_window_center().values())])
        self.driver.tap(center, duration)
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
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
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
            self.driver.swipe(*offset, duration)
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
        self.driver.flick(start_x, start_y, end_x, end_y)
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
            self.driver.flick(*offset)
        return self

    def _get_coordinate(
        self,
        coordinate: Coordinate,
        name: str
    ) -> TupleCoordinate:

        # Check coordinate type.
        if not isinstance(coordinate, dict | tuple):
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
                e.g., [{'x': 100, 'y': 100}, {'x': 200, 'y': 300}, ...];
                or [(100, 100), (200, 300), ...].
            duration: The time taken to draw between two points.
        """
        self.logger.debug(f'origin dots: {dots}')
        if isinstance(dots, list) and all(isinstance(dot, dict) for dot in dots):
            dots = [(dot["x"], dot["y"]) for dot in cast(list[dict[str, int]], dots)]
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
                e.g., [{'x': 100, 'y': 100}, {'x': 200, 'y': 100}, ...];
                or [(100, 100), (200, 100), ...].
                If dots are elements, use `page.elements.centers`.
            gesture: A string containing the actual positions of the nine dots,
                such as '1235789' for drawing a Z shape.
        """
        self.logger.debug(f'origin dots: {dots}')
        if isinstance(dots, list) and all(isinstance(dot, dict) for dot in dots):
            dots = [(dot["x"], dot["y"]) for dot in cast(list[dict[str, int]], dots)]
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

    def get_status(self) -> dict:
        """
        Appium API. Get the Appium server status.

        Examples:
            ::

                page.get_status()

        """
        return self.driver.get_status()

    @property
    def context(self) -> str:
        """Appium API. Get current context."""
        return self.driver.context

    @property
    def contexts(self) -> list[str]:
        """Appium API. Get current all contexts."""
        return self.driver.contexts

    def switch_to_context(self, context: str | None) -> str:
        """
        Appium API.
        Sets the context for the current session.
        Passing None is equal to switching to native context.
        Returns the current context.
        """
        self.driver.switch_to.context(context)
        return self.driver.context

    def switch_to_webview(
        self,
        switch: bool = True,
        index: int = -1,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> str | Literal[False]:
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
            (str | False):
                `str` for current context;
                `False` for no any WEBVIEW in contexts.
        """
        try:
            return self.waiting(timeout).until(ECEX.webview_is_present(switch, index))
        except TimeoutException as exc:
            status = f'Timed out waiting {self.wait.timeout} seconds for WEBVIEW to be present.'
            return self._timeout_process(status, exc, reraise)

    def switch_to_app(self) -> str:
        """
        Appium API. Switch to native app.
        Return the current context after judging whether to switch.
        """
        self.driver.switch_to.context('NATIVE_APP')
        return self.driver.context

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
        return self.driver.terminate_app(app_id, **options)

    def activate_app(self, app_id: str) -> Self:
        """
        Appium API.
        Activates the application if it is not running
        or is running in the background.

        Args:
            app_id: The application id to be activated.
        """
        self.driver.activate_app(app_id)
        return self

    def switch_to_flutter(self) -> str:
        """Appium API. Switch to flutter app."""
        self.driver.switch_to.context('FLUTTER')
        return self.driver.context
