#!/bin/sh

if [ $# -ne 1 ]
then
    echo "$0 <element size>"
    exit -1
fi

ELEM_SIZE=$1

FILE_LIST=`ls ~/vq/examples/fault_traces/ca_traces/trace_Arroyo-MRidge.txt ~/vq/examples/fault_traces/ca_traces/trace_San_Cayetano.txt ~/vq/examples/fault_traces/ca_traces/trace_Oakridge-onsho.txt ~/vq/examples/fault_traces/ca_traces/trace_Red_Mtn.txt ~/vq/examples/fault_traces/ca_traces/trace_Ventura.txt ~/vq/examples/fault_traces/ca_traces/trace_Snta_Ynez-E.txt ~/vq/examples/fault_traces/ca_traces/trace_Snta_Ynez-W.txt ~/vq/examples/fault_traces/ca_traces/trace_Simi.txt ~/vq/examples/fault_traces/ca_traces/trace_Santa_Susana.txt ~/vq/examples/fault_traces/ca_traces/trace_B_Northridge.txt`

EDITOR_ARGS=
for FILE in $FILE_LIST
do
    EDITOR_ARGS="$EDITOR_ARGS--import_file=$FILE --import_file_type=trace --import_trace_element_size=$ELEM_SIZE --taper_fault_method=none "
done

~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=so_cal_mostly_overlap_10faults_${ELEM_SIZE}.kml \
    --export_file_type=kml \
    --export_file=so_cal_mostly_overlap_10faults_${ELEM_SIZE}.h5 \
    --export_file_type=hdf5 \
    --merge_duplicate_verts

