import numpy as np
import quakelib, sys, collections, re
import scipy
from scipy.integrate import quad
from scipy.optimize import fsolve
from scipy.interpolate import UnivariateSpline
from shapely.geometry import Point, LineString, MultiPoint
from matplotlib import pyplot as plt
from shapely.ops import linemerge

#-----------  INIT -------------
WORKING_DIR = '/Users/kasey/VQModels/'
ASEISMIC_CUT = 0.11
SAVE_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
SAVE_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
SAVE_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'.txt'


# Original UCERF 3 model
UCERF3 = WORKING_DIR+'UCERF3/UCERF3_EQSIM_FM3_1_ZENGBB_Geometry.dat'
UCERF3_fric = WORKING_DIR+'UCERF3/UCERF3_EQSIM_Friction.dat'
model = quakelib.ModelWorld()
model.read_files_eqsim(UCERF3, "", UCERF3_fric, "none")


#-------------- First, Re-Faulting -------------=--=-=-=-=-=-==--=-=-=-=-=--
fault_ids = model.getFaultIDs()
uniq_faults = {}
uniq_faults_combined = {}

print("------Read "+str(len(model.getSectionIDs()))+" Sections-----")
print("------     belonging to "+str(len(fault_ids))+" Faults-----")

# Removing all instances of ..._Subsection_1.. etc
# Removing all instances of ..._2011_CFM
# Upon visual inspection, this tag means a new section was added 
#   to extend an old one, even though both are the same fault.

REGEX_strings = ['_Subsection_(\d)+', '_2011','_CFM', '_Extension', '_extension',
                '_alt_1', '_alt1', '_connector', '_Keough_Hot_Springs','_No$', '_So$',
                '_North$','_South$', '_north$','_south$', '_East$', '_West$', 
                '_San_Fernando$', '_Offshore$','_Onshore$']

# The following faults have multiply named sections containing the following key words, 
#   its easier to match these than cut out each instance of the variant names.
special_faults = ['Calaveras','Contra_Costa','Death_Valley','Elsinore','Garlock',
                    'Kern_Canyon','San_Andreas','San_Jacinto']
special_fault_ids = [602,626,246,299,341,544,295,101]
assert(len(special_fault_ids)==len(special_faults))

# Input the special faults as the first entries in the combined uniq_faults dictionary
for i, name in enumerate(special_faults):
    uniq_faults_combined[name] = special_fault_ids[i]

# Loop once over sections to determine the unique fault names and IDs
for sec_id in sorted(model.getSectionIDs()):
    sec_name = model.section(sec_id).name()
    sec_fault_id = model.section(sec_id).fault_id()
    
    trimmed_name = sec_name
    for REGEX in REGEX_strings:
        trimmed_name = re.sub(REGEX, '', trimmed_name)
    
    uniq_faults[trimmed_name] = sec_fault_id
    
print("------Parsed "+str(len(uniq_faults.keys()))+" Uniquely Named Faults-----")

# Loop over the sections again to reset the fault IDs to whichever unique fault matches
for sec_id in sorted(model.getSectionIDs()):
    sec_name = model.section(sec_id).name()
    
    trimmed_name = sec_name
    for REGEX in REGEX_strings:
        trimmed_name = re.sub(REGEX, '', trimmed_name)
    
    # ===== These get set if the trimmed name contains a special fault name.
    #           If no match, then it is assumed to be a unique fault.
    new_fault_id = None
    new_fault_name = None
    
    # Try to find a special fault name that matches
    for i, spec_fault_name in enumerate(special_faults):
        if trimmed_name.find(spec_fault_name) >= 0:
            new_fault_id = special_fault_ids[i]
            new_fault_name = spec_fault_name
            break
    
    # If no match to special faults, then process it as a uniquely named fault.
    # Try to grab an already-processed fault_id of a previous fault with the 
    #     same unique fault name.
    if new_fault_id is None:
        new_fault_name = trimmed_name
        try:
            new_fault_id = uniq_faults_combined[trimmed_name]
            
        except KeyError:
            new_fault_id = model.section(sec_id).fault_id()
            uniq_faults_combined[new_fault_name] = new_fault_id
            
    # Now that the fault has been matched to a unique one, reset fault_id
    if new_fault_id is None:
        raise "Error: Did not match any unique faults."
    else:
        model.section(sec_id).set_fault_id(new_fault_id)
    

# Order the faults alphabetically
ordered_uniq_faults = collections.OrderedDict(sorted(uniq_faults_combined.items()))
print("=== Combined into "+str(len(ordered_uniq_faults.keys()))+" Unique Faults ====")


# ================ Apply a lower limit to the aseismic slip ===============
for ele_id in model.getElementIDs():
    this_element = model.element(ele_id)
    if this_element.aseismic() < ASEISMIC_CUT:
        this_element.set_aseismic(0.0)
        
print("=== Applied Aseismic Fraction Cut at "+str(ASEISMIC_CUT )+" ====")


##### SAVE RE-FAULTED MODEL

#model.write_files_eqsim(SAVE_FILE_GEO, "", SAVE_FILE_FRIC)
#print("Re-faulted files written: {}, {}".format(SAVE_FILE_GEO,SAVE_FILE_FRIC))

# Creating a new model world for the modified faults
#new_model = quakelib.ModelWorld()
#new_model.read_files_eqsim(SAVE_FILE_GEO, "", SAVE_FILE_FRIC, "none")


model.create_faults_minimal()  # Create the fault objects but don't worry about the area/DAS/etc.
#-------------- Next, Re-Sectioning -------------=--=-=-=-=-=-==--=-=-=-=-=--
fault_ids = model.getFaultIDs()
#fault_ids = ordered_uniq_faults.values()
sys.stdout.write("Found {} faults to Re-Section...\n".format(len(fault_ids)))


elem_to_section_map = {elem_num: model.element(elem_num).section_id() for elem_num in model.getElementIDs()}
section_elements = {}
fault_sections = {}
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

# -----------      ----------
for fid in fault_ids:
    section_lines = []
    sec_distances = {}
    section_ids = fault_sections[fid]
    reg = '\_[0-9]+$'  # trim the underscore and the trailing number
    section_names = [ re.sub(reg,'',model.section(sid).name()) for sid in section_ids ]
    num_uniq_sections = len(np.unique(section_names))
    
    # We only have to apply the fix if there are multiple unique sections
    if num_uniq_sections > 1:
        first_section_id = section_ids[0]
        xy_points, x_points, y_points=[],[],[]
        sys.stdout.write("--------- Fault {} ".format(fid))
        sys.stdout.write("with {} sections ----------- \n".format(len(section_ids)))
        for sid in section_ids:
            element_id = section_first_elements[sid]
            element_xyz = model.vertex(model.element(element_id).vertex(0)).xyz()/1000.0
            element_xyz_end = model.vertex(model.element(section_last_elements[sid]).vertex(0)).xyz()/1000.0
            xy_points.append((element_xyz[0],element_xyz[1]))
            x_points.append(element_xyz[0])
            y_points.append(element_xyz[1])
            # Make a line segment out of the first and last elements in a section
            section_lines.append( ( (element_xyz[0],element_xyz[1]), (element_xyz_end[0],element_xyz_end[1])  ) )
            
        lines_merged = linemerge(section_lines)

        for i,sid in enumerate(section_ids):
            dist_along = lines_merged.project(Point((x_points[i],y_points[i])), normalized=True)
            #sys.stdout.write("{} at distance of {}\n".format(model.section(sid).name(), dist_along))
            sec_distances[dist_along] = sid
            
        ordered_sec_dists = collections.OrderedDict(sorted(sec_distances.items()))
            
        for i,value in enumerate(ordered_sec_dists.items()):
            dist,sid = value
            sys.stdout.write("{} -> {}\t{}\tat\t{}\n".format(sid,first_section_id+i,model.section(sid).name(), dist))
            # Re-assign the section id so it's in order
            model.section(sid).set_id(first_section_id+i)


# ============ OUTPUT THE MODIFIED MODEL ==============
#model.write_file_ascii(SAVE_FILE_TEXT)
#print("New model file written: {}".format(SAVE_FILE_TEXT))
model.write_files_eqsim(FINAL_FILE_GEO, "", FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FILE_GEO, FINAL_FILE_FRIC))





