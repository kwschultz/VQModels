import numpy as np
import quakelib, sys, collections
import scipy
from scipy.integrate import quad
from scipy.optimize import fsolve
from scipy.interpolate import UnivariateSpline
from shapely.geometry import Point, LineString, MultiPoint
from matplotlib import pyplot as plt
from shapely.ops import linemerge

WORKING_DIR = '/Users/kasey/VQModels/'
UCERF3 = WORKING_DIR+'UCERF3/UCERF3_VQmeshed_from_EQSIM_AseismicCut_0-11_ReFaulted_taper_renorm_drops0-7.txt'
model = quakelib.ModelWorld()
model.read_file_ascii(UCERF3)

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

section_lines = []

#for fid in fault_sections.keys():
for fid in [341]:
    section_ids = fault_sections[fid]
    first_section_id = section_ids[0]  #!!!!!!!!!!!!!!!!
    xy_points, x_points, y_points=[],[],[]
    min_x,max_x,min_y,max_y = np.inf, -np.inf, np.inf, -np.inf
    sys.stdout.write("Fault {}..".format(fid))
    sys.stdout.write("with {} sections..".format(len(section_ids)))
    for sid in section_ids:
        element_id = section_first_elements[sid]
        element_xyz = model.vertex(model.element(element_id).vertex(0)).xyz()/1000.0
        element_xyz_end = model.vertex(model.element(section_last_elements[sid]).vertex(0)).xyz()/1000.0
        xy_points.append((element_xyz[0],element_xyz[1]))
        x_points.append(element_xyz[0])
        y_points.append(element_xyz[1])
        section_lines.append( ( (element_xyz[0],element_xyz[1]), (element_xyz_end[0],element_xyz_end[1])  ) )
        
line = MultiPoint(xy_points)
line_convex_hull = line.convex_hull
line_hull_exterior = line_convex_hull.exterior
sec_distances = {}
lines_merged = linemerge(section_lines)

for i,line in enumerate(lines_merged):
    x,y = line.xy
    if i == 0: 
        plt.plot(x,y,c='k',label='lines merged')
    else:
        plt.plot(x,y,c='k')


for i,sid in enumerate(section_ids):
    dist_along = lines_merged.project(Point((x_points[i],y_points[i])), normalized=True)
    #sys.stdout.write("{} at distance of {}\n".format(model.section(sid).name(), dist_along))
    sec_distances[dist_along] = model.section(sid).name()
    
ordered_sec_dists = collections.OrderedDict(sorted(sec_distances.items()))
    
for key,value in ordered_sec_dists.items():
    sys.stdout.write("{}\tat\t{}\n".format(value, key))


conv_x,conv_y = line_hull_exterior.xy
plt.scatter(x_points,y_points,c='g',label='data')
plt.plot(conv_x,conv_y,c='r',label='convex hull')
plt.legend(loc='best')
plt.savefig("shapely_objects_from_trace.png")

