"""
Simple automated passing of reCAPTCHA. Useful for small webscrapping projects.
Tested with 100% success rate* using:
1) IE11 webdriver
2) Log into google account

* In situations where it would pass a human.
 If you try to pass 20+ in a few minutes it will fail you (even if you manually try to click).
"""

from input_automation import InputAutomator
from input_automation import rand_sleep


with InputAutomator() as driver:

    driver.get('https://www.google.com/recaptcha/api2/demo')

    driver.wait_for("class", "g-recaptcha")

    rand_sleep(2, 4)

    driver.move_to("class", "g-recaptcha", x_offset=35, y_offset=25)

    rand_sleep(.1, 1.2)

    driver.click()

    print("Done")
