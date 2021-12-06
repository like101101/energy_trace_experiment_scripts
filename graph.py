import pandas as pd
import numpy as np
#from mpl_toolkits.axes_grid.inset_locator import inset_axes
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys
                                
plt.rc('axes', labelsize=18)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=18)    # fontsize of the tick labels
plt.rc('ytick', labelsize=18)    # fontsize of the tick labels
plt.rc('legend', fontsize=10)    # legend fontsize
#plt.rcParams['ytick.right'] = plt.rcParams['ytick.labelright'] = True
#plt.rcParams['ytick.left'] = plt.rcParams['ytick.labelleft'] = False

#plt.rcParams['figure.figsize'] = 18, 8

#QPS=600000
if len(sys.argv) != 2:
    print("graph.py <QPS>")
    exit()
QPS = int(sys.argv[1])

#plt.ion()

x_offset, y_offset = 0.01/5, 0.01/5

LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']
EBBRT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

dvfs_dict = {
    "0xc00" :  1.2,
    "0xd00" :  1.3,
    "0xe00" :  1.4,
    "0xf00" :  1.5,
    "0x1000" : 1.6,
    "0x1100" : 1.7,
    "0x1200" : 1.8,
    "0x1300" : 1.9,
    "0x1400" : 2.0,
    "0x1500" : 2.1,
    "0x1600" : 2.2,
    "0x1700" : 2.3,
    "0x1800" : 2.4,
    "0x1900" : 2.5,
    "0x1a00" : 2.6,
    "0x1b00" : 2.7,
    "0x1c00" : 2.8,
    "0x1d00" : 2.9,
    "0xffff" : 3.0,
}

mqps_dict = {
    50000 : "50K QPS",
    100000 : "100K QPS",
    200000 : "200K QPS",
    400000 : "400K QPS",
    600000 : "600K QPS",
    1000000 : "1000K QPS",
    1500000 : "1500K QPS"
}

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

#workload_loc='/scratch2/mcd/mcd_combined_11_9_2020/mcd_combined.csv'
workload_loc='collected_data/mcd_combined.csv'
#workload_loc='collected_data/mcd_busy.csv'
#workload_loc='/scratch2/mcdsilo/mcdsilo_combined_11_20_2020/mcdsilo_combined.csv'
log_loc='/scratch2/mcd/mcd_combined_11_9_2020/'

COLORS = {'linux_default': 'blue',
          'linux_tuned': 'green',
          'ebbrt_tuned': 'red'}          
LABELS = {'linux_default': 'Linux Default',
          'linux_tuned': 'Linux Tuned',
          'ebbrt_tuned': 'LibOS Tuned'}
FMTS = {'linux_default':   'o--',
          'linux_tuned':   '*-.',
          'ebbrt_tuned':   'x:'}
LINES = {'linux_default':  '--',
          'linux_tuned':   '-.',
          'ebbrt_tuned':   ':'}
HATCHS = {'linux_default': 'o',
          'linux_tuned':   '*',
          'ebbrt_tuned':   'x'}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df = df[df['read_99th'] <= 500.0]
#df['edp'] = df['joules'] * df['time']
df['edp'] = df['joules'] * df['read_99th']
df['dvfs'] = df['dvfs'].apply(lambda x: dvfs_dict[x])
df['processor'] = df['dvfs'] * df['rapl']
df['cpi'] = df['ref_cycles'] / df['instructions']
df['cstate_exit_latency'] = ((df['c1']*2)+(df['c1e']*20)+(df['c3']*211)+(df['c6']*345)++(df['c7']*345))/1000000.0
df['rx_desc_per_itr'] = df['rx_desc'] / df['num_interrupts']
df['rx_bytes_per_itr'] = df['rx_bytes'] / df['num_interrupts']
df['tx_desc_per_itr'] = df['tx_desc'] / df['num_interrupts']
df['tx_bytes_per_itr'] = df['tx_bytes'] / df['num_interrupts']

'''
for QPS in [200000, 400000, 600000]:
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']==3.0) & (df['target_QPS'] == QPS)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['target_QPS'] == QPS)].copy()
det = df[(df['sys']=='ebbrt_tuned') & (df['target_QPS'] == QPS)].copy()
dpoll = df[(df['sys']=='ebbrt_poll') & (df['target_QPS'] == QPS)].copy()

    #dfmerge = pd.merge(dlt, det, on=['itr', 'dvfs', 'rapl'])
    #dfmerge['rx_desc_per_itr_gain'] = (dfmerge['rx_bytes_per_itr_x'] / dfmerge['rx_bytes_per_itr_y']) * 50.0
    #print(dfmerge['rx_desc_per_itr_gain'])
    #print(dfmerge.columns)
    
    #normalize
    sstr ='cpi'
    sscale=100.0
    det[sstr] = (det[sstr]/dlt[sstr].max())*sscale
    dlt[sstr] = (dlt[sstr]/dlt[sstr].max())*sscale

    # 
    #fig, ax = plt.figure()
    fig, ax = plt.subplots(1)
    #ax.set_title(mqps_dict[QPS], x=0.1, y=0.9)
    #plt.scatter(dfmerge['itr'], dfmerge['dvfs'], marker='o', s=dfmerge['rx_desc_per_itr_gain'], label="libOS_rx_bytes_per_itr/linux_tuned_rx_bytes_per_itr", color='red', alpha=0.9)
    plt.scatter(det['read_99th'], det['joules'], marker='o', s=det[sstr], label="libOS "+sstr, color='red', alpha=0.5)
    plt.scatter(dlt['read_99th'], dlt['joules'], marker='o', s=dlt[sstr], label="linux "+sstr, color='green', alpha=0.5)
    #plt.scatter(dld['read_99th'], dld['joules'], marker='o', s=dld['rx_bytes_per_itr'], label=LABELS[dld['sys'].max()], color='blue', alpha=0.9)

    for dbest in [dlt, det]:
        b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
        bjoules = b['joules']
        btail = b['read_99th']
        plt.plot(btail,  bjoules, fillstyle='none', marker='o', markersize=15, c=COLORS[b['sys']])

    
    #plt.xlabel('ITR')
    #plt.ylabel('DVFS')
    plt.xlabel("99% Tail Latency (usecs)")
    plt.ylabel("Energy Consumed (Joules)")
    plt.legend(loc="upper right")
    plt.title("Memcached "+mqps_dict[QPS])
    #cbar=plt.colorbar(cb1)
    #cbar.set_label('Processor Frequency')

    plt.xticks([0, 100, 200, 300, 400], [0, 100, 200, 300, 400, 500])
    plt.yticks([800, 1500, 2000, 2500, 3000], [800, 1500, 2000, 2500, 3000])

    plt.grid()
    plt.tight_layout()
    #plt.show()
    plt.savefig(f"mcd_{QPS}_"+sstr+".png")
'''


dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']==3.0) & (df['target_QPS'] == QPS)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['target_QPS'] == QPS)].copy()
det = df[(df['sys']=='ebbrt_tuned') & (df['target_QPS'] == QPS)].copy()


# read_99th vs joules
#fig, ax = plt.figure()
fig, ax = plt.subplots(1)
#ax.set_title(mqps_dict[QPS], x=0.1, y=0.9)
#ax.yaxis.set_label_position("right")
#norm= matplotlib.colors.Normalize(vmin=1,vmax=10)
cb1=plt.scatter(det['read_99th'], det['joules'], marker='o', s=det['itr'], c=det['dvfs'], label=LABELS[det['sys'].max()], cmap='Reds_r', alpha=0.9)
plt.scatter(dlt['read_99th'], dlt['joules'], marker='o', s=dlt['itr'], c=dlt['dvfs'], label=LABELS[dlt['sys'].max()], cmap='Greens_r', alpha=0.9)
#plt.scatter(dld['read_99th'], dld['joules'], marker='o', s=dld['itr'], c=dld['dvfs'], label=LABELS[dld['sys'].max()], cmap='Blues_r', alpha=0.9)

#for dbest in [dld, dlt, det]:
#    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
#    bjoules = b['joules']
#    btail = b['read_99th']
#    plt.plot(btail,  bjoules, fillstyle='none', marker='o', markersize=15, c=COLORS[b['sys']])
#plt.legend(['linuxd', 'linuxt', 'libos'], ncol=3, loc="upper right")

#b = dpoll[dpoll.edp==dpoll.edp.min()].iloc[0]
#plt.plot(b['read_99th'], b['joules'], fillstyle='none', marker='*', markersize=15, c='black')

#print('ebbrt_poll min_read_99th', dpoll.read_99th.min())
#print('ebbrt_tuned min read_99th', det.read_99th.min())

plt.xlabel("99% Tail Latency (usecs)")
plt.ylabel("Energy Consumed (Joules)")
plt.title("MCD "+mqps_dict[QPS])
cbar=plt.colorbar(cb1)
cbar.set_label('Processor Frequency')

plt.xticks([100, 200, 300, 400, 500], [100, 200, 300, 400, 500])
plt.yticks([500, 1000, 1500, 2000, 2500, 3000], [500, 1000, 1500, 2000, 2500, 3000])

plt.grid()
plt.tight_layout()
plt.show()
#plt.savefig(f'mcdsilo_{QPS}_overview.png')


'''
## itr/dvfs x cstates
plt.figure()
for dsys in [det, dlt]:
    plt.plot(dsys['processor'], dsys['cstate_exit_latency'], HATCHS[dsys['sys'].max()], label=LABELS[dsys['sys'].max()], c=COLORS[dsys['sys'].max()], alpha=0.7)
plt.xlabel("DVFSxRAPL")
plt.ylabel("Cstate_exit_latency (secs)")
#plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))

#plt.xticks([100, 200, 300, 400, 500], [100, 200, 300, 400, 500])
plt.yticks([100, 200, 300, 400, 500, 600, 700, 800], [100, 200, 300, 400, 500, 600, 700, 800])
#plt.xlim(xmin=0)
plt.ylim(ymin=0)
plt.title("Memcached "+mqps_dict[QPS])
plt.legend(loc="upper left")
plt.grid()
#plt.show()
plt.savefig(f'mcd_{QPS}_dvfs_cstate.png')
'''

'''
## itr/dvfs x joules
sstrx='itr'
sstry='ref_cycles'
plt.figure()
for dsys in [det, dlt]:
#for dsys in [det]:
    plt.plot(dsys[sstrx], dsys[sstry], HATCHS[dsys['sys'].max()], label=LABELS[dsys['sys'].max()], c=COLORS[dsys['sys'].max()], alpha=0.7)
    
plt.xlabel(sstrx)
plt.ylabel(sstry)
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))

#plt.xticks([100, 200, 300, 400, 500], [100, 200, 300, 400, 500])
#plt.yticks([100, 200, 300, 400, 500, 600, 700, 800], [100, 200, 300, 400, 500, 600, 700, 800])
plt.xlim(xmin=0, xmax=500)
plt.ylim(ymin=df[sstry].min(), ymax=df[sstry].max())
#plt.ylim(ymin=0, ymax=3000)
plt.title("Memcached "+mqps_dict[QPS])
plt.legend(loc="upper left")
plt.grid()
#plt.show()
plt.savefig(f"mcd_{QPS}_"+sstrx+"_"+sstry+".png")
'''

'''
nom='ref_cycles'
for dsys in [dlt, det]:
#for dsys in [det]:
    print("QPS", QPS, dsys['sys'].max(), nom, int(dsys[nom].mean()), int(dsys[nom].std()), 'std percent:', round(dsys[nom].std()/dsys[nom].mean(), 2))
#print(nom, 'diff:', int(dlt[nom].mean()) - int(det[nom].mean()), int(dlt[nom].mean()) /int(det[nom].mean()))
print("")
'''
