import numpy as np
import quakelib, sys, collections, re
from shapely.geometry import Point, LineString, MultiPoint
import matplotlib.colors as mcolor
import matplotlib.colorbar as mcolorbar
from matplotlib import pyplot as plt
from shapely.ops import linemerge, unary_union

ASEISMIC_CUT = 0.11

WORKING_DIR = '/Users/kasey/VQModels/'

UCERF3_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Geometry.dat'
UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Friction.dat'
UCERF3_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Geometry.txt'

FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
FINAL_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_'+str(ASEISMIC_CUT)+'.txt'

FINAL_FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_ReVertexed_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
FINAL_FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_ReVertexed__AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
FINAL_FINAL_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_ReVertexed__AseismicCut_'+str(ASEISMIC_CUT)+'.txt'


#ELEMENT_FILE = WORKING_DIR+'UCERF3/UCERF3_ReElemented_LineSegment.txt'

cmap = plt.get_cmap('Reds')
norm = mcolor.Normalize(vmin=-.1, vmax=1)
mag_slope = 1.0/1.1
def get_color(magnitude):
     return cmap(mag_slope * (magnitude + .1))

def dotproduct(v1, v2):
  return sum((a*b) for a, b in zip(v1, v2))

def length(v):
  return np.sqrt(dotproduct(v, v))

def angle(v1, v2):
  return np.arccos(dotproduct(v1, v2) / (length(v1) * length(v2)))
    

def strike(x,y):
    vec = np.array([x,y])
    north = np.array([0,1])
    if x < 0.0:
        return 180.0*(2*np.pi - angle(vec,north))/np.pi
    else:  
        return 180.0*angle(vec,north)/np.pi

model = quakelib.ModelWorld()
model.read_files_eqsim(FINAL_FILE_GEO, "", FINAL_FILE_FRIC, "none")

####  Create the vertex remap      
vertex_remap = quakelib.ModelRemapping()

model.create_faults_minimal()
fault_ids = model.getFaultIDs()
section_ids = model.getSectionIDs()
element_ids = model.getElementIDs()
sys.stdout.write("Read {} faults...\n".format(len(fault_ids)))
sys.stdout.write("Read {} sections...\n".format(len(section_ids)))
sys.stdout.write("Read {} elements...\n".format(len(element_ids)))

elem_to_section_map = {elem_num: model.element(elem_num).section_id() for elem_num in element_ids}
section_elements = {}
fault_sections = {}
elements_to_reverse = []

for elem,section in elem_to_section_map.items():
    try:
        section_elements[section].append(elem)
    except KeyError:
        section_elements[section] = [elem]
        
    fault_id = model.section(section).fault_id()
    try:
        if section not in fault_sections[fault_id]:
            fault_sections[fault_id].append(section)
    except KeyError:
        fault_sections[fault_id] = [section]
        
fault_mean_strikes = {}

        
### For each fault, compute the mean strike using elements of each section
for fid in fault_ids:
    section_ids = fault_sections[fid]
    fault_mean_strike = 0.0
    num_fault_elements = 0
    for sid in section_ids:
        these_element_ids = section_elements[sid]
        for element_id in these_element_ids:
            num_fault_elements += 1
            fault_mean_strike += 180*model.create_sim_element(element_id).strike()/np.pi
    fault_mean_strikes[fid] = fault_mean_strike/float(num_fault_elements)
        
        
num_secs_reversed = 0
winning_diffs = []


### For each element, check it it's strike aligns with the mean strike of the fault, if not the reverse the vertices
for ele_id in element_ids:
    element_strike = 180*model.create_sim_element(element_id).strike()/np.pi
    element_strike_reversed = (element_strike+180.0)%360.0
    fault_mean_strike       = fault_mean_strikes[model.section(model.element(ele_id).section_id()).fault_id()]
    
    fault_vs_element_strike_diff = abs(fault_mean_strike-element_strike)
    fault_vs_rev_element_strike_diff = abs(fault_mean_strike-element_strike_reversed)
    
    if (fault_vs_rev_element_strike_diff < fault_vs_element_strike_diff): 
        elements_to_reverse.append(ele_id)
        print("----- Element {} is has reversed vertices -------".format(ele_id))

print("Found that {} ({}%) elements are reversed.".format(len(elements_to_reverse),float(len(elements_to_reverse))/float(len(element_ids))))


#############
sys.exit()
#############

#############
sys.exit()
#############

#plt.hist(winning_diffs,bins=100)
#plt.show()            

model.apply_remap(vertex_remap)
        
model.write_files_eqsim(FINAL_FINAL_FILE_GEO, "", FINAL_FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FINAL_FILE_GEO, FINAL_FINAL_FILE_FRIC))


