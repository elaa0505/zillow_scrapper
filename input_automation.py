from time import sleep
from time import time
from ahk import AHK
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import JavascriptException
import numpy.random as random

def rand_sleep(sleep_time_min, sleep_time_max):
    """
    Adds some randomness to sleep times.
    :param sleep_time_max: max time to sleep
    :type sleep_time_max: float
    :param sleep_time_min: min time to sleep
    :type sleep_time_min: float
    """
    sleep_time = sleep_time_min + (sleep_time_max - sleep_time_min) *abs(random.rand())
    print(f"Sleeping for {sleep_time} secs")
    sleep(sleep_time)


def constrained_walk_2d(start, end):
    """
    Creates x, y coordinates for a constrained random walk between two points.
    :param start: x, y coordinates to start from
    :type start: tuple
    :param end: x, y coordinates to end at
    :type end: tuple
    :return:
    """
    x0, y0 = start
    xtarg, ytarg = end
    x = x0
    y = y0
    n = max([abs(xtarg-x0), abs(ytarg-y0)]) * 2
    if not (xtarg - x0) % 2 == (ytarg - y0) % 2:
        ytarg = ytarg + 1
    if not (ytarg - y0) % 2 == n % 2:
        n = n + 1
    unifs_x = random.random((n+1,))
    unifs_y = random.random((n+1,))
    res_x = [x0] * n + [xtarg]
    res_y = [y0] * n + [ytarg]
    for i in range(n - 1):
        theta_x = (1 - (xtarg - x) / (n - i)) / 2
        theta_y = (1 - (ytarg - y) / (n - i)) / 2
        if unifs_x[i] <= theta_x:
            x = x - 1
        else:
            x = x + 1
        if unifs_y[i] <= theta_y:
            y = y - 1
        else:
            y = y + 1
        res_x[i + 2] = x
        res_y[i + 2] = y
    return res_x, res_y


class InputAutomator(webdriver.Ie):

    options = webdriver.IeOptions()
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("IgnoreZoomLevel=true")

    def __init__(self, *args, **kwargs):
        kwargs['executable_path'] = 'IEDriverServer.exe'
        kwargs['options'] = self.options
        super().__init__(*args, **kwargs)
        self.maximize_window()
        self.ahk = AHK(executable_path="AutoHotkeyU64.exe")

    def adjust_coordinates(self, x, y):
        """
        Adjusts document coordinates given by selenium to screen coordinates used by AHK.
        :param x: x coordinate (pixels) in document
        :param y: y coordinate (pixels) in document
        :return: (x_adj, y_adj)
        """
        window_pos = self.get_window_position()
        browser_navigation_panel_height = self.execute_script('return window.outerHeight - window.innerHeight;')
        return x+window_pos['x'], y+window_pos['y']+browser_navigation_panel_height

    def move_rand(self, elem_type, elem_text, x_offset=0, y_offset=0):
        """
        Moves mouse to a given element using a random walk path. Does not seem to make a difference.
        :param elem_type: one of "class", "css" or "id"
        :param elem_text: value of "class", "css" or "id"
        :param x_offset: x offset from element coordinates for final mouse position
        :param y_offset: y offset from element coordinates for final mouse position
        """
        try:
            if elem_type == "class":
                out = self.find_element_by_class_name(elem_text).location
            elif elem_type == "css":
                out = self.find_element_by_css_selector(elem_text).location
            elif elem_type == "id":
                out = self.find_element_by_class_name(elem_text).location
            else:
                raise ValueError("Unknown elem_type: must be class, css or id")
        except (NoSuchElementException, TimeoutException, JavascriptException):
            return False
        x_final, y_final = self.adjust_coordinates(out['x'] + x_offset, out['y'] + y_offset)
        x0, y0 = self.ahk.mouse_position
        x_path, y_path = constrained_walk_2d((x0, y0), (x_final, y_final))
        # Reduce points
        x_path = x_path[:1] + x_path[::max([len(x_path)//50, 1])] + x_path[-1:]
        y_path = y_path[:1] + y_path[::max([len(y_path)//50, 1])] + y_path[-1:]
        for x, y in zip(x_path, y_path):
            self.ahk.run_script(f"SetMouseDelay, -1\nMouseMove, {x}, {y} , 0")
            # self.ahk.mouse_move(x=x, y=y, blocking=True, speed=0)

    def move_to(self, elem_type, elem_text, x_offset=0, y_offset=0):
        self.maximize_window()
        """
        Moves mouse to a given element directly. Passes reCAPTCHA.
        :param elem_type: one of "class", "css" or "id"
        :param elem_text: value of "class", "css" or "id"
        :param x_offset: x offset from element coordinates for final mouse position
        :param y_offset: y offset from element coordinates for final mouse position
        """
        try:
            if elem_type == "class":
                out = self.find_element_by_class_name(elem_text).location
            elif elem_type == "css":
                out = self.find_element_by_css_selector(elem_text).location
            elif elem_type == "id":
                out = self.find_element_by_class_name(elem_text).location
            else:
                raise ValueError("Unknown elem_type: must be class, css or id")
            self.ahk.mouse_move(*self.adjust_coordinates(out['x'] + x_offset, out['y'] + y_offset), speed=10,
                                blocking=True)
            return True
        except (NoSuchElementException, TimeoutException, JavascriptException):
            return False

    def click(self):
        self.ahk.click()

    def type(self, text):
        self.ahk.send_input(text)

    def scroll(self, direction, times):
        [self.ahk.mouse_wheel(direction) for i in range(times)]

    def wait_for(self, elem_type, elem_text, timeout=15):
        result = False
        start = time()
        while not result and time() - start < timeout:
            try:
                if elem_type == "class":
                    result = self.find_element_by_class_name(elem_text).is_displayed()
                elif elem_type == "css":
                    result = self.find_element_by_css_selector(elem_text).is_displayed()
                elif elem_type == "id":
                    result = self.find_element_by_class_name(elem_text).is_displayed()
                return result
            except (NoSuchElementException, TimeoutException, JavascriptException):
                result = False
            sleep(0.1)
        if not result:
            print(f"Warn: Element {elem_text} not found after {timeout} sec")
            return result

