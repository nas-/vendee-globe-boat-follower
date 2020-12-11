import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import random
from typing import Dict


def plot(data_file: Dict, number_of_points: int) -> None:
    """
    :param number_of_points: number of points per boat to plot
    :type data_file: Dictionary of all boat values
    """
    sns.set(rc={'figure.figsize': (23.4, 16.54)})
    df = pd.DataFrame()
    for record in data_file:
        data = data_file.get(record)
        df_temp = pd.DataFrame.from_records(data)
        df_temp['BOAT'] = record
        df = df.append(df_temp, ignore_index=True)

    df[['LON', 'LAT', 'SPEED']] = df[['LON', 'LAT', 'SPEED']].astype(float)
    df['SPEED'] = df['SPEED'] / 10
    all_boats = data_file.keys()
    all_markers = [',', '.', 'o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X']
    markers = {"BOSS": "s", "APIVIA": "X", 'LINKED': "*", 'CAM': "o"}
    for boat in all_boats:
        if boat not in markers.keys():
            markers[boat] = random.choice(all_markers)
    df = df.sort_values('ELAPSED').groupby('BOAT').tail(number_of_points).reset_index(drop=True)
    plt.figure(figsize=(20, 10))
    sns_plot = sns.scatterplot(data=df, x='LON', y='LAT', style='BOAT', markers=markers, hue='SPEED', size='SPEED')
    labels = set()
    for line in range(0, df.shape[0], 5):
        if df['BOAT'][line] not in labels:
            sns_plot.text(df['LON'][line] - 2, df['LAT'][line],
                          df['BOAT'][line])
            labels.add(df['BOAT'][line])
        sns_plot.text(df['LON'][line] + 0.02, df['LAT'][line],
                      df['SPEED'][line], horizontalalignment='left',
                      size='small', color='black')

    sns_plot.get_figure().savefig("output.png")
    plt.close()


if __name__ == "__main__":
    with open('data.json') as json_file:
        datafile = json.load(json_file)
    plot(datafile, 100)
