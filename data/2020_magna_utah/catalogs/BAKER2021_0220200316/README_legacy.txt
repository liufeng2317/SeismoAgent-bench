This a machine-learning derived automatic catalog for the sequence.  The file contains P, S, and first-motion picks made on three-component network and nodal data as well as event informmation.   The soon to be mentioned cross-correlation catalog is available from http://www.isc.ac.uk/dataset_repository/view_submission.php?dsid=20. 

Fields:

event_number:  A unique event counter that is specific to this catalog.  Note the maximum value is not equal to the number of events in this catalog as many events were eliminated by the quality control.
network: The station's code - likely UU.
station: The station's name. 
channel: A channel code.  The useful information here is the first two letters which signify sampling rate and instrument gain.  The third letter will be Z for all P picks and N for all S picks.
phase: The name of the picked phase.  This will be P or S.
arrival_time: The phase pick's arrival time in UTC.  
static_correction: A static correction to add to the arrival time for purposes of locating in the paper.
first_motion: The arrival's polarity which is only applicable for P picks.  This will be up (+1), down (-1), or unknown (0). 
first_motion_weight: The posterior probability of the classification as made by the deep-learning network.
residual: The residual in seconds between this arrival and the predicted arrival during location.  This is obtained from HypoInverse2000.
take_off_angle: The take-off angle obtained from our event locator.  This is obtained from HypoInverse2000.
source_receiver_azimuth: The source-receier azimuth measured in degrees positive east from north.  This is obtained from HypoInverse2000.
source_receiver_distance: The source-receiver epicentral distance in km.  This is obtained from HypoInverse2000. 
weight_used: The weight used by HypoInverse2000 during location.  
event_latitude: The event's latitude in degrees obtained from HypoInverse2000.  
event_longitude: The event's longitude in degrees obtained from HypoInverse2000.  This is corrected to a positive east coordinate system. 
event_depth: The event depth in kilometers obtained from HypoInverse2000.  
origin_time: The event origin time in UTC obtaiend from HypoInverse2000.  
azimuthal_gap: The largest azimuthal gap in degrees obtained from HypoInverse2000.
n_weighted_residuals: The number of weighted residuals used by HypoInverse2000.  
n_first_motions: The number of picks with first motions for this event.  
rms: The root-mean-squared misfit for HypoInverse2000's solution.
epochal_origin_time: The origin time of the event in UTC seconds from the epoch (Jan 1 1970)
epochal_arrival_time: The arrival time of the phase in UTC secodns from the epoch (Jan 1 1970)
magnitude: An event magnitude obtained from the UUSS official catalog or cross-correlation catalog.  This is applicable to events that were collocated to the event catalog.
magnitude_type: If an event was found in the UUSS official catalog then this is the corresponding magnitude type.  This will be w (moment magnitude), l (local aka Richter magnitude) or d (coda aka duration magnitude).
catalog_evid: If an event was found in the UUSS catalog or the cross-correlation catalog then we note the corresponding event ID from the respective catalog
Mj: This is a magnitude obtained from an independent study conducted by James Holt that aimed to calibrate Mw to small magnitudes.  This only is available fro a handful of events.
