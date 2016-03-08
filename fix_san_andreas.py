import numpy as np
import re, math
from matplotlib import pyplot as plt

SECTION_FILE = 'section_strikes.txt'
FIXED_SECTION_STRIKES = 'section_strikes_SAF_fix.txt'

section_strike_file = open(SECTION_FILE,'r')
new_section_strike_file = open(FIXED_SECTION_STRIKES,'w')

corrected_section_strikes = {}

reg = '\_Subsection\_[0-9]+$'  # trim the "Subsection" and underscore and the trailing number


#######  UTILITIES ------------------------------------------
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
#######  UTILITIES ------------------------------------------



for line in section_strike_file:
    name, secs = line.split(" = ")
    corrected_section_strikes[name] = []
    trimmed_name = re.sub(reg,'', name)
    section_strike_floats = [float(x) for x in secs.split()]
    #print("{:60s} = {}".format(name,section_strike_floats))
    trimmed_and_split = trimmed_name.split("_")
    if len(trimmed_and_split) > 1:
        ## Detected a San Andreas section
        if trimmed_and_split[1] == "Andreas":
            ### Enforce that SAF strikes should be bigger than 180 degrees
            old_mean_strike = compute_mean_strike(section_strike_floats)
            if old_mean_strike < 180.0:
                section_strike_floats = [x+180.0 for x in section_strike_floats]
                #print("{:60s} mean strike {:.3f} -> {:.3f}".format(name,old_mean_strike,compute_mean_strike(section_strike_floats)))
    line_to_write = name+" = "
    for strike_float in section_strike_floats:
        line_to_write += str(strike_float)+" "
    new_section_strike_file.write(line_to_write+"\n")


section_strike_file.close()
new_section_strike_file.close()
    