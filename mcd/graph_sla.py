import matplotlib.pyplot as plt
import matplotlib as mplt

#mplt.rcParams.update({'font.size': 20})
plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
plt.rc('ytick', labelsize=20)    # fontsize of the tick labels
plt.rc('legend', fontsize=20)    # legend fontsize


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


def graphSLA(x, y, tt, sla=500, ttop=800):
    if len(y) != len(x):
        for i in range(0, len(x) - len(y)):
            y.append(9999)
                
    plt.errorbar(x, y, fmt=FMTS[tt], label=LABELS[tt], c=COLORS[tt], alpha=1.0)
    plt.errorbar(x, [sla], ls='-', color='orange')    

#graphSLA([50, 100, 200, 250, 300, 350, 400, 450], [345	,321,	381,	946], 'linux_default')
#graphSLA([50, 100, 200, 250, 300, 350, 400, 450], [169.7,	201.3,	315.6,	880.1], 'linux_tuned')
#graphSLA([50, 100, 200, 250, 300, 350, 400, 450], [187.1	,198.8	,231.3	,268.6	,322.2	,385.7	,501.9, 824.5], 'ebbrt_tuned')
graphSLA([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200], [101, 109.4, 136.4, 228.1, 732.1, 1369.7], 'linux_default')
graphSLA([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200], [65, 73, 108.8, 250.4, 845.3, 1375], 'linux_tuned')
graphSLA([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200], [67.2,	73.2,	73.4,	72.2,	67.9,	64.9,	59.9,	60.2,	63.5,	70.3,	1429.7], 'ebbrt_tuned')

plt.xlabel("QPS (K)")
plt.ylabel("99% Tail Latency (us)")
#plt.legend()
plt.grid(True,axis="both")
plt.ylim(bottom=0, top=800)
plt.tight_layout()
plt.savefig('mcd_sla.pdf')
#plt.savefig('mcdsilo_sla.pdf')
#plt.show()
