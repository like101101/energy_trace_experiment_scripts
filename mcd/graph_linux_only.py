import pandas as pd
import numpy as np
#from mpl_toolkits.axes_grid.inset_locator import inset_axes
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys
                                
plt.rc('axes', labelsize=19)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=19)    # fontsize of the tick labels
plt.rc('ytick', labelsize=19)    # fontsize of the tick labels
plt.rc('legend', fontsize=19)    # legend fontsize
#plt.rcParams['ytick.right'] = plt.rcParams['ytick.labelright'] = True
#plt.rcParams['ytick.left'] = plt.rcParams['ytick.labelleft'] = False
#plt.rcParams['figure.figsize'] = 18, 8

#QPS=600000
if len(sys.argv) != 2:
    print("graph.py <QPS>")
    exit()
QPS = int(sys.argv[1])

x_offset, y_offset = 0.01/5, 0.01/5
LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

def updateDF(fname, START_RDTSC, END_RDTSC, ebbrt=False):
    df = pd.DataFrame()
    if ebbrt:
        df = pd.read_csv(fname, sep=' ', names=EBBRT_COLS, skiprows=1)
        df['c1'] = 0
        df['c1e'] = 0
    else:
        df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
    ## filter out timestamps
    df = df[df['timestamp'] >= START_RDTSC]
    df = df[df['timestamp'] <= END_RDTSC]
    #converting timestamps
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
    tmp = df_non0j[['instructions', 'ref_cycles', 'cycles', 'joules', 'timestamp_non0', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
    tmp.columns = [f'{c}_diff' for c in tmp.columns]
    df_non0j = pd.concat([df_non0j, tmp], axis=1)
    df_non0j['ref_cycles_diff'] = df_non0j['ref_cycles_diff'] * TIME_CONVERSION_khz    
    df_non0j.dropna(inplace=True)
    df_non0j['nonidle_frac_diff'] = df_non0j['ref_cycles_diff'] / df_non0j['timestamp_non0_diff']
    return df, df_non0j

JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

workload_loc='/scratch2/mcd/mcd_combined_11_9_2020/mcd_combined.csv'
log_loc='/scratch2/mcd/mcd_combined_11_9_2020/'

COLORS = {'linux_default': 'blue',
          'linux_tuned_joule': 'green',
          'linux_tuned_tail': 'red'}
LABELS = {'linux_default': 'Default',
          'linux_tuned_joule': 'MinEnergy',
          'linux_tuned_tail': 'MinTailLat'}
FMTS = {'linux_default':   'o--',
          'linux_tuned_joule':   '*-.',
          'linux_tuned_tail':   'x:'}
LINES = {'linux_default':  '--',
          'linux_tuned_joule':   '-.',
          'linux_tuned_tail':   ':'}
HATCHS = {'linux_default': 'o',
          'linux_tuned_joule':   '*',
          'linux_tuned_tail':   'x'}

CALPHA= {'linux_default': 0.01,
          'linux_tuned_joule':   0.5,
          'linux_tuned_tail':   0.5}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df = df[df['read_99th'] <= 500.0]
df['edp'] = df['joules'] * df['read_99th']
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff') & (df['target_QPS'] == QPS)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['target_QPS'] == QPS)].copy()

## prep
bconf={}

## Linux Default - use EPP for now
b = dld[dld.edp==dld.edp.min()].iloc[0]
bconf['linux_default'] = [b['i'], b['itr'], b['dvfs'], b['rapl']]

## Linux tuned for min energy use
b = dlt[dlt.joules==dlt.joules.min()].iloc[0]
bconf['linux_tuned_joule'] = [b['i'], b['itr'], b['dvfs'], b['rapl']]

## Linux tuned for min tail latency
b = dlt[dlt.read_99th==dlt.read_99th.min()].iloc[0]
bconf['linux_tuned_tail'] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
print(bconf)

ddfs = {}
for dsys in ['linux_tuned_joule', 'linux_tuned_tail', 'linux_default']:
    fname=''    
    START_RDTSC=0
    END_RDTSC=0
    i = bconf[dsys][0]
    itr = bconf[dsys][1]
    dvfs = bconf[dsys][2]
    rapl = bconf[dsys][3]
    qps = QPS
    core=0
    
    if 'linux_tuned' in dsys or dsys == 'linux_default':        
        frdtscname = f'{log_loc}/linux.mcd.rdtsc.{i}_{itr}_{dvfs}_{rapl}_{qps}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            if int(tmp[2]) > START_RDTSC:                                
                START_RDTSC = int(tmp[2])
            
            if END_RDTSC == 0:                                
                END_RDTSC = int(tmp[3])
            elif END_RDTSC < int(tmp[3]):
                END_RDTSC = int(tmp[3])                                                            
        frdtsc.close()

        fname = f'{log_loc}/linux.mcd.dmesg.{i}_{core}_{itr}_{dvfs}_{rapl}_{qps}'
        if 'linux_tuned' in dsys:
            ltdf, ltdfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [ltdf, ltdfn]
        elif dsys == 'linux_default':
            lddf, lddfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [lddf, lddfn]

print(dlt)

'''
fig, ax = plt.subplots(1)
#ax.yaxis.set_label_position("right")
#plt.errorbar(dlt['joules'], dlt['read_99th'], fmt='x', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned_tail'], alpha=1)
plt.errorbar(dlt['joules'], dlt['read_99th'], fmt='o', label='Tuned', c='brown', alpha=0.8)
plt.errorbar(dld['joules'], dld['read_99th'], fmt='o', label=LABELS['linux_default'], c=COLORS['linux_default'], alpha=0.8)

## min joules
b = dlt[dlt.joules==dlt.joules.min()].iloc[0]
bjoules = b['joules']
btail = b['read_99th']
plt.plot(bjoules,  btail, fillstyle='none', marker='*', markersize=20, c=COLORS['linux_tuned_joule'])

## min tail
b = dlt[dlt.read_99th==dlt.read_99th.min()].iloc[0]
bjoules = b['joules']
btail = b['read_99th']
plt.plot(bjoules, btail, fillstyle='none', marker='x', markersize=20, c=COLORS['linux_tuned_tail'])
plt.ylabel("99% Tail Latency (usecs)")
plt.xlabel("Energy Consumed (Joules)")

plt.legend()
plt.grid()
plt.tight_layout()
ax.legend(markerscale=3)
#plt.savefig(f'mcd_linux_{QPS}_overview.png')


### cstates subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex='col', sharey='row', gridspec_kw={'hspace':0, 'wspace': 0})
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ax1.plot(ddfn['timestamp_non0'], ddfn['c1_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
    ax2.plot(ddfn['timestamp_non0'], ddfn['c1e_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
    ax3.plot(ddfn['timestamp_non0'], ddfn['c3_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
    ax4.plot(ddfn['timestamp_non0'], ddfn['c7_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
    ax1.set_xticks([])
    ax2.set_xticks([])
    ax3.set_xticks([])
    ax4.set_xticks([])
    ax1.set_yticks([])
    ax2.set_yticks([])
    ax3.set_yticks([])
    ax4.set_yticks([])
    ax1.set_ylabel('C1')
    ax2.set_ylabel('C1E')
    ax3.set_ylabel('C3')
    ax4.set_ylabel('C7')
    ax2.yaxis.set_label_position("right")
    ax4.yaxis.set_label_position("right")
    ax2.legend(loc='upper left', markerscale=3)

plt.tight_layout()
'''
'''
## c1 timeline
fig, ax = plt.subplots(1)
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    plt.plot(ddfn['timestamp_non0'], ddfn['c1_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
plt.xlabel("Time (secs)")
plt.ylabel("C1")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.tight_layout()
ax.legend(markerscale=3)

## c1e timeline
fig, ax = plt.subplots(1)
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    plt.plot(ddfn['timestamp_non0'], ddfn['c1e_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
plt.xlabel("Time (secs)")
plt.ylabel("C1E")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.tight_layout()
ax.legend(markerscale=3)
#plt.savefig(f'mcd_linux_{QPS}_c1e_timeline.png')

## c3 timeline
fig, ax = plt.subplots(1)
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    plt.plot(ddfn['timestamp_non0'], ddfn['c3_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
plt.xlabel("Time (secs)")
plt.ylabel("C3")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.tight_layout()
ax.legend(markerscale=3)
#plt.savefig(f'mcd_linux_{QPS}_c3_timeline.png')

#plt.savefig(f'mcd_linux_{QPS}_c1_timeline.png')

## c7 timeline
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    plt.plot(ddfn['timestamp_non0'], ddfn['c7_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=CALPHA[dsys])
plt.xlabel("Time (secs)")
plt.ylabel("C7")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
ax.legend(markerscale=3)
plt.tight_layout()
#plt.savefig(f'mcd_linux_{QPS}_c7_timeline.png')
'''
## nonidle timeline
fig, ax = plt.subplots(1)
#ax.yaxis.set_label_position("right")
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['nonidle_frac_diff'] > 0) & (ddfn['nonidle_frac_diff'] < 1.1)]
    plt.plot(ddfn['timestamp_non0'], ddfn['nonidle_frac_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Nonidle Time (%)")
plt.ylim((0, 1.1))
plt.grid()
ax.legend(markerscale=3, loc='upper right')
plt.tight_layout()
#plt.savefig(f'mcd_linux_{QPS}_nonidle_timeline.png')

## joule timeline
fig, ax = plt.subplots(1)
#ax.yaxis.set_label_position("right")
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['joules_diff'] > 0) & (ddfn['joules_diff'] < 3000)]
    plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend(markerscale=3, loc='upper right')
plt.grid()
plt.tight_layout()
#plt.savefig(f'mcd_linux_{QPS}_joules_timeline.png')

## instructions timeline
#plt.figure()
fig, ax = plt.subplots(1)
#ax.yaxis.set_label_position("right")
for dsys in ['linux_tuned_joule', 'linux_tuned_tail']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['instructions_diff'] > 0) & (ddfn['instructions_diff'] < 250000000)]
    plt.plot(ddfn['timestamp_non0'], ddfn['instructions_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Instructions")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend(markerscale=3, loc='upper right')
plt.grid()
plt.tight_layout()
#plt.savefig(f'mcd_linux_{QPS}_instructions_timeline.png')

#### bar plot
metric_labels = ['CPI', 'Instructions', 'Cycles', 'RxBytes', 'TxBytes', 'Interrupts']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops
fig, ax = plt.subplots(1)
idx = np.arange(N_metrics) #one group per metric
width = 0.2
data_dict = {}

for dsys in ['linux_tuned_joule', 'linux_tuned_tail', 'linux_default']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    data_dict[dsys] = np.array([(ddfn['ref_cycles_diff'].sum()/ddfn['instructions_diff'].sum()),
                                ddfn['instructions_diff'].sum(),
                                ddfn['ref_cycles_diff'].sum(),
                                ddf['rx_bytes'].sum(),
                                ddf['tx_bytes'].sum(),
                                ddf.shape[0]])
counter=0
last=0
for sys in data_dict: #normalize and plot
    data = data_dict[sys] / data_dict['linux_default'] 
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1
    
idx = np.arange(N_metrics) #one group per metric
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15, fontsize=14)
plt.legend()
plt.tight_layout()
#plt.savefig(f'nodejs_barplot.pdf')
plt.show()

'''
## c6 timeline
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
for dsys in ['linux_default', 'linux_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    plt.plot(ddfn['timestamp_non0'], ddfn['c6_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("C6")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig(f'mcd_linux_{QPS}_c6_timeline.png')

'''

'''
##rxbyte timeline
plt.figure()
for dsys in ['linux_tuned', 'linux_default']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    #ddf = ddf[(ddf['timestamp'] > 10) & (ddf['timestamp'] < 15)]
    plt.plot(ddf['timestamp'], ddf['rx_bytes'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.2)
plt.xlabel("Time (secs)")
plt.ylabel("RxBytes")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
#plt.legend()
plt.grid()
plt.savefig(f'mcd_linux_{QPS}_rxbytes_timeline.png')

## txbyte timeline
plt.figure()
for dsys in ['linux_tuned', 'linux_default']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddf['timestamp'], ddf['tx_bytes'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.2)
plt.xlabel("Time (secs)")
plt.ylabel("TxBytes")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
#plt.legend()
plt.grid()
plt.savefig(f'mcd_linux_{QPS}_txbytes_timeline.png')
'''

'''
#fig, ax = plt.figure()


## timediff timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddf['timestamp'], ddf['timestamp_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Time diff (usecs)")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.savefig(f'mcd_linux_{QPS}_timediff_timeline.png')

## llc_miss timeline
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
for dsys in ['linux_default', 'linux_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    plt.plot(ddfn['timestamp_non0'], ddfn['llc_miss_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("LLC_MISS")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig(f'mcd_linux_{QPS}_llc_miss_timeline.png')

'''
