import numpy as np
import quakelib, sys, collections, re, math
from shapely.geometry import Point, LineString, MultiPoint
import matplotlib.colors as mcolor
import matplotlib.colorbar as mcolorbar
from matplotlib import pyplot as plt

## Change this path to match your directory structure
WORKING_DIR = '/Users/kasey/VQModels/'

UCERF3_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_0.11_ReFaulted_Geometry.dat'
UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_0.11_ReFaulted_Friction.dat'

FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_0.11_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_0.11_Friction.dat'


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
for sec_name in section_strikes.keys():
    this_mean_strike = compute_mean_strike(section_strikes[sec_name])
    section_mean_strikes[sec_name] = this_mean_strike
    #print("{:60s}\t{:.2f}".format(sec_name,this_mean_strike))
    


model = quakelib.ModelWorld()
model.read_files_eqsim(UCERF3_FILE_GEO, "", UCERF3_FILE_FRIC, "none")

model.create_faults_minimal()
fault_ids = model.getFaultIDs()
sys.stdout.write("Read {} faults...\n".format(len(fault_ids)))

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

new_sec_id_map = {}
strike_diffs = []
segment_strikes = []
section_mean_xyz = {}

### Compute the mean xyz of each section from the elements
for sid in section_elements.keys():
    mean_xyz = quakelib.Vec3()
    for eid in section_elements[sid]:
        this_xyz = model.element_mean_xyz(eid)
        mean_xyz[0] += this_xyz[0]
        mean_xyz[1] += this_xyz[1]
        mean_xyz[2] += this_xyz[2]
    section_mean_xyz[sid] = mean_xyz/float(len(section_elements[sid]))

for fid in fault_ids:
    section_lines = []
    section_points_dict = {}
    sec_distances = {}
    point_distances = {}
    sec_points = []
    section_ids = fault_sections[fid]
    first_section_id = min(section_ids)
    xy_points, x_points, y_points=[],[],[]
    ######sys.stdout.write("--------- Fault {} ".format(fid))
    ######sys.stdout.write("with {} sections ----------- \n".format(len(section_ids)))
    section_strike_values = []
    for sid in section_ids:
        section_strike_values.append(section_strikes[model.section(sid).name()])
        mean_xyz = section_mean_xyz[sid]
        sec_points.append(Point(mean_xyz[0],mean_xyz[1]))
        section_points_dict[sid] = [mean_xyz[0],mean_xyz[1]]
        x_points.append(mean_xyz[0])
        y_points.append(mean_xyz[1])
    
    # Unpack the list of lists that is section_strike_values
    section_strike_values_list = [item for sublist in section_strike_values for item in sublist]
    
    # Compute the distances between all section endpoints, the max distance will give the ends of the fault
    for i in range(len(sec_points)):
        for j in range(len(sec_points)):
            point_distances[sec_points[i].distance(sec_points[j])] = [i,j]
            
    max_i, max_j = point_distances[max(point_distances.keys())]
    endpoint_i = sec_points[max_i]
    endpoint_j = sec_points[max_j]
    
    i_to_j = LineString((endpoint_i, endpoint_j) )
    j_to_i = LineString((endpoint_j, endpoint_i) )
    
    strike_j_to_i = strike(endpoint_i.x-endpoint_j.x, endpoint_i.y-endpoint_j.y)
    strike_i_to_j = strike(endpoint_j.x-endpoint_i.x, endpoint_j.y-endpoint_i.y)

    sec_mean_strike = compute_mean_strike(section_strike_values_list)
    ####sys.stdout.write("Sections {:60s} to {:60s} mean strike = {:.2f}\n".format(model.section(min(section_ids)).name(),model.section(max(section_ids)).name(),sec_mean_strike))
    
    diff_i_to_j = strike_difference_angle(sec_mean_strike,strike_i_to_j)
    diff_j_to_i = strike_difference_angle(sec_mean_strike,strike_j_to_i)
    
    if diff_i_to_j < diff_j_to_i: 
        strike_line = i_to_j
        strike_diffs.append(diff_i_to_j)
        segment_strikes.append(strike_i_to_j)
        #print("i->j better match with strike {} (angle difference {})".format(strike_i_to_j,diff_i_to_j))
    else:
        strike_line = j_to_i
        strike_diffs.append(diff_j_to_i)
        segment_strikes.append(strike_j_to_i)
        #print("j->i better match with strike {} (angle difference {})".format(strike_j_to_i,diff_j_to_i))
    
    for i,sid in enumerate(section_ids):
        dist_along = strike_line.project(Point((x_points[i],y_points[i])), normalized=True)
        sec_distances[dist_along] = sid
        #sys.stdout.write("{} at distance of {}\n".format(model.section(sid).name(), dist_along))
        #distance_color = get_color(dist_along)
        #plt.scatter([section_points_dict[sid][0]],[section_points_dict[sid][1]], s=80, color=distance_color, marker='*', zorder=10)
        
    ordered_sec_dists = collections.OrderedDict(sorted(sec_distances.items()))
        
    for i,value in enumerate(ordered_sec_dists.items()):
        dist,sid = value
        ############sys.stdout.write("{} -> {}\t{}\tat\t{}\n".format(sid,first_section_id+i,model.section(sid).name(), dist))
        # Write the ordered sections to file as well for comparing.
        #sections.write("{} -> {}\t{}\tat\t{}\n".format(sid,first_section_id+i,model.section(sid).name(), dist))
        # Be sure not to do anything if it's already in order (used for testing, 
        #       re run the script on the edited and saved fault model)
        if sid != first_section_id+i:  
            # Re-assign the section id so it's in order
            new_sec_id_map[sid] = first_section_id+i



sys.stdout.write("-=-=-=-=-=-  Remapped IDs for {:.2f}% of sections  -==-=-=-=-=-=\n".format(len(new_sec_id_map.keys())*100.0/len(model.getSectionIDs())))

####  Create the section remap      
section_remap = quakelib.ModelRemapping()

## Only apply a remap if there are sections to remap
if len(new_sec_id_map.keys()):
    for old_sec_id, new_sec_id in new_sec_id_map.items():
        section_remap.remap_section(old_sec_id, new_sec_id)

    model.apply_remap(section_remap)
    sys.stdout.write("Applied section ID remapping..")

model.write_files_eqsim(FINAL_FILE_GEO, "", FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FILE_GEO, FINAL_FILE_FRIC))


##### TESTING PLOTS below #########

#for i,line in enumerate(lines_merged):
#    x,y = line.xy
#    if i == 0: 
#        plt.plot(x,y,c='k',label='lines merged')
#    else:
#        plt.plot(x,y,c='k')
#line = MultiPoint(xy_points)
#line_convex_hull = line.convex_hull
#line_hull_exterior = line_convex_hull.exterior
#conv_x,conv_y = line_hull_exterior.xy
#plt.scatter(x_points,y_points,c='r',label='data colored by distance along strike')
#plt.plot(conv_x,conv_y,c='r',label='convex hull')
#x,y = strike_line.xy
#plt.plot(x,y,c='b',label="strike line")
#plt.legend(loc='best',fontsize=10)
#plt.savefig("shapely_objects_from_trace.png")

#x,y = strike_line.xy
#dx = x[1]-x[0]
#dy = y[1]-y[0]
###plt.plot(x,y,c='b',label="strike line, mean strike = {}".format(sec_mean_strike))
#plt.arrow(x[0], y[0], dx, dy , head_width=8, label="strike line, mean strike = {}".format(sec_mean_strike))
#plt.xlim(x[0]*0.9,x[1]*1.1)
#plt.ylim(y[0]*0.9,y[1]*1.1)
#plt.savefig("shapely_objects_from_trace_Zayante.png")                                                
##plt.hist(strike_diffs,bins=100)
##plt.savefig("strike_differences.png")

