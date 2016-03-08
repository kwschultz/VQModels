#!/bin/sh

if [ $# -ne 2 ]
then
    echo "$1 <taper method>"
    echo "$2 <stress drop factor>"
    exit -1
fi

#ELEM_SIZE=$1
#KM=$(($ELEM_SIZE / 1000))

TAPER=$1
GEOFILE='ALLCAL2_1-7-11_no-creep/ALLCAL2_1-7-11_no-creep_Geometry.dat'
FRICFILE='ALLCAL2_1-7-11_no-creep/ALLCAL2_1-7-11_no-creep_Friction.dat'
OUTNAME='UCERF2_VQmeshed_3km_preTapered_noCreep'
STRESS_DROP_FACTOR=$2

EDITOR_ARGS="--import_eqsim_geometry=$GEOFILE --import_eqsim_friction=$FRICFILE"

~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=${OUTNAME}_${TAPER}_drops${STRESS_DROP_FACTOR}.txt \
    --export_file_type=text \
    --export_file=${OUTNAME}_${TAPER}_drops${STRESS_DROP_FACTOR}.h5 \
    --export_file_type=hdf5 \
    --export_file=${OUTNAME}_${TAPER}.kml \
    --export_file_type=kml \
    --taper_fault_method=${TAPER} \
    --stress_drop_factor=${STRESS_DROP_FACTOR}  \

