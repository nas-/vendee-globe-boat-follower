from seleniumwire import webdriver
from selenium.common.exceptions import TimeoutException
import time
import logging
import src.utils

logger = logging.getLogger('Main')


# noinspection PyMissingConstructor
class ScrapeSelenium(webdriver.Chrome):
    def __init__(self, *args, **kwargs):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('connection_keep_alive=False')
        chrome_options.add_argument('disable-blink-features=AutomationControlled')
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0")

        options = {
            'backend': 'mitmproxy',
            'disable_encoding': True  # Tell the server not to compress the response
            # Set the backend to mitmproxy
        }

        self.driver = webdriver.Chrome('chromedriver', options=chrome_options, seleniumwire_options=options)

        self.driver.maximize_window()
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
        Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
        })
        """
        })

    def request_marinetrafic_url(self, url, **kwargs):
        del self.driver.requests
        try:
            self.driver.get(url)
        except TimeoutException:
            logger.critical(f'Timeout exception. Cannot get data')
            return
        time.sleep(15)
        requests_boats = src.utils.req_boat(self.driver.requests)
        return src.utils.unpack_boats(requests_boats)

    def cleanup(self):
        self.driver.close()
        self.driver.quit()
