import argparse
import datetime
import json
import logging
import os
import re
import threading

import src.utils
from backends.cfscrape_requests import Scrape
from backends.seleniumwire_requests import ScrapeSelenium
from src.geojson_creator import create_geojson
from src.plot import plot
from src.scrape_rankings import handle_rankings


class MegaClass:
    def __init__(
        self,
        fleet_positions,
        datafile,
        url,
        marinetraffic_instance,
        boat_name,
        refresh=False,
    ):
        self.fleet_positions = fleet_positions
        self.all_positions = datafile
        self.refresh = refresh
        self.boat_name = boat_name
        self.previous_positions = self.all_positions.get(self.boat_name)
        if url:
            pattern = r"centerx:([-\d.]{4,7}).+centery:([-\d.]{4,7}).zoom:(\d{1,2})"
            self.longitude, self.latitude, self.zoom = map(
                float, re.findall(pattern, url)[0]
            )
        else:
            self.longitude, self.latitude, self.zoom = None, None, None
        self.instance = marinetraffic_instance

    def get_new_positions(self):
        status = ""
        if (not self.refresh) and self.previous_positions:
            (
                _,
                boats_current_position,
                status,
            ) = src.utils.get_data_from_prevpoint_with_boat_data(
                self.previous_positions[-1],
                self.boat_name,
                self.fleet_positions,
                self.all_positions,
            )
            if status == "OK":
                return
            else:
                _, boats_current_position, status = src.utils.get_data_from_prevpoint(
                    self.instance,
                    self.previous_positions[-1],
                    self.boat_name,
                    self.all_positions,
                )

            if status == "OK":
                return

        if (
            self.refresh or not self.previous_positions or status != "OK"
        ) and self.latitude:
            return self.request_and_get_closest_to_center()

    def request_and_get_closest_to_center(self):
        boats_in_area = self.instance.request_marinetraffic_coordinate(
            self.longitude, self.latitude, self.zoom, do_req=True
        )
        if not boats_in_area:
            return None
        distances_to_center = [
            src.utils.EarthFunctions.calculate_distance(
                (boat.get("LAT"), boat.get("LON")), (self.latitude, self.longitude)
            )
            for boat in boats_in_area
        ]

        _mostProbableBoat, status = src.utils.search_for_duplicate(
            distances_to_center, boats_in_area, self.all_positions, self.boat_name
        )
        if _mostProbableBoat:
            src.utils.save_data(self.boat_name, _mostProbableBoat, self.all_positions)
            return _mostProbableBoat
        return None


def mainloop(refresh=None, selenium=None) -> None:
    """
    :param refresh: If true, use only links in config.json.
    :param selenium: Uses legacy selenium backend
    """
    with open("config.json") as json_file:
        CONFIG = json.load(json_file)

    marinetraffic_instance = ScrapeSelenium() if selenium else Scrape()

    logger.info(f"starting run {datetime.datetime.now()}")

    handle_rankings()

    with open("src/data.json") as json_file:
        datafile = json.load(json_file)

    boats_to_retrieve = [item for item in CONFIG]
    fleet_positions = marinetraffic_instance.request_marinetrafic_url(
        "https://www.marinetraffic.com/en/ais/home/centerx:147.6/centery:-53.4/zoom:6",
        do_req=True,
    )
    for item in boats_to_retrieve:
        A = MegaClass(
            fleet_positions,
            datafile,
            CONFIG.get(item),
            marinetraffic_instance,
            item,
            refresh,
        )
        A.get_new_positions()

    marinetraffic_instance.cleanup()

    with open("src/data.json") as json_file:
        datafile = json.load(json_file)

    print("----------------------")
    print(f"starting run {datetime.datetime.now()}")
    for item in datafile:
        if datafile[item]:
            print(src.utils.handle_data(item, datafile[item][-1]))
    print("----------------------")
    plot(datafile, 25)
    create_geojson(datafile)


if __name__ == "__main__":
    WAIT_TIME_SECONDS = 600

    parser = argparse.ArgumentParser(description="Starts the process.")
    parser.add_argument(
        "-r",
        "--refresh",
        action="store_true",
        help="Uses only the position specified in config",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Debug purposes")
    parser.add_argument(
        "-sel",
        "--selenium",
        action="store_true",
        help="Force use of legacy selenium backend",
    )
    args = parser.parse_args()

    if args.debug:
        logger = logging.getLogger("Main")
        logger.setLevel(logging.DEBUG)
        logger.debug("Setting level to debug")
    else:
        logger = logging.getLogger("Main")
        logger.setLevel(logging.INFO)
        logger.info("Setting level to info")

    args2 = {"refresh": args.refresh, "selenium": args.selenium}
    logger.debug(f"using selenium {args.selenium}")

    if not os.path.isfile("src/data.json"):
        open("src/data.json", "w+").write('{"BOSS":[]}')
    if not os.path.getsize("src/data.json"):
        open("src/data.json", "w+").write('{"BOSS":[]}')

    mainloop(**args2)
    args2 = {"selenium": args.selenium}
    ticker = threading.Event()
    while not ticker.wait(WAIT_TIME_SECONDS):
        mainloop(**args2)
