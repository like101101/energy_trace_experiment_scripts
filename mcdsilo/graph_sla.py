import matplotlib.pyplot as plt
import matplotlib as mplt

mplt.rcParams.update({'font.size': 20})

colors = ['red', 'green', 'blue']

def graphSLA(x, y, tt, col, sla=500, ttop=800):
    if len(y) != len(x):
        for i in range(0, len(x) - len(y)):
            y.append(9999)
                
    plt.errorbar(x, y, fmt='p-', label=tt, color=col)
    plt.errorbar(x, [sla], ls='-', color='orange')    

#graphSLA([50, 100, 200, 250, 300, 350, 400, 450], [345	,321,	381,	946], 'Linux Default', 'blue')
#graphSLA([50, 100, 200, 250, 300, 350, 400, 450], [169.7,	201.3,	315.6,	880.1], 'Linux Tuned', 'green')
#graphSLA([50, 100, 200, 250, 300, 350, 400, 450], [187.1	,198.8	,231.3	,268.6	,322.2	,385.7	,501.9, 824.5], 'Library OS Tuned', 'red')
graphSLA([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200], [101, 109.4, 136.4, 228.1, 732.1, 1369.7], 'Linux Default', 'blue')
graphSLA([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200], [65, 73, 108.8, 250.4, 845.3, 1375], 'Linux Tuned', 'green')
graphSLA([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200], [72.2,	75.2,	75.4,	72.2,	67.9,	64.9,	59.9,	60.2,	63.5,	70.3,	1429.7], 'Library OS Tuned', 'red')

plt.xlabel("RPS (K)")
plt.ylabel("99% Tail Latency (us)")
plt.legend()
plt.grid(True,axis="both")
plt.ylim(bottom=0, top=800)
plt.show()
