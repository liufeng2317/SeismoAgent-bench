# Tracking dike propagation leading to the 2018 K¯ılauea eruption

Olivier Lengliné <sup>a</sup>,∗, Zacharie Duputel <sup>a</sup>, P.G. Okubo <sup>b</sup>

![](mineru/LENGLINE2021_EPSL116653__paper/images/82db4e8db98a0ac9342bce62f9987ee23347349f7c0836c4872e27d0b0147ee9.jpg)

<sup>a</sup> Institut de Physique du Globe de Strasbourg, UMR7516, Université de Strasbourg/EOST, CNRS, Strasbourg, France

<sup>b</sup> Department ofEarth Sciences, School ofOcean and Earth Science and Technology, University ofHawaii at Manoa, Honolulu, HI 96822, USA

## a r t i c l e i n f o

Article history: Received 25 May 2020 Received in revised form 14 October 2020 Accepted 28 October 2020 Available online 9 November 2020 Editor: R. Bendick

Keywords: Kilauea volcano seismicity dike dynamics

## a b s t r a c t

In May 2018, a major eruption occurred in the lower East Rift Zone of the K¯ılauea volcano. The eruption started with the collapse of the Pu’u ’O’<sup>¯</sup> o¯ crater followed by a large downrift dike intrusion for more than 20 km in a well instrumented region. This large volcanic event is a rare opportunity to infer the dynamics of magma transfer that is often dificult to capture. In this study, we use seismological records to infer the migration of the dike. We detect, pick and locate more than 6000 earthquakes during the course of the magma intrusion. Using these locations together with near-field seismic amplitudes, we can precisely reconstruct the progression of the dike over time. We show that this migration is consistent with a logarithmic model of dike growth connected to a feeding magma chamber. The decrease of pressure inside the reservoir is also consistent with the dike propagation model derived from our observations. This work encourages real time monitoring of magma intrusions from the combination of seismological data and physical models.

© 2020 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/)

## 1. Introduction

Lateral dike intrusions are ubiquitous features of basaltic volcanoes (Walker and Sigurdsson, 2000). These horizontal migrations usually occur after vertical ascent of magma under a central vent or within a complex plumbing network (Rivalta et al., 2015; Townsend et al., 2017). For example at Piton de la Fournaise volcano, magma tracked by earthquake locations and geodetic signals, is first transferred vertically before propagating into the rift zones where eruptive vents are formed (e.g, Smittarello et al., 2019; Duputel et al., 2019). This last stage of lateral magma migration before eruptions is thus of interest in order to assess the location of the future eruptive site.

As hydraulic fractures, volcanic dikes are geometrically controlled by the direction of the least principal stress (Gudmundsson, 2002), but the extent and timing of intrusions remain dificult to predict (Segall, 2013). Dike propagation is mainly governed by rock strength and the driving pressure at the crack tip, which is the difference between the least compressive stress and magma pressure within the dike (Rubin, 1995). Real-time in situ assessment of the dike driving pressure is unfeasible. One has to rely on models to explain the propagation of dikes and predict their future behavior. Constraints on these models can be derived from analog experiments (e.g., Maccaferri et al., 2019) or from the tracking of intrusions using seismological and geodetic signals. Such observations have been made on several occasions for example in Afar (Grandin et al., 2010, 2011) or in Iceland (Sigmundsson et al., 2015; Woods et al., 2019). At K¯ılauea volcano, magma intrusions in the rift zones are frequently captured by seismic and geodetic instruments (Owen et al., 2000; Montgomery-Brown et al., 2010; Lundgren et al., 2013). In most cases, we observe that seismicity migrates and delineates the advance of the dike (Brandsdóttir and Einarsson, 1979). Earthquake migration speed is usually high at the beginning of the intrusion and then decays with time before stopping. This behavior is generally interpreted as the consequence of the decrease in the driving pressure resulting from the progressive drainage of the feeding magma reservoir (Rivalta, 2010). Such interpretation is in agreement with geodetic signals (tiltmeter or GPS) that exhibit a deflationary trend where the magma originates. In some cases, outflow of the magma reservoir is barely visible while the dike propagates over a long distance. This observation can be explained by the low compressibility of rock that will force the magma in the reservoir to decompress considerably (Rivalta and Segall, 2008). Several models have been proposed to explain lateral dike propagations. These models usually rely on several hypotheses to derive analytical predictions of dike dynamics (Rubin, 1995; Rivalta, 2010; Pinel et al., 2017; Grossman-Ponemon et al., 2019). With the improvement of computing capabilities, an increasing number of physical processes and couplings are taken into account. Models generally include fluid mechanics associated with magma within the dike, coupled with linear elastic fracture mechanics governing the dike propagation. Some studies include a connection between the dike and a filled magma reservoir. In general, all of these models are limited to 2 dimensions.

![](mineru/LENGLINE2021_EPSL116653__paper/images/e7cce6bcdeeb38bff2c7f013197e80d374019c4f00d45a98cd6d5e03c5d79039.jpg)  
Fig. 1. May 2018 Dike propagation in the Middle East Rift Zone (MERZ) of the K¯ılauea volcano. Circles are earthquake locations from the HVO catalog that occurred during the dike intrusion (circle colors indicate time relative to the 1st of May 2018). The assumed dike geometry is depicted with a purple dashed line. Background colors correspond to an unwrapped Sentinel-1 interferogram showing surface displacement in Line Of Sight (LOS) direction. Black lines shows mapped cracks and fissures and black triangles are vents from Trusdell et al. (2005). Seismic stations used in this study are blue triangles. The map on the upper left corner show the studied location. (For interpretation of the colors in the figure(s), the reader is referred to the web version of this article.)

Well documented dike propagations are essential to assess the validity of numerical models. However, as magma usually propagate away from the volcano summit, dikes often reach areas where the monitoring network is less dense, providing poorer constraints on the intrusion dynamics. Dike propagation can also occur aseismically. At Piton de la Fournaise volcano for example, lateral migrations take place at very shallow depth such that only weak seismic signals are produced and most of the migration is aseismic (Duputel et al., 2019). In other cases, long-range dike propagation is well monitored, but is complicated by multiple structures activated during the intrusion that are dificult to model properly (Woods et al., 2019).

In this study, we focus on the dike intrusion of May 2018 that propagated in the Middle East Rift Zone (MERZ) of K¯ılauea volcano (Fig. 1). This intrusion is connected to the collapse of Pu’u ’O’<sup>¯</sup> o¯ crater floor which occurred during a period of high pressurization of the K¯ılauea’s magmatic system as noticed from the high lava lake level at the summit of the volcano (Neal et al., 2019). The downrift propagation of the dike was detected by the occurrence of earthquakes and associated deformation. The dike eventually created the first eruptive fissures in Leilani Estates subdivision, about 20 km downrift from Pu’u ’O’<sup>¯</sup> o¯ crater, at 03:00 UTC on May 4. This intrusion led to one of the largest effusive eruptions in the recent history of K¯ılauea with a large eruptive volume of 0.8 km<sup>3</sup> (Neal et al., 2019). This major volcanic event was accompanied by the triggering of a $M _ { W } = 7 . 2$ earthquake on the south flank of the volcano (Chen et al., 2019) and a large summit caldera collapse (Segall et al., 2019; Tepp et al., 2020) similar to what has been observed in 2007 at Piton de la Fournaise (Duputel and Rivera, 2019). We are particularly interested in testing if observations of the dike propagating in the MERZ can help to constrain a physical model and highlight the early stages of the 2018 eruptive sequence at

K¯ılauea volcano. To closely track the magma migration, we need to improve our temporal and spatial resolution by detecting and locating as many events as possible during the diking episode. Given the sparsity of the seismic network in the area and the small size of dike-triggered events, earthquake signals are not clearly visible at most stations. Fortunately, one station is located right on the dike path, at the center of the intrusion segment. We therefore use this station to increase the number of dike-induced event detections and recorded more than 6300 events. The relatively simple and long-range propagation of the dike (around 20 km) also facilitates inferences on the intrusion dynamics. Our observations are interpreted in the context of a previously proposed model of dike growth.

## 2. Template matching detections

To carry out our analysis, we start by selecting earthquakes in the Hawaii Volcano Observatory (HVO) catalog that occurred approximately at the time of the initial 2018 dike intrusion. This catalog contains 280 events located in the vicinity of the MERZ between 2018-04-29 (0 h UTC) and 2018-05-04 (21 h UTC). This time span starts with the first sign of activity in the MERZ and ends before the occurrence of a $M _ { W } = 5 . 7$ earthquake in the south flank of the volcano. It encompasses the collapse of the Pu’u ’O’<sup>¯</sup> o¯ crater and the opening of the first eruptive fissure in the Lower East Rift Zone (LERZ). As shown in Fig. 1, most earthquakes occur on the 1st of May and show an apparent migration from the Pu’u ’O’<sup>¯</sup> o¯ crater towards the North-East in about a day (Shiro et al., 2018). Seismic events are then located close to the Leilani estates.

We assume a dike intrusion starting at Pu’u ’O’<sup>¯</sup> o¯ crater with an azimuth of 67◦. This simple geometry is consistent both with the alignments of fissures and craters along the MERZ and the observed descending Interferometric Synthetic Aperture Radar image captured by the sentinel 1 satellite between 2018/04/23 and

2018/05/05 (see Fig. 1). It is also very close to the dike geometry of Chen et al. (2019) derived from observed deformations. Fig. 1 shows that most events in the initial catalog are located south of the rift zone. Such apparent shift of event locations has been previously noted by Hansen et al. (2004) and attributed to a systematic bias mainly resulting from poor station coverage in the south flank of K¯ılauea volcano. Here we take advantage of one station (JOKA) located very close to the dike pathway to mitigate this potential location bias in our results.

In this study, we employ a template matching approach in order to detect possible missed events in the original catalog during the lateral propagation of the dike. This strategy follows similar studies performed in other volcanic environments (Shelly and Hill, 2011; Lengliné et al., 2016; Duputel et al., 2019; Shelly and Thelen, 2019). We use as templates, all events reported in the initial HVO catalog and shown in Fig. 1, but in order to possibly filter events that took place in the south flank of the volcano, we only select earthquakes with a depth shallower than 5 km. Indeed, it is likely that a dike in the rift zone can trigger events usually occurring at larger depth within the south flank Dieterich et al. (2000). So while we focus on rift zone events. the whole process of this dike intrusion episode might be more complex with activation of structures in the south flank of the volcano. The template signals are filtered between 2 and 20 Hz using a time-window of 5.12 s starting 1 s before the P-wave arrival. These templates are used to detect new events in continuous records for the 3 components of the JOKA station and the vertical component of KUPD or KLUD depending on whether a P-wave pick is available. This choice is mostly mo tivated by the proximity of those recording sites to the dike path as the signal to noise ratio decreases rapidly with the epicentra distance. For each time step (0.01 s) and each station, we compute the correlation coeficient between the template waveform and the continuous signal. The average correlation coeficient is then computed on 4 channels after shifting each trace according to the associated P-wave travel time. This results into an average correlation function for each template over the investigated time period. New detections are finally obtained when the average cor relation function exceeds a threshold value that is computed each day from a fixed probability of false detection. This probability is estimated by computing the average correlation coeficients be tween continuous records and a reversed version of the template signals (both time and polarity reversed). The resulting values rep resent the correlation coeficients of a noise signal preserving the time-bandwidth product of the template event and processed in the same way (using the same passband filter, same network geometry, etc.). From this population of correlation coeficients, we can then derive a correlation threshold by imposing a given probability of false detection. Here we fixed this probability of false detection to $1 0 ^ { - 1 }$ per day per template. For the 280 templates in the HVO catalog, we thus expect 168 false detections in total between 2018-04-29 and 2018-05-04. This analysis results into the detection of 6327 events (see Fig. 2). From this new catalog, we extract the waveform signal of each detection at all stations for which a P-wave pick is available for the template associated with each detection.

From the visual inspection of detected waveforms at station JOKA (see Fig. 2), we can already deduce some rough information on the position of dike-induced earthquakes. Indeed, the S-P times decrease from events 300 to 1000 and increase after event 1500 up to a maximum for events 3000 to 4000. After event 4000, a lower S-P time is observed and seems constant for the rest of the events. This observation is consistent with a dike propagating eastward from the west of JOKA site, passing nearby the station and then moving away to the east. The minimum S-P time delay observed at station JOKA is typically around 0.6 s. This indicates a minimum distance to the station of 3300 m assuming $V _ { P } = 4 0 0 0 ~ { \mathrm { m } } . s ^ { - 1 }$ derived from the model of Klein (1981) and setting $V _ { S } = V _ { P } / \sqrt { 3 }$ As the dike trace inferred from geodetic measurements is typically around 1 km from the station (Chen et al., 2019), this suggests a depth estimate of the events the closest to the station around 3 km. The S-P time delay observed at the onset of the migration is around 2.2 s and increase up to the same value after passing the station. We can also observe that a lot of the latest events have a delay typically of the order of 1.5 s. This gives us distances to station JOKA of 12 km and 8 km respectively for these two sets of time delays supposing the same velocity model. If we impose the same depth of 3 km for these events we get epicentral distances of 11.1 km and 8.1 km, placing the first events around the Pu’u ’O’<sup>¯</sup> o¯ crater and the last events, associated with the propagation, at the location where the first ground cracks were reported, so in agreement with geological observations. We also observe that events after event 4000 are then located around the same location and are not at the dike front. At that time, based on the location of the farthest seismic events, the dike tip is at least 3 km farther downrift.

## 3. Location of dike-induced earthquakes

## 3.1. Distance to station JOKA

In order to get first-order constraints on the location of newly detected earthquakes, we use signals recorded by the three components of station JOKA to estimate variations in raypath distance from S-P travel time delays. Considering that the event separation distance is small compared to the epicentral distance to the recording site, the differential P-wave, $\Delta T _ { P } ^ { i j }$ and S-wave, $\Delta T _ { S } ^ { i j }$ travel time between two events, i and $j ,$ can be written as

$$
\Delta T _ {c} ^ {i j} = T _ {c} ^ {j} - T _ {c} ^ {i} = \Delta r _ {c} ^ {i j} / V _ {c}\tag{1}
$$

where the index c refers either to P or $\mathsf { S } , \mathsf { \Delta } T _ { c } ^ { j }$ is the travel time fo event j, $V _ { c }$ is the velocity and $\Delta r _ { c } ^ { i j }$ is the difference of raypath distance for wave c between event i and j. We assume that P- and S-wave raypaths are similar such that $\Delta r _ { P } ^ { i j } = \Delta r _ { S } ^ { i j } = \Delta r ^ { i j }$ . Thus, we can write

$$
\Delta T _ {S} ^ {i j} - \Delta T _ {P} ^ {i j} = \Delta r ^ {i j} / V _ {S} - \Delta r ^ {i j} / V _ {P}\tag{2}
$$

$$
= \Delta r ^ {i j} \left(\frac {V _ {P} - V _ {S}}{V _ {P} V _ {S}}\right)\tag{3}
$$

$$
= \left(r ^ {j} - r ^ {i}\right) \left(\frac {V _ {P} - V _ {S}}{V _ {P} V _ {S}}\right)\tag{4}
$$

where $r ^ { i }$ is the distance of event i to station JOKA. Using this technique, we can thus estimate the distance of each event to the station.

We compute differential travel times for P- and S-waves measured by cross-correlation for all pairs of events. Differential travel times are estimated for P-waves in a window of 1.10 s encompassing the P-wave arrival. The S-wave arrival is computed from the P-wave travel time assuming $V _ { P } / V _ { S } = 1 . 7 3$ (where $V _ { P }$ and $V _ { S }$ denote P- and S-wave velocities). We measure S-wave travel time differences in a window starting 0.5 s before the S-wave arrival and ending $2 \ s$ later (see Fig. 2). We only keep event pairs with a cross-correlation larger than 0.6 in P- and S-wave windows and with travel time difference smaller than 0.15 s. If both East and North components provide measurements that meet the required threshold, we only keep the delay associated with the highest correlation coeficient.

We set up an inverse problem to find the distances $r ^ { i }$ for each event based on the multiple differential travel time measured for all possible pairs of events. We set m the parameter vector that contains the distances to station JOKA for all events $( \mathrm { i } . \mathrm { e } . , r _ { i } ) .$ . Our data vector, d is given by the differential travel time measurements $\Delta T _ { S } ^ { i j } - \Delta T _ { P } ^ { i j }$ for all pair of events. The forward problem in Eq. (4) can then be rewritten as

![](mineru/LENGLINE2021_EPSL116653__paper/images/53e6b071ac0559b69b8ee07a972243deb8c646630ee767278dcd4742f6f11f7e.jpg)

![](mineru/LENGLINE2021_EPSL116653__paper/images/4da55c56854678a790820d7a30799bf60ab0f834cfcf17c2ad3ed721a4365ccf.jpg)  
Fig. 2. Detected events at station JOKA. Top figure, vertical component records. Each row indicates the signal of a different event starting 1 s before the P-wave pick. The vertical axis denotes time in samples (sampling step is 0.01 s). Colors shows the normalized amplitude of each seismogram filtered between 2 and 20 Hz. The window used for computing the P-wave delays are shown unaltered while the other parts of the seismogram are transparent. Bottom figure shows records at the same station on the horizontal (East) component. In that case, only the S-wave window is shown with non-transparent colors.

$$
\mathbf {d} = \mathbf {G m}\tag{5}
$$

where G is a matrix that only contains two non zero values for each row that are $\pm \frac { V _ { P } - V _ { S } } { V _ { P } V _ { S } }$ . Uncertainty on the data vector d are described by a diagonal covariance matrix $\mathbf { C _ { d } }$ whose elements are given by $\frac { 1 } { 2 } \frac { ( 1 - C C ) ^ { 2 } } { ( C C ) ^ { 2 } }$ where CC is the average correlation coeficient measure for P and S delay times. We assume a Gaussian a priori information with a mean prior model $\mathbf { m } _ { \mathrm { p r i o r } }$ corresponding to the distance from station JOKA obtained using initial locations in the HVO catalog. Given the poorly constrained depths in the HVO catalog, we set the depth for all events at 3 km as determined in the previous section. This is consistent with the relocation results of Rubin et al. (1998), showing that all events recorded during the 1983 intrusion in K¯ılauea’s rift zone are located close to the dike path at about 3 to 4 km depth. The a priori distance uncertainties are set to 5 km for all events. The distances from station JOKA are obtained by solving the linear least square problem defined in

Eq. (5). The maximum a posteriori model is given by (Tarantola, 2005):

$$
\widetilde {\mathbf {m}} = \left(\mathbf {G} ^ {t} \mathbf {C} _ {\mathrm{d}} ^ {- 1} \mathbf {G} + \mathbf {C} _ {\mathrm{m}} ^ {- 1}\right) ^ {- 1} \left(\mathbf {G} ^ {t} \mathbf {C} _ {\mathrm{d}} ^ {- 1} \mathbf {d} + \mathbf {C} _ {\mathrm{m}} ^ {- 1} \mathbf {m} _ {\text { prior }}\right),\tag{6}
$$

where $\mathbf { c } _ { \mathrm { m } }$ is the diagonal a priori covariance matrix that contains the initial uncertainties on the distance from JOKA. A posteriori uncertainties, $\tilde { \sigma } _ { m }$ , are also estimated on the inferred parameters as the square root elements of the diagonal of the posterior covariance matrix $\widetilde { \mathbf { c } } _ { \mathrm { m } } = \left( \mathbf { G } ^ { t } \mathbf { C } _ { \mathrm { d } } ^ { - 1 } \mathbf { G } + \mathbf { C } _ { \mathrm { m } } ^ { - 1 } \right) ^ { - 1 }$ . Results on Fig. 3 confirm what has been inferred above from S-P time delays (cf., Section 2 and Fig. 2). The seismicity migration associated with the eastward dike propagation is evident from event 500 to event 3500. Earthquakes are first getting closer to JOKA station down to a minimum distance of 3.5 km. Events are then moving away, in agreement with an overall dike propagation to the East of JOKA. We also observe that some events located close to the station that appears continuously over the whole investigated period. This might reflect the fact that there exists an area near the recording site that has permanent weak structures, close to equilibrium that are activated by slight changes of stress. This might also reflects the increase sensibility of our detection method to events located close by the recording site.

![](mineru/LENGLINE2021_EPSL116653__paper/images/9e55b384180e63f4af7aa5cd12b0bcc263487367b66e5414740404c005ee8c55.jpg)  
Fig. 3. Inverted distance to station JOKA obtained from differential travel time, -T<sup>ij</sup> (black circles) as a function of the event number. The blue and red circles indicate the 2σ distance uncertainty for each earthquake

## 3.2. Earthquake localization from P-wave travel-time differences

In this section, we estimate absolute earthquake locations by taking advantage of the fact that each detected event has been recorded by at least another station than JOKA (cf., Section 2). With this purpose we have to pick the P-wave arrival time for all detected events. This is realized by using a kurtosis approach. This technique simply detects changes in the distribution of seismic amplitudes at the arrival of the seismic wave. To optimize the results, for each detected waveform, we first apply a band-pass filter between 2 and 20 Hz and remove the mean of the vertical trace. The kurtosis is then computed as

$$
F (t) = \frac {\tilde {x} _ {4} (t)}{| \tilde {x} _ {2} (t) | ^ {2}}\tag{7}
$$

where t is time and $\tilde { x } _ { k } ( t )$ is the k-th order moment of the waveform x(t) computed in a sliding window including N data samples. The kurtosis function F(t) will show peaks when there is a change of the statistical content of the waveform, which is commonly used to detect P-wave onsets (Langet et al., 2014). As detected earthquakes should be spatially located in the vicinity of their associated template events, their P-wave travel times must also be similar to their respective templates. As an a priori information for each detection, we therefore give higher weights to peaks in F(t) that are close to the template P-wave pick. More specifically, the weight is defined as

$$
w (t - t _ {\text { prior }}) = \exp \left(- 0. 1 (t - t _ {\text { prior }}) ^ {2}\right)\tag{8}
$$

where $t _ { \mathrm { p r i o r } }$ is the template P-wave arrival time. For each detection, the P-wave arrival is then picked at the maximum of the function

$$
F _ {w} (t) = F (t) w \left(t - t _ {\text { prior }}\right),\tag{9}
$$

where F is computed in an interval of 0.5 s around $t _ { p r i o r }$ . Following Baillard et al. (2014), we have tested various combinations of window sizes N and filtering parameters. By comparing the results of the above procedure for several signals, we found that more robust picking was achieved taking N 20 samples (0.2 s) and filtering the waveforms in the 2-20 Hz frequency passband.

Based on the resulting catalog of P-wave arrivals, we then locate each earthquake individually using differences of P-wave arrival times at all available pair of stations. Using this differential approach, we do not have to estimate the event origin time. It also has the advantage of correcting any systematic bias in our picking procedure (e.g., due to bandpass filtering). We use a grid-search approach to find the optimum location for each event. We consider a 2D grid of horizontal locations to be explored and set the depth of all events to 3 km (consistently with results in Section 2). For a given event, the posterior probability distribution of the earthquake location x is defined as (Tarantola, 2005)

$$
p (\mathbf {x} | \mathbf {d t} _ {\mathrm{obs}}) \propto p (\mathbf {d t} _ {\mathrm{obs}} | \mathbf {x})   p (\mathbf {x})\tag{10}
$$

where $p ( \mathbf { d t _ { \mathrm { o b s } } } | \mathbf { x } )$ is the likelihood function describing the ability of a location x to fit the observed P-wave differential travel-times $\mathbf { d t } _ { \mathrm { o b s } }$ . In this equation, p(x) is our a priori information on the event location.

To mitigate the impact of outliers, we employ a L1 norm misfit function, corresponding to a Laplacian distribution for the data likelihood:

$$
p (\mathbf {d t} _ {\mathrm{obs}} | \mathbf {x}) = \prod_ {j} \frac {1}{2 \sigma_ {d t} ^ {j}} \exp \left(- \frac {\left| d t ^ {j} (\mathbf {x}) - d t _ {\mathrm{obs}} ^ {j} \right|}{\sigma_ {d t} ^ {j}}\right)\tag{11}
$$

where $d t ^ { j } ( { \bf x } )$ and $d t _ { \mathrm { o b s } } ^ { j }$ are the predicted and observed differential travel times for the j-th pair of stations (in average an we have 5 P-wave picks by event and thus 10 pairs). $\sigma _ { d t } ^ { j }$ corresponds to an uncertainty on $d t _ { \mathrm { o b s } } ^ { j } .$ . Based on visual inspections for several waveforms, we set the picking uncertainty to $0 . 5 / \sqrt { \operatorname* { m a x } ( F ) }$ , where F is the maximum amplitude of the kurtosis function in Eq. (7). The differential travel time uncertainty $\sigma _ { d t } ^ { j }$ is then derived by summing up the variances of the corresponding P-wave picks. The a priori distribution is defined as:

$$
p (\mathbf {x}) = p _ {\perp} (\mathbf {x}) p _ {r} (\mathbf {x})\tag{12}
$$

![](mineru/LENGLINE2021_EPSL116653__paper/images/399ce8abdb2811ee85bcab11a444b1d3cc0f51ba7967c8ad0b38eef7ab0b08a0.jpg)

where $p _ { \perp } ( \mathbf { x } )$ and $p _ { r } ( \mathbf { x } )$ are two distributions that are described below. The first term written as

$$
p _ {\perp} (\mathbf {x}) = \frac {1}{\sqrt {2 \pi}} \exp \left(\frac {- d _ {\perp} ^ {2} (\mathbf {x})}{2}\right)\tag{13}
$$

penalizes event locations x at a large horizontal distance $d _ { \perp }$ (here in km) from the rift zone (idealized as a dashed purple line in Fig. 1). The second term $p _ { r } ( \mathbf { x } )$ is defined as

$$
p _ {r} (\mathbf {x}) = \frac {1}{2 \sigma_ {r}} \exp \left(- \frac {\left| r (\mathbf {x}) - r _ {\text { prior }} \right|}{\sigma_ {r}}\right).\tag{14}
$$

This is a Laplace prior on the distance r from station JOKA (see Eq. (4)). The distribution is centered on $r _ { \mathrm { p r i o r } }$ corresponding to the maximum a posteriori distance in Eq. (6) with a scale parameter $\sigma _ { r }$ corresponding to the associated posterior variance (see Section 3.1).

The localization procedure is illustrated in Fig. 4 for an event lo cated between stations JOKA and KUPD. For that example, we show the posterior distribution $p ( \mathbf { x } | \mathbf { d t } _ { \mathrm { o b s } } )$ along with the data likelihood $p ( \mathbf { d t } _ { \mathbf { 0 } \mathbf { b } \mathbf { s } } | \mathbf { x } )$ and the prior distribution p(x) defined in Eq. $( 1 0 ) – ( 1 4 )$ For each event, the optimum location is defined from the maximum a posteriori $( \mathrm { i . e . }$ , the location maximizing $p ( \mathbf { x } | \mathbf { d t } _ { \mathrm { o b s } } )$ shown in Fig. 4a). P-wave differential travel-times provide good constraints on the event location along the dike. However, as shown by the data likelihood in Fig. 4d, these observations lead to a significant uncertainty on the distance perpendicular to the dike. This is mainly due to the geometry of the network characterized by a linear distribution of stations along the rift zone. Using the prior information of the event distance from JOKA (Fig. 4b) and assuming that the location cannot be too far from the rift zone (Fig. 4c), we still end up with relatively tight constraints on the event location.

Fig. 5 shows the resulting localization results projected along the rift zone as a function of time. There is a clear migration of earthquakes propagating from the Pu’u $\bar { \cdot } \bar { 0 } \bar { 0 }$ crater at time $t _ { 0 }$ on 1 May 2018 around 01h30 UTC and ending up around Leilani Estates after a bit less than 2 days.

The migration can be well approximated by a function of the form proposed by Grossman-Ponemon et al. (2019) for lateral dike migration fed by an over-pressurized magma reservoir, setting the distance along dike propagation as $d _ { \parallel }$

$$
d _ {\parallel} (t) = a \log (1 + (t - t _ {0}) / \tau)\tag{15}
$$

where a and τ are constants and t is the time since the start of the migration. Although there are some uncertainties on these parameters depending on the choice of the events used to define the migration front, setting $a = 8 . 2$ km and $\tau = 0 . 1 1$ day is in good agreement with the observed seismicity (cf., Blue line in Fig. 5). These results are validated in the next section using seismic amplitudes to track the propagating dike.

## 4. Tracking dike from seismic amplitudes

We follow the method presented by Battaglia and Aki (2003) and later improved by Taisne et al. (2011) that exploits recorded seismic amplitudes as an indicator of the proximity of the seismic source to the recording sites. Given that both intrinsic attenuation and geometrical spreading attenuate seismic waves with distance, the seismic amplitudes measured at different seismic stations can be used to locate earthquakes. Such a method has been shown to be well adapted to track dike intrusion in various volcanic environments (Taisne et al., 2011; Caudron et al., 2015, 2018). One advantage of this approach is that we do not need to identify individual events or pick arrival times, which is particularly useful to locate small earthquakes with low signal to noise ratio. Here we follow the processing procedure proposed by Taisne et al. (2011). We first deconvolve records from their instrumental response and band-pass filter them in the 5-15 Hz frequency range, as we are mainly interested in high frequency signals emitted by the propagating dike. We then compute the envelope of the signal and estimate its median in a moving time-window of 10 s. The signal originally sampled at 100 Hz is decimated to one point every 10 s. Finally, we apply a last median filtering with a moving window size of 5 minutes. This gives us the smoothed high frequency amplitude recorded at seismic stations. Here we consider the 3 stations that are located along the dike path (KUPD, KLUD and JOKA in Fig. 1). We compute ratio of seismic amplitude for the 3 possible pairs of stations. This amplitude ratio is defined as

![](mineru/LENGLINE2021_EPSL116653__paper/images/53c519bbf7f828c54d15da12f93d7b2755878c55d520172529437d952cc66cfc.jpg)  
x (m)  
Fig. 4. Example of event localization from P-wave travel-time differences. The posterior probability density (a) $p ( \mathbf { x } | \mathbf { d t } _ { \mathrm { o b s } } )$ on the event location x given the observed travel-time differences $\mathbf { d t } _ { 0 \mathrm { b s } }$ is shown on top. We use the maximum of this function as the most probable event location. This posterior probability density is obtained from the combination of the data likelihood $( { \mathsf { d } } ) ,$ $p ( \mathbf { d t _ { \mathrm { o b s } } } | \mathbf { x } )$ with prior information on the event distance from JOKA (b), p (x) and the event distance from the rift zone (c), p (x). For more clarity, the probability density functions (pdf) are normalized with respect to their maximum amplitude.

$$
\frac {U _ {i} (t)}{U _ {j} (t)} = \left(\frac {r _ {j} (t)}{r _ {i} (t)}\right) ^ {n} \exp \left[ - B (r _ {i} (t) - r _ {j} (t)) \right]\tag{16}
$$

![](mineru/LENGLINE2021_EPSL116653__paper/images/88b6d1847b4098a79d876fddf840bfe66e9c48c07e4fdccd629f30a1a78a31ef.jpg)  
Fig. 5. Evolution of earthquake distance along the dike path as a function of time (gray circles). The three stars indicate the location of the 3 station JOKA, KUPD and KLUD. The blue line shows a fit of the form of Eq. (15) with a 8.2 km and τ 0.11 day.

where $U _ { i } ( t )$ and $U _ { j } ( t )$ refer to the smoothed seismic amplitude measured at station i and j, r (t) is the distance to station i and B is a factor defined as

$$
B = \frac {\pi f}{Q V _ {S}}\tag{17}
$$

with $V _ { S }$ the shear wave velocity, f the frequency and Q is the quality factor for attenuation. The exponent n in Eq. (16) is equal to 1 for body waves. For simplicity, we consider an isotropic medium with constant $V _ { S }$ and Q . Using the fit of Eq. (15) to the event locations in Section 3.2, the distance of the dike tip to the stations is then estimated as a function of time. We then predict the amplitude ratios for the 3 possible pairs of stations using Eq. (16). As each station is associated with different local site effects, the predicted amplitude ratios must be corrected from the corresponding amplification of seismic waves. One way to estimate such amplification is to use the coda of large regional events (Aki and Ferrazzini, 2000). In this study, we invert for amplification factors minimizing differences between observed and predicted amplitude ratios given the previously inferred dike migration. Notice that these amplitude corrections are estimated for each station and are constant through time as we do not expect significant changes in site effects. Results presented in Fig. 6 indicate a good agreement between observed and predicted ratios of seismic amplitudes. Here we set $V _ { S } = 4 0 0 0 \mathrm { \bar { / } } \sqrt { 3 } \mathrm { m } . s ^ { - 1 }$ and $Q = 1 7 0$ (the same quality factor as used by Taisne et al. (2011)). We also use $f = 1 0$ Hz, corresponding the middle of our frequency passband. We found that results are not much affected by change of these parameters. However, we observe that a source depth of 3 km as inferred for earthquakes in previous sections does not fit the observed amplitude ratios. The best agreement between our model and the observed data is obtained for a depth of 1 km (Fig. 6). We note here that we also do not take into account variation of topography (this corresponds to roughly a difference of 400 m between the two dike extremities).

## 5. Discussion

## 5.1. Limitations ofthe present results

We can notice all along the dike path, bursts of dike growth followed by pauses as well as gaps of seismicity at some locations. We first want to point that, because the dyke dynamics is uniquely inferred from seismicity, it has inevitably some limitations. For ex amples, volcano-tectonic earthquakes are only triggered, close to the dyke, at the location of pre-existing structures already near to failure Rubin et al. (1998). The absence of seismicity in some areas may then possibly indicate that no pre-existing structures are present at these locations. It may also be possible that these structures exist and that they produce some small earthquakes but unfortunately we do not have any template event at that location which allows us to recover these small signals. Similarly burst of seismicity appearing during the dike growth may possibly be linked to our varying detection capability. Indeed, we see a lot of events located close to the station site JOKA, which may indicate the higher sensibility of our detection approach close to the recording instrument. These zones of earthquake clusters or gaps may also be linked to local changes of the dike or host rocks properties but and can also represent a real complex dike dynamics such that the model in Eq. (15) represents only an average description of the dike propagation. This model predicts an infinitely long dike propagation which is obviously not realistic as the dike stopped and reached the surface after a bit more than 20 km. A possible reason to explain the dike arrest is to propose that the dike overpressure, as governed by the pressure in the feeding magma chamber, becomes too small after a certain distance such that the fracture cannot propagate anymore. It may also be possible that, because the surface elevation above the dike is decaying as the dike propagates downrift, at some point the minimum compressive stress above the dike is low enough such that it becomes possible to propagate upward to the surface. Finally, we note there also exists models that predicts a finite dike length such as in Rivalta and Segall (2008) and could provide a different interpretation of our results.

## 5.2. Constraints on dike opening

The results above show that earthquake locations and seismic amplitudes are consistent with the logarithmic dike propagation described in Eq. (15). Here, we first investigate if geodetic data is also in agreement with this model. Station JOKA includes a GPS station and a tiltmeter in addition to the seismometer used in this study. Unfortunately, with a limited number of geodetic observations, estimating the evolution of dike opening is an undetermined problem with a wide range of possible solutions. We rather use geodetic time-series to get an independent constrain on the timing of the dike emplacement. Fig. 7 compares geodetic data recorded at JOKA with the distance of seismic events to this station. Assuming that seismicity is activated on pre-existing fractures close to the tip of dike, Fig. 7a shows that the dike tip reaches JOKA on May 1 around 9:40 UTC. At the same time, geodetic time-series show a slight change compared to the reference baseline observed before. As geodetic data is mostly sensitive to deformation in the vicinity of the instrument, we assume that these observations reflect dike opening close to the station. It suggests that the arrival of the tip brings little local deformation, but when the tip passes the station then opening really starts and it is basically complete in about 4 hours, at least locally.

![](mineru/LENGLINE2021_EPSL116653__paper/images/1e763757fc08943fb5cf13d6a6c5019c245da123085cf4e63cbaf5ed4334810d.jpg)

![](mineru/LENGLINE2021_EPSL116653__paper/images/ff10bf28aea8cd4cf6aff3bfbf748541f31739d01b9a328cf352d4aade7ab15f.jpg)

![](mineru/LENGLINE2021_EPSL116653__paper/images/4a7fa932456e124c8f7cc4e345000d8240b08ef294439024a9ea3574d60c49e9.jpg)  
Fig. 6. Seismic amplitude ratio measured for 3 pairs of stations as a function of time (red curve). Black lines correspond to amplitude ratios predicted assuming sources located at the tip of a dike propagating according to Eq. (15). The gray rectangle at the beginning indicates the time period before the dike propagation. In the bottom figure, a map shows the location of the three used station and the assumed location of the dike.

## 5.3. Predicting magma chamber overpressure

We can also test if a model of a feeding magma chamber below the Pu’u ’O’<sup>¯</sup> o¯ crater is consistent with the proposed dike propagation. To test this hypothesis, we compute the non-dimensional pressure change in the supplying magma chamber following the model of Grossman-Ponemon et al. (2019). We here assumed some parameters, typical of basaltic volcanoes (similar to Grossman-Ponemon et al. (2019)), to perform this computation: magma chamber radius, R 1 km, magma viscosity $\eta = 1 0 0 \ \mathrm { P a } . s ,$ deviatoric stress S 1 MPa and shear modulus, $\mu = 3 0 { \mathrm { ~ G P a } }$ . This model assumes that the dike is fed by a lateral reservoir and that the magma pressure within the dike is uniform. Using the parameters obtained from Eq. (15), it is then possible to estimate the nondimensional pressure change in the reservoir associated with the dike intrusion in the MERZ. We can compare this predicted pres-

![](mineru/LENGLINE2021_EPSL116653__paper/images/cf77148075ccb363be98daa1ab4fa93d2b30620c9ce978174dc55ab5a1ff75aa.jpg)  
Fig. 7. Comparison between earthquake locations and geodetic observations. a) Epicentral distances between located seismic events and station JOKA (gray dots). The gray area, common of panel a, b and c, shows the time when the dike reaches the station as determined from the minimum distances of the earthquakes; b) Tiltmeter records at station JOKA on the East and North component; c) 30 s GPS displacement recorded at the same site (JOKA) (Miklius, 2007) in the 3 directions and processed using the method of Twardzik et al. (2019); d) radial tilt at station POO located less than 2 km away from Pu’u ’O’<sup>¯</sup> o¯ cone (blue curve). Decreasing curve indicates deflation in the direction of the cone. The black dashed line is the computed variation of pressure of the magma chamber feeding the dike. This value has been shifted and multiplied by a constant in order to fit the tilt data.

sure history with an observation reflecting the pressure change in the reservoir. With this purpose, we analyze tilt records at station POO which is located less than 2 km away from the Pu’u ’O’<sup>¯</sup> o¯ cone. The station POC located closer to the cone went off-scale during this episode and unfortunately cannot be considered here. We compute the radial tilt, and assume that this signal is linked to a spherical deflating magma source embedded in an elastic half space that we can model as a point source. If we suppose that elastic constants along with the size and location of the magma reservoir remain constants during deflationary episode, the tilt sig nal should be proportional to variations in the reservoir pressure (Lisowski, 2007). Fig. 7d shows the shifted radial tilt and the inferred pressure variation multiplied by a constant. Overall, we observe a good agreement between tilt observations and predicted pressure variations in the magma reservoir. This good agreement allow us to infer some other properties derived from the model parameters, namely the total compressibility (the sum of the magma and chamber compressibility), $\bar { \beta } = 1 . 8 . \dot { 1 } 0 ^ { - 1 0 }$ Pa. and the initial overpressure in the magma reservoir -P 9.7 MPa. The data misfit observed at the beginning of the intrusion is likely due to a contamination of the tilt signal by the dike starting its propagation near station POO. These results indicate that the deflationary behavior at the origin at the $\mathrm { P u } ^ { \prime } \mathrm { u } \ \mathrm { \bar { 0 } } \bar { 0 }$ crater floor collapse is mainly linked to the propagation of the dike in the MERZ. Although our simple model consider a single feeding magma chamber underneath the Pu’u ’O’<sup>¯</sup> o¯ vent, its ability to fit tilt observations suggests that this reservoir might have acted as an initial pressure source to the dike intrusion.

The deciphered scenario of dike intrusion that occurred during this episode show that inference of the dike dynamics can be mapped by seismological data. As the processing achieved here can be performed in near-real time, using these data in conjunction with a theoretical predictive model can help to estimate the future advance of the dike emplacement.

## 6. Conclusion

We track the dike intrusion that led to the 2018 K¯ılauea eruption in the LERZ. Our results reveal that both earthquake locations and seismic amplitudes are consistent with a dike starting at Pu’u ’O’<sup>¯</sup> o¯ crater and propagating downrift in the northeast direction for more than 20 km. The observed dike migration is well modeled by logarithmic growth, whose parameters inform us about the pressure decrease in the magma reservoir. The resulting predicted pressure decay is in good agreement with tilt records near the Pu’u ’O’<sup>¯</sup> o¯ vent, showing that most of the observed deflation is associated with the dike intrusion. We emphasize that applying such a procedure in real time can help to estimate the dike movement.

## CRediT authorship contribution statement

Olivier Lengliné: Conceptualization, Methodology, Validation, Visualization, Writing – original draft, Writing – review & editing. Zacharie Duputel: Conceptualization, Methodology, Validation, Vi sualization, Writing – original draft, Writing – review & editing. P.G. Okubo: Data curation, Resources, Validation, Writing – original draft, Writing – review & editing.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Acknowledgements

We thank Brian Shiro from USGS HVO for discussion along Meredith Townsend and an anonymous reviewer for their suggestions. Sentinel-1A interferogram is provided by the European Space Agency’s Sentinel-1satellite and was processed by University of Hawaii (http://pgf.soest.hawaii.edu/Kilauea\_insar/). All figures are made with the GMT software (Wessel et al., 2013). This project has received funding from the European Research Council (ERC, under the European Union’s Horizon 2020 research and innovation program under grant agreement No. 805256) and from Agence Nationale de la Recherche (project ANR-17-ERC3-0010). All seismic data are from HVO seismic network and can be accessed from IRIS (HVO, 1956). Tiltmeter and lava lake data shown here are from Johanson and Miklius (2019) and Patrick et al. (2019).

## Appendix A. Supplementary material

Supplementary material related to this article can be found online at https://doi.org/10.1016/j.epsl.2020.116653.

## References

Aki, K., Ferrazzini, V., 2000. Seismic monitoring and modeling of an active volcano for prediction. J. Geophys. Res. 105, 23763.

Baillard, C., Crawford, W.C., Ballu, V., Hibert, C., Mangeney, A., 2014. An automatic kurtosis-based P-and S-phase picker designed for local seismic networks. Bull Seismol. Soc. Am. 104, 394–409.

Battaglia, J., Aki, K., 2003. Location of seismic events and eruptive fissures on the Piton de la Fournaise volcano using seismic amplitudes. J. Geophys. Res., Solid Earth 108.

Brandsdóttir, B., Einarsson, P., 1979. Seismic activity associated with the September 1977 deflation of the Krafla central volcano in northeastern Iceland. J. Volcanol. Geotherm. Res, 6. 197–212

Caudron, C., Taisne, B., Kugaenko, Y., Saltykov, V., 2015. Magma migration at the onset of the 2012–13 Tolbachik eruption revealed by seismic amplitude ratio analysis. J. Volcanol. Geotherm. Res. 307, 60–67.

Caudron, C., White, R.S., Green, R.G., Woods, J., Ágústsdóttir, T., Donaldson, C., Greenfield, T., Rivalta, E., Brandsdóttir, B., 2018. Seismic amplitude ratio analysis of the 2014–2015 Bár arbunga-Holuhraun dike propagation and eruption. J. Geophys. Res., Solid Earth 123, 264–276

Chen, K., Smith, J.D., Avouac, J.P., Liu, Z., Song, Y.T., Gualandi, A., 2019. Triggering of the Mw 7.2 Hawaii earthquake of 4 may 2018 by a dike intrusion. Geophys. Res Lett. 46, 2503–2510.

Dieterich, J., Cayol, V., Okubo, P., 2000. The use of earthquake rate changes as a stress meter at Kilauea volcano. Nature 408, 457–460.

Duputel, Z., Lengliné, O., Ferrazzini, V., 2019. Constraining spatiotemporal characteristics of magma migration at Piton de la Fournaise volcano from pre-eruptive seismicity. Geophys. Res. Lett. 46, 119–127.

Duputel, Z., Rivera, L., 2019. The 2007 caldera collapse of Piton de la Fournaise volcano: source process from very-long-period seismic signals. Earth Planet. Sci. Lett. 527, 115786.

Grandin, R., Jacques, E., Nercessian, A., Ayele, A., Doubre, C., Socquet, A., Keir, D., Kassim, M., Lemarchand, A., King, G., 2011. Seismicity during lateral dike propagation: insights from new data in the recent Manda Hararo–Dabbahu rifting episode (Afar, Ethiopia). Geochem. Geophys. Geosyst. 12.

Grandin, R., Socquet, A., Jacques, E., Mazzoni, N., de Chabalier, J.B., King, G., 2010. Sequence of rifting in Afar, Manda-Hararo rift, Ethiopia, 2005–2009: time-space evolution and interactions between dikes from interferometric synthetic aperture radar and static stress change modeling. J. Geophys. Res., Solid Earth 115.

Grossman-Ponemon, B.E., Heimisson, E.R., Lew, A.J., Segall, P., 2019. Logarithmic growth of dikes from a depressurizing magma chamber. Geophys. Res. Lett. 47, e2019GL086230.

Gudmundsson, A., 2002. Emplacement and arrest of sheets and dykes in central volcanoes. J. Volcanol. Geotherm. Res. 116, 279–298.

Hansen, S., Thurber, C., Mandernach, M., Haslinger, F., Doran, C., 2004. Seismic velocity and attenuation structure of the east rift zone and south flank of Kilauea volcano, Hawaii. Bull. Seismol. Soc. Am. 94, 1430–1440.

HVO, USGS Hawaiian Volcano Observatory, 1956. Hawaiian Volcano Observatory Network. International Federation of Digital Seismograph Networks, Dataset/Seismic Network

Johanson, I., Miklius, A., 2019. Tiltmeter data from K¯ılauea Volcano, Hawaii, spanning the 2018 eruption and earthquake sequence. U.S. Geological Survey data release. https://doi.org/10.5066/P9310M9N.

Klein, F.W., 1981. A linear gradient crustal model for south Hawaii. Bull. Seismol. Soc. Am. 71, 1503–1510.

Langet, N., Maggi, A., Michelini, A., Brenguier, F., 2014. Continuous kurtosis-based migration for seismic event detection and location, with application to Piton de la Fournaise volcano, la réunioncontinuous kurtosis-based migration for seismic event detection and location. Bull, Seismol, Soc. Am. 104. 229–246.

Lengliné, O., Duputel, Z., Ferrazzini, V., 2016. Uncovering the hidden signature of a magmatic recharge at Piton de la Fournaise volcano using small earthquakes. Geophys. Res. Lett. 43, 4255–4262.

Lisowski, M., 2007. Analytical volcano deformation source models. In: Volcano Deformation. Springer, pp. 279–304.

Lundgren, P., Poland, M., Miklius, A., Orr, T., Yun, S.H., Fielding, E., Liu, Z., Tanaka, A., Szeliga, W., Hensley, S., et al., 2013. Evolution of dike opening during the March 2011 Kamoamoa fissure eruption, K¯ılauea volcano, Hawaii. J. Geophys. Res, Solid Earth 118 897-914

Maccaferri, F., Smittarello, D., Pinel, V., Cayol, V., 2019. On the propagation path of magma-filled dikes and hydrofractures: the competition between external stress, internal pressure, and crack length. Geochem. Geophys. Geosyst. 20, 2064-2081

Miklius, A., 2007. Hawaii GPS Network - JOKA-Jonika P.S. the GAGE Facility operated by UNAVCO, Inc., GPS/GNSS Observations Dataset. https://doi.org/10.7283 T58P5XR4

Montgomery-Brown, E.K., Sinnett, D., Poland, M., Segall, P., Orr, T., Zebker, H., Miklius, A., 2010. Geodetic evidence for en echelon dike emplacement and concurrent slow slip during the June 2007 intrusion and eruption at K¯ılauea volcano, Hawaii. J. Geophys. Res., Solid Earth 115.

Neal, C., Brantley, S., Antolik, L., Babb, J., Burgess, M., Calles, K., Cappos, M., Chang, J., Conway, S., Desmither, L., et al., 2019. The 2018 rift eruption and summit collapse of K¯ılauea volcano. Science 363, 367–374.

Owen, S., Segall, P., Lisowski, M., Miklius, A., Murray, M., Bevis, M., Foster, J., 2000. January 30, 1997 eruptive event on Kilauea volcano, Hawaii, as monitored by continuous GPS. Geophys. Res. Lett, 27. 2757–2760.

Patrick, M., Younger, E., Tollett, W., 2019. Lava Level and Crater Geometry Data During the 2018 Lava Lake Draining at K¯ılauea Volcano, Hawaii. U.S. Geological Survey, data release.

Pinel, V., Carrara, A., Maccaferri, F., Rivalta, E., Corbi, F., 2017. A two-step model for dynamical dike propagation in two dimensions: application to the July 2001 Etna eruption. J. Geophys. Res., Solid Earth 122, 1107–1125.

Rivalta, E., 2010. Evidence that coupling to magma chambers controls the volume history and velocity of laterally propagating intrusions. J. Geophys. Res., Solid Earth 115.

Rivalta, E., Segall, P., 2008. Magma compressibility and the missing source for some dike intrusions. Geophys. Res. Lett. 35.

Rivalta, E., Taisne, B., Bunger, A., Katz, R., 2015. A review of mechanical models of dike propagation: schools of thought, results and future directions. Tectonophysics 638, 1–42

Rubin, A.M., 1995. Propagation of magma-filled cracks. Annu. Rev. Earth Planet. Sci. 23, 287–336.

Rubin, A.M., Gillard, D., Got, J.L., 1998. A reinterpretation of seismicity associated with the January 1983 dike intrusion at Kilauea Volcano, Hawaii. J. Geophys. Res., Solid Earth 103, 10003–10015

Segall, P., 2013. Volcano deformation and eruption forecasting. Geol. Soc. (Lond.) Spec. Publ. 380, 85–106.

Segall, P., Anderson, K.R., Johanson, I., Miklius, A., 2019. Mechanics of inflationary deformation during caldera collapse: evidence from the 2018 K¯ılauea eruption. Geophys. Res. Lett., 149.

Shelly, D.R., Hill, D.P., 2011. Migrating swarms of brittle-failure earthquakes in the lower crust beneath Mammoth Mountain, California. Geophys. Res. Lett. 38.

Shelly, D.R., Thelen, W.A., 2019. Anatomy of a caldera collapse: K¯ılauea 2018 summit seismicity sequence in high resolution. Geophys. Res. Lett.

Shiro, B., Burgess, M.K., Chang, J.C., Dotray, P., Okubo, P., Thelen, W.A., Waite, G.P., Antolik, L., Johanson, I.A., Anderson, K.R., Montgomery-Brown, E.K., 2018. Earthquake sequences of the 2018 K¯ılauea Volcano eruption. In: AGU Fall Meeting Abstracts. V41B-01.

Sigmundsson, F., Hooper, A., Hreinsdóttir, S., Vogfjörd, K.S., Ófeigsson, B.G., Heimisson, E.R., Dumont, S., Parks, M., Spaans, K., Gudmundsson, G.B., et al., 2015. Segmented lateral dyke growth in a rifting event at Bárðarbunga volcanic system, Iceland. Nature 517, 191–195.

Smittarello, D., Cayol, V., Pinel, V., Peltier, A., Froger, J.L., Ferrazzini, V., 2019. Magma propagation at Piton de la Fournaise from joint inversion of InSAR and GNSS. J. Geophys. Res., Solid Earth 124, 1361–1387.

Taisne, B., Brenguier, F., Shapiro, N., Ferrazzini, V., 2011. Imaging the dynamics of magma propagation using radiated seismic intensity. Geophys. Res. Lett. 38.

Tarantola. A., 2005. Inverse Problem Theory and Methods for Model Parameter Estimation, vol. 89. SIAM.

Tepp, G., Hotovec-Ellis, A., Shiro, B., Johanson, I., Thelen, W., Haney, M.M., 2020. Seismic and geodetic progression of the 2018 summit caldera collapse of K¯ılauea volcano Farth Planet, Sci Lett 540 116250

Townsend, M.R., Pollard, D.D., Smith, R.P., 2017. Mechanical models for dikes: a third school of thought. Tectonophysics 703, 98–118.

Trusdell, F.A., Wolfe, E.W., Morris, J., 2005. Digital Database of the Geologic Map of the Island of Hawaii. U.S. Geological Survey, Data Series 144.

Twardzik, C., Vergnolle, M., Sladen, A., Avallone, A., 2019. Unravelling the contribution of early postseismic deformation using sub-daily gnss positioning. Sci. Rep. 9, 1–12.

Walker, G.P., Sigurdsson, H., 2000. Basaltic volcanoes and volcanic systems. In: Encyclopedia of Volcanoes, pp. 283–289.

Wessel, P., Smith, W.H., Scharroo, R., Luis, J., Wobbe, F., 2013. Generic mapping tools: improved version released. Eos 94, 409–410.

Woods, J., Winder, T., White, R.S., Brandsdóttir, B., 2019. Evolution of a lateral dike intrusion revealed by relatively-relocated dike-induced earthquakes: the 2014–15 Bárðarbunga–Holuhraun rifting event, Iceland. Earth Planet. Sci. Lett. 506, 53–63.