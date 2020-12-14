import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys

EBBRT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']
LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

idlestates={}
idlestates['C1'] = 2
idlestates['C1E'] = 15
idlestates['C3'] = 145
idlestates['C6'] = 224
idlestates['C7'] = 227

def updateDF(fname, START_RDTSC, END_RDTSC, isEbbRT=False):
    df = pd.DataFrame()
    if isEbbRT:
        df = pd.read_csv(fname, sep=' ', names=EBBRT_COLS)
    else:
        df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
    df = df.iloc[150:]
    #if isEbbRT:
    #    print(fname, START_RDTSC, END_RDTSC)
    #    print(df.shape[0])
    df = df[df['timestamp'] >= START_RDTSC]
    df = df[df['timestamp'] <= END_RDTSC]
    #if isEbbRT:
    #    print(df.shape[0])
        
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
    
    if isEbbRT == True:
        tmp = df_non0j[['instructions', 'ref_cycles', 'cycles', 'joules', 'timestamp_non0', 'llc_miss']].diff()
        tmp.columns = [f'{c}_diff' for c in tmp.columns]
        df_non0j = pd.concat([df_non0j, tmp], axis=1)
        df_non0j['c1_diff']=0
        df_non0j['c1e_diff']=0
        df_non0j['c3_diff']=0
        df_non0j['c6_diff']=0
        df_non0j['c7_diff']=df_non0j['c7']        
    else:
        #df_non0j['c1'] = df_non0j['c1'] - df_non0j['c1'].min()
        #df_non0j['c1e'] = df_non0j['c1e'] - df_non0j['c1e'].min()
        #df_non0j['c3'] = df_non0j['c3'] - df_non0j['c3'].min()
        #df_non0j['c6'] = df_non0j['c6'] - df_non0j['c6'].min()
        #df_non0j['c7'] = df_non0j['c7'] - df_non0j['c7'].min()
        tmp = df_non0j[['instructions', 'ref_cycles', 'cycles', 'joules', 'timestamp_non0', 'c1', 'c1e', 'c3', 'c6', 'c7', 'llc_miss']].diff()
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

workload_loc='/scratch2/netpipe/graph_data/netpipe_combined.csv'
log_loc='/scratch2/netpipe/graph_data/'

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
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff') & (df['msg']==MMSG)].copy()

bconf={}
bconf['linux_default'] = [1, '0xFFFF']

df['msg'] = df['msg']/1000.0

### timeline plot prep
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bconf[b['sys']] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
print(bconf)

ddfs = {}
lddf = pd.DataFrame()
lddfn = pd.DataFrame()
ltdf = pd.DataFrame()
ltdfn = pd.DataFrame()
etdf = pd.DataFrame()
etdfn = pd.DataFrame()

for dsys in ['ebbrt_tuned', 'linux_tuned', 'linux_default']:
    fname=''
    START_RDTSC=0
    END_RDTSC=0
    dnum = bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    
    if dsys == 'linux_default' or dsys == 'linux_tuned':
        fname = f'{log_loc}/linux.np.log.{dnum}_1_{MMSG}_5000_{ditr}_{ddvfs}_{drapl}'
        fnserver = f'{log_loc}/linux.np.server.{dnum}_1_{MMSG}_5000_{ditr}_{ddvfs}_{drapl}'
        
        f = open(fnserver, 'r')
        for line in f:
            if 'WORKLOAD' in line.strip():
                tmp = list(filter(None, line.strip().split(' ')))
                START_RDTSC = int(tmp[1])
                END_RDTSC = int(tmp[2])
                break
        f.close()

        if dsys == 'linux_default':
            lddf, lddfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [lddf, lddfn]
        elif dsys == 'linux_tuned':    
            ltdf, ltdfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [ltdf, ltdfn]
    else:
        fname = f'{log_loc}/ebbrt.dmesg.{dnum}_{MMSG}_5000_{ditr}_{ddvfs}_{drapl}'
        fnpout = f'{log_loc}/ebbrt.np.out.{dnum}_{MMSG}_5000_{ditr}_{ddvfs}_{drapl}'
        
        f = open(fnpout, 'r')
        for line in f:
            tmp = list(filter(None, line.strip().split(' ')))
            START_RDTSC = int(tmp[10])
            END_RDTSC = int(tmp[11])
            break
        f.close()
                                        
        etdf, etdfn = updateDF(fname, START_RDTSC, END_RDTSC, True)
        ddfs[dsys] = [etdf, etdfn]

#bar plots
metric_labels = ['CPI', 'Instructions', 'Cycles', 'RxBytes', 'TxBytes', 'Interrupts', 'Halt']
#metric_labels = ['CPI', 'Instructions', 'Cycles', 'Halt', 'RxBytes', 'TxBytes', 'Interrupts']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops

fig, ax = plt.subplots(1)

idx = np.arange(N_metrics-1) #one group per metric
width = 0.2
data_dict = {}

cstates_all={}
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    if 'ebbrt' in dsys:
        c_all = np.array([0, 0, 0, 0, int(ddfn['c7'].sum())])
    else:
        c_all=np.array([int(ddfn['c1_diff'].sum()), int(ddfn['c1e_diff'].sum()), int(ddfn['c3_diff'].sum()), int(ddfn['c6_diff'].sum()), int(ddfn['c7_diff'].sum())])
    cstates_all[dsys]=c_all
    #print(cstates_all[dsys], sum(cstates_all[dsys]))

for dsys in ['linux_tuned', 'ebbrt_tuned', 'linux_default']:
    cstates_all[dsys] = cstates_all[dsys]/sum(cstates_all['linux_default'])
    print(cstates_all[dsys])
                
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    #c_all = 0
    #if 'ebbrt' in dsys:
    #    c_all = np.array([0, 0, 0, 0, ddfn['c7'].sum()])
        #print(f"{dsys} c7={c_all}")
    #else:
        #c_all = ddfn['c1_diff'].sum() + ddfn['c1e_diff'].sum() + ddfn['c3_diff'].sum() + ddfn['c6_diff'].sum() + ddfn['c7_diff'].sum()
    #    c_all=np.array([ddfn['c1_diff'].sum(), ddfn['c1e_diff'].sum(), ddfn['c3_diff'].sum(), ddfn['c6_diff'].sum(), ddfn['c7_diff'].sum()])
        #print(f"{dsys} c1={ddfn['c1_diff'].sum()} c1e={ddfn['c1e_diff'].sum()} c3={ddfn['c3_diff'].sum()} c6={ddfn['c6_diff'].sum()} c7={ddfn['c7_diff'].sum()}")
    
    #print(len(c_all), c_all)
    data_dict[dsys] = np.array([ddfn['ref_cycles_diff'].sum()/ddfn['instructions_diff'].sum(),
                                ddfn['instructions_diff'].sum(),
                                ddfn['ref_cycles_diff'].sum(),
                                ddf['rx_bytes'].sum(),
                                ddf['tx_bytes'].sum(),
                                ddf.shape[0]])

counter = 0
last=0
for sys in data_dict: #normalize and plot
    #print(len(data_dict[sys]))
    data = data_dict[sys] / data_dict['linux_default']
    #print(idx + counter*width)
    last=(idx + counter*width)[len(idx + counter*width)-1]
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1

last = last+width

for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    #cstates_all[dsys] = cstates_all[dsys]/sum(cstates_all['linux_default'])
    #print(last)
    last = last + width
    bars=0
    for i in range(0, len(cstates_all[dsys])):
        llen=len(cstates_all[dsys])
        colors = plt.cm.BuPu(np.linspace(0, 1, llen))
        
        if 'linux_default' == dsys:
            colors = plt.cm.get_cmap('Blues', llen) #plt.cm.Blues(np.linspace(0, 1, len(cstates_all[dsys])))
        elif 'linux_tuned' == dsys:
            colors = plt.cm.get_cmap('Greens', llen) #plt.cm.Greens(np.linspace(0, 1, len(cstates_all[dsys])))
        else:
            colors = plt.cm.get_cmap('Reds', llen) #plt.cm.Reds(np.linspace(0, 1, len(cstates_all[dsys])))
            
        if i == 0:
            ax.bar(last, cstates_all[dsys][i], width=width, color=colors(i/llen), edgecolor='black', hatch=HATCHS[dsys])
        else:
            ax.bar(last, cstates_all[dsys][i], bottom=bars, width=width, color=colors(i/llen), edgecolor='black', hatch=HATCHS[dsys])
        bars = bars + cstates_all[dsys][i]

idx = np.arange(N_metrics) #one group per metric
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15, fontsize=14)
plt.legend()
#plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig(f'netpipe_{MMSG}_barplot.pdf')

## joule timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    
    #dwatts = ddfn[(ddfn['joules_diff'] > 0.0185) & (ddfn['joules_diff'] < 0.0192)]
    #tj = ddfn['joules_diff'].sum()
    #tjime = ddf['timestamp_diff'].sum()
    #print(dsys, tj/tjime)
    
    #ddfn = ddfn[(ddfn['joules_diff'] > 0.0185) & (ddfn['joules_diff'] < 0.02)]
    #ddfn = ddfn[(ddfn['timestamp_non0'] > 0.85) & (ddfn['timestamp_non0'] < 1.0)]

    #ddfn = ddfn[(ddfn['joules_diff'] > 0.01) & (ddfn['joules_diff'] < 0.03)]
    #'*-.
    plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=1.0)
    #plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], '*-.', label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)

    
    #if 'tuned' in dsys:
    #    plt.text(x_offset + btime, y_offset + bjoules, f'({ditr}, {ddvfs}, {135})')
#plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
#plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend(loc="lower right")
plt.grid()
plt.tight_layout()
plt.savefig(f'netpipe_{MMSG}_joule_timeline.png')

## nonidle timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    
    plt.plot(ddfn['timestamp_non0'], ddfn['nonidle_frac_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=1.0)
#plt.xlabel("Time (secs)")
plt.ylabel("Nonidle Time (%)")
plt.ylim((0, 1.1))
plt.legend(loc="lower right")
plt.grid()
plt.tight_layout()
plt.savefig(f'netpipe_{MMSG}_nonidle_timeline.png')

## joule timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddfn['timestamp_non0'], ddfn['instructions_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=1.0)
#plt.xlabel("Time (secs)")
plt.ylabel("Instructions")
plt.legend(loc="lower right")
plt.grid()
plt.tight_layout()
plt.savefig(f'netpipe_{MMSG}_instructions_timeline.png')

## EDP        
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    #print(dsys)

    plt.plot(ddfn['timestamp_non0'], ddfn['joules'], LINES[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[0], ddfn['joules'].iloc[0], HATCHS[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[-1], ddfn['joules'].iloc[-1], HATCHS[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[::140], ddfn['joules'].iloc[::140], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=1.0)    
    btime = ddf['timestamp_diff'].sum()
    bjoules = ddfn['joules_diff'].sum()
    if 'ebbrt_tuned' in dsys:
        plt.text(x_offset + btime-0.1, y_offset + bjoules, f'({ditr}, {ddvfs}, {drapl})', fontsize=14)
    elif 'linux_tuned' in dsys:
        plt.text(x_offset + btime-0.3, y_offset + bjoules, f'({ditr}, {ddvfs}, {drapl})', fontsize=14)
#plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend(loc="lower right")
plt.grid()
plt.tight_layout()
plt.savefig(f'netpipe_{MMSG}_epp.pdf')

'''
# Cstates
metric_labels = ['C1', 'C1E', 'C3', 'C6', 'C7']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops
fig, ax = plt.subplots(1)
idx = np.arange(N_metrics) #one group per metric
width = 0.2
data_dict = {}
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
        
    data_dict[dsys] = np.array([ddfn['c1_diff'].sum(),
                                ddfn['c1e_diff'].sum(),
                                ddfn['c3_diff'].sum(),
                                ddfn['c6_diff'].sum(),
                                ddfn['c7_diff'].sum()])

    print(dsys)
    c1h=ddfn['c1_diff'].sum()
    c1eh=ddfn['c1e_diff'].sum()
    c3h=ddfn['c3_diff'].sum()
    c6h=ddfn['c6_diff'].sum()
    c7h=ddfn['c7_diff'].sum()
    
    C1t=idlestates['C1']*c1h
    C1Et=idlestates['C1E']*c1eh
    C3t=idlestates['C3']*c3h    
    C6t=idlestates['C6']*c6h
    C7t=idlestates['C7']*c7h

    print(f"C1  = {C1t} usecs")
    print(f"C1E = {C1Et} usecs")
    print(f"C3  = {C3t} usecs")
    print(f"C6  = {C6t} usecs")
    print(f"C7  = {C7t} usecs")
    print(f"C_ALL  = {C1t+C1Et+C3t+C6t+C7t} usecs {c1h+c1eh+c3h+c6h+c7h} times")
    print('')
    
counter = 0
for sys in data_dict: #normalize and plot
    data = data_dict[sys]
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15)
plt.legend()
#plt.legend(loc='lower left')
plt.savefig(f'netpipe_{MMSG}_cstates.pdf')


## instruction timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    
    plt.plot(ddfn['timestamp_non0'], ddfn['instructions_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=1.0)
plt.xlabel("Time (secs)")
plt.ylabel("Instructions")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_instructions_timeline.pdf')

## time_diff timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    #ddf = ddf[(ddf['timestamp'] > 0.1) & (ddf['timestamp'] < 0.15)]
    #ddf = ddf[(ddf['timestamp_diff'] < 0.00003)]
    ddf['tmp'] = 1000000
    ddf['timestamp_diff'] = ddf['timestamp_diff'] * ddf['tmp']
    plt.plot(ddf['timestamp'], ddf['timestamp_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Time diff (us)")
plt.legend(loc='upper right')
plt.grid()
plt.savefig(f'netpipe_{MMSG}_timediff_timeline.png')

## rx_byte timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    plt.plot(ddf['timestamp'], ddf['rx_bytes'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Bytes Rx")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_rxbytes_timeline.png')

## tx_byte timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    plt.plot(ddf['timestamp'], ddf['tx_bytes'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Bytes Tx")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_txbytes_timeline.png')
'''

'''        
## time_diff timeline
plt.figure()
#for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
for dsys in ['linux_tuned', 'ebbrt_tuned']:
    ditr = 0
    ddvfs=''
    dnum= bconf[dsys][0]
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    #ddf = ddf[(ddf['timestamp'] > 2.45) & (ddf['timestamp'] < 2.5)]
    #ddf = ddf[(ddf['timestamp_diff'] > 0.00002) & (ddf['timestamp_diff'] < 0.00003)]
    
    plt.plot(ddf['timestamp'], ddf['timestamp_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Time diff (secs)")
plt.legend()
plt.grid()
plt.savefig(f'netpipe_{MMSG}_timediff_timeline.pdf')

'''
