#!/bin/sh

if [ $# -ne 1 ]
then
    echo "$0 <element size>"
    exit -1
fi

ELEM_SIZE=$1

GEOFILE='UCERF3_EQSIM_FM3_1_ZENGBB_Geometry.dat'
FRICFILE='UCERF3_EQSIM_Friction.dat'

EDITOR_ARGS="--import_eqsim_geometry=$GEOFILE --import_eqsim_friction=$FRICFILE"
#EDITOR_ARGS="--import_eqsim_geometry=$GEOFILE"

../../vq/build/src/mesher $EDITOR_ARGS \
    --export_file=UCERF3_fault_${ELEM_SIZE}.txt \
    --export_file_type=text \
    --export_file=UCERF3_fault_${ELEM_SIZE}.kml \
    --export_file_type=kml --merge_duplicate_verts
    #--export_eqsim_geometry=UCERF3_${ELEM_SIZE}_EQSIM_out.dat \
    
    
    
#     --export_file=UCERF3_fault_${ELEM_SIZE}.h5 \
#     --export_file_type=hdf5 \

