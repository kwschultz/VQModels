import numpy as np
import quakelib, sys, collections, re, math
from shapely.geometry import Point, LineString, MultiPoint
import matplotlib.colors as mcolor
import matplotlib.colorbar as mcolorbar
from matplotlib import pyplot as plt

ASEISMIC_CUT = 0.11

WORKING_DIR = '/Users/kasey/VQModels/'


###!!! This vertex remapper is applied only after using   fault_match.py then sectioning.py then elements.py
UCERF3_FILE_GEO  = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_0.11_Geometry.dat'
UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_AseismicCut_0.11_Friction.dat'

FINAL_FILE_GEO  = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_ReVertexed_AseismicCut_0.11_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_ReElemented_ReVertexed_AseismicCut_0.11_Friction.dat'


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
element_ids = model.getElementIDs()
sys.stdout.write("Read {} faults...\n".format(len(fault_ids)))
sys.stdout.write("Read {} sections...\n".format(len(section_ids)))
sys.stdout.write("Read {} elements...\n".format(len(element_ids)))

# Get the Lat/Lon/Depth object for model basis
model_base = model.get_base()
base_lld = quakelib.LatLonDepth(model_base[0], model_base[1], 0.0)

elem_to_section_map = {elem_num: model.element(elem_num).section_id() for elem_num in model.getElementIDs()}
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
        
section_target_strikes = {}

### For each section, compute the mean strike using elements of each section
for sid in model.getSectionIDs():
    section_strike_values_list = section_strikes[model.section(sid).name()]
    section_target_strikes[sid] = compute_mean_strike(section_strike_values_list)
        
        
num_secs_reversed = 0
winning_diffs = []
all_diffs = []


### For each element, check it it's strike aligns with the mean strike of the fault, if not the reverse the vertices
for ele_id in model.getElementIDs():
    element_strike          = 180*model.create_sim_element(ele_id).strike()/np.pi
    element_strike_reversed = (element_strike+180.0)%360.0
    section_mean_strike     = section_mean_strikes[model.section(model.element(ele_id).section_id()).name()]
    
    target_vs_element_strike_diff     = strike_difference_angle(section_mean_strike, element_strike)
    target_vs_rev_element_strike_diff = strike_difference_angle(section_mean_strike, element_strike_reversed)
    
    all_diffs.append(target_vs_element_strike_diff)
    
    ## If the conjugate angle of the element strike is a better match, we need to change vertices
    if (target_vs_rev_element_strike_diff < target_vs_element_strike_diff): 
        elements_to_reverse.append(ele_id)
        winning_diffs.append(target_vs_rev_element_strike_diff)
        element_minus_one_strike = 180*model.create_sim_element(ele_id-1).strike()/np.pi
        element_plus_one_strike = 180*model.create_sim_element(ele_id+1).strike()/np.pi
        #print("----- Element {} in Section {} has reversed vertices -------".format(ele_id, model.section(model.element(ele_id).section_id()).name()))
        print("Element {}\tMean section strike {:.2f}\tElement Strike\Rake {:.2f}  {:.2f}\tElement-1 Strike\Rake {:.2f}   {:.2f}\t\tElement+1 Strike\Rake {:.2f}  {:.2f}".format(ele_id, section_mean_strike, element_strike, model.element(ele_id).rake(), element_minus_one_strike, model.element(ele_id-1).rake(), element_plus_one_strike, model.element(ele_id+1).rake()))
        #v0 = model.vertex(model.element(ele_id).vertex(0)).xyz()/1000.0
        #v1 = model.vertex(model.element(ele_id).vertex(1)).xyz()/1000.0
        #v2 = model.vertex(model.element(ele_id).vertex(2)).xyz()/1000.0
        #print("v0 = {:.2f}, {:.2f}, {:.2f}".format(v0[0],v0[1],v0[2]))
        #print("v1 = {:.2f}, {:.2f}, {:.2f}".format(v1[0],v1[1],v1[2]))
        #print("v2 = {:.2f}, {:.2f}, {:.2f}".format(v2[0],v2[1],v2[2]))
        
        # To remap vertex ids, switch vertex0 <-> vertex2 IDs within the element (the actual Vertex IDs don't matter), 
        #   and change the coordinates of vertex1 to be the coords of the implicit (4th) vertex.
        implicit = model.create_sim_element(ele_id).implicit_vert()
        model.vertex(model.element(ele_id).vertex(1)).set_xyz(implicit, base_lld)

        new_v0_id      = model.element(ele_id).vertex(2)
        new_v2_id      = model.element(ele_id).vertex(0)
        
        model.element(ele_id).set_vertex(0, new_v0_id)
        model.element(ele_id).set_vertex(2, new_v2_id)
        
    
print("Found that {} ({:.2f}%) elements have vertices reversed.".format(len(elements_to_reverse),float(100*len(elements_to_reverse))/float(len(element_ids))))

#plt.hist(all_diffs,bins=100, log=True)
#plt.savefig("vertex_remapper_strikeMatchDiffs.png")   
        
        
model.write_files_eqsim(FINAL_FILE_GEO, "", FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FILE_GEO, FINAL_FILE_FRIC))


