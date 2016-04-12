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

GEOFILE1='singleFaultFlat_trace.txt'
OUTNAME='singleFaultFlat_dip90'

EDITOR_ARGS="--import_file=$GEOFILE1 --import_file_type=trace --import_trace_element_size=$ELEM_SIZE --taper_fault_method=$TAPER"

../vq/build/src/mesher $EDITOR_ARGS \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}mElements_drops${STRESS_DROP}.txt \
    --export_file_type=text \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}mElements_drops${STRESS_DROP}.kml \
    --export_file_type=kml \
    --stress_drop_factor=${STRESS_DROP}

#    --export_eqsim_geometry=${OUTNAME}_fault_${ELEM_SIZE}.dat 
