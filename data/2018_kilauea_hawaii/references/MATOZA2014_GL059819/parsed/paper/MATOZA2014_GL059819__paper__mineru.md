## RESEARCH LETTER

10.1002/2014GL059819

## Key Points:

• Automated event classification and systematic relocation of LPs

• Kilauea LPs in compact source volume, intermittently active from 1986 to 2009

• Source process controlled by barrier to magma flow or geometrical discontinuity

## Supporting Information:

• Readme

• Readme

• Text S1

• Figure S1

• Catalog S1

Correspondence to: R. S. Matoza, rmatoza@ucsd.edu

## Citation:

Matoza, R. S., P. M. Shearer, and P. G. Okubo (2014), High-precision relocation of long-period events beneath the summit region of K¯ılauea Volcano, Hawai‘i, from 1986 to 2009, Geophys. Res. Lett., 41, 3413–3421, doi:10.1002/2014GL059819.

Received 5 MAR 2014 Accepted 1 MAY 2014 Accepted article online 6 MAY 2014 Published online 20 MAY 2014

# High-precision relocation of long-period events beneath the summit region of K¯ılauea Volcano, Hawai‘i, from 1986 to 2009

Robin S. Matoza<sup>1</sup>, Peter M. Shearer<sup>1</sup>, and Paul G. Okubo<sup>2</sup>

<sup>1</sup>Institute of Geophysics and Planetary Physics, Scripps Institution of Oceanography, University of California, San Diego, La Jolla, California, USA, <sup>2</sup>Hawaiian Volcano Observatory, U.S. Geological Survey, Hawaii Volcanoes National Park, Hawaii, USA

Abstract Long-period (0.5–5 Hz, LP) seismicity has been recorded for decades in the summit region of K¯ılauea Volcano, Hawai‘i, and is postulated as linked with the magma transport and shallow hydrotherma systems. To better characterize its spatiotemporal occurrence, we perform a systematic analysis of 49,030 seismic events occurring in the K¯ılauea summit region from January 1986 to March 2009 recorded by the ∼50-station Hawaiian Volcano Observatory permanent network. We estimate 215,437 P wave spectra, considering all events on all stations, and use a station-averaged spectral metric to consistently classify LP and non-LP seismicity. We compute high-precision relative relocations for 5327 LP events (43% of all classified LP events) using waveform cross correlation and cluster analysis with 6.4 million event pairs, combined with the source-specific station term method. The majority of intermediate-depth (5–15 km) LPs collapse to a compact volume, with remarkable source location stability over 23 years indicating a source process controlled by geological or conduit structure.

## 1. Introduction

Long-period (0.5–5 Hz, LP) seismic events are transient signals consisting of a brief broadband onset, followed by a coda of decaying harmonic oscillations containing pronounced spectral peaks that are inde pendent of azimuth and distance to the source. This is commonly interpreted as a broadband, time-localized pressure excitation mechanism (or trigger mechanism), followed by the volumetric response of a fluid-filled resonator [e.g., Chouet and Matoza, 2013].

On Hawai‘i Island, LP events are closely associated with volcanic tremor, magma transport, and shallow hydrothermal activity and have been observed at a range of depths below K¯ılauea, Mauna Loa, and Loihi [Koyanagi et al., 1987; Battaglia et al., 2003; Okubo and Wolfe, 2008; Wright and Klein, 2006]. Here we focus on LP events occurring below the summit region of K¯ılauea. K¯ılauea LPs have generally been observed in three broad depth ranges: (1) shallow <5 km, (2) intermediate 5–15 km, and (3) deep 30–60 km [Koyanagi et al., 1987]. Since the beginning of the ongoing Pu‘u O‘<sup>¯</sup> o-K¯ upaianaha eruption in 1983, deep LP seismicity (3) has¯ largely diminished and is not considered in this study.

We focus on the shallow (1) and intermediate (2) depth LPs below K¯ılauea, which are believed to outline parts of the magma transport pathway beneath the summit [Wright and Klein, 2006]. Studies of the shallow LPs, and very long period (VLP) events within the same depth range, have generally attributed them to magmatic-hydrothermal interactions, e.g., to impulsive discharges of steam and collapse of hydrothermal cracks associated with rising magmatic gases and groundwater boiling [e.g., Ohminato et al., 1998; Saccorotti et al., 2001; Almendros et al., 2001b; Kumagai et al., 2005]. The intermediate-depth LPs are less well understood. However, there is a general association between swarms of the shallow LPs with rapid summit deflation and of the intermediate-depth LPs with slower inflation and resupply [Okubo and Nakata, 2003]. A relatively aseismic zone between the intermediate and shallow LPs has been interpreted as a magma storage reservoir [Koyanagi et al., 1987; Klein et al., 1987; Wright and Klein, 2006]. Much of the proposed deep magma transport system beneath K¯ılauea is aseismic, inferred as relatively open flow channels, in which quasi-steady magma flow does not generate seismicity [Aki and Koyanagi, 1981; Koyanagi et al., 1987; Klein et al., 1987; Wright and Klein, 2006].

Locating LP seismicity is often challenging because of emergent onsets [e.g., Koyanagi et al., 1987; Lahr et al., 1994], and a number of diferent strategies have been developed [e.g., Almendros et al., 2001a; Battaglia et al., 2003; Rowe et al., 2004; Neuberg et al., 2006; Thelen et al., 2008; De Barros et al., 2009; Gambino et al.,

![](mineru/MATOZA2014_GL059819__paper/images/cec3b15c07eb15329f3900907c37094f6c6c843758b72fa4b787d1695c493c9f.jpg)

![](mineru/MATOZA2014_GL059819__paper/images/dba0ab0d1466b05e05a4d98e2f0dc44e09f3e2da6207d7d3755971997c034d6b.jpg)  
Figure 1. Starting catalog locations of events in the K¯ılauea summit study region, with events color coded according to their station-averaged frequency index (FI) value (see text for details). This plot shows 41,475 events for which P spectra could be computed matching our signal-to-noise criteria. We define 12,290 events with FI ≤ −1 as LP events for the purpose of this study (blue colors). Inverted triangles are the stations in this area (for the full station distribution used in this work, see Matoza et al. [2013]).

2009; Arciniega-Ceballos et al., 2012; Kumagai et al., 2013; Zecevic et al., 2013]. In this paper, we systematically apply waveform cross correlation, cluster analysis, and relative relocation to 23 years of LP seismicity at K¯ılauea in order to characterize spatiotemporal variability of the magma transport system. In addition, we develop a method for classifying and isolating LP events from other types of volcanic and tectonic seismicity. Our emphasis is on methods that do not rely heavily on waveform repicking and event classification by analysts, can be applied systematically to large data sets, and could potentially be automated and incorporated into routine network processing for near-real-time analysis of volcanic seismicity.

## 2. Data and Spectral Event Classification

We begin with event-triggered waveform data from the U.S. Geological Survey (USGS) Hawaiian Volcano Observatory (HVO) permanent telemetered seismic network from January 1986 to March 2009, a time period in which data were cataloged and available in a consistent format (e.g., in March 2009, the data acquisition system was changed from Caltech-USGS Seismic Processing (CUSP) to ANSS (Advanced National Seismic System) Quake Monitoring System (AQMS) [Nakata and Okubo, 2010]). We also begin with catalog locations produced using the CUSP system and a one-dimensional (1-D) velocity model and, when available for a subset of events, phase pick data from HVO [Nakata and Okubo, 2010]. The standard stations are 1 Hz short-period geophones, and the majority are vertical component only [Nakata and Okubo, 2010]. All event data are resampled to a uniform 100 Hz sample rate. In this study, we focus on 49,030 seismic events with an initial (CUSP) catalog location falling within a region defined by [19.35<sup>◦</sup>, 19.45<sup>◦</sup>N; −155.35<sup>◦</sup>, −155.15<sup>◦</sup>W] and with depths ≤20 km, which includes shallow and intermediate-depth LPs in the K¯ılauea summit region (Figure 1).

As a first step, it is necessary to identify and isolate the LP events from the rest of the seismicity occurring within the K¯ılauea summit region, which includes ordinary tectonic and volcano-tectonic (VT) events [Klein et al., 1987]. LP events have been classified and flagged by HVO analysts based on waveform and spectral characteristics and location [e.g., Okubo and Nakata, 2003]. However, this classification scheme is subjective

![](mineru/MATOZA2014_GL059819__paper/images/84878cee427e7a35284494976c658874650d9bcc89a439f6745faa9205a1a9c3.jpg)  
Figure 2. Histogram of station-averaged FI values (median FI over all recording stations) for the 41,475 events considered. The threshold value of −1 is indicated by the dashed line.

and has not been consistently or systematically applied through time. We seek an automated method that can be applied in a standardized way to all event data. We investigate the suitability of the Frequency Index (FI) metric introduced by Buurman and West [2010]. The FI is defined as

$$
\mathsf {F I} = \log_ {1 0} \frac {\overline {{A}} _ {\text { upper }}}{\overline {{A}} _ {\text { lower }}},\tag{1}
$$

where $\overline { { A } } _ { \mathsf { u p p e r } }$ and $\overline { { A } } _ { \mathsf { i o w e r } }$ are the mean spectral amplitudes in a chosen band of high frequencies and low frequencies, respectively. Here we choose bands of 1–5 Hz for $\overline { { A } } _ { \mathsf { i o w e r } }$ and 5–15 Hz for $\overline { { A } } _ { \mathsf { u p p e r } }$ . We compute the $P$ wave spectra and FI values for all stations on the vertical component (unfiltered data) for the 49,030 events. The spectra are computed for 1.28 s noise and signal windows before and after the P pick with a Hanning taper [Shearer et al., 2006]. If pick data are not available for the waveform, we use a predicted pick based on the catalog location and

1-D velocity model. Spectra are only used if the signal-to-noise ratio is >3 in the 1–15 Hz band. This results in 215,437 P spectra; 7,555 events had no P spectra matching the signal-to-noise requirements and were excluded from all subsequent analysis.

We found the FI to vary systematically with waveform features and spectra at a given station, indicating its suitability as a metric for characterizing LP versus non-LP events. By comparing results from diferent stations, we found that the single-station FI [Buurman and West, 2010; Ketner and Power, 2013] is reasonably robust with respect to source-receiver azimuth and distance, but there is a weak dependence of single-station FI with distance. We define a more robust FI metric as the median average FI across all recording stations (Figure 1). This station-averaged FI is more robust with respect to path and site efects and does not depend upon the position of the events with respect to a single station. FI is weakly dependent on event magnitude (via variations in corner frequency for tectonic and VT events), but the variation is not significant for our application, so we do not apply a magnitude-dependent correction.

Both the single-station and station-averaged FI values form bimodal distributions, indicating two separate event types (Figure 2). However, the probability density functions of the two event types overlap, precluding a complete separation based on FI alone. Nevertheless, LP events under K¯ılauea can be largely isolated by selecting events with station-averaged FI ≤ −1. This cutof was determined based upon the geographic distribution of events according to their FI values (Figure 1), as well as by examining representative waveforms and spectra of events with diferent FI values. Events with low FI values are more likely to be flagged by analysts as LP events than those with high FI values, but the analyst classifications are inconsistent, as illustrated in Figure 3. For this reason we use the FI to classify the LP events, as it can be applied uniformly to the entire data set.

The resultant catalog of 12,290 LP events (25% of all events considered and corresponding to $\mathsf { F l } \le - 1 )$ will be slightly incomplete, as it does not include the overlapping portion of the histogram shown in Figure 2 $( - 1 < \mathsf { F l } < - 0 . 7 )$ , but we consider this more desirable for the current application than including mixed or ambiguous event types. Note, for example, that traces 4 and 5 in Figure 3 (both flagged and nonflagged) are likely LP events but occur in the overlapping portion of the FI histogram (Figure 2). Furthermore, presumed shallow LPs (<5 km) tend to have higher FI values than intermediate-depth (5–15 km) LPs (Figure 1), with a higher proportion of the analyst-flagged shallow LPs tending to fall within the excluded overlapping range $( - 1 < \mathsf { F l } < - 0 . 7 )$ . For 1986 to 2009, 28% of all 17,615 analyst-flagged LPs are shallow (<5 km) and 72% are intermediate depth (5–15 km). In contrast, for the same time period, 19% of our 12,290 FI-defined LP events are shallow and 81% are intermediate depth. Therefore, our catalog of LPs is somewhat more biased toward the intermediate-depth LPs.

![](mineru/MATOZA2014_GL059819__paper/images/0190396dd11a3f7ac2213a385b16fc6ed6c0f5a3c0fb7e93a977265321ea27fa.jpg)  
Figure 3. Representative waveforms at station AHU (see Figure 1), vertical component, corresponding to the FI range indicated on the right. The waveforms on the left are events flagged by analysts as “LP,” while those on the right are not flagged as LP. In our classification scheme, any event with a frequency index ≤ −1 is defined as an LP event (i.e., the lower five blue waveforms in each case).

We note that we investigated an alternative metric based on the ratio of spectral amplitudes in a small bandwidth compared to a broad bandwidth and a metric based on the coda duration (ratio of signal power at a later time in the waveform compared to the event onset), but neither of these metrics improved the ability to separate the event types. A classification scheme that also incorporates source mechanism type is desirable [e.g., Chouet and Matoza, 2013] but would depend on the quality of focal mechanism solutions, and we do not attempt this here. Future extensions to this work could use more elaborate event classification techniques [e.g., Falsaperla et al., 1996; Langer et al., 2009; Dawson et al., 2010; Messina and Langer, 2011]. While such techniques may ofer significant advances in the ability to classify, separate, and cluster event types, an advantage of the present approach is its relative simplicity, robustness, and ease of interpretation.

## 3. Cross Correlation and Relocation

Our data and methodology are similar to those described by Matoza et al. [2013], to which the reader is referred for more details. The principal aim is to improve the relative location accuracy between nearby events using a 1-D velocity model, neglecting topography and station elevation [see Matoza et al., 2013]. We also use the shrinking-box source-specific station term (SSST) method [Lin and Shearer, 2005, 2006] to improve the absolute locations using the available phase pick data.

We have adapted our cross-correlation and relocation methods for use on LP events, which have waveform properties that are diferent from ordinary tectonic and volcano-tectonic (VT) events on Hawai‘i Island. We pair each event with all events within 2 km, or at least 100 nearest neighbors (based on initial catalog locations). For each of these 6.4 million pairs, we compute cross correlations. Unlike Matoza et al. [2013], we do not compute cross correlations and measure diferential times for S phases for the LP events.

LP events are often reported as (and sometimes defined by) lacking clear S waves [Mcnutt, 2005], but the classic fluid-driven crack source model for LP events predicts both P and S wave radiation, with the S waves often being obscured by extended coda waves from the fluid resonance [Chouet, 1988]. We undertook several tests to identify if S waves are present in the LP waveform data (see supporting information). These tests indicated that S phases are sometimes present on some stations and components for LP events but that often a long-duration P coda merges into the S arrival. If the S wave arrival time contains mixed phases, determining diferential travel times based on S wave windows may lead to spurious results from aligning part of the LP coda. Therefore, in our relocation of LP events, we use diferential time measurements from P wave cross correlations of vertical components only. We cross correlate P phases using a time window chosen to be shorter than the S − P time in order to avoid S waves.

Prior to waveform cross correlation, the data are band-pass filtered from 1 to 10 Hz [see Matoza et al., 2013]. We compute the cross-correlation functions using time shifts of up to ±1.5 s and waveform time windows defined as follows: (1) If P picks are available, the P window is −0.5 s to 1 s around the P pick; or (2) If P picks are not available, we use −1 s to 1 s around a predicted P pick. We only save waveform cross-correlation results for event pairs that have an average P waveform correlation coeficient >0.45 and at least eight diferential time measurements with correlation coeficient >0.75 from source-station distances <80 km. We only use diferential time measurements with correlation coeficient values >0.75. Using this cross-correlation information, we relocate 5327 events (43% of all LP events defined by our FI threshold, section 2) using the combined cluster analysis and relocation algorithm described by Matoza et al. [2013] with 1.6 million diferential times from ∼167,000 similar event pairs.

During the relative relocation procedure, the absolute locations of similar event cluster centroids are constrained only by the starting (CUSP) catalog locations. If the starting locations exhibit too much scatter, separate clusters of events may end up with centroids that are erroneously separated, arising from scatter in the starting locations of events contributing to diferent clusters. In order to reduce this efect, we also incorporated phase pick information where available. Phase pick data were available for a subset of 7300 of the LP events defined based on the FI threshold. For these events, we computed new locations using the shrinking-box SSST method, implemented in the COMPLOC earthquake location package [Lin and Shearer, 2005, 2006].

We then shifted our relocated seismicity clusters to align with the improved SSST locations as follows. For each similar event cluster, we identify events within the cluster that also have an independent SSST location. If at least 10 events and 20% of all events in the cluster have independent SSST locations, we shift the cluster centroid so that it aligns with the centroid of the corresponding SSST locations (5199 final events relocated). As a test, we also repeated our cross correlation and relative relocation procedure on only the 7300 SSST event locations. The results were very similar to those presented here but contained fewer final relocations (3320 events).

We compute formal relative location uncertainties using the bootstrap approach of Lin et al. [2007] (see supporting information Figure S1). As described by Matoza et al. [2013], the formal relative location uncertainties do not account for unmodeled 3-D velocity structure, and the absolute location uncertainties are likely much greater (perhaps on the order of ±1 km horizontally and ±2 km in depth).

## 4. Relocation Results and Discussion

Our relocation results are shown in Figure 4. The vast majority of intermediate-depth LPs collapse to a compact volume (Figure 4b), in contrast to the relatively large distributed source volume indicated by the original catalog locations (Figure 4a). Spherical volumes of radius 800 m and 2 km enclose 50% and 75% of the relocated intermediate-depth LPs, respectively, although these volumes are likely dependent on the 1-D velocity model used. The remarkable source location stability and temporal evolution are further illustrated in Figure 5. The intermediate-depth LPs occur with swarm-like behavior and within the same small volume (Figures 4b and 5).

Relocated LPs in Figure 5a exhibit minor switching back and forth between two preferred depths, which is visible as two clusters in Figure 4b and appears to be a robust feature of the relocation results. The shallower cluster is mainly active during 1989 and after 1996. The two distinct spatial clusters of events shown in Figure 4b are actually part of the same similar event cluster, so their relative positions are well constrained. However, a similar feature (closely spaced spatial clusters) could potentially arise as an artifact. For example, a similar location pattern might be produced if the true event locations are in one compact cluster, but some of the events happen to be recorded by diferent station configurations. To examine this further, we performed a series of tests, e.g., varying the cross-correlation threshold and relocation parameters, varying the relocation algorithm, varying a distance cutof for contributing stations, and removing data from key stations. In none of these tests did the two spatial clusters collapse into a single cluster. We also relocated well-correlated pairs of events spanning the two clusters and found them to locate into the two distinct clusters. These tests suggest that the two separate cluster locations are a true feature. However, it is possible that further tests (beyond the scope of the present study) may reveal another source of bias hitherto uncounted for.

The locations in Figure 4b also include some events in a more difuse volume surrounding the main relocated cluster. These events cross correlate more poorly with other events and have greater location uncertainty than events in the main cluster (see supporting information Figure S1). A likely interpretation is that the difuse volume represents location uncertainty rather than a truly difuse source region. Indeed, when applying more strict threshold criteria for using cross-correlation information (results not shown here), only events within the small compact clusters remain. This indicates a relatively compact, true source region for all of the intermediate-depth LPs. However, because of the location uncertainty (supporting information Figure S1), we cannot rule out that some events do occur in the more difuse volume.

(a)  
![](mineru/MATOZA2014_GL059819__paper/images/a7f1845e8cd034c665cd38107d599bc0c67fffedb5a0e7741270897f71b8e23f.jpg)

![](mineru/MATOZA2014_GL059819__paper/images/4031553bd92fcbaf72e07b115d32fa13c3f81a77fd2304e1c884a5b74df9547e.jpg)  
(b)

![](mineru/MATOZA2014_GL059819__paper/images/3ef978d9b2b28022c1c3783807086a5fd93a9c2d4bfb0bdff92354f9ad80c9d8.jpg)

![](mineru/MATOZA2014_GL059819__paper/images/98aa8d446d37531111153ab781abd57edf46dd5e51f3e63102bebdac0c37bd27.jpg)  
Figure 4. (a) Original catalog locations of 12,290 events we classify as LP based upon station-averaged FI (see Figure 1). (b) The 5199 LP events relocated using a 1-D velocity model, P waveform cross correlation, and cluster analysis, com bined with the source-specific station term method, Note that shallow I Ps shown in Figure 4a do not cross correlate and relocate as well as the intermediate-depth LPs given our threshold parameters.

(a)  
![](mineru/MATOZA2014_GL059819__paper/images/b15ac25ce51d4e5a075cc02b2020aa34793fbb1f34fc021e99994b635b889f7e.jpg)

(b)  
![](mineru/MATOZA2014_GL059819__paper/images/64d96ef62eb90a5155c2f598aac1b0828d9701dd1715317b27f6dd95adb313a7.jpg)

(c)  
![](mineru/MATOZA2014_GL059819__paper/images/e997c767e1ece85db929007bcaa43e663d093fb92e715e78aa3f9499af8f531a.jpg)

![](mineru/MATOZA2014_GL059819__paper/images/881599589396906a84dc54f850d0f8ac3a34b13cc16701737e57eccdafff9515.jpg)  
Figure 5. Temporal evolution of seismicity in the K¯ılauea summit region. (a) Depth versus time for the relocated LP events (blue dots) and all LPs (grey dots, catalog depths). (b) Multiplet number of the relocated LP events, with multiplet numbers corresponding to the ranked number of events in the multiplet. Note that most events are in multiplets 1–3, which are active from 1986 to 2009. (c) Cumulative number of events N for all LPs (grey line) and relocated LPs (blue line) (d) N for all seismicity shown in Figure 1 (black line) and all events with station-averaged FI > −0.7 (red line).

As shown in Figure 4, the shallow LPs do not cross correlate and relocate as well as the intermediate-depth LPs but do collapse to a compact cluster beneath the Halema‘uma‘u pit crater. In total, 709 (31% of 2291) shallow LPs cross correlated and relocated well compared to 4490 (45% of 9999) intermediate-depth LPs. This may be because the shallow LPs have less repetitive waveforms than the intermediate-depth LPs but may also be because there are fewer shallow LP events in total, leading to fewer possible similar events pairs.

The 23 year span of this data set covers a wide range of eruptive activity, including, for example, the Pu‘u O‘<sup>¯</sup> o-K¯ upaianaha eruption from 1983 onward; multiple intrusions into the east rift zone; the shutdown of¯ Kupaianaha in 1992; an intrusion into the caldera region in early 1996; a surge in summit region activity¯ in early 1997 followed by lava eruption from Napau in the east rift zone; the disruption and reorganization of magma supply to Pu‘u O‘<sup>¯</sup> o in 2007; and the beginning of the summit eruption in 2008 [e.g.,¯ Heliker and Mattox, 2003; Okubo and Nakata, 2003; Poland et al., 2008, 2012]. The relative location stability of the intermediate-depth LPs during this time indicates a source location and process controlled by geologic or conduit structure. For example, an abrupt change in lithology and/or a geometrical conduit discontinuity may lead to magma flow disturbances and enhanced seismogenic potential at this location. It is well known that geometrical complexity in conduits, e.g., elbows, bends, constrictions, and flares, can be important in generating various types of volcanic seismicity [e.g., Chouet et al., 2010; Thomas and Neuberg, 2012]. A geometrical discontinuity is also consistent with the intermediate-depth LPs occurring at the base of a relatively aseismic summit magma storage reservoir [Klein et al., 1987]. Additionally or alternatively, this location may represent a particularly strong barrier to magma flow, which is seismogenic when magma is forced through it [Aki and Koyanagi, 1981].

It is beyond the scope of the present work to integrate our LP observations within the context of the complex eruptive history of K¯ılauea during this time period or in the context of other data such as continuous volcanic tremor metrics or deformation data. However, we note that LP event occurrence decreases from 2005 (Figure 5). Since the CUSP catalog triggers were being generated at a consistent rate, and since our LP classification scheme is automatic (does not rely on analysts), the drop in intermediate-depth LP activity from 2005 to 2009 appears to be real. In addition, the increase in intermediate-depth LPs in 2003 broadly coincides with summit inflation in late 2003 [Poland et al., 2008]. We note, however, that LP observations at K¯ılauea have often occurred in swarms not clearly related to changes in eruptive activity [Okubo and Nakata, 2003].

Our results are consistent with previous relocation studies of LP seismicity at K¯ılauea [Battaglia et al., 2003; Wolfe et al., 2004]. Battaglia et al. [2003] relocated K¯ılauea LP events between January 1997 and December 1999. In addition to the diferent time periods and number of events considered, the principal diferences between our study and that of Battaglia et al. [2003] are that (1) Battaglia et al. [2003] used analyst flags to classify LP events, whereas we use the FI (see section 2); (2) Battaglia et al. [2003] used longer time windows for estimating diferential times (20.48 s) (see section 3); and (3) Battaglia et al. [2003] revised the event absolute locations using the spatial amplitude method. We performed tests incorporating diferences (1) and (2) to validate our method against their results. Using HVO analyst flags of LP events (1) and longer time windows for cross correlation (2), we obtained highly consistent results. The main diference after making these changes was in the absolute centroid of the intermediate-depth LPs. This centroid is constrained to a location beneath the eastern edge of the Halema‘uma‘u pit crater in our relocation results but is shifted to a position beneath the eastern edge of the rim of K¯ılauea Caldera in the work by Battaglia et al. [2003]. Our results are also consistent with those of Wolfe et al. [2004], who relocated analyst-flagged LPs ≥13 km depth beneath K¯ılauea from 1988 to 1998. Our study demonstrates the feasibility of comprehensive and systematic spectral classification and relocation of LP seismicity, which could be automated for use in near-real-time eruption monitoring.

## 5. Conclusions

We have systematically analyzed 49,030 seismic events occurring in the K¯ılauea summit region from January 1986 to March 2009 as recorded on the HVO permanent network. We classified events consistently based on their spectra and achieved relative relocation of 5327 identified LP events. Intermediate-depth (5–15 km) LPs spanning the 23 year data set collapse to a remarkably consistent and small source volume (a sphere of radius 2 km encloses 75% of the relocated intermediate-depth LPs). The repeated seismic illumination of a tiny portion of K¯ılauea’s inferred magma transport system, during 23 years of eruptive changes, indicates an LP source process controlled by stable geologic or conduit structure, such as a geometrical conduit discontinuity or a particularly strong barrier to magma flow. Extensions to this work include continuing the analysis on waveform data from March 2009 onward, combined with inversions for the source mechanism of intermediate-depth LPs.

## Acknowledgements

We thank the staf of the USGS Hawaiian Volcano Observatory for maintaining the seismic network and enabling studies of long-term seismicity variations. Cecily Wolfe and Guoqing Lin worked with us to convert and assemble the data set. We thank Charlotte Rowe, Phil Dawson, and an anonymous reviewer for their insightful comments. This work was funded by NSF award EAR-1045035 with additional support from the Cecil H. and Ida M. Green Foundation at the Institute of Geophysics and Planetary Physics, Scripps Institution of Oceanography. The relocated LP catalog is available for download in the supporting information.

The Editor thanks Charlotte Rowe and Michael West for their assistance in evaluating this paper.

## References

Aki, K., and R. Koyanagi (1981), Deep volcanic tremor and magma ascent mechanism under Kilauea, Hawaii, J. Geophys. Res., 86(B8), 7095–7109.

Almendros, J., B. Chouet, and P. Dawson (2001a), Spatial extent of a hydrothermal system at Kilauea Volcano, Hawaii, determined from array analyses of shallow long-period seismicity 1. Method, J. Geophys. Res., 106(B8), 13,565–13,580

Almendros, J., B. Chouet, and P. Dawson (2001b), Spatial extent of a hydrothermal system at Kilauea Volcano, Hawaii, determined from array analyses of shallow long-period seismicity 2. Results, J. Geophys. Res., 106(B8), 13,581–13,597.

Arciniega-Ceballos, A., P. Dawson, and B. A. Chouet (2012), Long period seismic source characterization at Popocatépetl volcano, Mexico, Geophys. Res. Lett., 39, L20307, doi:10.1029/2012GL053494.

Battaglia, J., J.-L. Got, and P. Okubo (2003), Location of long-period events below Kilauea Volcano using seismic amplitudes and accurate relative relocation, J. Geophys. Res., 108(B12), 2553, doi:10.1029/2003JB002517

Buurman, H., and M. E. West (2010), Seismic precursors to volcanic explosions during the 2006 eruption of Augustine Volcano, in The 2006 Eruption of Augustine Volcano, Alaska, U.S. Geol. Surv. Prof. Pap., 1769, edited by J. A. Power, M. L. Coombs, and J. T. Freymueller, chap. 2, pp. 41–57, U.S. Geological Survey, Reston, Va.

Chouet, B. (1988), Resonance of a fluid-driven crack: Radiation properties and implications for the source of long-period events and harmonic tremor, J. Geophys. Res., 93, 4375–4400.

Chouet, B. A., and R. S. Matoza (2013), A multi-decadal view of seismic methods for detecting precursors of magma movement and eruption, J. Volcanol. Geotherm. Res., 252, 108–175.

Chouet, B. A., P. B. Dawson, M. R. James, and S. J. Lane (2010), Seismic source mechanism of degassing bursts at Kilauea Volcano, Hawaii Results from waveform inversion in the 10–50 s band, J. Geophys. Res., 115, B09311, doi:10.1029/2009JB006661.

Dawson, P. B., M. C. Benitez, B. A. Chouet, D. Wilson, and P. G. Okubo (2010), Monitoring very-long-period seismicity at Kilauea Volcano, Hawaii, Geophys. Res. Lett., 37, L18306, doi:10.1029/2010GL044418.

De Barros, L., C. J. Bean, I. Lokmer, G. Saccorotti, L. Zuccarello, G. S. O’Brien, J. P. Métaxian, and D. Patanè (2009), Source geometry from exceptionally high resolution long period event observations at Mt Etna during the 2008 eruption, Geophys. Res. Lett., 36, L24305, doi:10.1029/2009GL041273.

Falsaperla, S., S. Graziani, G. Nunnari, and S. Spampinato (1996), Automatic classification of volcanic earthquakes by using multi-layered neural networks, Nat. Hazard., 13, 205–228

Gambino, S., L. Cammarata, and S. Rapisarda (2009), High precision locations of long-period events at La Fossa Crater (Vulcano Island, Italy), Ann. Geophys., 52(2), 137–147.

Heliker, C., and T. N. Mattox (2003), The first two decades of the Pu‘u O‘<sup>¯</sup> o-K¯ upaianaha eruption: Chronology and selected bibliography,¯ in The Pu‘u O‘<sup>¯</sup> o-K¯ upaianaha Eruption of K¯ ¯ılauea Volcano, Hawai‘i: The First 20 Years, U.S. Geol. Surv. Prof. Pap., 1676, edited by C. Heliker, D. A. Swanson, and T. J. Takahashi, chap. 1, pp. 1–28, U. S. Geological Survey, Reston, Va.

Ketner, D., and J. Power (2013), Characterization of seismic events during the 2009 eruption of Redoubt Volcano, Alaska, J. Volcanol. Geotherm. Res. 259.45-62

Klein, F. W., R. Y. Koyanagi, J. S. Nakata, and W. R. Tanigawa (1987), The seismicity of Kilauea’s magma system, in Volcanism in Hawaii, U.S. Geol. Surv. Prof. Pap., 1350(2), edited by R. W. Decker, T. L. Wright, and P. H. Staufer, chap. 43, pp. 1019–1185, U. S. Geological Survey, Reston, Va.

Koyanagi, R. Y., B. Chouet, and K. Aki (1987), Origin of volcanic tremor in Hawaii: Part I. Data from the Hawaiian Volcano Observatory 1969–1985, in Volcanism in Hawaii, U.S. Geol. Surv. Prof. Pap.,1350(2), edited by R. W. Decker, T. L. Wright, and P. H. Staufer, chap. 43, pp. 1221–1257, U. S. Geological Survey, Reston, Va.

Kumagai, H., B. A. Chouet, and P. B. Dawson (2005), Source process of a long-period event at Kilauea Volcano, Hawaii, Geophys. J. Int., 161, 243–254.

Kumagai, H., R. Lacson, Y. Maeda, M. S. Figueroa, T. Yamashina, M. Ruiz, P. Palacios, H. Ortiz, and H. Yepes (2013), Source amplitudes of volcano-seismic signals determined by the amplitude source location method as a quantitative measure of event size, J. Volcanol. Geotherm. Res., 257, 57–71.

Lahr, J. C., B. A. Chouet, C. D. Stephens, J. A. Power, and R. A. Page (1994), Earthquake classification, location, and error analysis in a volcanic environment: Implications for the magmatic system of the 1989–1990 eruptions of Redoubt Volcano, Alaska, J. Volcanol. Geotherm. Res., 63, 137–151.

Langer, H., S. Falsaperla, M. Masotti, R. Campanini, S. Spampinato, and A. Messina (2009), Synopsis of supervised and unsupervised pattern classification techniques applied to volcanic tremor data at Mt Etna, Italy, Geophys. J. Int., 178(2), 1132–1144, doi:10.1111/j.1365-246X.2009.04179.x.

Lin, G., and P. Shearer (2005), Tests of relative earthquake location techniques using synthetic data, J. Geophys. Res., 110, B04304, doi:10.1029/2004JB003380.

Lin, G., and P. Shearer (2006), The COMPLOC earthquake location package, Seismol. Res. Lett., 77(4), 440–444

Lin, G., P. M. Shearer, and E. Hauksson (2007), Applying a three-dimensional velocity model, waveform cross correlation, and cluster analysis to locate southern California seismicity from 1981 to 2005, J. Geophys. Res., 112, B12309, doi:10.1029/2007JB004986.

Matoza, R. S., P. M. Shearer, G. Lin, C. J. Wolfe, and P. G. Okubo (2013), Systematic relocation of seismicity on Hawaii Island from 1992 to 2009 using waveform cross correlation and cluster analysis, J. Geophys. Res., 118, 2275–2288, doi:10.1002/jgrb.50189

Mcnutt, S. R. (2005), Volcanic seismology, Annu. Rev. Earth Planet. Sci., 32, 461–491, doi:10.1146/annurev.earth.33.092203.122459.

Messina, A., and H. Langer (2011), Pattern recognition of volcanic tremor data on Mt. Etna (Italy) with KKAnalysis—A software program for unsupervised classification, Comput. Geosci., 37, 953–961.

Nakata, J. S., and P. G. Okubo (2010), Hawaiian Volcano Observatory Seismic Data, January to March 2009. U. S. Geol. Surv. Open File Rep., 2010-1079, Geological Survey, Reston, Va.

Neuberg, J. W., H. Tufen, L. Collier, D. Green, T. Powell, and D. Dingwell (2006), The trigger mechanism of low-frequency earthquakes on Montserrat, J. Volcanol. Geotherm. Res., 153, 37–50.

Ohminato, T., B. A. Chouet, P. B. Dawson, and S. Kedar (1998), Waveform inversion of very-long-period impulsive signals associated with magmatic injection beneath Kilauea Volcano, Hawaii, J. Geophys. Res., 103, 23,839–23,862

Okubo, P., and J. S. Nakata (2003), Tectonic pulses during Kilauea’s current long-term eruption, in The Pu‘u O‘<sup>¯</sup> o-K¯ upaianaha Eruption of¯ K¯ılauea Volcano, Hawai‘i: The First 20 Years, U.S. Geol. Surv. Prof. Pap., 1676, edited by C. Heliker, D. A. Swanson, and T. J. Takahashi, chap. 11, pp. 173–186, U. S. Geological Survey, Reston, Va.

Okubo, P. G., and C. J. Wolfe (2008), Swarms of similar long-period earthquakes in the mantle beneath Mauna Loa Volcano, J. Volcanol. Geotherm. Res., 178, 787–794.

Poland, M., A. Miklius, T. Orr, J. Sutton, C. Thornber, and D. Wilson (2008), New episodes of volcanism at Kilauea Volcano, Hawaii, EOS, Trans. AGU, 89(5), 37–38, doi:10.1029/2008EO050001.

Poland, M. P., A. Miklius, A. J. Sutton, and C. R. Thornber (2012), A mantle-driven surge in magma supply to Kilauea Volcano during 2003–2007, Nat. Geosci., 5, 295–300.

Rowe, C. A., C. H. Thurber, and R. A. White (2004), Dome growth behavior at Soufriere Hills Volcano, Montserrat, revealed by relocation of volcanic event swarms, 1995–1996, J. Volcanol. Geotherm. Res., 134, 199–221.

Saccorotti, G., B. Chouet, and P. Dawson (2001), Wavefield properties of a shallow long-period event and tremor at Kilauea Volcano, Hawaii, J. Volcanol. Geotherm. Res., 109, 163–189

Shearer, P. M., G. A. Prieto, and E. Hauksson (2006), Comprehensive analysis of earthquake source spectra in Southern California, J. Geophys. Res., 111, B06303, doi:10.1029/2005JB003979.

Thelen, W. A., R. S. Crosson, and K. C. Creager (2008), Absolute and relative locations of earthquakes at Mount St. Helens, Washington using continuous data: Implications for magmatic processes, in A Volcano Rekindled: The First Year of Renewed Eruptions at Mount St. Helens 2004-2006, U.S. Geol. Surv. Prof. Pap., 1750, edited by D. R. S. W. E. Scott and P. H. Staufer, pp. 71–95, chap. 11, pp. 173–186, U. S. Geological Survey, Reston, Va.

Thomas, M. E., and J. Neuberg (2012), What makes a volcano tick—A first explanation of deep multiple seismic sources in ascending magma, Geology, 40(4), 351–354.

Wolfe, C. J., P. G. Okubo, G. Ekstrom, M. Nettles, and P. M. Shearer (2004), Characteristics of deep (≥13 km) Hawaiian earthquakes and Hawaiian earthquakes west of 155.55<sup>◦</sup>W, Geochem. Geophys. Geosyst., 5, Q04006, doi:10.1029/2003GC000618.

Wright, T. L., and F. W. Klein (2006), Deep magma transport at Kilauea volcano, Hawaii, Lithos, 87, 50–79.

Zecevic, M., L. De Barros, C. J. Bean, G. S. O’Brien, and F. Brenguier (2013), Investigating the source characteristics of long-period (LP) seismic events recorded on Piton de la Fournaise volcano, La Réunion, J. Volcanol. Geotherm. Res., 258, 1–11, doi:10.1016/j.jvolgeores.2013.04.009