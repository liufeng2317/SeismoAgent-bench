# Supporting Information for “An improved earthquake catalog during the 2018 K¯ılauea eruption from combined onshore and ofshore seismic arrays” XiaoZhuo Wei<sup>1</sup>, Yang Shen<sup>1</sup>, Jacqueline Caplan-Auerbach<sup>2</sup>, Julia K.

Morgan<sup>3</sup>

<sup>1</sup>Graduate School of Oceanography, University of Rhode Island, Narragansett, RI, United States

<sup>2</sup>Geology Department, Western Washington University, Bellingham, WA, United States

<sup>3</sup>Department of Earth, Environmental and Planetary Sciences, Rice University, Houston, TX, United States

## Contents of this file

1. Text S1 to S11

2. Figures S1 to S2

3. Tables S1 to S4

4. Dataset S1

## Introduction

In the supplement, we provide a full list of the noisy nodal stations (Text S1). We describe the details of our methods, from earthquake detection (Text S2), association (Text S3, Table S1) and phase picking (Text S4), to the velocity model used (Text S5, Figure S1), localization (Text S6, Table S2) and re-association (Text S7, Table S3). The

Corresponding author: XiaoZhuo Wei (xiaozhuo wei@uri.edu)

diferences between our catalog and other existing catalogs are compared in Text S8 and Table S4. For the HVO catalog, our detailed comparison also includes the phase pick diferences (Text S9), source time and location diferences (Text S10) and magnitude diferences (Text S11). Finally, the resultant earthquake catalog of this study is included as Dataset S1.

## Text S1. Data

Some stations in the nodal array sufered from trafic noise. The identified noisy stations included No. 31 - No. 60, No. 77, No. 90 - No. 91, No. 100 and No. 102 - No. 106.

## Text S2. Detection

Occasionally a short-time-average/long-time-average (STA/LTA) triggered window could contain more than one event. To reduce possible wrong associations, any triggered window longer than 25 s was cut into two windows. Any triggered window shorter than 2 s, if not detected on a caldera station, was discarded to avoid possible noise. In practice, we found that despite the use of the shortened LTA window for the caldera stations (5 s), the intense seismicity there could still cause the trigger to mis-identify two earthquakes into one. Thus, we introduced a triggered window length checking and cutting step, as explained in detail in Text S3.

## Text S3. Association

Because of the strongly uneven distributions of earthquakes and seismic stations, we found it necessary to have variable association criteria for the optimum results.

The location of the station with the earliest detection window start time, if not a nodal station, was used as the initial and approximate earthquake source location. If the station belonged to a caldera station, the source would be chosen as the station with the earliest window central time among the caldera stations. This re-selection procedure was added to increase reliability, as the stations around the caldera were not evenly distributed. For the stations whose closest nearby station was more than 10 km away, they wouldn’t be assumed to be the source station unless the window was longer than 3 s, to increase the reliability. If the station had more than one component, a cross-check would be performed among the components to make sure that this triggered window overlapped with another triggered window by at least 50% on at least one other component. Otherwise, the triggered window would be considered to be produced by noise instead of earthquakes and discarded.

Once the first station (denoted as Sta1) was found, we would check the other stations one by one as follows, according to their distances from Sta1, to see which station also recorded the same earthquake:

1. We chose a reference triggered window first in the following way: For each station (denoted as Staj), we found the closest one that recorded the same earthquake (denoted as Stac), and used it as a center to find the other stations within a certain radius. The radius was set to 10% of the distance between Sta1 and Staj, but no greater than 4 km. If there were more than two components on the stations within the circle that recorded the earthquake, the reference triggered window would be set to have their medium start and end time. Otherwise, the reference triggered window would be set to have their earliest start time and the latest end time. However, if the distance between Staj and Stac was greater than a threshold distance, which was defined as the greater value of the distance from one station (Staj or Stac) to its eighth station from it, no further steps would be performed on Staj, and the process would move on to the next station. The eighth station from it was revised to be the sixth if the station (Staj or Stac) was separated from all other stations by at least 12 km.

2. We shifted the reference triggered time window by assuming a P-wave speed of 5 km/s and a S-coda speed of 3 km/s. The S-coda speed might be faster than the actual case, but this value was found to help reduce the wrong association in regions with sparse station distributions. The distance used to calculate the time shift was the average distance from Staj to the two stations (around Stac), whose window times were selected to be the reference window time.

3. All of the components of Staj were checked to see if the next triggered window overlapped with the shifted window for a certain threshold, which decreases with distance in the step above (Table S1), as the efect of three-dimensional velocity structures would lead to larger travel time prediction error as distance increased. If the distance used to calculate time shift is larger than 16 km but there were stations within 8 km range of the two reference stations, the threshold would be increased by 10% to increase the reliability and reduce the possibility of mistakenly associating two diferent events into one. If Sta1 was in the caldera area and Staj was within 8 km range of Sta1, a special window length check would be applied: if the window length of Staj was more than twice the length of the shifted window, the window of Staj would be cut to a comparable length to re-check if it overlapped with the shifted reference time window. The overlapping check on Staj with the shifted window would move from the first window to the last window on each component, as long as the station was more than 4 km away from Sta1, or the window was cut from an original window, until it found the beginning of a new window was later than the end of the shifted reference window and stopped.

4. After checking all of the components of Staj and finding some components recording the earthquake, we would again make sure all of the found time windows on diferent components overlapped with each other. If not, we considered the recording unreliable. This step was similar to the procedure applied when we tried to find Sta1. However, here we required an overlap of at least 40% instead of 50%. If the window was the only window or the windows did not overlap with each other, we considered the recording unreliable, not labeling them components that recorded this earthquake.

5. If in the end no components of Staj recorded the earthquake, we would move on to the next station. If this is the fourth station away from Sta1 and there hasn’t been a second station recording the earthquake, we would consider the triggers on Sta1 not reliable or the event not big enough and move to associate the next event.

An earthquake would be saved if it was detected on more than three stations or had more than six arrivals. The detections on the nodal stations listed in Text S1 were not taken into account. Additionally, two events were required to be separated by a certain amount of time, allowing the S-coda from the previous event to arrive earlier than the earliest detection on Sta1.

## Text S4. Phase Picker

For every station, the automatic phase picker started with finding the trial picks for the S-wave, which would be assigned as the maximum point of the twenty-datapoint-smoothed amplitude waveform. The triggered window start and end times were re-selected as the medium time values on all of the components. The window start time would be moved forward 20% of its length but no longer than 1 s, if not overlapped with the previous windows, and the window end time would be added 1 s as well. For those events with

Sta1 in the caldera or with a window length shorter than 3 s, no extension would be applied to the window end time.

The S-wave arrival would be picked as the first maximum of the kurtosis derivative prior to the S-wave trial pick by an iterative process. The initial threshold value was set to 50 for three-component data and 20 for single-component data. The search would end at half the triggered window length, but no less than 2 s, before the trial pick. If no maximum was above the threshold, the threshold would be reduced by 20%, and the searching process was repeated until a maximum was found. If in the end two S-wave picks on diferent components passed the SNR test, the one with a larger product of SNR and wave energy (SNR times squared amplitude) would be retained as the final S-wave pick.

The trial pick of P-wave was set equal to the arrival of the S-wave. If no S-wave pick existed, it would be set to the (earlier) S-wave trial pick instead. The P-wave arrival would be determined as the global maximum of the kurtosis derivative, and the search would end at the smaller of the following two values, before the trial pick: 1. The triggered window length; or 2. The maximum inter-station distance among all of the stations recording the same event, divided by the S-wave coda propagation speed. Besides, the search would also stop if it went into the previous triggered window. Initially the threshold value was set to 40 for three-component data and 20 for single-component data, but it would be adjusted to 1/3 of the S-wave pick value if it was smaller.

The clustering analysis we included for the caldera stations was a simplified version of k-mean clustering (one-dimensional with k=2; Jin & Han, 2010). For each kind of picks (P- or S-wave), we initialized the clustering by setting the two clusters located at the earliest and the latest picks. Then, the picks were assigned to their nearest cluster. After all picks had been assigned, the cluster positions were re-calculated as the mean value of the picks it contained. The clustering stopped after three iterations.

## Text S5. Velocity Model

There are a few details regarding how we implemented the three-dimensional velocity model of Park et al. (2009) for our study: We adjusted the topography in the model by rounding up to the closest kilometer values to avoid unrealistic raypaths. The leftmost 20 km of the model was cut of to reduce sharp velocity variations at shallow depths. The air space was filled with a very low velocity $( 0 . 0 1 \mathrm { k m / s } )$ , while the water space was filled with P- and S-wave velocity of 1.5 km/s and $0 . 0 1 \mathrm { k m / s } .$ , respectively. The very small velocities in the air and water do not afect travel time calculation in the solid earth and are used only to satisfy a non-zero wave speed required by the ray-tracing code.

## Text S6. Localization

The earthquake locations were obtained as the maximum equal-diferential-time (EDT) likelihood locations from an Oct-tree importance sampling algorithm (Lomax, 2005). The Oct-tree sampling was deployed in the model space, starting with 10 cells in the longitude and latitude direction and 4 cells in the vertical direction. It stopped when the minimum cell size reached 0.01 km, with the maxmium 20,000 cells generated.

We set five weight levels in the NonLinLoc package, representing diferent arrival time errors (Table S2). Another 0.5 s was set to the origin time error. Generally speaking, the P-wave arrivals would be assigned weight level 0, and the S-wave arrivals would be assigned weight level 1. However, due to the varying data quality of the networks, we introduced several rules to down-weight the less reliable picks to minimize possible deterioration in localization caused by them:

1. All of the P-wave picks on the horizontal components would be down-weighted to level 1 because the P-wave onset was most prominent on the vertical component. The P-wave picks recorded on station KSFG would also be down-weighted to level 1.

2. All of the picks on the noisy nodal stations (Text S1) would be down-weighted to the next level, unless both of its adjacent nodal stations also recorded the same event. Typically, even adjacent nodal stations were too far away from each other to record trafic noise simultaneously, as the speed of car (tens of kilometers per hour) is much less than the speed of seismic waves (hundreds of kilometers per minute).

The final normalized weights were obtained as follows (Lomax, 2005):

$$
\overline {{w}} _ {i} = w _ {i} / \sum_ {i} w _ {i}\tag{1}
$$

$$
w _ {i} = \sum_ {j} w _ {i j} \exp (- \frac {1}{2} w _ {i j} ^ {2} g _ {i j} ^ {2})\tag{2}
$$

$$
w _ {i j} = \frac {1}{\sqrt {\left(\epsilon_ {i} ^ {2} + \delta_ {i} ^ {2}\right) + \left(\epsilon_ {j} ^ {2} + \delta_ {j} ^ {2}\right)}}\tag{3}
$$

where $\overline { { { w } } } _ { i } , \ w _ { i } , \ w _ { i j } , \ g _ { i j } , \ \epsilon _ { i } , \ \epsilon _ { j } , \ \delta _ { i }$ and $\delta _ { j }$ stand for the normalized weight of arrival $i ,$ , the weight of arrival $i ,$ the weight of the EDT between arrival i and arrival $j ,$ , the EDT misfits between arrival i and $j ,$ , the arrival time error of arrival i (Table S2), the arrival time error of arrival $j ,$ the travel time dependent error of arrival $i ,$ and the travel time dependent error of arrival $j ,$ respectively. The travel time dependent error was set to be 2% of the predicted travel time, but no less than 0.05 s and no more than $2 \ \mathrm { s } ,$ accounting for the accumulation of velocity model errors.

## Text S7. Re-association

Here we expand the details of the re-association process. When applying the RMS criterion for the re-association process, we increase the RMS threshold by 0.01 s for each arrival so that an event with a large number of arrivals would still be retained even if its RMS misfit was slightly larger than 1 s.

For each station, two windows would be built. One window started at the P-wave arrival time, and the other window started at the S-wave arrival time. The window overlapping check would only be performed in each kind of windows, to reduce the possibility of associating the P-wave window of one event with the S-wave window of another event. Similar to the association, the overlap threshold was designed to decrease as the source-receiver distance decreased (Table S3). The window length was set to 2 s plus the epicentral distance in kilometers divided by a factor of 12 $\mathrm { ( k m / s ) }$ . If the earthquake was the first event after the clustering process (Text S4), 1 s would be reduced from the window length. No inter-component window overlapping check would be performed, but for three-component seismometers, at least two components needed to record the event.

When locating the re-associated events, we further used the synthetic arrival times from the NonLinLoc package to help assign weights for the noisy nodal stations and the Raspberry Shake stations. Any phase picks within 1 s range of the synthetic arrival times would be given weight level 1, while picks out of the range would have the weight level further reduced by one from the level assigned according to Text S6. However, the P-wave picks 0.5 s later than the predicted S-wave arrivals and the S-wave picks 0.5 s earlier than the predicted P-wave arrivals would be set to zero weight, as their large derivations could indicate that the results are unreliable. If both of the P- and S-wave picks were assigned with weight level 1, the P-wave pick would be elevated to normal weight level 0. If the

P-wave pick on a station were below level 2, neither would the P- nor S-wave pick be used for localization.

## Text S8. Consistency of Catalogs and Earthquake Magnitude Completeness

The consistency between our catalog and other catalogs was checked (Table S4). Two earthquakes in two diferent catalogs would be considered the same if their source times were within 1.5 s and their longitudinal and latitudinal diferences were less than 0.1<sup>◦</sup>.

Our new catalog contains the majority of the events in the HVO catalog and the caldera catalog, which is not surprising. The caldera catalog required the events to have more than 10 P- and S-wave travel times (Shelly & Thelen, 2019), which prohibited it from including tiny events. Furthermore, the additional dense nodal network also allowed us to detect micro-earthquakes in the caldera area. Still, a certain portion of the earthquakes are missing in our catalog. There are two possible reasons behind the missing events: First, the filter used in this study has a lower frequency corner around 8 Hz, which is higher than in previous studies (e.g., Anchieta et al., 2011), due to the “6-Hz problem” in the OBS data (Wei et al., 2021). Overall, the filter works well for typical volcanotectonic events, which have high frequency energy, as demonstrated by the number of events detected and located. However, stations at large epicentral distances might lack high frequency signals due to attenuation and thus could be missed by the detector. We note that the filter is not well suited for long-period (LP) and very-long-period (VLP) earthquakes with dominant energy at frequencies below 5 Hz (e.g., Matoza et al., 2014; Dawson & Chouet, 2014). Nevertheless, extending the filter frequency to the LP and VLP frequencies may cause an overall decrease of SNRs because the frequencies of LP and VLP earthquakes overlap with the oceanic microseism (Shen & Shen, 2021). We suggest that

LP and VLP events should be processed separately from the typical catalog earthquakes. Second, some of the events in our catalog and the HVO catalog are not accurate enough to find a match due to, for example, noise and three-dimensional velocity structure.

Our catalog only shared a very small portion of events with the East Rift Zone catalog. Our test shows that even if we allow the earthquakes to be recorded on as few as three stations, only tens of earthquakes could be added, which is still far from their event number. This could be attributed to the sparse station distribution in the East Rift Zone and the low magnitude of the earthquakes in their catalog (Lenglin´e et al., 2021).

## Text S9. Phase Picking Errors

We further compared the automatic picks in our study with the picks in the HVO catalog. The majority of the picks in the HVO catalog were also picked by computer algorithms, though a portion of the picks were reviewed by analysts and thus expected to be more accurate than ours. However, not all of the picks of every HVO catalog event are publicly available, so only a subset (the ComCat catalog) is compared.

The result shows a systematic (0.15 s on average) diference between our P-wave picks and the HVO picks (Figure S2(a)) and less scatter in P-wave pick time diference compared with S-wave picks (Figure S2(b)). An example could be found in Figure 2(b) of the main text on the HHZ component of station JOKA. One possible cause of the diference is a higher sensitivity of our automatic picker to the early perturbations of the P-wave energy. Alternatively, it could also be due to the diferent filters used in the two catalogs. The high frequency, zero-phase filter we used could create more side lobes prior to the impulse P-wave arrival.

However, no systematic diference is found for S-wave picks (Figure S2(b)). The S-wave picks have larger uncertainties, despite the usage of polarization filters in the phase picking procedure. For example, for earthquakes with a large distance, occasionally the automatic picker would pick the large amplitude converted S-wave after the first arrival, rather than the small amplitude direct S-wave, possibly due to the source radiation patterns. Nevertheless, as we have demonstrated in the previous part, the weight assignment and adjustment during the localization could reduce the bias produced by picks with a large error, still yielding a reasonable source location. Thus, those large pick errors appearing here do not necessarily produce large errors for the earthquake location.

## Text S10. Source Time and Location Errors

For the earthquake location error analysis, only the HVO catalog is compared with our catalog, because the caldera template matching catalog was obtained with the hypoDD relocation (Shelly & Thelen, 2019), which would yield more accurate locations.

Because we would pick the P-wave arrival slightly earlier than in the HVO catalog, it would thus lead to a slightly earlier source origin time and a deeper source depth, as the P- and S-wave travel time diferences were increased. From Figure S2(c), the source time diference is ∼0.1 s, which is comparable to the P-wave travel time diference of ∼0.15 s.

There is also a certain extent of location diference between the two catalogs (Figure S2(d)). The horizontal ofsets between the source locations in the two catalogs peak at 0.5-1 km. This is not surprising since we used a three-dimensional velocity model during the localization, whereas HVO used a one-dimensional velocity model.

The source depth diferences (Figure S2(e)) follow a bi-Gaussian distribution. One peak is found around 0 km, indicating the consistency between the two catalogs. Another peak is found around -1.5 km, maybe also due to the velocity model diferences for our catalog and the HVO catalog or the P- and S-wave arrival time pick diferences.

## Text S11. Magnitude Errors

The magnitudes in our catalog could have some diferences from the value reported in the HVO catalog (Figure S2(f)). A certain portion of the magnitude diferences could be due to the self-inconsistency of the HVO catalog. Apart from equation (1) in the main text, there was another equation used by HVO to calculate the coda magnitude, with diferent parameters:

$$
M _ {d} = - 1. 2 1 + 2. 2 2 \log_ {1 0} \tau + 0. 0 1 5 z + 0. 0 0 1 1 d - 0. 0 0 5 H (z - 2 6) + s t a c o r r\tag{4}
$$

It’s obvious that the two equations would yield diferent $M _ { d }$ for the same input $\tau , \ z$ and d values. This magnitude mismatch was also reported by Shelly and Thelen (2019). Additionally, we applied a universal station correction term to all of the stations, ignoring variations in the site efects for diferent stations. For some large earthquakes, their magnitude would be underestimated in our catalog as the local magnitude will saturate. The calibration of the magnitude equations and specific station correction terms need to be performed for the Island of Hawai‘i in the future and are beyond the scope of this paper.

## Data Set S1.

The earthquake catalog of this study. The columns are the origin time (UTC), latitude, longitude, depth (km), azimuthal gap (<sup>◦</sup>), minimum station distance (km), number of phase arrivals, RMS (s), location error in the latitude direction (km), location error in the longitude direction (km), location error in the depth direction (km), magnitude, magnitude type (“l” for local magnitude, “d” for duration magnitude, and “Unk” for no magnitude), and magnitude error.

## References

Anchieta, M. C., Wolfe, C. J., Pavlis, G. L., Vernon, F. L., Eakins, J. A., Solomon, S. C., . . . Collins, J. A. (2011). Seismicity around the Hawaiian Islands recorded by the PLUME seismometer networks: Insight into faulting near Maui, Molokai, and Oahu. Bulletin of the Seismological Society of America, 101 (4), 1742–1758. doi: 10.1785/0120100271

Dawson, P., & Chouet, B. (2014). Characterization of very-long-period seismicity accompanying summit activity at K¯ılauea Volcano, Hawai’i: 2007–2013. Journal of Volcanology and Geothermal Research, 278 , 59–85. doi: 10.1016/j.jvolgeores.2014.04 .010

Jin, X., & Han, J. (2010). K-means clustering. In C. Sammut & G. I. Webb (Eds.), Encyclopedia of machine learning (pp. 563–564). Boston, MA: Springer US. doi: 10.1007/978-0-387-30164-8 425

Lenglin´e, O., Duputel, Z., & Okubo, P. (2021). Tracking dike propagation leading to the 2018 K¯ılauea eruption. Earth and Planetary Science Letters, 553 , 116653. doi: 10.1016/j.epsl.2020.116653

Lomax, A. (2005). A reanalysis of the hypocentral location and related observations for the great 1906 California earthquake. Bulletin of the Seismological Society of America, 95 (3), 861–877. doi: 10.1785/0120040141

Matoza, R. S., Shearer, P. M., & Okubo, P. G. (2014). High-precision relocation of long-period events beneath the summit region of K¯ılauea Volcano, Hawai‘i, from

1986 to 2009. Geophysical Research Letters, 41 (10), 3413–3421. doi: 10.1002/ 2014GL059819

Park, J., Morgan, J. K., Zelt, C. A., & Okubo, P. G. (2009). Volcano-tectonic implications of 3-D velocity structures derived from joint active and passive source tomography of the island of Hawaii. J. of Geophys. Res. Solid Earth, 114 (B9), B09301. doi: 10.1029/2008JB005929

Shelly, D. R., & Thelen, W. A. (2019). Anatomy of a caldera collapse: K¯ılauea 2018 summit seismicity sequence in high resolution. Geophysical Research Letters, 46 (24), 14395–14403. doi: 10.1029/2019GL085636

Shen, H., & Shen, Y. (2021). ArrayBased Convolutional Neural Networks for Automatic Detection and 4D Localization of Earthquakes in Hawai‘i. Seismological Research Letters, 92 (5), 2961-2971. doi: 10.1785/0220200419

Shiro, B., Burgess, M. K., Chang, J. C., Dotray, P., Okubo, P., Thelen, W. A., . . . others (2018). Earthquake sequences of the 2018 K¯ılauea Volcano eruption. In AGU Fall Meeting 2018.

Wei, X., Shen, Y., Caplan-Auerbach, J., & Morgan, J. K. (2021). An OBS array to investigate ofshore seismicity during the 2018 K¯ılauea eruption. Seismological Research Letters, 92(1), 603–612. doi: 10.1785/0220200206

(a)  
![](mineru/Wei2022_Kilauea_SI/images/dfbceb1143029eacfd336751b08a755e8212581f51372bc089b8d684d81db7f7.jpg)

(b)  
![](mineru/Wei2022_Kilauea_SI/images/705dbe18ca38d06ff1227b20f8900b44fd30abc74478decc7ca30fba1c7a17fd.jpg)

(c)  
![](mineru/Wei2022_Kilauea_SI/images/8ff5b64883d2d52837e0a08efc23d6b1d91080d9fb74dd3783088d0ecb8cd266.jpg)

Figure S1. The P-wave velocity model used in this study at the depth of (a) -1 km (1 km above sea level, which only afect the summits of the volcanoes), (b) 2 km and (c) 8 km, respectively. Table S1. The overlap percentage threshold against the distance, in the association process.

<table><tr><td>Distance (d)</td><td>Threshold</td></tr><tr><td>d &lt; 4 km</td><td>50%</td></tr><tr><td>4 km ≤ d &lt; 12 km</td><td>40%</td></tr><tr><td>12 km ≤ d</td><td>30%</td></tr></table>

Table S2. The five levels of quality and their corresponding time errors.

<table><tr><td>Weight level</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td></tr><tr><td>Error (s)</td><td>0.1</td><td>0.5</td><td>1.0</td><td>2.0</td><td> $\infty$ </td></tr></table>

Table S3. The overlap percentage threshold against the distance, in the re-association process.

<table><tr><td>Distance (d)</td><td>Threshold</td></tr><tr><td>d &lt; 2 km</td><td>0%</td></tr><tr><td>2 km ≤ d &lt; 4 km</td><td>20%</td></tr><tr><td>4 km ≤ d &lt; 8 km</td><td>40%</td></tr><tr><td>8 km ≤ d</td><td>60%</td></tr></table>

Table S4. The shared events, unique events and missing events of our catalog compared with

the three existing catalogs. Only the corresponding overlapped time spans were analyzed.

<table><tr><td>Catalog</td><td>Shared events</td><td>Missing events</td></tr><tr><td>the HVO catalog</td><td>60,793</td><td>8,893</td></tr><tr><td>Shiro et al. (2018)</td><td>87.2%</td><td>12.8%</td></tr><tr><td>the caldera catalog</td><td>40,188</td><td>3,753</td></tr><tr><td>Shelly and Thelen (2019)</td><td>90.9%</td><td>9.1%</td></tr><tr><td>the East Rift Zone catalog</td><td>386</td><td>5,547</td></tr><tr><td>Lengliné et al. (2021)</td><td>6.1%</td><td>93.9%</td></tr></table>

(a)  
![](mineru/Wei2022_Kilauea_SI/images/0e724d7a92349cd93f02628334eeb4c457f1b29e3236e13a49aa75ecf9364ead.jpg)

(b)  
![](mineru/Wei2022_Kilauea_SI/images/c99027a306a58fc330f62bdbee344a140c68907b563f105db56980c60b470976.jpg)

(c)  
![](mineru/Wei2022_Kilauea_SI/images/626d08bcfe754cc586608c0911fb3a07dbf1966e16e2d06b6788d8488562e466.jpg)

(d)  
![](mineru/Wei2022_Kilauea_SI/images/ff7efb80627565c20a06f51d44ff917526bac5ac2956d4a3fffcb0338767b3a3.jpg)

(e)  
![](mineru/Wei2022_Kilauea_SI/images/143d62972ba27e795819ea85fd1cc203362af1c5e7cc5b66358c227bbe2b9e31.jpg)

(f)  
![](mineru/Wei2022_Kilauea_SI/images/ec2f5d34afc196503aba1743a804df12e2ac0bc18a84aff8dfe96ebca8d6c55f.jpg)
Figure S2. The frequency distribution of arrival time diference between our picks and the HVO picks, for (a) the P-wave and (b) the S-wave, respectively. (c) The source time, (d) horizontal location, (e) depth and (f) magnitude diference frequency distribution between our catalog and the HVO catalog, respectively.