source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"
mkdir -p $DUMP_DIR

DT=101
ABM=110

TCP=1

SERVERS=16
LEAVES=2
SPINES=1
LINKS=2
SERVER_LEAF_CAP=10
LEAF_SPINE_CAP=10
LATENCY=10

RED_MIN=65
RED_MAX=65

N_PRIO=2

ALPHAFILE="$DIR/alphas"
CDFFILE="$DIR/websearch.txt"

ALPHA_UPDATE_INT=1

STATIC_BUFFER=0
BUFFER_PER_PORT_PER_GBPS=9.6
BUFFER=$(python3 -c "print(int($BUFFER_PER_PORT_PER_GBPS*1024*($SERVERS+$LINKS*$SPINES)*$SERVER_LEAF_CAP))")

START_TIME=0
END_TIME=3
FLOW_END_TIME=1.5

cd $NS3

N=0

BURST_SIZES=0.3
BURST_SIZE=$(python3 -c "print($BURST_SIZES*$BUFFER)")
BURST_FREQ=2

for ALG in $DT $ABM; do
    for LOAD in 0.4 0.6 0.8; do
        FLOWFILE="$DUMP_DIR/fcts-single-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
        TORFILE="$DUMP_DIR/tor-single-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
        while [[ $(ps aux | grep "ns3.39-abm-evaluation-default" | grep -v grep | wc -l) -ge $N_CORES ]]; do
            sleep 30
            echo "waiting for cores, $N running..."
        done
        N=$((N+1))
        (time ./waf --run "abm-evaluation --load=$LOAD --StartTime=$START_TIME --EndTime=$END_TIME --FlowLaunchEndTime=$FLOW_END_TIME --serverCount=$SERVERS --spineCount=$SPINES --leafCount=$LEAVES --linkCount=$LINKS --spineLeafCapacity=$LEAF_SPINE_CAP --leafServerCapacity=$SERVER_LEAF_CAP --linkLatency=$LATENCY --TcpProt=$TCP --BufferSize=$BUFFER --statBuf=$STATIC_BUFFER --algorithm=$ALG --RedMinTh=$RED_MIN --RedMaxTh=$RED_MAX --request=$BURST_SIZE --queryRequestRate=$BURST_FREQ --nPrior=$N_PRIO --alphasFile=$ALPHAFILE --cdfFileName=$CDFFILE --alphaUpdateInterval=$ALPHA_UPDATE_INT --fctOutFile=$FLOWFILE --torOutFile=$TORFILE"; echo "$FLOWFILE") &
        sleep 2
    done
done

wait

echo "DONE"