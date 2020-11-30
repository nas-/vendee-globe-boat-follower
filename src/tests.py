from unittest import TestCase
from src import utils
import datetime

request = b'{"type":1,"data":{"rows":[{"LAT":"-42.8567","LON":"-29.80231","SPEED":"122","COURSE":"82","HEADING":"82",' \
          b'"ELAPSED":"10","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"8",' \
          b'"SHIP_ID":"TmpNNE5qUXdOak00TmpRd05qTTROZz09LVljMGJtaHlZNUZIQTArcXlLcjF1VXc9PQ==","TYPE_IMG":"8",' \
          b'"TYPE_NAME":"Tanker","STATUS_NAME":"Underway using Engine"},{"LAT":"-41.40326","LON":"-46.93161",' \
          b'"SPEED":"118","COURSE":"261","HEADING":"261","ELAPSED":"9","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"7",' \
          b'"SHIP_ID":"T0RVNU16QTRPRFU1TXpBNE9EVTVNdz09LUxjY015MVVBZ0FpT25sc2dpcXpjZWc9PQ==","TYPE_IMG":"7",' \
          b'"TYPE_NAME":"Cargo Vessel","STATUS_NAME":"Underway using Engine"},{"LAT":"-42.69098","LON":"-6.722048",' \
          b'"SPEED":"95","COURSE":"90","HEADING":"90","ELAPSED":"8","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"7",' \
          b'"SHIP_ID":"T0RRM01ERXhPRFEzTURFeE9EUTNNQT09LWVwV2orWWxiK0cvT1M2bk10bnNhSlE9PQ==","TYPE_IMG":"7",' \
          b'"TYPE_NAME":"Cargo Vessel","STATUS_NAME":"Underway using Engine"},{"LAT":"-39.12271","LON":"-38.224",' \
          b'"SPEED":"136","COURSE":"103","HEADING":"103","ELAPSED":"10","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"8",' \
          b'"SHIP_ID":"Tnpjek56UXlOemN6TnpReU56Y3pOdz09LVNCMHBPSmRiWnlvQjRpLytsRmV2b1E9PQ==","TYPE_IMG":"8",' \
          b'"TYPE_NAME":"Tanker","STATUS_NAME":"Underway using Engine"},{"LAT":"-42.64273","LON":"-2.848365",' \
          b'"SPEED":"109","COURSE":"88","HEADING":"88","ELAPSED":"8","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"7",' \
          b'"SHIP_ID":"TXpRME1qQXpNelEwTWpBek16UTBNZz09LXdQd2pLendRNmdEdHZwWjNkdE5EZ0E9PQ==","TYPE_IMG":"7",' \
          b'"TYPE_NAME":"Cargo Vessel","STATUS_NAME":"Moored"},{"LAT":"-39.26303","LON":"-15.44128","SPEED":"130",' \
          b'"COURSE":"89","HEADING":"89","ELAPSED":"10","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"7",' \
          b'"SHIP_ID":"TkRFeU56VTBOREV5TnpVME5ERXlOdz09LUJMQ1NrdWdRUzI3ME4yRkc4dFhQbFE9PQ==","TYPE_IMG":"7",' \
          b'"TYPE_NAME":"Cargo Vessel","STATUS_NAME":"Underway using Engine"},{"LAT":"-60.44409","LON":"-47.53643",' \
          b'"SPEED":"67","COURSE":"78","HEADING":"78","ELAPSED":"10","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"2",' \
          b'"SHIP_ID":"T0RZd01qY3dPRFl3TWpjd09EWXdNZz09LWFpUVYzM2VocEVjK1hFOXVpMDJrNUE9PQ==","TYPE_IMG":"2",' \
          b'"TYPE_NAME":"Fishing","STATUS_NAME":"Underway using Engine"},{"LAT":"-60.46066","LON":"-47.04898",' \
          b'"SPEED":"94","COURSE":"22","HEADING":"22","ELAPSED":"10","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"2",' \
          b'"SHIP_ID":"TkRZM01ERTJORFkzTURFMk5EWTNNQT09LTBWVmZIMjVueHdPOTR4elZ4M2VjRnc9PQ==","TYPE_IMG":"2",' \
          b'"TYPE_NAME":"Fishing","STATUS_NAME":"Underway using Engine"},{"LAT":"-39.38987","LON":"-9.74721",' \
          b'"SPEED":"106","COURSE":"266","HEADING":"266","ELAPSED":"9","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"7",' \
          b'"SHIP_ID":"TWpVMU5qVTRNalUxTmpVNE1qVTFOZz09LU44OVhhcVV1NDNoODZVV3hPNmQ2Vnc9PQ==","TYPE_IMG":"7",' \
          b'"TYPE_NAME":"Cargo Vessel","STATUS_NAME":"Underway using Engine"},{"LAT":"-43.77048","LON":"-33.34991",' \
          b'"SPEED":"102","COURSE":"197","HEADING":"197","ELAPSED":"3","DESTINATION":"KING EDWARD POINT","FLAG":"UK",' \
          b'"LENGTH":"100","ROT":"0","SHIPNAME":"JAMES CLARK ROSS","SHIPTYPE":"3","SHIP_ID":"780940","WIDTH":"18",' \
          b'"L_FORE":"44","W_LEFT":"9","DWT":"2917","GT_SHIPTYPE":"59"},{"LAT":"-39.95451","LON":"-7.403518",' \
          b'"SPEED":"152","COURSE":"91","HEADING":"91","ELAPSED":"111","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"9",' \
          b'"SHIP_ID":"TnprNE5qZ3pOems0Tmpnek56azROZz09LUZUdGJXRXFpdWFHOXJBUDloTlcyTHc9PQ==","TYPE_IMG":"9",' \
          b'"TYPE_NAME":"Pleasure Craft","STATUS_NAME":"Unknown"},{"LAT":"-39.67762","LON":"-9.14808","SPEED":"240",' \
          b'"COURSE":"94","HEADING":"94","ELAPSED":"17","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"9",' \
          b'"SHIP_ID":"T1RVeE16QTBPVFV4TXpBME9UVXhNdz09LTZtaEFyOWdGWDhaSXp3cVM5ZEYvZkE9PQ==","TYPE_IMG":"9",' \
          b'"TYPE_NAME":"Pleasure Craft","STATUS_NAME":"Unknown"},{"LAT":"-39.92724","LON":"-6.348073","SPEED":"196",' \
          b'"COURSE":"112","HEADING":"112","ELAPSED":"124","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"9",' \
          b'"SHIP_ID":"TnprME5EZzVOemswTkRnNU56azBOQT09LW9vQ01ZNjgxRWQ1ZjVKUnhQbldzV1E9PQ==","TYPE_IMG":"9",' \
          b'"TYPE_NAME":"Pleasure Craft","STATUS_NAME":"Unknown"},{"LAT":"-60.675","LON":"-44.3325","SPEED":"0",' \
          b'"COURSE":"0","HEADING":"511","ELAPSED":"4","DESTINATION":"","FLAG":"AR","LENGTH":"4","ROT":"0",' \
          b'"SHIPNAME":"ROCAS HERDMAN","SHIPTYPE":"1","SHIP_ID":"3358541","WIDTH":"4","L_FORE":"0","W_LEFT":"0"},' \
          b'{"LAT":"-60.61666","LON":"-45.04667","SPEED":"0","COURSE":"0","HEADING":"511","ELAPSED":"1",' \
          b'"DESTINATION":"","FLAG":"AR","LENGTH":"4","ROT":"0","SHIPNAME":"ISLOTES BRISBANE","SHIPTYPE":"1",' \
          b'"SHIP_ID":"3364172","WIDTH":"4","L_FORE":"0","W_LEFT":"0"},{"LAT":"-40.81548","LON":"-7.297678",' \
          b'"SPEED":"143","COURSE":"96","HEADING":"96","ELAPSED":"15","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"9",' \
          b'"SHIP_ID":"T1RnMU9EVTBPVGcxT0RVME9UZzFPQT09LUFFSFJXUWZnNStueHI5S2ZsZVBCY1E9PQ==","TYPE_IMG":"9",' \
          b'"TYPE_NAME":"Pleasure Craft","STATUS_NAME":"Unknown"},{"LAT":"-41.12354","LON":"-5.118488","SPEED":"133",' \
          b'"COURSE":"110","HEADING":"110","ELAPSED":"264","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"9",' \
          b'"SHIP_ID":"Tmpjek56YzNOamN6TnpjM05qY3pOdz09LXBjdmdFcERFNjdWaUdqSDIvV3BORnc9PQ==","TYPE_IMG":"9",' \
          b'"TYPE_NAME":"Pleasure Craft","STATUS_NAME":"Unknown"}],"areaShips":17}} '
response = [{'LAT': '-39.67762', 'LON': '-9.14808', 'SPEED': '240', 'COURSE': '94', 'HEADING': '94', 'ELAPSED': 17,
             'SHIPNAME': '[SAT-AIS]', 'SHIPTYPE': '9', 'TYPE_IMG': '9', 'TYPE_NAME': 'Pleasure Craft',
             'STATUS_NAME': 'Unknown'},
            {'LAT': '-39.92724', 'LON': '-6.348073', 'SPEED': '196', 'COURSE': '112', 'HEADING': '112', 'ELAPSED': 124,
             'SHIPNAME': '[SAT-AIS]', 'SHIPTYPE': '9', 'TYPE_IMG': '9', 'TYPE_NAME': 'Pleasure Craft',
             'STATUS_NAME': 'Unknown'},
            {'LAT': '-39.95451', 'LON': '-7.403518', 'SPEED': '152', 'COURSE': '91', 'HEADING': '91', 'ELAPSED': 111,
             'SHIPNAME': '[SAT-AIS]', 'SHIPTYPE': '9', 'TYPE_IMG': '9', 'TYPE_NAME': 'Pleasure Craft',
             'STATUS_NAME': 'Unknown'},
            {'LAT': '-40.81548', 'LON': '-7.297678', 'SPEED': '143', 'COURSE': '96', 'HEADING': '96', 'ELAPSED': 15,
             'SHIPNAME': '[SAT-AIS]', 'SHIPTYPE': '9', 'TYPE_IMG': '9', 'TYPE_NAME': 'Pleasure Craft',
             'STATUS_NAME': 'Unknown'},
            {'LAT': '-41.12354', 'LON': '-5.118488', 'SPEED': '133', 'COURSE': '110', 'HEADING': '110', 'ELAPSED': 264,
             'SHIPNAME': '[SAT-AIS]', 'SHIPTYPE': '9', 'TYPE_IMG': '9', 'TYPE_NAME': 'Pleasure Craft',
             'STATUS_NAME': 'Unknown'},
            ]

for boatdata in response:
    tm = datetime.datetime.now()
    tm = tm - datetime.timedelta(minutes=int(boatdata['ELAPSED']), seconds=tm.second,
                                 microseconds=tm.microsecond)
    boatdata['ELAPSED'] = tm.timestamp()


class Test(TestCase):
    def test_calculate_distance(self):
        self.assertAlmostEqual(utils.EarthFunctions.calculate_distance((0, 0), (1, 1)), 84.9079932, 3)
        self.assertAlmostEqual(utils.EarthFunctions.calculate_distance((2, 3), (4, 5)), 169.6996215, 3)

    def test_great_circle_destination(self):
        lat, lon = utils.EarthFunctions.gcd((52.20472, 0.14056), 90, 15)
        self.assertAlmostEqual(lat, 52.20444, 3)
        self.assertAlmostEqual(lon, 0.548271, 3)

    def test_unpack_boats(self):
        self.assertListEqual(utils.unpack_boats([b'{}']), [])
        self.assertListEqual(utils.unpack_boats([b'test']), [])
        self.assertListEqual(utils.unpack_boats([b'{"data":"AA"}']), [])
        self.assertListEqual(utils.unpack_boats([b'[]']), [])
        self.assertListEqual(utils.unpack_boats([b'']), [])
        self.assertListEqual(utils.unpack_boats([b'180731']), [])
        self.assertListEqual(utils.unpack_boats([
            b'{"type":1,"data":{"rows":[{"LAT":"-42.18295","LON":"9.222814","SPEED":"138","COURSE":"76",'
            b'"HEADING":"76","ELAPSED":"3","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"8",'
            b'"SHIP_ID":"TkRrMU1UUTJORGsxTVRRMk5EazFNUT09LWIzRTZkd2Uzbnd4SkM2bFdoTEtZZ0E9PQ==","TYPE_IMG":"8",'
            b'"TYPE_NAME":"Tanker","STATUS_NAME":"Underway using Engine"},{"LAT":"-50.02695","LON":"32.10826",'
            b'"SPEED":"130","COURSE":"308","HEADING":"308","ELAPSED":"4","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"3",'
            b'"SHIP_ID":"TVRJeE5qSTVNVEl4TmpJNU1USXhOZz09LSszbndXdUtjRm5iTm5VcCtuQjZlaFE9PQ==","TYPE_IMG":"3",'
            b'"TYPE_NAME":"Tugs & Special Craft","STATUS_NAME":"Underway using Engine"},{"LAT":"-44.65273",'
            b'"LON":"36.45672","SPEED":"82","COURSE":"52","HEADING":"52","ELAPSED":"3","SHIPNAME":"[SAT-AIS]",'
            b'"SHIPTYPE":"2","SHIP_ID":"TmpBd05qUTNOakF3TmpRM05qQXdOZz09LUxlNUhyOFA0eUhZekV1OGtjZDJGL0E9PQ==",'
            b'"TYPE_IMG":"2","TYPE_NAME":"Fishing","STATUS_NAME":"Underway using Engine"},{"LAT":"-65.46892",'
            b'"LON":"35.51491","SPEED":"2","COURSE":"191","HEADING":"191","ELAPSED":"37","SHIPNAME":"[SAT-AIS]",'
            b'"SHIPTYPE":"2","SHIP_ID":"T1RFM056VTRPVEUzTnpVNE9URTNOdz09LTludEE5N015RUVsRGlXZzI5dnZ3QXc9PQ==",'
            b'"TYPE_IMG":"2","TYPE_NAME":"Fishing","STATUS_NAME":"Unknown"},{"LAT":"-61.67232","LON":"35.1214",'
            b'"SPEED":"5","COURSE":"346","HEADING":"346","ELAPSED":"103","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"2",'
            b'"SHIP_ID":"T1RrME1UazVPVGswTVRrNU9UazBNUT09LUltM2pidDZkeEl1czUvYUNjdS93SWc9PQ==","TYPE_IMG":"2",'
            b'"TYPE_NAME":"Fishing","STATUS_NAME":"Unknown"},{"LAT":"-66.6423","LON":"34.71627","SPEED":"36",'
            b'"COURSE":"246","HEADING":"246","ELAPSED":"104","SHIPNAME":"[SAT-AIS]","SHIPTYPE":"2",'
            b'"SHIP_ID":"T1RrME5qa3dPVGswTmprd09UazBOZz09LWlFYm91cHZkZ1BZamtKbG50SkpacFE9PQ==","TYPE_IMG":"2",'
            b'"TYPE_NAME":"Fishing","STATUS_NAME":"Unknown"}],"areaShips":6}}']),
            [])
        self.assertListEqual(utils.unpack_boats([request]), response)

    def test_handle_data(self):
        self.assertEqual(utils.handle_data('TEST',
                                           {'LAT': '-41.12354', 'LON': '-5.118488', 'SPEED': '133', 'COURSE': '110',
                                            'HEADING': '110', 'ELAPSED': 1606658751,
                                            'SHIPNAME': '[SAT-AIS]', 'SHIPTYPE': '9', 'TYPE_IMG': '9',
                                            'TYPE_NAME': 'Pleasure Craft',
                                            'STATUS_NAME': 'Unknown'}),
                         'TEST--------->LAT:  -41.1235 LON:  -5.11850, SPEED: 13.3, HEADING: 110, TIME: 2020-11-29 15:05:51')
