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

FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
FINAL_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'.txt'

FINAL_FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
FINAL_FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
FINAL_FINAL_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_'+str(ASEISMIC_CUT)+'.txt'


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


model.create_faults_minimal()
fault_ids = model.getFaultIDs()
section_ids = model.getSectionIDs()
sys.stdout.write("Read {} faults...\n".format(len(fault_ids)))
sys.stdout.write("Read {} sections...\n".format(len(section_ids)))

elem_to_section_map = {elem_num: model.element(elem_num).section_id() for elem_num in model.getElementIDs()}
section_elements = {}
fault_sections = {}
sections_to_reverse = []

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
        
        

section_first_elements = {sec:min(elements) for sec,elements in section_elements.items()}
section_last_elements = {sec:max(elements) for sec,elements in section_elements.items()}

## For each section, compile the groups of elements at each DAS
section_elements_by_DAS = dict.fromkeys(section_ids)
for sec_id in section_elements.keys():
    section_elements_by_DAS[sec_id] = {}
    sec_elements = section_elements[sec_id]
    for element_id in sec_elements:
        this_das = model.element_min_das(element_id)
        try:
            section_elements_by_DAS[sec_id][this_das].append(element_id)
        except KeyError:
            section_elements_by_DAS[sec_id][this_das] = [element_id]
        

new_sec_id_map = {}
fault_mean_strikes = {}

####  Create the element remap      
element_remap = quakelib.ModelRemapping()
        
        
### For each fault, compute the mean strike using elements of each section
for fid in fault_ids:
    section_ids = fault_sections[fid]
    fault_mean_strike = 0.0
    num_fault_elements = 0
    for sid in section_ids:
        element_ids = section_elements[sid]
        for element_id in element_ids:
            num_fault_elements += 1
            fault_mean_strike += 180*model.create_sim_element(element_id).strike()/np.pi
    fault_mean_strikes[fid] = fault_mean_strike/float(num_fault_elements)
        
        
num_secs_reversed = 0
winning_diffs = []
for sec_id in section_elements.keys():
    current_element_order   = sorted(section_elements[sec_id])
    reversed_element_order  = sorted(section_elements[sec_id], reverse=1)
    first_element_id        = min(section_elements[sec_id])
    last_element_id         = max(section_elements[sec_id])
    first_element_xyz       = model.vertex(model.element(first_element_id).vertex(0)).xyz()/1000.0
    last_element_xyz        = model.vertex(model.element(last_element_id).vertex(0)).xyz()/1000.0
    section_strike_reversed = strike(first_element_xyz[0]-last_element_xyz[0], first_element_xyz[1]-last_element_xyz[1])
    section_strike          = strike(last_element_xyz[0]-first_element_xyz[0], last_element_xyz[1]-first_element_xyz[1])
    fault_mean_strike       = fault_mean_strikes[model.section(sec_id).fault_id()]
    
    fault_vs_section_strike_diff = abs(fault_mean_strike-section_strike)
    fault_vs_rev_section_strike_diff = abs(fault_mean_strike-section_strike_reversed)
    
    if (fault_vs_rev_section_strike_diff < fault_vs_section_strike_diff): 
        #print("--Section {:45s} is reversed\tfault strike = {:6.2f}\tsection strike = {:6.2f} ({:.2f})\treversed section strike = {:6.2f} ({:.2f})".format(model.section(sec_id).name(),fault_mean_strike,section_strike,fault_vs_section_strike_diff, section_strike_reversed,fault_vs_rev_section_strike_diff))
        winning_diffs.append(fault_vs_rev_section_strike_diff)
        num_secs_reversed += 1.0
        sections_to_reverse.append(sec_id)
        print("------- {} -------".format(model.section(sec_id).name()))
        
print("Found that {:.2f}% of sections are reversed.".format(num_secs_reversed/float(len(section_ids))))



### Go through the section elements grouped by DAS and create a new dictionary 
###   indexed by the minimum element id at each DAS subtracted by the sections minimum element id.
### This computes the current index of each DAS group. In the last loop over sections, we will reverse this index
###   for those sections whose element IDs need to be reversed.
section_elements_by_DAS_index = dict.fromkeys(section_elements_by_DAS.keys(), {})
for sec_id in section_elements_by_DAS.keys():
    sec_first_element_id = section_first_elements[sec_id]
    num_DAS_groups       = len(section_elements_by_DAS[sec_id].keys())
    #print("Section {} has {} DAS groups...".format(sec_id,num_DAS_groups))
    section_elements_by_DAS_index[sec_id] = {}

    for DAS in section_elements_by_DAS[sec_id].keys():
        ## Assuming here that the number of elements at each DAS is constant across a section.
        num_elements_at_this_DAS = len(section_elements_by_DAS[sec_id][DAS])
        first_element_at_this_DAS = int(min(section_elements_by_DAS[sec_id][DAS]))
        this_DAS_index = int(first_element_at_this_DAS - sec_first_element_id)/int(num_elements_at_this_DAS) 
        #print("At DAS = {} there are {} elements...".format(DAS,num_elements_at_this_DAS))
        section_elements_by_DAS_index[sec_id][this_DAS_index] = section_elements_by_DAS[sec_id][DAS]
        
                
    #print('{}\n'.format(section_elements_by_DAS_index[sec_id]))



### Go through the section elements grouped by DAS index and determine the new element numbers
for sec_id in section_elements_by_DAS_index.keys():
    if sec_id in sections_to_reverse:
        sec_first_element_id = section_first_elements[sec_id]
        num_DAS_groups = len(section_elements_by_DAS_index[sec_id].keys())
        for DAS_index in section_elements_by_DAS_index[sec_id].keys():
            num_elements_at_this_DAS = len(section_elements_by_DAS_index[sec_id][DAS_index])
            new_DAS_index = (num_DAS_groups-1) - DAS_index  # This reverses the order of the DAS_index
            for i,ele_id in enumerate(section_elements_by_DAS_index[sec_id][DAS_index]):
                new_id = sec_first_element_id + (new_DAS_index*num_elements_at_this_DAS) + i
                element_remap.remap_element(ele_id, new_id)



#############
#sys.exit()
#############

#plt.hist(winning_diffs,bins=100)
#plt.show()            

model.apply_remap(element_remap)
        
model.write_files_eqsim(FINAL_FINAL_FILE_GEO, "", FINAL_FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FINAL_FILE_GEO, FINAL_FINAL_FILE_FRIC))


