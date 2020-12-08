import cfscrape
from src.utils import unpack_boats
import re
import logging

logger = logging.getLogger('Main')

class Scrape(cfscrape.Session):
    def __init__(self):
        super().__init__()
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0'}
        self.session = cfscrape.create_scraper()
        self.session.get("http://marinetraffic.com", headers=headers)

    def request_marinetraffic_coordinate(self, x, y, zoom, do_req=False, **kwargs):
        url_referrer = f'https://www.marinetraffic.com/en/ais/home/centerx:{x:.1f}/centery:{y:.1f}/zoom:{zoom}'

        if zoom == 10:
            X_coeff = [256, 1.416666666]
            Y_coeff = [256, - 1.467447463, - 5.44692E-05, - 6.00027E-05]

            X = round(X_coeff[0] + X_coeff[1] * x)
            Y = round(Y_coeff[0] + Y_coeff[1] * y + Y_coeff[2] * y ** 2 + Y_coeff[3] * y ** 3)

        elif zoom == 6:
            # LON1 0.088158378
            # LON0 15.46274808
            X_coeff = [15.46274808, 0.088158378]

            Y_coeff = [15.50333876, -0.074571165, 2.79456E-05, -1.16363E-05]
            # YYYY -> Parameters got are always within 0.5 from real value.
            # LAT3    -1.16363E-05
            # LAT2    2.79456E-05
            # LAT1    -0.074571165
            # LAT0    15.50333876
            X = round(X_coeff[0] + X_coeff[1] * x)
            Y = round(Y_coeff[0] + Y_coeff[1] * y + Y_coeff[2] * y ** 2 + Y_coeff[3] * y ** 3)
        else:
            raise Exception(f"\n\nSupported Zoom levels: 6, 10. Current value={zoom}.Change or use -sel to fall back to "
                            f"the selenium backend.\n Url={url_referrer}")

        Xs = [X - 1, X, X + 1]
        Ys = [Y - 1, Y, Y + 1]
        urls = [f"https://www.marinetraffic.com/getData/get_data_json_4/z:{zoom}/X:{X_str}/Y:{Y_str}/station:0" for
                X_str in Xs
                for Y_str in Ys]
        headers = {
            "accept": "*/*",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "vessel-image": "00d4f8099979955994a13cbf137120c4a609",
            "x-requested-with": "XMLHttpRequest",
            "referrer": f"{url_referrer}",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "method": "GET"
        }

        responses = []
        for url in urls:
            logging.debug(f'requesting Url {url}')
            if do_req:
                session_attempt = self.session.get(url, headers=headers)
                if not session_attempt.raise_for_status():
                    responses.append(session_attempt.json())
        return unpack_boats(responses)

    def request_marinetrafic_url(self, url, **kwargs):
        pattern = r'centerx:([-\d.]{4,7}).+centery:([-\d.]{4,7}).zoom:(\d{1,2})'
        longitudex, latitudey, zoom = re.findall(pattern, url)[0]
        longitudex = float(longitudex)
        latitudey = float(latitudey)
        zoom = int(zoom)
        return self.request_marinetraffic_coordinate(longitudex, latitudey, zoom, **kwargs)

    def cleanup(self):
        pass


if __name__ == "__main__":
    name = Scrape()
    MR = name.request_marinetrafic_url(
        'https://www.marinetraffic.com/en/ais/home/centerx:68.1/centery:-44.3/zoom:10',
        do_req=True)
    print(MR)

# kk = s.get("https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:250/Y:325/station:0", headers={
#     "accept": "*/*",
# "accept-language": "en-US,en;q=0.9,it;q=0.8",
# "cache-control": "no-cache",
# "pragma": "no-cache",
# "sec-fetch-dest": "empty",
# "sec-fetch-mode": "cors",
# "sec-fetch-site": "same-origin",
# "vessel-image": "00d4f8099979955994a13cbf137120c4a609",
# "x-requested-with": "XMLHttpRequest",
# "referrer": "https://www.marinetraffic.com/en/ais/home/centerx:-4.0/centery:-44.0/zoom:10",
# "referrerPolicy": "strict-origin-when-cross-origin",
# "method": "GET",
# "mode": "cors",
# "credentials": "include"
# })
