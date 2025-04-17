# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import Any, cast, Self

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement

from ..selenium import ELEMENT_REFERENCE_EXCEPTIONS, GenericElement
from ..common import Area, Offset
from ..types import Coordinate
from .by import ByAttr
from .page import Page


class Element(GenericElement[WebDriver, WebElement]):

    page: Page

    def _verify_by(self, by: Any) -> None:
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.appium import By).')

    def _verify_descriptor_instance(self, instance: Any) -> None:
        if not isinstance(instance, Page):
            raise TypeError(
                f'"appium Element" must be used in "appium Page", got {type(instance).__name__}'
            )

    def _verify_descriptor_owner(self, owner: Any) -> None:
        if not issubclass(owner, Page):
            raise TypeError(
                f'"appium Element" must be used in "appium Page", got {type(owner).__name__}'
            )

    def _verify_descriptor_value(self, value: Any) -> None:
        if not isinstance(value, Element):
            raise TypeError(f'Assigned value must be "appium Element", got {type(value).__name__}.')

    def is_viewable(self, timeout: int | float | None = None) -> bool:
        """
        Appium API.
        This method is typically used with swipe-based element searching.
        Checks if the current element is visible on the mobile screen.
        """
        element = self.wait_present(timeout, False)
        result = bool(element and element.is_displayed())
        self._cache_visible_element(element, result)
        return result

    @property
    def location_in_view(self) -> dict[str, int]:
        """
        Appium API.
        Retrieve the location (coordination) of the element
        relative to the view when it is present.
        For example: `{'x': 100, 'y': 250}`.
        """
        try:
            return self.present_caching.location_in_view
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.location_in_view

    def tap(self, duration: int | None = None) -> Self:
        """
        Appium API.
        Tap the center location of the element when it is present.
        This method can be used when `click()` fails.

        Args:
            duration: Length of time to tap, in ms.
        """
        center = cast(list[tuple[int, int]], [tuple(self.center.values())])
        self.driver.tap(center, duration)
        return self

    def app_scroll(self, target: Element, duration: int | None = None) -> Self:
        """
        Appium API. Scrolls from one element to another.

        Args:
            target: The element to scroll to (center of element).
            duration: Defines speed of scroll action when moving to target.
                Default is 600 ms for W3C spec.
        """
        try:
            self.driver.scroll(self.present_caching, target.present_caching, duration)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.driver.scroll(self.present_element, target.present_element, duration)
        return self

    def app_drag_and_drop(self, target: Element, pause: float | None = None) -> Self:
        """
        Appium API. Drag the origin element to the destination element.

        Args:
            target: The element to drag to.
            pause: How long the action pauses before moving after
                the tap and hold in seconds.
        """
        try:
            self.driver.drag_and_drop(self.present_caching, target.present_caching, pause)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.driver.drag_and_drop(self.present_element, target.present_element, pause)
        return self

    def swipe_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        timeout: int | float = 3,
        max_round: int = 10,
        max_align: int = 2,
        min_xycmp: int = 100,
        duration: int = 1000
    ) -> Self:
        """
        Appium API.
        For native iOS and Android apps, it swipes the screen until
        the element becomes visible within the specified area.

        Args:
            offset: `(start_x, start_y, end_x, end_y)` or `(sx, sy, ex, ey)`.
            area: `(x, y, width, height)` or `(x, y, w, h)`.
            timeout: Maximum wait time in seconds.
            max_round: Maximum number of swipe attempts.
            max_align: Maximum attempts to align all borders of the element
                within the area (view) border.
            min_xycmp: Minimum x and y components to avoid being mistaken
                as a click **during alignment**.
                Should be considered along with `duration`.
            duration: Swipe and alignment duration in milliseconds.
                If too short, it may be mistaken as a click.
                Should be considered along with `offset` and `min_xycmp`.

        Examples:
            ::

                from huskium import Offset, Area

                # Swipe by default.
                # Offset.UP (sx, sy, ex, ey) = (0.5, 0.75, 0.5, 0.25)
                # Area.FULL (x, y, w, h) = (0.0, 0.0, 1.0, 1.0)
                # offset x: Fixed 0.5 of current window width.
                # offset y: From 0.75 to 0.25 of current window height.
                my_page.target_element.swipe_by()

                # Swipe to the direction using Offset.
                my_page.target_element.swipe_by(Offset.DOWN)
                my_page.target_element.swipe_by(Offset.UPPER_LEFT)

                # Swipe with customize relative offset.
                my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35))

                # Swipe within a swipeable range.
                # Get the absolute area rect using the scrollable element.
                area = my_page.scrollable_element.rect
                my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35), area)

                # Swipe with customize absolute offset.
                my_page.target_element.swipe_by((250, 300, 400, 700))

                # Swipe with customize relative offset of customize relative area.
                # The area is relative to current window rect, for example:
                # current window rect = (10, 20, 500, 1000)
                # area = (0.1, 0.2, 0.6, 0.7)
                # area_x = 10 + 500 x 0.1 = 60
                # area_y = 20 + 1000 x 0.2 = 220
                # area_width = 500 x 0.6 = 300
                # area_height = 1000 x 0.7 = 700
                my_page.target_element.swipe_by(
                    (0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7)
                )

                # Swipe with customize relative offset of customize absolute area.
                my_page.target_element.swipe_by(
                    (0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700)
                )

        """
        area = self.page._get_area(area)
        offset = self.page._get_offset(offset, area)
        self._swipe_by(offset, timeout, max_round, duration)
        self._align_by(area, max_align, min_xycmp, duration)
        return self

    def flick_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        timeout: int | float = 3,
        max_round: int = 10,
        max_align: int = 2,
        min_xycmp: int = 100,
        duration: int = 1000
    ) -> Self:
        """
        Appium API.
        For native iOS and Android apps, it flicks the screen until
        the element becomes visible within the specified area.

        Args:
            offset: `(start_x, start_y, end_x, end_y)` or `(sx, sy, ex, ey)`.
            area: `(x, y, width, height)` or `(x, y, w, h)`.
            timeout: Maximum wait time in seconds.
            max_round: Maximum number of flick attempts.
            max_align: Maximum attempts to align all borders of the element
                within the area (view) border.
            min_xycmp: Minimum x and y components to avoid being mistaken
                as a click **during alignment**.
                Should be considered along with `duration`.
            duration: **Alignment** (not flick) duration in milliseconds.
                If too short, it may be mistaken as a click.
                Should be considered along with `min_xycmp`.

        Examples:
            ::

                from huskium import Offset, Area

                # Filck by default.
                # Offset.UP (sx, sy, ex, ey) = (0.5, 0.75, 0.5, 0.25)
                # Area.FULL (x, y, w, h) = (0.0, 0.0, 1.0, 1.0)
                # offset x: Fixed 0.5 of current window width.
                # offset y: From 0.75 to 0.25 of current window height.
                my_page.target_element.filck_by()

                # Filck to the direction using Offset.
                my_page.target_element.filck_by(Offset.DOWN)
                my_page.target_element.filck_by(Offset.UPPER_LEFT)

                # Filck with customize relative offset.
                my_page.target_element.filck_by((0.3, 0.85, 0.5, 0.35))

                # Filck within a filckable range.
                # Get the absolute area rect using the scrollable element.
                area = my_page.scrollable_element.rect
                my_page.target_element.filck_by((0.3, 0.85, 0.5, 0.35), area)

                # Filck with customize absolute offset.
                my_page.target_element.filck_by((250, 300, 400, 700))

                # Filck with customize relative offset of customize relative area.
                # The area is relative to current window rect, for example:
                # current window rect = (10, 20, 500, 1000)
                # area = (0.1, 0.2, 0.6, 0.7)
                # area_x = 10 + 500 x 0.1 = 60
                # area_y = 20 + 1000 x 0.2 = 220
                # area_width = 500 x 0.6 = 300
                # area_height = 1000 x 0.7 = 700
                my_page.target_element.filck_by(
                    (0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7)
                )

                # Filck with customize relative offset of customize absolute area.
                my_page.target_element.filck_by(
                    (0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700)
                )

        """
        area = self.page._get_area(area)
        offset = self.page._get_offset(offset, area)
        self._flick_by(offset, timeout, max_round)
        self._align_by(area, max_align, min_xycmp, duration)
        return self

    def _swipe_by(
        self,
        offset: tuple[int, int, int, int],
        timeout: int | float,
        max_round: int,
        duration: int
    ) -> int | None:
        if not max_round:
            self.logger.warning(f'For max_round is {max_round}, no swiping performed.')
            return None
        self.logger.debug('Start swiping.')
        round = 0
        while not self.is_viewable(timeout):
            if round == max_round:
                self.logger.warning(f'Stop swiping. Element remains not viewable after max {max_round} rounds.\n')
                return round
            self.driver.swipe(*offset, duration)
            round += 1
            self.logger.debug(f'Swiping round {round} done.\n')
        self.logger.debug(f'Stop swiping. Element is viewable after {round} rounds.\n')
        return round

    def _flick_by(
        self,
        offset: tuple[int, int, int, int],
        timeout: int | float,
        max_round: int
    ) -> int | None:
        if not max_round:
            self.logger.warning(f'For max_round is {max_round}, no flicking performed.')
            return None
        self.logger.debug('Start flicking.')
        round = 0
        while not self.is_viewable(timeout):
            if round == max_round:
                self.logger.warning(
                    f'Stop flicking. Element remains not viewable after max {max_round} rounds.\n')
                return round
            self.driver.flick(*offset)
            round += 1
            self.logger.debug(f'Flicking round {round} done.\n')
        self.logger.debug(f'Stop flicking. Element is viewable after {round} rounds.\n')
        return round

    def _align_by(
        self,
        area: tuple[int, int, int, int],
        max_align: int,
        min_xycmp: int,
        duration: int
    ) -> int | None:

        if not max_align:
            self.logger.debug(f'For max_align is {max_align}, no alignment performed.')
            return None

        self.logger.debug('Start aligning.')

        # Area critical points
        al, at, aw, ah = area  # rect
        ar, ab = (al + aw), (at + ah)  # right, bottom
        ahw, ahh = int(aw / 2), int(ah / 2)  # half_width, half_height
        acx, acy = (al + ahw), (at + ahh)  # center_x, center_y
        area_border = (al, ar, at, ab)
        self.logger.debug(f'AREA(l, r, t, b) = {area_border}')
        area_halfwh = (ahw, ahh)
        self.logger.debug(f'AREA(hw, hh) = {area_halfwh}')
        area_center = (acx, acy)
        self.logger.debug(f'AREA(cx, cy) = {area_center}')

        round = 0
        while (aligned_offset := self._get_aligned_offset(area_border, area_halfwh, area_center, min_xycmp)):
            if round == max_align:
                self.logger.debug(f'Stop aligning after max {max_align} rounds.\n')
                return round
            self.driver.swipe(*aligned_offset, duration)
            round += 1
            self.logger.debug(f'Aligning round {round} done.\n')
        self.logger.debug(f'Stop aligning after {round} round.\n')
        return round

    def _get_aligned_offset(
        self,
        area_border: tuple[int, int, int, int],
        area_halfwh: tuple[int, int],
        area_center: tuple[int, int],
        min_xycmp: int,
    ) -> tuple[int, int, int, int] | None:

        # area critical points
        al, ar, at, ab = area_border
        max_xcmp, max_ycmp = area_halfwh
        oex, oey = acx, acy = area_center

        # element border
        element_border = el, er, et, eb = tuple(self.border.values())
        self.logger.debug(f'ELEMENT(l, r, t, b) = {(element_border)}')

        # delta = (area - element)
        delta_border = dl, dr, dt, db = (al - el), (ar - er), (at - et), (ab - eb)
        self.logger.debug(f'DELTA(l, r, t, b) = {delta_border}')

        # align action = (l>0, r<0, t>0, b<0)
        align = align_dl, align_dr, align_dt, align_db = (dl > 0), (dr < 0), (dt > 0), (db < 0)
        self.logger.debug(f'ALIGN(l>0, r<0, t>0, b<0) = {align}')

        # update delta with min_distance
        if align_dl:
            dl = max(min(dl, max_xcmp), min_xycmp)  # max_xcmp >= dl >= min_xycmp > 0
            oex = acx + dl
            self.logger.debug(f'O(ex) = A(cx) + D{[min_xycmp, max_xcmp]}(l) = {acx} + {dl} = {oex}')
        if align_dr:
            dr = min(max(dr, -max_xcmp), -min_xycmp)  # 0 > -min_xycmp >= dr >= -max_xcmp
            oex = acx + dr
            self.logger.debug(f'O(ex) = A(cx) + D{[-min_xycmp, -max_xcmp]}(r) = {acx} + {dr} = {oex}')
        if align_dt:
            dt = max(min(dt, max_ycmp), min_xycmp)  # max_ycmp >= dt >= min_xycmp > 0
            oey = acy + dt
            self.logger.debug(f'O(ey) = A(cy) + D{[min_xycmp, max_ycmp]}(t) = {acy} + {dt} = {oey}')
        if align_db:
            db = min(max(db, -max_ycmp), -min_xycmp)  # 0 > -min_xycmp >= db >= -max_ycmp
            oey = acy + db
            self.logger.debug(f'O(ey) = A(cy) + D{[-min_xycmp, -max_ycmp]}(b) = {acy} + {db} = {oey}')

        # check if adjustment is needed
        if (oex, oey) == area_center:
            self.logger.debug('All the element border is in Area, no alignment required.')
            return None
        offset = (acx, acy, oex, oey)
        self.logger.debug(f'OFFSET(sx, sy, ex, ey) = {offset}')
        return offset
