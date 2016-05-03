import numpy as np
import re, math
from matplotlib import pyplot as plt


### !!!!!! First thing!!! We want the finalized file containing strikes to be named 
## section_strikes_with_fixes.txt, so go and rename the current one to something else
SECTION_FILE = 'section_strikes_with_fixes_previous.txt'
FIXED_SECTION_STRIKES = 'section_strikes_with_fixes.txt'

## Faults that have been fixed to have correct strikes: listed in verified_and_fixed_faults.txt 
section_strike_file = open(SECTION_FILE,'r')
new_section_strike_file = open(FIXED_SECTION_STRIKES,'w')

## This implementation works for matching the unique word in the section name before the first
## underscore. I.e. "Bartlett" matches "Bartlett_Springs_2011_CFM_Subsection_0" 
UNIQUE_SECTION_SUB_NAMES = ["Hunting","Bartlett"]


reg = '\_Subsection\_[0-9]+$'  # trim the "Subsection" and underscore and the trailing number


#######  UTILITIES --------------------------------------
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
    
# These functions take a list of strikes (as a string) and return
#  a list of corrected strikes (as a string). 
def flip_strike(string):
    ray = [ (float(x)+180)%360 for x in string.split()]
    line = ""
    for val in ray:
        line+=str(val)+" "
    return line
####### ------------------------------------------




for line in section_strike_file:
    name, secs = line.split(" = ")
    trimmed_name = re.sub(reg,'', name)
    trimmed_and_split = trimmed_name.split("_")
    ##############################
    ##############################
    #### Modify the line below if you need to match, for example "name1_name2"
    ##############################
    if trimmed_and_split[0] in UNIQUE_SECTION_SUB_NAMES:
        line_to_write = name+" = "+flip_strike(secs)+"\n"
    else:
        line_to_write = line
    
    new_section_strike_file.write(line_to_write)


section_strike_file.close()
new_section_strike_file.close()
print("New strike data written to "+FIXED_SECTION_STRIKES)
    