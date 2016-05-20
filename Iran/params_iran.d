sim.time.end_year                 = 20000
sim.greens.method                 = file
sim.greens.input                  = greens_Iran_Lakarkuh_subsample.h5
###----------------------------------------------
sim.friction.dynamic              = 0.2          
## This "sim.friction.dynamic" is also a tuning variable                                  
sim.file.input                    = Iran_Lakarkuh_subsample_fault_3000m_drops0-9.txt  
## The last "drops0-9" indicates stress drop factor = 0.9, tuning variable used in the Mesher
###----------------------------------------------
sim.file.input_type               = text
sim.file.output_event             = Iran_Lakarkuh_subsample_noTaper_20kyr_drops0-9_dyn0-2_DynDrops_GreensGuess_mult0-8.h5
sim.file.output_event_type        = hdf5
sim.system.sanity_check           = 0
sim.system.progress_period        = 5
sim.bass.max_generations          = 0
sim.friction.dynamic_stress_drops = 1
sim.greens.offdiag_multiplier     = 0.8

####### 4 sigma to exclude largest outliers
sim.greens.shear_offdiag_min      = -1200000
sim.greens.shear_offdiag_max      =  4400000
#### guess
sim.greens.normal_offdiag_min     = -1000000
sim.greens.normal_offdiag_max     =  1000000


# Other possible parameters (with default values where given)
# sim.bass.b = 1
# sim.bass.c = 0.1
# sim.bass.d = 300
# sim.bass.dm = 1.25
# sim.bass.max_generations = 0
# sim.bass.mm = 4
# sim.bass.p = 1.25
# sim.bass.q = 1.35
# sim.file.output_stress =
# sim.file.output_stress_index =
# sim.file.output_stress_type =
# sim.greens.bh_theta = 0
# sim.greens.input =
# sim.greens.kill_distance = 0
# sim.greens.output =
# sim.greens.sample_distance = 1000
# sim.greens.use_normal = false
# sim.system.checkpoint_period = 0
# sim.system.checkpoint_prefix = sim_state_
# sim.system.transpose_matrix = 1