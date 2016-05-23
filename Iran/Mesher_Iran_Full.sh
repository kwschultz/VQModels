#!/bin/sh

if [ $# -ne 3 ]
then
    echo "$0 <element size>"
    echo "$1 <taper method>"
    echo "$2 <stress drop factor>"
    exit -1
fi

ELEM_SIZE=$1
TAPER=$2
STRESS_DROP=$3

FILE_LIST=`ls Fault*/trace_*.txt`
OUTNAME='Iran_full'

EDITOR_ARGS="--taper_fault_method=$TAPER "

for FILE in $FILE_LIST
do
    EDITOR_ARGS="$EDITOR_ARGS --import_file=$FILE --import_file_type=trace --import_trace_element_size=$ELEM_SIZE "
done


 ~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}m_drops${STRESS_DROP}.txt \
    --export_file_type=text \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}m_drops${STRESS_DROP}.h5 \
    --export_file_type=hdf5 \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}m_drops${STRESS_DROP}.kml \
    --export_file_type=kml \
    --stress_drop_factor=${STRESS_DROP}

