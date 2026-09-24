# @AGUPUBLICATIONS

Geophysical Research Letters

Supporting Information for

# Anatomy of a Caldera Collapse: Kīlauea 2018 Summit Seismicity Sequence in High Resolution

David R. Shelly<sup>1</sup>, Weston A. Thelen<sup>2</sup>

<sup>1</sup>U.S. Geological Survey, Golden, CO, 80401, USA; <sup>2</sup>U.S. Geological Survey, Vancouver, WA, 98683, USA

Contents of this file

Text S1 Figures S1 to S3 Table S1

Additional Supporting Information (Files uploaded separately)

Captions for Movies S1 to S2

Captions for Datasets S1 to S2

## Introduction

Supplemental material for this manuscript includes supplemental Methods text, three supplemental figures, one supplemental table, two earthquake datasets derived in this study (text files), and two animations showing seismicity evolution (MP4 movie files).

## Text S1. Supporting Methods, Event detection and location procedure

For each template event, we formed P and S waveform templates on each channel with at least one (P or S) seismic phase pick. In cases with only one phase pick (stations commonly have only P picks), we estimated the other phase arrival time using the catalog origin time and a $\mathsf { v } _ { \mathsf { p } } / \mathsf { v } _ { \mathsf { s } }$ ratio of 1.75. This $\mathsf { v } _ { \mathsf { p } } / \mathsf { v } _ { \mathsf { s } }$ ratio was chosen to be deliberately slightly low, to avoid missing the S-wave onset. Templates were started 0.2 seconds prior to the estimated phase arrival time. P-wave templates were limited to 2.5 s, though many were truncated to avoid overlapping with S-wave templates. S templates were 4.0 seconds long. All data were filtered 3-15 Hz, a band chosen for generally good signal-to-noise ratio and event coherence.

These templates were then scanned through the continuous seismic data to search for similar events, with similarity measured as the sum of correlation coefficients measured on each channel of data. At the same time, we also measured precise differential arrival times between template events and each detected event. This is achieved using the time of summed correlation as a detection reference time from which we derive a reference origin time. Individual channel differential times are then calculated from the detection reference time. Later, we apply an origin time correction as necessary to account for slightly different reference origin times for the same event detected by different templates. Detection thresholds and weightings were implemented as described in Shelly et al. [2016a], with 8 times the daily median absolute deviation (MAD) for the summed correlations and $7 ^ { * } { \mathsf { M A D } }$ for individual channel differential time measurements. Data weighting combined the squared correlation values with the difference in height between primary and secondary (nearby) peaks. To accommodate events with different phase polarities, both positive and negative correlation peaks were allowed in the individual channel measurements.

All event pairs with at least four successful differential time measurements were input into the hypoDD double-difference relocation algorithm [Waldhauser and Ellsworth, 2000], resulting in more than 25 million correlation-derived differential times (\~20 million P and \~5.5 million S). Additionally, we used \~1.9 million catalog-derived differential P times and 0.8 million differential S times. We used a 1-D velocity model approximating the P-wave model of Dawson et al. [1999] for the area. Previously estimated $\mathsf { v } _ { \mathsf { p } } / \mathsf { v } _ { \mathsf { s } }$ values in the source region have varied wildly from low values of \~1.6 [Lin et al., 2015] to very high values >2.0 [Dawson et al., 1999]. For this study we therefore used a moderate $\mathsf { v } _ { \mathsf { p } } / \mathsf { v } _ { \mathsf { s } }$ ratio of 1.78. Waveform data from seismic stations within 20 km of Kīlauea summit were used for cross-correlation measurements, while catalog phase pick times were used from stations within 70 km. Catalog event starting locations were set to their HVO catalog locations, while each newly detected event was started at the median location of all catalog events that detected the event. We note that locations produced in this study are predominantly hypocentroid, rather than hypocenter locations, due to their final relative locations being primarily constrained by correlation-derived differential arrival times.

![](mineru/Shelly2019_Kilauea_Figure_SI/images/d06b3799266c2c622edd7f4329d8a63b7a3e2c03b652072bd227a430fd1dd540.jpg)
Figure S1. Helicorder plot showing example of seismic cycle, with quiescence following and build-up preceding collapse events. Plotted is station AHUD, EHZ (vertical) component, located \~4 km SSE of Kīlauea Caldera. Data is artificially clipped to emphasize smaller earthquakes between collapse events.

Seismicity in 6 hours preceding collapse

![](mineru/Shelly2019_Kilauea_Figure_SI/images/26fb795059c5ff0ffe5e7d5fb98048929c6c907c3261b7809e2459e1ebc75772.jpg)

Seismicity in 6 hours following collapse

![](mineru/Shelly2019_Kilauea_Figure_SI/images/45490c81a0c47bd59abb69fe4e3a0b8a5972ebeb3eec48541e00f5741d12f661.jpg)

b)  
![](mineru/Shelly2019_Kilauea_Figure_SI/images/560f9f2acfa48705a37a72a22d8d619d58796b21fda3e15894139f22f4991f1a.jpg)

d)  
![](mineru/Shelly2019_Kilauea_Figure_SI/images/55fec5cda1d873101b66e7283b8abe9ecb5716cd845a5fc173df63bf9b6d89f5.jpg)
Figure S2. Comparison of seismicity during 6 hours prior to collapse events (a,b) versus 6 hours after collapse events, for events during June and July 2018. Top plots (a,c) show map views; lower plots $( \mathsf { b } , \mathsf { d } )$ show corresponding cross-sections.

![](mineru/Shelly2019_Kilauea_Figure_SI/images/3ef248202c3ec25e105f6c3db3c634807d6f8a75e67c67d3e2a0d59ad4e9f8f7.jpg)
Figure S3. Depth versus time for Kīlauea summit seismicity. Thin vertical black lines indicate timing of collapse events [Shiro et al., 2018]. Events with M>3 are shown by red bars, with length roughly approximating expected rupture dimension (3 MPa stress drop assumed, but rupture dimension is only weakly dependent on stress drop). Note the increase in shallow M 3+ seismicity in the latter half of the eruption. Seismicity in the first few days of May (prior to $M _ { w } 6 . 9$ earthquake on May 5) is largely just outside Kīlauea caldera itself.

<table><tr><td>Post Date to HVO Logs</td><td>Date range detected/relocated</td><td>Template date range</td><td># of EQs relocated</td></tr><tr><td>Run1: June 7, 2018</td><td>4/29-6/6</td><td>4/29-6/1</td><td>4615</td></tr><tr><td>Run 2: Jun 12, 2018</td><td>4/29-6/11</td><td>4/29-6/6</td><td>5295</td></tr><tr><td>Run 3: June 20, 2018</td><td>4/29-6/19</td><td>4/29-6/6</td><td>10149</td></tr><tr><td>Run 4: June 28, 2018</td><td>4/29-6/27</td><td>4/29-6/24</td><td>19529</td></tr><tr><td>Run 5: July 5, 2018</td><td>6/6-7/4</td><td>4/29-7/2</td><td>19237</td></tr><tr><td>Run 6: August 7, 2018</td><td>4/29-8/1</td><td>4/29-7/27</td><td>42994</td></tr><tr><td>Final (reported here)</td><td>4/29-8/6</td><td>4/29-8/6</td><td>44188</td></tr></table>

Table S1. Summary of event relocations posted to HVO internal log system and used in eruption response. Run 5 did not include events 4/29-6/5 due to a technical issue limiting relocation data size. This issue was overcome for run 6 and final versions.

![](mineru/Shelly2019_Kilauea_Figure_SI/images/600f434b447868f8af57dbe9377eb7f40562338e068bb1a1f4d08e8b98ef39a6.jpg)

Longitude (°)  
B  
![](mineru/Shelly2019_Kilauea_Figure_SI/images/cf8799fafd5cb6f2c591057088879f15a26ea0c1c0a438793228b834a5b3a50c.jpg)
Distance (km)  
Movie S1. Animation of earthquakes with time. a) Month of May b) Month of June c) Month of July and early August. Each month plots seismicity extending one week prior (the last week of the previous month) and following (the first week of the next month). Top panel view shows map view. Lower panel shows rotation cross-section $\mathsf { A } { \boldsymbol { \cdot } } \mathsf { B } ,$ as indicated in map view. Animation shows a 6-hour moving window. Events within this window show up as red (at leading edge) and transition through the color spectrum to blue to aid in viewing migration. Circle size scales with magnitude and is a rough approximation of physical rupture dimension (3 MPa stress drop assumed). Events occurring after this window (future events) are shown as small white dots. Events occurring before this window (past events) are shown as small black dots. White lines in map view show major caldera topographic features, as they existed prior to the 2018 eruption sequence.

Ev. 22241-22640, 06/26,18:49 - 06/27,01:45  
![](mineru/Shelly2019_Kilauea_Figure_SI/images/5eeb10c04cce22ce7e6524b519ce48fefea6522d713fdb4ef2142e20e340a054.jpg)

Longitude (°)  
![](mineru/Shelly2019_Kilauea_Figure_SI/images/a4e3a9f86c7153138ec43dc77c04073c297ef01baaca0ca35df5c3bf1575c30d.jpg)
Distance (km)  
Movie S2. Animation of sequence showing a moving window with a fixed number of events (400 events, variable time range), colored by cluster (see Figure 2). Top panel shows map view; lower panel shows corresponding west-east cross section. Depth is referenced to Kīlauea summit of 1.2 km asl. Circle size scales with magnitude and is a rough approximation of physical rupture dimension (3 MPa stress drop assumed).

Data Set S1. Event location catalog (44,188 events). Depth is referenced to Kīlauea summit at 1.2 km asl.

yyyy mm dd HH MM SS.SSS lat(deg) lon(deg) depth(km) x(m) y(m) z(m) magnitude eventID

Data Set S2. Event location and polarity cluster catalog (43,950 events). Depth is referenced to Kīlauea summit at 1.2 km asl.

cluster# yyyy mm dd HH MM SS.SSS lat(deg) lon(deg) depth(km) magnitude