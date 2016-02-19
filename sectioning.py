import numpy as np
import quakelib, sys, collections, re
from shapely.geometry import Point, LineString, MultiPoint
from matplotlib import pyplot as plt
from shapely.ops import linemerge

ASEISMIC_CUT = 0.11

WORKING_DIR = '/Users/kasey/VQModels/'
UCERF3 = WORKING_DIR+'UCERF3/UCERF3_VQmeshed_from_EQSIM_AseismicCut_0-11_ReFaulted_taper_renorm_drops0-7.txt'
OUTFILE = WORKING_DIR+'UCERF3/UCERF3_VQmeshed_from_EQSIM_AseismicCut_0-11_ReFaulted_taper_renorm_drops0-7_ReSectioned.txt'
OUTKML = WORKING_DIR+'UCERF3/UCERF3_VQmeshed_from_EQSIM_AseismicCut_0-11_ReFaulted_taper_renorm_drops0-7_ReSectioned.kml'


UCERF3_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Geometry.dat'
UCERF3_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Friction.dat'
UCERF3_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Geometry.txt'

FINAL_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'_Geometry.dat'
FINAL_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'_Friction.dat'
FINAL_FILE_TEXT = WORKING_DIR+'UCERF3/UCERF3_EQSim_ReFaulted_ReSectioned_AseismicCut_'+str(ASEISMIC_CUT)+'.txt'

model = quakelib.ModelWorld()
#model.read_file_ascii(UCERF3)
model.read_files_eqsim(UCERF3_FILE_GEO, "", UCERF3_FILE_FRIC, "none")

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


model.create_faults_minimal()  # Create the fault objects but don't worry about the area/DAS/etc.
model.write_files_eqsim(FINAL_FILE_GEO, "", FINAL_FILE_FRIC)
print("New model files written: {}, {}".format(FINAL_FILE_GEO, FINAL_FILE_FRIC))

#model.create_faults("none")
#model.write_file_ascii(OUTFILE)
#model.write_file_kml(OUTKML)

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
#plt.scatter(x_points,y_points,c='g',label='data')
#plt.plot(conv_x,conv_y,c='r',label='convex hull')
#plt.legend(loc='best')
#plt.savefig("shapely_objects_from_trace.png")

