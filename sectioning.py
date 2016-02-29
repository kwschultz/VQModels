import numpy as np
import quakelib, sys, collections, re, math
from shapely.geometry import Point, LineString, MultiPoint
import matplotlib.colors as mcolor
import matplotlib.colorbar as mcolorbar
from matplotlib import pyplot as plt
from shapely.ops import linemerge, unary_union

WORKING_DIR = '/Users/kasey/VQModels/'

UCERF3_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_0.11_ReFaulted_Geometry.dat'
UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_0.11_ReFaulted_Friction.dat'

FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_0.11_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_0.11_Friction.dat'

#SECTION_FILE = WORKING_DIR+'UCERF3/UCERF3_ReSectioned_SectionList_LineSegment.txt'

cmap = plt.get_cmap('Reds')
norm = mcolor.Normalize(vmin=-.1, vmax=1)
mag_slope = 1.0/1.1
def get_color(magnitude):
     return cmap(mag_slope * (magnitude + .1))

def dotproduct(v1, v2):
  return sum((a*b) for a, b in zip(v1, v2))

def length(v):
  return math.sqrt(dotproduct(v, v))

def angle(v1, v2):
  return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))
    

def strike(x,y):
    vec = np.array([x,y])
    north = np.array([0,1])
    if x < 0.0:
        return 180.0*(2*np.pi - angle(vec,north))/np.pi
    else:  
        return 180.0*angle(vec,north)/np.pi

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
section_first_elements = {sec:min(elements) for sec,elements in section_elements.items()}
section_last_elements = {sec:max(elements) for sec,elements in section_elements.items()}

new_sec_id_map = {}


#sections = open(SECTION_FILE,'w')
for fid in fault_ids:
    section_lines = []
    section_points_dict = {}
    sec_distances = {}
    point_distances = {}
    sec_mean_strike = 0.0
    sec_points = []
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
            sec_mean_strike += 180*model.create_sim_element(section_first_elements[sid]).strike()/(np.pi*len(section_ids))
            # Make a line segment out of the first and last elements in a section
            #   Below is for LineMerge
            section_lines.append( ( (element_xyz[0],element_xyz[1]), (element_xyz_end[0],element_xyz_end[1])  ) )
            #   Below is for unary_union
            #section_lines.append( LineString( ((element_xyz[0],element_xyz[1]), (element_xyz_end[0],element_xyz_end[1])) ) )
            sec_points.append(Point(element_xyz[0],element_xyz[1]))
            sec_points.append(Point(element_xyz_end[0],element_xyz_end[1]))
            section_points_dict[sid] = [element_xyz[0],element_xyz[1]]
            
        lines_merged = linemerge(section_lines)
        #lines_merged = unary_union(section_lines)
        
        # Compute the distances between all section endpoints, the max distance will give the ends of the fault
        for i in range(len(sec_points)):
            for j in range(len(sec_points)):
                point_distances[sec_points[i].distance(sec_points[j])] = [i,j]
                
        max_i, max_j = point_distances[max(point_distances.keys())]
        #print("Found max distance of {}".format(max(point_distances.keys())))
        endpoint_i = sec_points[max_i]
        endpoint_j = sec_points[max_j]
        
        i_to_j = LineString((endpoint_i, endpoint_j) )
        j_to_i = LineString((endpoint_j, endpoint_i) )
        
        strike_i_to_j = strike(endpoint_j.x-endpoint_i.x, endpoint_j.y-endpoint_i.y)
        strike_j_to_i = strike(endpoint_i.x-endpoint_j.x, endpoint_i.y-endpoint_j.y)
        
        diff_i_to_j = abs(sec_mean_strike-strike_i_to_j)
        diff_j_to_i = abs(sec_mean_strike-strike_j_to_i)
    
        #print("Mean strike {}".format(sec_mean_strike))
        #print("i->j strike {}".format(strike_i_to_j))
        #print("j->i strike {}".format(strike_j_to_i))
        
        if diff_i_to_j < diff_j_to_i: 
            strike_line = i_to_j
            #print("i->j better match")
        else:
            strike_line = j_to_i
            #print("j->i better match")
        
        
        for i,sid in enumerate(section_ids):
            #dist_along = lines_merged.project(Point((x_points[i],y_points[i])), normalized=True)
            dist_along = strike_line.project(Point((x_points[i],y_points[i])), normalized=True)
            #sys.stdout.write("{} at distance of {}\n".format(model.section(sid).name(), dist_along))
            sec_distances[dist_along] = sid
            #distance_color = get_color(dist_along)
            #plt.scatter([section_points_dict[sid][0]],[section_points_dict[sid][1]], s=80, color=distance_color, marker='*', zorder=10)
            
        ordered_sec_dists = collections.OrderedDict(sorted(sec_distances.items()))
            
        for i,value in enumerate(ordered_sec_dists.items()):
            dist,sid = value
            sys.stdout.write("{} -> {}\t{}\tat\t{}\n".format(sid,first_section_id+i,model.section(sid).name(), dist))
            # Write the ordered sections to file as well for comparing.
            #sections.write("{} -> {}\t{}\tat\t{}\n".format(sid,first_section_id+i,model.section(sid).name(), dist))
            # Be sure not to do anything if it's already in order (used for testing, 
            #       re run the script on the edited and saved fault model)
            if sid != first_section_id+i:  
                # Re-assign the section id so it's in order
                new_sec_id_map[sid] = first_section_id+i
            

####  Create the section remap      
section_remap = quakelib.ModelRemapping()

if len(new_sec_id_map.keys()):
    for old_sec_id, new_sec_id in new_sec_id_map.items():
        section_remap.remap_section(old_sec_id, new_sec_id)

    model.apply_remap(section_remap)
    sys.stdout.write("Applied section ID remapping..")

sys.stdout.write("-=-=-=-=-=-  Remapped IDs for {:.2f}% of sections  -==-=-=-=-=-=\n".format(len(new_sec_id_map.keys())*100.0/len(model.getSectionIDs())))


#model.create_faults_minimal()  # Create the fault objects but don't worry about the area/DAS/etc.
model.write_files_eqsim(FINAL_FILE_GEO, "", FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FILE_GEO, FINAL_FILE_FRIC))

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

