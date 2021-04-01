import pandas as pd
import numpy as np
import os
import glob
import sys

if len(sys.argv) != 2:
    print("combinations.py <FILENAME>")
    exit()
fname = sys.argv[1]

df = pd.read_csv(fname, sep=' ')

print('Column Names:')
print(df.columns)

# filter ebbrt and linux only dataset
df_ebbrt = df[(df['sys']=='ebbrt_tuned')].copy()
df_linux = df[(df['sys']=='linux_tuned')].copy()

print('EBBRT')
# number of iterations
print('i:', df_ebbrt['i'].unique())
# interrupt delay
print('itr:', df_ebbrt['itr'].unique())
# dvfs
print('dvfs:', df_ebbrt['dvfs'].unique())
# rapl
print('rapl:', df_ebbrt['rapl'].unique())
# target queries-per-second (QPS)
print('QPS:', df_ebbrt['target_QPS'].unique(), len(df_ebbrt['target_QPS'].unique()))
print('EbbRT combinations: ', len(df_ebbrt['itr'].unique()) * len(df_ebbrt['dvfs'].unique()) * len(df_ebbrt['rapl'].unique()))


print('')
print('LINUX')
# number of iterations
print('i', df_linux['i'].unique())
# interrupt delay
print('itr:', df_linux['itr'].unique())
# dvfs
print('dvfs:', df_linux['dvfs'].unique())
# rapl
print('rapl:', df_linux['rapl'].unique())
# target queries-per-second (QPS)
print('QPS:', df_linux['target_QPS'].unique())
print('Linux combinations: ', len(df_linux['itr'].unique()) * len(df_linux['dvfs'].unique()) * len(df_linux['rapl'].unique()))
