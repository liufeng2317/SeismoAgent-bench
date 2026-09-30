## RESEARCH LETTER 10.1002/2017GL072944

## Key Points:

• Subspace analysis of the first month of activity increases the number of precisely located aftershocks more than fivefold

• Numerous very small aftershocks comprising 40% of the catalog and <1% of the moment are identified within the above-basement Arbuckle Group

• Aftershocks preferentially occur in low-slip regions of the Meeker-Prague fault that ruptured during the mainshock

Supporting Information:

• Data Set S1

• Data Set S2

• Supporting Information S1

• Table S1

• Movie S1

Correspondence to: N. D. McMahon, nmcmahon@usgs.gov

## Citation:

McMahon, N. D., R. C. Aster, W. L. Yeck, D. E. McNamara, and H. M. Benz (2017), Spatiotemporal evolution of the 2011 Prague, Oklahoma, aftershock sequence revealed using subspace detection and relocation, Geophys. Res. Lett., 44, 7149–7158, doi:10.1002/2017GL072944.

Received 3 FEB 2017 Accepted 29 JUN 2017 Accepted article online 5 JUL 2017 Published online 18 JUL 2017

# Spatiotemporal evolution of the 2011 Prague, Oklahoma, aftershock sequence revealed using subspace detection and relocation

Nicole D. McMahon<sup>1,2</sup> , Richard C. Aster<sup>2</sup> , William L. Yeck<sup>1</sup> , Daniel E. McNamara<sup>1</sup> , and Harley M. Benz<sup>1</sup>

<sup>1</sup>National Earthquake Information Center, U.S. Geological Survey, Golden, Colorado, USA, <sup>2</sup>Department of Geosciences, Colorado State University, Fort Collins, Colorado, USA

Abstract The 6 November 2011 $M _ { w } ~ 5 . 7$ earthquake near Prague, Oklahoma, is the second largest earthquake ever recorded in the state. $\mathsf { A } M _ { w }$ 4.8 foreshock and the $M _ { w } 5 . 7$ mainshock triggered a prolific aftershock sequence. Utilizing a subspace detection method, we increase by fivefold the number of precisely located events between 4 November and 5 December 2011. We find that while most aftershock energy is released in the crystalline basement, a significant number of the events occur in the overlying Arbuckle Group, indicating that active Meeker-Prague faulting extends into the sedimentary zone of wastewater disposal. Although the number of aftershocks in the Arbuckle Group is large, comprising \~40% of the aftershock catalog, the moment contribution of Arbuckle Group earthquakes is much less than 1% of the total aftershock moment budget. Aftershock locations are sparse in patches that experienced large slip during the mainshock.

Plain Language Summary We investigate the aftershocks of the November 2011 Prague, Oklahoma, earthquake sequence and find approximately 4500 additional aftershocks, mostly very small magnitude. These aftershocks help identify below surface geologic units, map fault structures including a previously unknown fault, and provide insight on how the sequence developed in space and time in the month following the 6 November 2011 magnitude 5.7 earthquake, the second largest earthquake ever recorded in the state.

## 1. Introduction

In the 2011 $M _ { w }$ 5.7 Prague, Oklahoma, sequence, three relatively large earthquakes (M 4.8, 5.7, and 4.8) on 5, 6, and 8 November 2011, respectively, were likely induced by deep wastewater injection at a nearby well [Keranen et al., 2013]. The mainshock is currently the second largest instrumentally recorded earthquake in Oklahoma history [Keranen et al., 2013; Sumy et al., 2014], only recently succeeded by the $M _ { w }$ 5.8 Pawnee, Oklahoma, earthquake on 3 September 2016 [Yeck et al., 2017]. The largest aftershock of the sequence, a $M _ { w } 4 . 8 ,$ occurred 2 days after the mainshock. Much of this seismicity sequence occurred along the Meeker-Prague fault, a 20 km splay off the Wilzetta fault zone (WFZ). The WFZ is a complex, \~200 km long, Pennsylvanian-aged fault system that trends NE-SW through central Oklahoma [Way, 1983; Joseph, 1987]. Focal mechanisms and aftershock locations reveal a steeply dipping right-lateral strike-slip fault [Dycus, 2013; Holland, 2013; Sumy et al., 2014].

We apply subspace detectors and multiple-event relocation to the 2011 $M _ { w }$ 5.7 Prague, Oklahoma, aftershock sequence to significantly lower the magnitude of completeness of the catalog and to better understand the spatiotemporal evolution of seismicity. Subspace detection is a powerful tool for detecting seismic events in low signal-to-noise environments and/or during high rates of seismicity. Subspace detectors improve upon simple cross correlation or matched filtering techniques by using multiple orthogonal waveform templates that approximately span the signals from all previously identified events within a data set; subspace detectors are also typically more computationally efficient [Harris, 2006]. The subspace methodology has been increasingly used for the characterization of large earthquake swarms [Harris, 2006; Morton, 2013; Harris and Dodge, 2011; Barrett and Beroza, 2014]; low-frequency earthquakes within nonvolcanic tremor [Maceira et al., 2010]; extensive aftershock sequences [Harris and Dodge, 2011]; microseismic monitoring of hydrofracturing sequences [Song et al., 2014]; exploration of deep, long-period magmatic events [McMahon et al., 2016]; characterization of coal mine-related seismicity [Chambers et al., 2015]; and investigation of induced seismicity clusters [Benz et al., 2015b; Skoumal et al., 2015].

![](mineru/MCMAHON2017_GL072944__paper/images/24df39ab36d142a0734ba61ac2b5117a91d95f12e4f90690d4a16c212950b2a1.jpg)  
Figure 1. Map of aftershocks in the McNamara et al. [2015] catalog used for subspace detector construction (circles) colored by time of occurrence after 4 November 2011, seismic stations utilized in the study (green triangles), class II injection wells (diamonds) colored by type of activity, and mapped faults (solid black lines). The earthquakes extend southwestward away from a pair of active wastewater disposal wells. Location map of all historic seismicity above $M _ { w } 2 . 5 \mathrm { i }$ n Oklahoma complete through July 2016 in the top right. The aftershocks illuminated \~20 km of the Meeker-Prague fault and an off-fault cluster of events to the southeast.

## 2. Observational Waveform Data

We utilized waveform data from 21 temporary seismic stations: 18 from the Oklahoma RAMP network [Keranen, 2011] and 3 from the U.S. Geological Survey (USGS) network [Albuquerque Seismological Laboratory, 1980], all deployed within 1 week after the $M _ { w }$ 4.8 foreshock (Table S1 in the supporting information). Stations were deployed around the aftershock sequence at distances between 0.7 and 14.7 km from the $M _ { w }$ 5.7 mainshock epicenter (Figure 1). Data from nine EarthScope USArray Transportable Array stations [IRIS Transportable Array, 2003] and an Oklahoma Seismic Network [Oklahoma Geological Survey, 1978] station were also utilized to better capture the foreshock-mainshock-aftershock activity and to enhance detection and location capabilities prior to full functionality of the temporary networks. The last deployed temporary stations became fully operational on 11 November 2011. We analyzed data from 4 November 2011, 1 day prior to the foreshock, through 5 December 2011.

## 3. Methodology

We utilized the catalog of McNamara et al. [2015] (see the supporting information) as the initial catalog for our subspace detector construction. A total of 998 events in the month following the foreshock were identified, located, and manually reviewed.

Detectors were developed exclusively for the S-phase, which observationally is the simplest in complexity and the largest amplitude signal. We followed the methodology of Benz et al. [2015b] for subspace detector construction, detection, and estimation of S-phase arrival time. We found that between 11 and 91 multichan nel templates were needed to describe 90% of the observed event waveform energy on each of the stations (Table S1). The multichannel templates were simultaneously cross-correlated against continuous data at each station from the time the station became operational for temporary stations and from 4 November 2011 fo permanent stations through 5 December 2011 (Table S1).

Although they excel at identifying smaller events, our subspace detectors can be insensitive to larger $( M _ { w } > 3 )$ events because the extended source duration of the mainshock and largest aftershocks makes them difficult to detect using templates that are derived from small earthquakes. We supplemented the detection catalog with larger event information by adding the P- and S-phase arrival times of the original catalog. The additional arrival time and station information of precisely located events resulted in a more robust final catalog.

After the arrival times from the detections were associated into events using an arrival time associator [Benz et al., 2015a] and supplemented with large and precisely located event information, we used Bayesloc [Myers et al., 2007, 2009] to estimate hypocenters utilizing the velocity model of McNamara et al. [2015] (Table S2).

For detected events, magnitudes relative to the nearest original event catalog neighbor were computed at each station using the method of Benz et al. [2015b] and averaged across all stations to determine the final event magnitude (Figure S2 in the supporting information). To calculate the event catalog b-value [e.g., Gutenberg and Richter, 1944], we utilized the methods of Benz et al. [2015b].

The subspace detection methodology was chosen for its computational efficiency over running all the cataloged events as templates. A total of 14,150 events identified on the 31 stations of interest was reduced to 1116 subspace detection templates representing a 92% reduction in the number of templates cross correlated against the continuous data and an equivalent reduction in processing time.

## 4. Results

A total of 577,040 S-phase arrival times from subspace detection were obtained using 31 seismic stations. A total of 191,100 of the arrival times were associated into 20,788 events observed at five or more stations. Most remaining arrival times were likely events observed on fewer than five stations. Few false detections are likely given that we set the detection threshold relatively high. Of the 21,786 events located, 5176 events had estimated epicentral uncertainties less than 500 m and depth uncertainties less than 1 km. After relocation, 184 of the events in the original catalog were excluded due to the uncertainty constraints, bringing the final event count to 5262. These excluded events were added to Figures S11–S15 for comparative visualization.

Aftershocks align primarily along the known fault strands of the WFZ, as indicated by the initial catalog (Figure 2a) and extend down to \~10 km depth. Aftershocks extend southwestward from a pair of active wastewater disposal wells along the main strike of the WFZ (A0-A″) before turning more westerly and extending \~16 km along the main strike of the Meeker-Prague fault (A-A0), short of the 20 km length previously indicated due to strict uncertainty parameters used in this study. A splay (E-E0; Figure S1) extends \~4 km westward away from the Meeker-Prague fault. A linear, NE-SW oriented satellite sequence (G-G0; Figure S1) appears \~9 km to the southeast of the main aftershock sequence, subparallel to the Meeker-Prague fault. This nearly vertical active fault structure was not clearly visible in the initial catalog.

The 5 November $M _ { w }$ 4.8 foreshock ruptured a portion of the main WFZ along A0-A″ (Figures 2c1–2c3). The aftershocks extend southwestward from a pair of active wastewater disposal wells, deepening over a distance of \~3 km to 10 km depth. The $M _ { w }$ 5.7 mainshock ruptured the Meeker-Prague fault along A-A (Figures 2b1–2b3). Along this fault, most aftershocks are concentrated in an \~9 by 9 km section of the fault extending southwestward away from the intersection with the main WFZ. The largest aftershock, a $M _ { w }$ 4.8, ruptured an \~4 km westward trending splay of the Meeker-Prague fault along E–E0 (Figure S1).

From map view and cross section C-C0 we see the geometry of the Meeker-Prague fault striking N55°E and dipping $8 5 ^ { \circ }$ to the northwest which is consistent with the USGS W-phase moment tensor solution striking N56°E and dipping $8 5 ^ { \circ }$ to the northwest.

Common characteristics are visible in the cross sections. First, there is a “lid” of seismicity characterized by dense aftershock occurrence between \~1.4 and 2.6 km depth with relatively few aftershocks occurring immediately above and below this zone. Within this zone, there is a bifurcation in aftershock occurrence at \~1.9 km depth. We note that the input velocity model had an increase at this depth, which may cause this split in location depths in the Arbuckle, but it cannot cause the difference in depths between these events and the deeper, larger basement events. Dense aftershock occurrence is seen on cross sections A-A0 and A0-A″ between \~4.7 and 8 km depth with relatively little activity between the top of this zone and the base of the above described lid. While the number of aftershocks shallower than 2.6 km is relatively high, the moment released (Figures 2b3, 2c3, and 2d3) is relatively low, indicating smaller aftershocks occurring above this depth and larger ones below. Additional cross sections can be found in Figure S1.

Seismic Station

Production Well

Disposal Well

Xsection

Original Earthquake

Newly Detected Earthquake

![](mineru/MCMAHON2017_GL072944__paper/images/0e1b1e1c78612ad4bd89afc222eb018eac45a45f15a2989c759a9078338facc2.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/b5897afee11941139e244d090dfd79b18e04061ec02e73b1f0a7f807847e31c8.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/149c2746e42f89c9e97d88115a816b408601a2b5d1edddbc455703b06ffec1d8.jpg)

Distance along cross-section (km)Number of Earthquakes Moment at Depth (dyn-cm) -16-12 -8 -4 200400 0 2.4E21  
![](mineru/MCMAHON2017_GL072944__paper/images/4189de9daaf3a9aa0fe60f8647edbc4f7b99e66940837fbae0e63bdf0d765d43.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/02a30aafff32ddfd8fdca72678ecf75bc3e98053377fdf4d5852845d66f6036b.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/126f520e645037ec0af7b50e3724a06fc0367f1e104177e23b8b52f2e073c37e.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/29091315403bfeb5e1133329f47d3595f6563e4f50b32836188a8142a27caf6c.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/af92eeecabdcac917bf01fe2095096d65130dd119adda3c93b13ea2997d4c077.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/2eb286866f28bd80c3385d1e209e472fecd2bb41e4d3c2b600faeb1f25557d13.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/426a2b6baca46347ece8483f79d6a121cf6dd7a42fc6a6f7e9536725f7b02efc.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/29f57162e7bfca8f001de1b5832b7348328bce017d6cf6ac19383e7068fa9118.jpg)  
Figure 2. (a) Map of final event catalog locations with epicentral uncertainties less than 500 m and depth uncertainties less than 1 km. The yellow depth range depicts the approximate extent of the Arbuckle Group in the region. Events are colored by magnitude as indicated in the legend. The three large events (Figure 1) are plotted as white stars, and cross sections are indicated by red lines. (b1) Event locations within 1.5 km of cross section A-A0 along the strike Meeker-Prague fault. (b2) Number of earthguakes in cross section A-A' as a function of depth in 0.1 km depth bins. (b3) Seismic moment in cross section A-A0 as a function of depth in 0.1 km depth bins. (c1–c3) Follows Figures 2b1–2b3 for cross section A0-A″ along the main strike of the Wilzetta fault zone. (d1–d3) Follows Figures 2b1–2b3 for cross section ${ \mathsf { C } } { \mathsf { - } } { \mathsf { C } } ^ { \prime }$ perpendicular to the Meeker-Prague fault.

Time after Full Network Functionality (days)  
a  
![](mineru/MCMAHON2017_GL072944__paper/images/51f88da688f9bbcf31a6ee5a4fa74925f88fb0d6e77bc26137f6fa7ca06361d0.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/5f771926ba7d78240edf20983cd890e8a203df774bf91c825f1ac30262a2f1f2.jpg)

c  
![](mineru/MCMAHON2017_GL072944__paper/images/6303ad7d5648cc5f6cbb57c294b9d4eb49b196601c2891c72c80cbd3a73c8275.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/7a66503d0d40af9571c66ef60e47387ed87dc0610f075914fb3cb39a4d03a3e6.jpg)  
Figure 3. (a) Frequency-magnitude distributions for the original catalog of events (green), the catalog using only subspace detected events (blue), and the final catalog amalgamating the two previous catalogs (gray). Minimum magnitude of completeness $M _ { C }$ and b-value lines are also plotted. The triangles indicate absolute number of events within respective magnitude bins, and the squares indicate cumulative number of events greater than or equal to respective magnitudes. (b) Modified Omori decay parameter, ${ \bf \nabla } , p ,$ using all catalog events (red) and only events above the $M _ { C }$ (blue). (c) Follows Figure 3a showing the differing frequency-magnitude distributions between the Arbuckle Group (red) and the crystalline basement (blue). (d) Follows Figure 3b showing the differing modified Omori decay parameters between the Arbuckle Group (red) and the basement (blue).

The complete catalog b-value is 0.52 with a minimum magnitude of completeness, $M _ { G } ,$ of 0.8 extending the initial catalog’s $M _ { C }$ down 1.2 units of magnitude while maintaining the general nature of the frequencymagnitude distribution (Figure 3a). We note a difference between the frequency-magnitude distribution of the complete catalog and the catalog of detected events alone. The catalogs have the same magnitude of completeness, but there is a divergence between the number of detected events in the original and sub space detected catalog above M 1.5. If we enlarge the subspace catalog by increasing the uncertainty allowed in locations to 2.0 km horizontal error and 5.0 km depth error, while seeing more scatter in locations and less well-defined fault structures, we do not see a significant change in the frequency-magnitude distri bution. We noted previously that subspace detection can be insensitive to larger events, and this divergence may suggest, in contrast to a minimum magnitude of completeness, a maximum magnitude of completeness achievable with subspace detection alone.

The number of detected aftershocks decays steadily after the network became fully functional on 11 November 2011 (Figure 3c), while the mean magnitude of events remained relatively constant. The decay rate is consistent with a modified Omori decay law [Utsu et al., 1995] p-value of 0.61 (Figure 3b). This value increases to 0.69 when looking at only aftershocks above the catalog $M _ { C } .$ Both values, however, are smaller than standard p-values found globally, 0.9–1.5 [Utsu et al., 1995]. These low values indicate a slower decay rate than most earthquake sequences possibly explained by the intraplate location [Zhao et al., 1992] and low heat-flow values [Blackwell et al., 2011] leading to lower stress relaxation [Mogi, 1967; Kisslinger and Jones, 1991]. This finding contrasts with the short-term results of McNamara et al. [2015], which estimated a p-value for the first few months of the Prague aftershock sequence of 1.25 and a rapidly decaying aftershock. This discrepancy between estimated p-values likely arises because this study analyzed just 25 days of data (post full network functionality), whereas McNamara et al. [2015] studied 95 days of data. The detection and location of low-magnitude events via subspace detection also contribute to this discrepancy, detecting more events over an increased time period slowing the decay rate and subsequently lowering the p-value. Both studies note slower aftershock decay in the days immediately following the mainshock, with the decay rate increasing 20–30 days post–mainshock.

A diurnal variation in the number of precisely located earthquakes shows the sensitivity of the subspace detection method to background noise levels. We note a diurnal variation in the temporal decay of aftershocks (Figures 4a and 4b). Overall, there is a 60% increase in the number of aftershocks detected in the local overnight hours (18:00–06:00) versus local daylight hours (06:00–18:00). We attribute this difference to diurnal variation in anthropogenic noise (e.g., vehicle traffic). This effect increases the catalog’s overnight $M _ { C }$ from M 1.2 to M 0.6 relative to the daylight $M _ { C } .$ When analyzing only aftershocks above the entire catalog’s $M _ { C } ,$ the difference in numbers of detected aftershocks and mean magnitude is significantly lessened.

## 5. Discussion

Utilizing subspace detection, we increased the number of precisely located events in the catalog fivefold and decrease the $M _ { C }$ by 1.2 units of magnitude to M 0.8. Many smaller events are hard to detect at multiple stations because of poor signal-to-noise characteristics, but this is overcome by strategically correlating the S-phase recorded on three components (see Figures S6–S8 for waveform examples). This significant increase in detected and locatable earthquakes allows for more detailed spatiotemporal analysis of the evolution of the aftershock sequence.

The Arbuckle Group, the principal wastewater disposal formation in the Prague region, is composed of late Cambro-Ordovician cyclic carbonate and underlies most of Oklahoma and the adjacent states [Johnson, 1991; Fritz et $a l . ,$ 2013]. A high density of very small earthquakes occurring between 1.4 and 2.6 km depth on both the main and off-fault seismicity trends, combined with information from nearby well logs, indicates slip on small WFZ structures extending into this formation.

Overlying the Arbuckle Group is the middle Ordovician Simpson Group, a sequence of basal sandstones grad ing upward to shales and limestones [Suhm, 1997; Dycus, 2013]. This group records the first influx of clastic sediments over a region that had previously been the site of a vast amount of carbonate accumulation [Islam and Crump, 1990]. The sandy and clastic nature of the Simpson Group sharply contrasting against the underlying Arbuckle Group carbonates may indicate why earthquakes do not propagate to shallower depths in the Prague region. The lithologic change also explains the sharply delineated top of the lid of seis micity at \~1.4 km. Only 16 events in the catalog have hypocentral depths <1.4 km.

Although other studies have noted some seismicity within the Arbuckle Group [e.g., Keranen et al., 2014], the enhanced detection capabilities of subspace detection reveals a great number of aftershocks within the Arbuckle Group, with 40% of the aftershocks identified in this study located between 1.4 and 2.6 km depth (Figure S4). The vast majority of these events are very small: 95% were smaller than M 0.2. For scale, a M 0.2 corresponds to a $7 0 ~ \mathsf m ^ { 2 }$ fault area slipping 1 mm using equation 1 of Hanks and Kanamori [1979] and assuming a shear modulus of 32 GPa. As a consequence, the total moment release for earthquakes in the Arbuckle Group is small, despite the large number of aftershocks, and nearly all of the seismic moment is released in the crystalline basement, with >99.9% of the cumulative moment in the catalog released below 2.6 km depth. All but one of the 168 events larger than M 2 occur below 2.6 km depth.

![](mineru/MCMAHON2017_GL072944__paper/images/9f18100d53cfe9c30f2f56c8407a5392643ca1980ddfefec9acb3c3b2ac2c82e.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/b8a03b442799d503d076e6c5268f282abff6de4ae382a2ab97607945222fb8ec.jpg)

![](mineru/MCMAHON2017_GL072944__paper/images/847ab9284ebebd68d756895fd6720778cae34ee2a9c918789d5e46986d1de58b.jpg)  
Figure 4. (a) Number of events and mean magnitude as a function of time. Event count per 6 h interval plotted as gray bars, mean magnitude as blue line, and magnitude of events occurring during the 6 h interval as black dots. (b) Examination of the diurnal variation seen in Figure 4a. Number of events per hour of the day for full catalog plotted in gray and catalog above the magnitude of completeness $M _ { C }$ plotted in blue with mean magnitude shown. Magnitude of events occurring during the 6 h interval plotted as black dots. (c) Finite-fault slip model from Sun and Hartzell [2014], depth indicated by scale on left and color-coded slip amplitude by scale on right, overlain by aftershock locations (white dots) from this study. The foreshock (Figure 4a), mainshock (Figure 4b), and largest aftershock (Figure 4c) locations are shown by the white stars. The gray line indicates the basement-Arbuckle Group contact. As noted previously, large slip patches are predominantly free of aftershocks.

The Arbuckle Group overlies the Precambrian granitic basement. Both Dycus [2013] and Keranen et al. [2013] put the top of basement at \~2.5 km depth in the aftershock region, which is congruent with the observed base of the small magnitude Arbuckle lid of seismic activity at \~2.6 km. The unconformity between the base of the sedimentary Arbuckle Group and the top of the volcanic basement may explain the sharp contrast in earthquake density and energy release across the formation boundary, reflecting sharply differing stress and/or rheological conditions between the two units.

We note a difference in the frequencymagnitude distributions (FMD) between the Arbuckle Group and the basement (Figure 3c). The FMD of the basement resembles that of the original catalog as few small events in the Arbuckle Group were originally detected. The bvalue of the Arbuckle Group follows more closely with the empirically estimated global b-value of 1.0. This disparity across the unconformity is expected as larger events are occurring in the basement decreasing the b-value, and only small events are occurring in the Arbuckle Group increasing the b-value. Friberg et al. [2014] suggest, in hydraulic fracturing sequences, that lower bvalues are associated with reactivation of preexisting faults rather than the creation of new fractures as intended by the operations. The low b-value in the basement may represent the reactivation of the Wilzetta fault zone and therefore be characterized by a lower b-value. The higher b-value in the Arbuckle Group may represent the creation of new fractures associated with wastewater injection operations. The entire catalog’s b-value, however, is dominated by basement events.

We also note a difference in the modified Omori decay p-values between the Arbuckle Group and the basement (Figure 3d). A lower p-value in the Arbuckle Group indicates a slower decay in the number of aftershocks over time. This disparity is possibly explained by a larger number of small events being detected in the Arbuckle Group over time due to the proximity to seismic stations. The increase in the decay rate/p-value seen in the entire catalog is only found in the Arbuckle Group, however. It is possible that the sedimentary section may be experiencing this change due to the induced nature of the sequence, perhaps taking a few weeks for the fluid pressures and perturbations associated with the wastewater injection to stabilize.

## Acknowledgments

Most seismic data were obtained from the Incorporated Research Institutions for Seismology Data Management Center (http://www.iris.edu/, last accessed June 2015). IRIS Data Services are funded through the Seismological Facilities for the Advancement of Geoscience and EarthScope (SAGE) Proposal of the National Science Foundation under cooperative agreement EAR-1261681. Seismic data for stations ZQ.LC01-ZQ.LC08 were obtained from the U.S. Geological Survey National Earthquake Information Center archives. The initial catalog of events was obtained through written communication with E. Bergman and D. McNamara. The final aftershock catalog data are available at the U.S. Geologica Survey ScienceBase website https:// www.sciencebase.gov/catalog/item/ 595276c6e4b062508e3c7650 (last accessed July 2017) [McMahon, 2017]. Class II injection well information was obtained from the Oklahoma Corporation Commission electronic wel database (http://www.occpermit.com/ WellBrowse/, last accessed May 2015) and oil and gas data files (http://www. occeweb com/og/ogdatafiles2 htm. last accessed May 2015). Fault data were obtained from the Oklahoma Geologica Survey Open-File Report OFR3-2015 [Holland, 2015]. Finite-fault slip data were obtained via written communication with S. Hartzell. We thank S. Larson for geological comments on this study and A. Holland, G. Choy, and M. Brudzinksi for thoughtful reviews. Some figures were created using the Generic Mapping Tools (GMT) version 5.1.2 (www.soest.hawaii.edu/gmt) [Wessel et al., 2013].

The size of an earthquake is determined by the constitutive properties of the medium [Lapusta and Rice, 2003] and the frictional strength of the fault [Byerlee, 1978; Das and Scholz, 1983]. These principles may explain why larger-magnitude events are not occurring in the shallow sediments in the Prague region. It is unlikely that an event larger than M 2–3 will initiate in the Arbuckle Group or M 1 in the shallow sediments, and unlikely larger events, such as the $M _ { w }$ 4.8 foreshock and $M _ { w }$ 5.7 mainshock, will occur much shallower than 5 km in the Meeker-Prague region (Figure S5). We hypothesize that limitations on earthquake magni tudes in the Arbuckle Group could be controlled by physical parameters: the lower shear modulus of the car bonate compared to the basement granite thus producing smaller magnitudes, the change in rheologica properties across the Arbuckle-basement unconformity limiting the size of faults and disallowing them to progress downward, or the increased pore fluid pressure lowering the frictional strength of the rocks causing smaller strains to accumulate and hence smaller slips.

The aftershock locations along the Meeker-Prague fault show good correlation with the finite-fault slip mode estimated by Sun and Hartzell [2014] (Figure 4). As shown previously, the large slip patches are predominantly free of aftershocks. Approximately 73% of events locate in cells with less than 10 cm slip and only 5% in cells with more than 30 cm slip which agrees with the observation that aftershocks are preferentially located in low-slip regions of faults [Mendoza and Hartzell, 1988; Beroza and Zoback, 1993; Das and Henry, 2003; Woessner et al., 2006] (Figure S3).

In addition to the main faults ruptured during the Prague sequence, a subparallel, unmapped fault approximately 9 km to the southeast of the principal Meeker-Prague fault system was illuminated by aftershock activity along G-G0 (Figures S1d1–S1d3). This fault exhibits characteristics that are similar to the main Meeker-Prague fault: a NE-SW trend similar to a majority of seismogenic faults in Oklahoma, a high density of low-magnitude earthquakes occurring at shallow depths, and larger-magnitude events occurring below this depth. There appears to be a clear lineation of earthquakes at \~2.3 km depth which may demarcate the base of the Arbuckle Group, slightly shallower than the main fault system to the northwest. This new fault appears to have become active on 9 November 2011, and activity may have been statically triggered by the seismicity on the main fault zone.

## 6. Conclusions

Application of subspace detection methodology increased the number of precisely located events in the Prague, Oklahoma, aftershock catalog more than fivefold. Most events in the updated catalog are located using only the S-phase which may be useful for environments in which other body phases may be difficult to discern or pick. We find a large number of earthquakes (\~40%) within the Arbuckle Group, the zone of wastewater injection in the Prague region, indicating that the Meeker-Prague fault may extend into the above-basement sediment. These earthquakes, however, are mostly very small, comprising ≪1% of moment budget of the entire catalog. We find a previously unmapped, subparallel fault delineated by aftershock locations approximately 9 km to the southeast of the main Meeker-Prague fault. The aftershock locations show good correlation with finite-fault slip models showing that patches that experienced large slip during the mainshock are predominantly free of aftershocks. Via subspace detection, we effectively lowered the catalog’s minimum magnitude of completeness to M 0.8, detecting microseismic events that may not be possible with more traditional detection techniques and allowing for more detailed analysis of spatiotemporal trends in seismicity.

## References

Albuquerque Seismological Laboratory (ASL)/USGS (1980), U.S. Geological Survey Networks, International Federation of Digital Seismograph Networks, Other/Seismic Network, doi:10.7914/SN/GS

Barrett, S. A., and G. C. Beroza (2014), An empirical approach to subspace detection, Seismol. Res. Lett., 85(3), 594–600, doi:10.1785/ 0220130152.

Benz, H. M., C. E. Johnson, J. M. Patton, N. D. McMahon, and P. S. Earle (2015a), GLASS 2.0: An operational, multimodal, Bayesian earthquake data association engine, Abstract S21B-2687 presented at 2015 Fall Meeting, AGU, San Francisco, Calif., 15-19 Dec

Benz, H. M., N. D. McMahon, R. C. Aster, D. E. McNamara, and D. B. Harris (2015b), Hundreds of earthquakes per day: The 2014 Guthrie, Oklahoma, earthquake sequence, Seismol. Res. Lett., 86(5), doi:10.1785/0220150019

Beroza, G. C., and M. D. Zoback (1993), Mechanism diversity of the Loma Prieta aftershocks and the mechanisms of mainshock-aftershock interaction, Science, 259(5092), 201–213, doi:10.1126/science.259.5092.210.

Blackwell, D. D., M. C. Richards, Z. S. Frone, J. F. Batir, M. A. Williams, A. A. Ruzo, and R. K. Dingwall (2011), SMU geothermal heatflow map of the conterminous United States, 2011, Supported by Google.org. [Available at http://www.smu.edu/geothermal.]

Byerlee, J. (1978), Friction of rocks, Pure Appl. Geophys., 116(4–5), 615–626, doi:10.1007/BF00876528.

Chambers, D. J. A., K. D. Koper, K. L. Pankow, and M. K. McCarter (2015), Detecting and characterizing coal mine related seismicity in the western U.S. using subspace methods, Geophys. J. Int., 203(2), 1388–1399, doi:10.1093/gji/ggv383.

Das, S. and C. H. Scholz (1983), Why large earthquakes do not nucleate at shallow depths, Nature, 305, 621–623, doi:10.1038/305621a0

Das, S. and C. Henry (2003), Spatial relationship between main earthquake slip and its aftershock distribution, Rev. Geophys., 41(3), 1013, doi:10.1029/2002RG000119.

Dycus, M. N. (2013), Structural characterization of the Wilzetta fault zone; Lincoln, Pottawatomie, and Creek Counties, Oklahoma, MS thesis Dep. of Geosc., Univ. of Tulsa, Tulsa, Okla.

Friberg, P. A., G. M. Besana-Ostman, and I. Dricker (2014), Characterization of an earthquake sequence triggered by hydraulic fracturing in Harrison County, Ohio, Seismol. Res. Lett., 85(6), doi:10.1785/0220140127.

Fritz, R. D., P. Medlock, M. J. Kiykendall, and J. L. Wilson (2013), The geology of the Arbuckle Group in the Midcontinent: Sequence stratigraphy, reservoir development, and the potential for hydrocarbon exploration, in The Great American Carbonate Bank: The Geology and Economic Resources of the Cambro-Ordovician Sauk Megasequence of Laurentia, AAPG Memoir., vol. 98, edited by J. Derby et al., pp. 203–273, AAPG, Tulsa, Okla.

Gutenberg, B., and C. F. Richter (1944), Frequency of earthquakes in California, Bull. Seismol. Soc. Am., 34(4), 185–188

Hanks, T. C., and H. Kanamori (1979), Moment magnitude scale, J. Geophys. Res., 84(B5), 2348–2350, doi:10.1029/JB084iB05p02348.

Harris, D. B. (2006), Subspace detectors: Theory, Rep. UCRL-TR-222758, Lawrence Livermore Natl. Lab., Livermore, Calif.

Harris, D. B., and D. A. Dodge (2011), An autonomous system for grouping events in a developing aftershock sequence, Bull. Seismol. Soc. Am., 101(2), 763–774, doi:10.1785/0120100103.

Holland, A. (2013), Optimal fault orientations within Oklahoma, Seismol. Res. Lett., 84(5), 876–890, doi:10.1785/0220120153.

Holland, A (2015), Preliminary fault map of Oklahoma, Open File Rep. 03–2015, scale 1:750,000, Okla. Geol. Surv., Norman, Okla.

IRIS Transportable Array (2003), USArray Transportable Array, International Federation of Digital Seismograph Networks, Other/Seismic Network, doi:10.7914/SN/TA.

Islam, Q. T. and J. Crump (1990), Simpson Group extent in Oklahoma focus of stud, Oil Gas J., 88(24). [Available at http://www.ogj.com/ articles/print/volume-88/issue-24/in-thisissue/exploration/simpson-group-extent-in-oklahoma-focus-of-stud.html.]

Johnson, K. S. (1991), Geological overview and economic importance of Late Cambrian and Ordovician rocks in Oklahoma, in Late Cambrian-Ordovician Geology of the Southern Midcontinent, 1989 Symposium: Oklahoma Geol. Surv. Circular, vol. 92, edited by K. S. Johnson, pp. 3–14, Okla. Geol. Surv., Norman, Okla.

Joseph, L. (1987), Subsurface analysis, “Cherokee” Group (Des Monesian), portions of the Lincoln Pottawatomie, Seminole, and Okfuskee Counties: Oklahoma, Oklahoma City Geological Society Shale Shaker, Dec. 1986/Jan. 1987.

Keranen, K. (2011), Oklahoma RAMP, International Federation of Digital Seismograph Networks, Other/Seismic Network, doi:10.7914/SN/ ZQ\_2011.

Keranen, K. M., H. M. Savage, G. A. Abers, and E. S. Cochran (2013), Potentially induced earthquakes in Oklahoma, USA: Links between wastewater injection and the 2011 M 5.7 earthquake sequence, Geology, 41(6), 699–702, doi:10.1130/G34045.1.

Keranen, K. M., M. Weingarten, G. A. Abers, B. A. Bekins, and S. Ge (2014), Sharp increase in central Oklahoma seismicity since 2008 induced by massive wastewater injection, Science, 345(6195), 448–451, doi:10.1126/science.1255802.

Kisslinger, C., and L. M. Jones (1991), Properties of aftershock sequences in southern California, J. Geophys. Res., 96(B7), 11,947–11,958, doi:10.1029/91JB01200.

Lapusta, N. and J. R. Rice (2003), Nucleation and early seismic propagation of small and large events in a crustal earthquake model, J. Geophys. Res., 108(B4), 2205, doi:10.1029/2001JB000793.

Maceira, M., C. A. Rowe, G. Beroza, and D. Anderson (2010), Identification of low frequency earthquakes in non-volcanic tremor using the subspace detector method, Geophys. Res. Lett., 37, L06303, doi:10.1029/2009GL041876.

McMahon, N. D., R. C. Aster, E. K. Myers, and A. C. Lough (2016), Using subspace detection to study deep long-period seismicity beneath the Executive Committee Range, Marie Byrd Land, Antarctica, Abstract S31E-04 presented at 2016 Fall Meeting, AGU, San Francisco, Calif., 12-16 Dec.

McMahon, N. D., R. C. Aster, W. L. Yeck, D. E. McNamara, and H. M. Benz (2017), Aftershock catalog for the November 2011 Prague, Oklahoma, earthquake sequence, U.S. Geol. Surv. Data Release, doi:10.5066/F7FJ2FNT.

McNamara, D. E., H. M. Benz, R. B. Herrmann, E. A. Bergman, P. Earle, A. Holland, R. Baldwin, and A. Gassner (2015), Earthquake hypocenters and focal mechanisms in central Oklahoma reveal a complex system of reactivated subsurface strike-slip faulting, Geophys. Res. Lett., 42, 2742-2749.doi:10.1002/2014GL062730

Mendoza, C., and S. H. Hartzell (1988), Aftershock patterns and main shock faulting, Bull. Seismol. Soc. Am., 78(4), 1438–1449.

Mogi, K. (1967), Earthquakes and fractures, Tectonophysics, 5(1), 35–55, doi:10.1016/0040-1951(67)90043-1.

Morton, E. A. (2013), Dynamic earthquake triggering above the Socorro magma body and automated event detection in the 2009 Socorro New Mexico earthquake swarm, MS thesis, Dep. of Earth and Env. Sci., New Mexico Inst. of Mining and Tech., Socorro, N. M.

Myers, S. C., G. Johannesson, and W. Hanley (2007), A Bayesian hierarchical method for multiple-event seismic location, Geophys. J. Int., 171(3), 1049–1063, doi:10.1111/j.1365-246X.2007.03555.x.

Myers, S. C., G. Johannesson, and W. Hanley (2009), Incorporation of probabilistic seismic phase labels into a Bayesian multiple-event seismic locator, Geophys. J. Int., 177(1), 193–204, doi:10.1111/j.1365-246X.2008.04070.x.

Oklahoma Geological Survey (1978), Oklahoma Seismic Network, International Federation of Digital Seismograph Networks, Other/Seismic Network, doi:10.7914/SN/OK.

Skoumal, R. J., M. R. Brudzinski, and B. S. Currie (2015), Microseismicity induced by deep wastewater injection in southern Trumbull County Ohio, Seismol. Res. Lett., 86(5), 1326–1334, doi:10.1785/0220150055

Song, F., N. R. Warpinski, M. N. Toksöz, and H. S. Kuleli (2014), Full-waveform based microseismic event detection and signal enhancement: An application of the subspace approach, Geophys. Prospect., 62(6), 1406–1431, doi:10.1111/1365-2478.12126.

Suhm, R. W. (1997), Simpson stratigraphy of the southern midcontinent, in Simpson and Viola Groups in the Southern Midcontinent, 1994 Symposium, Oklahoma Geol. Surv. Circular, vol. 99, edited by K. S. Johnson, pp. 3–38, Okla. Geol. Surv., Norman, Okla.

Sumy, D. F., E. S. Cochran, K. M. Keranen, M. Wei, and G. A. Abers (2014), Observations of static Coulomb stress triggering of the Novembe 2011 M5.7 Oklahoma earthquake sequence, J. Geophys. Res. Solid Earth, 119, 1904–1923, doi:10.1002/2013JB010612.

Sun, X., and S. Hartzell (2014), Finite-fault slip model of the 2011 M 5.6 Prague, Oklahoma earthquake from regional waveforms, Geophys. Res. Lett., 41, 4207–4213, doi:10.1002/2014GL060410.

Utsu, T., Y. Ogata, and R. S. Matsu’ura (1995), A centenary of the Omori formula for a decay law of aftershock activity, J. Phys. Earth, 43(1), 1–33, doi:10.4294/jpe1952.43.1.

Way, H. S. K. (1983), Structural study of the Hunton Lime of the Wilzetta Field, T12N-13N, R5E, Lincoln County, Oklahoma, pertaining to the exploration for hydrocarbons, MS thesis, Boone Pickens School of Geol., Okla. St. Univ., Stillwater, Okla.

Wessel, P., W. H. F. Smith, R. Scharroo, J. Luis, and F. Wobbe (2013), Generic Mapping Tools: Improved version released, Eos. Trans. AGU, 94(45), 409–410, doi:10.1002/2013EO450001.

Woessner, J., D. Schorlemmer, S. Wiemer, and P. M. Mai (2006), Spatial correlation of aftershock locations and on-fault main shock properties, J. Geophys. Res., 111, B08301, doi:10.1029/2005JB003961.

Yeck, W. L., G. P. Hayes, D. E. McNamara, J. L. Rubinstein, W. D. Barnhart, P. S. Earle, and H. M. Benz (2017), Oklahoma experiences largest earthquake during ongoing regional wastewater injection hazard mitigation efforts, Geophys. Res. Lett., 44, 711–717, doi:10.1002 2016GL071685.

Zhao, Z., K. Qike, K. Matsumura, and J. Xu (1992), p-values of continental aftershock activity in China, Acta Seismol. Sin., 5(4), 683–690 doi:10.1007/BF02651015.