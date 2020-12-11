import datetime
import json
import os
import threading
import argparse
import logging
import re

from config import CONFIG
from src.plot import plot
import src.utils
from src.geojson_creator import create_geojson

from backends.cfscrape_requests import Scrape
from backends.seleniumwire_requests import ScrapeSelenium


def mainloop(refresh=None, selenium=None) -> None:
    """
    :param refresh: If true, use only links in config.py.
    :param selenium: Uses legacy selenium backend
    """

    marinetraffic_instance = ScrapeSelenium() if selenium else Scrape()

    logger.info(f'starting run {datetime.datetime.now()}')
    if not os.path.isfile('src/data.json'):
        open('src/data.json', 'w+').write('{"BOSS":[]}')

    with open('src/data.json') as json_file:
        datafile = json.load(json_file)
    boats_to_retrieve = [item for item in CONFIG]
    boats_to_remove = []

    if not refresh:
        # Higher zooms give better results. Lower zooms cover more maparea.
        boats = marinetraffic_instance.request_marinetrafic_url(
            'https://www.marinetraffic.com/en/ais/home/centerx:80.0/centery:-39.6/zoom:6', do_req=True)
        if not boats:
            boats = marinetraffic_instance.request_marinetrafic_url(
                'https://www.marinetraffic.com/en/ais/home/centerx:80.0/centery:-39.6/zoom:6', do_req=True)

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

                a, b = src.utils.get_data_from_prevpoint(marinetraffic_instance, lastdata, item,
                                                         datafile)
                if a:
                    boats_to_remove.append(item)

        boats_to_retrieve = list(set(boats_to_retrieve) - set(boats_to_remove))
        logger.info(f'finished retrieval based on last position - missing {boats_to_retrieve}')

    pattern = r'centerx:([-\d.]{4,7}).+centery:([-\d.]{4,7}).zoom:(\d{1,2})'
    for item in boats_to_retrieve:
        longitudex, latitudey, zoom = re.findall(pattern, CONFIG.get(item))[0]
        longitudex = float(longitudex)
        latitudey = float(latitudey)
        boats = marinetraffic_instance.request_marinetrafic_url(CONFIG.get(item), do_req=True)
        if not boats:
            logger.debug(f'{item} --> Not found :( - Trying again')
            boats = marinetraffic_instance.request_marinetrafic_url(CONFIG.get(item), do_req=True)
        _distances = [src.utils.EarthFunctions.calculate_distance((float(boat.get('LAT')), float(boat.get('LON'))),
                                                                  (latitudey, longitudex)) for boat in boats]
        _mostProbableBoat = src.utils.search_for_duplicate(_distances, boats, datafile, item)
        if not _mostProbableBoat:
            continue
        if not boats:
            logger.debug(f'{item} --> Not found :(. Skipping')
        elif len(boats) == 1:
            # TODO check if same position.
            print(src.utils.handle_data(item, boats[0]))
            try:
                if boats[0] == datafile.get(item)[-1]:
                    logger.info(f'{item} Position is the same as last recorded.')
                    continue
                else:
                    src.utils.save_data(item, boats[0], datafile)
            except (IndexError, TypeError):
                src.utils.save_data(item, boats[0], datafile)
        else:
            logger.info(f'{item} more than 1 value detected. Picking closest to the center')
            distances = [src.utils.EarthFunctions.calculate_distance((float(boat.get('LAT')), float(boat.get('LON'))),
                                                                     (latitudey, longitudex)) for boat in boats]
            mostProbableBoat = src.utils.search_for_duplicate(distances, boats, datafile, item)
            # todo check if same position
            if mostProbableBoat:
                print('aaaaaaaaaa')
                print(src.utils.handle_data(item, mostProbableBoat))
                src.utils.save_data(item, mostProbableBoat, datafile)
            else:
                print('DUpolicata')

    marinetraffic_instance.cleanup()

    print('----------------------')
    print(f'starting run {datetime.datetime.now()}')
    for item in datafile:
        if datafile[item]:
            print(src.utils.handle_data(item, datafile[item][-1]))
    print('----------------------')
    plot(datafile, 25)
    create_geojson(datafile)


if __name__ == "__main__":
    WAIT_TIME_SECONDS = 60

    parser = argparse.ArgumentParser(description='Starts the process.')
    parser.add_argument('-r', '--refresh', action='store_true', help="Uses only the position specified in config")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug purposes")
    parser.add_argument('-sel', '--selenium', action='store_true', help="Force use of legacy selenium backend")
    args = parser.parse_args()

    if args.debug:
        logger = logging.getLogger('Main')
        logger.setLevel(logging.DEBUG)
        logger.debug('Setting level to debug')
    else:
        logger = logging.getLogger('Main')
        logger.setLevel(logging.INFO)
        logger.info('Setting level to info')

    args2 = {'refresh': args.refresh, 'selenium': args.selenium}
    logger.debug(f'using selenium {args.selenium}')

    mainloop(**args2)
    args2 = {'selenium': args.selenium}
    ticker = threading.Event()
    while not ticker.wait(WAIT_TIME_SECONDS):
        mainloop(**args2)
