import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon

fig, ax1= plt.subplots(1)

ax1.bar(range(1, 5), range(1, 5), color='red', edgecolor='black', hatch="/")
ax1.bar(range(1, 5), [6] * 4, bottom=range(1, 5),
        color='blue', edgecolor='black', hatch='//')
ax1.set_xticks([1.5, 2.5, 3.5, 4.5])
plt.show()
