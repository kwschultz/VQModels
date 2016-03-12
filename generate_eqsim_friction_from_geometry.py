######## Kasey Schultz
## This script will generate a meaningless but necessary matching EQSim friction file
##   for each element in the provided EQSim geometry file. This Friction file is required
##   for input into the mesher, but I'm using values of 0.0 for the stress drops since we
##   will be calculating them with Virtual Quake.

import numpy as np

FILE = 'UCERF3/UCERF3_EQSim_ReIndexed_LA_Basin_and_Mojave_AseismicCut_0.11_Geometry.dat'
OUTFILE = FILE.split("Geometry.dat")[0]+"Friction.dat"


model_file = open(FILE,'r')
out_file = open(OUTFILE,'w')

vertex_ids = []
element_ids = []
section_ids = []
fault_ids = []

for line in model_file:
    split_line = line.split()
    if len(split_line)>1:
        if split_line[0]=="201":
            section_ids.append(int(split_line[1]))
            fault_ids.append(int(split_line[-1]))
        elif split_line[0]=="202":
            vertex_ids.append(int(split_line[1]))
        elif split_line[0]=="204":
            element_ids.append(int(split_line[1]))
        
print("Found {} faults".format(len(np.unique(fault_ids))))
print("Found {} sections".format(len(np.unique(section_ids))))
print("Found {} elements".format(len(np.unique(element_ids))))       
print("Found {} vertices".format(len(np.unique(vertex_ids))))

header = "101 EQSim_Input_Friction_by_hand_Schultz\n111 Fault friction from UCERF3\n102 End_Metadata\n120 200 summary 4    Record 200: Fault friction summary\n121 1 n_element 1    Field 1: Total number of elements in the file\n121 2 elastic_flag 1    Field 2: 1 if elastic parameters (record 201) are included, 0 if not\n121 3 strength_flag 1    Field 3: 1 if fault strength (record 202) is included, 0 if not\n121 4 rate_state_flag 1    Field 4: 1 if rate-state parameters (record 203) are included, 0 if not\n120 201 elastic_param 2    Record 201: Elastic parameters\n121 1 lame_lambda 2    Field 1: Lame modulus lambda (Pascal)\n121 2 lame_mu 2    Field 2: Lame modulus mu, also known as the shear modulus (Pascal)\n120 202 fault_strength 3    Record 202: Fault strength\n121 1 index 1    Field 1: Element index number (consecutive integers, starting with 1)\n121 2 static_strength 2    Field 2: Element static yield strength (Pascal)\n121 3 dynamic_strength 2    Field 3: Element dynamic sliding strength (Pascal)\n120 203 rate_state 6    Record 203: Rate-state parameters\n121 1 index 1    Field 1: Element index number (consecutive integers, starting with 1)\n121 2 A 2    Field 2: Element rate-state parameter A\n121 3 B 2    Field 3: Element rate-state parameter B\n121 4 L 2    Field 4: Element rate-state characteristic distance L (meters)\n121 5 f0 2    Field 5: Element rate-state friction coefficient f0\n121 6 V0 2    Field 6: Element rate-state reference velocity V0 (meters/second)\n103 End_Descriptor\n"

summary_line = "200 {} 1 1 0\n".format(len(element_ids))
lame_parameters_line = "201  3.200000e+010  3.000000e+010\n"


out_file.write(header)
out_file.write(summary_line)
out_file.write(lame_parameters_line)

for element_id in element_ids:
    out_file.write("202 {} 0.000000e+000 0.000000e+000\n".format(element_id))

out_file.write("999 End\n")



out_file.close()
model_file.close()
print("EQSim friction written to: {}".format(OUTFILE))
    




