source config.sh

DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"

DT=101
FAB=102
CS=103
IB=104
ABM=110
BUF_ALGS=($DT $FAB $CS $IB $ABM)

TCP=1
LEAF_SPINE_CAP=10
LATENCY=10
N_PRIO=2

FLOW_START=0
FLOW_END=1.5
BURST_SIZES=0.3

echo "short999fct short99fct short95fct shortavgfct shortmedfct incast999fct incast99fct incast95fct incastavgfct incastmedfct long999fct long99fct long95fct longavgfct longmedfct avgTh medTh bufmax buf999 buf99 buf95 avgBuf medBuf load burst alg tcp scenario nprio"

for ALG in "${BUF_ALGS[@]}"; do
    for LOAD in 0.4 0.6 0.8; do
        for RATE in 1 2 5; do
            FLOWFILE="$DUMP_DIR/fcts-incastrate-$TCP-$ALG-$LOAD-$BURST_SIZES-$RATE.fct"
            TORFILE="$DUMP_DIR/tor-incastrate-$TCP-$ALG-$LOAD-$BURST_SIZES-$RATE.stat"

            python3 parseData-myexp.py \
                "$FLOWFILE" "$TORFILE" \
                "$LEAF_SPINE_CAP" "$((LATENCY * 8))" \
                "$LOAD" "$BURST_SIZES" "$ALG" "$TCP" "bufrate_$RATE" "$N_PRIO" \
                "$FLOW_START" "$FLOW_END"
        done
    done
done