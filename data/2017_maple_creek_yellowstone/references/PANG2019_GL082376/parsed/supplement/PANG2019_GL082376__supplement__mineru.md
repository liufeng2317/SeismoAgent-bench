# AGUPUBLICATIONS

Geophysical Research Letters

Supporting Information for

The 2017-2018 Maple Creek Earthquake Sequence in Yellowstone National Park, USA

Guanning Pang<sup>1\*</sup>, Keith D. Koper<sup>1</sup>, J. Mark Hale<sup>1</sup>, Relu Burlacu<sup>1</sup>, Jamie Farrell<sup>1</sup>, and Robert B. Smith<sup>1</sup>

<sup>1</sup>Dept. of Geology and Geophysics, University of Utah, Salt Lake City, UT 84112, USA.

\*Corresponding author: Guanning Pang (g.Pang@utah.edu)

## Contents of this file

Text S1 to S3 Figures S1 to S7 Tables S1 to S2

## Introduction

This document contains the description of the University of Utah Seismograph Stations (UUSS) data, the methodology used to select and calculate P- and S- differential travel times, and a description of the process used to estimate $\mathrm { V _ { P } / V _ { S } }$ from P- and Sdifferential times. It also has seven supplementary figures (S1–S7) and two tables (S1– S2).

Earthquakes in the Yellowstone region are routinely detected and located by the University of Utah Seismograph Stations (UUSS) using data recorded by five nearby regional seismic networks: MB (Montana Bureau of Mines and Geology/Montana Tech (MBMG, MT USA), 2001), PB (Plate Boundary Observatory), TA (IRIS Transportable Array, 2003), US (Albuquerque Seismological Laboratory (ASL)/USGS, 2003), and WY (University of Utah, 1984). The sampling rate for most instruments is 100 Hz, while a few is 40 Hz. UUSS seismic analysts manually pick arrival times of P- and S-waves for each event and determine hypocenters using HYPOINVERSE (Klein, 2002) with a 1-D velocity model (Table S1). Since 2010, UUSS has located an average of \~1,750 earthquakes per year in the Yellowstone region. The corresponding earthquake catalog is complete to about M<sub>C</sub> 1.2, where M<sub>C</sub> is the UUSS defined coda/duration magnitude scale for the Yellowstone region (Pechmann et al., 2006). The UUSS Yellowstone earthquake catalog is released in quarterly reports on the UUSS webpage (quake.utah.edu) and is

available from the Comprehensive Catalog (ComCat) of the Advanced National Seismic System (ANSS) (earthquake.usgs.gov/data/comcat).

## Text S1: Measurement of Differential Travel Times

We used a bispectrum cross-correlation package, BCSEIS (Du et al., 2004), to measure differential travel times from 24 local stations in the Yellowstone region and two nearby regional stations (Figure 1, yellow triangles). We imposed a time window that started 0.30–0.75 s before the picked P arrival and ended 1.2–3.0 s after, depending on the sample rate. For S waves, we used time windows that started 1.0–2.5 s before the pick and ended 3.0–7.5 s after the pick. If no picked S-wave time was available we used the theoretical arrival time as the reference time. For each windowed arrival, we applied a 10% width Hanning taper and a zero-phase, 2-pole Butterworth bandpass filter with corner frequencies of 1 and 10 Hz.

To obtain as many reliable differential travel times as possible, we applied bispectrum verification, which required the cross-correlation (CC) lag number to be within 2 sample points of the lag number obtained from the bispectrum method. We also used minimum CC coefficients to guide selection of the highest-quality differential travel times. For a given earthquake pair, we defined $\mathrm { C C } _ { \mathrm { m a x } }$ as the maximum CC coefficient from all available stations. $\mathrm { I f } \mathrm { C C } _ { \mathrm { m a x } } > 0 . 7 0$ , we accepted all the time delays for which CC $> 0 . 6 5 ; \mathrm { i f } 0 . 6 8 < \mathrm { C C } _ { \mathrm { m a x } } < 0 . 7 0$ , we accepted all time delays for which $\mathrm { C C } > 0 . 6 8 ; \mathrm { i f C C _ { \operatorname* { m a x } } }$ $< 0 . 6 8$ we rejected all the times from the event pair. A total of \~4.4 million differential travel times (27% S and 73% P) satisfied our criteria.

## Text S2: Estimation of V<sub>P</sub>/V<sub>S</sub> ratio from P and S differential travel time pairs

Lin and Shearer (2007) developed an approach to estimate the $\mathrm { V _ { P } / V _ { S } }$ ratio in the source region of an earthquake cluster based on the relative variation of cross-correlation derived P and S differential travel times. They show that under certain conditions the slope of a line relating pairs of demeaned P- and S- differential travel times is a direct estimate of the near-source $\mathrm { V _ { P } / V _ { S } }$ ratio: $( \delta t s ^ { i } - \ \bar { \delta t } s ) = ( V _ { P } / V _ { S } ) \ ( \delta t _ { P } { } ^ { i } - \ \bar { \delta t } _ { P } )$ , where $\delta t _ { P } { ^ i }$ and $\delta t _ { S } ^ { j }$ are the P- and S- differential times for single event pair in station $i ,$ and $\bar { \delta t } _ { P }$ and $\overline { { \delta } } t _ { S }$ are the median values of all differential times from all stations. Furthermore, instead of using least square fitting, they used a modified least square fitting approach to find the best-fitting line (Lin & Shearer, 2007). Using this approach, Lin and Shearer (2009) obtained a relatively low median $\mathrm { V _ { P } / V _ { S } }$ ratio of 1.67 for seismicity clusters in southern California and interpreted it as evidence of water-filled cracks in the earthquake source regions. Lin et al. (2015) applied the approach to earthquake clusters beneath the Kilauea volcano summit caldera in Hawaii and obtained $\mathrm { V _ { P } / V _ { S } }$ ratios of 1.41–1.85, with the lowest values interpreted as evidence for $\mathrm { C O } _ { 2 } { \cdot } \mathrm { f i l l e d }$ cracks and the highest values interpreted as evidence for partial melt.

## Text S3: Location Uncertainties from Bootstrapping

The key concept of bootstrapping is that the original data set is resampled to form a larger number of pseudo data sets. The pseudo data sets may contain a certain datum more than once while omitting other data (Tichelaar and Ruff, 1989). In our work, we require the resampled data set have the same size as the original data set. In GrowClust, the differential times are organized into arrays of length N, where N is the total number of combined P- and S- wave data. For each bootstrap iteration, GrowClust will randomly resample the differential time array with replacement and then invert it to generate a perturbed set of event locations. This procedure will be repeated B times (for relocation, normally B is 100) to generate a distribution of hypocenters for each event. Next, we estimate the uncertainties using the median absolute deviations (MAD) of the bootstrap distribution (Trugman and Shearer, 2017). A similar procedure is applied to PCA and the Vp/Vs ratio estimation. For PCA, we use 500 resamplings and for the Vp/Vs we use 200 resamplings.

![](mineru/Pang2019_MapleCreek_SI/images/53a87afade6902622e771fc587fb802bb310f652ea2033f1b135bc84e95fadf1.jpg)

![](mineru/Pang2019_MapleCreek_SI/images/018f03c1beb3e70e95b47c771cc72eedba9695def42b1cbfe72a46d1f4de0c9e.jpg)

(d)  
(e)  
![](mineru/Pang2019_MapleCreek_SI/images/ffacd6502c88cdb3699d8733f6662649651b0f459c38d50bb26d896f548760a2.jpg)

(c)  
![](mineru/Pang2019_MapleCreek_SI/images/d825f2fd1a539ff8543f182697c3291eb88ff3c5def0bf27e3a550796753460e.jpg)
Figure S1. (a) Earthquake magnitude (M<sub>C</sub>) as a function of time for the 2017–2018 Maple Creek sequence. Red dots represent earthquakes that occurred in 2017 and blue dots are used for earthquakes that occurred in 2018. (b) Cumulative frequency-magnitude curve for the earthquakes. The red triangle indicates the magnitude of completeness (M<sub>C</sub> 0.5) and the red line is the best-fitting Gutenberg-Richter relationship for M<sub>C</sub> 0.5–3.5. (c) Absolute locations using the same color scheme as in (a). The black star marks the largest earthquake and the green triangle is the seismic station closest to the sequence (WY.YMC). The background color is the P-velocity anomaly at 8 km below the sea level from Farrell et al. (2014). The black line is the surface rupture caused by 1959 Hebgen Lake earthquake (Johnson et al., 2018) (d) Absolute locations along the $\mathbf { A } { - } \mathbf { A } ^ { \prime }$ cross section. Depths are relative to sea level and the colors are the same as in (c). (e) Same as (d) but along the B-B’ cross section.

![](mineru/Pang2019_MapleCreek_SI/images/4b4e2d982865589124a41ef9cf04e86245715a3cda9ccc481ada44101a376525.jpg)
Figure S2. Positive Coulomb stress perturbation from Hebgen Lake earthquake (red star) and locations for the 1985–86 swarm (black), the 2010 Madison Plateau swarm (green), and the 2017–18 Maple Creek sequence (red). Cyan lines mark the 0.64 Ma Yellowstone caldera boundary and the red lines mark the 1959 Hebgen Lake surface rupture. Modified from Chang and Smith (2002).

![](mineru/Pang2019_MapleCreek_SI/images/5ee09d8fc907f82cfd1e8848c0401643035fb16ca561d06896290657631c9218.jpg)

(c)  
![](mineru/Pang2019_MapleCreek_SI/images/afeb3e96a2914f671a45380a68ce09fc9cf86518795f3d791b9e4b9766e22a30.jpg)

(b)  
![](mineru/Pang2019_MapleCreek_SI/images/0166f19203bd8dd7b81799375de19853a17f412e283d19068590c61faa0c5c82.jpg)

(d)  
![](mineru/Pang2019_MapleCreek_SI/images/d4374c13e354dd574a50ec4c991eb669a5fe68da5c626fde615a33f8505da370.jpg)
Figure S3. (a) Horizontal and (b) vertical errors for absolute locations in the UUSS catalog. (c) Horizontal and (d) vertical errors for double-difference relative relocations based on 100 bootstrap resamplings.

(a)  
![](mineru/Pang2019_MapleCreek_SI/images/d7953585bf9d50f0c071c01bcbb5c2092bd0ae08a53ec569ae2955a6bec80572.jpg)
Depth = 15 Strike = 62 ; 327 Rake = -151 ; -10 Dip = 81 ; 62 M\_ TOT= 4.42 Percent DC = 85 Percent CLVD = 15 Percent ISO = 0 Var. Red. = 78.9

![](mineru/Pang2019_MapleCreek_SI/images/786d67aabff6ef858cfe5d50c92d18b2e2759814277b4a3c2f8936cd8d04e728.jpg)

(b)  
![](mineru/Pang2019_MapleCreek_SI/images/232d691bd9beeac868ff101d555668f545103c807a2f50c949cc6bf78b92a79a.jpg)
Figure S4. Moment tensor solution for the largest earthquake in the 2017–2018 Maple Creek sequence $( \mathrm { M } _ { \mathrm { w } } 4 . 4$ on June 16, 2017). (a) Comparison of observed (black) and predicted (red dashed) waveforms. The optimal solution is shown on the right. (b) Depth sensitivity of the moment tensor inversion. The blue y-axis on the right marks the variance reduction (VR) and the red y-axis on the left is the residual divided by the double-couple percent in the solution.

![](mineru/Pang2019_MapleCreek_SI/images/3688a0bcdf26feaca11027e36a48bf226c298d3b1384ba1a1011cd6caf22d7ae.jpg)

(b)  
![](mineru/Pang2019_MapleCreek_SI/images/94cd49578f70f89db417b2e440a39b03195faab2aee7de0ea748ab98ab04b727.jpg)
Figure S5. (a) Time evolution of the 2017–2018 Maple Creek sequence. Circles represent earthquakes in 2017 and stars represent earthquakes in 2018. The horizontal color bar refers to events in 2017 and the vertical color bar refers to events in 2018. (b) Time evolution as a function of depth. (c) Time evolution as a function of distance from the two reference points. The solid blue line indicates a constant rate of 0.1 km/hr and the solid red line indicates a constant rate of 0.05 km/hr. The curve consisting of red pluses follows the homogeneous 3D diffusion model of Shapiro et al. (1997) with hydraulic diffusivity (D) of $0 . 4 \mathrm { m } ^ { 2 } / \mathrm { s }$ , and the faint curve consisting of black pluses corresponds to a D of $0 . 0 2 \mathrm { m } ^ { 2 } / \mathrm { s }$

(a)  
![](mineru/Pang2019_MapleCreek_SI/images/6be605455025376ef6091861de9b708c3b419183d36ece9ef479a682ac72c5d9.jpg)
(b)

(c)  
![](mineru/Pang2019_MapleCreek_SI/images/c13148364061093e2fce5794579ed6fd7823b5cc53811db06e16dfb7319733f3.jpg)
Figure S6. (a) Space-time evolution of Clusters n-II and n-III (circles and squares, respectively, Aug. 2017) and Cluster s-I (stars, July 2017). Each cluster has its own reference point for calculating times and distances: black rectangle (n-II), blue star (n-III), and red triangle (s-I). (b) Time evolution as a function of depth for s-I (left stars), n-II (middle circles), and n-III (right squares). (c) Time evolution as a function of distance for s-I (left stars), n-II (middle circles), and n-III (right squares). The solid blue lines show a rate of 0.1 km/hr, the solid red lines show a rate of 0.05 km/hr, and the solid green lines show a rate of 0.03 km/hr. The curve consisting of red pluses follows the homogeneous 3D diffusion model of Shapiro et al. (1997) with hydraulic diffusivity (D) of 1 $\mathrm { m } ^ { 2 } / \mathrm { s } ,$ and the faint curve consisting of black pluses corresponds to a D of $0 . 0 2 \mathrm { m } ^ { 2 } / \mathrm { s }$

![](mineru/Pang2019_MapleCreek_SI/images/cb0e2f006f9218e99ffdd2ff69621b58f4d5fca860e52193bc5a57d226c454a4.jpg)

![](mineru/Pang2019_MapleCreek_SI/images/31879eb2d6ecd2588d286a375da00a44ccbd57b5cb3035e03efde37c9b4ee048.jpg)
Figure S7. Earthquake divisions by origin time and location for time evolution characterization. The divisions are color matched with Figure 4.

<table><tr><td>Depth (km)</td><td> $V_P$ (km/sec)</td><td> $V_S$ (km/sec)</td></tr><tr><td>0.0</td><td>2.72</td><td>1.66</td></tr><tr><td>1.3</td><td>2.79</td><td>1.74</td></tr><tr><td>4.3</td><td>5.21</td><td>3.23</td></tr><tr><td>7.3</td><td>5.56</td><td>3.42</td></tr><tr><td>10.3</td><td>5.77</td><td>3.49</td></tr><tr><td>14.3</td><td>6.07</td><td>3.68</td></tr><tr><td>18.3</td><td>6.33</td><td>3.78</td></tr><tr><td>23.3</td><td>6.63</td><td>4.00</td></tr><tr><td>52.3</td><td>8.00</td><td>4.85</td></tr></table>

Table S1. 1-D velocity model used by UUSS to locate earthquakes in the Yellowstone region.

<table><tr><td></td><td>Strike (°)</td><td>Dip (°)</td><td>Planarity</td></tr><tr><td>Cluster n-I</td><td>96° ± 3°</td><td>77° ± 5°</td><td>0.89 ± 0.011</td></tr><tr><td>Cluster n-II</td><td>115° ± 2°</td><td>88° ± 3°</td><td>0.77 ± 0.012</td></tr><tr><td>Cluster n-III</td><td>108° ± 1°</td><td>90° ± 3°</td><td>0.78 ± 0.017</td></tr><tr><td>Cluster s-I</td><td>266° ± 1°</td><td>66° ± 1°</td><td>0.98 ± 0.002</td></tr><tr><td>Cluster s-II</td><td>106° ± 4°</td><td>46° ± 2°</td><td>0.85 ± 0.026</td></tr><tr><td>Cluster s-III</td><td>270° ± 1°</td><td>55° ± 1°</td><td>0.96 ± 0.002</td></tr><tr><td>Cluster s-VI</td><td>267° ± 1°</td><td>59° ± 1°</td><td>0.97 ± 0.005</td></tr><tr><td>Cluster s-V</td><td>84° ± 1°</td><td>87° ± 1°</td><td>0.99 ± 0.003</td></tr></table>

Table S2. Results from principal component analysis of the spatial covariance matrices of various earthquake clusters (Figure 2). The best-fitting plane in a least squares sense is that plane which is perpendicular to the smallest eigenvalue. Errors are derived from a bootstrap resampling process.