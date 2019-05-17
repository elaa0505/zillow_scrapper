# zillow_scrapper

Quick webscrapper created to practice Selenium & to collect a small dataset for a data science class.

Using Selenium & ChromeDriver (similar to here) I was getting flagged as a bot pretty quickly. Switching to IE helped.

But the real icing on the cake: you can pass as completely human if you use AutoHotkey to do the mouse movement, clicking, etc. See this reCAPTCHA demo: https://github.com/adriangb/zillow_scrapper/blob/master/beating%20captcha.mp4

I made a thin wrapper around Selenium webdriver that integrates autohotkey functionality, making it easy to move to and click on elements.

