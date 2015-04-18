#!/bin/sh

if [ $# -ne 2 ]
then
    echo "$0 <element size>"
    echo "$1 <taper method>"
    exit -1
fi

ELEM_SIZE=$1
TAPER=$2

GEOFILE1='single_thrust_dip45_switch.txt'
OUTNAME='thrust_dip45_switch_10x10km'

EDITOR_ARGS="--import_file=$GEOFILE1 --import_file_type=trace --import_trace_element_size=$ELEM_SIZE --taper_fault_method=$TAPER"

../vq/build/src/mesher $EDITOR_ARGS \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}mElements.txt \
    --export_file_type=text \
    --export_file=${OUTNAME}_fault_${ELEM_SIZE}mElements.kml \
    --export_file_type=kml \
    --merge_duplicate_verts

#    --export_eqsim_geometry=${OUTNAME}_fault_${ELEM_SIZE}.dat 
