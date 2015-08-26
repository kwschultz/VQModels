sim.version                       = 2.0
sim.time.end_year                 = 1000
sim.greens.method                 = standard
sim.greens.output                 = greens_ALLCAL2_VQmeshed_subset_NorCal_3km.h5
sim.greens.use_normal             = false
sim.friction.dynamic              = 0.5
sim.file.input                    = ALLCAL2_VQmeshed_subset_NorCal_3km.txt
sim.file.input_type               = text
sim.file.output_event             = events_ALLCAL2_VQmeshed_subset_NorCal_3km_1kyr_dyn0-5.h5
sim.file.output_event_type        = hdf5
sim.system.sanity_check           = 0
sim.system.progress_period        = 5
sim.bass.max_generations          = 0
sim.friction.compute_stress_drops = 0


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