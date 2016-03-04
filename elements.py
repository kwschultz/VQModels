import numpy as np
import quakelib, sys, collections, re, math
from shapely.geometry import Point, LineString, MultiPoint
import matplotlib.colors as mcolor
import matplotlib.colorbar as mcolorbar
from matplotlib import pyplot as plt

WORKING_DIR = '/Users/kasey/VQModels/'

##!!!!!!!!!!!!!! These models have already been through   fault_match.py   and   sectioning.py 
UCERF3_FILE_GEO =  WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_0.11_Geometry.dat'
UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_0.11_Friction.dat'

FINAL_UCERF3_FILE_GEO  = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_0.11_Geometry.dat'
FINAL_UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_0.11_Friction.dat'


# ======== READ the actual strikes from the original model =========
STRIKE_FILE = WORKING_DIR+'section_strikes.txt'
strike_file = open(STRIKE_FILE, 'r')
section_strikes = {}
for line in strike_file:
    name, secs = line.split(" = ")
    section_strikes[name] = [float(num) for num in secs.split()]
strike_file.close()


#------------- UTILITIES ---------------------------------
cmap = plt.get_cmap('Reds')
norm = mcolor.Normalize(vmin=-.1, vmax=1)
def get_color(magnitude):
    mag_slope = 1.0/1.1
    return cmap(mag_slope * (magnitude + .1))

def dotproduct(v1, v2):
  return sum((a*b) for a, b in zip(v1, v2))

def length(v):
  return math.sqrt(dotproduct(v, v))

def angle(v1, v2):
  return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))
    
def vector_from_strike(this_strike):
    strike_rad = this_strike*np.pi/180.0
    return [np.sin(strike_rad), np.cos(strike_rad)]
    
def compute_mean_strike(strike_list):
    assert not isinstance(strike_list, basestring)
    vectors = [np.array(vector_from_strike(s)) for s in strike_list]
    x,y = np.mean(vectors, axis=0)
    return strike(x,y)

def strike(x,y):
    vec = np.array([x,y])
    north = np.array([0,1])
    if x < 0.0:
        return 180.0*(2*np.pi - angle(vec,north))/np.pi
    else:  
        return 180.0*angle(vec,north)/np.pi
        
def strike_difference_angle(strike1, strike2):
    vector1 = np.array(vector_from_strike(strike1))
    vector2 = np.array(vector_from_strike(strike2))
    return 180.0*angle(vector1, vector2)/np.pi
    

## ----- Read in the target sections strikes from file -----------
## ---- These are used to align sections in order along strike -----
section_mean_strikes = dict.fromkeys(section_strikes.keys())
###### Section IDs change, section names are immutable, so index this dictionary by section name
for sec_name in section_strikes.keys():
    this_mean_strike = compute_mean_strike(section_strikes[sec_name])
    section_mean_strikes[sec_name] = this_mean_strike
    #print("{:60s}\t{:.2f}".format(sec_name,this_mean_strike))
    

model = quakelib.ModelWorld()
model.read_files_eqsim(UCERF3_FILE_GEO, "", UCERF3_FILE_FRIC, "none")


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

## Use these dictionaries to make line segments from the lowest to highest element IDs
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
section_target_strikes = {}
fault_target_strikes = {}

####  Create the element remap      
element_remap = quakelib.ModelRemapping()
        
### For each fault, compute the mean strike using elements of each section
for fid in model.getFaultIDs():
    section_ids = fault_sections[fid]
    section_strike_values = []
    for sid in section_ids:
        section_strike_values.append(section_strikes[model.section(sid).name()])
    # Unpack the list of lists that is section_strike_values
    section_strike_values_list  = [item for sublist in section_strike_values for item in sublist]
    fault_target_strikes[fid] = compute_mean_strike(section_strike_values_list)
        
        
### For each section, compute the mean strike using elements of each section
for sid in model.getSectionIDs():
    section_strike_values_list = section_strikes[model.section(sid).name()]
    section_target_strikes[sid] = compute_mean_strike(section_strike_values_list)
        
        
        
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
        
        
num_secs_reversed = 0
winning_diffs = []
large_diffs = 0
large_diff = 10
for sec_id in section_elements.keys():
    ## We only need to check those sections that are not single columns of elements.
    ## Sections that consist of single columns of elements will have been ordered by sectioning.py previously.
    if len(section_elements_by_DAS[sec_id].keys()) > 1:
        first_element_id        = section_first_elements[sec_id]
        last_element_id         = section_last_elements[sec_id]
        first_element_xyz       = model.element_mean_xyz(first_element_id)
        last_element_xyz        = model.element_mean_xyz(last_element_id)
        #### Compute the strike angle of the line segment from the lowest element ID to the highest element ID for this section
        section_strike          = strike(last_element_xyz[0]-first_element_xyz[0], last_element_xyz[1]-first_element_xyz[1])
        section_strike_reversed = strike(first_element_xyz[0]-last_element_xyz[0], first_element_xyz[1]-last_element_xyz[1])
        section_target_strike   = section_target_strikes[sec_id]
        fault_target_strike     = fault_target_strikes[model.section(sec_id).fault_id()]
        
        ### Kasey: I tested both fault and section strike here. Section strike leaves the fewest mis-classified
        target_strike = section_target_strike
        
        target_vs_section_strike_diff     = strike_difference_angle(target_strike, section_strike)
        target_vs_rev_section_strike_diff = strike_difference_angle(target_strike, section_strike_reversed)
        
        if (target_vs_rev_section_strike_diff < target_vs_section_strike_diff):
            winning_diffs.append(target_vs_rev_section_strike_diff)
            num_secs_reversed += 1.0
            #### After inspection, it looks like there are only a few outliers that have reversed element ordering with target_vs_rev_section_strike_diff > 10
            if target_vs_rev_section_strike_diff < large_diff:
                sections_to_reverse.append(sec_id)
            else:
                ##### Outliers do to highly curved sections. Only a few out of these 10 actually have reversed elements.
                large_diffs = large_diffs+1
                print("--Section {:60s} is reversed\ttarget strike = {:6.2f}\treversed section strike = {:6.2f} ({:.2f})\tsection strike = {:6.2f} ({:.2f})".format(model.section(sec_id).name(),target_strike, section_strike_reversed,target_vs_rev_section_strike_diff,section_strike,target_vs_section_strike_diff))
        
print("Found that {:.2f}% of sections have reversed element ordering.\n".format(100.0*num_secs_reversed/float(len(model.getSectionIDs()))))
print("Found {} sections with winning strike differences > {}".format(large_diffs,large_diff))


num_elements_at_DAS_indexed_by_elementID = {}

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
                num_elements_at_DAS_indexed_by_elementID[new_id] = num_elements_at_this_DAS


#plt.hist(winning_diffs,bins=100)
#plt.show()   

model.apply_remap(element_remap)


#### Not done yet, we still need to re-write DAS values correctly
for sec_id in section_elements.keys():  
    if sec_id in sections_to_reverse:
        for ele_id in sorted(section_elements[sec_id]):
            min_element_ID_in_sec    = min(section_elements[sec_id])
            num_elements_at_DAS      = num_elements_at_DAS_indexed_by_elementID[ele_id]
            element_index_within_sec = ele_id - min_element_ID_in_sec
            element_length           = model.vertex(model.element(ele_id).vertex(0)).xyz().dist( model.vertex(model.element(ele_id).vertex(2)).xyz() )
            if element_index_within_sec < num_elements_at_DAS:
                # First column of elements is easy
                model.vertex( model.element(ele_id).vertex(0) ).set_das(0.0)
                model.vertex( model.element(ele_id).vertex(1) ).set_das(0.0)
                model.vertex( model.element(ele_id).vertex(2) ).set_das(element_length)
            else:
                ## Use the just-set DAS values for the column of elements just before this element
                neighbor_id             = ele_id - num_elements_at_DAS_indexed_by_elementID[ele_id]
                DAS_before_this_element = model.vertex(model.element(neighbor_id).vertex(2)).das()
                this_DAS_min            = DAS_before_this_element + model.vertex(model.element(ele_id).vertex(0)).xyz().dist( model.vertex(model.element(neighbor_id).vertex(2)).xyz() )
                this_DAS_max            = this_DAS_min + element_length
                
                model.vertex( model.element(ele_id).vertex(0) ).set_das(this_DAS_min)
                model.vertex( model.element(ele_id).vertex(1) ).set_das(this_DAS_min)
                model.vertex( model.element(ele_id).vertex(2) ).set_das(this_DAS_max)

        
model.write_files_eqsim(FINAL_UCERF3_FILE_GEO, "", FINAL_UCERF3_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_UCERF3_FILE_GEO, FINAL_UCERF3_FILE_FRIC))


