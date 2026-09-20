# Liu2020_Ridgecrest_SI

Source: `Liu2020_Ridgecrest_SI.docx`

Geophysical Research Letters

Supporting Information for

Rapid Characterization of the 2019 July Ridgecrest, California Earthquake Sequence from Raw Seismic Data using Machine Learning Phase Picker

Min Liu1,2, Miao Zhang2*, Weiqiang Zhu3, William L. Ellsworth3 and Hongyi Li1

1School of Geophysics and Information Technology, China University of Geosciences (Beijing), China

2Department of Earth and Environmental Sciences, Dalhousie University, Canada

3Department of Geophysics, Stanford University, USA

*Corresponding author: Miao Zhang (miao.zhang@dal.ca)

Contents of this file

Texts S1 to S3

Figures S1 to S17

Additional Supporting Information not in this file

Descriptions for a table and two Movies

Introduction

This supporting information provides three texts, seventeen figures, one table (separate from this file) and two movies (separate from this file) to support the discussions in the main text.

### Text S1. Magnitude estimation

We estimate local magnitude () using the attenuation relation of Hutton and Boore (1987). The maximum amplitudes of horizontal component data are measured after deconvolving the instrument response from the raw waveforms and then convolving the obtained signal with the theoretical Wood-Anderson seismometer response (Zhang et al., 2019). The measured waveform window starts 0.5 sec before P wave arrivals and is twice the predicted S-P travel time in length.

We compare the magnitude difference between our REAL catalog and the routine catalog. Magnitudes in our catalog are systematically lower than the routine catalog (even for the common events in both catalogs, see Figure S15), especially for the events with magnitude larger than 4.0. Such differences can be caused by many reasons such as 1) different formulas are adopted in the two catalogs (https://scedc.caltech.edu/eq-catalogs/change-history.html; last accessed Oct. 2019) (note that different types of magnitude were adopted for those large events in the routine catalog), 2) different stations are used in the two catalogs (note that we only use stations with epicentral distance less than 100 km), leading to underestimated magnitudes for some large events, including the Mw 6.4 and Mw 7.1 mainshocks, 3) magnitudes of some events were overestimated in the routine catalog due to the effects of coda waves of previous large events.

### Text S2. Pick quality control for hypoDD

To improve the location precision, we reselect P and S picks before we apply hypoDD to relatively relocate earthquakes. We only keep P wave and S wave picks with epicentral distance less than 80 km and systematically remove the outlier picks with arrival time off from the major trend of P and S travel time curves larger than 0.8 sec and 1.2 sec, respectively (Figure S16).

### Text S3. Missed events in the VELEST catalog

There is always a trade-off between number of earthquakes and earthquake location precision. Here the strategy is, without human intervention, to build a high-quality and robust earthquake catalog rapidly. With strict threshold settings, VELEST documents more than twice as many events as the routine catalog, recovering 88% of them. The 12% (884) missed events are due to:

1) events triggered an insufficient number of picks. In REAL, we use a strict threshold to build a robust catalog (i.e., five P picks and a total of thirteen P and S picks). But the number of associated picks can be as small as four in routine catalog. There are 359 events with fewer than 13 arrival time picks in the routine catalog, suggesting we would miss them even though we have the same number of picks for them. We could recover more by decreasing the threshold, but potentially reducing the location precision (e.g., include more picks with large uncertainty and degrading the network geometry) while also increasing the possibility of false detection.

2) event occurred out of searched depth. REAL detects and preliminarily locates events in a limited 3D searching region. In this study, we only focus on events occurred with depth less than 20 km. Among the missed earthquakes, 113 events in the routine catalog have a depth larger than 20 km (assumedly their depth can be constrained very well in routine catalog), which exceeds our searching range.

3) events occurred closely in space and time (Figure S3). To prevent multiple detections for one earthquake, REAL only keeps the most reliable event within a limited time window (i.e., five sec in this paper), leading to some events missing due to their occurrence closely in time (Zhang et al., 2019).

4) events buried in the coda waves of previous events (Figure S17). It is still challenging to detect those events occurring following previous large events. Due to the low signal-to-noise-ratios at most stations, there are not enough picks to associate and locate the events.

5) events recorded with large station gap and/or travel time residual. In our VELEST catalog, we only keep those well-constrained earthquakes with < 200° station gap and < 0.6 sec travel time residual.

### Figure S1. Distribution of seismic stations used in this study. Left panel: seismic stations are marked by red triangles, along with their names. Right panel: Zoomed-in area in Figure S1 (black rectangle) to better show overlapped stations.

Figure S2. An example of phase picks (an event with ML 1.32) by PhaseNet. Red and blue lines mark the detected P and S phases, respectively. Black dashed line in the panel (d) indicates the probability threshold of 0.5 when applying PhaseNet.

Figure S3. Number of events with time for the routine catalog, REAL catalog and missed events. (a) Number of events as a function of time in one hour bins. Two black stars indicate the Mw 6.4 and Mw 7.1 mainshocks, respectively. (b) Similar to top panel, but for the accumulated number of events.

Figure S4. Distribution of earthquakes documented in the REAL catalog. Left panel shows the map view of earthquake locations and right panel shows the 3D version. Blackness is proportional to the number of overlapped events.

Figure S5. Travel-time curves for the associated P and S waves by REAL. Black lines indicate the major trend of P and S travel time curves.

Figure S6. Earthquake location comparison along B-B’ cross section in Figure 2 among different earthquake catalogs. (a) Black dots indicate earthquake locations reported by SCSN. Earthquakes within 3 km of the cross section B-B’ are projected on the profile. (b-d) Similar to Figure S6a, but for the VELEST catalog, hypoDD catalog, and routine CC catalog, respectively.

Figure S7. Similar to Figure 2, but for 3D version. Black dots with a 25% transparency represent the locations of earthquakes listed in the corresponding catalogs (see titles). Blackness is proportional to the number of overlapped events.

Figure S8. Four named faults in main text: NW main fault (in dark yellow), NE fault (in dark orange), NW branch fault (in dark blue) and subparallel branch faults (in red). Light blue lines indicate the surveyed surface ruptures (Kendrick et al, 2019).

Figure S9. Detailed spatio-temporal distribution of the 2019 Ridgecrest sequence along the B-B’ cross section (section B-B’ in Figure 3 and the orange bar in Figure S8). (a) Earthquake activity from July 4, 2019 to the Mw 6.4 mainshock. Earthquakes within 3 km of the cross section B-B’ are projected on the profile. (b) Similar to Figure S9a, but for events occurring between the Mw 6.4 and Mw 7.1 mainshocks. (c) Similar to Figure S9a, but for events occurring from the Mw 7.1 mainshock to July 9, 2019. (d) Earthquake activity in the total period from July 4, 2019 to July 9, 2019. Event color changes with their origin time.

Figure S10. Detailed spatio-temporal seismicity evolution before the Mw 7.1 mainshock. (a) Light blue lines indicate the surveyed surface ruptures (Kendrick et al, 2019). Earthquakes are projected along the A-A’ cross section (red line), showing on the bottom profile. Black dots represent the earthquakes occurred in the time period from the first foreshock to the Mw 6.4 mainshock. Purple star and circle pinpoint the locations of the Mw 6.4 mainshock hypocenter in map view and profile, respectively. (b-e) Similar to Figure S10a but for different periods (b – from the first event occurred on the NE-trending fault to the time point before the first event occurred along the NW-trending branch fault; c – from the first event occurred on the NW-trending branch fault to the time point before the first event occurred close to the hypocenter of the Mw 7.1 mainshock; d – from the first event occurred close to the hypocenter of the Mw 7.1 mainshock to the time point before a burst of seismicity extended activity towards the hypocenter of the MW 7.1 mainshock; e – from the beginning of a burst of events to the time point before the Mw 7.1 mainshock occurred). (f) Similar to Figure S10a but for the whole period. Colored dots indicate the locations of the foreshocks with elapsed time. Earthquakes after the Mw 7.1 mainshock are marked by gray dots as background. Purple star and circle indicate the Mw 7.1 mainshock in map view and profile, respectively.

### Figure S11. (a) Distribution of the triggered seismicity after the Mw 6.4 mainshock and before the Mw 7.1 mainshock. Light blue lines indicate the surveyed surface ruptures (Kendrick et al, 2019). Two black rectangles mark the two regions with triggered seismicity. (b-c) Accumulated triggered events with time in regions 1 and 2, respectively.

Figure S12. (a) Distribution of the triggered seismicity after the Mw 7.1 mainshock. Light blue lines indicate the surveyed surface ruptures (Kendrick et al, 2019). Two black rectangles mark the two regions with triggered seismicity. (b-c) Accumulated triggered events with time in regions 1 and 2, respectively.

Figure S13. Earthquake map view in different depths and time periods. (a) Earthquake distribution before the Mw 7.1 mainshock. Light blue lines represent the surveyed surface ruptures (Kendrick et al, 2019). Red star marks the Mw 6.4 mainshock epicenter. (b-d) Similar to Figure S13a, but in different depth ranges (i.e., 0-3 km, 3-10 km and 10-13 km). (e) Similar to Figure S13a, but for events after the Mw 7.1 mainshock. Red star represents the Mw 7.1 mainshock epicenter. (f-h) Similar to Figures S13b-d, but for the events after the Mw 7.1 mainshock.

Figure S14. 3D back view of Figure 4 (zoomed-in area in Figure 3d). Light blue lines represent the surveyed surface ruptures (Kendrick et al, 2019). Red and gray dots with a 25% transparency (deeper color means events are overlapped) indicate the locations of earthquakes before and after the Mw 7.1 mainshock in a depth range of 3-10 km, respectively. Small and large black stars represent the Mw 6.4 and Mw 7.1 mainshocks, respectively. Areas marked by black dashed lines indicate the identified two major near-orthogonal buried faults activated by the aftershocks of the Mw 6.4 mainshock.

Figure S15. Left panel shows the magnitude distribution of common events with time for the routine catalog and REAL catalog. Right panel shows their magnitude differences. Detailed discussions can be found in Text S1.

Figure S16. Phase selection before applying hypoDD. Blue dots represent the selected picks that adopted in hypoDD, which best fit the major trend of P and S travel time curves. Red dots represent those P and S picks in VELEST catalog but not adopted when applying hypoDD.

Figure S17. An example of an event missing from our catalog. Red dashed line indicates an approximate P wave velocity of 5.74 km/s.

### Ridgecrest2019catalog.txt. The final hypoDD earthquake catalog. The study region can be found in Figure 1.

### Movie S1. 3D movie showing detailed spatio-temporal distribution of the 2019 Ridgecrest sequence from 4 July 2019 to 9 July 2019. This movie was inspired from a similar movie (https://response.scec.org/sites/default/files/Ridgecrest_relocs_thruJuly9_Shelly_run2f.mp4) posted by Dr. David Shelly.

### Movie S2. 3D movie showing the seismicity distribution in hypoDD catalog. This movie was inspired from a similar movie (https://response.scec.org/sites/default/files/Ridgecrest_relocs3D_thruJuly9_run2f_Shelly.mp4) posted by Dr. David Shelly.
