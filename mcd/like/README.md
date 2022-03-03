To run experiment:

`NITERS="2" MDVFS="0x1d00" MRAPL="135" ITRS="1" MQPS="200000 400000 600000" ./run_mcd.sh runMCD`
```
NITERS - number of experimental runs [0, NITERS]
MDVFS - different DVFS values
MRAPL - different RAPL values (leave as is)
ITRS - different ITR values
MQPS - different QPS values
```

Experiment script will place all data in a folder timestamped by date and time, i.e. `03_03_2022_14_18_03/`

To parse data using `03_03_2022_14_18_03/`:

`python3 clean_mcd_linux.py 03_03_2022_14_18_03`
