source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"
mkdir -p $DUMP_DIR

DT=101
FAB=102
CS=103
IB=104
ABM=110

BUF_ALGS=($DT $FAB $CS $IB $ABM)

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

LOAD=0.4
BURST_FREQ=2
N_CORES=2

cd $NS3

for BURST_SIZES in 0.25 0.5 0.75; do
    BURST_SIZE=$(python3 -c "print($BURST_SIZES*$BUFFER)")
    for ALG in "${BUF_ALGS[@]}"; do
        while [[ $(jobs -r | wc -l) -ge $N_CORES ]]; do
            sleep 5
        done

        FLOWFILE="$DUMP_DIR/fcts-bufburst-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
        TORFILE="$DUMP_DIR/tor-bufburst-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"

        echo "Running ALG=$ALG BURST=$BURST_SIZES"

        (
            time ./waf --run "abm-evaluation \
                --load=$LOAD \
                --StartTime=$START_TIME \
                --EndTime=$END_TIME \
                --FlowLaunchEndTime=$FLOW_END_TIME \
                --serverCount=$SERVERS \
                --spineCount=$SPINES \
                --leafCount=$LEAVES \
                --linkCount=$LINKS \
                --spineLeafCapacity=$LEAF_SPINE_CAP \
                --leafServerCapacity=$SERVER_LEAF_CAP \
                --linkLatency=$LATENCY \
                --TcpProt=$TCP \
                --BufferSize=$BUFFER \
                --statBuf=$STATIC_BUFFER \
                --algorithm=$ALG \
                --RedMinTh=$RED_MIN \
                --RedMaxTh=$RED_MAX \
                --request=$BURST_SIZE \
                --queryRequestRate=$BURST_FREQ \
                --nPrior=$N_PRIO \
                --alphasFile=$ALPHAFILE \
                --cdfFileName=$CDFFILE \
                --alphaUpdateInterval=$ALPHA_UPDATE_INT \
                --fctOutFile=$FLOWFILE \
                --torOutFile=$TORFILE" && echo "Finished -> $FLOWFILE"
        ) &
    done
done

wait
echo "DONE"