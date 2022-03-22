import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt

def convert_to_df(df):
    res_df = df[['measure_QPS', 'joules']]
    return res_df

def plot_df(df):
    plt.plot(df)
    plt.show()

mcd_location = '/home/like/like_trace/energy_trace_experiment_scripts/mcd/like/mcd_symbio.csv'

df = pd.read_csv(mcd_location, sep=' ')
print(df.shape)
qps = df['measure_QPS'].tolist()
joules = df['joules'].tolist()
datas = list(zip(qps, joules))
print(datas[:10])
plt.plot(datas)
plt.show()
