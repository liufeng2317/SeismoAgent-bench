# grl59060-sup-0001-text_si-s01

Source: `grl59060-sup-0001-text_si-s01.docx`

Geophysical Research Letters

Supporting Information for

Crustal fault connectivity of the Mw 7.8 2016 Kaikōura earthquake constrained by aftershock relocations

F. Lanza1, C. J. Chamberlain2, K. Jacobs 3, E. Warren-Smith3, H. J. Godfrey2,3, M. Kortink2, C. H. Thurber1, M. K. Savage2, J. Townend2, S. Roecker4, and D. Eberhart-Phillips5.

1University of Wisconsin-Madison, Madison, Wisconsin, USA

2Victoria University of Wellington, Wellington, New Zealand

3GNS Science, Lower Hutt, New Zealand

4Rensselaer Polytechnic Institute, Troy, New York, USA

5GNS Science, Dunedin, New Zealand

Contents of this file:

Text S1 to S6

Figures S1 to S13

Table S2

Additional Supporting Information (Files uploaded separately)

Caption for Table S1

Caption for Movie S1

Catalog of relocated hypocenter data and pick times (QuakeML format)

Introduction

This supplementary material section contains further information about the processing techniques used for both phase arrival picking and aftershock relocation. A station map is shown in Figure S1. We outline the details of the auto-picker algorithm REST and its performance in Text S1 accompanied by explanatory Figures S2 through S5. We provide some additional relocation results obtained with the NonLinLoc algorithm in Text S2 and associated Figures S6 through S8. Figure S9 is a “heat map” of the final relocations; location uncertainties are spatially mapped in Figure S10. Location bias and absolute error estimations are discussed in Text S3 and Text S4 with supporting Figures S11 and S12, respectively. In Text S5 we discuss the choice of thresholds and hypocenter separation for the double-difference relocation analysis. A note on the role of the subduction interface in the post-seismic phase is presented in Text S6. Figure S13 supports the discussion in the main text regarding the Hope Fault role in the aftershock sequence. A 3D visualization of the obtained relocations is provided as movie S1. The relocated hypocenters and P and S arrival times are also provided as a file in QuakeML format. This file contains origin time, latitude, longitude, depth and magnitude information for the 2655 events relocated with simul2014 and HypoDD 3D v2.1b. Whenever an event has been relocated by both methods, the preferred location is set to be the one obtained with HypoDD. For each event, arrival time picks and their uncertainties are also provided.

Text S1. REST autopicker algorithm theory

Various algorithms have been developed for automatically detecting P- and S-wave arrivals, including the original short-term average/long-term average (STA/LTA) algorithm (Allen, 1982), to the incorporation of auto-regressive methods (Leonard and Kennett, 1999), higher-order statistics (Baillard et al., 2014; Ross et al., 2016), neural networks or trees (Gentili and Michelini, 2006; Ross et al., 2018; Wang & Teng, 1997), wavelets (Anant & Dowla, 1997), and combinations of techniques (Sleeman & van Eck, 1999), among others. We introduce here a hybrid method for automated detection and onset estimation, called REST, which combines a modified version of the nearest-neighbor similarity scheme of Rawles & Thurber (2015) with the auto-regressive approach of Kushnir et al. (1990).

The general purpose of the REST package of programs is to automatically generate a catalog of P and S arrival times and event locations starting from a set of seismograms recorded by a local network over some period of time. The principal philosophy adopted is one of iterative refinement. The algorithm starts by producing rough estimates of when coherent phases may be present in the data stream, and iteratively refines these estimates by determining if the phases can be associated with a reasonable event location. The Kushnir et al. (1990) detection method implemented here, uses autocorrelations computed in a moving window and a Bayesian hypothesis test to assess how different the autocorrelation is from zero (it will be zero in the case of pure zero-mean Gaussian noise). The running mean normalization scheme of Bensen et al. (2007), used in ambient noise pre-processing, is also incorporated in the algorithm in order to reduce the effects of coherent signals (such as earthquakes) in defining noise segments. This is especially useful for aftershock sequences, when the persistent high amplitudes due to many earthquakes biases the true noise level. The fall-off of the Kushnir et al. (1990) estimation function is used to assign uncertainties and the asymmetry of the function serves as a causality constraint (Figure S2). Once a detection is declared and an automatically designed noise suppression filter is applied, the algorithm identifies when the auto-regressive model of the time series changes abruptly to determine the arrival times. The next processing step associates picks into events, and the events are then located using a grid-search method and a provided 1D velocity model. The algorithms for travel time computation and event location are from the tomoFD package of Roecker et al. (2006). Once a location has been estimated, a reasonable window for searching for the P arrival can be defined using the hypocentral distance and an average P-wave velocity value. Once an origin time for an event and a P arrival for a particular trace are known, then a reasonable window for searching for the S arrival can be defined based on an appropriate range of Vp/Vs values. Both horizontal components are used for picking S-wave arrivals. The dissimilarity between the signals before versus after a particular time sample is measured using the ratio of the probability density for signal and noise, with the dissimilarity maximum taken as the arrival time.

1.1 REST phase-picks

We apply the REST onset estimation scheme to the 2768 catalog events selected for this study. Traces are resampled to 100 Hz (as needed) and bandpass filtered between 1 and 20 Hz using a Bessel filter with 6 pole rolloffs. The moving window length selected for arrival detection is 420 seconds with 60 seconds of overlap. The grid area used by the location routine is a volume with dimensions 536 x 660 x 400 km in x, y, and z directions and a grid spacing of 4 km. The grid is oriented N-S, with the northwestern corner of the selected area at longitude 171.38° E and latitude 39.0° S.

By applying REST to the set of events, all events but 3 were successfully picked and located by the algorithm. The 3 events missed failed to be located by the autopicker due to the scarcity of good quality picks. For the 2765 events correctly identified, the final numbers of P and S-wave arrival times are 117,568 and 91,659, respectively.

1.2 REST performance from manual pick comparison

When testing REST performance and NonLinLoc location performance (Text S2) we used a subset of 632 GeoNet events that were reviewed at the time of testing (December 2017). To assess REST algorithm accuracy, two subsets of events from the original selected catalog were picked manually. The first dataset includes 48 events with minimum GeoNet reported magnitudes of 3.0 from a two-week period (9-20 December 2016), and the second set comprises 103 events with minimum GeoNet reported magnitude of 4.0 over the ~6-month period (from 16 November 2016 to 13 May 2017) for which the STREWN experiment was operative. The two sets of events were chosen purposely to have different magnitude ranges and to span different time periods, in order to ensure that a variety of events were included in the analysis. To mitigate the effect of the subjectivity of manual picking, the two datasets were picked by different analysts, with nine events common to both datasets. For events in these datasets, traces were demeaned, detrended and bandpass filtered between 0.5 and 17 Hz with a Butterworth filter due to the presence of significant noise during the smaller magnitude events. No instrument response or polarity corrections were applied at this stage.

For the lower magnitude dataset, 1,426 P-wave arrival times and 1,135 S-wave arrival times were manually picked across the 48 events and 46 stations. The total number of corresponding automatically-picked P- and S-wave arrival times for the same station/event combinations was 1,358 and 540, respectively. Of these automatic picks, 1,291 P (95.0%) and 401 S-wave phases (77%) picks fall within the picking and travel time residual thresholds set in the auto-picker algorithm. The time difference between the manual and automatic picks for 96.8% of the quality automatic P-wave arrivals and 95.0% of the quality S-wave arrivals is within the uncertainty of the automatically-picked arrival times (below the dashed line in Figure S3).

For the higher magnitude dataset, 2,801 P-wave arrival times and 2,415 S-wave arrival times were manually picked across the 103 events and 46 stations. The total number of corresponding automatically picked P- and S-wave arrival times for the same station/event combinations was 2,510 and 710, respectively. Of the automatic picks, 2,390 P (95.2%) and 547 S (77.0%) picks fall within the picking and travel time residual thresholds set in the auto-picker algorithm. Overall, the time difference between the manual and automatic picks for 88.4% of the 2,390 quality automatic P-wave arrivals and 93.2% of the 547 quality S-wave arrivals is within the uncertainty of the automatically-picked arrival times (below the dashed line in Figure S3).

Of the two datasets used in the manual comparison with REST auto-picks, the lower magnitude dataset performed better, with 96.8% and 95.0% of quality automatic P- and S-picks falling within the auto-pick error, respectively (Figure S3). The difference in the magnitude distribution of the two datasets could be the cause of this difference in performance. We observe that magnitude 4.0+ events tend to show more emergent phase arrivals and complex waveforms than the magnitude 3.0 events, with stronger head- and direct-wave partitioning and phase conversions. This explains the lower number of qualifying automatically picked S-wave arrivals. Higher magnitude events are also more likely to have longer and more complex source-time functions, complicating phase identification. This could result in fewer quality automatic picks for magnitude 4.0 events than for magnitude 3.0 events, even though the larger earthquakes have higher amplitudes (and therefore higher signal-to-noise ratios). Quality automatic P-picks with corresponding manual picks represent 68.7% and 74.1% of potential P-picks for higher and lower magnitude datasets, respectively. Similarly, quality automatic S-picks represent 19.2% and 28.9% of potential S-picks in the two datasets.

In both datasets, there is a substantial number of P-picks with time difference between the automatic and manual picks exceeding the uncertainty estimate of the automatically-picked arrival times (above the dashed line in Figure S3), but with the lowest assigned auto-pick uncertainty. We attribute this anomaly to cycle skipping where the automatic P pick is n half-cycles different from the manual pick. This could result when the autopicker observes the earliest/smallest first motion for emergent P-waves which are missed by the analyst, as its amplitude can be dwarfed by quickly increasing energy or masked by noise at frequencies otherwise filtered out by the autopicker. Conversely, the autopicker algorithm may miss the first n half-cycles if the amplitude does not meet the detection threshold.

We further evaluate REST accuracy with respect to S-P time in order to determine the method’s ability to apply to different distance ranges. Figure S4 shows a density plot of deviation between automatic and analyst picks as a function of S-P time. Most events have an S-P time less than 25 s. For both P wave and S wave, there appears to be little correlation between uncertainty and S-P times. Higher uncertainties characterize the S-wave picks, as expected. This suggests a good success rate for the REST auto-picker for events spanning a wide distance range.

Overall, the REST auto-picker performs well for our data set (Figure S4). In order to increase the robustness of the automatic S-wave arrival picks, we supplement the REST S-picks by applying the non-parametric auto-picking algorithm kpick (Rawles & Thurber, 2015) to the 2765 events selected. The algorithm uses a ratio of the similarity of a given trace to a set of ‘positive’ reference waveforms (i.e., containing real picks), to the similarity of the trace to a set of ‘negative’ reference waveforms (i.e., containing P-wave coda or a flat horizontal line). Our set of reference waveforms includes 10 positive traces with good S-wave manual picks, whereas the negative traces consist of a horizontal line. Traces were bandpass filtered between 2 and 20 Hz with a Butterworth filter. Examples of S-wave auto-pick results for one event are shown in Figure S5.

The slope of the L1-norm fit to the measurements in the Wadati diagram of Figure S5b is used to assess the quality of the S-wave picks made by kpick. Any point outside the lines with slope +/- 0.2 away from that of the L1-norm fit is considered erroneous and removed. Overall, kpick S-picks are in good agreement with hand-picked arrivals, with approximately 78% of the newly auto-picked S-wave arrivals being within 0.5 s of the manual picks, and ~51% within 0.2 s of the manual picks. This is comparable to typical S-wave picking uncertainties (e.g., Rawles and Thurber, 2015).

Using the kpick algorithm, we identified 16,245 additional S-wave arrival times and 1,599 additional P-wave arrival times. We applied a further quality control to exclude all the picks with estimated arrival time uncertainty greater than 0.6 s for both the kpick S-picks and the original 91,659 REST S-wave picks, as well as excluding all the un-paired S-wave arrivals, and applying an unweighted absolute residual (Tobs - Tcalc) constraint of less than 2.0 s. Limiting the uncertainty and restricting the arrival time picks only to P and S pairs resulted in ~32% fewer S-phases, for a total of 73,783 high quality S-picks to be used for our location analysis. Applying a slightly lower residual travel time threshold (0.2 s) reduced the total 119,167 P-wave picks (REST P-wave picks + kpick P-wave picks) to 114,140 high-quality P picks (~96%).

Text S2. Non-linear earthquake relocation inversion (NonLinLoc)

The subset of 632 events we analyzed at the beginning of this study utilizing the available reviewed events from GeoNet at the time was also used to perform a probabilistic non-linear global-search using the NonLinLoc (NLLoc) inversion approach of Lomax et al. (2006). The location method uses an Equal Differential Time minimization method and an Oct-tree nested search to sample the parameter space. Locations computed using NLLoc mirror the simul2014 and HypoDD locations where the station coverage is good (near Cape Campbell), but tend to move offshore and deeper than the simul2014 and hypoDD locations near Kaikōura (Figure S6, see Figure 2 in the main manuscript for simul2014 and hypoDD locations).

In order to understand the disagreement between the location algorithms, we select a set of 53 events located in the Kaikōura and epicentral regions where the location algorithms show the most disagreement, and perform in-depth pick quality assessment and NLLoc parameter testing. In general, the picks are reasonable. Different NLLoc parameters (i.e., effective distance weighting) shows that NLLoc is fitting nearby stations poorly, and outputs high location uncertainties, especially for depth. Allowing 40% model-related uncertainty due to path-length, removing more distant picks, and adding nearby S picks seems to improve the location (the epicenters of the tested events become more consistent with simul2014), but the depths still show large uncertainties (Figure S7) and the fits to the phase arrivals perform poorly (Figure S8). We suspect the poorer fits to the data might be related to poorer resolution in the velocity model used in this particular area.

Based on these tests, we comment here regarding the large discrepancies in the mainshocks location that has been proposed by different groups: for example, Nicol et al. (2018) and Mouslopoulou et al. (2019), argue that the earthquake nucleated on a south dipping fault, while this study is more consistent with a northward dipping structure (see section 5.1 in the main text). We believe that the cause of the difference is likely to due to the location program used. As we show, NonLinLoc, which is the standard location software used by GeoNet, does a poor job of locating earthquakes in the region south of Kaikoura. This includes the mainshock region. Starting relocations with a poor initial location will result in poor relocations: the relocations computed by Nicol et al. (2018) use a similar starting location to the GeoNet location, so the relocation is similar to the initial location.

Text S3. Location bias

In order to assess the possibility of any bias between the aftershock relocations obtained when using both the GeoNet and STREWN networks with respect to those obtained when using the GeoNet network only, we relocated the aftershock sequence excluding the STREWN stations. We then assess the change in latitude, longitude and depth considering first all the events together and secondly, dividing the relocated events into three separate groups progressively distant from where the STREWN stations are located. For each group, from the closest to the STREWN stations (group 1) to the farthest (group 3), we show histograms of the changes in latitude, longitude and depth in Figure S11. Ideally, the effect of the STREWN stations should decrease as we go from group 1 to group 3. The overall average change in depth corresponds to ~0.013 km, with changes of ~0.005 km, ~0.105 km and ~0.083 km for group 1, 2 and 3, respectively. Similarly, the overall average change in latitude corresponds to ~0.047 km, with changes of ~0.050 km, ~0.056 km, and ~0.031 km for group 1, 2 and 3, respectively. Lastly, the overall average change in longitude is ~0.046 km, with changes of ~0.091 km, ~0.032 km, and ~0.010 km for group 1, 2 and 3, respectively. We conclude that, by including versus excluding the contribution from STREWN network, there is little or no bias in the obtained relocations.

Text S4. Absolute location errors

We here attempt to estimate the absolute error associated with the 2655 event locations obtained with simul2014. Following Pavlis (1986), the hypocenter error is bounded as:

(1)

where s is a vector of path lengths, and is a priori slowness uncertainty. We can then write:

(2)

where T means transpose. This is comparable to the equation for hypocenter uncertainty due to pick uncertainty :

(3)

where we generally assume is the misfit or the misfit plus some a priori additional constant.

Therefore, to get the hypocenter uncertainty from the model uncertainty, we can divide the standard errors by the RMS residual and then multiply that by the average path length times the a priori model error estimate . This rough calculation will give us an upper bound estimate of the absolute errors.

If, for an a priori slowness uncertainty, we consider a slowness value of 0.2 s/km (which corresponds to 5 km/s), we can assume a reasonable value for of ~0.02 s/km. Figure S12 shows a histogram of the estimated absolute uncertainties for each of the 2655 events relocated with simul2014. Except for few outliers, most of the events shows uncertainties due to the model of less than 2 km.

Text S5. Choosing thresholds for the double-difference analysis and their influence on the locations

The choice of thresholds for the double-difference analysis is somewhat arbitrary. We have sufficiently dense seismicity that we can choose a relatively small inter-event separation and still retain a large portion of our original catalog. Choosing a larger inter-event distance would likely allow us to relocate more events, but at the expense of larger uncertainty due to velocity model heterogeneities: the double-difference relocation method assumes that there is little to no velocity variation between neighboring events, so allowing larger inter-event distances would tend to invalidate this assumption. Choosing smaller inter-event separations would result in the relocation of a smaller subset of our catalog and a coupled increase in uncertainty as the number of observations is reduced. Similarly, if we increased the cross-correlation threshold, we would see a reduction in event numbers and increase in uncertainty. We chose a cross-correlation threshold that produced stable lags, with similar but more precise relative arrival times compared to the differential times calculated from our automatic picks. We have not undertaken extensive testing to find the optimum density of relocations, however, we are satisfied with the uncertainties obtained from our final catalog, and the number of events in the catalog which allow us to make useful observations on the nature of the faults.

Text S6. Note on the role of the subduction interface in the post-seismic phase

We briefly comment here on the possible later seismic involvement of the subduction interface. Mouslopoulou et al. (2019) have recently suggested a role reversal during the post-seismic phase, where the plate interface is showing important transients in the later phase. However, from our relocation study, the occurrence of only eight aftershocks on or near the subduction interface makes it difficult to discern any temporal pattern or direct relationship to afterslip. The first of these aftershocks occurs about 11 hours after the main shock, ruling out direct dynamic triggering by the main shock. We infer that this event (as well as the other seven) was triggered by afterslip. The subsequent aftershocks in this area occurred at intervals ranging from a bit under three hours (the second event) to nearly two and a half months (Figure 4, Table S2). There is an interesting pattern of 2 days, 23 days, 23 days, and 2 days between events 2, 3, 4, 5, and 6, but there is no physical process we can think of that would cause such a pattern, so we presume that it is most likely random.

References

Allen, R. (1982). Automatic phase pickers: Their present use and future prospects, Bull. Seismol. Soc. Am., 72, S225–S242.

Anant, K.S., & Dowla, F. U. (1997). Wavelet transform methods for phase identification in three-component seismograms, Bull. Seismol. Soc. Am., 87, 1598–1612.

Baillard, C., Crawford, W. C., Ballu, V., Hibert, C., & Mangeney, A. (2014). An automatic kurtosis-based P- and S-phase picker designed for local seismic networks, Bull. Seismol. Soc. Am., 104, 394–409. https://doi.org/10.1785/0120120347.

Bensen, G. D., M. H. Ritzwoller, M. P. Barmin, A. L. Levshin, F. Lin, M. P. Moschetti, N. M. Shapiro, and Y. Yang (2007). Processing seismic ambient noise data to obtain reliable broad‐band surface wave dispersion measurements. Geophys. J. Int., 169, 1239-1260. doi:10.1111/j.1365-246X.2007.03374.x

Gentili, S., & Michelini, A. (2006). Automatic picking of P and S phases using a neural tree, Journal of Seismology, 10, 39–63. https://doi.org/10.1007/s10950-006-2296-6.

Kushnir, A. F., Lapshin, V. M., Pinsky, V. I., & Fyen, J. (1990). Statistically optimal event detection using small array data, Bull. Seismol. Soc. Am., 80, 1934–1950.

Leonard, M., & Kennett, B.L.N. (1999). Multi-component autoregressive techniques for the analysis of seismograms, Phys. Earth Planet. Inter., 113, 247-263, https://doi.org/10.1016/S0031-9201(99)00054-0

Lomax, A., Michelini, A., & Curtis, A. (2009). Earthquake location, direct, global-search methods, Meyers, R. A. (ed.) in Encyclopedia of Complexity and System Science, Part 5, Springer, New York, 2449-2473, doi:10.1007/978-0-387-30440-3.

Mouslopoulou, V., Saltogianni, V., Nicol, A., Oncken, O., Begg, J., Babeyko, A., et al. (2019). Breaking a subduction-termination from top to bottom: The large 2016 Kaikōura Earthquake, New Zealand, Earth Planet. Sci. Lett., 506, 221-230, doi: https//doi.org/10.1016/j.epsl.2018.10.020

Nicol, A., Khajavi, N., Pettinga, J. R., Fenton, C., Stahl, T., Bannister, S., et al. (2018). Preliminary geometry, displacement, and kinematics of fault ruptures in the epicentral region of the 2016 Mw 7.8 Kaikōura, New Zealand, earthquake, Bull. Seismol. Soc. Am.,108, 1521-1539, doi: 10.1785/0120170329.

Pavlis, G. (1986). Appraising earthquake hypocenter location errors: a complete, practical approach for single-event locations, Bull. Seismol. Soc. Am., 76, 1699-1717.

Rawles, C., & Thurber, C. H. (2015). A non-parametric method for automatic determination of P-wave and S-wave arrival times: application to local micro earthquakes, Geophys. J. Int., 202, 1164–1179, https://doi.org/10.1093/gji/ggv218.

Roecker, S., Thurber, C. H., Roberts, K., & Powell, L. (2006). Refining the image of the San Andreas Fault near Parkfield, California using a finite difference travel time computation technique, Tectonophysics, 426, 189-205.

Ross, Z. E., White, M. C., Vernon, F. L., & Ben-Zion, Y. (2016). An improved algorithm for real-time S-wave picking with application to the (augmented) ANZA network in Southern California, Bull. Seismol. Soc. Am., 106, 2013-2022, https://doi.org/10.1785/0120150230.

Ross, Z. E., Meier, M., & Hauksson, E. (2018). P-wave arrival picking and first-motion polarity determination with deep learning, J. Geophys. Res., 123, 5120-5129, https://doi.org/10.1029/2017JB015251.

Sleeman, R., & van Eck, T. (1999). Robust automatic P-phase picking: an on-line implementation in the analysis of broadband seismogram recordings, Phys. Earth Planet. Int., 113, 265–275. https://doi.org/10.1016/S0031-9201(99)00007- 2.

Wang, J., & Teng, T. (1997). Identification and picking of S phase using an artificial neural network, Bull. Seismol. Soc. Am. 87, 1140–1149.

Figures

Figure S1. Map of seismograph stations used in the aftershock relocation analysis, including GeoNet permanent stations (shown as inverted triangles), GeoNet strong motion sensors (squares) and stations from the STREWN temporary deployment (diamonds). We excluded some of the strong-motion sites after extensive manual analysis revealed poor data quality and/or inaccurate timing. The STREWN array was equipped with 10 3-component broadband sensors (Trillium Compact and Trillium PH at 120s corner period) and 14 3-component short-period sensors (Lennartz LE-3DliteMK2, Geospace HS-13C, and Sercel L22). Data were recorded on 17 Reftek 130 and seven Taurus digitizers operating in continuous mode at 100 samples per second and equipped with Global Positioning Systems (GPS) timing. SP –Short Period sensors; BB –Broadband sensors.

Figure S2. Example of onset estimation functions for P and S waves. The 3-component seismogram is shown in the top three panels. 0 denotes the start time of the estimation window for S and P in the lower two panels.

Figure S3. Auto-pick error plotted against the time difference between the manual and automatic picks. Red pluses mark events M > 4.0 (code: MK – analyst initials) whereas blue crosses mark events 3.0 < M < 4.0 (code: HJG). Dashed line marks exact equality between the difference in manual and automatic pick times and assigned auto-pick uncertainty. Red and blue percentages denote proportions of valid (below dashed line) and unacceptable (above line) picks for each subset.

Figure S4. Scatter plots of deviation between the REST automatic and analyst pick as a function of S-P time for (a) P-wave picks, and (b) S-wave picks. Cumulative histograms are shown at the top and side edges.

Figure S5. Results of S-wave kpick auto-picking for one event in the Cape Campbell aftershock cluster (orange star in the map – panel a). b) Comparison of manual, kpick and REST P- and S-wave arrivals as a function of distance. c) Wadati plot: white circles indicate the P-wave picks versus the difference between P-wave and S-wave auto-picks on all stations. Red circles represent discarded picks. d) S-wave auto-picking results for selected stations. North component is used.

Figure S6. Map view and cross-sections of the earthquake relocations using NonLinLoc. Relocated background seismicity from 2001 to 2011 (blue circles) is from Eberhart-Phillips et al. (2014). For the cross-sections, each panel shows projected earthquakes with a maximum distance of 20 km from the cross-section line, and the rightmost panels are zoom within cross-sections along the same profile as indicated by the dashed box in the center panels. Red star indicates the Kaikōura hypocenter from the initial GeoNet catalog and blue solid lines indicate the subduction interface contours from Williams et al. (2013).

Figure S7. Location plot for test event 2016p959735. NonLinLoc location is the best-fitting from our parameter tests using LOC GAU 0.4 (40% model uncertainty), removing picks from the 21 most distant stations and adding additional S-phase picks manually. Black circles mark the scatter cloud from NLLoc. The NLLoc location is plotted as a red star and the simul2014 location as a cyan star.

Figure S8. Example of NonLinLoc poor data fits for test event 2016p959735. NonLinLoc location is the best-fitting from our parameter tests as plotted in Figure S7. Plotted are waveforms of a few nearby stations with pick times (dashed lines) and calculated arrival times (solid lines).

Figure S9. Heat map of the final relocations obtained with HypoDD.

Figure S10. a), b), c). Spatial distribution of the hypoDD relocation uncertainties in the model-aligned x, y, and z directions, respectively. Arrows indicate the model-aligned directions x, y, and z (vertical).

Figure S11. Histograms showing the change in latitude, longitude and depth between the aftershock locations obtained when using both the GeoNet and STREWN network and those obtained when using the GeoNet network only. Group 1 includes all events north of latitude -42° (closer to the STREWN network); Group 2 includes events with latitude comprises between -42° and -42.4°, and Group 3 includes events south of latitude -42.4° (farthest away from the STREWN network).

Figure S12. Histogram showing the distribution of the absolute location uncertainties for all the 2655 events relocated with simul2014. Bottom panel is a zoom-in of the upper panel.

Figure S13. 3D perspective views showing the simplified Hope Fault after Litchfield et al. (2018), and the clustered aftershock relocations color coded by date of occurrence. Red lines indicate faults that ruptured during the mainshock.Tables

Tables S1. Station list used in both picking and relocation analyses. File uploaded separately.

Table S2. Focal mechanisms slip vectors and standard errors for the eight interface events. Solutions are reported for the hypoDD depths

Movie S1. 3D visualization of the relocated aftershock sequence. Fault planes are from Litchfield et al. (2018). File uploaded separately (ms01).

Data Set S1. Catalog of relocated hypocenter data and pick times (QuakeML format). File uploaded separately (ds01).
