# Earth and Space Science

![](mineru/WEI2022_EA001979__paper/images/cfb7fb904f78ff74f4e7591ddcf132b28b04a2ea7461fc234789f49ba808e382.jpg)

## RESEARCH ARTICLE 10.1029/2021EA001979

## Key Points:

• Using most available data onshore and offshore, we developed a workflow to detect and locate earthquakes during the 2018 Kı̄lauea eruption

• The new catalog contains a total of 375,736 earthquakes between 1 March and 30 September 2018, 439% more than reported by the Hawaiian Volcano Observatory

• The new catalog provides a foundational data set, revealing rich information to better understand the eruption processes

## Supporting Information:

Supporting Information may be found in the online version of this article.

Correspondence to: X. Wei, xiaozhuo\_wei@uri.edu

## Citation:

Wei, X., Shen, Y., Caplan-Auerbach, J., & Morgan, J. K. (2022). An improved earthquake catalog during the 2018 Kı̄lauea eruption from combined onshore and offshore seismic arrays. Earth and Space Science 9 https://doi.org/10.1029/2021EA001979

Received 23 AUG 2021 Accepted 17 MAY 2022

## Author Contributions:

Conceptualization: XiaoZhuo Wei Formal analysis: XiaoZhuo Wei Funding acquisition: Yang Shen Methodology: XiaoZhuo Wei Supervision: Yang Shen Writing – original draft: XiaoZhuo We Writing – review & editing: XiaoZhuo Wei, Yang Shen, Jacqueline Caplan-Auerbach, Julia K. Morgan

# An Improved Earthquake Catalog During the 2018 Kı̄lauea Eruption From Combined Onshore and Offshore Seismic Arrays

XiaoZhuo Wei<sup>1</sup> , Yang Shen<sup>1</sup> , Jacqueline Caplan-Auerbach<sup>2</sup> , and Julia K. Morgan<sup>3</sup>

<sup>1</sup>Graduate School of Oceanography, University of Rhode Island, Narragansett, RI, USA, <sup>2</sup>Department of Geology, Western Washington University, Bellingham, WA, USA, <sup>3</sup>Department of Earth, Environmental and Planetary Sciences, Rice University, Houston, TX, USA

Abstract The Island of Hawai’i was formed by repeated eruptions of basalts at an oceanic hotspot. Kı̄lauea, the youngest among the subaerial volcanoes of the island, erupted intensely in 2018. The eruption provided an opportunity to look into the mechanisms that operate at the volcano and associated earthquake activities, as it was recorded simultaneously, for the first time, by onshore and offshore seismometers. We used most of the publicly available seismic data during the eruption period, including temporary arrays, to build a more complete earthquake catalog during the eruption than that provided by the Hawaiian Volcano Observatory. We used a short-time-average/long-time-average method to identify potential earthquakes. The detections were associated with events and automatically picked with P-wave and S-wave arrivals, which were used to locate the events in a three-dimensional velocity model. After re-examining these earthquake events, their coda/duration magnitudes were determined. The resulting half-year catalog contains 375,736 events with one of the highest daily earthquake numbers ever reported (6,128 on 21 June 2018). A great number of events were recorded during the caldera collapses, from its beginning until its rapid ending. The catalog also contains abundan events near the Pu’u‘ō‘ō vent and in the lower East Rift Zone, where an increase of seismicity in mid-July and August indicated a step-up in magma intrusion after the eruption

## 1. Introduction

In the year 2018, Kı̄lauea Volcano on the Island of Hawai’i went through a major eruption. The eruption was the most intense one observed at the volcano over the past 200 years, causing its caldera to collapse (Nea et al., 2019). The eruption was preceded by the inflation at Pu’u‘ō‘ō since mid-March and the collapse of the Pu’u‘ō‘ō vent on May 1 (UTC). The first fissure opened on May 4 (UTC) in the lower East Rift Zone and was followed by the 2018 $M _ { w }$ 6.9 Kalapana earthquake under the south flank of Kı̄lauea, which might have been trig gered by the dike intrusion in the East Rift Zone. In the following weeks, a total number of 24 fissures opened in the lower East Rift Zone, pouring out ∼0.8 km<sup>3</sup> or more of lava before the eruption completely ended (Nea et al., 2019). The extraction of magma led the lava lake level at the Kı̄lauea summit to drop at the start of May, and the summit caldera began to collapse at the end of May. The caldera collapse stopped, and the eruptive fissures became minimally active in early August. The last fissure eruptive activity was observed on September 6, mark ing the end of the 2018 Kı̄lauea eruption.

The eruption provided the volcanological community a great opportunity to pursue a number of scientific ques tions, including eruption triggering (Farquharson & Amelung,  2020; Patrick et al., 2020) and the subsequent caldera collapse mechanism (Anderson et al., 2019). Researchers from various agencies and institutions reacted quickly to this eruption. The rapid responses included deployment of several temporary seismic arrays (Figure 1), with the instrument types varying from broadband seismometers, ocean bottom seismometer (OBS), to noda seismometers (Shiro et al., 2021: Wei et al., 2021: Wu et al., 2020). Although the Hawajian Volcano Observator (HVO) successfully monitored the seismicity during the eruption, such as the down-rift dike intrusion and the caldera collapse, the existing catalogs only used the permanent seismic networks on land (Lengliné et al., 2021; Lin & Okubo, 2020; Shelly & Thelen, 2019). The permanent seismic networks had a larger inter-station distance in the lower East Rift Zone of Kı̄lauea, which limited its detection ability in this area. Furthermore, the permanent networks had no stations in the offshore area, making them poorly suited for monitoring the underwater after shocks of the 2018 $M _ { w }$ 6.9 Kalapana earthquake (Wei et al., 2021). Although there have been studies building detailed earthquake catalogs from template matching (Lengliné et al., 2021; Shelly & Thelen, 2019), their results could still be limited by the available waveform templates, particularly in the seismically less active areas before the eruption, including the offshore flank.

(a)  
![](mineru/WEI2022_EA001979__paper/images/9bf645c319bb24980102a1e8d63b7ef10105ca7f714cfb5f35b3057d980143be.jpg)  
Figure 1. (a) The station distribution map of this study. Different color symbols refer to seismic stations of different networks, as shown in the legend. Ka’ōiki-Hı̄le refers to the Ka’ōiki-Hı̄lea Seismic Zone. (b) An enlarged map of the Kı̄lauea region, including its caldera, its East Rift Zone, and its south flank area. The red dash circle marks the region within 4 km distance from 19.41°N, 155.275°W encircling the caldera stations. The lava flow map (red irregular areas) is from Zoeller et al. (2020).

To provide a more complete earthquake catalog as a foundational data set to better understand the eruption processes, we incorporated most of the available onshore and offshore seismic data in this study. The new catalog contains approximately fourfold more earthquakes compared with the existing HVO catalog of the same time span, and can be used to gain new insights into the initiation, development, and cessation of the eruption.

## 2. Data

We collected most of the available data on the Island of Hawai’i from March 1, 2018 to September 30, 2018 (Figure 1), including data from the following permanent networks: HVO (network code: HV; Okubo et al., 2014: Shiro et  al.,  2021), Pacific Tsunami Warning Center (network code: PT), and Global Seismograph Network (network code: IU). In addition, three temporary seismic networks were included: a rapid response nodal arra (network code: Z1; Wu et  al.,  2020), a rapid response OBS array (network code: Z6; Wei et  al.,  2021), and a four-station temporary broadband network(network code: 4S; Johnson et  al.,  2018). All of these data were downloaded from the Incorporated Research Institutions for Seismology (IRIS). Finally, the Raspberry Shake Network (network code: AM) was used as a supplementary network. We did not use the United States Nationa Strong-Motion Network (network code: ZU) as it had limited publicly available data.

The HVO network is the backbone among all of the networks (Shiro et al., 2021). Nearly all of the stations of the permanent networks were equipped with at least a velocity sensor, and a few stations were equipped only with accelerometers. Only the velocity components were used, unless acceleration components were the only choice.

The temporary networks provided additional station coverage during various periods over the time span of this study (Table 1). For the nodal network, we found some of its stations along a local highway contained highe levels of noise (Text S1 in Supporting Information S1), which could be produced by traffic. There were also notable instrumental malfunctions of the OBSs, described in detail by Wei et al. (2021), and the problematic OB components were not used in this study.

<table><tr><td colspan="3">Table 1Time Span of the Networks Used in This Study</td></tr><tr><td>Network code</td><td>Start time (UTC)</td><td>End time (UTC)</td></tr><tr><td>HV</td><td>-</td><td>-</td></tr><tr><td>PT</td><td>-</td><td>-</td></tr><tr><td>IU</td><td>-</td><td>-</td></tr><tr><td>Z1</td><td>2018-06-15</td><td>2018-07-26</td></tr><tr><td>Z6</td><td>2018-07-10</td><td>2018-09-16</td></tr><tr><td>4S</td><td>2018-07-27</td><td>-</td></tr><tr><td>AM</td><td>-</td><td>-</td></tr><tr><td colspan="3">Note. Dash indicates that the start time or the end time equals 2018-03-01 (UTC) and 2018-09-30 (UTC), respectively.</td></tr></table>

## 3. Methods

Because of the strongly uneven distributions of the seismicity and station coverage, we developed a workflow with parameters that were optimized via trial and error for the event and station distributions. The general workflow to construct the earthquake catalog in this study could be divided into the following steps. First, we marked the earthquake events on different seismometer components using earthquake triggers. Second, we associated the triggered time windows with different events. Third, we picked the P-wave and S-wave arrivals and located the events. Then, we re-associated the triggered time windows based on the resultant source time and locations. Finally, we measured the magnitude of each event and merged possibly duplicated events.

## 3.1. Earthquake Detection

To detect earthquakes, we first bandpass-filtered the raw OBS records with a four-corner zero-phase-shift Butterworth filter between 8 and 12 Hz, due

to the “6 Hz problem” (Wei et al., 2021). To keep the filters coherent but retain more energy, all the other raw records were filtered between 8 and 20  Hz. The design of the filters is to mainly focus on volcano-tectonic earthquakes, instead of long-period events. Then, we applied the recursive short-time-average/long-time-averag (STA/LTA) algorithm (Withers et al., 1998) in the ObsPy package (Beyreuther et al., 2010), to every component of all the seismic stations. The standard STA window and LTA window were set to 1 and 10 s, respectively. Fo the stations near the caldera (Figure 1b), which are within 4 km of the summit (∼19.41°N, ∼155.275°W), both of the windows were cut to half to have better temporal resolution for the intense seismicity produced by the caldera collapse (Text S2 in Supporting Information S1). The triggered window's starting threshold was set to 3. The window ending threshold was set to 1 for all of the OBSs and stations that had no nearby stations within 8 km, and 1.2 for the caldera stations and the remaining stations. The network AM was not included during this step due to its relatively lower recording quality.

## 3.2. Association

After the on and off times for the triggered windows were obtained, they were associated with different events by assuming the earliest triggered station as the initial source location and predicting the triggered windows at other stations for the P-wave and S-wave traveling with speeds of 5 and 3 km/s, respectively (Text S3 in Supporting Information S1). For the associated earthquakes, they were saved on all the recorded stations with the instrument responses removed to obtain the ground velocities.

## 3.3. Phase Picker

For all stations, the data were filtered between 8 and 20 Hz before automated phase picking. The P-wave was picked only on the vertical component unless the vertical component was not available. The S-wave was picked only on the horizontal components unless the horizontal components were not available.

The phase picker in this study was built on the polarization filter and kurtosis rate function (Text S3 in Supporting Information S1; Baillard et al., 2014; Ross et al., 2016). If a station had three-component data, the waveform was filtered with the polarization filter before phase picking. The P-wave and S-wave polarization filters were calculated and applied according to Ross et al. (2016). The time window to calculate the polarization filter was 0.4 s, while the time window to calculate the kurtosis rate was 0.75 s. The polarization filter value was assigned to the central point of the window, whereas the kurtosis rate value was assigned to the end point of the window. If the station with the earliest detection was in the caldera region, other stations within 6 km would have their polarization filter time windows reduced to 0.3 s. We found that the polarization filter was quite effective to separate the S-wave (Baillard et al., 2014; Ross et al., 2016).

Next, the kurtosis function and its time derivative were calculated on all of the components. The three transformations introduced by Baillard et al. (2014) were applied when calculating the kurtosis functions. The first maximum before the S-wave trial pick was recognized as the S-wave arrival, and the global maximum before the P-wave trial pick was recognized as the P-wave arrival. The exact pick time was then refined to the minimum before the maximum (Ross et al., 2016). The picks on three-component stations would not be accepted if their signal-to-noise ratios (SNRs) were less than 16 and 8 for P-wave and S-wave arrivals, respectively. The pick SNR was defined as the average energy in the time window after the pick divided by the average energy in twice the time window before the pick, similar to the definition of Baillard et al. (2014). These SNR requirements were reduced to 10 and 5 for single component seismometers, considering that there was no applicable polarization filter to improve the SNR.

To better pick P-wave arrivals, an iterative process would be initiated if no P-wave arrival was found after the above procedures. First, we doubled the time window and recalculated the kurtosis rate to see if a P-wave pick could be found in the widened window. If not, the original kurtosis rate function was further multiplied with an STA/LTA trigger. The STA/LTA trigger was less sensitive to short-period energy fluctuations and could help suppress kurtosis rate peaks produced by noise. If still no P-wave arrival could be found, one last step was to multiply the STA/LTA trigger with the recalculated kurtosis rate function. It would be declared no P-wave arriva recorded if the final step still yielded no reliable pick.

Finally, for each wave type and each event, the pick times out of three standard deviations from the average of all of the arrival times of each event were removed, following Baillard et al. (2014). This is a tradeoff between minimizing erroneous picks and possibly removing a station (or stations) that has (have) very different epicentra distances, which are yet undetermined at this stage.

In addition, for both the P-wave and S-wave picks, we also included a clustering analysis for the caldera stations (Text S4 in Supporting Information S1). Because of the caldera collapses, the seismicity near the caldera was intense, and the automatic picker occasionally picked the arrival of the previous or next event mistakenly. To reduce this kind of error, we divided all of the arrivals into two sets when the two centroids of arrival time clus ters were more than 1.8 s apart, whatever the wave type, unless there were less than three picks. The arrivals in different clusters would be located separately.

Examples of the phase picks are shown in Figure 2. To highlight the increased detection capacity of the combined onshore and offshore networks and a phase-picking procedure tailored to the very uneven distribution of seismicity and stations, none of the events in Figure 2 are included in the HVO catalog. It is clear that our automatic picker could yield reasonably reliable picks of P-wave and S-wave arrivals. There are unreliable picks, but the generally get down-weighted during the following localization process. The unreliable picks can be largely attrib uted to low SNRs, mostly on the nodal and OBS stations. The permanent stations with only one vertical compo nent are also susceptible to large phase picking errors.

## 3.4. Localization

For every event, the regional version NonLinLoc package (Lomax et al., 2000, 2001) was used to determine the maximum likelihood source origin time and location. The NonLinLoc package incorporates three-dimensiona velocity models and topographic masks, which are important to obtain more accurate earthquake origins (Lin Shearer, et al., 2014) with their depths not above the physical ground surface.

The P-wave velocity model of Park et al. (2009) was used to calculate wave travel times (Text S5 and Figure S in Supporting Information S1). However, part of our study region was not included in their model. We first calculated the average velocity profiles for the model of Park et al. (2009) at a topography interval of 100 m. Then th average profiles were signed to the grids outside of Park et al. (2009) model space but in the same topography range. The Vp/Vs ratio was fixed at 1.732, close to the average Vp/Vs presented by Lin, Amelung, et al. (2014), and was used to obtain the S-wave velocity model. This model was chosen mainly because it was constructed from both earthquake arrivals and offshore airgun records and had high resolution not only for the onshor structures, but also for the submarine south flank of Kı̄lauea. In addition, this model was integrated with the topography during its inversion (Park et al., 2009). The topography mask data (Figure 1) were obtained through the Global Multi-Resolution Topography MapTool (Ryan et al., 2009).

The NonLinLoc package offers five weights for the P-wave and S-wave arrivals, ranging from level 0 to level 4, corresponding to arrival time uncertainties of 0.1–2.0 s (Table S2 in Supporting Information S1). Level 0 was the

Time (s)

Time (s)  
(a)  
![](mineru/WEI2022_EA001979__paper/images/eab8507a56084b13048786853ff0333a0ffa060d6c10ec259d15ba6be7755ce6.jpg)

![](mineru/WEI2022_EA001979__paper/images/47f8eff056f5c66bbb62669d8c86d283627abcb3b05e37ee4027960bde9b3778.jpg)

![](mineru/WEI2022_EA001979__paper/images/5a8b79f25a7639f74e1b8d70d9139b1a3c0167f7d25aa37e083a0156ea8eb30a.jpg)

(b)  
Time (s)  
Time (s)  
![](mineru/WEI2022_EA001979__paper/images/263a49578d42fa2d0844288b62d415c9c4735ea6136abf5d9360923821343170.jpg)  
(c)

Time (s)  
![](mineru/WEI2022_EA001979__paper/images/1239bf40ee4995b025c162f8705b96c757adb467c47bb364dc24a4df16efa8d1.jpg)

Time (s)  
![](mineru/WEI2022_EA001979__paper/images/4724bc13cc7f6fd4bd560f213feea92596d7c93b904f921c77871d9abcd484f7.jpg)

Time (s)  
![](mineru/WEI2022_EA001979__paper/images/7984d67708cd43bcdde28791e8a6eb53088ef8f8cd453a29cb7bf118f8e9f4ec.jpg)  
Figure 2. Three examples of events with their P-wave and S-wave arrival picks. The three events, of $M _ { d } ^ { } 0 . 6 5 , 1 . 1 5 ,$ and 1.84, are located in different regions: (a) the caldera, (b) the East Rift Zone, and (c) the offshore region. All the traces were filtered between 8 and 20 Hz and normalized by their maximum amplitudes. The network, station, and components names are marked on the left side of the traces. The intense seismicity in the caldera can be seen from the left-most part of (a), where codas of the previous earthquake precede the new event. All traces are normalized to their maximum to better show the data quality.

highest whereas level 4 is given 0 weight. Generally speaking, the P-wave arrivals would be assigned an initia weight level of 0, and the S-wave arrivals would be assigned an initial weight level of 1 during the localization (Text S6 in Supporting Information S1), as the automatic P-wave picks were more accurate (Baillard et al., 2014). During the localization, the weight would be adjusted based on their travel time misfit.

## 3.5. Re-association

From all of the located events, we selected only the events with at least one valid P-wave arrival, no less than four total valid arrivals and the root-mean-square (RMS) misfit less than 1 s. An arrival would be considered as valid if its normalized weight remained more than 0.2 after the localization process (Text S6 in Supporting Information S1). The misfit criterion would be relaxed for events with a large number of arrival times and a slightly larger RMS misfit (Text S7 in Supporting Information S1). Then we replaced the station having the earliest detection (Sta1; Text S3 in Supporting Information S1) with the event location in the association workflow to find out if the other stations also recorded the same event. The detection time windows were no longer based on the inter-statio distance and the wave travel speeds, but rather on the arrival times directly predicted by the NonLinLoc package We saved the station where its observed detection window overlapped with the predicted window for the event (Text S7 in Supporting Information S1). In addition, the detections on the Raspberry Shake Network were also brought into analysis.

Then, these re-associated events were located again following the workflow described in Section 3.4

## 3.6. Magnitude Determination

We followed HVO's approach to determine the earthquake magnitudes. Our primary magnitude choice for an earthquake was the coda/duration magnitude (Eaton, 1992), not only because it is more accurate but also easy to measure for small earthquakes. The vertical component records with valid P-wave picks were used. All the traces were high passed with a six-corner zero phase-shift Butterworth filter above 0.75 Hz and converted to envelopes The envelopes were further smoothed with a 2 s long moving window before the coda durations were measured The coda was set to start at the P-wave arrival time and end when the smoothed envelope value dropped back to the background noise level. The background noise level was defined as the average of the smoothed envelope inside the noise window before the P-wave arrival. The length of the noise window was adjustable from 5 to 2 s with an interval of 0.5 s to avoid the energy from the previous event.

On each station, the magnitude $( M _ { d } )$ was calculated using the following equation:

$$
M _ {d} = - 0. 4 0 2 + 1. 6 4 9 \log_ {1 0} \tau + 0. 0 1 5 z + 0. 0 0 1 1 d + 0. 0 0 1 5 \tau - 0. 0 0 5 H (z - 2 6) + s t a c o r r\tag{1}
$$

where $\tau , d , z ,$ and stacorr are the coda duration in seconds, epicentral distance in kilometers, source depth in kilometers, and station correction term, respectively. And $H ( z )$ is the Heaviside function of z. The average of the magnitudes of different stations yielded the magnitude of the event and its standard deviation. Thus, at least two measurements were needed to calculate both values. For simplicity, no distance limitation was applied. A statio correction term of 0.272 was applied to all of the measurements. This value was roughly inferred from the cod duration time and the magnitude in the USGS ComCat catalog (U. S. Geological Survey, 2017).

During this step, we also removed the duplicate events. The criteria were that the difference in the origin times of the two events was less than 1 s and location differences less than $0 . 1 ^ { \circ }$ in latitude and longitude. If the two events did not have the same arrival information, we would use all the arrival times to relocate the event once more

No coda/duration magnitude would be given if an earthquake was closely followed by another one or its noise window before the P-wave arrival was contaminated by the previous event. For large earthquakes, the coda could be too long to measure accurately. For those events, we instead used local magnitudes (Richter, 1935).

On each station, the local magnitude $( M _ { L } )$ was calculated using the following equation:

$$
M _ {L} = \log_ {1 0} A - \log_ {1 0} A _ {0} (r) + s t a c o r r\tag{2}
$$

where $A , A _ { 0 } , r ,$ and stacorr are the observed Wood-Anderson seismometer peak amplitude in millimeters, the amplitude attenuation function in millimeters, hypocentral/slant distance in kilometers, and station correction term, respectively. According to Uhrhammer et al. (2011), the amplitude decay function $- \mathrm { l o g } _ { 1 0 } A _ { 0 } ( r )$ between 8 and 500 km can be expressed as:

$$
\begin{array}{l} - \log_ {1 0} A _ {0} (r) = 1. 1 1 \log_ {1 0} (r) + 0. 0 0 1 8 9 r + 0. 5 9 1 \\ + 0. 0 5 6 T _ {0} (\tilde {r}) - 0. 0 3 1 T _ {1} (\tilde {r}) - 0. 0 5 3 T _ {2} (\tilde {r}) - 0. 0 8 0 T _ {3} (\tilde {r}) - 0. 0 2 8 T _ {4} (\tilde {r}) + 0. 0 1 5 T _ {5} (\tilde {r}) \end{array}\tag{3}
$$

�where $T _ { n } \left( \tilde { r } \right)$ is the n the order first kind Chebyshev polynomials of � �:

$$
T _ {n} (\tilde {r}) = \cos (n \arccos \tilde {r})\tag{4}
$$

where

$$
\tilde {r} = 1. 1 1 3 6 6 \log_ {1 0} r - 2. 0 0 5 7 4\tag{5}
$$

projects $r \in [ 8 , 5 0 0 ] \mathrm { ~ t o ~ } \tilde { r } \in [ - 1 , 1 ]$ . More details, such as how to extend this equation for $r < \aleph$ km, can be found in Uhrhammer et al. (2011). The horizontal velocity records were converted to the Wood-Anderson seismographs with its calibrated transfer function (Uhrhammer et al., 1996) and bandpasses between 0.5 and 17.86 Hz. The peak amplitude was defined as half of the peak-to-peak value within a 0.8 s sliding window, which was the free period of the Wood-Anderson instrument. The center of sliding window search started from the earthquak source time until the end of the detection windows.

To reduce the uncertainty of the measurements, the local magnitude was measured only on stations with a valid pick. Similarly, only magnitudes within three standard deviations were used to calculate the earthquake magnitudes and their uncertainties.

Although all the above equations were originally formulated for California but directly carried out in the Island of Hawai’i, their errors could be limited, as the maximum epicentral distances in the Island of Hawai’i are not as large as in California.

## 4. Results

We associated 650,899 events and successfully located 503,339 of them. Among those events, 420,963 origin time and locations were used to perform the re-association. A total number of 392,977 events were finally located from the 392,789 events re-associated, and ended up with a final catalog of 375,736 earthquakes, approximatel fourfold more than the 69,686 earthquakes located by HVO (Figure 3a). For each event, there is at least one P-wave arrival to ensure the accuracy of its source location.

To assess the quality of our catalog, we compared our catalog with other existing catalogs of similar time span: the HVO catalog (Shiro et al., 2018), the caldera template matching catalog (Shelly & Thelen, 2019), and the East Rift Zone template matching catalog (Lengliné et al., 2021). The three catalogs were selected as their events do not fully overlap with each other. The HVO catalog compared here covered exactly the same time span with our study, while the caldera template matching catalog started on April 29 and ended on June 23. The East Rift Zone template matching catalog started on April 29 and ended on May 5. The details of the comparison are presented in Text S8–S11, Table S4, and Figure S2 in Supporting Information S1.

## 4.1. Earthquake Locations

The event spatial distributions in our new catalog and the HVO catalogs are quite similar (Figure 3). The majority of events are in the Kı̄lauea and Mauna Loa caldera areas, the Ka’ōiki-Hı̄lea Seismic Zone, the lower East Rif Zone of Kı̄lauea, the Hilina Fault Zone, and the Pāhala region. However, our new catalog shows more events in all of the above regions. We note that the earthquake clusters in the Kealakekua Fault Zone (Figure 1) only appear in our catalog. Deep events at depth ∼30 km were also observed in our catalog under the Kı̄lauea and Mauna Kea. In the Kı̄lauea region (Figure 4), both catalogs have abundant earthquakes in the caldera area, the Hilina Fault Zone and the East Rift Zone. Still, our catalog shows more events in the above regions and further reveals the Pu’u‘ō‘ō vent as another seismically active region during the eruption period. All of these suggest that the combined networks in our workflow detected smaller magnitude events not included in the HVO catalog. On th other hand, our catalog does have more scattered events, compared with the HVO catalog.

![](mineru/WEI2022_EA001979__paper/images/872119051ddaac4c65bb379a5605f97cfa29830f03f945f3ddb8f973666fa695.jpg)

![](mineru/WEI2022_EA001979__paper/images/8efc699890489c49e06040628d9c27c2585a72a803266c45882d7a6d7470fbf6.jpg)

(a)  
![](mineru/WEI2022_EA001979__paper/images/4ebf2b66992c3bc0b6f980c4e5e7a1a22116c2e290d09ba77e34a53e05661a7f.jpg)

![](mineru/WEI2022_EA001979__paper/images/52f6752b618096f5ee7642e94f66fec5fce6bca9a5eb4c0777d354d630a61fc8.jpg)

(b)  
![](mineru/WEI2022_EA001979__paper/images/0554f2ab37d0255d21c6cc39661358c96045cf5ab5cfeacaa9b8299d9b2f2009.jpg)  
(a) The event distribution map of the HVO catalog. The lava flow map (red irregular areas) is from Zoeller et al. (2020). The top and left panels are th longitudinal and latitudinal projections, respectively. (b) The event distribution map of our new earthquake catalog. The top and left panels are the longitudinal and latitudinal depth projections, respectively.

## 4.2. Earthquake Magnitudes

The majority of the earthquakes, 308,017 events, have a corresponding magnitude. Those without a magnitude are too small to have at least one P-wave pick for the coda/duration magnitude, not big enough to be measured by the local magnitude, or too close in time from the previous or next earthquake. The earthquake magnitud

(a)  
![](mineru/WEI2022_EA001979__paper/images/32245b17a09520beef60c9a258a3619dcb2a71edacdee1b805b7376b6b52b8d7.jpg)  
(b)

![](mineru/WEI2022_EA001979__paper/images/908b4076203a8861f5bbf2439c780b2cac256cc9cf1ac9509dd4b24d9c21d2a8.jpg)

![](mineru/WEI2022_EA001979__paper/images/bd7bbd98e2b6dc110f05633d07dd8925ee241758ad0ef744cac02706dfb54eb4.jpg)  
Figure 4. (a) The event distribution map of the HVO catalog in the Kı̄lauea region. The lava flow map (red irregular areas) is from Zoeller et al. (2020). The top and left panels are the longitudinal and latitudinal projections, respectively. (b) The enlarged event distribution map of our new catalog in the same region. Five dashed regions of red, cyan, pink, orange, and purple mark the caldera, the Hilina Fault Zone, Pu’u‘ō‘ō, the lower East Rift Zone, and the submarine south flank used in Figure 6, respectively. The top and left panels are the longitudinal and latitudinal depth projections, respectively.

(a)  
![](mineru/WEI2022_EA001979__paper/images/e48ebe121d584b2fe0ff36b3c1f02a70ff6e5aea5cf89bfd2cb16cfb63ebf0d0.jpg)

(b)  
![](mineru/WEI2022_EA001979__paper/images/e05483c3b46e67aa4a72c8ab915a8dd0498fe8adca8667aaa24b2ead8dff18c5.jpg)

(c)  
![](mineru/WEI2022_EA001979__paper/images/db61943d764162885406b13b613fe80aaa3e0cc1472f19a17ca7bf114010ca51.jpg)

(d)  
![](mineru/WEI2022_EA001979__paper/images/583d227be4a61da4ef1dcc80dd0013629472e46c1231b9c5a0fea88f8d768b2d.jpg)

(e)  
![](mineru/WEI2022_EA001979__paper/images/79bb0b83ff34cf79c8b2cd70bc80f50e46ed9aa8965ed448f7af635d7de463e8.jpg)

(f)  
![](mineru/WEI2022_EA001979__paper/images/8eba6f1d66ed39f5824359e281b105029c5119c430df6daa5de4f9e4b0d4ae26.jpg)  
Figure 5. The earthquake magnitude frequency distribution of (a) the HVO catalog and (b) our new catalog for the entire study period. The earthquake magnitud frequency distribution of (c) the HVO catalog and (d) our new catalog before and after the eruption (March, April, and September). The earthquake magnitude frequency distribution of (e) the HVO catalog and (f) our new catalog during the eruption period (May, June, July, and August). Notice the difference in the earthquake numbers of each panel.

frequency distributions (Figure 5) show that the magnitude of completeness $( M _ { c } )$ of our catalog, where the maximum curvature of the distribution appears, is around ∼1.4 and fairly consistent over different time periods. This $M _ { c }$ value is comparable to the results from the Southern California Seismic Network (Ross et al., 2019)

## 5. Discussion

## 5.1. Implications for the Caldera Collapse

The first collapse event (Neal et  al.,  2019) occurred on May 17 (UTC, 13  days after the eruption), and the large-scale and fault-bounded caldera collapses started on May 29, 25 days after the eruption initiated (Anderson et al., 2019; Neal et al., 2019). The onset of the collapse/explosion events followed a pulse of daily seismicity on May 16 (12 days after the eruption) found in our catalog (Figure 6a). Our new catalog also reveals that the dail earthquake number in the caldera region pulsed around May 24 (20 days after the eruption), slightly earlier tha the actual start of the large-scale caldera collapses.

(a)  
![](mineru/WEI2022_EA001979__paper/images/85591e0710ee392959ff09a87861f178a2de5430c96e468dde96efb6d99b074c.jpg)

(b)  
![](mineru/WEI2022_EA001979__paper/images/a819b98307028555b5888efa7aa3d98307e5a652acf5390c6959b1bd50a5bf37.jpg)

(c)  
![](mineru/WEI2022_EA001979__paper/images/90e11c2da443c7f128d9895b2b18b26be8de315f8b396f3ff944aa0a9e063e9b.jpg)

(d)  
![](mineru/WEI2022_EA001979__paper/images/75403d9577e74272eef035a7038cb5d95c8a0307202ba41ec35f630e09584898.jpg)

(e)  
![](mineru/WEI2022_EA001979__paper/images/6df2f6f5bc61c0eb900f8c0e5e4958db7b624d0325443e28a72670eaf1e29a05.jpg)  
Figure 6. The daily earthquake numbers of the five subregions in our catalog, (a) the Kīlauea caldera, (b) the Hilina Faul Zone, (c) Pu’u‘ō‘ō, (d) the lower East Rift Zone, and (e) the submarine south flank represented by the red, cyan, pink, orange, and purple curves, respectively. Black curves are the daily earthquake numbers from the HVO catalog. The onset of eruption is defined as May 4, 2018 (UTC), when the first fissure opened (Neal et al., 2019)

As the large-scale caldera collapse progressed, the seismicity in the caldera area became more and more intense. However, the sharp increase (from ∼3,000 to ∼6,000) of the daily earthquake events from June 16 (43 days after the eruption) to June 21 (48 days after the eruption) cannot be explained as the result of volcanic activity. Th deployment of nodal seismometers in the caldera area between June 15 and 16 (Table 1) did improve the earth quake detection ability in the caldera by doubling the total number of seismic stations (Figure 1). This is consistent with the fact that no sharp seismicity increase is found during the corresponding time period in the HVO catalog. For the same reason, the drop in event number around July 22 (79 days after the eruption) corresponds to the removal of nodal seismometers in the caldera area. Thus, caution is needed when interpreting the earthquake occurrence in our catalog with respect to time, as the effects of the network changes during the eruption period can be non-negligible. A possible way to account for this would be to use the cumulative seismic moment release (Gudmundsson et al., 2016), which is not yet available for Hawai’i, due to the inconsistency of the earthquake magnitudes among different catalogs (Text S11 in Supporting Information S1).

The end of the caldera collapse is reflected by the sudden drop in seismicity observed around August 6 (93 days after the eruption). Within 2 days, the daily earthquake event number dropped from ∼3,000 per day to ∼150 per day. This date is consistent with the time of the ending of summit subsidence reported by the HVO and the tim when the last fissure in the rift zone became minimally active (Neal et al., 2019), supporting the coupling of the caldera collapse and the rift eruption (Gudmundsson et al., 2016; Patrick et al., 2020; Sigmundsson, 2019) Compared with the initialization and the development of the caldera collapse, its termination is much more rapid

## 5.2. Implications for the Eruption Process

Our catalog also includes many events outside of the Kı̄lauea caldera area. The events clustered near the Hilina Fault Zone, the Pu’u‘ō‘ō vent, and the lower East Rift Zone during the first 20 days after the eruption started (Figures 3a and 6b–6d). Previous study has shown the activation of a shallow detachment in the Hilina Fault Zone during the eruption (Lin & Okubo, 2020).

A sharp increase of the located events is found near the Pu’u‘ō‘ō vent, compared with the HVO catalog (Figure 6c). Unlike the Hilina Fault Zone, the Pu’u‘ō‘ō region started to exhibit a high rate of seismicity rate on May 1 (3 days before the eruption), due to its crater floor and lava lake collapse, along with the intrusion caused by the critical level pressurization in the plumbing system (Patrick et  al.,  2020). The daily seismicity stayed around 80–100 events during the following 30 days and gradually reduced to the pre-eruption level by mid-July (∼80 days after the eruption). Although the exact end time of the Pu’u‘ō‘ō vent collapse is unclear, our catalog suggests the date must be prior to the mid-July. This decay of the seismic rate may indicate the reduction of magma transport through the Pu’u‘ō‘ō region. More interestingly, the seismicity gradually increased again within a few days back to ∼40 events per day, much higher than the pre-eruption seismicity level in March. In addition Poland et al. (2019) suggested that both uplift and spreading were observed near the Pu’u‘ō‘ō vent, since the end of major eruptive activity in August 2018, which is roughly the same period we observed the increase of seismicity. Both our seismic and the geodetic observations indicate the post-eruption magma reservoir refilling occurred near Pu'uōō.

Earthquake occurrence in the lower East Rift Zone shows a similar pattern as the Pu’u‘ō‘ō area (Figure 6d). Th daily earthquake number started to rise also on May 1 (3 days before the eruption). as the result of down-rift dike intrusion (Lengliné et al., 2021). The peak seismicity took place on May 10 (6 days after the eruption), which may still be the result of the dike intrusion, because new fissures started to form in the same area only 2 days later (Gansecki et al., 2019). The high seismicity rate was also observed by HVO (Neal et al., 2019; Shiro et al., 2018) Similar to the Kı̄lauea caldera area, an apparent increase and a decrease of daily seismic events around June 16 (43 days after the eruption) and July 24 (81 days after the eruption) correspond to the seismic network changes of the nodal array (Table 1). Another sharp increase of seismicity occurred on August 9 (97 days after the eruption) which was a few days later than the time when seismicity in Pu’u‘ō‘ō increased. The deployment of the network 4S should not be the cause as it happened at the end of July. Thus, we interpret this earthquake rate increase as another piece of evidence of the post-eruption magma refilling in the lower East Rift Zone.

## 5.3. Implications for the Activation of the Submarine South Flank

The 2018 $M _ { w }$ 6.9 Kalapana earthquake took place on the submarine south flank of Kı̄lauea on May 4. It ruptured a large area of the mobile south flank (e.g., Liu et al., 2018) and was the third major earthquake that happened along the décollement fault since 1908 (Klein et al., 2001).

Background seismicity in the offshore region, typically one or two earthquakes per day, is lower than in all of the other regions (Figure 6) and could be the results of both sparse station coverage and less active local structures. The daily earthquake number started to rise also on May 1 (3 days before the eruption), displaying a similar varying pattern compared with the lower East Rift Zone. The seismicity peaked on May 4, with the occurrence of the $M _ { w }$ 6.9 earthquake, contributed by both the aftershocks and events associated with the dike intrusion. The daily earthquake numbers dropped back to low levels (∼15 events per day) very quickly, over ∼25 days, indicating a short aftershock duration of the $M _ { w } 6 . 9$ earthquake. This is consistent with the notion that the aftershock duration varies inversely with the fault loading rate (Stein & Liu, 2009). The submarine south flank has a fast shortening rate of 30–60 cm/yr (Morgan et al., 2003), equivalent to a slip rate of 45–150 cm/yr along the décollement fault (e.g., Delaney et al., 1993; Owen et al., 1995, 2000).

The deployment of the OBS array was associated with a significant increase of detected events (Figure 6d). We note that compared with the initial results by Wei et al. (2021), the event numbers were reduced due to the following three reasons: First, we introduced the re-association process and found some previously detected offshore events were actually the S-waves of earthquakes that took place in the lower East Rift Zone. Second, we applie a more strict SNR check for the picks, removing some low SNR picks for the OBS stations. Finally, we found that station KSFG often picked the $\mathrm { S p }$ phase as the P-wave arrival, so our catalog did not include those events in which only station KSFG had P-wave picks. Overall, the OBS data quality is not as good as onshore data. More work is required, including manual inspection of all located offshore events and the use of template matching, to better understand the activation of the submarine south flank during the 2018 Kı̄lauea eruption.

## 6. Conclusions

In this study, we combined most of the available onshore and offshore seismic data during the 2018 Kı̄lauea eruption and developed a workflow tailored to the very uneven seismicity and station coverage to detect, associate, and locate earthquakes in the Island of Hawai’i. The earthquake magnitudes were calculated for the re-associated events. The final earthquake catalog contains 375,736 events with an $M _ { c }$ of ∼1.4. There is a fourfold increase of the event number compared with the HVO catalog. The $M _ { c }$ of our catalog ∼1.4 is also considerably lower tha (about half of) the HVO value during the same period. The located earthquakes are mainly distributed around the Mauna Loa summit, the Kı̄lauea summit, and the East Rift Zone of Kı̄lauea. In all the regions around Kı̄lauea, the seismicity peaked with the onset of the volcano eruption at the beginning of May, except the caldera region. The most intense seismicity near Kı̄lauea caldera is observed during the caldera collapse process, which built up gradually from May to June but ended abruptly in August. In addition, post-eruption lava refilling is inferred from the increase of seismicity near Pu’uōō and in the lower East Rift Zone since August. The seismicity under the submarine south flank dropped back to low levels in a few weeks after the main shock, which indicates a shor duration of aftershocks, consistent with the fast slip rate along the basal décollement fault

Overall, the new catalog provides a foundational data set, from which the earthquake locations can be refined, new waveform templates can be extracted to further improve the earthquake detection and localization, and new seismic arrival times can be used in tomographic inversion, just to name a few. It is thus a useful data set to better understand the eruption process, from the initiation to the dike intrusion, until the final caldera collapse.

## Data Availability Statement

All of the seismic data of this study are publicly available from IRIS. under the network code HV. PT. Z1. Z6. 4S and from RASPISHAKE, under the network code AM. The ComCat catalog is publicly available from https:// earthquake.usgs.gov (last accessed 2 April 2021). The resultant earthquake catalog of this study is publicl available in the supplement or from the Dryad digital repository (Wei et al., 2022). The NonLinLoc Version 7.00 package can be downloaded from http://alomax.free.fr/nlloc/index.html (last accessed 16 February 2021).

## Acknowledgments

The authors thank all of the people involved in the deployment and main. tenance of all of the seismic networks used in this study, and Kevin Bryan for helping with the data processing at the High Performance Research Computing facility at University of Rhode Island. The authors thank Dr. Brian Shiro and Dr. Jefferson Chang of USGS for kindly answering our questions and providing useful information including station responses and magnitude determination procedures. The authors thank Dr. Anthony Lomax for the software NonLinLoc, making it open-accessed, and answering questions regarding its usage. The careful review of Dr. Brian Shiro and an anonymous reviewer are appreciated. This study is supported by the NSF Grant no. 1949620.

## References

Anderson, K. R., Johanson, I. A., Patrick, M. R., Gu, M., Segall, P., Poland, M. P., et al. (2019). Magma reservoir failure and the onset of caldera collapse at Kīlauea Volcano in 2018. Science, 366(6470), eaaz1822. https://doi,org/10.1126/science,aaz1822

Baillard, C., Crawford, W. C., Ballu, V., Hibert, C., & Mangeney, A. (2014). An automatic kurtosis-based P-and S-phase picker designed for local seismic networks. Bulletin of the Seismological Society of America, 104(1), 394–409. https://doi.org/10.1785/0120120347

Beyreuther, M., Barsch, R., Krischer, L., Megies, T., Behr, Y., & Wassermann, J. (2010). ObsPy: A Python toolbox for seismology. Seismologica Research Letters, 81(3), 530–533. https://doi.org/10.1785/gssrl.81.3.530

Delaney, P. T., Miklius, A., Árnadóttir, T., Okamura, A. T., & Sako, M. K. (1993). Motion of Kilauea volcano during sustained eruption from the Puu Oo and Kupaianaha vents, 1983–1991. Journal of Geophysical Research, 98(B10), 17801–17820. https://doi.org/10.1029/93JB01819

Eaton, J. P. (1992). Determination of amplitude and duration magnitudes and site residuals from short-period seismographs in Northern Califor Bulletin of the Seismological Society of America 82

Farquharson, J. I., & Amelung, F. (2020). Extreme rainfall triggered the 2018 rift eruption at Kı̄lauea Volcano. Nature, 580(7804), 491–495. https://doi.org/10.1038/s41586-020-2172-5

Gansecki, C., Lee, R. L., Shea, T., Lundblad, S. P., Hon, K., & Parcheta, C. (2019). The tangled tale of Kı̄lauea’s 2018 eruption as told by geochemical monitoring. Science, 366(6470), eaaz0147. https://doi.org/10.1126/science.aaz0147

Gudmundsson, M. T., Jónsdóttir, K., Hooper, A., Holohan, E. P., Halldórsson, S. A., Ófeigsson, B. G., et al.,(2016). Gradual caldera collapse at Bárdarbunga volcano, Iceland, regulated by lateral magma outflow. Science, 353(6296), aaf8988. https://doi.org/10.1126/science.aaf8988

Johnson, J. H., Herd, R., Eyles, J., Shiro, B., & McLeod, B. (2018). Shear wave splitting tomography at Kilauea. In AGU Fall Meeting 2018 (V43J-0293).

Klein, F. W., Frankel, A. D., Mueller, C. S., Wesson, R. L., & Okubo, P. G. (2001). Seismic hazard in Hawaii: High rate of large earthquake and probabilistic ground-motion maps. Bulletin of the Seismological Society of America, 91(3), 479–498. https://doi.org/10.1785/0120000060

Lengliné, O., Duputel, Z., & Okubo, P. (2021). Tracking dike propagation leading to the 2018 Kı̄lauea eruption. Earth and Planetary Science Letters, 553, 116653. https://doi.org/10.1016/i.epsl.2020.116653

Lin, G., Amelung, F., Lavallée, Y., & Okubo, P. G. (2014). Seismic evidence for a crustal magma reservoir beneath the upper east rift zone of Kilauea volcano, Hawaii. Geology, 42(3), 187–190. https://doi,org/10.1130/G35001.1

Lin, G., & Okubo, P. G. (2020). Seismic evidence for a shallow detachment beneath Kı̄lauea’s south flank during the 2018 activity. Geophysica Research Letters, 47(15), e2020GL088003. https://doi.org/10.1029/2020GL08800

Lin, G., Shearer, P. M., Matoza, R. S., Okubo, P. G., & Amelung, F. (2014). Three-dimensional seismic velocity structure of Mauna Loa and Kilauea volcanoes in Hawaii from local seismic tomography. Journal of Geophysical Research: Solid Earth, 119(5), 4377–4392. https://doi. org/10.1002/2013JB010820

Liu, C., Lay, T., & Xiong, X. (2018). Rupture in the 4 May 2018 Mw 6.9 earthquake seaward of the Kilauea east rift zone fissure eruption in Geophysical Research Letters 45

Lomax, A., Virieux. J., Volant. P., & Berge-Thierry, C. (2000). Probabilistic earthquake location in 3D and lavered models. In C. H. Thurber, & N. Rabinowitz (Eds.), Advances in seismic event location (pp. 101–134). Springer. https://doi.org/10.1007/978-94-015-9536-0\_5

Lomax. A., Zollo. A., Capuano, P.. & Virieux. J. (2001). Precise, absolute earthquake location under Somma–Vesuvius volcano using a ney three-dimensional velocity model. Geophysical Journal International, 146(2), 313–331. https://doi.org/10.1046/j.0956-540x.2001.01444.x

Morgan, J. K., Moore, G. F., & Clague, D. A. (2003). Slope failure and volcanic spreading along the submarine south flank of Kilauea volcano, Hawaii. Journal of Geophysical Research, 108(B9), 2415. https://doi.org/10.1029/2003JB002411

Neal, C. A., Brantley, S., Antolik, L., Babb, J., Burgess, M., Calles, K., et al. (2019). The 2018 rift eruption and summit collapse of Kı̄laue Volcano. Science, 363(6425), 367–374. https://doi.org/10.1126/science.aav7046

Okubo, P. G., Nakata, J. S., Koyanagi, R. Y., Poland, M., Takahashi, T., & Landowski, C. (2014). The evolution of seismic monitoring systems at U. S. Geological Survey Professional Paper, 1801

Owen, S., Segall, P., Freymueller, J., Mikijus, A., Denlinger, R., Árnadóttir, T., et al. (1995). Rapid deformation of the south flank of Kilauea volcano, Hawaii. Science, 267(5202), 1328–1332. https://doi,org/10.1126/science,267.5202.132

Owen, S., Segall, P., Lisowski, M., Miklius, A., Denlinger, R., & Sako, M. (2000). Rapid deformation of Kilauea Volcano: Global positioning system measurements between 1990 and 1996. Journal of Geophysical Research, 105(B8), 18983–18998. https://doi.org/10.1029/2000JB90010

Park, J., Morgan, J. K., Zelt. C. A., & Okubo, P. G. (2009). Volcano-tectonic implications of 3-D velocity structures derived from joint active and passive source tomography of the island of Hawaii. Journal of Geophysical Research, 114(B9), B09301. https://doi.org/10.1029/2008JB005929

Patrick, M., Houghton, B., Anderson, K., Poland, M., Montgomery-Brown, E., Johanson, I., et al. (2020). The cascading origin of the 2018 Kı̄lauea eruption and implications for future forecasting. Nature Communications, 11(1), 5646. https://doi.org/10.1038/s41467-020-19190-

Poland, M. P., de Zeeuw-van Dalfsen, E., Bagnardi, M., & Johanson, I. A. (2019). Post-collapse gravity increase at the summit of Kı̄lauea volcano Geophysical Research Letters 46

Richter, C. F. (1935). An instrumental earthquake magnitude scale. Bulletin of the Seismological Society of America, 25(1), 1–32. https://doi org/10.1785/BSSA0250010001

Ross, Z. E., Trugman, D. T., Hauksson, E., & Shearer, P. M. (2019). Searching for hidden earthquakes in Southern California. Science, 364(6442), 767–771. https://doi.org/10.1126/science.aaw6888

Ross, Z. F., White, M., Vernon, F., & Ben-Zion, Y. (2016). An improved algorithm for real-time S-wave picking with application to the (augmented) ANZA network in Southern California. Bulletin of the Seismological Society of America, 106(5), 2013–2022. https://doi org/10.1785/0120150230

Ryan, W. B., Carbotte, S. M., Coplan, J. O., O’Hara, S., Melkonian, A., Arko, R., et al. (2009). Global multi-resolution topography synthesis Geochemistry, Geophysics, Geosystems 10

Shelly, D. R., & Thelen, W. A. (2019). Anatomy of a caldera collapse: Kı̄lauea 2018 summit seismicity sequence in high resolution. Geophysical Research Letters, 46(24). 14395–14403. https://doi.org/10.1029/2019GL085636

Shiro, B., Burgess, M. K., Chang, J. C., Dotray, P., Okubo, P., Thelen, W. A., et al. (2018). Earthquake sequences of the 2018 Kı̄lauea Volcano eruption. In AGU Fall Meeting 2018 (V41B-01).

Shiro, B., Zoeller, M. H., Kamibayashi, K., Johanson, I., Parcheta, C., Patrick, M. R., et al. (2021). Monitoring network changes during the 201 Kı̄lauea Volcano eruption. Seismological Research Letters, 92(1), 102–118. https://doi.org/10.1785/0220200284

Sigmundsson, F. (2019). Calderas collapse as magma flows into rifts. Science, 366(6470), 1200–1201. https://doi.org/10.1126/science.aaz7126

Stein, S., & Liu, M. (2009). Long aftershock sequences within continents and implications for earthquake hazard assessment. Nature, 462(7269) 87–89. https://doi.org/10.1038/nature08502

Uhrhammer, R. A., Hellweg, M., Hutton, K., Lombard, P., Walters, A., Hauksson, E., & Oppenheimer, D. (2011). California Integrated Seis mic Network (CISN) local magnitude determination in California and vicinity. Bulletin of the Seismological Society of America, 101(6), 2685–2693. https://doi.org/10.1785/0120100106

Uhrhammer, R. A., Loper, S. J., & Romanowicz, B. (1996). Determination of local magnitude using BDSN broadband records. Bulletin of the Seismological Society of America 86

U.S. Geological Survey. (2017). Earthquake hazards program, 2017, Advanced national seismic system (ANSS) comprehensive catalog of earth quake events and products: Various

Wei, X., Shen, Y., Caplan-Auerbach, J., & Morgan, J. K. (2021). An OBS array to investigate offshore seismicity during the 2018 Kı̄lauea erup tion. Seismological Research Letters, 92(1), 603–612. https://doi.org/10.1785/0220200206

Wei, X., Shen, Y., Caplan-Auerbach, J., & Morgan, J. K. (2022). An improved earthquake catalog during the 2018 Kilauea eruption from combined onshore and offshore seismic arrays. Dryad. https://doi.org/10.5061/dryad.np5hqbzw9

Withers, M., Aster, R., Young, C., Beiriger, J., Harris, M., Moore, S., & Trujillo, J. (1998). A comparison of select trigger algorithms for automated global seismic phase and event detection. Bulletin of the Seismological Society of America, 88(1), 95–106. https://doi.org/10.1785 BSSA0880010095

Wu, S.-M., Lin, F.-C., Farrell, J., Shiro, B., Karlstrom, L., Okubo, P., & Koper, K. (2020). Spatiotemporal seismic structure variations associated with the 2018 Kı̄lauea eruption based on temporary dense geophone arrays. Geophysical Research Letters, 47(9), e2019GL086668. https:/ doi.org/10.1029/2019GL086668

Zoeller, M., Perroy, R., Wessels, R., Fisher, G., Robinson, J., Bard, J., et al. (2020). Geospatial database of the 2018 lower East Rift Zone eruption of Kı̄lauea volcano. Hawai'i. U.S. Geological Survey Data Release. https://doi.org/10.5066/P9S7UQKQ

## References From the Supporting Information

Anchieta, M. C., Wolfe, C. J., Pavlis, G. L., Vernon, F. L., Eakins, J. A., Solomon, S. C., et al. (2011). Seismicity around the Hawaiian Islands recorded by the PLUME seismometer networks: Insight into faulting near Maui, Molokai, and Oahu. Bulletin of the Seismological Society of America, 101(4), 1742–1758. https://doi.org/10.1785/0120100271

Dawson, P., & Chouet, B. (2014). Characterization of very-long-period seismicity accompanying summit activity at Kı̄lauea Volcano, Hawai’i: 2007–2013. Journal of Volcanology and Geothermal Research, 278, 59–85. https://doi.org/10.1016/j.jvolgeores.2014.04.010

Jin, X., & Han, J. (2010). K-means clustering. In C. Sammut, & G. I. Webb (Eds.), Encyclopedia of machine learning (pp. 563–564). Boston, MA Springer US. https://doi.org/10.1007/978-0-387-30164-8\_425

Lomax, A. (2005). A reanalysis of the hypocentral location and related observations for the great 1906 California earthquake. Bulletin of th Seismological Society of America, 95(3), 861–877. https://doi.org/10.1785/012004014

Matoza, R. S., Shearer, P. M., & Okubo, P. G. (2014). High-precision relocation of long-period events beneath the summit region of Kilauea Volcano, Hawaii, from 1986 to 2009. Geophysical Research Letters, 41(10), 3413–3421. https://doi,org/10.1002/2014GL059819

Shen, H., & Shen, Y. (2021). Array-based convolutional neural networks for automatic detection and 4D localization of earthquakes in Hawai'i Seismological Research Letters 92