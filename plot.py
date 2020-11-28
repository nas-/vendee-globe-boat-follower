import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns




def plot(data_file):
    sns.set(rc={'figure.figsize': (11.7, 8.27)})
    df = pd.DataFrame()
    for record in data_file:
        data = data_file.get(record)
        df_temp = pd.DataFrame.from_records(data)
        df_temp['BOAT'] = record
        df = df.append(df_temp, ignore_index=True)

    df[['LON', 'LAT', 'SPEED']] = df[['LON', 'LAT', 'SPEED']].astype(float)
    df['SPEED'] = df['SPEED'] / 10
    markers = {"BOSS": "s", "APIVIA": "X", 'LINKED': "*", 'CAM': "o", 'ARKEA': 'o', 'BURTON': 'X', 'INITIATIVE': 'o'}
    plt.figure(figsize=(20, 10))
    sns_plot = sns.scatterplot(data=df, x='LON', y='LAT', style='BOAT', markers=markers, hue='SPEED', size='SPEED')
    for line in range(0, df.shape[0]):
        sns_plot.text(df['LON'][line] + 0.02, df['LAT'][line],
                      df['SPEED'][line], horizontalalignment='left',
                      size='small', color='black')

    sns_plot.get_figure().savefig("output.png")


if __name__ == "__main__":
    with open('data.json') as json_file:
        datafile = json.load(json_file)
    plot(datafile)
