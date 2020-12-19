import json
import os
import re
import logging

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tzlocal import get_localzone

logger = logging.getLogger('Main')


def convert(row, lat_long):
    lat = row[lat_long]
    deg, primes, cardinal = re.findall(r'(\d{1,3})°(\d{2}\.\d{2}).([ESWN])', lat)[0]
    emisphere = 1
    if cardinal in ['S', 'W']:
        emisphere = -1
    return round(emisphere * (float(deg) + float(primes) / 60), 3)


def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    logging.info(f'Downloaded file {local_filename}')
    return local_filename


def get_rankings():
    soup = BeautifulSoup(requests.get("https://www.vendeeglobe.org/en/ranking").text, 'html.parser')
    Current_ranking = soup.find(class_='rankings__download').get('href')
    if not os.path.isfile('src/ranking.txt') or not os.path.getsize('src/ranking.txt'):
        open('src/ranking.txt', 'w+').write('')
    with open('src/ranking.txt', 'r+') as file:
        if file.readline() == Current_ranking:
            logging.info('Positions already downloaded')
            return None

    url = f'https://www.vendeeglobe.org{Current_ranking}'
    year, month, day = map(int, re.findall(r'(202\d)(\d{2})(\d{2})', Current_ranking)[0])
    try:
        file = download_file(url)
    except requests.exceptions.HTTPError as err:
        logger.warning(f'Error while getting the file from vendee site: \n{err}')
        return None

    df = pd.read_excel(file, skiprows=4, skipfooter=4)
    os.remove(file)
    df = df[['Unnamed: 3', 'Heure FR\nHour FR', 'Latitude\nLatitude', 'Longitude\nLongitude', 'Cap\nHeading',
             'Vitesse\nSpeed']]
    df.columns = ['NAME', 'ELAPSED', 'LAT', 'LON', 'HEADING', 'SPEED']
    df.NAME = df.NAME.str.split('\n').str.get(-1).str.split('-').str.get(0).str.strip().str.normalize(
        'NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper()
    df.ELAPSED = df.ELAPSED.str.replace('\n', '').str.split('-').str.get(0).str.replace('FR', '').str.strip()
    df.SPEED = df.SPEED.str.split(' ').str.get(0).astype('float64') * 10
    df.HEADING = df.HEADING.str.replace('°', '')
    df['COURSE'] = df.HEADING
    df = df[~df['ELAPSED'].isna()]
    df['ELAPSED'] = pd.to_datetime(f'{year}-{month}-{day} ' + df.ELAPSED).dt.tz_localize('Europe/Paris').dt.tz_convert(
        get_localzone().zone).astype('int64') // 10 ** 9
    df['LAT'] = df.apply(convert, args=('LAT',), axis=1)
    df['LON'] = df.apply(convert, args=('LON',), axis=1)
    df = df.astype({'HEADING': 'int64', 'COURSE': 'int64'})
    with open('src/ranking.txt', 'r+') as file:
        file.write(Current_ranking)
    return json.loads(df.set_index('NAME', drop=True).to_json(orient='index'))


def handle_rankings():
    rankings = get_rankings()
    if not rankings:
        return
    with open('src/data.json') as json_file:
        file = json.load(json_file)
    for element in rankings:
        series = file.get(element)
        position = rankings.get(element)
        if series:
            if position['ELAPSED'] > series[-1]['ELAPSED']:
                file[element].append(position)
            else:
                logger.debug(f"not appending  {element} {position['ELAPSED']} {series[-1]['ELAPSED']}")
        else:
            file[element] = [position]
    with open('src/data.json', 'w') as outfile:
        json.dump(file, outfile, indent=2)


if __name__ == '__main__':
    handle_rankings()
