#!/bin/sh

if [ $# -ne 2 ]
then
    echo "$1 <taper method>"
    echo "$2 <stress drop factor>"
    exit -1
fi

TAPER=$1
STRESS_DROP_FACTOR=$2


FRICFILE='UCERF3_EQSim_ReIndexed_LA_Basin_and_Mojave_AseismicCut_0.11_Friction.dat'
GEOFILE='UCERF3_EQSim_ReIndexed_LA_Basin_and_Mojave_AseismicCut_0.11_Geometry.dat'
OUTNAME='UCERF3_EQSim_ReIndexed_LA_Basin_and_Mojave_AseismicCut_0.11'


EDITOR_ARGS="--import_eqsim_geometry=$GEOFILE --import_eqsim_friction=$FRICFILE --taper_fault_method=$TAPER"

~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=${OUTNAME}_${TAPER}_drops${STRESS_DROP_FACTOR}.txt \
    --export_file_type=text \
    --export_file=${OUTNAME}_${TAPER}_drops${STRESS_DROP_FACTOR}.h5 \
    --export_file_type=hdf5 \
    --export_file=${OUTNAME}_${TAPER}.kml \
    --export_file_type=kml \
    --merge_duplicate_verts \
    --stress_drop_factor=${STRESS_DROP_FACTOR} 
    