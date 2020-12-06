import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys

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

plt.rc('axes', labelsize=14)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=14)    # fontsize of the tick labels
plt.rc('ytick', labelsize=14)    # fontsize of the tick labels
plt.rc('legend', fontsize=14)    # legend fontsize

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

# overview
plt.figure()

det = df[(df['sys']=='ebbrt_tuned') & (df['msg']==MMSG)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['msg']==MMSG)].copy()
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xFFFF') & (df['msg']==MMSG)].copy()

#plt.title('NetPIPE - 8KB')
plt.errorbar(det['joules'], det['time'], fmt='x', label=LABELS[det['sys'].max()], c=COLORS['ebbrt_tuned'], alpha=0.5)
plt.errorbar(dlt['joules'], dlt['time'], fmt='*', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned'], alpha=0.5)
plt.errorbar(dld['joules'], dld['time'], fmt='o', label=LABELS[dld['sys'].max()], c=COLORS['linux_default'], alpha=0.5)

plt.ylabel("Time (secs)")
plt.xlabel("Energy Consumed (Joules)")
plt.legend(loc='lower right')
plt.grid()
plt.show()
plt.savefig(f'netpipe_{MMSG}_overview.pdf')

### throughput graphs
bconf={}
bconf['linux_default'] = [1, '0xFFFF']

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
        plt.text(x_offset + msg, y_offset + (0.1) + tput, label)
    elif msg == (524288/1000.0):        
        plt.text(x_offset + (-55) + msg, y_offset + (0.1) + tput, label)
    else:
        plt.text(x_offset + msg, y_offset + y_linux_offset + tput, label)

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
        plt.text(x_offset + (-55) + msg, y_offset + y_linux_offset + tput, label)
    else:
        plt.text(x_offset + msg, y_offset + y_linux_offset + tput, label)

#plot 1: throughput vs msg size
#1a: default linux
d = df_comb[(df_comb['sys']=='linux_default') & (df_comb['itr']==1) & (df_comb['dvfs']=='0xFFFF')].copy()
d.sort_values(by='msg', ascending=True, inplace=True)
plt.errorbar(d['msg'], d['tput_mean'], yerr=d['tput_std'], label=LABELS[d['sys'].max()], fmt=FMTS[d['sys'].max()], c=COLORS[d['sys'].max()], markersize=10)

#plt.xticks([64, MMSG, 65536, 524288], ('64', '8K', '64K', '512K'), rotation=40)
plt.xlabel("Message Size (KB)")
plt.ylabel("Throughput (Gb/s)")
plt.legend()
plt.grid()
plt.savefig('netpipe_tput.pdf')
plt.show()

'''
### timeline plot prep
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bconf[b['sys']] = [b['itr'], b['dvfs']]
print(bconf)

if MMSG == 8192:
    bconf['linux_tuned'] = [8, '0x1900']
#bconf['linux_tuned'] = [0, '0x1500']
#bconf['linux_tuned'] = [12, '0x1500']

ddfs = {}
lddf = pd.DataFrame()
lddfn = pd.DataFrame()
ltdf = pd.DataFrame()
ltdfn = pd.DataFrame()
etdf = pd.DataFrame()
etdfn = pd.DataFrame()

for dsys in ['ebbrt_tuned', 'linux_tuned', 'linux_default']:
    fname=''
    ditr = 0
    ddvfs=''
    ditr = bconf[dsys][0]
    ddvfs = bconf[dsys][1]
    
    if dsys == 'linux_default':
        fname = f'{log_loc}/linux.dmesg.1_{MMSG}_5000_{ditr}_{ddvfs}_135.csv'
        lddf, lddfn = updateDF(fname)
        ddfs[dsys] = [lddf, lddfn]
    elif dsys == 'linux_tuned':        
        fname = f'{log_loc}/linux.dmesg.1_{MMSG}_5000_{ditr}_{ddvfs}_135.csv'
        ltdf, ltdfn = updateDF(fname)
        ddfs[dsys] = [ltdf, ltdfn]
    else:
        fname = f'{log_loc}/ebbrt.dmesg.1_{MMSG}_5000_{ditr}_{ddvfs}_135.csv'
        etdf, etdfn = updateDF(fname)
        ddfs[dsys] = [etdf, etdfn]
        
## EDP        
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    ditr = bconf[dsys][0]
    ddvfs = bconf[dsys][1]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    print(dsys)
    plt.plot(ddfn['timestamp_non0'], ddfn['joules'], LINES[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[0], ddfn['joules'].iloc[0], HATCHS[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[-1], ddfn['joules'].iloc[-1], HATCHS[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[::140], ddfn['joules'].iloc[::140], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)    
    btime = ddf['timestamp_diff'].sum()
    bjoules = ddfn['joules_diff'].sum()
    if 'tuned' in dsys:
        plt.text(x_offset + btime, y_offset + bjoules, f'({ditr}, {ddvfs}, {135})')
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_edp.pdf')

## joule timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    ditr = bconf[dsys][0]
    ddvfs = bconf[dsys][1]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    
    plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
    btime = ddf['timestamp_diff'].sum()
    bjoules = ddfn['joules_diff'].sum()
    #if 'tuned' in dsys:
    #    plt.text(x_offset + btime, y_offset + bjoules, f'({ditr}, {ddvfs}, {135})')
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_joule_timeline.pdf')

## nonidle timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    ditr = bconf[dsys][0]
    ddvfs = bconf[dsys][1]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    
    plt.plot(ddfn['timestamp_non0'], ddfn['nonidle_frac_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
    btime = ddf['timestamp_diff'].sum()
    bjoules = ddfn['joules_diff'].sum()
plt.xlabel("Time (secs)")
plt.ylabel("Nonidle Time (%)")
plt.ylim((0, 1.001))
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_nonidle_timeline.pdf')

#bar plots
metric_labels = ['Instructions', 'Energy', 'RefCycles', 'TxBytes', 'Interrupts']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops

fig, ax = plt.subplots(1)

idx = np.arange(N_metrics) #one group per metric
width = 0.2
data_dict = {}

for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    data_dict[dsys] = np.array([ddfn['instructions_diff'].sum(),
                                ddfn['joules_diff'].sum(),
                                ddfn['ref_cycles_diff'].sum(),
                                ddf['tx_bytes'].sum(),
                                ddf.shape[0]])
counter = 0
for sys in data_dict: #normalize and plot
    data = data_dict[sys] / data_dict['linux_default']    
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1
    
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15)
plt.legend()
#plt.legend(loc='lower left')
plt.savefig(f'netpipe_{MMSG}_barplot.pdf')
'''    
        
'''
det = df[(df['sys']=='ebbrt_tuned')].copy()
dlt = df[(df['sys']=='linux_tuned')].copy()
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xFFFF')].copy()

for d in [dld, dlt, det]:
#    for m in [64/1000.0, 8192/1000.0, 65536/1000.0, 524288/1000.0]:
    for m in [8192/1000.0]:
        dbest = d[d['msg'] == m].copy()
        dbest['edp'] = dbest['joules'] * dbest['time']
        b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
        print('Best EPP', m)
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['edp'], 3)} {round(b['time'],3)}")
    
        b = dbest[dbest.joules==dbest.joules.min()].iloc[0] 
        print('Best Joules', m)
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'],3)} {round(b['time'],3)}")

        b = dbest[dbest.time==dbest.time.min()].iloc[0]
        print('Best Time', m)
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'], 3)} {round(b['time'],3)}")
        print('')
'''
