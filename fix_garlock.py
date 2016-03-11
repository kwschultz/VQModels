import numpy as np
import re, math
from matplotlib import pyplot as plt

SECTION_FILE = 'section_strikes_SAF_fix_LA_Basin_and_Mojave_Fix.txt'
FIXED_SECTION_STRIKES = 'section_strikes_with_fixes.txt'

## Faults that have been fixed to have correct strikes:
# San Andreas, Garlock, Raymond, Hollywood, Santa Monica, Palos Verdes, 


section_strike_file = open(SECTION_FILE,'r')
new_section_strike_file = open(FIXED_SECTION_STRIKES,'w')


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
    
# These functions take a list of strikes (as a string) and return
#  a list of corrected strikes (as a string).
def add_180(string):
    ray = [ float(x)+180 for x in string.split()]
    line = ""
    for val in ray:
        line+=str(val)+" "
    return line
    
    
def subtract_180(string):
    ray = [ float(x)-180 for x in string.split()]
    line = ""
    for val in ray:
        line+=str(val)+" "
    return line
    
    
#######  UTILITIES ------------------------------------------



for line in section_strike_file:
    name, secs = line.split(" = ")
    trimmed_name = re.sub(reg,'', name)
    trimmed_and_split = trimmed_name.split("_")
    if trimmed_and_split[0] == "Garlock":
        # I know apriori that I need to subtract 180
        line_to_write = name+" = "+subtract_180(secs)+"\n"
    else:
        line_to_write = line
    
    new_section_strike_file.write(line_to_write)


section_strike_file.close()
new_section_strike_file.close()
    