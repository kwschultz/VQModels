import numpy as np
import quakelib
import re, sys, collections

# Change this to match your computer/file system
WORKING_DIR = '/home/jmwilson/VirtQuake/VQModels/'
ASEISMIC_CUT = 0.11
STRESS_DROP = 0.5
SAVE_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Geometry.dat'
SAVE_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Friction.dat'
SAVE_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted.txt'


# Original UCERF 3 model
UCERF3 = WORKING_DIR+'UCERF3/UCERF3_ZENGBB_EQSIM_improved.txt'
UCERF3_fric = WORKING_DIR+'UCERF3/UCERF3_EQSIM_Friction.dat'
model = quakelib.ModelWorld()
model.read_files_eqsim(UCERF3, "", UCERF3_fric, "none")
model.create_faults_minimal()
fault_ids = model.getFaultIDs()

uniq_faults = {}
uniq_faults_combined = {}
new_fault_names = {}

print("------Read "+str(len(model.getSectionIDs()))+" Sections-----")
print("------     belonging to "+str(len(fault_ids))+" Faults-----")

# Removing all instances of ..._Subsection_1.. etc
# Removing all instances of ..._2011_CFM
# Upon visual inspection, this tag means a new section was added 
#   to extend an old one, even though both are the same fault.

REGEX_strings = ['_Subsection_(\d)+', '_2011','_CFM', '_Extension', '_extension',
                '_alt_1', '_alt1', '_connector', '_No$', '_So$',
                '_North$','_South$', '_north$','_south$', '_East$', '_West$', 
                '_San_Fernando$', '_Offshore$','_Onshore$', '_rev$']
                
subsection_trimmer_reg = '\_Subsection\_[0-9]+$'
                
####  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!                
#### We may want to be less restrictive in the future, not trimming _East, _West, _South, _North.
#### For example, check out (in the Google Earth KML file) the Ortigalita North and South faults.
####   For Ortigalita, it doesn't make sense to have DAS defined along both North and South since
####   the two subsections overlap a bit.
####  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# The following faults have multiply named sections containing the following key words, 
#   its easier to match these than cut out each instance of the variant names.
special_faults = ['Calaveras','Contra_Costa','Death_Valley','Elsinore','Garlock',
                    'Kern_Canyon','San_Andreas']
sanJacinto_North = ["San_Jacinto_San_Bernardino", "San_Jacinto_San_Jacinto_Valley", "San_Jacinto_Stepovers_Combined", "San_Jacinto_Anza", "San_Jacinto_Clark"]
sanJacinto_South = ["San_Jacinto_Coyote_Creek", "San_Jacinto_Borrego", "San_Jacinto_Superstition_Mtn"]
specific_faults_to_create = ["San_Andreas_North_Branch_Mill_Creek", "Ortigalita_North", "Ortigalita_South", "South_Klamath_Lake_East", "South_Klamath_Lake_West", "San_Jacinto_Lytle_Creek"]


# Loop once over sections to determine the unique fault names and IDs
for sec_id in sorted(model.getSectionIDs()):
    sec_name = model.section(sec_id).name()
    sec_fault_id = model.section(sec_id).fault_id()
    
    trimmed_name = sec_name
    for REGEX in REGEX_strings:
        trimmed_name = re.sub(REGEX, '', trimmed_name)
        if trimmed_name in sanJacinto_North:
            trimmed_name = "San_Jacinto_North"
            break
        if trimmed_name in sanJacinto_South:
            trimmed_name = "San_Jacinto_South"
            break
        if trimmed_name in specific_faults_to_create: break
    
    uniq_faults[trimmed_name] = sec_fault_id
    
print("------Parsed "+str(len(uniq_faults.keys()))+" Uniquely Named Faults-----")
    
# Print the semi-final faults
#for key, val in uniq_faults.iteritems():
#    print('{}\t{}'.format(val, key))
    
# Loop over the sections again to reset the fault IDs to whichever unique fault matches
for sec_id in sorted(model.getSectionIDs()):
    sec_name = model.section(sec_id).name()
    
    trimmed_name = sec_name
    for REGEX in REGEX_strings:
        trimmed_name = re.sub(REGEX, '', trimmed_name)
        if trimmed_name in sanJacinto_North:
            trimmed_name = "San_Jacinto_North"
            break
        if trimmed_name in sanJacinto_South:
            trimmed_name = "San_Jacinto_South"
            break
        if trimmed_name in specific_faults_to_create: break
    
    # ===== These get set if the trimmed name contains a special fault name.
    #           If no match, then it is assumed to be a unique fault.
    new_fault_id = None
    new_fault_name = None
    
    #print("{} -> {}".format(sec_name,trimmed_name))
    
    # Try to find a special fault name that matches
    for i, spec_fault_name in enumerate(special_faults):
        if (trimmed_name.find(spec_fault_name) >= 0) and (trimmed_name not in specific_faults_to_create):        
            try:
                new_fault_id = uniq_faults_combined[spec_fault_name]
            except KeyError:
                new_fault_id = model.section(sec_id).fault_id()
                uniq_faults_combined[spec_fault_name] = new_fault_id
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

# Print the final faults
#for key, val in ordered_uniq_faults.iteritems():
#    print('{}\t{}'.format(val, key))

# Print all sections associated with each fault name
faults_byID = {}
for key, val in ordered_uniq_faults.iteritems():
    faults_byID[val] = key

fault_sec_dict = {}
for sec_id in sorted(model.getSectionIDs()):
    fname = faults_byID[model.section(sec_id).fault_id()]
    try:
        fault_sec_dict[fname].append(sec_id)
    except KeyError:
        fault_sec_dict[fname] = [sec_id]

for key, val in collections.OrderedDict(sorted(fault_sec_dict.items())).iteritems():
    print('{}\t{}\n'.format(key, val))


print("=== Combined into "+str(len(ordered_uniq_faults.keys()))+" Unique Faults ====")



# ================ Apply a lower limit to the aseismic slip ===============
for ele_id in model.getElementIDs():
    this_element = model.element(ele_id)
    if this_element.aseismic() < ASEISMIC_CUT:
        this_element.set_aseismic(0.0)

 
# ============ OUTPUT THE MODIFIED MODEL ==============
model.write_files_eqsim(SAVE_FILE_GEO, "", SAVE_FILE_FRIC)
print("New model files written: {}, {}".format(SAVE_FILE_GEO,SAVE_FILE_FRIC))


######################
#model.create_faults_minimal()  # Create the fault objects but don't worry about the area/DAS/etc.
#model.write_file_ascii(SAVE_FILE_TEXT)
#print("New model file written: {}".format(SAVE_FILE_TEXT))


    