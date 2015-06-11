#!/bin/sh

#if [ $# -ne 1 ]
#then
#    echo "$0 <element size>"
#    exit -1
#fi

#ELEM_SIZE=$1
#KM=$(($ELEM_SIZE / 1000))

GEOFILE='ALLCAL2_1-7-11_no-creep/ALLCAL2_1-7-11_no-creep_Geometry.dat'
FRICFILE='ALLCAL2_1-7-11_no-creep/ALLCAL2_1-7-11_no-creep_Friction.dat'

EDITOR_ARGS="--import_eqsim_geometry=$GEOFILE --import_eqsim_friction=$FRICFILE"

~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=ALLCAL2_VQmeshed_3km.txt \
    --export_file_type=text \
    --export_file=ALLCAL2_VQmeshed_3km.h5 \
    --export_file_type=hdf5 \
    --export_file=ALLCAL2_VQmeshed_3km.kml \
    --export_file_type=kml \
    --merge_duplicate_verts \
    --delete_unused 

