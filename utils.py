import datetime
import json
import math
import time


def unpack_boats(boats_response):
    # filter only pleasure crafts
    pleasures = []
    for boatdata in boats_response:
        item_dict = json.loads(boatdata)
        if type(item_dict) is not dict:
            continue
        test = item_dict.get('data')
        if test is None:
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
        boatdata['ELAPSED'] = get_ais_signal_time(int(boatdata['ELAPSED']))

    return pleasuresDeduplicates


def handle_data(boatname, boatdict, datafile=None):
    lat_decimal = len(boatdict.get('LAT').split('.')[1])
    lon_decimal = len(boatdict.get('LON').split('.')[1])
    LAT = str(round(float(boatdict.get('LAT')), 4)).ljust(13 - lat_decimal, '0').rjust(9, ' ')
    LON = str(round(float(boatdict.get('LON')), 4)).ljust(13 - lon_decimal, '0').rjust(9, ' ')
    SPEED = str(int(boatdict.get('SPEED')) / 10).rjust(4, ' ')
    HEADING = str(boatdict.get('HEADING')).rjust(3, ' ')
    TIME = datetime.datetime.fromtimestamp(boatdict.get('ELAPSED'))
    string = f"LAT: {LAT} LON: {LON}, SPEED: {SPEED}, HEADING: {HEADING}, TIME: {TIME}"
    print(f"{boatname.ljust(12, '-')}->{string.rjust(80, ' ')}")
    if datafile:
        datafile[boatname].append(boatdict)
        with open('data.json', 'w') as outfile:
            json.dump(datafile, outfile)


def get_ais_signal_time(elapsed):
    tm = datetime.datetime.now()
    tm = tm - datetime.timedelta(minutes=elapsed, seconds=tm.second,
                                 microseconds=tm.microsecond)
    return tm.timestamp()


def great_circle_destination(lon1, lat1, bearing, dist):
    R = 6371 / 1.82
    lat2 = lat1 + math.atan(dist * math.cos(math.radians(bearing)) / R)
    lon2 = lon1 + math.atan(dist * math.sin(math.radians(bearing)) / R)
    return lon2, lat2


def calculate_distance(boat, x, y):
    X = (float(boat.get('LON')) - x) ** 2
    Y = (float(boat.get('LAT')) - y) ** 2
    return math.sqrt(X + Y)


def get_data_from_prevpoint(d, prevpoint, item, datafile):
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(prevpoint.get('ELAPSED')))
    distance = int(prevpoint.get('SPEED')) / 10 * timeElapsed.total_seconds() / 3600  # mm
    lon, lat = great_circle_destination(float(prevpoint.get('LON')), float(prevpoint.get('LAT')),
                                        math.radians(int(prevpoint.get('COURSE'))), distance)
    del d.requests
    url = f'https://www.marinetraffic.com/en/ais/home/centerx:{round(lon, 3)}/centery:{round(lat, 3)}/zoom:8'
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
        return None
    distances = [calculate_distance(boat, lon, lat) for boat in _boats]
    if not distances:
        print(f'No positions for {item} boat -No distances _boats= {_boats}')
        return None
    mostProbableBoat = _boats[distances.index(min(distances))]
    if mostProbableBoat.get('ELAPSED') - prevpoint.get('ELAPSED') < 80:
        print(f'{item} No new positions')
        return item
    else:
        handle_data(item, _boats[distances.index(min(distances))], datafile)
        return item


def get_data_from_prevpoint_with_boat_data(prevpoint, item, boat_data, datafile):
    timeElapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(prevpoint.get('ELAPSED')))
    distance_covered = int(prevpoint.get('SPEED')) / 10 * timeElapsed.total_seconds() / 3600  # mm
    lon, lat = great_circle_destination(float(prevpoint.get('LON')), float(prevpoint.get('LAT')),
                                        math.radians(int(prevpoint.get('COURSE'))), distance_covered)
    distances = [calculate_distance(boat, lon, lat) for boat in boat_data]

    if min(distances) > 6:
        print(f'{item} distance = {min(distances)}, too much, falling back.')
        return None, boat_data
    mostProbableBoat = boat_data[distances.index(min(distances))]
    if mostProbableBoat.get('ELAPSED') - prevpoint.get('ELAPSED') < 80:
        print(f'{item} No new positions')
        boat_data.remove(mostProbableBoat)
        return item, boat_data
    elif mostProbableBoat.get('LON') == prevpoint.get('LON') and mostProbableBoat.get('LAT') == prevpoint.get('LAT'):
        print(f'{item} Position is the same as last recorded.')
        boat_data.remove(mostProbableBoat)
        return item, boat_data
    else:
        handle_data(item, boat_data[distances.index(min(distances))], datafile)
        boat_data.remove(mostProbableBoat)
        return item, boat_data
