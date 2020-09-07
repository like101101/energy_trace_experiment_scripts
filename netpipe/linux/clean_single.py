import re
import os
from os import path
import sys
import time
import numpy as np

print(len(sys.argv), sys.argv)
if len(sys.argv) != 5:
    print("clean.py itr dvfs rapl msg")
    exit()
    
itr = sys.argv[1]
dvfs = sys.argv[2]
rapl = sys.argv[3]
msg = sys.argv[4]

iters = 10

TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526
START_RDTSC = 0
END_RDTSC = 0
tdiff = 0
tput = 0
tins = 0
tcyc = 0
trefcyc = 0
tllcm = 0
tc3 = 0
tc6 = 0
tc7 = 0
tjoules = 0.0

def checkExist(fname, fnpserver, fnpout):
    if not path.exists(fname):
        print(fname, "doesn't exist?")
        exit()
    if not path.exists(fnpserver):
        print(fnpserver, "doesn't exist?")
        exit()
    if not path.exists(fnpout):
        print(fnpout, "doesn't exist?")
        exit()

def parseTput(fnpout):
    global tput
    tput = 0.0
    lat = 0.0
    f = open(fnpout, 'r')
    for line in f:
        tmp = list(filter(None, line.strip().split(' ')))
        tput = float(tmp[1])
        break
    f.close()

def parseRdtsc(fnpserver):
    global START_RDTSC
    global END_RDTSC
    global tdiff

    START_RDTSC = 0
    END_RDTSC = 0
    
    f = open(fnpserver, 'r')    
    for line in f:
        if 'WORKLOAD' in line.strip():
            tmp = list(filter(None, line.strip().split(' ')))
            START_RDTSC = int(tmp[1])
            END_RDTSC = int(tmp[2])
            break
    f.close()
    tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 1)
    
def parseLogs(fname):
    global START_RDTSC
    global END_RDTSC
    global tdiff
    global tput
    global tins
    global tcyc
    global trefcyc
    global tllcm
    global tc3
    global tc6
    global tc7
    global tjoules

    cc = 0
    total_ins = 0
    total_cyc = 0
    total_refcyc = 0
    total_llcm = 0
    prevj = 0
    sumj = 0
    
    ins = 0
    cyc = 0
    refcyc = 0
    llcm = 0
    
    total_c3 = 0
    total_c6 = 0
    total_c7 = 0
    
    c3 = 0
    c6 = 0
    c7 = 0

    f = open(fname)
    for line in f:
        tmp = list(filter(None, line.strip().split(' ')))
        if len(tmp) > 5 and 'i' not in line.strip():
            tmp2 = list(filter(None, line.strip().split(']')))
            tmp3 = list(filter(None, tmp2[1].strip().split(' ')))
            if int(tmp3[13]) > START_RDTSC and int(tmp3[13]) < END_RDTSC and int(tmp3[5]) > 0 and int(tmp3[6]) > 0 and int(tmp3[7]) > 0 and int(tmp3[8]) > 0:
                joules = int(tmp3[12])
                if joules > 0:
                    if prevj == 0:
                        prevj = joules
                    elif prevj > 0 and joules < prevj:
                        prevj = joules
                    elif prevj > 0 and joules >= prevj:
                        sumj += joules - prevj
                        prevj = joules
                                        
                    if cc == 0 and joules > 0:
                        ins = int(tmp3[5])
                        cyc = int(tmp3[6])
                        refcyc = int(tmp3[7])
                        llcm = int(tmp3[8])
                        c3 = int(tmp3[9])
                        c6 = int(tmp3[10])
                        c7 = int(tmp3[11])
                        cc = 1
                                        
                    if ins > 0 and int(tmp3[5]) > ins:
                        total_ins = total_ins + (int(tmp3[5]) - ins)
                        ins = int(tmp3[5])
                    if cyc > 0 and int(tmp3[6]) > cyc:
                        total_cyc = total_cyc + (int(tmp3[6]) - cyc)
                        cyc = int(tmp3[6])
                    if refcyc > 0 and int(tmp3[7]) > refcyc:
                        total_refcyc = total_refcyc + (int(tmp3[7]) - refcyc)
                        refcyc = int(tmp3[7])    
                    if llcm > 0 and int(tmp3[8]) > llcm:
                        total_llcm = total_llcm + (int(tmp3[8]) - llcm)
                        llcm = int(tmp3[8])
                    if c3 > 0 and int(tmp3[9]) > c3:
                        total_c3 = total_c3 + (int(tmp3[9]) - c3)
                        c3 = int(tmp3[9])
                    if c6 > 0 and int(tmp3[10]) > c6:
                        total_c6 = total_c6 + (int(tmp3[10]) - c6)
                        c6 = int(tmp3[10])
                    if c7 > 0 and int(tmp3[11]) > c7:
                        total_c7 = total_c7 + (int(tmp3[11]) - c7)
                        c7 = int(tmp3[11])

    f.close()
    tjoules += (JOULE_CONVERSION * sumj)        
    tins += total_ins
    tcyc += total_cyc
    trefcyc += total_refcyc
    tllcm += total_llcm
    tc3 += total_c3
    tc6 += total_c6
    tc7 += total_c7        

print("sys i core itr dvfs rapl tput time joule ins cyc refcyc llcm c3 c6 c7 RDTSC_START RDTSC_END")    
for i in range(0, iters):
    fname = 'dmesg_devicelog.'+str(i)+'_'+msg+'_5000_'+itr+'_'+dvfs+'_135'
    fnpserver = 'np.server.'+str(i)+'_'+msg+'_5000_'+itr+'_'+dvfs+'_135'
    fnpout = 'np.out.'+str(i)+'_'+msg+'_5000_'+itr+'_'+dvfs+'_135'
    #print(fname)

    tdiff = 0
    tput = 0
    tins = 0
    tcyc = 0
    trefcyc = 0
    tllcm = 0
    tc3 = 0
    tc6 = 0
    tc7 = 0
    tjoules = 0.0
    
    checkExist(fname, fnpserver, fnpout)                
    parseTput(fnpout)
    parseRdtsc(fnpserver)
    parseLogs(fname)

    print("linux "+str(i)+" "+str(itr)+" "+str(dvfs)+" "+str(rapl)+" "+str(round(tput,2))+" "+str(tdiff)+" "+str(round(tjoules,2))+" "+str(tins)+" "+str(tcyc)+" "+str(trefcyc)+" "+str(tllcm)+" "+str(tc3)+" "+str(tc6)+" "+str(tc7)+" "+str(START_RDTSC)+" "+str(END_RDTSC))

    
