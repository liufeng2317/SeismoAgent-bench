# A High-Resolution Seismic Catalog for the Initial 2019 Ridgecrest Earthquake Sequence: Foreshocks, Aftershocks, and Faulting Complexity

David R. Shelly<sup>\*1</sup>

## Abstract

I use template matching and precise relative relocation techniques to develop a highresolution earthquake catalog for the initial portion of the 2019 Ridgecrest earthquake sequence, from 4 to 16 July, encompassing the foreshock sequence and the first 10+ days of aftershocks following the $\pmb { M } _ { \mathbf { w } }$ 7.1 mainshock. Using 13,525 routinely cataloged events as waveform templates, I detect and precisely locate a total of 34,091 events. Precisely located earthquakes reveal numerous crosscutting fault structures with dominantly perpendicular southwest and northwest strikes. Foreshocks of the $\pmb { M } _ { \mathbf { w } }$ 6.4 event appear to align on a northwest-striking fault. Aftershocks of the $\pmb { M } _ { \mathbf { w } }$ 6.4 event suggest that it further ruptured this northwest-striking fault, as well as the southwest-striking fault where surface rupture was observed. Finally, aftershocks of the $\pmb { M } _ { \mathbf { w } }$ 7.1 show a highly complex distribution, illuminating a primary northwest-striking fault zone consistent with surface rupture but also numerous crosscutting southwest-striking faults. Aftershock relocations suggest that the $\pmb { M } _ { \mathbf { w } }$ 7.1 event ruptured adjacent to the previous northwest-striking rupture of the $\pmb { M } _ { \mathbf { w } }$ 6.4, perhaps activating a subparallel structure southwest of the earlier rupture. Both the northwest and southeast rupture termini of the $\pmb { M } _ { \mathbf { w } }$ 7.1 rupture exhibited multiple fault branching, with particularly high rates of aftershocks and multiple fault orientations in the dilatational quadrant northeast of the northwest rupture terminus.

Cite this article as Shelly, D. R. (2020). A High-Resolution Seismic Catalog for the Initial 2019 Ridgecrest Earthquake Sequence: Foreshocks, Aftershocks, and Faulting Complexity, Seismol Res Lett XX, 1–8, doi: 10.1785/0220190309.

Supplemental Material

## Introduction

The 2019 Ridgecrest earthquake sequence first gained attention with an $M _ { \mathrm { w } }$ 6.4 earthquake on 4 July 2019. This earthquake was in fact preceded by several foreshocks in the preceding ${ \sim } 2$ hr, the largest (though not the first) being an $M _ { \mathrm { w } }$ 4.0 event at 17:02:55 UTC. The $M _ { \mathrm { w } }$ 6.4 event (at 17:33:48 UTC) was followed by a vigorous aftershock sequence with two main, nearly perpendicular trends. Approximately 34 hr after the $M _ { \mathrm { w } }$ 6.4 event, an $M _ { \mathrm { w } }$ 7.1 mainshock struck, primarily rupturing a northwest-striking fault in a right-lateral sense.

This sequence produced tens of thousands of earthquakes over the first ∼12 days following the 4 July $M _ { \mathrm { w } }$ 6.4 event. Although capabilities of real-time network processing have improved dramatically in recent years, traditional individual event locations have inherent limitations. In cases like this with incredibly high rates of activity, the vast majority of events (at least initially) are detected and located automatically without analyst review and refinement.

Retrospective, high-precision relative earthquake relocation studies using waveform cross correlation have significantly improved on routine catalog locations, revealing new fault structures and new insights into fault-slip behaviors (e.g., Frémont and Malone, 1987; Got et al , 1994; Rubin et al , 1999; Waldhauser et al , 2004). These studies include relatively largescale relocation of routine catalog-detected seismicity for multiple decades over all of northern California (Waldhauser and Schaff, 2008) and southern California (Hauksson et al , 2012). Real-time double-difference processing, in which new events are compared with a database of older relocated events, has also been implemented for northern California (Waldhauser, 2009).

Meanwhile, multichannel matched-filter event detection, using known earthquakes as waveform templates, has proven successful at detecting small, low signal-to-noise earthquakes that evade routine detection procedures (Shearer, 1994;

![](mineru/SHELLY2020_0220190309__paper/images/e61e13dfb884d1c2f15e2433b1000c532d49d18718c058a48f7d457fefeccf8d.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/dfc5ccd9178b1b719c91789585ba324a6c6af12c25b9eeba9baccf5f262641b8.jpg)  
Figure 1. Shaded relief map views of the 2019 Ridgecrest sequence. (a) Events are shown as colored dots, according to whether they preceded or followed the $M _ { \mathrm { w } } \ : 7 .$ 1 mainshock. Dot size does not scale with magnitude. Stars indicate $M _ { \mathrm { w } }$ 6.4 and 7.1 epicenter locations from this study. The seismic station used in this study is shown as small white triangles (additional stations beyond main map view shown in inset). Pink squares show town

![](mineru/SHELLY2020_0220190309__paper/images/e8e27c5cc737830e31183486f413c479d762426cb8b16d1a1f947bfc84cce9a7.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/f0fbe661cfedd34678cc94304e11480bcd8fa2fc181e97397f60ed32da0e015b.jpg)  
centers. White lines indicate mapped surface rupture (both fully and not fully verified) (Kendrick et al , 2019). (b) Same as (a) but with events color coded by depth. Depth is referenced to a surface elevation of 0.7 km a.s.l. (c,d) Same as (a) and (b) but shown for the routine Southern California Seismic Network (SCSN) catalog, as available when downloaded (see the Methods section).

Gibbons and Ringdal, 2006; Shelly et al , 2007; Peng and Zhao, 2009). More recently, matched-filter detection has been naturally combined with precise relative relocation. Although it is more challenging to locate events rather than just detect them, this combined approach has facilitated precise location of many more earthquakes than are routinely cataloged. Such work was initially focused on individual earthquake swarms (e.g., Shelly and Hill, 2011; Shelly et al , 2013) but has recently expanded in scope to encompass many years of data over all of southern California (Ross et al , 2019). These studies have illuminated faulting complexity, spatial migration, and other features not resolved in routine earthquake catalogs. These results have also provided constraints for understanding earthquake behavior in combination with geodetic and other available datasets.

In this article, I report an enhanced, high-resolution earthquake catalog constructed using template matching in combination with high-precision relative relocation. This relatively rapid relocated catalog covers the initial portion of the 2019 Ridgecrest earthquake sequence, from 4 to 16 July, including the foreshock sequence and the first 10+ days of aftershocks following the $M _ { \mathrm { w } }$ 7.1 mainshock. In total, 34,091 events are detected and relocated here, including more than 20,000 newly detected events (Figs. 1 and 2).

![](mineru/SHELLY2020_0220190309__paper/images/45f56d8ac3e5cc56e900c065496b76ecc7df224d2b8965329f462d5bd53aa03c.jpg)  
Figure 2. Event magnitudes versus time. Magnitudes shown are SCSN preferred magnitudes (for SCSN catalog events) and $M _ { \ L }$ estimates (calibrated to SCSN M<sub>L</sub> scaling, see Fig. 4) for newly detected events. Note the strongly varying detection levels at small magnitudes following the $M _ { \mathrm { w } }$ 6.4 and 7.1 events, a reflection of high noise levels from the seismic coda of numerous moderate $( M _ { \mathrm { w } } \ 3 – 4 + )$ at these times.

overlapping with the S-wave templates on individual stations. If only one phase was picked in the catalog for a particular station, the timing for the other phase (typically S) was estimated using the catalog origin time and a $V _ { P } / V _ { S }$ ratio of 1.7. All data were band-pass filtered at 2–12 Hz. Both P and S templates were

## Methods

I followed the event detection and relocation approach described by Shelly et al (2016). I used earthquakes and phase picks routinely cataloged by the Southern California Seismic Network (SCSN), along with short-period and broadband seismic stations included in real-time processing (Fig. 1). To facilitate rapid processing as the sequence unfolded, data were downloaded from the Southern California Earthquake Data Center (SCEDC) in stages on 8 July (for 4–6 July), 12 July (for 7–9 July), and 18 July (for 10–16 July). Templates were formed based on phase pick times available in this catalog (Fig. 3). P and S templates were formed separately, beginning 0.3 s prior to the pick time. P and S template lengths were set at 2.5 and 4.0 s, respectively; P-wave templates were truncated if necessary to avoid formed on all components (typically east, north, and vertical) of velocity seismograms, as available.

![](mineru/SHELLY2020_0220190309__paper/images/2cdce8a6a0dd69953ae2710d819e65b89a3b5d501281a19ddfe92d187c4cf553.jpg)  
Figure 3. Example template waveforms. The P-wave template is shown in red, and the S-wave template is in blue. This is the first reported foreshock event in the SCSN catalog (origin time indicated in header, with SCSN event ID in parentheses), with $M _ { \ L }$ 0.5. Station and channel names (station.channel) shown at right.

![](mineru/SHELLY2020_0220190309__paper/images/60d1f0edd7628c8733fd1f6d6cf94143cde347df7a194c7aa70cfbde015c93a9.jpg)  
Figure 4. SCSN magnitude (M ) differences versus measured amplitude ratio. Using a robust linear fit, I find a best-fitting slope of 0.831. This scaling is then applied to extend the magnitude scale to newly detected events.

Templates were scanned through the continuous waveform data (100 samples per second) in daily blocks. All templates were scanned on all days from 3 to 18 July (no events were detected and located on 3 July). Detection thresholds were set at eight times the daily median absolute deviation (MAD) for the correlation coefficient summed across all stations and seven times MAD of the absolute value correlation coefficient for differential times as measured on individual channels. Maximum allowed differential times were set as 0.5 s for P and 0.85 s for S. Differential time measurements were weighted as described by Shelly t l (2016), considering both the absolute value of the correlation coefficient measurement and difference in peak height with the second largest absolute value correlation measurement.

<table><tr><td colspan="3">TABLE 1Velocity Model Used for Relative Relocation</td></tr><tr><td>Top of Layer (km)</td><td>P-Wave Velocity (km/s)</td><td> $V_P/V_S$ </td></tr><tr><td>0</td><td>4.74</td><td>1.73</td></tr><tr><td>1</td><td>5.01</td><td>1.73</td></tr><tr><td>2</td><td>5.35</td><td>1.73</td></tr><tr><td>3</td><td>5.71</td><td>1.73</td></tr><tr><td>4</td><td>6.07</td><td>1.73</td></tr><tr><td>5</td><td>6.17</td><td>1.73</td></tr><tr><td>6</td><td>6.27</td><td>1.73</td></tr><tr><td>7</td><td>6.34</td><td>1.73</td></tr><tr><td>8</td><td>6.39</td><td>1.73</td></tr><tr><td>30</td><td>7.8</td><td>1.73</td></tr></table>

This model was constructed as an approximation to the Southern California Earthquake Center (SCEC) Community Velocity Model, with some modifications to make velocity transitions more gradual to reduce potential location artefacts.

Finally, all differential times were combined and input in the hypoDD double-difference relocation algorithm (Waldhauser and Ellsworth, 2000). During this combination process, I accounted for slightly different detection times of the same newly detected event by different templates by adjusting the origin time correction field available in hypoDD accordingly. In total, 8.6 million and 15.8 million correlation-derived differential P and S times, respectively, were input into hypoDD, in addition to 6.6 and 2.9 million SCSN catalog-derived differential P and S times, respectively. In the relocation process, starting locations were set to their SCSN locations for catalog events and to the median of the locations of detecting template events for newly detected events. The velocity model used in relocation is shown in Table 1.

All events retaining at least 12 P and 12 S correlationderived differential times were considered well located. In total, 34,091 events met these criteria and are reported here. Relocated depths are referenced to an approximate surface elevation of 0.7 km a.s.l. (the elevation of the town of Ridgecrest).

Magnitudes for newly detected events were estimated by comparison with catalog events of known magnitude, following the method described by Shelly et al (2016). These magnitudes were calibrated as by Shelly et al (2016) to match empirical scaling observed in SCSN catalog events. By examining pairs of catalog events for which relative amplitude measurements were also made, I find that a factor of 10 in amplitude corresponds to ∼0:83 SCSN $M _ { \mathrm { L } }$ magnitude units difference (Fig. 4). This empirical value is similar to previous studies (e.g., Shelly et al , 2016) and intermediate between theoretical small-magnitude scaling values of 1.0 for $M _ { \mathrm { L } }$ and 2/3 for $M _ { \mathrm { w } } .$ Magnitudes were left unchanged for SCSN catalog events, for which I retained the preferred network magnitudes.

## Caveats

The nature of the relocation process, in which relative locations are most precisely constrained by correlation-derived differential times, means that small- to moderate-magnitude event locations are usually best constrained. The locations constrained by differential times are then centroid, rather than hypocenter, locations. For several reasons, caution is advised in interpreting locations of the largest events. The largest earthquakes have increased waveform complexity, may have source durations longer than the longest periods considered, and do not have many other events of similar magnitude with which to naturally correlate. Therefore, the locations of these largest events are primarily hypocenter locations (as constrained by the catalog phase arrivaltime picks) but may be shifted somewhat by a small number of correlation-derived differential times. Thus, the relocated dataset presented here is not the best resource for those seeking accurate hypocenters (or centroids) of $M _ { \mathrm { w } } > \sim 5$ events (the $M _ { \mathrm { w } } \ 6 . 4$ and 7.1 mainshocks, in particular).

![](mineru/SHELLY2020_0220190309__paper/images/4f2f155bcc0f9e21088373a72988bd0ede923b37988e243198970714c5cc87cf.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/d655627b361ad18a11cb9da6765d85dfe20e4d2fd523b391b513c9a6fcaea94c.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/7c6367a8dd2fd464a21af5335ddbbe2ba3197847d9b683dd2c3d4f871e49a1e7.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/245e0ffcfe8a524d482943c3906a58d5d7687fbf11dc0c0ec6914ef805cac304.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/537084a404455360a6b268fd5a898ebc6ebcc703bc052aa6bb30ec4f84e1cc86.jpg)

![](mineru/SHELLY2020_0220190309__paper/images/e486a4d4ba3a7eb7d99bac223340d9eb5113136ff55645c6c71dc3acf74d58b5.jpg)  
Figure 5. Depth slices of relocated seismicity. All events preceding the $M _ { \mathrm { w } } ~ 7 . 1$ are shown in small blue dots. All events following the $M _ { \mathrm { w } } 7 . 1$ are shown in small red dots. Black lines indicate mapped surface rupture (both fully and not fully verified) (Kendrick et al , 2019).

This is a large and mostly unreviewed relocated dataset, including many small-magnitude events with low signalto-noise ratios. Large errors in locations may exist for a small subset of events. This dataset is intended to be interpreted in aggregate; locations of individual events should not be overinterpreted.

## Initial Results

The magnitude–time history of SCSN catalog and newly detected events is shown in Figure 2. This plot only shows the locatable events as described throughout this article; many additional events could be detected but lack sufficient data to precisely constrain their locations. As is evident in Figure 2, detection rates at smaller magnitudes vary strongly over the sequence, particularly during the hours following the $M _ { \mathrm { w } }$ 7.1 mainshock, when the seismic data are saturated by the codas of many moderated $( M _ { \mathrm { w } } \ 3 – 4 + )$ events. This strongly timevarying completeness magnitude will have to be carefully considered when subsequent b-value analyses are performed. The magnitude determination method $( \mathrm { e . g . } , M _ { \mathrm { L } }$ vs. $M _ { \mathrm { w } } )$ will also significantly impact resulting Gutenberg–Richter b-value estimates.

![](mineru/SHELLY2020_0220190309__paper/images/cf9d5e07dac959ea77f791be282995de1e296e84f063476028b98938f28b4a24.jpg)  
Figure 6. Distribution of foreshocks to the $M _ { \mathrm { w } }$ 6.4 event, relative to other seismicity. Plot shows a depth slice from 10 to 14 km depth. The foreshocks occur dominantly at 11–13 km depth, apparently along a northwest-striking fault that also ruptured during the $M _ { \mathrm { w } }$ 6.4 event.

The geometry of the Ridgecrest sequence seismicity is highly complex, dominated by numerous crosscutting northwest- and southwest-striking seismicity alignments, with nearly perpendicular trends (Figs. 1 and 5). These structures vary considerably by depth, but the shallow seismicity largely mirrors the complexity of the mapped surface rupture (Kendrick et al , 2019).

The 2019 Ridgecrest sequence began with a series of initially very small earthquakes. The first events detected here were $M _ { \mathrm { L } }$ 0.2 and 0.6 events at 15:35 and 15:42 (UTC), respectively, on 4 July. These two initial events were not included in the SCSN catalog, and they preceded the $M _ { \mathrm { w } }$ 6.4 event at 17:33 by ∼2 hr. The sequence began to ramp up with an $M _ { \mathrm { L } } \ 1 . 5$ at 16:13 and even more so with an $M _ { \mathrm { w } }$ 4.0 event at 17:02, the latter ∼30 min prior to the $M _ { \mathrm { w } }$ 6.4. Precise relocations suggest that this initial foreshock sequence (i.e., the foreshocks to the $M _ { \mathrm { w } }$ 6.4 event) activated a northwest-striking fault (Fig. 6).

The $M _ { \mathrm { w } }$ 6.4 event followed this foreshock sequence. Although surface rupture was verified only on a left-lateral, southwest-striking fault (K. Hudnut, oral comm., 2019), the foreshock and aftershock patterns strongly suggest that a nearly perpendicularly oriented, right-lateral northwest-striking fault also ruptured in the event. The aftershocks at depth clearly illuminate a northwest-striking structure (Figs. 5 and 6), likely the extension of the fault activated during the initial foreshock sequence. Based on this, the most likely scenario seems to be that the $M _ { \mathrm { w } }$ 6.4 rupture initiated on the right-lateral, northwest-striking fault, before activating the southwest-striking fault and eventually rupturing that fault to the surface.

The northwest-striking limb of the $M _ { \mathrm { w } }$ 6.4 aftershock sequence also shows at least two alignments of earthquake locations approximately perpendicular to this trend, which may reflect other left-lateral strike-slip faults (Fig. 7). Although at least one of these was activated early in the $M _ { \mathrm { w } }$ 6.4 aftershock sequence, a prominent structure was formed by the aftershocks of an $M _ { \mathrm { w } }$ 5.4 event at 11:07 on 5 July, which appeared to rupture the crosscutting left-lateral nodal plane striking toward the southwest rather than potential the right-lateral nodal plane striking northwest. Despite an apparent difference in slip orientation, the $M _ { \mathrm { w } }$ 5.4 event occurred in close proximity and about 16 hr prior to the $M _ { \mathrm { w } }$ 7.1 mainshock (Fig. 7).

The $M _ { \mathrm { w } }$ 7.1 mainshock dominantly ruptured in a rightlateral sense along a northwest-striking fault, yet aftershock patterns suggest considerable complexity (red events in Figs. 1 and 5; see also Movie S1), including numerous crosscutting southwest-striking alignments and multifault branching at the northwest and southeast rupture terminations. The $M _ { \mathrm { w } }$ 7.1 event apparently initiated at the northwestern edge of the $M _ { \mathrm { w } }$ 6.4 rupture, and based on aftershock locations and surface rupture, eventually extended the earlier rupture both to the northwest and to the southeast. This raises the intriguing issue of the rupture geometry in the area that previously ruptured in the $M _ { \mathrm { w } }$ 6.4 event. Did the $M _ { \mathrm { w } }$ 7.1 rerupture the area that ruptured in the $M _ { \mathrm { w } }$ 6.4? Based on the aftershock distribution, the $M _ { \mathrm { w } }$ 7.1 may have ruptured a subparallel fault southwest of the fault that ruptured in the $M _ { \mathrm { w } }$ 6.4, perhaps stepping back over toward the northeast to continue the earlier fault rupture toward the southeast (Fig. 7).

At least two fault strands were activated near the southeastern terminus of the $M _ { \mathrm { w } }$ 7.1 rupture. Although seismicity does not appear to extend south of the Garlock fault, some aftershocks may have occurred on the Garlock itself, particularly between 7 and 9 km depth (Figs. 1 and 5). The rupture geometry appears even more complex at the northwest rupture terminus, as reflected in both the surface rupture and the aftershock distribution. The aftershocks define numerous shallow fault planes in this area, dominantly on the northeast side of the main rupture, in the dilatational quadrant. These faults align in multiple orientations, including a northwest-striking set, a nearly perpendicular southweststriking set, and a set of faults that takes a mostly northerly strike, curving toward the northwest at their northerly tips. As the aftershock sequence progressed, this zone extended increasingly toward the northeast (Movie S2). An area of aftershocks even farther north, in the Coso geothermal field, was unresolved, including potential triggering relationships during the sequence, the cause and role of nearly perpendicular crosscutting faults, and the relationship between mainshock and aftershock fault activations. The wealth of available data for this sequence provides an important opportunity to move earthquake science forward.

![](mineru/SHELLY2020_0220190309__paper/images/fc2c97c5134cf184a0145a927e5cf18cb47bf7b9cb5d80e705704479b9f6bd9e.jpg)  
Figure 7. Interpreted map view of Ridgecrest sequence. Dashed lines indicate inferred fault structures based on seismicity alignments. Moment tensor for M 5.4 event is shown as blue focal mechanism plot, with inferred fault plane highlighted. Other symbols are as in Figure 1. Many features have sharper expressions in limited depth slices, as shown in Figure 5 and Movie S1.

## Data and Resources

Seismic waveform data and phase arrival-time data used in this study were downloaded from the Southern California Earthquake Data Center (SCEDC) at https:// scedc.caltech.edu/ (Southern California Earthquake Data Center [SCEDC], 2013, last accessed August 2019). Seismic stations used in this study were operated by Caltech, U.S. Geological Survey, UNAVCO, and University of Nevada, Reno. Supplemental material accompanies this article, including the detected and relocated seismic catalog presented here and two supplemental movies. The detected and relocated catalog can also be accessed from Shelly (2019).

## Acknowledgments

The author thanks Sarah Minson and two anonymous reviewers for their insightful reviews, which significantly improved this article. The author thinks Bill Ellsworth, Ken Hudnut, Gavin Hayes, Sue Hough, Ryan Gold, and Kate

apparently remotely triggered and is outside of the region examined here.

## Summary

The long-term investment in a high-quality, real-time seismic monitoring network in the area of the 2019 Ridgecrest earthquake sequence has provided an incredibly valuable dataset from which important lessons about earthquake physics will be learned. In this study, I leverage those investments to provide an enhanced high-resolution earthquake catalog, which can help facilitate some of these forthcoming discoveries. Numerous features of this sequence remain

Scharer for enlightening discussions regarding the Ridgecrest earthquake sequence and related observations. The author thanks Kyle Withers for assistance extracting the Southern California Earthquake Center (SCEC) Community Velocity Model. Figures 1 and 7 were made using Generic Mapping Tools software (Wessel et al , 2013).

## References

Frémont, M. J., and S. D. Malone (1987). High precision relative locations of earthquakes at Mount St. Helens, Washington, J Geophys R<sub>es</sub> 92, no. B10, 10,223–10,236.

Gibbons, S. J., and F. Ringdal (2006). The detection of low magnitude seismic events using array-based waveform correlation, Geophys J I<sub>n</sub>t 165, no. 1, 149–166.

Got, J. L., J. Fréchet, and F. W. Klein (1994). Deep fault plane geometry inferred from multiplet relative relocation beneath the south flank of Kilauea, J<sub>.</sub> G<sub>eop</sub>h<sub>ys.</sub> R<sub>es.</sub> 99, no. B8, 15,375–15,386.

Hauksson, E., W. Yang, and P. M. Shearer (2012). Waveform relocated earthquake catalog for southern California (1981 to June 2011), B<sub>u</sub>ll S<sub>e</sub>i<sub>smo</sub>l S<sub>oc</sub> A<sub>m</sub> 102, no. 5, 2239–2244.

Kendrick, K. J., S. O. Akciz, S. J. Angster, J. Avouac, J. L. Bachhuber, S. E. Bennett, K. Blake, S. Bork, B. A. Brooks, P. Burgess, et al (2019). Geologic observations of surface fault rupture associated with the Ridgecrest M6.4 and M7.1 earthquake sequence by the Ridgecrest Rupture Mapping Group, Poster Presentation at 2019 SCEC Annual Meeting, Palm Springs, California, 8–11 September 2019.

Peng, Z., and P. Zhao (2009). Migration ofearly aftershocks following the 2004 Parkfield earthquake, N<sub>a</sub>t<sub>ure</sub> G<sub>eosc</sub>i 2, 877–881, doi: 10.1038/ ngeo697.

Ross, Z. E., D. T. Trugman, E. Hauksson, and P. M. Shearer (2019). Searching for hidden earthquakes in Southern California, Science 364, no. 6442, 767–771.

Rubin, A. M., D. Gillard, and J. L. Got (1999). Streaks of microearthquakes along creeping faults, N<sub>a</sub>t<sub>ure</sub> 400, no. 6745, 635.

Shearer, P. M. (1994). Global seismic event detection using a matched filter on long-period seismograms, J G<sub>eop</sub>h<sub>ys</sub> R<sub>es</sub> 99, no. B7, 13,713–13,725.

Shelly, D. R. (2019). A high-resolution seismic catalog for the initial 2019 Ridgecrest earthquake sequence, U S Geological Survey Data Release, doi: 10.5066/P9JN6H0N.

Shelly, D. R., and D. P. Hill (2011). Migrating swarms of brittle-failure earthquakes in the lower crust beneath Mammoth Mountain, California, G<sub>eop</sub>h<sub>ys</sub> R<sub>es</sub> L<sub>e</sub>tt 38, L20307, doi: 10.1029/ 2011GL049336.

Shelly, D. R., G. C. Beroza, and S. Ide (2007). Non-volcanic tremor and low-frequency earthquake swarms, N<sub>a</sub>t<sub>ure</sub> 446, no. 7133, 305.

Shelly, D. R., W. L. Ellsworth, and D. P. Hill (2016). Fluid-faulting evolution in high definition: Connecting fault structure and frequency-magnitude variations during the 2014 Long Valley Caldera, California, earthquake swarm, J G<sub>eop</sub>h<sub>ys</sub> R<sub>es</sub> 121, no. 3, 1776–1795.

Shelly, D. R., S. C. Moran, and W. A. Thelen (2013). Evidence for fluid-triggered slip in the 2009 Mount Rainier, Washington earthquake swarm, G<sub>eop</sub>h<sub>ys</sub> R<sub>es</sub> L<sub>e</sub>tt 40, no. 8, 1506–1512.

Southern California Earthquake Data Center (SCEDC) (2013). Southern California Earthquake Data Center, Caltech Dataset, doi: 10.7909/C3WD3xH1.

Waldhauser, F. (2009). Near-real-time double-difference event location using long-term seismic archives, with application to Northern California, B<sub>u</sub>ll S<sub>e</sub>i<sub>smo</sub>l S<sub>oc</sub> A<sub>m</sub> 99, no. 5, 2736–2748.

Waldhauser, F., and W. L. Ellsworth (2000). A double-difference earthquake location algorithm: Method and application to the northern Hayward fault, California, B<sub>u</sub>ll S<sub>e</sub>i<sub>smo</sub>l S<sub>oc</sub> A<sub>m</sub> 90, no. 6, 1353–1368.

Waldhauser, F., and D. P. Schaff (2008). Large-scale relocation of two decades of northern California seismicity using cross-correlation and double-difference methods, J G<sub>eop</sub>h<sub>ys</sub> R<sub>es</sub> 113, no. B08311, doi: 10.1029/2007JB005479.

Waldhauser, F., W. L. Ellsworth, D. P. Schaff, and A. Cole (2004). Streaks, multiplets, and holes: High-resolution spatio-temporal behavior of Parkfield seismicity, G<sub>eop</sub>h<sub>ys</sub> R<sub>es</sub> L<sub>e</sub>tt 31, L18608, doi: 10.1029/2004GL020649.

Wessel, P., W. H. Smith, R. Scharroo, J. Luis, and F. Wobbe (2013). Generic mapping tools: Improved version released, Eos Trans AGU 94, no. 45, 409–410.