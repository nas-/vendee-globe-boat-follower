import datetime
import json
import logging
from typing import Dict, List, Tuple, Union

from geopy import distance

logger = logging.getLogger("Main")


class EarthFunctions:
    @staticmethod
    def calculate_distance(
        origin: [Tuple[float, float], List[float]],
        destination: [Tuple[float, float], List[float]],
    ) -> float:
        """
        :param origin: Starting point coordinates
        Latitude(Negative for suthern emisphere)
        Longitude(Negative for western emisphere). Degrees
        :param destination:Ending point coordinates
        Latitude(Negative for suthern emisphere)
        Longitude(Negative for western emisphere). Degrees
        :return: float: distance in nautical miles.
        """

        actual_distance = distance.great_circle(origin, destination)
        return actual_distance.nautical

    @staticmethod
    def gcd(
        origin: [Tuple[float, float], List[float]], bearing: float, dist: float
    ) -> Tuple[float, float]:
        """
        :rtype: Tuple
        :param origin: Starting point coordinates
        Latitude(Negative for suthern emisphere)
        Longitude(Negative for western emisphere). Degrees
        :param bearing: Bearing (degrees) from origin. [0-359°]
        :param dist: Distance in nautical miles
        :return: Destination point Tuple
        Latitude(Negative for southern emisphere)
        Longitude(Negative for western emisphere)
        """
        destination = distance.great_circle(nautical=dist).destination(origin, bearing)
        return destination.latitude, destination.longitude


def unpack_boats(boats_response: List) -> List[Dict]:
    """
    Reads the responses from Marinetraffic, and returns only pleasure crafts.
    :param boats_response: Responses from Marinetraffic
    :return: List of dictionaries, each representing a boat
    """
    pleasures = []
    for boatdata in boats_response:
        if isinstance(boatdata, bytes):
            try:
                item_dict = json.loads(boatdata)
            except json.decoder.JSONDecodeError:
                continue
        else:
            item_dict = boatdata
        if type(item_dict) is not dict:
            continue
        test = item_dict.get("data")
        if test is None or type(test) == str:
            continue
        else:
            rows = test.get("rows")
        for row in rows:
            ship_kind = row.get("TYPE_NAME")
            if ship_kind == "Pleasure Craft":
                pleasures.append(row)
    pleasures_no_shipID = [
        {
            k: float(v)
            for k, v in d.items()
            if k
            not in [
                "SHIP_ID",
                "STATUS_NAME",
                "TYPE_IMG",
                "SHIPNAME",
                "SHIPTYPE",
                "TYPE_NAME",
                "INVALID_DIMENSIONS",
            ]
        }
        for d in pleasures
    ]

    pleasuresDeduplicates = [
        dict(t) for t in {tuple(d.items()) for d in pleasures_no_shipID}
    ]
    for boatdata in pleasuresDeduplicates:
        tm = datetime.datetime.now()
        tm = tm - datetime.timedelta(
            minutes=int(boatdata["ELAPSED"]),
            seconds=tm.second,
            microseconds=tm.microsecond,
        )
        boatdata["ELAPSED"] = tm.timestamp()

    return sorted(pleasuresDeduplicates, key=lambda i: i["LAT"])


def handle_data(boatname: str, boatdict: Dict) -> str:
    """
    Prints out the data about this boat in a nice way.
    :param boatname: name of the boat.
    :param boatdict: Dictionary of boat data to print.
    :return:
    """
    LAT = f"{round(float(boatdict.get('LAT')), 4):.4f}"
    LON = f"{round(float(boatdict.get('LON')), 4):.4f}"
    SPEED = f"{(int(boatdict.get('SPEED')) / 10):.1f}"
    HEADING = f"{boatdict.get('HEADING'):.0f}"
    TIME = datetime.datetime.fromtimestamp(boatdict.get("ELAPSED"))
    string = f"LAT: {LAT:>9} LON: {LON:>9}, SPEED: {SPEED:>4}, HEADING: {HEADING:>3}°, TIME: {TIME}"
    return f"{boatname.ljust(22, '-')}->{string.rjust(80, ' ')}"


def save_data(boatname: str, boatdict: Dict, datafile: Dict = None) -> None:
    """
    Save the data of the current position in boatdict and saves to disk
    :param boatname: name of the boat.
    :param boatdict: Dictionary of boat data to print.
    :param datafile: Content of the file.
    """
    boatdict = {k: float(v) for k, v in boatdict.items()}
    if datafile:
        if boatname in datafile.keys():
            datafile[boatname].append(boatdict)
        else:
            datafile[boatname] = [boatdict]
        with open("src/data.json", "w") as outfile:
            json.dump(datafile, outfile, indent=2)


def get_data_from_prevpoint_with_boat_data(
    prevpoint: Dict, item: str, boat_data: List[Dict], datafile: Dict
) -> Union[tuple[None, list[dict], str], tuple[str, list[dict], str]]:
    """
    Function that take in the previous recorded point for the boat, the boat name, and all the data got from MT.
    It calculates where the boat should be now.
    Checks if there is a boat closeby (dist<MINDISTANCE) in the current response, returned if within x miles.

    If it finds a boat, it removes the position used from boat_dict, so it cannot be used in subsequent runs.

    :return:Tuple, Boatname-boat_data
    :param prevpoint: Previous position of the boat
    :param item: Boat name.
    :param boat_data: All the boats returned by Marinetaffic
    :param datafile: Content of the file.
    """
    MINDISANCE = 35
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(
        prevpoint.get("ELAPSED")
    )
    distance_covered = (
        prevpoint.get("SPEED") / 10 * timeElapsed.total_seconds() / 3600
    )  # mm
    origin = (prevpoint.get("LAT"), prevpoint.get("LON"))
    lat, lon = EarthFunctions.gcd(origin, prevpoint.get("COURSE"), distance_covered)
    distances = [
        EarthFunctions.calculate_distance(
            (boat.get("LAT"), boat.get("LON")), (lat, lon)
        )
        for boat in boat_data
    ]
    if not distances:
        logger.warning(f"{item} - Distances is an empty sequence")
        return None, boat_data, "NOK"
    # TODO check here if boat is already present in another part of dict.
    logger.debug(f"{item}: running get_data_from_prevpoint_with_boat_data")
    mostProbableBoat, status = search_for_duplicate(
        distances, boat_data, datafile, item
    )
    if not mostProbableBoat:
        return None, boat_data, status

    if min(distances) > MINDISANCE:
        logger.debug(
            f'{item}: Should be {(lat, lon)},is {mostProbableBoat.get("LAT"), mostProbableBoat.get("LON")}'
            f" distance = {min(distances)}, too much, falling back. Out of map?"
        )
        return None, boat_data, "NOK"
    if mostProbableBoat.get("SPEED") == "0":
        logger.debug(f"{item}: Speed = 0, probably fake data")
        return None, boat_data, "NOK"
    if mostProbableBoat.get("ELAPSED") - prevpoint.get("ELAPSED") < 100:
        logger.info(f"{item} No new positions")
        return None, boat_data, "OK"
    elif mostProbableBoat.get("LON") == prevpoint.get("LON") and mostProbableBoat.get(
        "LAT"
    ) == prevpoint.get("LAT"):
        logger.info(f"{item} Position is the same as last recorded.")
        return None, boat_data, "OK"
    else:
        handle_data(item, boat_data[distances.index(min(distances))])
        save_data(item, boat_data[distances.index(min(distances))], datafile)
        boat_data.remove(mostProbableBoat)
        return item, boat_data, "OK"


def get_data_from_prevpoint(
    d, prevpoint: Dict, item: str, datafile: Dict
) -> Union[
    tuple[None, None, str], tuple[None, list[dict], str], tuple[str, list[dict], str]
]:
    """

    :param d: webdriver or Scrape
    :param prevpoint: Dictionary contains data from previous point.
    :param item:  Boat name
    :param datafile: all the data from the file as dict
    :return: Tuple Boatname-boatdata
    """
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(
        prevpoint.get("ELAPSED")
    )
    miles_done = prevpoint.get("SPEED") / 10 * timeElapsed.total_seconds() / 3600  # nm
    lat, lon = EarthFunctions.gcd(
        (prevpoint.get("LAT"), prevpoint.get("LON")),
        prevpoint.get("COURSE"),
        miles_done,
    )

    url = f"https://www.marinetraffic.com/en/ais/home/centerx:{round(lon, 3)}/centery:{round(lat, 3)}/zoom:10"
    # TODO: Modify this.
    _boats = d.request_marinetrafic_url(url, do_req=True)
    if not _boats:
        logger.debug(f"{item} - No boats in zoom 10. Trying zoom 6.")
        url = f"https://www.marinetraffic.com/en/ais/home/centerx:{round(lon, 3)}/centery:{round(lat, 3)}/zoom:6"
        logger.debug(f"{item} - {url}")
        _boats = d.request_marinetrafic_url(url, do_req=True)
    if not _boats:
        logger.warning(f"{item} No positions. Cannot get data.")
        return None, None, "NOK"
    # TODO End Modify
    return get_data_from_prevpoint_with_boat_data(prevpoint, item, _boats, datafile)


def search_for_duplicate(distances: List, boat_data: List, datafile: Dict, item: str):
    keys = ["LAT", "LON", "SPEED", "COURSE", "HEADING"]
    if not distances:
        return None, "NOK"
    mostProbableBoat = boat_data[distances.index(min(distances))]
    if len(distances) == 1:
        previous_positions = datafile.get(item)
        if not previous_positions:
            logging.debug("no previous positions")
            return mostProbableBoat, "OK"
        for position in previous_positions:
            if all(position.get(c) == mostProbableBoat.get(c) for c in keys):
                logging.debug("Same position as before")
                return None, "OK"
    MAXDIST = 30
    for a in datafile:
        for b in datafile[a]:
            if all(b.get(c) == mostProbableBoat.get(c) for c in keys):
                if a == item:
                    logging.debug(f"{item} has the same position a previously")
                    return None, "OK"
                distances[distances.index(min(distances))] = 400000
                logging.debug(f"{item} Position {b} is already used by {a}.")
                if min(distances) >= MAXDIST:
                    logging.debug(
                        f"{item} - Closest boat allowed is {min(distances)} nm away.max allowed is {MAXDIST}."
                    )
                    return None, "NOK"
                return boat_data[distances.index(min(distances))], "OK"
    logging.debug(f"{item} no duplicates found")
    return mostProbableBoat, "OK"


class BoatNotFound(ValueError):
    pass
