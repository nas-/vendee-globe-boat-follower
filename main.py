from seleniumwire import webdriver
import json
import time
import os
import datetime
import threading

from utils import unpack_boats, handle_data, get_data_from_prevpoint, get_data_from_prevpoint_with_boat_data
from plot import plot
from config import CONFIG

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


def mainloop():
    driver = webdriver.Chrome('chromedriver', options=chrome_options, seleniumwire_options=options)
    try:

        driver.maximize_window()
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
        })
        """
        })

        print(f'starting run {datetime.datetime.now()}')
        if not os.path.isfile('data.json'):
            open('data.json', 'w+').write('{"BOSS":[]}')

        with open('data.json') as json_file:
            datafile = json.load(json_file)

        driver.get('https://www.marinetraffic.com/en/ais/home/centerx:-16.5/centery:-25.9/zoom:4')
        time.sleep(15)
        requests_boats = [item.response.body for item in driver.requests if
                          item.url.startswith('https://www.marinetraffic.com/getData')]
        boats = unpack_boats(requests_boats)
        if not boats:
            driver.refresh()
            time.sleep(15)
            requests_boats = [item.response.body for item in driver.requests if
                              item.url.startswith('https://www.marinetraffic.com/getData')]
            boats = unpack_boats(requests_boats)
        boats_to_retrieve = [item for item in CONFIG]
        boats_to_remove = []
        for item in boats_to_retrieve:
            if not datafile.get(item):
                datafile[item] = []
                prevpoints = []
            else:
                prevpoints = datafile[item]
            if prevpoints:
                selected_boat, boats = get_data_from_prevpoint_with_boat_data(prevpoints[-1], item, boats, datafile)
                if selected_boat:
                    boats_to_remove.append(item)

        boats_to_retrieve = list(set(boats_to_retrieve) - set(boats_to_remove))
        boats_to_remove = []
        print(f'finished_general retrieval - missing {boats_to_retrieve}')
        for item in boats_to_retrieve:
            if not datafile.get(item):
                datafile[item] = []
                prevpoints = []
            else:
                prevpoints = datafile[item]
            if prevpoints:
                lastdata = prevpoints[-1]
                a = get_data_from_prevpoint(driver, lastdata, item, datafile)
                if a:
                    boats_to_remove.append(item)

        boats_to_retrieve = list(set(boats_to_retrieve) - set(boats_to_remove))
        print(f'finished retrieval based on last position - missing {boats_to_retrieve}')

        for item in boats_to_retrieve:
            del driver.requests
            driver.get(CONFIG.get(item))
            time.sleep(20)
            requests_boats = [item.response.body for item in driver.requests if
                              item.url.startswith('https://www.marinetraffic.com/getData')]
            boats = unpack_boats(requests_boats)
            if not boats:
                print(f'{item} --> Not found :( - Trying again')
                driver.get(CONFIG.get(item))
                driver.refresh()
                time.sleep(25)
                requests_boats = [item.response.body for item in driver.requests if
                                  item.url.startswith('https://www.marinetraffic.com/getData')]
                boats = unpack_boats(requests_boats)
            if not boats:
                print(f'{item} --> Not found :( - Trying again - Definitive')
            if len(boats) == 1:
                handle_data(item, boats[0], datafile)
            else:
                print(f'{item} more than 1 value detected')

        del driver.requests
        driver.close()
        print('----------------------')
        print(f'starting run {datetime.datetime.now()}')
        for item in datafile:
            if datafile[item]:
                handle_data(item, datafile[item][-1])
        print('----------------------')
        plot(datafile)
        driver.quit()
    except Exception as e:  # Hehe this is fine
        print(e)
        driver.close()
        driver.quit()


if __name__ == "__main__":
    WAIT_TIME_SECONDS = 900
    mainloop()
    ticker = threading.Event()
    while not ticker.wait(WAIT_TIME_SECONDS):
        mainloop()
