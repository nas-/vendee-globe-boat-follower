import datetime
import json
import logging
from typing import Tuple, List, Dict, Union

from geopy import distance

logger = logging.getLogger('Main')


class EarthFunctions:
    @staticmethod
    def calculate_distance(origin: [Tuple[float, float], List[float]],
                           destination: [Tuple[float, float], List[float]]) -> float:
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
    def gcd(origin: [Tuple[float, float], List[float]], bearing: float, dist: float) -> Tuple[float, float]:
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
        logger.debug(f' {origin}, {bearing}')
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
        test = item_dict.get('data')
        if test is None or type(test) == str:
            continue
        else:
            rows = test.get('rows')
        for row in rows:
            ship_kind = row.get('TYPE_NAME')
            if ship_kind == 'Pleasure Craft':
                pleasures.append(row)
    pleasures_no_shipID = [
        {
            k: v
            for k, v in d.items()
            if k not in [
                'SHIP_ID',
                'STATUS_NAME',
                'TYPE_IMG',
                'SHIPNAME',
                'SHIPTYPE',
                'TYPE_NAME',
                'INVALID_DIMENSIONS']
        }
        for d in pleasures
    ]

    pleasuresDeduplicates = [dict(t) for t in {tuple(d.items()) for d in pleasures_no_shipID}]
    for boatdata in pleasuresDeduplicates:
        tm = datetime.datetime.now()
        tm = tm - datetime.timedelta(minutes=int(boatdata['ELAPSED']), seconds=tm.second,
                                     microseconds=tm.microsecond)
        boatdata['ELAPSED'] = tm.timestamp()

    return sorted(pleasuresDeduplicates, key=lambda i: i['LAT'])


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
    HEADING = f"{boatdict.get('HEADING')}"
    TIME = datetime.datetime.fromtimestamp(boatdict.get('ELAPSED'))
    string = f"LAT: {LAT:>9} LON: {LON:>9}, SPEED: {SPEED:>4}, HEADING: {HEADING:>3}°, TIME: {TIME}"
    return f"{boatname.ljust(12, '-')}->{string.rjust(80, ' ')}"


def save_data(boatname: str, boatdict: Dict, datafile: Dict = None) -> None:
    """
    Save the data of the current position in boatdict and saves to disk
    :param boatname: name of the boat.
    :param boatdict: Dictionary of boat data to print.
    :param datafile: Content of the file.
    """
    if datafile:
        if boatname in datafile.keys():
            datafile[boatname].append(boatdict)
        else:
            datafile[boatname] = [boatdict]
        with open('src/data.json', 'w') as outfile:
            json.dump(datafile, outfile, indent=2)


def get_data_from_prevpoint_with_boat_data(prevpoint: Dict, item: str, boat_data: List[Dict], datafile: Dict) -> Union[
    Tuple[None, List[dict]], Tuple[str, List[dict]]]:
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
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(prevpoint.get('ELAPSED')))
    distance_covered = int(prevpoint.get('SPEED')) / 10 * timeElapsed.total_seconds() / 3600  # mm
    origin = (float(prevpoint.get('LAT')), float(prevpoint.get('LON')))
    lat, lon = EarthFunctions.gcd(origin, int(prevpoint.get('COURSE')), distance_covered)
    distances = [EarthFunctions.calculate_distance((float(boat.get('LAT')), float(boat.get('LON'))), (lat, lon)) for
                 boat in boat_data]
    if not distances:
        logger.warning(f'{item} - Distances is an empty sequence')
        return None, boat_data
    # TODO check here if boat is already present in another part of dict.
    mostProbableBoat = search_for_duplicate(distances, boat_data, datafile, item)
    if not mostProbableBoat:
        print('Position is the same')
        return None, boat_data

    if min(distances) > MINDISANCE:
        logger.debug(f'{item}: Should be {(lat, lon)},is {mostProbableBoat.get("LAT"), mostProbableBoat.get("LON")}'
                     f' distance = {min(distances)}, too much, falling back. Out of map?')
        return None, boat_data
    if mostProbableBoat.get('SPEED') == '0':
        logger.debug(f'{item}: Speed = 0, probably fake data')
        return None, boat_data
    if mostProbableBoat.get('ELAPSED') - prevpoint.get('ELAPSED') < 100:
        logger.info(f'{item} No new positions')
    elif mostProbableBoat.get('LON') == prevpoint.get('LON') and mostProbableBoat.get('LAT') == prevpoint.get('LAT'):
        logger.info(f'{item} Position is the same as last recorded.')
    else:
        handle_data(item, boat_data[distances.index(min(distances))])
        save_data(item, boat_data[distances.index(min(distances))], datafile)
    boat_data.remove(mostProbableBoat)
    return item, boat_data


def get_data_from_prevpoint(d, prevpoint: Dict, item: str, datafile: Dict) -> Union[
    Tuple[None, None], Tuple[str, List[dict]]]:
    """

    :param d: webdriver or Scrape
    :param prevpoint: Dictionary containg data from previous point.
    :param item:  Boat name
    :param datafile: all the data from the file as dict
    :return: Tuple Boatname-boatdata
    """
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(prevpoint.get('ELAPSED')))
    miles_done = int(prevpoint.get('SPEED')) / 10 * timeElapsed.total_seconds() / 3600  # nm
    lon, lat = EarthFunctions.gcd((float(prevpoint.get('LAT')), float(prevpoint.get('LON'))),
                                  int(prevpoint.get('COURSE')), miles_done)

    url = f'https://www.marinetraffic.com/en/ais/home/centerx:{round(lon, 3)}/centery:{round(lat, 3)}/zoom:10'
    # TODO: Modify this.
    _boats = d.request_marinetrafic_url(url, do_req=True)
    if not _boats:
        logger.debug(f'{item} - No boats in zoom 10. Trying zoom 6.')
        url = f'https://www.marinetraffic.com/en/ais/home/centerx:{round(lon, 3)}/centery:{round(lat, 3)}/zoom:6'
        _boats = d.request_marinetrafic_url(url, do_req=True)
    if not _boats:
        logger.warning(f'{item} No positions. Cannot get data.')
        return None, None
    # TODO End Modify
    return get_data_from_prevpoint_with_boat_data(prevpoint, item, _boats, datafile)


def req_boat(requests) -> List:
    """
    Filter requests for those coming from get data endpoint.

    :type requests: LazyRequest
    """
    req_boats = []
    for item in requests:
        if item.url.startswith('https://www.marinetraffic.com/getData'):
            try:
                req_boats.append(item.response.body)
            except AttributeError:
                continue
    return req_boats


def search_for_duplicate(distances: List, boat_data: List, datafile: Dict, item: str):
    if not distances:
        return
    keys = ['LAT', 'LON', 'SPEED', 'COURSE', 'HEADING']
    mostProbableBoat = boat_data[distances.index(min(distances))]
    if len(distances) == 1:
        return mostProbableBoat
    for a in datafile:
        for b in datafile[a]:
            if all(b.get(c) == mostProbableBoat.get(c) for c in keys):
                if b == a:
                    logger.debug(f'{item} has the same position a previously')
                    return None
                distances[distances.index(min(distances))] = 400000
                logger.debug(f'{item} Position {b} is already used by {a}.')
                return boat_data[distances.index(min(distances))]
    logger.debug(f'{item} no duplicates found')
    return mostProbableBoat
