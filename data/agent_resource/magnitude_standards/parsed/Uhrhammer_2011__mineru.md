Ⓔ

# California Integrated Seismic Network (CISN) Local Magnitude Determination in California and Vicinity

by R. A. Uhrhammer, M. Hellweg, K. Hutton, P. Lombard, A. W. Walters, E. Hauksson, and D. Oppenheimer

Abstract Determining local magnitude $( M _ { \mathrm { L } } )$ in a manner that is uniform and internally consistent for earthquakes throughout California and the vicinity is an important component of the California Integrated Seismic Network (CISN). We present a new local magnitude attenuation function and corresponding station adjustments that are valid throughout California. The new attenuation function is an analytic function of the radial hypocentral distance between 1 and 500 km. Associated station adjustments are also available for 1185 horizontal seismometer and accelerometer channels from five seismic networks operating in California. The new attenuation function and adjustments provide several advantages to CISN. They allow a more robust $M _ { \mathrm { L } }$ computation, the $M _ { \mathrm { L } } \mathrm { s }$ are more consistent between northern and southern California than they have been in the past, and because adjustments are now available for more station-network-channel-location codes (SNCLs), $M _ { \mathrm { L } } \mathrm { s }$ can be computed for small earthquakes in more locations than was previously possible. In addition to describing our method for calibrating the new CISN $M _ { \mathrm { L } }$ , we also present a tool for adding adjustments for new or upgraded stations.

Online Material: Map of candidate earthquakes, stations, and associated dML values, tables of candidate events and dML adjustments, and FORTRAN software.

## Introduction

Since Richter (1935) and Gutenberg and Richter (1942) developed the local or Richter magnitude $( M _ { \mathrm { L } } )$ scale for earthquakes in southern California using records from Wood–Anderson (<sub>WA</sub>) seismographs, $M _ { \mathrm { L } }$ has been used to describe earthquake sizes in the catalogs of both northern and southern California. To maintain historical consistency, it is important to continue to report local magnitude. Different amplitude decay functions $\left( - \log A _ { 0 } \right)$ have, however, been used for some time in each region (Uhrhammer et al., 1996, Kanamori et al., 1999). With each change in instrumentation and each addition of a station, careful calibration procedures were necessary to ensure catalog continuity. Now, many digital broadband stations and strong-motion stations have been added to the networks in both northern and southern California but have not yet been calibrated. The institutions charged with monitoring earthquakes in the state of California, the Seismological Laboratories of the University of California Berkeley (UCB), the California Institute of Technology (Caltech), and the U.S. Geological Survey offices in Menlo Park and Pasadena (USGS-MP and USGS-P), have joined with the California Integrated Seismic Network (CISN) to provide earthquake information to various agencies and institutions as well as to the public.

The need to include the new stations in $M _ { \mathrm { L } }$ determination and the desire to unify magnitude reporting led to this project, which aims to define $\mathrm { ~ a ~ } - \log A _ { 0 }$ function that is valid throughout the entire state and to determine associated channel adjustments for horizontal channels from both broadband and strong-motion sensors.

In our analysis, which provides a historically consistent, statewide method for determining the local magnitude of earthquakes, we opted not to use absolute magnitudes for the calibration. An absolute calibration would require the arbitrary selection of one site as the origin. Instead, we chose a differential approach in which the differences in local magnitudes for a suite of earthquakes for each possible pair of channels (excluding channels oriented the same direction at a station) were inverted in two steps. First, a new statewide $- \log A _ { 0 }$ function was determined. For this inversion,  <sup>log</sup> $A _ { 0 } ( 1 0 0$ km was constrained to be 3.0 to match Richter’s (1935) original definition. In addition, the sum of $d M _ { \mathrm { L } } ( { \mathrm { S N C L } } )$ for a set of stations that have been operating for most of the catalog interval was constrained to match their historical sum. In the second step, channel adjustments were calculated for all horizontal components, both broadband seismometers and accelerometers.

## Candidate Earthquakes

A list of candidate earthquakes was developed from the Advanced National Seismic System (ANSS) online earthquake catalog (see the Data and Resources section) for 2000 through 2006. This catalog provides a composite list that includes both northern and southern California events. To achieve a relatively uniform coverage of event-station pairs, California and the neighboring regions were divided into grid squares of $5 0 \times 5 0$ km (Fig. 1; a high-resolution version is available in Ⓔthe electronic supplement to this paper). From each square, two events were selected if possible: the largest event with $M _ { \mathrm { L } } \geq 3$ in the interval 2000–2006 and the largest earthquake with $M _ { \mathrm { L } } \geq 3$ from the year 2006. The requirement that the candidate events have $M _ { \mathrm { L } } \geq 3$ ensured that each event has a good signal-to-noise ratio (SNR) at many stations. The events from 2006 were added to provide data from recently installed stations and from the Transportable Array Stations of the USArray (see the Data and Resources section), a component of the Earthscope project (http://www .earthscope.org/) funded by the National Science Foundation. If the largest earthquake in any grid square took place in 2006, then the second largest event from 2000–2006 from that grid square was added to the set. This procedure netted

![](images/891df22999285b47fef44ca049b5a8a34d1315d6fde851503f79f357c7ff25d9.jpg)  
Figure 1 This map shows the study area including candidate earthquakes (small gray circles), candidate stations with both broadband and strong-motion sensors (large colored circles), and the $5 0 \times 5 0$ km grid (dotted lines) used for selecting the earthquakes. The candidate earthquakes are given in Appendix A in Ⓔthe electronic supplement to this paper. Stations with only strong-motion sensors are not shown on the map for clarity. The colors of the vertical (north component) and horizontal (east component) lenses superimposed on the station symbols give the magnitude of the CISN SNCL adjustment $( d M _ { \mathrm { L } } )$ as shown on the color scale. The CISN SNCL $d { \bar { M } } _ { \mathrm { { L } } }$ are given in the Appendix B in Ⓔthe electronic supplement to this paper. The magnitude of the CISN $d M _ { \mathrm { L } }$ correlates with the competence of the soil/rock on which the station is sited. Hard rock sites have large positive $d \boldsymbol { M _ { \mathrm { L } } }$ values, and very soft soil sites have large negative $d M _ { \mathrm { L } }$ values. Stations in the region 8 of the LA Basin are shown in the insert at a larger scale.

253 candidate earthquakes (See Appendix A in Ⓔthe electronic supplement to this paper and Fig. 1).

## Candidate Horizontal Channels (SNCLs)

In 2006, five networks operated broadband and strongmotion seismic stations in California that contributed to realtime earthquake monitoring:

• The Anza network operated by the University of California San Diego (abbreviation ANZA, network code AZ).

• The Berkeley Digital Seismic Network operated by <sub>UCB</sub> (BDSN, BK).

• The Southern California Seismic Network operated by Caltech and the USGS-P (SCSN, CI).

• The Northern California Seismic Network operated by the USGS-MP (NCSN, NC).

• The Transportable Array operated by the USArray component of Earthscope (USArray, TA).

From these networks, a list of 1230 candidate broadband and strong-motion horizontal channels (each designated by its station-network-channel-location code or SNCL) was compiled (Fig. 1 and Appendix B in Ⓔthe electronic supplement to this paper). All channels are recorded digitally with high resolution (24-bit integer) at sampling rates of 20–100 samples per second. Data from the SNCLs were acquired as described in the Data and Resources section.

## Candidate Waveforms

We compiled a list of candidate waveforms by reviewing the following criteria for each combination of candidate earthquake and candidate SNCL:

• Is the distance from the hypocenter to station 700 km?

• Is the theoretical maximum trace amplitude for the event on a WA seismograph ≥<sup>0:03</sup> mm?

These criteria were chosen to select for good SNR. Approximately 100,000 waveforms met all criteria and were extracted for this study. The time window for the data extracted from the archives for each waveform started 30 s prior to the theoretical P-wave onset and ended 60 s after a 2-km=s wave would have arrived at the station.

## Data Processing

Prior to decommissioning the last WA seismographs with photographic recording in the BK network of northern California in early 1993, we demonstrated that equivalent, synthetic WA seismograms could be generated accurately from digitally recorded broadband or strong-motion waveforms via convolution (Uhrhammer and Collins, 1990; Uhrhammer et al., 1996). The empirically determined WA transfer function is equivalent to an inertial pendulum with a free period of 0.8 s, a damping coefficient of 0.7 critical, and a static magnification of 2080. It is important to note that the value for the WA static magnification is 2080 and not 2800 as originally reported by Anderson and Wood (1925) and commonly used since that time. While this difference is unimportant when using amplitudes measured from the original WA sensors, it is crucial when producing synthetic WA seismograms. If the correct magnification value is not used, $M _ { \mathrm { L } }$ estimates will be low by $0 . 1 2 9 M _ { \mathrm { L } }$ The error apparently occurred because Anderson and Wood (1925) incorrectly assumed that the taut-wire suspension used in the WA sensor did not deflect from a straight line. The deflection is actually sufficient to increase the polar moment of inertia and lower the static magnification by approximately 30% (Uhrhammer and Collins, 1990). Theoretically, a synthetic WA seismic record has an approximately 80-dB greater dynamic range than can be measured on a photographic WA seismogram. In practice, however, the difference is closer to 44 dB. The seismic background noise limits resolution at low signal amplitudes, and the linearity of the sensors limits it at high amplitudes.

For this important reason, we produced our own set of WA amplitudes, starting with the raw data rather than using WA amplitudes extracted from the northern and southern California event catalogs for the selected events and SNCLs. For several years, the WA amplitudes were calculated using different algorithms in each part of the state (Uhrhammer et al., 1996, Kanamori et al., 1999). For the analysis to be valid, it required that the WA amplitudes be determined in a uniform way, producing a consistent set for comparison.

For our analysis, each time series was preprocessed in the time domain before being converted to a synthetic WA seismogram in the frequency domain. The mean was removed from each record, and it was windowed to minimize contamination of the data by spurious amplitudes. The preprocessed waveforms for each earthquake were (1) converted to the frequency domain using a fast Fourier transform FFT; (2) filtered using a 0.5–10 Hz, 6-pole Butterworth band-pass filter; (3) transformed into a synthesized WA seismogram by deconvolution of the instrument response and the convolution with the empirical WA transfer function (Uhrhammer et al., 1996); (4) transformed into the time domain; and (5) automatically scanned to pick the maximum trace amplitude, A. All the WA maximum amplitudes, A, were indexed by SNCL and event and stored in a file for further processing. The band-pass filter was applied to reduce contamination of the waveforms by microseisms or surface waves at low frequencies and by noise spikes at high frequencies. Figure 2 shows an example of the waveform processing for a local event riding on the surface waves ofthe 27 February 2010 $M _ { \mathrm { w } }$ 8.8 Maule earthquake in Chile. The waveform for this $M _ { \mathrm { L } }$ 2.7 local earthquake, which occurred 66 km north of the recording station ORV, is nearly invisible in the original record but has a good SNR after the waveform processing. It is our experience that the frequencies associated with the maximum trace amplitudes recorded by standard WA torsion seismographs predominantly occur in the 2- to 4-Hz frequency band and rarely at frequencies either below 1 Hz or above 6 Hz.

Data from the amplitude file was again winnowed using period and amplitude criteria that depended on whether the data came from a broadband sensor or from an accelerometer. The period selection criteria effectively rejected data contaminated by low-frequency waves or glitches. The amplitude criteria ensured that the WA maximum trace amplitudes were unlikely to be due to noise and also that the sensor was responding linearly to the ground motions (i.e., the feedback electronics was not saturated or clipped). For the broadband sensors, A was required to be in the range 0.3–650 mm; for accelerometers, the range was 3– 12,000 mm. The maximum WA trace amplitudes that met these selection criteria were used in the subsequent analysis.

(a)  
![](images/94ebaa4f6c4705382961043eab56fa95c985affd1611900246dbcfcb3d150d42.jpg)

(b)  
![](images/3b24f59eb8fd7e7d0018cf4934b1bdce6dce21cdd3e1010d616a4646603e8042.jpg)

(c)  
![](images/6eb50369809661e9f32b157b630da762dcb76be9dc55387d5cea8296179039c9.jpg)  
Figure 2 Example of waveform processing showing (a) the raw ORV.BK.HHE broadband data, (b) the corresponding synthesized WA data, and (c) the synthesized WA record band-pass filtered with a 0.2- to 10-Hz, 6-pole Butterworth filter to remove microseismic background and long-period surface-wave signal contamination. The local event is an $M _ { \mathrm { L } }$ 2.7 earthquake located 66 km north of ORV, riding on the wavefield of the 27 February 2010 $M _ { \mathrm { w } }$ 8.8 Maule earthquake in Chile.

## Initial Analysis: The Differential Dataset and  log A<sub>0</sub> r

The differential dataset inverted is not formed directly from differences of the maximum WA trace amplitudes, A, but by differences of $M _ { \mathrm { L } }$ determined from A. To do this, we fundamentally followed the procedures for determining $M _ { \mathrm { L } }$ originally defined by Richter (1935) with one change. To determine the attenuation function, Richter relied on the determination of the epicentral distance from the earthquake to the station and assumed the event’s hypocentral depth to be 15 km, a more or less reasonable average value for southern California. This biased magnitudes that were measured at short hypocentral distances where $M _ { \mathrm { L } }$ is overestimated. For the formulation of the CISN attenuation function, we adopted the use of hypocentral distance (r) rather than epicentral distance to facilitate the accurate determination of $M _ { \mathrm { L } }$ at close distances.

Local magnitude for a given channel is thus defined as

$$
M _ {\mathrm{L}} = \log (A) - \log A _ {0} (r) + d M _ {\mathrm{L}},\tag{1}
$$

where A is the maximum WA trace amplitude, measured in millimeters, r is the hypocentral distance in kilometers, and $d M _ { \mathrm { L } }$ is the station or SNCL adjustment. Given the hypocentral distance for each earthquake–<sub>SNCL</sub> pair, we calculated the $M _ { \mathrm { L } }$ corresponding to the WA maximum trace amplitude, A, using the analytical attenuation function derived from Richter’s (1935) attenuation function (Kanamori et al., 1993):

$$
- \log A _ {0} (r) = 1. 1 1 \times \log (r) + 0. 0 0 1 8 9 \times r + 0. 5 9 1.\tag{2}
$$

Then, for each earthquake i, we determined the differences between the $M _ { \mathrm { L } }$ estimates for all SNCLs, $j , k ( j \neq k )$ , that recorded that earthquake:

$$
\Delta M _ {\mathrm{Li}, j k} = M _ {\mathrm{Li}, j} - M _ {\mathrm{Li}, k}.\tag{3}
$$

The result was a differential dataset with approximately 11.6 million observations for all earthquakes and SNCLs. This differential $M _ { \mathrm { L } }$ dataset was used in the inversions. The primary advantages of using a differential dataset are that the true $M _ { \mathrm { L } }$ of the earthquakes need not be known and that all observed differential $M _ { \mathrm { L } } \mathrm { s }$ contribute to the solution.

Subsequently, we performed a number of inversions using a constrained least-squares method to solve simultaneously for various discrete and analytical forms of perturbations to the analytical attenuation function (equation 2), and for corresponding SNCL $d M _ { \mathrm { L } } \mathbf { s } .$ . Only one constraint was supplied for the attenuation function in all inversions. We required that log $A _ { 0 } ( r = 1 0 0 ~ \mathrm { k m } ) = 3 . 0$ conform to Richter’s (1935) original concept that an $M _ { \mathrm { L } }$ 3 earthquake will have a maximum WA trace amplitude of 1 mm at a distance of 100 km. Various constraints for the station adjustments were tested, generally using combinations of selected BK and CI network stations for which historical $d M _ { \mathrm { L } } s$ existed. Both regional (northern and southern California) and global (statewide) perturbations to the attenuation function were determined along with the corresponding SNCL $M _ { \mathrm { L } }$ adjustments.

After numerous inversions, it was found that the sim plest attenuation perturbation function form that fit the observed data statewide, in a constrained least-squares sense, was a linear combination of the initial analytic function (equation 2) and a sixth-order Chebyshev polynomial (Fig. 3). The form for the new $- \log A _ { 0 } ( r )$ function is

$$
\begin{array}{c} - \log A _ {0} (r) = 1. 1 1 \log (r) + 0. 0 0 1 8 9 r \\ + 0. 5 9 1 + \mathrm{TP} (n) \times T (n, z), \end{array}\tag{4}
$$

where n is summed from 1 to 6. The TP n coefficients are

$$
\begin{array}{l l} \text {TP(1) = +0.056,} & \text {TP(2) = -0.031,} \\ \text {TP(3) = -0.053,} & \text {TP(4) = -0.080,} \\ \text {TP(5) = -0.028,} & \text {TP(6) = +0.015,} \end{array}
$$

and z is the scale transformation of $r ,$

$$
z (r) = 1. 1 1 3 6 6 \times \log (r) - 2. 0 0 5 7 4,\tag{5}
$$

that transforms $( 8 \leq r \leq 5 0 0 )$ to $( - 1 \leq z \leq + 1 )$ , and $T ( n , z )$ is the Chebyshev polynomial

![](images/17925306c5679de8dc7799da67c11ba2dff8b7c07261782445e67220aec04edd.jpg)  
Figure 3 Comparison of $- \log A _ { 0 } ( r )$ attenuation functions. The CISN function was developed during this project; the other two have been used in southern California (Caltech, CI), and northern California (Berkeley, UCB), respectively. All three attenuation functions are constrained so that log $A _ { 0 } ( 1 0 0$ km $= = 3$ . The CISN attenuation function is only valid to 500 km, and at distances shorter than 8 km, the function is an extrapolation of the average slope between 8 and 60 km (see Appendix C in Ⓔthe electronic supplement to this paper).

$$
T (n, z) = \cos (n \times a \cos (z)).\tag{6}
$$

This form of log $A _ { 0 } ( r )$ was found to provide a robust fit to the decay of earthquake amplitude as a function of hypocentral distance between 8 and 500 km (Fig. 3). In this case, robustly means that the good fit was relatively independent of the constraints on $d M _ { \mathrm { L } }$ and that this  log $A _ { 0 } ( r )$ formulation ultimately resulted in a 50% variance reduction. At hypocentral distances greater than 500 km, there were only a few differential amplitude values. This is mainly due to the fact that only a few of the events included in the analysis had magnitudes greater than five and, thus, only a few were measurable amplitudes at great distances. We therefore capped the definition of $- \log A _ { 0 } ( r )$ at 500 km. Likewise, for hypocentral distances less than 8 km, there were only a few differential amplitude values. For hypocentral distances shorter than 8 km, the average slope of  log $A _ { 0 } ( r )$ between 8 and 60 km was linearly extrapolated to 0.1 km. The resulting $- \log A _ { 0 } ( r )$ at distances less than 8 km is lower than either Richter’s (1935) or Kanamori’s $( 1 9 9 9 ) - \log A _ { 0 } ( r )$ , and it produces consistent $M _ { \mathrm { L } }$ estimates with smaller variances at short hypocentral distances. Thus, both broadband and strong motion estimates of $M _ { \mathrm { L } }$ at short distances will be more reliable, and also, $M _ { \mathrm { L } }$ can be reliably calculated for smaller earthquakes recorded at short distances.

The FORTRAN function given in Appendix C in Ⓔthe electronic supplement to this paper implements the above5 algorithm and has been adopted for the $\mathrm { C I S N } - \log A _ { 0 } ( r )$ attenuation function.

## Subsequent Analysis: Station (Component) Adjustments or $d M _ { \mathrm { L } }$

After adopting the CISN log $A _ { 0 } ( r )$ , we focused on determining the set of channel adjustments most consistent with past practices in northern and Ssouthern California. The $d M _ { \mathrm { L } }$ (SNCL) were determined using a linear least-squares fit. We discussed and tested a large suite of constraints before settling on one. We agreed that the sum of $d M _ { \mathrm { L } } ( { \mathrm { S N C L } } )$ for a set of stations that have been operating for most of the catalog interval $( 6 0 + \mathrm { ~ y r } )$ should be constrained to match their historical sum. For southern California, nine SNCLs were chosen that are operating WA instruments and are now equipped with broadband seismometers (PAS.CI.HHE, PAS. CI.HHN, BAR.CI.HHN, MWC.CI.HHE, MWC.CI.HHN, PLM.CI.HHE, PLM.CI.HHN, RVR.CI.HHE and RVR. CI.HHN). Northern California only has three WA stations that now host broadband seismometers, with six SNCLs (BKS.BK.HHE, BKS.BK.HHN, BRK.BK.HHE, BRK.BK. HHN, MHC.BK.HHE and MHC.BK.HHN). MIN.BK, which housed WA and broadband seismometers, was closed prior to 2000. To maintain equal weighting for northern and southern California, the sum for the BK SNCLs was multiplied by 1.5. The final constraint equation was

$$
\begin{array}{l} - 0. 9 4 3 = d M _ {\mathrm{L}} (\text {PAS.CI.HHE}) + d M _ {\mathrm{L}} (\text {PAS.CI.HHN}) \\ \quad + d M _ {\mathrm{L}} (\text {BAR.CI.HHN}) + d M _ {\mathrm{L}} (\text {MWC.CI.HHE}) \\ \quad + d M _ {\mathrm{L}} (\text {MWC.CI.HHN}) + d M _ {\mathrm{L}} (\text {PLM.CI.HHE}) \\ \quad + d M _ {\mathrm{L}} (\text {PLM.CI.HHN}) + d M _ {\mathrm{L}} (\text {RVR.CI.HHE}) \\ \quad + d M _ {\mathrm{L}} (\text {RVR.CI.HHN}) + 1. 5 * ((d M _ {\mathrm{L}} (\text {BKS.BK.HHE}) \\ \quad + d M _ {\mathrm{L}} (\text {BKS.BK.HHN}) + d M _ {\mathrm{L}} (\text {BRK.BK.HHE}) \\ \quad + d M _ {\mathrm{L}} (\text {BRK.BK.HHN}) + d M _ {\mathrm{L}} (\text {MHC.BK.HHE}) \\ \quad + d M _ {\mathrm{L}} (\text {MHC.BK.HHN})). \end{array}
$$

Figure 1, as well as Appendix B in the electronic supplement to this paper, list the stations for which $d M _ { \mathrm { L } } ( { \mathrm { S N C L } } )$ were adopted in the CISN. At each site, the $d M _ { \mathrm { L } }$ for a given orientation (i.e., north or east) is valid for all components with that orientation. For example, the same $d M _ { \mathrm { L } }$ value applies for adjusting WA amplitudes measured on the east components of the broadband seismometer and of the accelerometer at BKS.BK. In a second round of calculations, $d M _ { \mathrm { L } } s$ were determined for sites that had only accelerometers. The currently valid $d M _ { \mathrm { L } } s$ are available in Ⓔthe electronic supplement to this paper.

## New SNCL Calibration

When a new broadband/strong-motion station is installed in California, the new SNCL $d M _ { \mathrm { L } }$ adjustments can be determined once a sufficient number of local/regional earthquakes that meet the amplitude selection criteria have been recorded and WA amplitudes collected. To obtain robust $d M _ { \mathrm { L } }$ estimates, we recommend using at least 30 observations per SNCL, and we also recommend that the $d M _ { \mathrm { L } }$ and its uncertainty be calculated using median statistics of the differential $M _ { \mathrm { L } }$ residuals. Thus, once sufficient data are available from a new SNCL, its $d M _ { \mathrm { L } }$ adjustment can be determined using the observed differences between the new SNCL $d M _ { \mathrm { L } }$ estimates and the $M _ { \mathrm { L } }$ estimates from stations with known $d M _ { \mathrm { L } }$ . We provide a subroutine and instructions for this procedure in Ⓔthe electronic supplement to this paper.

## CISN $M _ { \mathrm { L } }$ and $d M _ { \mathrm { L } }$ Validation

We performed several validation exercises for CISN $M _ { \mathrm { L } }$ three of which are shown and discussed here (Fig. 4). We did not compare $M _ { \mathrm { L } } \mathrm { s }$ from the catalogs for the events used here with CISN $M _ { \mathrm { L } } \mathrm { s }$ determined from the WA amplitudes used in this study. There were two main reasons for this. First, the sets of stations used for the catalog $M _ { \mathrm { L } }$ s was almost certain to be different than the sets we used. Second, the method for calculating the WA amplitudes differed, at least for southern California (Kanamori et al., 1999). We consider it important that the WA amplitudes used for these $M _ { \mathrm { L } }$ comparisons be calculated in the same way. Thus, the network $M _ { \mathrm { L } } \mathrm { s }$ shown in Figure 4 were calculated using WA amplitudes determined in this study.

The first pair of comparisons allows the evaluation of how old $M _ { \mathrm { L } } \mathrm { s } .$ for northern and southern California, respectively, compare with the new values (Fig. 4a,b). To allow the comparison, old network $M _ { \mathrm { L } }$ values were determined for events with data from northern California (BK, NC, and some TA) stations. They are calculated from the WA amplitudes used in this study, using the former Berkeley log $A _ { 0 } ( r )$ and $d M _ { \mathrm { L } }$ (Uhrhammer et al., 1996). The same was done for events with data from southern California (CI, AZ, and some TA stations), but the former Caltech $- \log A _ { 0 } ( r )$ and $d M _ { \mathrm { L } }$ (Kanamori et al., 1999) were used. Then, the old $M _ { \mathrm { L } }$ values were regressed against the network CISN $M _ { \mathrm { L } }$ values derived from the same WA amplitudes using the CISN $- \log A _ { 0 } ( r )$ and $d M _ { \mathrm { L } } \left( \mathrm { F i g . 4 a , b } \right)$ . The network $M _ { \mathrm { L } }$ is always taken to be the median value, and the uncertainties are proportional to the inverse of the number of SNCLs contributing to the $M _ { \mathrm { L } }$ value. Because the different types of $M _ { \mathrm { L } }$ have similar uncertainties, the best-fit line is determined using a bilinear regression, which minimizes the inverse-variance weighted, normal distances from each datum to the least-squares fit line. For both the northern and southern California comparisons (Fig. 4a,b), the slopes and intercepts of the best-fit lines are one and zero, respectively, to within the uncertainties. This indicates that given a consistently determined set of WA amplitudes, magnitudes determined in northern and southern California using CISN $M _ { \mathrm { L } }$ are consistent, overall, with the local magnitudes determined in the past.

(a)  
![](images/1d086ad09db1a6d6c972fd14455ea2051161a88f38235039fa18ffc3b2f8f7b0.jpg)

(b)  
![](images/c2cf30b9a0ba31dc7086242a4c4738e04c5ba29143e9ca46775a65c6014f9f1d.jpg)

(c)  
![](images/33377987cd386344c937233092e2d5da2e63285b0b16e344596bd28687f93360.jpg)  
Figure 4 Validation of CISN $M _ { \mathrm { L } }$ . (a) Comparison of $M _ { \mathrm { L } }$ determined for northern California events using CISN $M _ { \mathrm { L } }$ (horizontal axis) and UCB $M _ { \mathrm { L } }$ (vertical axis). (b) Comparison of $M _ { \mathrm { I } }$ determined for southern California events using CISN $M _ { \mathrm { L } }$ (horizontal axis) and CI $M _ { \mathrm { L } }$ (vertical axis). (c) Comparison of CISN $M _ { \mathrm { L } }$ for events determined using amplitude data from northern California (horizontal axis) and from southern California (vertical axis) SNCLs. Data are shown for 96 selected earthquakes that occurred between 2000 and 2006. The linear regression was determined using a bilinear L1- norm, and the standard error is 0.159. Thus, there are no significant differences between the $M _ { \mathrm { L } } \mathrm { s }$ of earthquakes determined using NC and $\mathrm { \bf S C }$ SNCL subsets and the CISN  log $A _ { 0 } ( r )$ and corresponding CISN $d M _ { \mathrm { L } }$ determined in this study.

A second important goal toward which the CISN networks is striving is that northern California can reliably locate and determine magnitudes for big southern California events and vice versa. Figure 4c shows a set of events for which WA amplitudes exist for both northern and southern California stations, and $M _ { \mathrm { L } }$ values for each event have been determined using either only northern California SNCLs or southern California SNCLs. As before, the uncertainties are proportional to the inverse of the number of SNCLs contributing to the magnitude. As there are usually more southern California SNCLs contributing to a magnitude, the uncertainty on the southern California $M _ { \mathrm { L } }$ is generally smaller than on the northern California $M _ { \mathrm { L } }$ . Although the scatter is larger for this set of magnitudes, overall, the slope of a bilinear-fit line and its intercept are again one and zero, respectively. This indicates that on average, northern California magnitude estimates for southern California events match and vice versa. These two validation exercises show that the goal of unifying local magnitude reporting for northern and southern California has been satisfied.

## Discussion

For historical consistency, it is important to continue to report local magnitude, as that is our connection with old catalogs. We have shown that unbiased and internally consistent local magnitudes can be determined for earthquakes occurring throughout California and the vicinity.

The CISN magnitude strategy is to provide a uniform and robust methodology for determining the local magnitude of earthquakes that occur throughout California. The determination of local magnitude continues to fill an important role for two primary reasons: (1) it provides for continuity in determination of the size of earthquakes in historical seismicity catalogs that are used for determining the rate of seismicity and the earthquake hazard, and (2) it provides a uniform and internally consistent measure of earthquake size over a broad range of ground motions.

$M _ { \mathrm { L } }$ for historical earthquakes can be recalculated using the new algorithm as far back in time as a sufficient number of digital broadband stations existed. The broadband seismometers, some of which have operated since 1986, provide a large amount of waveform data from which to compute synthetic WA amplitudes and perform the CISN calibration procedure. This effort will provide improved continuity with the older data and prevent an unnecessary discontinuity in the earthquake catalogs. Other magnitudes used, such as duration magnitude $M _ { \mathrm { D } }$ , may then be recalibrated to match the revised $M _ { \mathrm { L } } \mathrm { s }$

The $\mathrm { C I S N } - \log A _ { 0 } ( r )$ and corresponding SNCL adjust ments $( d M _ { \mathrm { L } } )$ determined in this study result in more robust estimates of $M _ { \mathrm { L } }$ with less scatter. The variance of the $M _ { \mathrm { L } }$ estimates is reduced approximately by a factor of 2 and the corresponding uncertainty in the $M _ { \mathrm { L } }$ estimates is reduced from $\pm 0 . 1 9$ to 0:14 when using the CISN methodology compared to the original methodologies employed separately by northern and southern California. The uncertainty in the CISN $M _ { \mathrm { L } }$ estimates is limited by the innate uncertainty in $M _ { \mathrm { L } }$ when amplitude variations caused by source radiation pattern and lateral crustal structure are not taken into account. In addition, $M _ { \mathrm { L } }$ estimates at short distances (< 20 km) using the $\mathrm { C I S N } - \log A _ { 0 } ( r )$ are much more robust owing to (1) the incorporation of hypocenter distance $( r )$ in place of epicenter distance (Δ) and (2) the large amount of short hypocenter distance data available for determining the log $A _ { 0 } ( r )$ . Also, there are no significant differences between $M _ { \mathrm { L } }$ determined by northern and southern California earthquake data subsets. Thus, previously noted differences between magnitudes computed in northern and southern California, for the same earthquakes, have been largely removed.

Magnitudes of very small earthquakes (< 1:5) are substantially smaller with the CISN method than previous estimations, due to the revised attenuation function for very close distances, and also due to the high-pass filter used, which excludes much of the energy from microseisms and from teleseisms from the amplitude computation. These improvements, along with the ability of the data processing software Jiggle (see the Data and Resources section) to interactively select seismogram segments for amplitude computation, allows $M _ { \mathrm { L } }$ to be estimated for much smaller earthquakes than was previously possible in areas where the networks are dense. In practice, the hypocental distances to the proximal stations limit the lower bound for robust $M _ { \mathrm { L } }$ estimation and by the size of the SNCL $d M _ { \mathrm { L } } \mathbf { s } ,$ , it is unlikely to be much below 1:0.

For consistency with Richter’s original methodology and simplicity in the calculations, scatter in $M _ { \mathrm { L } }$ due to radiation pattern was not included in this analysis. Inclusion of the radiation pattern when determining $M _ { \mathrm { L } }$ in northern California indicates that there is a slight difference in attenuation and/or SNCL $d M _ { \mathrm { L } }$ adjustments between paths that are parallel to and perpendicular to the crustal structure in northern California.

The most robust estimates of $d M _ { \mathrm { L } } ( { \mathrm { S N C L } } )$ are obtained using either mean statistics with outliers removed when large numbers of observations are available or median statistics when the dataset is small (less than 30 observations) because it is insensitive to outliers.

The improved $M _ { \mathrm { L } }$ calibration using the $\mathrm { C I S N } - \log _ { 0 } ( r )$ and $d M _ { \mathrm { L } }$ results has produced a corresponding improvement in $M _ { \mathrm { L } }$ determinations throughout the State. In southern California, where $M _ { \mathrm { L } }$ is attempted for all events, approximately 90% of the locatable events now have an $M _ { \mathrm { L } }$ . For the remaining southern California events, the data fail the acceptance criteria. In northern California, $M _ { \mathrm { L } }$ has in the past only been applied to events with $M _ { \mathrm { D } } > 3$ , mainly due to the sparse network of broadband stations. Now, with many more $M _ { \mathrm { L } }$ -qualified stations available because of the calibration, the threshold for $M _ { \mathrm { L } }$ has decreased. In the near future, we will review whether we can calculate $M _ { \mathrm { L } }$ for small events too.

Other networks in the western United States will benefit from this study if they used the same methodology and crosscalibrate with CISN to produce a uniform and internally consistent estimation of local magnitude across the entire region. A significant question is whether or not the CISN attenuation function is applicable throughout the western United States. We suspect that the CISN attenuation function will be applicable in Oregon and Washington (Qamar et al., 2003) and off Canada’s west coast (Ristau et al., 2003) and possibly in the Basin and Range province in Nevada (Savage and Anderson, 1995). However, Uhrhammer et al. (1996) found that Berkeley $M _ { \mathrm { L } }$ estimates of earthquakes occurring in the Basin and Range province were small by ${ \sim } 0 . 4 M _ { \mathrm { L } }$ when compared to the $M _ { \mathrm { L } }$ determined by the University of Nevada, Reno (UNR) and that not all of the difference could be explained solely by differences in the attenuation model.

## Data and Resources

The events analyzed in this study were selected from the ANSS Composite Catalog available at www.ncedcn.org/anss.

BK, NC, and northern California TA network waveforms were requested as SEED data volumes (www.iris.edu/manuals /SEEDManual\_V2.4.pdf) from the northern California Earthquake Data Center (NCEDC; www.ncedc.org) that is located at the Berkeley Seismological Laboratory (www.seismo .berkeley.edu) at the University of California, Berkeley. The data were requested via NetDC (www.iris.edu/manuals .netdc). Miniseed and response data were extracted via rdseed (www.iris.edu/manuals/rdseed.htm). The NetDC requests returned about 50,000 waveforms.

AZ, CI, and southern California TA network waveforms were requested in miniseed format from the Southern California Earthquake Data Center (SCEDC; www.data.scec .org) that is located at the Southern California Earthquake Center (SCEC; www.scec.org) at the University of Southern California. The data were requested via STP (www.data.scec .org/STP/STP\_Manual\_v1.01.pdf). The corresponding response information was extracted via rdseed from dataless SEED volumes downloaded from SCEC. The STP requests also returned about 50,000 waveforms.

The TA network waveforms used in this study were all recorded locally at either the NCEDC or the SCEDC. The TA data are also available from their primary archive located at the Incorporated Research Institutions for Seismology (IRIS; www.iris.edu).

Some plots were made using the Generic Mapping Tools version 4.2.0 (www.soest/hawaii.edu/gmt; Wessel and Smith, 7 2007). For more information on the USArray, see http:// www.usarray.org/. For more information on Jiggle, see pasadena.wr.usgs.gov/jiggle/.

## Acknowledgments

We acknowledge the support of this study by the California Integrated Seismic Network (CISN; www.cisn.org), the U.S. Geological Survey (USGS; www.usgs.gov), and the California Emergency Management Agency (CalEMA; www.calema.ca.gov).

## References

Anderson, J. A., and H. O. Wood (1925). Description and theory of the torsion seismometer, Bull. Seismol. Soc. Am. 15 1–72.

Gutenberg, B., and C. F. Richter (1942). Earthquake magnitude, intensity, energy, and acceleration, Bull. Seismol. Soc. Am. 32 163–191.

Kanamori, H., P. Maechling, and E. Hauksson (1999). Continuous monitoring of ground-motion parameters, Bull. Seismol. Soc. Am 89 311–316.

Kanamori, H., J. Mori, E. Hauksson, T. H. Heaton, L. K. Hutton, and L. M. Jones (1993). Determination of earthquake energy release and M using TERRAscope, Bull. Seismol. Soc. Am. 83 330–346.

Qamar, A., A. Wright, and G. Thomas (2003). Using the local magnitude scale to determine site response in the Pacific Northwest, Eos. Trans AGU 84<sub>,</sub> no. 46, Fall Meet. Suppl. Abstract S42A-0152.

Richter, C. F. (1935). An instrumental earthquake magnitude scale, Bull. Seismol. Soc. Am. 25 1–32.

Ristau, J., G. C. Rogers, and J. F. Cassidy (2003). Moment magnitude-local magnitude calibration for earthquakes off Canada’s west coast, Bull. Seismol. Soc. Am. 93 2296–2300.

Savage, M. K., and J. G. Anderson (1995). A local-magnitude scale for the western Great Basin–eastern Sierra Nevada from synthetic Wood– Anderson seismograms, Bull. Seismol. Soc. Am. 85 1236–1243.

Uhrhammer, R. A., and E. R. Collins (1990). Synthesis of Wood–Anderson seismograms from broadband digital records, Bull. Seismol. Soc. Am. 80 702–716.

Uhrhammer, R. A., S. J. Loper, and B. Romanowicz (1996). Determination of local magnitude using BDSN broadband records, Bull. Seismol. Soc. Am. 86 1314–1330.

University of California Berkeley Seismological Lab, 219 McCone Hall #4760 Berkeley, California 94720-4760 bob@seismo.berkeley.edu (R.A.U., M.H., P.L.)

California Institute of Technology Seismological Lab Pasadena, California 91125 (K.H., A.W.W., E.H.)

U.S. Geological Survey Menlo Park, California 94025 (D.O.)

Manuscript received 23 April 2010

## Queries

1. BSSA style does not allow the use of quotes around terms. Is this omission acceptable?

2. I have placed all of the web addresses listed in the text at the end of the Data and Resources section per BSSA style. Please let me know how the Data and Resources section should be worded to accommodate these web sites.

3. Is fast Fourier transform the correct spelling out of FFT?

4. BSSA uses an X to indicate multiplication instead of an asterisks. Do any of the modified asterisks indicate convolution? BSSA uses a dot for concolution. Is this change acceptable?

5. BSSA does not allow the use of “above” and “below” to indicate locations in the text. Would it be OK to cite a specific equation here or simply say “in the algorithm presented in the previous paragraph”?

6. Should “seed” in rdseed and miniseed be capitalized? I’m not familiar with these terms.

7. Can you provide the reference information for Wessel and Smith, 2007 so this information can be included in the reference list?

8. Does LA here stand for Los Angeles? Would it be all right to spell it out?

9. Is the double equal sign correct here?