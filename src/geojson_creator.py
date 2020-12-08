import datetime
import json

from geojson import Feature, Point, FeatureCollection


def create_geojson(_datafile):
    list_of_features = []
    for item in _datafile:
        points = _datafile.get(item)
        if not points:
            continue
        data = points[-1]
        my_point = Point((float(data.get('LON')), float(data.get('LAT'))))

        properties = {'Name': item, 'Speed': float(data.get('SPEED')) / 10, "Heading": float(data.get('COURSE')),
                      "Time": str(datetime.datetime.fromtimestamp(data.get('ELAPSED')))}
        A = Feature(geometry=my_point, properties=properties)
        list_of_features.append(A)

    A = FeatureCollection(list_of_features)

    with open('./positions.geojson', 'w') as outfile:
        json.dump(A, outfile)


# Convert to GPX does not really work...
# feature_list = []
# for item in datafile:
#     points = datafile.get(item)
#     data = points[-1]
#     record = {"LON": float(data.get('LON')), "LAT": float(data.get('LAT')), 'Name': item, 'Speed': float(
#         data.get('SPEED')) / 10, "Heading": float(data.get('COURSE')),
#               "Time": str(datetime.datetime.fromtimestamp(data.get('ELAPSED')))}
#     feature_list.append(record)
# df = pd.DataFrame.from_records(feature_list)
#
# Converter.dataframe_to_gpx(input_df=df,
#                            lats_colname='LAT',
#                            longs_colname='LON',
#                            output_file='your_output.gpx')

if __name__ == "__main__":
    with open('data.json') as json_file:
        datafile = json.load(json_file)
