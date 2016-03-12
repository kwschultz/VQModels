#!/bin/sh

GEOFILE='UCERF3_ZENGBB_EQSIM_improved_only_Elsinore.dat'
FRICFILE='UCERF3_EQSIM_Elsinore_Only_Null_Friction.dat'
OUTNAME='UCERF3_VQmeshed_from_EQSIM_Elsinore_Only_no_taper'


EDITOR_ARGS="--import_eqsim_geometry=$GEOFILE --import_eqsim_friction=$FRICFILE --taper_fault_method=none"

~/vq/build/src/mesher $EDITOR_ARGS \
    --export_file=${OUTNAME}_drops0-5.txt \
    --export_file_type=text \
    --export_file=${OUTNAME}_drops0-5.h5 \
    --export_file_type=hdf5 \
    --export_file=${OUTNAME}.kml \
    --export_file_type=kml \
    --stress_drop_factor=0.5 