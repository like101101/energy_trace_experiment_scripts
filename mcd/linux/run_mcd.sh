#! /bin/bash

export RXU=${RXU:='8'}
export RXQ=${RXQ:='512'}
export TXQ=${TXQ:='512'}
export NITERS=${NITERS:='2'}
export SERVER=${SERVER:=192.168.1.230}
export OUTFILE=${OUTFILE:=0}
#export MQPS=${MQPS:='100000 200000 400000 600000 800000 900000'}
#export ITRS=${ITRS:-"100 200 400"}
#export MDVFS=${MDVFS:="0x1c00 0x1a00 0x1800 0x1600 0x1400 0x1200 0x1000 0xe00 0xc00"}
#export MDVFS=${MDVFS:="0x1d00 0x1c00 0x1b00 0x1a00 0x1900 0x1800 0x1700 0x1600 0x1500 0x1400 0x1300 0x1200 0x1100 0x1000 0xf00 0xe00 0xd00 0xc00"}
#export MRAPL=${MRAPL:-"135 125 115 105 95 85 75 65 55 45"}
#export MRAPL=${MRAPL:-"135 105 75 45"}

export MDVFS=${MDVFS:="0x1d00 0x1b00 0x1900 0x1700 0x1500 0x1300 0x1100 0xf00 0xd00"}
#export MDVFS=${MDVFS:="0x1d00 0x1b00 0x1900 0x1700"}
export MQPS=${MQPS:='200000 400000 600000'}
export ITRS=${ITRS:-"50 100 200 300 400"}
export MRAPL=${MRAPL:-"135 95 55"}

currdate=`date +%m_%d_%Y_%H_%M_%S`

function runMutilateBench
{
    timeout 600 python3 -u mutilate_bench.py "$@"
}

function runASPLOStest
{
    echo "runASPLOStest"
    
    #warm up
    runMutilateBench --bench mcd --qps 200000 --time 30 --itr 300 --rapl 135 --dvfs 0x1500 --nrepeat 0

    for itr in 300 400; do	    
	for qps in 200000 400000 600000; do	    	    
	    for r in 135 95 55; do	
		for i in `seq 0 1 $NITERS`; do
		    echo "runMutilateBench --bench mcd --qps ${qps} --time 30 --itr ${itr} --rapl ${r} --dvfs 0x1500 --nrepeat ${i}"
		    runMutilateBench --bench mcd --qps ${qps} --time 30 --itr ${itr} --rapl ${r} --dvfs 0x1500 --nrepeat ${i}
		    sleep 1
		done
	    done
	done
    done
    #   done
    
}

function runASPLOS
{
    echo "DVFS ${MDVFS}"
    echo "ITRS ${ITRS}"
    echo "MQPS ${MQPS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"

    #runASPLOStest
    
    for dvfs in ${MDVFS}; do
	for itr in $ITRS; do	    
	    for qps in ${MQPS}; do	    	    
		for r in ${MRAPL}; do				
			for i in `seq 0 1 $NITERS`; do
			echo "runMutilateBench --bench mcd --qps ${qps} --time 30 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
		        runMutilateBench --bench mcd --qps ${qps} --time 30 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}
			sleep 1
		    done
		done
	    done
	done
    done
}

function runASPLOSpart
{
    MDVFS="0xd00" ITRS="300" MQPS="200000" MRAPL="55" NITERS="2" runASPLOS    
    MDVFS="0xd00" ITRS="300" MQPS="400000" MRAPL="95" NITERS="2" runASPLOS    
    MDVFS="0x1100" ITRS="300" MQPS="600000" MRAPL="95" NITERS="2" runASPLOS
}

function runASPLOSgov
{
    echo "runASPLOSgov"
    echo "MQPS ${MQPS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    
    for qps in ${MQPS}; do	    	    
	for r in ${MRAPL}; do				
	    for i in `seq 0 1 $NITERS`; do
		echo "runMutilateBench --bench mcd --qps ${qps} --time 30 --rapl ${r} --nrepeat ${i}"
		runMutilateBench --bench mcd --qps ${qps} --time 30 --rapl ${r} --nrepeat ${i}
		sleep 1
	    done
	done
    done
}

function runASPLOSitr
{
    echo "runASPLOSitr"
    echo "DVFS ${MDVFS}"
    #echo "ITRS ${ITRS}"
    echo "MQPS ${MQPS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    
    for dvfs in ${MDVFS}; do
	#for itr in $ITRS; do	    
	for qps in ${MQPS}; do	    	    
	    for r in ${MRAPL}; do				
		for i in `seq 0 1 $NITERS`; do
		    echo "runMutilateBench --bench mcd --qps ${qps} --time 30 --itr 1 --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
		    runMutilateBench --bench mcd --qps ${qps} --time 30 --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}
		    sleep 1
		done
	    done
	done
    done
 #   done
}

function zygos
{
    for i in `seq 1 1 $NITERS`;
    do
	ssh $SERVER "pkill memcached"
	pkill mutilate
	sleep 1
	timeout 300 python3 mutilate_bench.py zygos $1
    done
}

function runZygos
{
    for i in `seq 1 1 $NITERS`;
    do
	for d in $RXU;
	do
	    ssh $SERVER "pkill memcached"
	    pkill mutilate
	    sleep 1
	    timeout 300 python3 mutilate_bench.py zygos_itr $d
	done
    done
}

function runZygosOvernight
{
    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_135Watt_etc.log

    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 120
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_120Watt_etc.log

    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 110
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_110Watt_etc.log

    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 100
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_100Watt_etc.log

    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 90
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_90Watt_etc.log
    
    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 80
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_80Watt_etc.log

    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 70
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_70Watt_etc.log

    sleep 5
    ssh 10.255.5.8 ~/uarch-configure/rapl-read/rapl-power-mod 60
    sleep 5

    NITERS=3 RXU='2 10 20 30 40 42 44 50 60 62 64 70 80 82 84 86 90 100 110 120 122 124 126 128 130 140 150' runZygos > zygos_10_7_2019_60Watt_etc.log
}

function runQPS
{
    ssh $SERVER "pkill memcached"
    pkill mutilate
    sleep 1
    timeout 90 python3 -u mutilate_bench.py $1 $2 $3
}

function run6
{
    #mcd_data/10_03_2019_QPS_930000_135Watt.log  mcd_data/10_03_2019_QPS_990000_16_8_16_135Watt.log
    #mcd_data/10_03_2019_QPS_930000_64Watt.log   mcd_data/10_03_2019_QPS_990000_64Watt.log
    #mcd_data/10_03_2019_QPS_930000_88Watt.log   mcd_data/10_03_2019_QPS_990000_88Watt.log
    #mcd_data/10_03_2019_QPS_990000_135Watt.log
    for i in `seq 1 1 $NITERS`;
    do
	for d in $RXU;
	do
	    ssh $SERVER "pkill memcached"
	    pkill mutilate
	    sleep 1
	    timeout 90 python3 -u mutilate_bench.py qps_itr $d $1
	done
    done
}

function test
{
    NITERS=2 RXU='64 70 80 82 84 86 90 100 110' run6 990000
}

function run5
{
    for i in `seq 1 1 $NITERS`;
    do
	for d in $RXU;
	do
	    ssh $SERVER "pkill memcached"
	    sleep 1
	    pkill mutilate
	    sleep 1
	    ssh 192.168.1.201 pkill mutilate
	    sleep 1
	    ssh 192.168.1.202 pkill mutilate
	    sleep 1
	    ssh 192.168.1.30 pkill mutilate
	    sleep 1
	    timeout 600 python3 -u mutilate_bench.py qps_itr $1 $d
	done
    done
}

function run4
{
    for i in `seq 1 1 $NITERS`;
    do
	for d in $RXU;
	do
	    ssh $SERVER "pkill memcached"
	    sleep 1
	    ssh $SERVER "pkill silotpcc-linux"
	    sleep 1
	    pkill mutilate
	    sleep 1
	    ssh 192.168.1.201 pkill mutilate
	    sleep 1
	    ssh 192.168.1.202 pkill mutilate
	    sleep 1
	    ssh 192.168.1.203 pkill mutilate
	    sleep 1
	    ssh 192.168.1.204 pkill mutilate
	    sleep 1
	    ssh 192.168.1.205 pkill mutilate
	    sleep 1
	    timeout 600 python3 -u mutilate_bench.py $1 $2 $3 $4
	done
    done
}

function run3
{
    while true; do
	ssh $SERVER "pkill memcached"
	pkill mutilate
	sleep 1
	timeout 90 python3 -u mutilate_bench.py overnight
	sleep 1
    done
}


function run6
{
    if [ $OUTFILE -eq 1 ]; then
	echo $currdate
	mkdir -p "mcd_data/$currdate"
	echo "Running $1 RXU=$RXU NITERS=$NITERS" > "mcd_data/$currdate/command.txt"
    fi

    for iter in `seq 2 1 $NITERS`;
    do
	for rxu in $RXU;
	do
	    echo $rxu
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    sleep 0.2
	    
	    ssh $SERVER "pkill memcached"
	    pkill mutilate
	    sleep 1
	    echo "**** ITER="$iter "RXU="$rxu
	    intrstart1=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
	    intrstart3=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-3" | tr -s ' ' | cut -d ' ' -f 6 )
	    intrstart5=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-5" | tr -s ' ' | cut -d ' ' -f 8 )
	    intrstart7=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-7" | tr -s ' ' | cut -d ' ' -f 10 )
	    intrstart9=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-9" | tr -s ' ' | cut -d ' ' -f 12 )
	    intrstart11=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-11" | tr -s ' ' | cut -d ' ' -f 14 )
	    intrstart13=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-13" | tr -s ' ' | cut -d ' ' -f 16 )
	    intrstart15=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-15" | tr -s ' ' | cut -d ' ' -f 18 )
	    python -u mutilate_bench.py
	    intrend1=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
	    intrend3=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-3" | tr -s ' ' | cut -d ' ' -f 6 )
	    intrend5=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-5" | tr -s ' ' | cut -d ' ' -f 8 )
	    intrend7=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-7" | tr -s ' ' | cut -d ' ' -f 10 )
	    intrend9=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-9" | tr -s ' ' | cut -d ' ' -f 12 )
	    intrend11=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-11" | tr -s ' ' | cut -d ' ' -f 14 )
	    intrend13=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-13" | tr -s ' ' | cut -d ' ' -f 16 )
	    intrend15=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-15" | tr -s ' ' | cut -d ' ' -f 18 )

	    intrtot1=$((intrend1-intrstart1))
	    intrtot3=$((intrend3-intrstart3))
	    intrtot5=$((intrend5-intrstart5))
	    intrtot7=$((intrend7-intrstart7))
	    intrtot9=$((intrend9-intrstart9))
	    intrtot11=$((intrend11-intrstart11))
	    intrtot13=$((intrend13-intrstart13))
	    intrtot15=$((intrend15-intrstart15))
	    
	    if [ $OUTFILE -eq 1 ]; then
		cp mutilate.log "mcd_data/$currdate/mcd_"$rxu\_$iter".log"
		scp $SERVER:~/perf.out "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot1",itr1" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot3",itr3" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot5",itr5" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot7",itr7" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot9",itr9" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot11",itr11" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot13",itr13" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot15",itr15" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
	    fi
	    sleep 1
	done
    done
}

function cleanAll
{
    ssh $SERVER "pkill memcached"
    sleep 0.5
    ssh $SERVER "pkill silotpcc-linux"
    sleep 0.5
    pkill mutilate
    sleep 0.5
    ssh 192.168.1.201 pkill mutilate
    sleep 0.5
    ssh 192.168.1.202 pkill mutilate
    sleep 0.5
    ssh 192.168.1.203 pkill mutilate
    sleep 0.5
    ssh 192.168.1.204 pkill mutilate
    sleep 0.5
    ssh 192.168.1.205 pkill mutilate
    sleep 0.5
    ssh $SERVER ifup enp4s0f1
    sleep 0.5

}

function runMQPS
{
    for mqps in $MQPS; do
	NITERS=$NITERS  runMutilateBench --qps $mqps "$@"
	sleep 1
    done
}

function cleanAllLocal
{
    ssh $SERVER "pkill memcached"
    sleep 0.5
    ssh $SERVER "pkill silotpcc-linux"
    sleep 0.5
    pkill mutilate
    ssh $SERVER ifup enp4s0f1
    sleep 0.5

}

function runMutilateBenchLocal
{
    for i in `seq 1 1 $NITERS`;
    do
	cleanAllLocal
	timeout 120 python3 -u mutilate_bench.py "$@"
    done
}

function runMQPSLocal
{
    for mqps in $MQPS; do
	NITERS=$NITERS runMutilateBenchLocal --qps $mqps "$@"
	sleep 1
    done
}

function runOvernight
{
    #counter=0
    while true; do
	# QPS Range: 50000 - 1100000
	mqps=0
	let "mqps = (($RANDOM % 27)+1) * 40000"

	# ITR Range: 2 - 1024
	itr=0
	let "itr = (($RANDOM % 511)+1) * 2"

	# Rapl Range: 40 - 130
	rapl=0
	let "rapl = (($RANDOM % 45) * 2) + 40"

	#echo $mqps $itr $rapl
	ITERS='1' MQPS=$mqps runMQPSLocal --bench='mcd' --time=30 --itr=$itr --rapl=$rapl --type='usr' --verbose 1
	
	#let "counter = counter + 1"
	#if [ $counter = 2 ]; then
	#    break
	#fi
	sleep 1
    done
}

function runov5
{
    MQPS='800000 600000 400000 200000' runMQPS --bench='mcd' --itr=14 --time=60 --type='etc' --verbose 1
    sleep 1
    echo " -------------------------------------------------------------------------------------------"
    MQPS='1000000 800000 600000 400000 200000' runMQPS --bench='mcd' --itr=14 --time=60 --type='usr' --verbose 1
}

function searchNIC
{
    qps=$1
    itr=$2
    workload=$3
    type=$4

    for((thresh=0; thresh<3; thresh++)); do
	for((ring=0; ring<2; ring++)); do
	    for((dtxmx=0; dtxmx<3; dtxmx++)); do
    		for((dca=0; dca<2; dca++)); do
		    if [ $workload = "mcd" ]; then
			echo ""
			echo "NITERS=1 runMutilateBench --bench $workload --qps $qps --time 120 --type $type --itr $itr --ring $ring --dtxmx $dtxmx --dca $dca --thresh $thresh --restartnic 1 --verbose 1"
			NITERS=1 runMutilateBench --bench $workload --qps $qps --time 120 --type $type --itr $itr --ring $ring --dtxmx $dtxmx --dca $dca --thresh $thresh --restartnic 1 --verbose 1
		    else
			echo ""
			echo "NITERS=1 runMutilateBench --bench $workload --qps $qps --time 120 --itr $itr --ring $ring --dtxmx $dtxmx --dca $dca --thresh $thresh --restartnic 1 --verbose 1"
			NITERS=1 runMutilateBench --bench $workload --qps $qps --time 120 --itr $itr --ring $ring --dtxmx $dtxmx --dca $dca --thresh $thresh --restartnic 1 --verbose 1
		    fi
		    sleep 1
		done
	    done
	done
    done
}

function runo3
{
    echo "runo3"
    sleep 1
    cleanAll
    sleep 1

    # ETC 400000,500000,600000,700000,800000,900000
    #searchNIC 400000 378 mcd etc >> mcd_data/10_25_19_MCD_ETC_QPS_400000.log
    #searchNIC 500000 358 mcd etc >> mcd_data/10_25_19_MCD_ETC_QPS_500000.log
    #searchNIC 600000 344 mcd etc >> mcd_data/10_25_19_MCD_ETC_QPS_600000.log
    #searchNIC 700000 334 mcd etc >> mcd_data/10_25_19_MCD_ETC_QPS_700000.log
    #searchNIC 800000 300 mcd etc >> mcd_data/10_25_19_MCD_ETC_QPS_800000.log
    searchNIC 900000 256 mcd etc >> mcd_data/10_25_19_MCD_ETC_QPS_900000.log

    sleep 1
    cleanAll
    sleep 1
    
    #USR 400000,600000,800000,1000000,1100000,1200000,1300000,1400000,1500000
    #searchNIC 400000 390 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_400000.log
    #searchNIC 600000 378 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_600000.log
    #searchNIC 800000 368 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_800000.log
    #searchNIC 1000000 364 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_1000000.log
    #searchNIC 1100000 356 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_1100000.log
    #searchNIC 1200000 350 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_1200000.log
    #searchNIC 1300000 332 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_1300000.log
    #searchNIC 1400000 328 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_1400000.log
    searchNIC 1500000 268 mcd usr >> mcd_data/10_25_19_MCD_USR_QPS_1500000.log

    sleep 1
    cleanAll
    sleep 1

    #SILO 140000,160000,180000,200000,210000,220000,230000,240000,250000
    #searchNIC 140000 648 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_140000.log
    #searchNIC 160000 640 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_160000.log
    #searchNIC 180000 568 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_180000.log
    #searchNIC 200000 500 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_200000.log
    #searchNIC 210000 488 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_210000.log
    #searchNIC 220000 298 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_220000.log
    searchNIC 230000 188 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_230000.log
    searchNIC 240000 168 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_240000.log
    searchNIC 250000 48 zygos 1 >> mcd_data/10_25_19_MCD_SILO_QPS_250000.log
}

function searchITRLocal
{
    sla=500
    TYPE='usr'
    for mqps in 10000 20000 40000 60000 80000 100000 200000 300000 400000 500000 600000 700000 800000 900000; do
	NITERS=1 runMutilateBenchLocal --qps $mqps --time 60 --itr 16 --bench mcd --type $TYPE
    	satisfy_sla=0
    	violate_sla=0
    	for itr in 100 160 220 280 340 400 460 500;
    	do
    	    NITERS=1 runMutilateBenchLocal --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
	    cat searchPowerLimit.log
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-60))
    		violate_sla=$itr
    		echo "ITR=$itr mqps=$mqps SLA < $read99th"
    	      	break
    	    fi
    	done

    	violate_sla=$((violate_sla-10))
    	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$violate_sla; itr>$satisfy_sla; itr-=10)); do
    	    NITERS=1 runMutilateBenchLocal --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
	    cat searchPowerLimit.log
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "ITR=$itr mqps=$mqps $read99th < SLA"
    		satisfy_sla=$itr
    		violate_sla=$((itr+10))
    		break
    	    fi
    	done

	violate_sla=$((violate_sla+10))
    	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$satisfy_sla; itr<=$violate_sla; itr+=2)); do
    	    NITERS=1 runMutilateBenchLocal --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
	    cat searchPowerLimit.log
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	done
    done
}

function searchITR
{
    # 200000 400000 600000 800000
    sla=500
    TYPE='etc'
    for mqps in 200000 400000 600000 800000; do
    	satisfy_sla=0
    	violate_sla=0
    	for itr in 100 160 220 280 340 400 460 520;
    	do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-60))
    		violate_sla=$itr
    		echo "ITR=$itr mqps=$mqps SLA < $read99th"
    	      	break
    	    fi
    	done

    	violate_sla=$((violate_sla-10))
    	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$violate_sla; itr>$satisfy_sla; itr-=10)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "ITR=$itr mqps=$mqps $read99th < SLA"
    		satisfy_sla=$itr
    		violate_sla=$((itr+10))
    		break
    	    fi
    	done

	violate_sla=$((violate_sla+10))
    	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$satisfy_sla; itr<=$violate_sla; itr+=2)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-2))
    		echo "satisfy_sla=$satisfy_sla"
    		#NITERS=1 runMutilateBench --qps $mqps --time 120 --itr $satisfy_sla --bench mcd --type $TYPE --verbose 1
    		NITERS=3 runMutilateBench --qps $mqps --time 60 --itr $satisfy_sla --bench mcd --type $TYPE --verbose 1 >> mcd_data/1_1_20_MCD_ETC_QPS_$mqps.log
		echo "------------------------------------" >> mcd_data/1_1_20_MCD_ETC_QPS_$mqps.log
    		break
    	    fi
    	done
    done

    sleep 1
    cleanAll
    sleep 1
    
    # USR: 600000 800000 1000000 1100000 1200000 1300000 1400000 1500000
    sla=500
    TYPE='usr'
    for mqps in 200000 400000 600000 800000 1000000; do
    	satisfy_sla=0
    	violate_sla=0
    	for itr in 100 160 220 280 340 400 460 520;
    	do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-60))
    		violate_sla=$itr
    		echo "ITR=$itr mqps=$mqps SLA < $read99th"
    	      	break
    	    fi
    	done

    	violate_sla=$((violate_sla-10))
    	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$violate_sla; itr>$satisfy_sla; itr-=10)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "ITR=$itr mqps=$mqps $read99th < SLA"
    		satisfy_sla=$itr
    		violate_sla=$((itr+10))
    		break
    	    fi
    	done

    	violate_sla=$((violate_sla+10))
    	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$satisfy_sla; itr<=$violate_sla; itr+=2)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-2))
    		echo "satisfy_sla=$satisfy_sla"
    		#NITERS=1 runMutilateBench --qps $mqps --time 120 --itr $satisfy_sla --bench mcd --type $TYPE --verbose 1
    		NITERS=3 runMutilateBench --qps $mqps --time 60 --itr $satisfy_sla --bench mcd --type $TYPE --verbose 1 >> mcd_data/1_1_20_MCD_USR_QPS_$mqps.log
    		echo "------------------------------------" >> mcd_data/1_1_20_MCD_USR_QPS_$mqps.log
    		break
    	    fi
    	done
    done

    sleep 1
    cleanAll
    sleep 1

    
    #SILO: 140000 160000 180000 200000 210000 220000 230000 240000 250000
    # sla=1000
    # for mqps in 200000 210000 220000 230000; do
    # 	satisfy_sla=0
    # 	violate_sla=0
    # 	for itr in 100 200 300 400 500 600 700 800 900;
    # 	do
    # 	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench zygos --pow_search_enable 1 > searchPowerLimit.log
    # 	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    # 	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    # 	    if [ $read99th -gt $sla ]
    # 	    then
    # 		satisfy_sla=$((itr-60))
    # 		violate_sla=$itr
    # 		echo "ITR=$itr mqps=$mqps SLA < $read99th"
    # 	      	break
    # 	    fi
    # 	done

    # 	violate_sla=$((violate_sla-10))
    # 	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    # 	for((itr=$violate_sla; itr>$satisfy_sla; itr-=10)); do
    # 	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench zygos --pow_search_enable 1 > searchPowerLimit.log
    # 	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    # 	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    # 	    if [ $read99th -lt $sla ]
    # 	    then
    # 		echo "ITR=$itr mqps=$mqps $read99th < SLA"
    # 		satisfy_sla=$itr
    # 		violate_sla=$((itr+10))
    # 		break
    # 	    fi
    # 	done

    # 	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    # 	for((itr=$satisfy_sla; itr<=$violate_sla; itr+=2)); do
    # 	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench zygos --pow_search_enable 1 > searchPowerLimit.log
    # 	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    # 	    echo "ITR=$itr mqps=$mqps 99percentile=$read99th"
    # 	    if [ $read99th -gt $sla ]
    # 	    then
    # 		satisfy_sla=$((itr-2))
    # 		echo "satisfy_sla=$satisfy_sla"
    # 		#NITERS=1 runMutilateBench --qps $mqps --time 120 --itr $satisfy_sla --bench zygos --verbose 1
    # 		NITERS=3 runMutilateBench --qps $mqps --time 120 --itr $satisfy_sla --bench zygos --verbose 1 >> mcd_data/10_25_19_MCD_SILO_QPS_$mqps.log
    # 		break
    # 	    fi
    # 	done
    # done

}

function rebootDynamic
{
    scp dynamic_interrupt_off/* 192.168.1.230:/boot/
    ssh 192.168.1.230 reboot &
    sleep 600
    ssh $SERVER ~/perf/run.sh
    sleep 1
}

function rebootDefault
{
    scp default/* 192.168.1.230:/boot/
    ssh 192.168.1.230 reboot &
    sleep 600
    ssh $SERVER ~/perf/run.sh
    
}

function searchRAPLETC
{
    echo "ETC start"
    sla=500
    for mqps in 200000 400000 600000 800000; do
	satisfy_sla=0
	violate_sla=0
	for rapl in 40 50 60 70 80 90 100 110 120 130;
	do
	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type etc --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "ETC RAPL=$rapl mqps=$mqps $read99th < SLA"
    		satisfy_sla=$rapl
    		break
    	    else
    		violate_sla=$rapl
    		echo "ETC RAPL=$rapl mqps=$mqps $read99th > SLA"
    	    fi
	done

	violate_sla=$((violate_sla+2))
	satisfy_sla=$((satisfy_sla+4))
	for ((rapl=$violate_sla; rapl < $satisfy_sla; rapl+=2)); do
	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type etc --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
	    echo "ETC RAPL=$rapl mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
		echo "FOUND ETC RAPL=$rapl mqps=$mqps $read99th < SLA"
		NITERS=2 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type etc --verbose 1
    		break
	    fi
	done	
    done    
}

function searchRAPLUSR
{
    echo "USR start"
    sla=500
    TYPE='usr'
    for mqps in 200000 400000 600000 800000; do
    	satisfy_sla=0
    	violate_sla=0
    	for rapl in 40 50 60 70 80 90 100 110 120 130;
    	do
            echo "MCD USR RAPL=$rapl mqps=$mqps"
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "MCD USR RAPL=$rapl mqps=$mqps $read99th < SLA"
    		satisfy_sla=$rapl
    		break
    	    else
    		violate_sla=$rapl
    		echo "MCD USR RAPL=$rapl mqps=$mqps SLA < $read99th"
    	    fi
    	done

	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
	
	violate_sla=$((violate_sla+2))
	satisfy_sla=$((satisfy_sla+4))
	for ((rapl=$violate_sla; rapl < $satisfy_sla; rapl+=2)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "MCD USR RAPL=$rapl mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "FOUND MCD USR RAPL=$rapl mqps=$mqps $read99th < SLA"
    		NITERS=3 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type $TYPE --verbose 1
    		break
    	    fi
	done

	sleep 1
	cleanAll
	sleep 1
    done

}

function searchITRUSR
{
    sla=500
    TYPE='usr'
    for mqps in 200000 400000 600000 800000; do
    	satisfy_sla=0
    	violate_sla=0
    	for itr in 100 160 220 280 340 400 460 520;
    	do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "USR ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-60))
    		violate_sla=$itr
    		echo "USR ITR=$itr mqps=$mqps SLA < $read99th"
    	      	break
    	    fi
    	done

    	violate_sla=$((violate_sla-10))
    	echo "USR satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$violate_sla; itr>$satisfy_sla; itr-=10)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "USR ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "USR ITR=$itr mqps=$mqps $read99th < SLA"
    		satisfy_sla=$itr
    		violate_sla=$((itr+10))
    		break
    	    fi
    	done

    	violate_sla=$((violate_sla+10))
    	echo "USR satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
    	for((itr=$satisfy_sla; itr<=$violate_sla; itr+=2)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --itr $itr --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "USR ITR=$itr mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -gt $sla ]
    	    then
    		satisfy_sla=$((itr-2))
    		echo "USR satisfy_sla=$satisfy_sla"
    		NITERS=3 runMutilateBench --qps $mqps --time 60 --itr $satisfy_sla --bench mcd --type $TYPE --verbose 1
    		break
    	    fi
    	done
    done

}

function run2
{   
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1

    echo "performance etc rapl-min poll-mode"
    searchRAPLETC
    sleep 1
    echo "********************************************************************"

    echo "performance usr rapl-min poll-mode"
    searchRAPLUSR
    sleep 1
    echo "********************************************************************"

    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    
    echo "powersave etc rapl-min poll-mode"
    searchRAPLETC
    sleep 1
    echo "********************************************************************"

    echo "powersave usr rapl-min poll-mode"
    searchRAPLUSR
    sleep 1
    echo "********************************************************************"
}

function run
{
    echo "performance dynamic etc"
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --type='etc' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "performance dynamic usr"
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --type='usr' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "powersave dynamic etc"
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --type='etc' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "powersave dynamic usr"
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --type='usr' --verbose 1
    sleep 1
    echo "********************************************************************"
    
    echo "performance dynamic rapl-min etc"
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1
    NITERS='3' MQPS='200000' runMQPS --bench='mcd' --time=60 --rapl=52 --type='etc' --verbose 1
    NITERS='3' MQPS='400000' runMQPS --bench='mcd' --time=60 --rapl=60 --type='etc' --verbose 1
    NITERS='3' MQPS='600000' runMQPS --bench='mcd' --time=60 --rapl=66 --type='etc' --verbose 1
    NITERS='3' MQPS='800000' runMQPS --bench='mcd' --time=60 --rapl=74 --type='etc' --verbose 1
    echo "********************************************************************"

    echo "powersave dynamic rapl-min etc"
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    NITERS='3' MQPS='200000' runMQPS --bench='mcd' --time=60 --rapl=34 --type='etc' --verbose 1
    NITERS='3' MQPS='400000' runMQPS --bench='mcd' --time=60 --rapl=52 --type='etc' --verbose 1
    NITERS='3' MQPS='600000' runMQPS --bench='mcd' --time=60 --rapl=66 --type='etc' --verbose 1
    NITERS='3' MQPS='800000' runMQPS --bench='mcd' --time=60 --rapl=76 --type='etc' --verbose 1
    echo "********************************************************************"
    
    echo "performance dynamic rapl-min usr"
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1
    searchRAPLUSR
    echo "********************************************************************"
    
    echo "powersave dynamic rapl-min usr"
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    searchRAPLUSR
    echo "********************************************************************"

    echo "starting reboot"
    rebootDynamic
    ssh $SERVER ./perf/cpufreq_performance.sh
    echo "finished reboot"
    NITERS='1' MQPS='200000' runMQPS --bench='mcd' --time=10 --itr=16 --type='etc' --verbose 1
    echo "********************************************************************"
    
    echo "performance static etc itr-16"
    sleep 1
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --itr=16 --type='etc' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "performance static usr itr-16"
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --itr=16 --type='usr' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "powersave static etc itr-16"
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --itr=16 --type='etc' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "powersave static usr itr-16"
    NITERS='3' MQPS='200000 400000 600000 800000 1000000 1200000' runMQPS --bench='mcd' --time=60 --itr=16 --type='usr' --verbose 1
    sleep 1
    echo "********************************************************************"

    echo "performance static etc itr-max"    
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1
    NITERS='3' MQPS='200000' runMQPS --bench='mcd' --time=60 --itr=430 --type='etc' --verbose 1
    NITERS='3' MQPS='400000' runMQPS --bench='mcd' --time=60 --itr=410 --type='etc' --verbose 1
    NITERS='3' MQPS='600000' runMQPS --bench='mcd' --time=60 --itr=384 --type='etc' --verbose 1
    NITERS='3' MQPS='800000' runMQPS --bench='mcd' --time=60 --itr=336 --type='etc' --verbose 1
    echo "********************************************************************"

    echo "powersave static etc itr-max"    
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    NITERS='3' MQPS='400000' runMQPS --bench='mcd' --time=60 --itr=372 --type='etc' --verbose 1
    NITERS='3' MQPS='600000' runMQPS --bench='mcd' --time=60 --itr=320 --type='etc' --verbose 1
    NITERS='3' MQPS='800000' runMQPS --bench='mcd' --time=60 --itr=264 --type='etc' --verbose 1
    echo "********************************************************************"

    echo "performance static usr itr-max"
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1
    searchITRUSR
    echo "********************************************************************"

    echo "powersave static usr itr-max"
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    searchITRUSR
    echo "********************************************************************"
}


function searchPowerLimit
{
    # ETC:
    echo "ETC start"
    sla=500
    for mqps in 200000 400000 600000 800000; do
	satisfy_sla=0
	violate_sla=0
	for rapl in 35 40 50 60 70 80 90 100 110 120 130;
	do
	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --itr 16 --bench mcd --type etc --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "ETC RAPL=$rapl mqps=$mqps $read99th < SLA"
    		satisfy_sla=$rapl
    		break
    	    else
    		violate_sla=$rapl
    		echo "ETC RAPL=$rapl mqps=$mqps $read99th > SLA"
    	    fi
	done

	violate_sla=$((violate_sla+2))
	satisfy_sla=$((satisfy_sla+4))
	for ((rapl=$violate_sla; rapl < $satisfy_sla; rapl+=2)); do
	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --itr 16 --bench mcd --type etc --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
	    echo "ETC RAPL=$rapl mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
		echo "FOUND ETC RAPL=$rapl mqps=$mqps $read99th < SLA"
		NITERS=3 runMutilateBench --qps $mqps --time 60 --rapl $rapl --itr 16 --bench mcd --type etc --verbose 1
    		break
	    fi
	done	
    done

    sleep 1
    cleanAll
    sleep 10
    
    echo "USR start"
    sla=500
    TYPE='usr'
    for mqps in 200000 400000 600000 800000 1000000; do
    	satisfy_sla=0
    	violate_sla=0
    	for rapl in 35 40 50 60 70 80 90 100 110 120 130;
    	do
            echo "MCD USR RAPL=$rapl mqps=$mqps"
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --itr 16 --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "MCD USR RAPL=$rapl mqps=$mqps $read99th < SLA"
    		satisfy_sla=$rapl
    		break
    	    else
    		violate_sla=$rapl
    		echo "MCD USR RAPL=$rapl mqps=$mqps SLA < $read99th"
    	    fi
    	done

	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
	
	violate_sla=$((violate_sla+2))
	satisfy_sla=$((satisfy_sla+4))
	for ((rapl=$violate_sla; rapl < $satisfy_sla; rapl+=2)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --itr 16 --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "MCD USR RAPL=$rapl mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "FOUND MCD USR RAPL=$rapl mqps=$mqps $read99th < SLA"
    		NITERS=3 runMutilateBench --qps $mqps --time 60 --rapl $rapl --itr 16 --bench mcd --type $TYPE --verbose 1
    		break
    	    fi
	done

	sleep 1
	cleanAll
	sleep 1
    done

    sleep 1
    cleanAll
    sleep 10
}

function searchPowerLimitUSRSILO
{
    # USR: 1500000, 1400000, 1200000, 1000000, 800000, 600000, 400000, 200000
    echo "USR start"
    sla=500
    TYPE='usr'
    # 1400000 
    for mqps in 1200000 1000000 800000 600000 400000; do
    	satisfy_sla=0
    	violate_sla=0
    	for rapl in 35 40 50 60 70 80 90 100 110 120 130;
    	do
            echo "MCD USR RAPL=$rapl mqps=$mqps"
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "MCD USR RAPL=$rapl mqps=$mqps $read99th < SLA"
    		satisfy_sla=$rapl
    		break
    	    else
    		violate_sla=$rapl
    		echo "MCD USR RAPL=$rapl mqps=$mqps SLA < $read99th"
    	    fi
    	done

	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
	
	violate_sla=$((violate_sla+2))
	satisfy_sla=$((satisfy_sla+4))
	for ((rapl=$violate_sla; rapl < $satisfy_sla; rapl+=2)); do
    	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type $TYPE --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    echo "MCD USR RAPL=$rapl mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "FOUND MCD USR RAPL=$rapl mqps=$mqps $read99th < SLA"
    		NITERS=3 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench mcd --type $TYPE --verbose 1
    		break
    	    fi
	done

	sleep 1
	cleanAll
	sleep 1
    done

    sleep 1
    cleanAll
    sleep 1

    echo "SILO start" 
    # SILO: 250000 240000 230000 220000 210000 200000 180000 160000 140000
    sla=500
    for mqps in 20000 30000 50000 80000 120000 160000; do
	satisfy_sla=0
	violate_sla=0
	for rapl in 35 40 50 60 70 80 90 100 110 120 130;
	do
	    echo "SILO RAPL=$rapl mqps=$mqps"
	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench zygos --pow_search_enable 1 > searchPowerLimit.log
	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
    	    if [ $read99th -lt $sla ]
    	    then
    		echo "SILO RAPL=$rapl mqps=$mqps $read99th < SLA"
    		satisfy_sla=$rapl
    		break
    	    else
    		violate_sla=$rapl
    		echo "SILO RAPL=$rapl mqps=$mqps SLA < $read99th"
    	    fi
	done

	echo "satisfiy_sla=$satisfy_sla violate_sla=$violate_sla"
	
	violate_sla=$((violate_sla+2))
	satisfy_sla=$((satisfy_sla+4))
	for ((rapl=$violate_sla; rapl < $satisfy_sla; rapl+=2)); do
	    NITERS=1 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench zygos --pow_search_enable 1 > searchPowerLimit.log
    	    read99th=$(tail -n 1 searchPowerLimit.log | cut -d. -f1)
	    echo "SILO RAPL=$rapl mqps=$mqps 99percentile=$read99th"
    	    if [ $read99th -lt $sla ]
    	    then
		echo "SILO RAPL=$rapl mqps=$mqps $read99th < SLA"
		NITERS=3 runMutilateBench --qps $mqps --time 60 --rapl $rapl --bench zygos --verbose 1
    		break
	    fi
	done
	
	sleep 1
	cleanAll
	sleep 1
    done

    
}

function runov4
{
    ssh $SERVER ./perf/cpufreq_powersave.sh
    sleep 1
    searchPowerLimit
    #sleep 1
    #searchPowerLimitUSRSILO
    
    echo "------------------------------------------------"
    
    ssh $SERVER ./perf/cpufreq_performance.sh
    sleep 1
    searchPowerLimit
    #sleep 1
    #searchPowerLimitUSRSILO       
}

function runon2
{
    # ETC: 1000000, 900000, 800000, 700000, 600000, 500000, 400000, 300000, 200000, 100000
    echo "******************** ETC START **********************************"
    NITERS=3 runMutilateBench --bench mcd --qps 1400000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1300000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1200000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1100000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1000000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 900000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 800000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 700000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 600000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 500000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 400000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 300000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 200000 --time 120 --type etc
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 100000 --time 120 --type etc
    sleep 1
    echo "******************** ETC END **********************************"
    
    # USR: 1600000, 1400000, 1200000, 1000000, 800000, 600000, 400000, 200000
    echo "******************** USR START **********************************"
    NITERS=3 runMutilateBench --bench mcd --qps 1900000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1800000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1700000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1600000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1500000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1400000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1300000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1200000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1100000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 1000000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 800000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 600000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 400000 --time 120 --type usr
    sleep 1
    NITERS=3 runMutilateBench --bench mcd --qps 200000 --time 120 --type usr
    sleep 1
    echo "******************** USR END **********************************"
    
    # ZYGOS: 250000 240000 230000 220000 210000 200000 180000 160000 140000 120000 100000 80000 60000 40000
    echo "******************** ZYGOS START **********************************"
    NITERS=3 runMutilateBench --qps 270000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 260000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 250000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 240000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 230000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 220000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 210000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 200000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 180000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 160000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 140000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 120000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 100000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 80000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 60000 --time 120 --bench zygos
    sleep 1
    NITERS=3 runMutilateBench --qps 40000 --time 120 --bench zygos
    sleep 1
    echo "******************** ZYGOS END **********************************"
}


"$@"

