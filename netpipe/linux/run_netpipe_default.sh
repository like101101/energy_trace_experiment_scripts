set -x

#example server: MSGSIZES='8192' REPEAT=1 WRITEBACK_DIR="/mnt/netpipe/linux/9_27" MYIP="192.168.1.9" ./run_netpipe_default.sh
#example client: MSGSIZES='8192' REPEAT=1 WRITEBACK_DIR="/mnt/netpipe/linux/9_27" ROLE="CLIENT" MYIP="192.168.1.11" NP_SERVER_IP="192.168.1.9" ./run_netpipe_default.sh
# tshark -i eth0 -w t.pcap -F pcap host 192.168.1.9 &

TS=$(date +"%m.%d.%y-%H.%M.%S")

INSMOD=insmod
RMMOD=rmmod
IP=ip
TASKSET=taskset
DMESG=dmesg
CAT=cat
SLEEP=sleep
IXGBE=ixgbe
RDMSR=rdmsr
WRMSR=wrmsr
SSH=ssh
SCP=scp
TSHARK=tshark
PKILL=pkill
ETHTOOL=/app/ethtool-4.5/ethtool
SETAFFINITY=/app/perf/set_irq_affinity_ixgbe.sh
DISABLE_HT=/app/perf/disable_ht.sh
ENABLE_IDLE=/app/perf/enable_cstates.sh
MSR_MAX_FREQ=/app/perf/msr_max_freq.sh
NETPIPE=/app/NetPIPE-3.7.1/NPtcp_joules
RAPL_POW_MOD=/app/uarch-configure/rapl-read/rapl-power-mod
ETHMODULE_NOLOG=/app/ixgbe/ixgbe_orig.ko
ETHMODULE_YESLOG=/app/ixgbe/ixgbe_log.ko
SET_IP=/app/perf/set_ip.sh
IXGBE_STATS_CORE=/proc/ixgbe_stats/core
DVFS="0x199"
TURBOBOOST="0x1a0"

export ROLE=${ROLE:-"SERVER"}
export DEVICE=${DEVICE:-"eth0"}
export MYIP=${MYIP:-"192.168.1.9"}
export NP_SERVER_IP=${NP_SERVER_IP:-"192.168.1.9"}
export HOST_IP=${HOST_IP:-"192.168.1.153"}
export ITR=${ITR:-"1"}
#export MSGSIZES=${MSGSIZES:-"64 128 256 512 1024 2048 3072 4096 8192 12288 16384 24576 49152 65536 98304 131072 196608 262144 393216 524288 786432"}
export MSGSIZES=${MSGSIZES:-"64 8192 65536 524288"}
export LOOP=${LOOP:-"5000"}
export TASKSETCPU=${TASKSETCPU:-"1"}
export MDVFS=${MDVFS:="0xFFFF"}
export MRAPL=${MRAPL:-"135"}
export REPEAT=${REPEAT:-1}
export BEGINI=${BEGINI:-0}
export PERF_INIT=${PERF_INIT:-0}
export CAPSHARK=${CAPSHARK:-0}
export WRITEBACK_DIR=${WRITEBACK_DIR:-"/tmp/"}
export SCREEN_PRESLEEP=${SCREEN_PRESLEEP:-1}

echo "Sleeping ${SCREEN_PRESLEEP} seconds for screen"
sleep ${SCREEN_PRESLEEP}

if [[ ${PERF_INIT} == 1 ]]; then
    ## apply performance scripts
    ${DISABLE_HT}
    ${SLEEP} 1
    ${RAPL_POW_MOD} 135
    ${SLEEP} 1

    ## apply ixgbe module with logging
    if [[ ${ROLE} == "SERVER" ]]; then    
	${SLEEP} 1
	#rmmod ixgbe && insmod /app/ixgbe/ixgbe_movnti.ko && /app/perf/set_ip.sh eth0 192.168.1.9
        ${RMMOD} ${IXGBE} && ${INSMOD} ${ETHMODULE_YESLOG} && ${SET_IP} ${DEVICE} ${MYIP}
	${SLEEP} 1
    fi
fi

## dump results from setting PERF_INIT
${SETAFFINITY} -x all ${DEVICE}
${ETHTOOL} -c ${DEVICE}
${SLEEP} 1
${RDMSR} -a ${DVFS}
${RDMSR} -a ${TURBOBOOST}

for ((i=$BEGINI;i<$REPEAT; i++)); do
    for msg in $MSGSIZES; do
	
	## SERVER
	if [[ ${ROLE} == "SERVER" ]]; then
	    ## clean up previous trace logs just incase
	    ${CAT} ${IXGBE_STATS_CORE}/${TASKSETCPU} &> /dev/null
	    
	    ## start wireshark
	    if [[ ${CAPSHARK} == 1 ]]; then
		${SLEEP} 1
		${TASKSET} -c 0 ${TSHARK} -i ${DEVICE} -w /app/tshark.pcap.${i}_${TASKSETCPU}_${msg}_${LOOP}_${ITR}_${MDVFS}_${MRAPL} -F pcap host ${MYIP} &
		${SLEEP} 1
	    fi
	    
	    ## start np server
	    ${TASKSET} -c ${TASKSETCPU} ${NETPIPE} -l ${msg} -u ${msg} -n ${LOOP} -p 0 -r -I &> /app/linux.np.server.${i}_${TASKSETCPU}_${msg}_${LOOP}_${ITR}_${MDVFS}_${MRAPL}
	    
	    if [[ ${CAPSHARK} == 1 ]]; then
		${SLEEP} 1
		${PKILL} ${TSHARK}
		${SLEEP} 1
	    fi			
	    
	    # dumps logs
	    ${CAT} ${IXGBE_STATS_CORE}/${TASKSETCPU} &> /app/linux.np.log.${i}_${TASKSETCPU}_${msg}_${LOOP}_${ITR}_${MDVFS}_${MRAPL}
	    ${SLEEP} 5
	else # CLIENT	   
	    while ! ${TASKSET} -c ${TASKSETCPU} ${NETPIPE} -h ${NP_SERVER_IP} -l ${msg} -u ${msg} -n ${LOOP} -p 0 -r -I; do
		echo "FAILED: Server not ready trying again ..."
		${SLEEP} 5
	    done
	    ${CAT} np.out &> /app/linux.np.client.${i}_${TASKSETCPU}_${msg}_${LOOP}_${ITR}_${MDVFS}_${MRAPL}
	    ${SLEEP} 5
	fi		    
	${SLEEP} 1
	${SCP} /app/*.${i}_${TASKSETCPU}_${msg}_${LOOP}_${ITR}_${MDVFS}_${MRAPL} ${HOST_IP}:${WRITEBACK_DIR}
    done
done
