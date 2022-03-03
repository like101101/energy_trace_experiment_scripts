#! /bin/bash

currdate=`date +%m_%d_%Y_%H_%M_%S`

#export MQPS=${MQPS:='100000 200000 400000 600000 800000 900000'}
#export MDVFS=${MDVFS:="0x1d00 0x1c00 0x1b00 0x1a00 0x1900 0x1800 0x1700 0x1600 0x1500 0x1400 0x1300 0x1200 0x1100 0x1000 0xf00 0xe00 0xd00 0xc00"}
#export MRAPL=${MRAPL:-"135 125 115 105 95 85 75 65 55 45"}
#export ITRS=${ITRS:-"2 4 10 20 30 40 50 100 200 300 400"}

export NITERS=${NITERS:='2'}
export BEGIN_ITER=${BEGIN_ITER:='0'}
export MDVFS=${MDVFS:="0x1d00"}
export MQPS=${MQPS:='200000 400000 600000'}
export ITRS=${ITRS:-"1"}
export MRAPL=${MRAPL:-"135"}

function runMutilateBench {
    timeout 600 python3 -u mutilate_bench.py "$@"
}

function runMCD {
    echo "DVFS ${MDVFS}"
    echo "ITRS ${ITRS}"
    echo "MQPS ${MQPS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    echo "mkdir ${currdate}"
    mkdir ${currdate}

    for qps in ${MQPS}; do
	for itr in $ITRS; do
	    for dvfs in ${MDVFS}; do
		for r in ${MRAPL}; do
		    for i in `seq ${BEGIN_ITER} 1 $NITERS`; do
		        runMutilateBench --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}
			sleep 1
			mv linux.mcd.* ${currdate}/
			sleep 1
			echo "FINISHED: runMutilateBench --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
		    done
		done
	    done
	done
    done
}

"$@"

