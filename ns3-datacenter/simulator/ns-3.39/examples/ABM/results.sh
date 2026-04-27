source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"

DT=101
FAB=102
CS=103
IB=104
ABM=110

TCP=1   # CUBIC

SERVERS=16
LEAVES=2
SPINES=1
LINKS=2
SERVER_LEAF_CAP=10
LEAF_SPINE_CAP=10
LATENCY=10
N_PRIO=2

BURST_SIZES=0.3
BURST_FREQ=2

cd $DIR

echo "short999fct short99fct short95fct shortavgfct shortmedfct incast999fct incast99fct incast95fct incastavgfct incastmedfct long999fct long99fct long95fct longavgfct longmedfct avgTh medTh bufmax buf999 buf99 buf95 avgBuf medBuf load burst alg tcp scenario nprio"

for ALG in $DT $FAB $CS $IB $ABM; do
    for LOAD in 0.4 0.6 0.8; do
        FLOWFILE="$DUMP_DIR/fcts-single-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
        TORFILE="$DUMP_DIR/tor-single-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
        python3 parseData-singleQ.py "$FLOWFILE" "$TORFILE" $LEAF_SPINE_CAP $(( $LATENCY*8 )) $LOAD $BURST_SIZES $ALG $TCP single $N_PRIO
    done
done
