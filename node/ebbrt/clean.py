import re
import os
from os import path
import sys

print(len(sys.argv), sys.argv)
if len(sys.argv) != 4:
    print("clean.py itr dvfs rapl")
    exit()
'''
dvfs = ["0xd00",
        "0xf00",
        "0x1100",
        "0x1300",
        "0x1500",
        "0x1700",
        "0x1900",
        "0x1b00",
        "0x1d00"]

itrs = ["4", "6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "80"]
rapls = ["135", "95", "55"]
'''

dvfs = []
itrs = []
rapls = []

itrs.append(sys.argv[1])
dvfs.append(sys.argv[2])
rapls.append(sys.argv[3])

iters = 4
TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526

lat_us_50 = 0
lat_us_75 = 0
lat_us_90 = 0
lat_us_99 = 0
START_RDTSC = 0
END_RDTSC = 0
tdiff = 0
total_requests = 0
                    
#fwh = open('linux_nodejs_all.csv', 'a+')
#fwh.write("\nsys i itr dvfs rapl lat50 lat75 lat90 lat99 Request Time Joule total_ins total_cyc total_refcyc total_llcm c3 c6 c7\n")
def parseOut(i, itr, d, rapl):
    global lat_us_50 
    global lat_us_75
    global lat_us_90 
    global lat_us_99 
    global total_requests
    
    fout = open('ebbrt_out.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl, 'r')
    lat_us_50 = 0
    lat_us_75 = 0
    lat_us_90 = 0
    lat_us_99 = 0
    total_requests= 0
    for line in fout:
        if "50%" in line:
            tmp = list(filter(None, line.strip().split(' ')))
            lat_us_50 = float(tmp[1][0:len(tmp[1])-2])
        if "75%" in line:
            tmp = list(filter(None, line.strip().split(' ')))
            lat_us_75 = float(tmp[1][0:len(tmp[1])-2])
        if "90%" in line:
            tmp = list(filter(None, line.strip().split(' ')))
            lat_us_90 = float(tmp[1][0:len(tmp[1])-2])
        if "99%" in line:
            tmp = list(filter(None, line.strip().split(' ')))
            lat_us_99 = float(tmp[1][0:len(tmp[1])-2])
        if "requests in" in line:
            tmp = list(filter(None, line.strip().split(' ')))
            total_requests = int(tmp[0])
    fout.close()

def parseRdtsc(i, itr, d, rapl):
    global START_RDTSC
    global END_RDTSC
    global tdiff
    
    frtdsc = open('ebbrt_rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl, 'r')
    START_RDTSC = 0
    END_RDTSC = 0
    tdiff = 0
    for line in frtdsc:
        tmp = line.strip().split(' ')
        START_RDTSC = int(tmp[0])
        END_RDTSC = int(tmp[1])
        tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
        break                        
    frtdsc.close()

    if tdiff < 20 or tdiff > 40:
        START_RDTSC = 0
        END_RDTSC = 0

def parseLogs(i, itr, d, rapl, fname):
    global START_RDTSC
    global END_RDTSC
    global tdiff
    global lat_us_50 
    global lat_us_75
    global lat_us_90 
    global lat_us_99 
    global total_requests

    cc = 0
    startj = 0
    endj = 0
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
        if len(tmp) == 14:
            if int(tmp[13]) > START_RDTSC and int(tmp[13]) < END_RDTSC and int(tmp[5]) > 0 and int(tmp[6]) > 0 and int(tmp[7]) > 0 and int(tmp[8]) > 0:
                joules = int(tmp[12])
                if prevj == 0:
                    prevj = joules
                elif prevj > 0 and joules < prevj:
                    prevj = joules
                elif prevj > 0 and joules >= prevj:
                    sumj += joules - prevj
                    prevj = joules                                
                                        
                if cc == 0 and joules > 0:
                    startj =  joules
                    ins = int(tmp[5])
                    cyc = int(tmp[6])
                    refcyc = int(tmp[7])
                    llcm = int(tmp[8])
                    c3 = int(tmp[9])
                    c6 = int(tmp[10])
                    c7 = int(tmp[11])
                    cc = 1

                if ins > 0 and int(tmp[5]) > ins:
                    total_ins = total_ins + (int(tmp[5]) - ins)
                    ins = int(tmp[5])
                if cyc > 0 and int(tmp[6]) > cyc:
                    total_cyc = total_cyc + (int(tmp[6]) - cyc)
                    cyc = int(tmp[6])
                if refcyc > 0 and int(tmp[7]) > refcyc:
                    total_refcyc = total_refcyc + (int(tmp[7]) - refcyc)
                    refcyc = int(tmp[7])    
                if llcm > 0 and int(tmp[8]) > llcm:
                    total_llcm = total_llcm + (int(tmp[8]) - llcm)
                    llcm = int(tmp[8])                    
                if c3 > 0 and int(tmp[9]) > c3:
                    total_c3 = total_c3 + (int(tmp[9]) - c3)
                    c3 = int(tmp[9])
                if c6 > 0 and int(tmp[10]) > c6:
                    total_c6 = total_c6 + (int(tmp[10]) - c6)
                    c6 = int(tmp[10])
                if c7 > 0 and int(tmp[11]) > c7:
                    total_c7 = total_c7 + (int(tmp[11]) - c7)
                    c7 = int(tmp[11])
                
    f.close()
    print("ebbrt "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(lat_us_50)+" "+str(lat_us_75)+" "+str(lat_us_90)+" "+str(lat_us_99)+" "+str(total_requests)+" "+str(tdiff)+" "+str(round((JOULE_CONVERSION * sumj),2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7), START_RDTSC, END_RDTSC)
                    
    

print("sys i itr dvfs rapl lat50 lat75 lat90 lat99 requests time joule ins cyc refcyc llcm c3 c6 c7")

for rapl in rapls:
    for itr in itrs:
        for d in reversed(dvfs):
            for i in range(0, iters):
                fname = 'ebbrt_dmesg.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl+'.csv'
                if not path.exists(fname):
                    print(fname, "doesn't exist?")
                else:                    
                    parseOut(i, itr, d, rapl)
                    parseRdtsc(i, itr, d, rapl)
                    #print("ebbrt "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(lat_us_50)+" "+str(lat_us_75)+" "+str(lat_us_90)+" "+str(lat_us_99)+" "+str(total_requests)+" "+str(tdiff))
                    if START_RDTSC != 0:
                        parseLogs(i, itr, d, rapl, fname)
                    else:
                        print(fname, "RTDSC = 0")
                    
                        
