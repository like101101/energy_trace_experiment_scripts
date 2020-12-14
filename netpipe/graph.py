import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys
from matplotlib.lines import Line2D

COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'llc_miss', 'joules', 'timestamp']
DEFAULT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

def updateDF(fname):
    print(fname)
    df = pd.read_csv(fname, sep=' ', names=DEFAULT_COLS, skiprows=1)
    df = df.iloc[150:]
    
    df['timestamp'] = df['timestamp'] - df['timestamp'].min()
    df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
    
    # update timestamp_diff
    df['timestamp_diff'] = df['timestamp'].diff()
    df.dropna(inplace=True)
        
    ## convert global_linux_tuned_df_non0j
    df_non0j = df[df['joules'] > 0
                  & (df['instructions'] > 0)
                  & (df['cycles'] > 0)
                  & (df['ref_cycles'] > 0)
                  & (df['llc_miss'] > 0)].copy()
    df_non0j['timestamp_non0'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
    df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
    df_non0j['joules'] = df_non0j['joules'] - df_non0j['joules'].min()
    tmp = df_non0j[['instructions', 'ref_cycles', 'cycles', 'joules', 'timestamp_non0', 'llc_miss']].diff()
    tmp.columns = [f'{c}_diff' for c in tmp.columns]
    df_non0j = pd.concat([df_non0j, tmp], axis=1)
    df_non0j['ref_cycles_diff'] = df_non0j['ref_cycles_diff'] * TIME_CONVERSION_khz
    df_non0j.dropna(inplace=True)
    df_non0j['nonidle_frac_diff'] = df_non0j['ref_cycles_diff'] / df_non0j['timestamp_non0_diff']
    return df, df_non0j

plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
plt.rc('ytick', labelsize=20)    # fontsize of the tick labels
plt.rc('legend', fontsize=20)    # legend fontsize

plt.ion()

x_offset, y_offset = 0.01/5, 0.01/5

JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

if len(sys.argv) != 2:
    print("graph.py <MMSG>")
    exit()
MMSG = int(sys.argv[1])

workload_loc='/scratch2/netpipe/netpipe_combined/netpipe_combined.csv'
log_loc='/scratch2/netpipe/netpipe_combined/'

COLORS = {'linux_default': 'blue',
          'linux_tuned': 'green',
          'ebbrt_tuned': 'red'}          
LABELS = {'linux_default': 'Linux Default',
          'linux_tuned': 'Linux Tuned',
          'ebbrt_tuned': 'LibOS Tuned'}
FMTS = {'linux_default': 'o--',
          'linux_tuned': '*-.',
          'ebbrt_tuned': 'x:'}
LINES = {'linux_default': '--',
          'linux_tuned': '-.',
          'ebbrt_tuned': ':'}
HATCHS = {'linux_default': 'o',
          'linux_tuned': '*',
          'ebbrt_tuned': 'x'}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df['edp'] = df['joules'] * df['time']
df['tput'] = df['tput']/1000.0

det = df[(df['sys']=='ebbrt_tuned') & (df['msg']==MMSG)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['msg']==MMSG)].copy()
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xFFFF') & (df['msg']==MMSG)].copy()

bconf={}

'''
# overview
plt.figure()

for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bconf[b['sys']] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
    
#plt.title('NetPIPE - 8KB')
plt.errorbar(det['joules'], det['time'], fmt='x', label=LABELS[det['sys'].max()], c=COLORS['ebbrt_tuned'], alpha=0.5)
plt.errorbar(dlt['joules'], dlt['time'], fmt='*', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned'], alpha=0.5)
plt.errorbar(dld['joules'], dld['time'], fmt='o', label=LABELS[dld['sys'].max()], c=COLORS['linux_default'], alpha=0.5)
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bjoules = b['joules']
    btime = b['time']
    plt.plot(bjoules,  btime, fillstyle='none', marker='o', markersize=15, c=COLORS[b['sys']])
    
plt.ylabel("Time (secs)")
plt.xlabel("Energy Consumed (Joules)")
plt.legend(loc='lower right')
plt.grid()
plt.show()
plt.savefig(f'netpipe_{MMSG}_overview.pdf')
'''
## prep

#plt.clf()
plt.figure()
df['msg'] = df['msg']/1000.0

NCOLS = ['sys', 'msg', 'itr', 'dvfs', 'rapl']
df_mean = df.groupby(NCOLS).mean()
df_std = df.groupby(NCOLS).std()

df_mean.columns = [f'{c}_mean' for c in df_mean.columns]
df_std.columns = [f'{c}_std' for c in df_std.columns]

df_comb = pd.concat([df_mean, df_std], axis=1)
df_comb.reset_index(inplace=True)

y_linux_offset = -0.4
#1c - ebbrt tuned
y_ebbrt_offset = -0.4
d = df_comb[(df_comb['sys']=='ebbrt_tuned') & (df_comb['itr']!=1) & (df_comb['dvfs']!='0xFFFF')].copy()
#keep it simple
msg_list, tput_list, tput_err_list, label_list = [], [], [], []
for msg in [64/1000.0, MMSG/1000.0, 65536/1000.0, 524288/1000.0]:
    e = d[d['msg']==msg]
    row_best_tput = e[e.tput_mean==e.tput_mean.max()].iloc[0]
    
    msg_list.append(row_best_tput['msg'])
    tput_list.append(row_best_tput['tput_mean'])
    tput_err_list.append(row_best_tput['tput_std'])
    label_list.append(f"({row_best_tput['itr']}, {row_best_tput['dvfs']}, *)")
    if msg == MMSG/1000.0:
        bconf[row_best_tput['sys']] = [row_best_tput['itr'], row_best_tput['dvfs']]
    
plt.errorbar(msg_list, tput_list, yerr=tput_err_list, label=LABELS[d['sys'].max()], fmt=FMTS[d['sys'].max()], c=COLORS[d['sys'].max()], markersize=10)
for idx, (msg, tput, label) in enumerate(zip(msg_list, tput_list, label_list)):
    if msg == (64/1000.0):        
        plt.text(x_offset + msg, y_offset + (0.1) + tput, label, fontsize=14)
    elif msg == (524288/1000.0):        
        plt.text(x_offset + (-55) + msg, y_offset + (0.1) + tput, label, fontsize=14)
    else:
        plt.text(x_offset + msg, y_offset + y_linux_offset + tput, label, fontsize=14)

#1b: tuned linux - best for each message size
d = df_comb[(df_comb['sys']=='linux_tuned') & (df_comb['itr']!=1) & (df_comb['dvfs']!='0xFFFF')].copy()
#keep it simple
msg_list, tput_list, tput_err_list, label_list = [], [], [], []
for msg in [64/1000.0, MMSG/1000.0, 65536/1000.0, 524288/1000.0]:
    e = d[d['msg']==msg]
    row_best_tput = e[e.tput_mean==e.tput_mean.max()].iloc[0]
    
    msg_list.append(row_best_tput['msg'])
    tput_list.append(row_best_tput['tput_mean'])
    tput_err_list.append(row_best_tput['tput_std'])
    label_list.append(f"({row_best_tput['itr']}, {row_best_tput['dvfs']}, *)")
    if msg == MMSG/1000.0:
        bconf[row_best_tput['sys']] = [row_best_tput['itr'], row_best_tput['dvfs']]
        
plt.errorbar(msg_list, tput_list, yerr=tput_err_list, label=LABELS[d['sys'].max()], fmt=FMTS[d['sys'].max()], c=COLORS[d['sys'].max()], markersize=10)
for idx, (msg, tput, label) in enumerate(zip(msg_list, tput_list, label_list)):
    if msg == (64/1000.0):        
        plt.text(x_offset + msg, y_offset + (-0.2) + tput, label)
    elif msg == (524288/1000.0):        
        plt.text(x_offset + (-55) + msg, y_offset + y_linux_offset + tput, label, fontsize=14)
    else:
        plt.text(x_offset + msg, y_offset + y_linux_offset + tput, label, fontsize=14)

#plot 1: throughput vs msg size
#1a: default linux
d = df_comb[(df_comb['sys']=='linux_default') & (df_comb['itr']==1) & (df_comb['dvfs']=='0xFFFF')].copy()
d.sort_values(by='msg', ascending=True, inplace=True)
plt.errorbar(d['msg'], d['tput_mean'], yerr=d['tput_std'], label=LABELS[d['sys'].max()], fmt=FMTS[d['sys'].max()], c=COLORS[d['sys'].max()], markersize=10)

#plt.xticks([64, MMSG, 65536, 524288], ('64', '8K', '64K', '512K'), rotation=40)
#plt.yscale('log')
plt.xlabel("Message Size (KB)")
plt.ylabel("Throughput (Gb/s)")
plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig('netpipe_tput.pdf')
plt.show()

