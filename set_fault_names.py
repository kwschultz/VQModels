#==============================================================================
# For application to UCERF3 text model file, after fixing_ucerf3.readme and mesher has been run
#==============================================================================

import numpy as np
import quakelib
import re, sys, collections, pickle

# Change this to match your computer/file system
WORKING_DIR = '/home/jmwilson/VirtQuake/VQModels/'

TAPER_METHOD = "taper"

ELE_SIZE = 3000

faultIDfile = open(WORKING_DIR+"faultIDs.p", "r")
faults_byID = pickle.load(faultIDfile)
faultIDfile.close()

OPEN_FILE = WORKING_DIR+'UCERF3/UCERF3_VQmeshed_from_EQSIM_ReIndexed_AseismicCut_0-11_taper_drops0.5.h5'
SAVE_FILE = WORKING_DIR+'UCERF3/UCERF3_VQmeshed_from_EQSIM_ReIndexed_ReNamed_AseismicCut_0-11_taper_drops0.5'


model = quakelib.ModelWorld()

model.read_file_hdf5(OPEN_FILE)


faultIDs = model.getFaultIDs()

for faultID in faultIDs:
    model.fault(faultID).set_name(faults_byID[faultID])

model.write_file_ascii(SAVE_FILE+'.txt')
model.write_file_hdf5(SAVE_FILE+'.h5')
model.write_file_kml(SAVE_FILE+'.kml')