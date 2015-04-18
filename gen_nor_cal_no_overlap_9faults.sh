#!/bin/sh

if [ $# -ne 1 ]
then
    echo "$0 <element size>"
    exit -1
fi

ELEM_SIZE=$1

FILE_LIST=`ls ~/vq/examples/fault_traces/ca_traces/trace_SAF-N_Mendocin.txt ~/vq/examples/fault_traces/ca_traces/trace_SAF-N_Coast_On.txt ~/vq/examples/fault_traces/ca_traces/trace_SAF-N_Coast_Of.txt ~/vq/examples/fault_traces/ca_traces/trace_C_Maacama.txt ~/vq/examples/fault_traces/ca_traces/trace_N_Maacama.txt ~/vq/examples/fault_traces/ca_traces/trace_S_Maacama.txt ~/vq/examples/fault_traces/ca_traces/trace_Bartlett_Spring.txt ~/vq/examples/fault_traces/ca_traces/trace_Berryessa.txt ~/vq/examples/fault_traces/ca_traces/trace_Collayomi.txt`

EDITOR_ARGS=
for FILE in $FILE_LIST
do
    EDITOR_ARGS="$EDITOR_ARGS--import_file=$FILE --import_file_type=trace --import_trace_element_size=$ELEM_SIZE --taper_fault_method=none "
done

~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=norcal_no_overlap_9faults_${ELEM_SIZE}.kml \
    --export_file_type=kml \
    --export_file=norcal_no_overlap_9faults_${ELEM_SIZE}.h5 \
    --export_file_type=hdf5 \
    --merge_duplicate_verts

