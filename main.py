import datetime
import json
import os
import threading
import time
import argparse
import logging

from seleniumwire import webdriver
from selenium.common.exceptions import TimeoutException

from config import CONFIG
from src.plot import plot
import src.utils
from src.geojson_creator import create_geojson

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
# chrome_options.add_argument(r'load-extension=C:\Extension\1.30.6_0') #Loads Adblock
chrome_options.add_argument('connection_keep_alive=False')
chrome_options.add_argument('disable-blink-features=AutomationControlled')
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0")
# prefs = {"profile.managed_default_content_settings.images": 2}
# chrome_options.add_experimental_option("prefs", prefs)

options = {
    'backend': 'mitmproxy',
    'disable_encoding': True  # Tell the server not to compress the response
    # Set the backend to mitmproxy
}


def mainloop(refresh=None, debug=None):
    """

    :param refresh: If true, use only links in config.py.
    :param debug:   Set loglevel to debug
    :return: None
    """
    if debug:
        logger = logging.getLogger('Main')
        logger.setLevel(logging.DEBUG)
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.DEBUG)
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)
        logger.debug('Setting level to debug')
    else:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)
        logger.info('Setting level to info')
    driver = webdriver.Chrome('chromedriver', options=chrome_options, seleniumwire_options=options)
    # try:
    logger.debug(f"{refresh}")
    driver.maximize_window()
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
    Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
    })
    """
    })

    logger.info(f'starting run {datetime.datetime.now()}')
    if not os.path.isfile('src/data.json'):
        open('src/data.json', 'w+').write('{"BOSS":[]}')

    with open('src/data.json') as json_file:
        datafile = json.load(json_file)
    boats_to_retrieve = [item for item in CONFIG]
    boats_to_remove = []

    if not refresh:
        # Higher zooms give better results. Lower zooms cover more maparea.
        try:
            driver.get('https://www.marinetraffic.com/en/ais/home/centerx:22.8/centery:-41.3/zoom:6')
        except TimeoutException:
            logger.critical(f'Timeout exception. Cannot get data')
            return
        time.sleep(15)
        requests_boats = src.utils.req_boat(driver.requests)
        boats = src.utils.unpack_boats(requests_boats)
        if not boats:
            driver.refresh()
            time.sleep(15)
            requests_boats = src.utils.req_boat(driver.requests)
            boats = src.utils.unpack_boats(requests_boats)

        for item in boats_to_retrieve:
            if not datafile.get(item):
                datafile[item] = []
                prevpoints = []
            else:
                prevpoints = datafile[item]
            if prevpoints:
                selected_boat, boats = src.utils.get_data_from_prevpoint_with_boat_data(prevpoints[-1], item, boats,
                                                                                        datafile)
                if selected_boat:
                    boats_to_remove.append(item)

        boats_to_retrieve = list(set(boats_to_retrieve) - set(boats_to_remove))
        boats_to_remove = []
        logger.info(f'finished_general retrieval - missing {boats_to_retrieve}')

        for item in boats_to_retrieve:
            if not datafile.get(item):
                datafile[item] = []
                prevpoints = []
            else:
                prevpoints = datafile[item]
            if prevpoints:
                lastdata = prevpoints[-1]
                a, b = src.utils.get_data_from_prevpoint(driver, lastdata, item, datafile)
                if a:
                    boats_to_remove.append(item)

        boats_to_retrieve = list(set(boats_to_retrieve) - set(boats_to_remove))
        logger.info(f'finished retrieval based on last position - missing {boats_to_retrieve}')

    for item in boats_to_retrieve:
        del driver.requests
        try:
            driver.get(CONFIG.get(item))
        except TimeoutException:
            logger.critical(f'Timeout exception. Cannot get data')
            return
        time.sleep(20)
        requests_boats = src.utils.req_boat(driver.requests)
        boats = src.utils.unpack_boats(requests_boats)
        if not boats:
            logger.debug(f'{item} --> Not found :( - Trying again')
            try:
                driver.get(CONFIG.get(item))
            except TimeoutException:
                logger.critical(f'Timeout exception. Cannot get data')
                return
            driver.refresh()
            time.sleep(25)
            requests_boats = src.utils.req_boat(driver.requests)
            boats = src.utils.unpack_boats(requests_boats)
        if not boats:
            logger.debug(f'{item} --> Not found :( - Trying again - Definitive')
        if len(boats) == 1:
            print(src.utils.handle_data(item, boats[0]))
            try:
                if boats[0] == datafile.get(item)[-1]:
                    logger.info(f'{item} Position is the same as last recorded.')
                    continue
            except IndexError:
                src.utils.save_data(item, boats[0], datafile)
        else:
            logger.info(f'{item} more than 1 value detected')

    del driver.requests
    driver.close()
    print('----------------------')
    print(f'starting run {datetime.datetime.now()}')
    for item in datafile:
        if datafile[item]:
            print(src.utils.handle_data(item, datafile[item][-1]))
    print('----------------------')
    plot(datafile)
    create_geojson(datafile)
    driver.quit()
    # except Exception as e:  # Hehe this is fine
    #     print(e)
    #     driver.close()
    #     driver.quit()


if __name__ == "__main__":
    WAIT_TIME_SECONDS = 900

    parser = argparse.ArgumentParser(description='Starts the process.')
    parser.add_argument('-r', '--refresh', action='store_true', help="Uses only the position specified in config")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug purposes")
    args = parser.parse_args()
    args2 = {'refresh': args.refresh, 'debug': args.debug}

    mainloop(**args2)
    ticker = threading.Event()
    while not ticker.wait(WAIT_TIME_SECONDS):
        mainloop()
