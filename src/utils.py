import datetime
import json
import time
from typing import Tuple, List, Dict, Union

from geopy import distance
from selenium import webdriver


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
        try:
            item_dict = json.loads(boatdata)
        except json.decoder.JSONDecodeError:
            continue
        if type(item_dict) is not dict:
            continue
        test = item_dict.get('data')
        if test is None:
            continue
        elif type(test) == str:
            continue
        else:
            rows = test.get('rows')
        for row in rows:
            ship_kind = row.get('TYPE_NAME')
            if ship_kind == 'Pleasure Craft':
                pleasures.append(row)
    pleasures_no_shipID = [{k: v for k, v in d.items() if k != 'SHIP_ID'} for d in pleasures]
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
    LAT = str(round(float(boatdict.get('LAT')), 4)).ljust(8, '0').rjust(9, ' ')
    LON = str(round(float(boatdict.get('LON')), 4)).ljust(8, '0').rjust(9, ' ')
    SPEED = str(int(boatdict.get('SPEED')) / 10).rjust(4, ' ')
    HEADING = str(boatdict.get('HEADING')).rjust(3, ' ')
    TIME = datetime.datetime.fromtimestamp(boatdict.get('ELAPSED'))
    string = f"LAT: {LAT} LON: {LON}, SPEED: {SPEED}, HEADING: {HEADING}, TIME: {TIME}"
    print(f"{boatname.ljust(12, '-')}->{string.rjust(80, ' ')}")
    return f"{boatname.ljust(12, '-')}->{string.rjust(80, ' ')}"


def save_data(boatname: str, boatdict: Dict, datafile: Dict = None) -> None:
    """
    Save the data of the current position in boatdict and saves to disk
    :param boatname: name of the boat.
    :param boatdict: Dictionary of boat data to print.
    :param datafile: Content of the file.
    """
    if datafile:
        datafile[boatname].append(boatdict)
        with open('src/data.json', 'w') as outfile:
            json.dump(datafile, outfile)


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
        print(f'{item} - Distances is an empty sequence')
        return None, boat_data
    mostProbableBoat = boat_data[distances.index(min(distances))]

    if min(distances) > MINDISANCE:
        print(f'{item}: Should be {(lat, lon)},is {mostProbableBoat.get("LAT"), mostProbableBoat.get("LON")}'
              f' distance = {min(distances)}, too much, falling back. Out of map?')
        return None, boat_data
    if mostProbableBoat.get('SPEED') == '0':
        print(f'{item}: Speed = 0, probably fake data')
        return None, boat_data

    if mostProbableBoat.get('ELAPSED') - prevpoint.get('ELAPSED') < 100:
        print(f'{item} No new positions')
        boat_data.remove(mostProbableBoat)
        return item, boat_data
    elif mostProbableBoat.get('LON') == prevpoint.get('LON') and mostProbableBoat.get('LAT') == prevpoint.get('LAT'):
        print(f'{item} Position is the same as last recorded.')
        boat_data.remove(mostProbableBoat)
        return item, boat_data
    else:
        handle_data(item, boat_data[distances.index(min(distances))])
        save_data(item, boat_data[distances.index(min(distances))], datafile)
        boat_data.remove(mostProbableBoat)
        return item, boat_data


def get_data_from_prevpoint(d: webdriver, prevpoint: Dict, item: str, datafile: Dict) -> Union[
    Tuple[None, None], Tuple[str, List[dict]]]:
    del d.requests
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(prevpoint.get('ELAPSED')))
    miles_done = int(prevpoint.get('SPEED')) / 10 * timeElapsed.total_seconds() / 3600  # mm
    lon, lat = EarthFunctions.gcd((float(prevpoint.get('LON')), float(prevpoint.get('LAT'))),
                                  int(prevpoint.get('COURSE')), miles_done)

    url = f'https://www.marinetraffic.com/en/ais/home/centerx:{round(lon, 3)}/centery:{round(lat, 3)}/zoom:10'
    # TODO: Modify this.
    d.get(url)
    d.refresh()
    time.sleep(10)
    req_boats = [item.response.body for item in d.requests if
                 item.url.startswith('https://www.marinetraffic.com/getData')]
    _boats = unpack_boats(req_boats)
    if not _boats:
        time.sleep(10)
        req_boats = [item.response.body for item in d.requests if
                     item.url.startswith('https://www.marinetraffic.com/getData')]
        _boats = unpack_boats(req_boats)
    if not _boats:
        print(f'{item} No positions. Cannot get data.')
        return None, None
    # TODO End Modify
    return get_data_from_prevpoint_with_boat_data(prevpoint, item, _boats, datafile)
