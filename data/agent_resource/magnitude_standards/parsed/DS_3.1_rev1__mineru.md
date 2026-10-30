<table><tr><td>Topic</td><td>Magnitude calibration formulas and tables, comments on their use and complementary data</td></tr><tr><td>Author</td><td>Peter Bormann (formerly GFZ German Research Centre for Geosciences, Potsdam, Telegrafenberg, D-14473 Potsdam, Germany; E-mail: pb65@gmx.net</td></tr><tr><td>Version</td><td>January 2012; DOI: 10.2312/GFZ.NMSOP-2_DS_3.1</td></tr></table>

## 1 Local magnitude Ml

The classical formula for determining the local magnitude Ml is, according to Richter (1935),

$$
\mathrm{Ml} = \log \mathrm{A} _ {\max} - \log \mathrm{A} _ {0}\tag{1}
$$

with $\mathbf { A } _ { \mathrm { m a x } }$ in mm of measured zero-to-peak trace amplitude in a Wood-Anderson seismogram. The respective corrections or calibration values –logA<sub>0</sub> are given in Table 1 as a function of epicentral distance ∆.

Table 1 The classical tabulated calibration function $\mathopen { } \mathclose \bgroup \left. - \mathrm { l o g A } _ { 0 } ( \Delta ) \aftergroup \egroup \right.$ for local magnitudes Ml according to Richter (1958). $\mathbf { A } _ { 0 }$ are the trace amplitudes in mm recorded by a Wood-Anderson Standard Torsion Seismometer from an earthquake of Ml = 0.

<table><tr><td>Δ (km)</td><td> $-\log A_0$ </td><td>Δ (km)</td><td> $-\log A_0$ </td><td>Δ (km)</td><td> $-\log A_0$ </td><td>Δ (km)</td><td> $-\log A_0$ </td></tr><tr><td>0</td><td>1.4</td><td>90</td><td>3.0</td><td>260</td><td>3.8</td><td>440</td><td>4.6</td></tr><tr><td>10</td><td>1.5</td><td>100</td><td>3.0</td><td>280</td><td>3.9</td><td>460</td><td>4.6</td></tr><tr><td>20</td><td>1.7</td><td>120</td><td>3.1</td><td>300</td><td>4.0</td><td>480</td><td>4.7</td></tr><tr><td>30</td><td>2.1</td><td>140</td><td>3.2</td><td>320</td><td>4.1</td><td>500</td><td>4.7</td></tr><tr><td>40</td><td>2.4</td><td>160</td><td>3.3</td><td>340</td><td>4.2</td><td>520</td><td>4.8</td></tr><tr><td>50</td><td>2.6</td><td>180</td><td>3.4</td><td>360</td><td>4.3</td><td>540</td><td>4.8</td></tr><tr><td>60</td><td>2.8</td><td>200</td><td>3.5</td><td>380</td><td>4.4</td><td>560</td><td>4.9</td></tr><tr><td>70</td><td>2.8</td><td>220</td><td>3.65</td><td>400</td><td>4.5</td><td>580</td><td>4.9</td></tr><tr><td>80</td><td>2.9</td><td>240</td><td>3.7</td><td>420</td><td>4.5</td><td>600</td><td>4.9</td></tr></table>

Different from the above, the IASPEI Working Group on Magnitude Measurement now recommends, as approved by the IASPEI Commission on Seismic Observation and Interpretation (CoSOI), the following standard formula for calculating Ml (quote from IASPEI, 2011, which uses the nomenclature ‘ML’ instead of ‘Ml’):

“For crustal earthquakes in regions with attenuative properties similar to those of Southern California, the proposed standard equation is

$$
M L = \log_ {1 0} (A) + 1. 1 1 \log_ {1 0} R + 0. 0 0 1 8 9 * R - 2. 0 9,\tag{2}
$$

where A = maximum trace amplitude in nm that is measured on output from a horizontalcomponent instrument that is filtered so that the response of the seismograph/filter system replicates that of a Wood-Anderson standard seismograph but with a static magnification of 1;

## R = hypocentral distance in km, typically less than 1000 km.

Equation (2) is an expansion of that of Hutton and Boore (1987) (see first equation in Table 2 below). The constant term in equation (2), -2.09, is based on an experimentally determined static magnification of the Wood-Anderson of 2080, rather than the theoretical magnification of 2800 that was specified by the seismograph´s manufacturer. The formulation of equation (2) reflects the intent of the Magnitude WG that reported ML amplitude data not be affected by uncertainty in the static magnification of the Wood-Anderson seismograph.

For seismographic stations containing two horizontal components, amplitudes are measured independently from each horizontal component, and each amplitude is treated as a single datum. There is no effort to measure the two observations at the same time, and there is no attempt to compute a vector average.

For crustal earthquakes in regions with attenuative properties that are different than those of coastal California, and for measuring magnitudes with vertical-component seismographs, the standard equation is of the form:

$$
M L = \log_ {1 0} (A) + C (R) + D,\tag{3}
$$

where A and R are as defined in equation (2), except that A may be measured from a verticalcomponent instrument, and where C(R) and D have been calibrated to adjust for the different regional attenuation and to adjust for any systematic differences between amplitudes measured on horizontal seismographs and those measured on vertical seismographs.”

Table 2 gives examples of regional Ml calibration functions from different countries and continents followed by explanatory comments. Many more Ml calibration functions, but also of other magnitude formulas used by different agencies in Europe, Tunesia, Israel, Iran, Mongolia and French Polynesia have been published in the EMSC-CSEM Newsletter of Nov. 15, 1999 (see http://www.emsc-csem.org/Documents/?d=newsl). It can also be downloaded via the list Download Programs & Files (see Overview on the NMSOP-2 front page).

Table 2 Regional calibration functions -log $\mathbf { A } _ { 0 }$ for Ml determinations. ∆ - epicentral distance and R - hypocentral ("slant") distance with $\mathbf { \bar { R } } = \surd ( \Delta ^ { 2 } + \mathbf { h } ^ { 2 } )$ , both in km ; h – hypocentral depth in km, T - period in s, Com. - recording component, S – station correction.

<table><tr><td>Region</td><td> $-\log A_0$ </td><td>Com.</td><td>Range (km)</td><td>Reference</td></tr><tr><td>Southern California</td><td>1.110 log (R/100) + 0.00189(R - 100) + 3.0</td><td>horiz.</td><td>10 ≤ R ≤ 700</td><td>Hutton&amp;Boore (1987) oWA</td></tr><tr><td>California</td><td>1.11 log (R) + 0.00189(R) + 0.591+ TP(n)×T(n,z) + S (see Comment 1.4)</td><td>horiz.</td><td>8 ≤ R ≤ 500</td><td>Uhrhammer et al. (2011); nWA but A in mm</td></tr><tr><td>Mexico, Baya Calif.</td><td>1,1319 log(R/100) + 0.0017 (R - 100) + 3.0</td><td rowspan="2">horiz.</td><td rowspan="2">0 &lt; R ≤ 400</td><td rowspan="2">Vidal&amp;Munguía (1999) csmWA</td></tr><tr><td>Mexico, Imp. Valley</td><td>1.0134 log(R/100) + 0.0025(R - 100) + 3.0</td></tr><tr><td>US Intermountain Belt (Utah)</td><td> $-\log A_0$ (Richter, 1958) + S</td><td>horiz. (arithm. mean)</td><td>Δ ≤ 600</td><td>Pechmann et al. (2007); oWA</td></tr><tr><td rowspan="2">Eastern N-America</td><td>1.55 log Δ - 0.22</td><td>horiz.</td><td>100 ≤ Δ ≤800</td><td rowspan="2">Kim (1998); oWA</td></tr><tr><td>1.45 log Δ + 0.11</td><td>vertic.</td><td>100≤ Δ ≤800</td></tr><tr><td rowspan="3">NW Turkey</td><td>log(R/17) + 0.00960(R-17) + 2 - S</td><td rowspan="3">horiz</td><td>5 ≤ R ≤ 62</td><td rowspan="3">Baumbach et al.(2003) oWA</td></tr><tr><td>log(R/62) + 0.00960(R-62) + 2.95 - S</td><td rowspan="2">62≤ R ≤110</td></tr><tr><td>1,58 log (R/100) + 3.0; for ML ≤ 3.7</td></tr><tr><td rowspan="2">Greece</td><td>2.00 log (R/100) + 3.0; for ML &gt; 3.7</td><td rowspan="2">horiz.</td><td rowspan="2">100≤ Δ ≤800</td><td rowspan="2">Kiratzi&amp;Papazachos (1984); oWA</td></tr><tr><td>1.6627 log Δ + 0.0008 Δ - 0.433</td></tr><tr><td>Albania</td><td>0.83 log R + (0.0017/T) (R - 100) + 1.41</td><td>horiz</td><td>10 ≤Δ ≤ 600</td><td>Muco&amp;Minga (1991) oWA</td></tr><tr><td>Central Europe</td><td>1.11 lg R + 0.95 R/1000 + 0.69</td><td>vertic.</td><td>100 ≤Δ ≤ 650</td><td>Wahlström&amp;Strauch (1984); oWA</td></tr><tr><td>SW Germany(Baden-Würtemberg)</td><td>0.91 log R + 0.00087 R + 1.010</td><td>vertic.</td><td>10 &lt; R &lt; 1000</td><td>Stange (2006) oWA</td></tr><tr><td>Norway/Fennoskan.</td><td>0.776 log(R/17) + 0.000902 (R - 17) + 2.0</td><td>vertic.</td><td>0 &lt; R ≤ 1500</td><td>Alsaker et al. (1991) nWA yet A in mm</td></tr><tr><td>Tanzania</td><td>1.075 log R + 0.00061R - 1.89 + S</td><td>horiz.</td><td>0 &lt; R ≤ 1000</td><td>Langston et al. (1998)?oWA?</td></tr><tr><td>South Africa</td><td>1.10 log Δ + 0.0013 Δ + 0.7</td><td>vertic.</td><td>0 &lt; R &lt; 1000</td><td>Sauder et al. (2011) nWA with A in nm</td></tr><tr><td>South Australia</td><td></td><td>vertic.</td><td>40 &lt; Δ &lt; 700</td><td>Greenhalgh&amp;Singh (1986);oWA</td></tr></table>

Comment 1.1: Pre-1990 regional calibration relationships in Table 2 were derived by assuming a static magnification of 2800 for the Wood-Anderson seismometer, whereas most of the more recent calibration formulas assumed the empirically derived average value of 2080 according to Uhrhammer and Collins (1990), as does the newly proposed IASPEI standard formula (2). For the response function and poles and zeros of this revised Wood-Anderson standard response see Figure 1 and Table 1 in IS 3.3. Accordingly, one might expect that reducing the constants in the older Ml formulas by 0.129 = log(2800/2080) would yield magnitude values that are compatible with the IASPEI (2011) standard formula und most of the post-1990 Ml formulas. However, the re-calibration by Uhrhammer and Collins yielded also another damping factor, namely 0.7 instead of 0.8. (see Table 1 in IS 3.3). With this, the difference between the old and new Ml relationships becomes slightly frequencydependent, as mentioned already by Kim (1998). According to D. Bindi (personal communication 2011) this difference is minimum at the response corner frequency of 1.28 Hz, 0.07 m.u. at 1 Hz, 0.08 m.u. at 0.8 Hz and 2 Hz, 0.11 m.u. at 0.5 and 3 Hz and 0.13 m.u. at < 0.12 Hz and > 8 Hz.

Formulas in Table 2 that have been derived assuming the old WA response are commented in the Reference column by oWA, those, which accounted only for the constant difference in static response by cdWA, but those derived by using the new WA response by nWA. While the difference plays no role as long as the amplitudes are measured on records of the original WA seismographs it has to be taken into account, also in its frequency dependence, when producing synthetic WA seismograms. It is, therefore, also not fully correct to follow the approaches by Kanamori et al. (1993) and Pechmann et al. (2007). They used the nominal WA gain of 2800 to construct the synthetic WA seismograms and then accounted for the (assumed constant) gain difference between the synthetic and actual WA records via the station corrections. Station corrections should not only serve a formal purpose, namely to reduce the data scatter and thus improve the precision of magnitude estimates but also have a geophysical meaning which relates to the recording site itself and not to an instrumental bias.

If the procedure used by the authors of formulas presented in Table 2 is not obvious to us, we put a question mark (?) in front. Then consultation of the original publication and/or of the author is recommended.

Comment 1.2: Calibration of alternative regional magnitude scales to the standard formula should be made in such a way, that at some specific distance ≤100 km identical amplitude values inserted in both the standard formula and the alternative regional Ml formula yield the same magnitude value. Fig. 3.12 in Chapter 3 shows such a mutual scaling of different scales around 50 km epicentral distance. However, for larger distances, due to differences in regional attenuation, the magnitudes resulting from identical amplitude values but using different regional calibration formulas may differ by about one magnitude unit at distances larger than 800 km when comparing, e.g., the standard formula eq. (2) for Southern California (young tectonic region with high heat flow) with the formula by Saunders et al. (2011) for South Africa (stable old continental platform area, low heat flow).

To allow a more meaningful comparison of earthquakes in regions having very different attenuation of waves already within the first 100 km, Hutton and Boore (1987) recommend even a scaling at 17 km hypocentral distance. There, in agreement with the original definition of magnitude in southern California Ml = 3 should correspond to 10 mm of motion on a Wood-Anderson instrument, rather than 1 mm of motion at 100 km (as for Table 1). This scaling recommendation was taken for the near range NW Turkey formula by Baumbach et al. (2003) and by Langston et al. (1998) in Tansania (see Table 2). Yet, the majority of formulas in Table 2 have been scaled to the yield Ml = 3 for measured 1 mm trace motion on a WA record at R = 100 km.

Comment 1.3: Station corrections S for Ml, based on short-period amplitude measurements, are rather large. They typically range between about ±0.5 m.u., are usually larger for horizontal than for vertical component recordings, negative for stations on sediments or weathered rocks and near zero or positive for station sites on hard rock (e.g., Baumbach et al., 2003; Hutton and Boore, 1987; Saunders et al. (2011); Strauch and Wylegalla, 1989; Vidal and Munguía, 1999).

Comment 1.4: The first part of the Uhrhammer et al. (2011) calibration function for all California is identical with the expanded Hutton and Boore (1987) relationship for Southern California. However, after several inversions, these authors found out that the best leastsquare fit to all California data was achieved by a linear combination of the Southern California relationship with a sixth order Chebychev polynomial $\mathrm { T P ( n ) } { \times } \mathrm { T } ( \mathrm { n } , \mathrm { z } )$ , where n is summed from 1 to 6 with different coefficients TP(1) to TP(6), T(n, z) = cos[n × acos(z)] and z being the scale transformation of the epicentral distances R. For the given data the relationship z(R) = 1.11366 log(R) - 2.00574 transforms R in the range 8 km $\le \mathsf { R } \le 5 0 0$ km to $- 1 \leq \mathbf { z } \leq \mathbf { \alpha } + 1$ . The new -logA<sub>0</sub>(R) relationship by Uhrhammer et al. (2011) was found to be robust with respect to constraints on the derived stations corrections and ultimately reduced to variance of the data by 50%. It should also be noted that the authors apply a pre-filter to reduce long-period noise.

## 2 Classical and new standard surface wave magnitudes Ms, Ms\_20 and Ms\_BB

Gutenberg (1945a) published the following relationship for calculating the surface-wave magnitude Ms based on measurements of the “absolute” maximum horizontal-component displacement amplitude in units of µm at periods “around 20 s”:

$$
\mathrm{Ms} = \log \mathrm{A} _ {\mathrm{Hmax}} + 1. 6 5 6 \log \Delta + 1. 8 1 8.\tag{4}
$$

Equation (4) is applicable at epicentral distances $\Delta$ between about $2 0 ^ { \circ }$ and $1 3 0 ^ { \circ }$ . Richter (1958) published tabulated Gutenberg Ms calibration values $\sigma _ { S } ( \Delta )$ . They allow to use the Gutenberg surface-wave magnitude formula in its general form $\begin{array} { r } { \mathbf { M s } = \log \mathbf { \delta A _ { H m a x } } \left( \Delta \right) + \boldsymbol { \sigma } _ { \mathrm { { S } } } ( \Delta ) } \end{array}$ up to $1 8 0 ^ { \circ }$ (see Table 3).

Table 3 . Tabulated Ms calibration values $\sigma _ { S } ( \Delta )$ according to Richter (1958) when $\mathbf { A } _ { \mathrm { H m a x } }$ is measured in µm.

<table><tr><td>Δ (degrees)</td><td> $\sigma_S (\Delta)$ </td><td>Δ (degrees)</td><td> $\sigma_S (\Delta)$ </td><td>Δ (degrees)</td><td> $\sigma_S (\Delta)$ </td></tr><tr><td>20</td><td>4.0</td><td>60</td><td>4.8</td><td>120</td><td>5.3</td></tr><tr><td>25</td><td>4.1</td><td>70</td><td>4.9</td><td>140</td><td>5.3</td></tr><tr><td>30</td><td>4.3</td><td>80</td><td>5.0</td><td>160</td><td>5.35</td></tr><tr><td>40</td><td>4.5</td><td>90</td><td>5.05</td><td>170</td><td>5.3</td></tr><tr><td>45</td><td>4.6</td><td>100</td><td>5.1</td><td>180</td><td>5.0</td></tr><tr><td>50</td><td>4.6</td><td>110</td><td>5.2</td><td></td><td></td></tr></table>

Comments 2.1: When rounded to the nearest tenth magnitude unit the values in Table 3 agree up to $1 3 0 ^ { \circ }$ with those calculated by formula (4). However, for larger distances, formula (4) yields magnitudes that are larger than those of Table 3 by 0.05 to 0.55 m.u. Reason: this simple average least-square data fitting relationship accounts only for the decay of amplitudes with distance but not for the energy focusing towards the antipodes, which is more correctly reflected by the average empirical calibration values.

Comment 2.2: Gutenberg calculated $\mathbf { A } _ { \mathrm { H m a x } }$ from the “vectorially” combined maximum amplitudes measured in the N-S and E-W component. These maxima may occur at different times and relate to different (Love and Rayleigh) surface waves. This differs from a true horizontal component vector amplitude maximum, which requires both components to be measured at the same time (within about a quarter of a period). Therefore, classical Gutenberg Ms values tends to be on average somewhat larger than Ms based on true vector sum A<sub>Hmax</sub> (Figure 1 and comments by Gellert and Kanamori, 1977; Abe and Kanamori, 1980; Lienkaemper, 1984).

![](images/a211a96dfdc68af57e470bb78acde3426126874c886da0d7960297fa0efdabb6.jpg)  
Figure 1 The difference between Ms derived from these records according to the Gutenberg “vectorial” combination $\mathrm { A _ { H m a x } = ( L R _ { E } } ^ { 2 } + \mathrm { L Q _ { N } } ^ { 2 } ) ^ { 1 / 2 }$ and the true $\mathbf { A } _ { \mathrm { H m a x } }$ of LR is +0.12 m.u. This is about the largest difference possible (0.15 m.u.) and depends on the BAZ (here 85°).

Comment 2.3: Gutenberg himself did not write in his notebooks, at which period he had measured amplitude A, because he had defined his Ms scale for “periods of about $2 0 ~ \mathrm { { s } } ^ { \prime \prime }$ . Yet, comparison with the original bulletins also of other stations used by Gutenberg as data sources for calculating the Gutenberg-Richter $\mathbf { M } _ { \mathrm { G R } }$ magnitudes in “Seismicity of the Earth” (Gutenberg and Richter, 1954) showed that periods as low as 12 s and as high as 23 s were sometimes used, with values outside of the period range 18 s to 22 s not being rare (Abe, 1981; Lienkaemper, 1984).

Another surface-wave calibration function has been published by Vanĕk et al. (1962) and Karnik et al. (1962). It has to be used for true (within half a period in the N-S and E-W component) vectorially combined readings of $( \mathrm { A _ { H } / T }$ )max in the distance range $1 ^ { \circ } < \Delta < 1 6 0 ^ { \circ }$ at periods between $2 \mathrm { ~ s ~ } { < } \mathrm { T } < 3 0 \mathrm { ~ s ~ }$ . This formula, which yields in fact a broadband surfacewave magnitude estimate, has been adopted by IASPEI in 1967 as standard formula for Ms determination. It reads:

$$
\mathrm{Ms} = \log (\mathrm {A_ {H} /T}) _ {\max} + 1. 6 6 \log \Delta + 3. 3.\tag{5}
$$

Tabulated average calibration values, to which formula (5) had been fitted, were published by Kondorskaya et al. (1981) for the distance range $1 ^ { \circ }$ to $1 8 0 ^ { \circ }$ (see Table 4).

Table 4 Ms magnitude calibration values $\sigma _ { S } ( \Delta )$ (according to Kondorskaya et al., 1981) for true vectorially combined horizontal component surface-wave displacement amplitudes (in µm) from shallow earthquakes $\left( \mathrm { h } \leq 6 0 \right)$ km), which relate to the largest ratio $( \mathbf { A _ { H } } / \mathbf { T } ) _ { \operatorname* { m a x } }$ in the surface-wave group in a wide range of periods between $2 \mathrm { s } < \mathrm { T } < 3 0 \mathrm { s }$

<table><tr><td> $\Delta^{\circ}$ </td><td> $0^{\circ}$ </td><td> $1^{\circ}$ </td><td> $2^{\circ}$ </td><td> $3^{\circ}$ </td><td> $4^{\circ}$ </td><td> $5^{\circ}$ </td><td> $6^{\circ}$ </td><td> $7^{\circ}$ </td><td> $8^{\circ}$ </td><td> $9^{\circ}$ </td></tr><tr><td> $0^{\circ}$ </td><td></td><td>3.30</td><td>3.80</td><td>4.09</td><td>4.30</td><td>4.46</td><td>4.59</td><td>4.70</td><td>4.80</td><td>4.88</td></tr><tr><td> $10^{\circ}$ </td><td>4.96</td><td>5.03</td><td>5.09</td><td>5.15</td><td>5.20</td><td>5.25</td><td>5.29</td><td>5.34</td><td>5.38</td><td>5.42</td></tr><tr><td> $20^{\circ}$ </td><td>5.46</td><td>5.50</td><td>5.53</td><td>5.56</td><td>5.59</td><td>5.62</td><td>5.65</td><td>5.68</td><td>5.71</td><td>5.73</td></tr><tr><td> $30^{\circ}$ </td><td>5.75</td><td>5.78</td><td>5.80</td><td>5.82</td><td>5.84</td><td>5.86</td><td>5.88</td><td>5.90</td><td>5.92</td><td>5.94</td></tr><tr><td> $40^{\circ}$ </td><td>5.96</td><td>5.98</td><td>5.99</td><td>6.01</td><td>6.03</td><td>6.04</td><td>6.06</td><td>6.07</td><td>6.09</td><td>6.10</td></tr><tr><td> $50^{\circ}$ </td><td>6.12</td><td>6.13</td><td>6.14</td><td>6.16</td><td>6.17</td><td>6.18</td><td>6.20</td><td>6.21</td><td>6.22</td><td>6.24</td></tr><tr><td> $60^{\circ}$ </td><td>6.25</td><td>6.26</td><td>6.27</td><td>6.28</td><td>6.30</td><td>6.31</td><td>6.32</td><td>6.33</td><td>6.34</td><td>6.35</td></tr><tr><td> $70^{\circ}$ </td><td>6.36</td><td>6.37</td><td>6.38</td><td>6.39</td><td>6.40</td><td>6.41</td><td>6.42</td><td>6.43</td><td>6.44</td><td>6.45</td></tr><tr><td> $80^{\circ}$ </td><td>6.46</td><td>6.47</td><td>6.48</td><td>6.49</td><td>6.49</td><td>6.50</td><td>6.51</td><td>6.52</td><td>6.53</td><td>6.54</td></tr><tr><td> $90^{\circ}$ </td><td>6.55</td><td>6.55</td><td>6.56</td><td>6.57</td><td>6.58</td><td>6.58</td><td>6.59</td><td>6.60</td><td>6.61</td><td>6.61</td></tr><tr><td> $100^{\circ}$ </td><td>6.62</td><td>6.63</td><td>6.64</td><td>6.64</td><td>6.65</td><td>6.66</td><td>6.66</td><td>6.67</td><td>6.68</td><td>6.69</td></tr><tr><td> $110^{\circ}$ </td><td>6.69</td><td>6.70</td><td>6.70</td><td>6.71</td><td>6.72</td><td>6.72</td><td>6.73</td><td>6.74</td><td>6.74</td><td>6.75</td></tr><tr><td> $120^{\circ}$ </td><td>6.75</td><td>6.76</td><td>6.76</td><td>6.76</td><td>6.77</td><td>6.77</td><td>6.78</td><td>6.78</td><td>6.78</td><td>6.79</td></tr><tr><td> $130^{\circ}$ </td><td>6.79</td><td>6.79</td><td>6.80</td><td>6.80</td><td>6.80</td><td>6.81</td><td>6.81</td><td>6.81</td><td>6.81</td><td>6.81</td></tr><tr><td> $140^{\circ}$ </td><td>6.82</td><td>6.82</td><td>6.82</td><td>6.82</td><td>6.83</td><td>6.83</td><td>6.83</td><td>6.83</td><td>6.83</td><td>6.83</td></tr><tr><td> $150^{\circ}$ </td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td><td>6.84</td></tr><tr><td> $160^{\circ}$ </td><td>6.84</td><td>6.84</td><td>6.83</td><td>6.83</td><td>6.83</td><td>6.82</td><td>6.82</td><td>6.82</td><td>6.82</td><td>6.82</td></tr><tr><td> $170^{\circ}$ </td><td>6.81</td><td>6.81</td><td>6.80</td><td>6.79</td><td>6.77</td><td>6.74</td><td>6.71</td><td>6.69</td><td>6.64</td><td>6.59</td></tr><tr><td> $180^{\circ}$ </td><td>6.49</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

Comment 2.3: The calibration values in Table 4 agree at epicentral distances between $1 ^ { \circ }$ and $1 4 0 ^ { \circ }$ within 0.05 magnitude units with the values calculated from the calibration term in the Prague-Moscow surface-wave magnitude formula (5). For larger distances, however, this formula overestimates the magnitude between 0.05 and 0.55 (at 180°) m.u., for the same

reason as the Gutenberg (1945a) formula (4). Therefore, preference should be given to the use of the tabulated values, at least for distances ${ > } 1 4 0 ^ { \circ }$

Comment 2.4: The calibration values in Table 4 have - since the 1960s - been used at the basic seismic stations of the former Soviet Union (USSR) and its follow-up Commenwealth of Independent States (CIS) countries for Ms determination from both horizontal and vertical component readings. The latter usually relate to the Airy phase of Rayleigh waves $\mathrm { ( R _ { m a x } }$ , see section 2.3 in Chapter 2). Table 5 gives the time difference between $\mathrm { R } _ { \mathrm { m a x } }$ and the P wave as a function of distance. The good agreement between vertical and horizontal component Ms determinations has also been confirmed by Hunter (1972). Therefore, from May 1975 onwards, also the USGS decided to calculate their Ms exclusively from vertical component reading using formula (5)..

Table 5 Approximate time interval $\left( \mathrm { { t } _ { R m a x } \cdot \mathrm { { t } _ { P } } } \right)$ between the arrival of the maximum Rayleigh wave amplitude and the first onset of P waves as a function of ∆ according to Archangelskaya (1959) and Gorbunova and Kondorskaya (1977) (copied from Willmore, 1979).

<table><tr><td> $\Delta^{\circ}$ </td><td> $t_{Rmax} - t_P$ (min)</td><td> $\Delta^{\circ}$ </td><td> $t_{Rmax} - t_P$ (min)</td><td> $\Delta^{\circ}$ </td><td> $t_{Rmax} - t_P$ (min)</td></tr><tr><td>10</td><td>4-5</td><td>55</td><td>26</td><td>100</td><td>45-46</td></tr><tr><td>15</td><td>6-8</td><td>60</td><td>28-29</td><td>105</td><td>47-48</td></tr><tr><td>20</td><td>9-10</td><td>65</td><td>31</td><td>110</td><td>48-50</td></tr><tr><td>25</td><td>10-12</td><td>70</td><td>33</td><td>115</td><td>53</td></tr><tr><td>30</td><td>13-14</td><td>75</td><td>35</td><td>120</td><td>55</td></tr><tr><td>35</td><td>15-16</td><td>80</td><td>37</td><td>125</td><td>57</td></tr><tr><td>40</td><td>18-19</td><td>85</td><td>39-40</td><td>130</td><td>60</td></tr><tr><td>45</td><td>21</td><td>90</td><td>42</td><td>140</td><td>64</td></tr><tr><td>50</td><td>24</td><td>95</td><td>43</td><td>150</td><td>70</td></tr></table>

Table 6 summarizes the distance-dependent prevailing period ranges at which Ms according to formula (5) should be calculated. Note that already in Willmore (1979) it is recommended that: “When the period differs significantly from the values in Table 3.2.2.1 (here Table 6), it may be advisable not to use the data for magnitude determination.” This, however, is permanently done when measuring the narrowband spectral surface-wave Ms\_20 (see formula (7)).

Table 6 Distance-dependent prevailing period ranges at which broadband Ms should be measured (according to Vanĕk et al. (1962), Karnik et al. (1962) and Willmore (1979). With currently available very broadband velocity seismographs Vmax may occasionally be observed at even longer period periods up to about 60 s.

<table><tr><td> $\Delta^{\circ}$ </td><td>T in s</td><td> $\Delta^{\circ}$ </td><td>T in s</td><td> $\Delta^{\circ}$ </td><td>T in s</td><td> $\Delta^{\circ}$ </td><td>T in s</td></tr><tr><td>1</td><td>3-5</td><td>10</td><td>7-10</td><td>40</td><td>12-18</td><td>90</td><td>16-22</td></tr><tr><td>2</td><td>4-6</td><td>15</td><td>8-15</td><td>50</td><td>12-20</td><td>100</td><td>16-25</td></tr><tr><td>4</td><td>5-7</td><td>20</td><td>9-14</td><td>60</td><td>14-20</td><td>120</td><td>16-25</td></tr><tr><td>6</td><td>5-8</td><td>25</td><td>9-16</td><td>70</td><td>14-22</td><td>140</td><td>18-25</td></tr><tr><td>8</td><td>6-9</td><td>30</td><td>10-16</td><td>80</td><td>16-22</td><td>160</td><td>18-25</td></tr></table>

Comment 2.5: The periods at which $\mathrm { R } _ { \mathrm { m a x } }$ occurs depend on epicentral distance, crust and upper mantle structure along the travel path and the earthquake magnitude. Accordingly, the period of $\mathrm { R } _ { \mathrm { m a x } }$ may vary in a wide range of periods between some 2 and ${ < } 6 0 ~ \mathrm { s }$ (see Figures 7 and 8 in Bormann et al., 2009 and related figures in Chapter 3 of this Manual). This notwithstanding, measuring the ratio $\left( \mathbf { A } / \mathrm { T } \right) _ { \mathrm { m a x } }$ yields rather stable Ms determinations (Soloviev, 1955). This has been confirmed recently by Bormann et al. (2009) down to localregional distances and periods as short as 2 to 5 s for dominatingly continental travel paths. For chiefly oceanic paths this still has to be proved (or disproved), as well as the distancedependent period-ranges at which Rmax is observed. This, however, might be more difficult because of the lack of regional seismic networks in ocean areas. For larger magnitudes and epicentral distances, however, the path-dependent variability of periods is much reduced (see Figures 7 and 8 in Bormann et al. (2009).

Comment 2.6: Because of the above, the Prague-Moscow formula (6) is now recommended, with slight modification, by IASPEI (2011) for calculating the new standard broadband surface-wave magnitude Ms\_BB (see IS 3.3):

$$
\mathbf {M} \mathbf {s \_ B} \mathbf {B} = \log_ {1 0} (\mathbf {V} _ {\max} / 2 \pi) + \mathbf {1 . 6 6} \log_ {1 0} \Delta + \mathbf {0 . 3},\tag{6}
$$

where: $\mathrm { \Delta V _ { m a x } = \mathrm { g r o u n d } }$ velocity in nm/s is associated with the maximum trace-amplitude in the surface-wave train, as recorded on a vertical-component seismogram that is proportional to velocity;

T, the period of the surface-wave, should satisfy the condition $\mathbf { 3 \ s < T < 6 0 \ s }$ ;

∆ = epicentral distance in degrees, with (6) being applicable in the range $2 ^ { \circ } \leq \Delta \leq 1 6 0 ^ { \circ }$ ;

the focal depth h being less than 60 km;

and the term $\log _ { 1 0 } ( \mathrm { V _ { \mathrm { m a x } } } / 2 \pi )$ replaces the $\log _ { 1 0 } ( \mathrm { A } / \mathrm { T } ) _ { \mathrm { m a x } }$ term of the original formula (5).

The same calibration terms as in formula (6) is used for the other IASPEI (2011) standard surface-wave magnitude Ms\_20, which is identical with the NEIC/PDE Ms:

$$
\mathbf {M} \mathbf {s \_ 2 0} = \log_ {1 0} (\mathbf {A} / \mathbf {T}) + \mathbf {1 . 6 6 l o g} _ {1 0} \Delta + \mathbf {0 . 3},\tag{7}
$$

where: A = vertical-component ground displacement in nm measured from the maximum surface-wave trace-amplitude having a period between 18 s and 22 s on a simulated World-Wide Standardized Seismograph Network (WWSSN) long-period seismograph record, with A being determined by dividing the maximum trace amplitude by the magnification of the simulated WWSSN-LP response at period T, and ∆ = epicentral distance in degrees in the range $2 0 ^ { \circ } \leq \Delta \leq 1 6 0 ^ { \circ }$

Comment 2.7: Theoretically, for periods T = 20 s, the IASPEI standard formula (5) for Ms is expected to yield magnitude values that are 0.18 m.u. larger than those derived from the Gutenberg formula (4). This, however, is not confirmed by empirical testing (see Lienkaemper, 1984) and partially due to the fact that Gutenberg did not measure the true maximum vector amplitude (see Comment 2.2).

For more detailed discussion and figures on the relationship between Ms\_20 and Ms\_BB see Chapter 3 and Bormann et al. (2009).

## 3 Classical and new standard body-wave magnitudes mB and mb

Gutenberg (1945b and c) developed a magnitude formula for teleseismic body waves P, PP and S. He used it in the wide period range between about 2 s and 20 s (Abe, 1981 and 1984; Abe and Kanamori, 1980). The formula reads:

$$
\mathrm{mB} = \log (\mathrm{A} / \mathrm{T}) _ {\max} + \mathrm{Q} (\Delta , \mathrm{h}).\tag{8}
$$

Thus, mB is in fact a medium-period body-wave broadband magnitude. Gutenberg and Richter (1956) published for the three types of body waves diagrams of Q values as a function of ∆ and source depth h (Figures 1a-c).

REVISED VALUES OF Q FOR PZ1955  
![](images/431baca12000246289a30e7300572a26ff2a38befbbb0758197b8bb9503275d0.jpg)  
Figure 1a

REVISED VALUES OFQFOR PPZ 1955  
![](images/fa304e181086e3bb20f8ee69d88609b6fe67d5da66dc2e214a5083917ba9577f.jpg)  
Figure 1b

REVISED VALUES OF Q FOR SH 1955  
![](images/b67c33153b93aa1d049fefcef10dd6f96657f6efbba99a17676690292f20d176.jpg)  
Figure 1c

Gutenberg and Richter (1956) published also a table of Q(∆) values for P, PP and S waves in vertical $( \mathrm {  ~ V ~ } = \mathrm {  ~ Z ) ~ }$ and horizontal (H; vectorially-combined) components for shallow earthquakes (Table 7). All G-R Q values are valid when A is given in µm $( 1 0 ^ { - 6 } ~ \mathrm { m } )$ . If A is measured in nm $\left( { { 1 0 } ^ { - 9 } } { \mathrm { ~ m } } \right)$ , as now common in modern analysis programs for processing data with high dynamic range and resolution, the Q values have to be reduced by -3.

Table 7 Values of Q(∆) for ${ \mathrm { P } } ,$ PP and S waves for shallow shocks (h ≈ 15 km) according to Gutenberg and Richter (1956) if the ground amplitude is given in µm.

<table><tr><td> $\Delta^{\circ}$ </td><td>PV</td><td>PH</td><td>PPV</td><td>PPH</td><td>SH</td><td> $\Delta^{\circ}$ </td><td>PV</td><td>PH</td><td>PPV</td><td>PPH</td><td>SH</td><td> $\Delta^{\circ}$ </td><td>PV</td><td>PH</td><td>PPV</td><td>PPH</td><td>SH</td></tr><tr><td>16</td><td>5.9</td><td>6.0</td><td></td><td></td><td>7.2</td><td>56</td><td>6.8</td><td>7.1</td><td>6.9</td><td>7.0</td><td>6.6</td><td>96</td><td>7.3</td><td>7.6</td><td>7.2</td><td>7.4</td><td>7.1</td></tr><tr><td>17</td><td>5.9</td><td>6.0</td><td></td><td></td><td>6.8</td><td>57</td><td>6.8</td><td>7.1</td><td>6.9</td><td>7.0</td><td>6.6</td><td>97</td><td>7.4</td><td>7.8</td><td>7.2</td><td>7.4</td><td>7.2</td></tr><tr><td>18</td><td>5.9</td><td>6.0</td><td></td><td></td><td>6.2</td><td>58</td><td>6.8</td><td>7.1</td><td>7.0</td><td>7.1</td><td>6.6</td><td>98</td><td>7.5</td><td>7.8</td><td>7.2</td><td>7.4</td><td>7.3</td></tr><tr><td>19</td><td>6.0</td><td>6.1</td><td></td><td></td><td>5.8</td><td>59</td><td>6.8</td><td>7.1</td><td>7.0</td><td>7.2</td><td>6.6</td><td>99</td><td>7.5</td><td>7.8</td><td>7.2</td><td>7.4</td><td>7.3</td></tr><tr><td>20</td><td>6.0</td><td>6.1</td><td></td><td></td><td>5.8</td><td>60</td><td>6.8</td><td>7.1</td><td>7.1</td><td>7.3</td><td>6.6</td><td>100</td><td>7.4</td><td>7.7</td><td>7.2</td><td>7.4</td><td>7.4</td></tr><tr><td>21</td><td>6.1</td><td>6.2</td><td></td><td></td><td>6.0</td><td>61</td><td>6.9</td><td>7.2</td><td>7.2</td><td>7.4</td><td>6.7</td><td>101</td><td>7.3</td><td>7.6</td><td>7.2</td><td>7.4</td><td>7.4</td></tr><tr><td>22</td><td>6.2</td><td>6.3</td><td></td><td></td><td>6.2</td><td>62</td><td>7.0</td><td>7.3</td><td>7.3</td><td>7.4</td><td>6.7</td><td>102</td><td>7.4</td><td>7.7</td><td>7.2</td><td>7.4</td><td>7.4</td></tr><tr><td>23</td><td>6.3</td><td>6.4</td><td></td><td></td><td>6.2</td><td>63</td><td>6.9</td><td>7.3</td><td>7.3</td><td>7.4</td><td>6.7</td><td>103</td><td>7.5</td><td>7.9</td><td>7.2</td><td>7.4</td><td>7.3</td></tr><tr><td>24</td><td>6.3</td><td>6.5</td><td></td><td></td><td>6.2</td><td>64</td><td>7.0</td><td>7.3</td><td>7.3</td><td>7.5</td><td>6.8</td><td>104</td><td>7.6</td><td>7.9</td><td>7.3</td><td>7.5</td><td>7.3</td></tr><tr><td>25</td><td>6.5</td><td>6.6</td><td></td><td></td><td>6.2</td><td>65</td><td>7.0</td><td>7.4</td><td>7.3</td><td>7.5</td><td>6.9</td><td>105</td><td>7.7</td><td>8.1</td><td>7.3</td><td>7.5</td><td>7.2</td></tr><tr><td>26</td><td>6.4</td><td>6.6</td><td></td><td></td><td>6.2</td><td>66</td><td>7.0</td><td>7.4</td><td>7.3</td><td>7.4</td><td>6.9</td><td>106</td><td>7.8</td><td>8.2</td><td>7.4</td><td>7.6</td><td>7.2</td></tr><tr><td>27</td><td>6.5</td><td>6.7</td><td></td><td></td><td>6.3</td><td>67</td><td>7.0</td><td>7.4</td><td>7.2</td><td>7.4</td><td>6.9</td><td>107</td><td>7.9</td><td>8.3</td><td>7.4</td><td>7.6</td><td>7.2</td></tr><tr><td>28</td><td>6.6</td><td>6.7</td><td></td><td></td><td>6.3</td><td>68</td><td>7.0</td><td>7.4</td><td>7.1</td><td>7.3</td><td>6.9</td><td>108</td><td>7.9</td><td>8.3</td><td>7.4</td><td>7.6</td><td>7.2</td></tr><tr><td>29</td><td>6.6</td><td>6.7</td><td></td><td></td><td>6.3</td><td>69</td><td>7.0</td><td>7.4</td><td>7.0</td><td>7.2</td><td>6.9</td><td>109</td><td>8.0</td><td>8.4</td><td>7.4</td><td>7.6</td><td>7.2</td></tr><tr><td>30</td><td>6.6</td><td>6.8</td><td>6.7</td><td>6.8</td><td>6.3</td><td>70</td><td>6.9</td><td>7.3</td><td>7.0</td><td>7.2</td><td>6.9</td><td>110</td><td>8.1</td><td>8.5</td><td>7.4</td><td>7.6</td><td>7.2</td></tr><tr><td>31</td><td>6.7</td><td>6.9</td><td>6.7</td><td>6.8</td><td>6.3</td><td>71</td><td>6.9</td><td>7.3</td><td>7.1</td><td>7.3</td><td>7.0</td><td>112</td><td>8.2</td><td>8.6</td><td>7.4</td><td>7.6</td><td></td></tr><tr><td>32</td><td>6.7</td><td>6.9</td><td>6.8</td><td>6.9</td><td>6.4</td><td>72</td><td>6.9</td><td>7.3</td><td>7.1</td><td>7.3</td><td>7.0</td><td>114</td><td>8.6</td><td>9.0</td><td>7.5</td><td>7.7</td><td></td></tr><tr><td>33</td><td>6.7</td><td>6.9</td><td>6.8</td><td>6.9</td><td>6.4</td><td>73</td><td>6.9</td><td>7.2</td><td>7.1</td><td>7.3</td><td>6.9</td><td>116</td><td>8.8</td><td></td><td>7.5</td><td>7.7</td><td></td></tr><tr><td>34</td><td>6.7</td><td>6.9</td><td>6.8</td><td>6.9</td><td>6.5</td><td>74</td><td>6.8</td><td>7.1</td><td>7.0</td><td>7.2</td><td>6.8</td><td>118</td><td>9.0</td><td></td><td>7.5</td><td>7.7</td><td></td></tr><tr><td>35</td><td>6.7</td><td>6.9</td><td>6.8</td><td>6.9</td><td>6.6</td><td>75</td><td>6.8</td><td>7.1</td><td>6.9</td><td>7.1</td><td>6.8</td><td>120</td><td></td><td></td><td>7.5</td><td>7.7</td><td></td></tr><tr><td>36</td><td>6.6</td><td>6.9</td><td>6.7</td><td>6.8</td><td>6.6</td><td>76</td><td>6.9</td><td>7.2</td><td>6.9</td><td>7.1</td><td>6.8</td><td>122</td><td></td><td></td><td>7.4</td><td>7.6</td><td></td></tr><tr><td>37</td><td>6.5</td><td>6.7</td><td>6.7</td><td>6.8</td><td>6.6</td><td>77</td><td>6.9</td><td>7.2</td><td>6.9</td><td>7.1</td><td>6.8</td><td>124</td><td></td><td></td><td>7.3</td><td>7.5</td><td></td></tr><tr><td>38</td><td>6.5</td><td>6.7</td><td>6.7</td><td>6.8</td><td>6.6</td><td>78</td><td>6.9</td><td>7.3</td><td>6.9</td><td>7.1</td><td>6.9</td><td>126</td><td></td><td></td><td>7.2</td><td>7.4</td><td></td></tr><tr><td>39</td><td>6.4</td><td>6.6</td><td>6.6</td><td>6.7</td><td>6.7</td><td>79</td><td>6.8</td><td>7.2</td><td>6.9</td><td>7.1</td><td>6.8</td><td>128</td><td></td><td></td><td>7.1</td><td>7.4</td><td></td></tr><tr><td>40</td><td>6.4</td><td>6.6</td><td>6.6</td><td>6.7</td><td>6.7</td><td>80</td><td>6.7</td><td>7.1</td><td>6.9</td><td>7.1</td><td>6.7</td><td>130</td><td></td><td></td><td>7.0</td><td>7.3</td><td></td></tr><tr><td>41</td><td>6.5</td><td>6.7</td><td>6.5</td><td>6.6</td><td>6.6</td><td>81</td><td>6.8</td><td>7.2</td><td>7.0</td><td>7.2</td><td>6.8</td><td>132</td><td></td><td></td><td>7.0</td><td>7.3</td><td></td></tr><tr><td>42</td><td>6.5</td><td>6.7</td><td>6.5</td><td>6.6</td><td>6.5</td><td>82</td><td>6.9</td><td>7.2</td><td>7.1</td><td>7.3</td><td>6.9</td><td>134</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>43</td><td>6.5</td><td>6.7</td><td>6.6</td><td>6.7</td><td>6.5</td><td>83</td><td>7.0</td><td>7.4</td><td>7.2</td><td>7.4</td><td>6.9</td><td>136</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>44</td><td>6.5</td><td>6.7</td><td>6.7</td><td>6.8</td><td>6.5</td><td>84</td><td>7.0</td><td>7.4</td><td>7.3</td><td>7.5</td><td>6.9</td><td>138</td><td></td><td></td><td>7.0</td><td>7.3</td><td></td></tr><tr><td>45</td><td>6.7</td><td>6.9</td><td>6.7</td><td>6.8</td><td>6.5</td><td>85</td><td>7.0</td><td>7.4</td><td>7.3</td><td>7.5</td><td>6.8</td><td>140</td><td></td><td></td><td>7.1</td><td>7.4</td><td></td></tr><tr><td>46</td><td>6.8</td><td>7.1</td><td>6.7</td><td>6.8</td><td>6.6</td><td>86</td><td>6.9</td><td>7.3</td><td>7.3</td><td>7.5</td><td>6.7</td><td>142</td><td></td><td></td><td>7.1</td><td>7.4</td><td></td></tr><tr><td>47</td><td>6.9</td><td>7.2</td><td>6.7</td><td>6.8</td><td>6.6</td><td>87</td><td>7.0</td><td>7.3</td><td>7.2</td><td>7.4</td><td>6.8</td><td>144</td><td></td><td></td><td>7.0</td><td>7.3</td><td></td></tr><tr><td>48</td><td>6.9</td><td>7.2</td><td>6.7</td><td>6.8</td><td>6.7</td><td>88</td><td>7.1</td><td>7.5</td><td>7.2</td><td>7.4</td><td>6.8</td><td>146</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>49</td><td>6.8</td><td>7.1</td><td>6.7</td><td>6.8</td><td>6.7</td><td>89</td><td>7.0</td><td>7.4</td><td>7.2</td><td>7.4</td><td>6.8</td><td>148</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>50</td><td>6.7</td><td>7.0</td><td>6.7</td><td>6.8</td><td>6.6</td><td>90</td><td>7.0</td><td>7.3</td><td>7.2</td><td>7.4</td><td>6.8</td><td>150</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>51</td><td>6.7</td><td>7.0</td><td>6.7</td><td>6.8</td><td>6.5</td><td>91</td><td>7.1</td><td>7.5</td><td>7.2</td><td>7.4</td><td>6.9</td><td>152</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>52</td><td>6.7</td><td>7.0</td><td>6.7</td><td>6.8</td><td>6.5</td><td>92</td><td>7.1</td><td>7.4</td><td>7.2</td><td>7.4</td><td>6.9</td><td>154</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>53</td><td>6.7</td><td>7.0</td><td>6.7</td><td>6.8</td><td>6.6</td><td>93</td><td>7.2</td><td>7.5</td><td>7.2</td><td>7.4</td><td>6.9</td><td>156</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>54</td><td>6.8</td><td>7.1</td><td>6.8</td><td>6.9</td><td>6.6</td><td>94</td><td>7.1</td><td>7.4</td><td>7.2</td><td>7.4</td><td>7.0</td><td>158</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td>55</td><td>6.8</td><td>7.1</td><td>6.9</td><td>7.0</td><td>6.6</td><td>95</td><td>7.2</td><td>7.6</td><td>7.2</td><td>7.4</td><td>7.0</td><td>160</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>170</td><td></td><td></td><td>6.9</td><td>7.2</td><td></td></tr></table>

Besides these original tabulated Gutenberg-Richter Q values for shallow crustal earthquake there exist also tables with values resulting from scanning Figure 1a for vertical component Pwave readings in discrete intervals of source distance and depth. The respective table, produced by the USGS/NEIC, is reproduced in PD 3.1 of this Manual, together with the source code of the program used for interpolation between these tabulated values.

Comment 3.1: Until now, this table has been used by the USGS/NEIC exclusively for scaling short-period narrowband P-wave amplitude readings at periods around $1 \mathrm { ~ s ~ } ( \mathrm { T } < 3 \mathrm { s } )$ and calculating mb by essentially the same formula (8). However, instead of looking for the true (A/T)max it has become common to measure the maximum trace amplitude in the used short-period narrow-band record, calculate from it the related ground motion amplitude by dividing the trace amplitude by the record magnification at the related period, and then dividing this calculated “ground motion amplitude” by the related period.

Comment 3.2: Note that for periods below 4 s differences in frequency-dependent attenuation, which are not accounted for by formula (8), may become significant. For more detailed discussion and figures on this issue see Chapter 3 of this Manual as well as Bormann et al. (2009).

Comment 3.3: At the IASPEI General Assembly in Zürich (1967) the Committee on Magnitudes recommended that stations should report the magnitude for all waves for which calibration functions are available, to publish amplitude and period values separately and to correct body-wave magnitudes that were exclusively determined from short-period records. However, aiming at simplifying routine analysis and saving time, it has become wide-spread practice to measure only vertical-component P-wave amplitudes, and in western countries only on short-period narrowband recordings.

The Gutenberg and Richter (1956) $\mathbf { Q } ( \Delta , \mathbf { h } ) _ { \mathbf { P Z } }$ values are still the accepted standard calibration values for both mB and mb.

The now recommended IASPEI (2011) standard formula for broadband mB\_BB reads:

$$
\mathbf {m B \_ B B} = \log_ {1 0} (\mathbf {V} _ {\max} / 2 \pi) + \mathbf {Q} (\Delta , \mathbf {h}) - 3. 0\tag{9}
$$

where (quote): $^ { 6 6 } \mathrm { { V } _ { \mathrm { { m a x } } } ~ = }$ ground velocity in nm/s associated with the maximum traceamplitude in the entire P-phase train (time spanned by $\mathrm { P , p P , s P , }$ , and possibly PcP and their codas, but ending preferably before PP, as recorded on a vertical-component seismogram that is proportional to velocity, where the period of the measured phase, T, should satisfy the condition $\mathbf { 0 . 2 \ s < T < 3 0 \ s }$ , and where T should be preserved together with $\mathrm { \Delta V _ { m a x } }$ in. bulletin data-bases”. Standard mB\_BB is calculated in the distance range $2 0 ^ { \circ } \leq \mathbf { \alpha } \Delta \leq 1 0 0 ^ { \circ }$ and for source depths down to 700 km. However, equation (9) differs from the Gutenberg and Richter (1956) equation (8) for mB by virtue of the log $_ { 1 0 } ( \mathrm { V _ { m a x } } / 2 \pi )$ term, which replaces the classical $\log _ { 1 0 } ( \mathrm { A } / \mathrm { T } ) _ { \mathrm { m a x } }$ term.

The now recommended IASPEI (2011) standard formulas for mb determination reads:

$$
\mathbf {m b} = \log_ {1 0} (\mathbf {A} / \mathbf {T}) + \mathbf {Q} (\Delta , \mathbf {h}) - 3. 0,\tag{10}
$$

where (quote): ${ \bf \ddot { A } } = { \bf P } .$ -wave ground amplitude in nm calculated from the maximum traceamplitude in the entire P-phase train (time spanned by $\mathrm { P } , \mathrm { p } \mathrm { P } , \mathrm { s } \mathrm { P } ,$ , and possibly PcP and their codas, and ending preferably before PP)”;

T = period in seconds of the maximum P-wave trace amplitude with $\mathbf { T } < 3 \mathbf { s }$ . The distance and depth range of measurement as well as the Q(∆, h) values used are the same as for mB\_BB.

Both T and the maximum trace amplitude are measured on simulated vertical component WWSSN-SP records. A is determined by dividing the maximum trace amplitude by the magnification of the simulated WWSSN-SP response at period T. For the WWSSN-SP response parameters, the tabulated Q-values, and the algorithm used by the USGS/NEIC for mb determination see IS 3.3, respectively PD 3.1 of this Manual.

There is still another IASPEI (2011) recommended short-period standard magnitude which is used in the local and regional distance range and has been scaled to be compatible with teleseismic mb. It is also measured on simulated vertical component WWSSN-SP records in a narrow period range around 1 s and termed mb\_Lg. Its formula reads:

$$
\mathbf {m b \_ L g} = \log_ {1 0} (\mathrm{A}) + 0. 8 3 3 \log_ {1 0} [ \mathrm{r} ] + 0. 4 3 4 3 \gamma (\mathrm{r} - 1 0) - 0. 8 7, \tag {11}
$$

where (quote): $\mathbf { \check { \Psi } } ^ { 6 6 } = \mathbf { \Psi } ^ { 6 }$ “sustained ground-motion amplitude” in nm, defined as the third largest amplitude in the time window corresponding to group velocities of 3.6 to 3.2 $k m / s ,$ , in the period (T) range $0 . 7 \mathrm { ~ s ~ }$ to 1.3 s, r = epicentral distance in km and <sub>γ</sub> = coefficient of attenuation in km .

$\gamma$ is related to the quality factor Q through the equation $\gamma = \pi / ( Q { \cdot } U { \cdot } T )$ , where $U$ is group velocity and $T$ is the wave period of the $\mathrm { L _ { g } }$ wave. <sub>γ</sub>is a strong function of crustal structure and should be determined specifically for the region in which the mb\_Lg is to be used.

Arrival times with respect to the origin of the seismic disturbance are used, along with epicentral distance, to compute group velocity $U _ { \cdot } ^ { \prime }$

## 4 Body-wave and surface-wave magnitude scales used by the IDC

Another calibration function $\mathrm { P } ( \Delta ,$ h) for short-period mb determination at periods around 1 s has been elaborated by Veith and Clawson (1972) (see Figure 2). It is based on large sets of vertical-component P-wave recordings of WWSSN-SP seismographs from large explosions at 19 different sites. The P(∆, h) were specifically derived from short-period data and scaled to the level of the Gutenberg-Richter $\mathrm { Q } ( \Delta ) _ { \mathrm { P Z } }$ for surface focus.

The P(∆, h) calibration curves are currently used by the International Data Center (IDC) under the Comprehensive Test-Ban Treaty Organisation (CTBTO). However, the short-period filter applied at the IDC to the original broadband records prior to mb measurement does not simulate the standard WWSSN-SP response, which was used to derive the Veith-Clawson calibration curves. Rather, at the IDC one uses a more high-frequency response that peaks at 3.4 Hz (see Figure 16 in IS 3.3). This contributes partially to the earlier saturation of mb(IDC) as compared to mb(PDE) and mb(IASPEI). The other reason is the very short and fixed IDC measurement time-window for P amplitudes within the first 5.5 s after the P onset (see Chapter 17, p. 26-27) which may cause for great earthquakes with magnitudes above 8 differences between mb(IASPEI) and mb(IDC) of more than 1 m.u (see related discussion in section 4.3 of IS 3.3).

![](images/a54c81c54f3751374a7b5dc512db0f1804902cfc3cd453615ac0c621663d356a.jpg)  
Figure 2 Calibration functions P(∆, h) for mb determination from narrow-band short-period vertical-component records with peak displacement magnification around 1 Hz (WWSSN-SP characteristic) according to Veith and Clawson (1972). Note: The P(∆, h) values have to be used in conjunction with maximum P-wave peak-to-trough (2A!) amplitudes in units of nanometers $\dot { ( 1 \ \mathrm { n m } } = 1 0 ^ { - 9 } \mathrm { m } )$ (modified from Veith and Clawson (1972). Magnitude from shortperiod P-wave data, BSSA, 62(2), p. 446,  Seismological Society of America).

When comparing Figure 1a and Figure 2 it is obvious that the P(∆, h) curves look much smoother than the Q(∆, h)<sub>PZ</sub> curves. This agrees with the also much smoother preliminary revision of the G-R Q(∆) curve for mB calibration of shallow focus earthquakes by Saul and Bormann (2007) (see Figure 22 in IS 3.3). However, for deep events the P(∆, h) curves have been scaled according to upper mantle attenuation relationships available some 40 years ago, which have not yet been well constrained and still are largely model-dependent. Granville et al. (2005) confirmed that because of the large differences between the Gutenberg-Richter and the Veith-Clawson calibration functions for very deep earthquakes individual event magnitudes mb(PDE) and mb(IDC) may differ by several tenths of m.u. Since, however, the main focus of the CTBTO is on the location, magnitude determination and discrimination of shallow earthquakes and underground nuclear explosions (UNEs) these biases in P(∆, h) for deep earthquakes are not so relevant for the IDC assignment. But earthquake seismologists using IDC data should be aware of it and account for systematic mb(IDC) biases.

The local magnitude scale used by the IDC also differs from the classical Ml procedure and has been scaled so as to yield magnitude values that are compatible with the teleseismic mb(IDC). For details see Chapter 17, Section 7.4.2.1.

More appropriate for global seismology is the use at the IDC of an Ms calibration relationship that has been specifically derived for the use of 20 s surface-wave amplitude readings. The IDC uses the difference between its mb and Ms as the main criterion for discriminating between natural earthquakes and strong sub-surface explosions. However, Evernden (1971), von Seggern (1977), Herak and Herak (!993) and Rezapour and Pearce (1998) have shown that using the IASPEI standard formula (5) for Ms based on 20 s surface-wave readings only results in systematic distance-dependent errors up to about 0.6 m.u. On the one hand this is due to the fact that the simple relationship (5) cannot account for the energy focusing of surface-waves towards the antipodes and on the other hand to the fact that for distances ${ < } 6 0 ^ { \circ }$ the average periods of Rayleigh surface-wave maxima tend to be smaller than 18 s, down to about 8 s only around $1 0 ^ { \circ }$ (see Table $^ 6$ in this Data Sheet, Figure 11 in IS 3.3 and Bormann et al., 2009). Yet the more elaborate Rezapour and Pearce (1998) Ms relationship for 20 s surface waves compensates for it. It reads, when amplitudes are measured in nm:

$$
\mathrm{Ms} = \log_ {1 0} (\mathrm{A} / \mathrm{T}) _ {\max} + 1 / 3 \log_ {1 0} (\Delta \square) + 1 / 2 \square \log_ {1 0} (\sin \Delta) + 0. 0 0 4 6 \Delta + 2. 3 7 0,\tag{12}
$$

where the term 0.0046 is $\gamma$ times $\log _ { 1 0 } ( \mathrm { e } ) ~ ( = 0 . 4 3 4 3 )$ , and $\gamma ,$ the attenuation coefficient. $\gamma$ was determined empirically by Rezapour and Pearce (1998) to be 0.0105 using a very large data set. Surely, this relationship would also be more appropriate than formula (7) for calculating standard Ms\_20, however, recommendations about new calibration relationships have been beyond the mandate of the current IASPEI Working Group on Magnitude Measurements. Maybe, this matter will be taken up again after several years of strict standard Ms\_20 measurements with reduced procedure-dependent errors.

## 5 An experimental calibration function for PKP waves

An experimental calibration function for magnitude determinations, based on short-period vertical-component readings of various PKP phases in the distance range $1 4 5 ^ { \circ }$ to $1 6 4 ^ { \circ }$ , has been developed by Wendt (see Bormann and Wendt, 1999). The calibration curves are presented in Figure 3 and mb is calculated with the following formula (with A in µm):

$$
\mathrm{mb} (\mathrm{PKP}) = \log_ {1 0} (\mathrm{A} / \mathrm{T}) + \mathrm{Q} (\Delta , \mathrm{h}) _ {\mathrm{PKPab,bc,df}}.\tag{13}
$$

Extensive use of this relationship at station CLL proved that mb determinations from core phases are possible with a standard deviation of less $\mathrm { t h a n } \pm 0 . 2$ magnitude units as compared to P-wave mb determinations by NEIC and ISC. If more than one PKP phase can be identified and A and $\mathrm { T }$ been measured then the average value from all individual magnitude determinations provides a more stable estimate. The applicability of these calibration functions should be tested with data from other stations of the world-wide network.

![](images/33b1cfe465d3559123aa672970e115c8421cfe7bfd634348997e683e5b1450c0.jpg)  
Figure 3 Calibration functions according to S. Wendt for the determination of mb(PKP) for PKPdf, PKPbc and PKPab (see Bormann and Wendt, 1999).

## 6 Other magnitude scales

Besides the above mentioned magnitude scales there exist many other ones. Yet, most of them are less (or no longer) widely used, often only within local networks (such as coda or duration magnitudes), or based on specific instrumentation (e.g., strong-motion magnitudes), or aimed at assessing the “size” of specific earthquake related phenomena (such as tsunami magnitudes). Others are of much younger origin and still in the experimental stage, or highly based on theory and requiring much more complicated algorithms and procedures than the above described “classical” magnitudes. But in any event, all such alternative or complementary magnitudes have to be scaled in one or the other way to the pioneering magnitudes described above, first and foremost to Ml, Ms, mB or mb. For more details see Chapter 3 of NMSOP-2 and encyclopedia review papers by Bormann (2011) and Bormann and Saul (2009).

Most important amongst these alternative magnitudes are the (supposedly) non-saturating and more physically based moment-magnitude scale Mw and the complementary energy magnitude scale Me. The former has even become – not fully justified when taking the advantages of Me into account – the preferred magnitude scale for “unifying” earthquake catalogs as well as for seismic hazard assessment. Yet, the procedures for determining Mw and Me are not yet standardized and too sophisticated to be routinely applicable by ordinary analysts at seismological stations or smaller analysis centres. However, software is already offered which calculates these magnitudes in near real-time based on the online-retrieval of wave-form data from regional and global virtual seismic networks (see Chapter 8 and IS 8.3). But these are black-box systems with usually no more analysis personnel involved. In Chapter 3 of this Manual the procedures for calculating the seismic moment tensor, and Mw as part of it, as well as the released seismic wave energy and related Me, are described in detail, while Bormann and Di Giacomo (2011) outline in detail the common roots, differences and benefits of complementary use of Mw and Me.

## References

Abe, K. (1981). Magnitudes of large shallow earthquakes from 1904 to 1980. Phys. Earth Planet. Interiors, 27, 72-92.

Abe, K. (1984). Complements to “Magnitudes of large shallow earthquakes from 1904 to 1980).

Abe, K., and Kanamori, H. (1980). Magnitudes of great shallow earthquakes from 1953-1977. Tectonophysics, 62, 191-203.

Alsaker, A., Kvamme, L. B., Hansen, R. A., Dahle, A., and Bungum, H. (1991). The $\mathbf { M } _ { \mathrm { L } }$ scale in Norway. Bull. Seism. Soc. Am., 81, 2, 379-389.

Archangelskaya, V. M. (1959). The dispersion of surface waves in the earth’s crust. Izv. Akad. Nauk SSSR, Seriya Geofiz., 9 (in Russian).

Bakun, W. H., and Joyner, W. (1984). The M<sub>L</sub> scale in Central California. Bull. Seism. Soc. Am., 74, 5,1827-1843.

Baumbach, M., Bindi, D., Grosser, H., Milkereit, C., Parolai, S, Wang, R., Karkisa, S., Zünbul, S. and Zschau, J. (2003). Calibration of an ML scale in northwestern Turkey from 1999 Izmit aftershocks. Bull. Seism. Soc. Am., 93(5), 2289-2295.

Bormann, P. (1999). Regional International Training Course 1999 on Seismology, Seismic Hazard Assessment and Risk Mitigation. Lecture and exercise notes. Vol. I and II, GeoForschungsZentrum Potsdam, Scientific Technical Report STR99/13, 675 pp.

Bormann, P. (2011). Earthquake magnitude. In: Harsh Gupta (ed.). Encyclopedia of Solid Earth Geophysics, Springer, 207-218; doi: 10.1007/978-90-481-8702-7.

Bormann, P., and Wendt, S. (1999). Identification and analysis of longitudinal core phases: Requirements and guidelines. In: Bormann (1999), 346-366.

Bormann, P. (2011). Earthquake magnitude. In: Harsh Gupta (ed.). Encyclopedia of Solid Earth Geophysics, Springer, 207-218; doi: 10.1007/978-90-481-8702-7.

Bormann, P., and Saul, J. (2009). Earthquake magnitude. In: Encyclopedia of Complexity and Systems Science, edited by A. Meyers, Springer, Heidelberg, Vol. 3, 2473-2496.

Bormann, P., and D. Di Giacomo (2011). The moment magnitude $M _ { \mathrm { w } }$ and the energy magnitude $M _ { \mathrm { e } } \mathrm { : }$ : common roots and differences. J. Seismology, 15, 411-427; doi: 10.1007/s10950-010-9219-2.

Bormann, P., Liu, R., Xu, Z., Ren, K., Zhang, L., Wendt S. (2009). First application of the new IASPEI teleseismic magnitude standards to data of the China National Seismographic Network, Bull. Seism. Soc. Am. 99 (3), 1868-1891; doi: 10.1785/0120080010

Chávez, E., and Priestley, K. F. (1985). $\mathbf { M } _ { \mathrm { L } }$ observations in the great basin and $\mathbf { M } _ { 0 }$ versus $\mathbf { M } _ { \mathrm { L } }$ relationships for the 1980 Mammoth Lakes, California, earthquake sequence. Bull. Seism. Soc. Am., 75, 6, 1583-1598.

Evernden, J. F. (1971). Variation of Rayleigh-wave amplitude with distance, Bull. Seism. Soc. Am., 61, 2, 231-240.

Gellert, R. J., and Kanamori, H. (1977). Magnitudes of great shallow earthquakes from 1904 to 1952). Bull. Seism. Soc. Am., 67(3), 587-598.

Gorbunova, I. V., and Kondorskaya, N. V. (1977). Magnitudes in the seismological practice of the USSR. Izv. Akad. Nauk SSSR, ser Fizika Zemli, No. 2, Moscow (in Russian).

Granville, J. P., Richards, . G., Kim, W.-Y., and Sykes, L. R. (2005). Understanding the differences between three teleseismic $m _ { \mathrm { b } }$ scales. Bull. Seism. Soc. Am., 95(5), 1809-1824.

Greenhalgh, S. A., and Singh, R. (1986). A revised magnitude scale for South Australian earthquakes. Bull. Seism. Soc. Am., 76, 3, 757-769.

Gutenberg, B. (1945a). Amplitudes of surface waves and magnitudes of shallow earthquakes. Bull. Seism. Soc. Am., 35, 3-12.

Gutenberg, B. (1945b). Amplitudes of P, PP, and S and magnitude of shallow earthquakes. Bull. Seism. Soc. Am., 35, 57-69.

Gutenberg, B. (1945c). Magnitude determination of deep-focus earthquakes. Bull. Seism. Soc. Am., 35, 117-130.

Gutenberg, B., and Richter, C. F. (1954). Seismicity of the Earth and asscociated Phenomena. 2<sup>nd</sup> edition, Princeton University Press, 310 pp.

Gutenberg, B., and Richter, C. F. (1956). Magnitude and energy of earthquakes. Annali di Geofisica, 9, 1-15.

Herak, M., and Herak. D. (1993). Distance dependence of $\mathbf { M } _ { S }$ and calibrating function for 20 s Rayleigh waves. Bull. Seism. Soc. Am., 83, 6, 1881-1892.

Hunter, R. N. (1972). Use of LPZ for magnitude. In: NOAA Technical Report ERL 236- ESL21, J. Taggart, Editor, U.S. Dept. Commerce, Boulder, Colorado.

Hutton, L. K., and Boore, D. M. (1987). The $\mathbf { M } _ { \mathrm { L } }$ scale in Southern California. Bull. Seism. Soc. Am., 77, 6, 2074-2094.

IASPEI (2011). http://www.iaspei.org/commissions/CSOI/Summary\_WG-Recommendations\_20110909.pdf, last accessed December 2011.

Kiratzi, A. A., and Papazachos, B. C. (1984). Magnitude scales for earthquakes in Greece. Bull. Seism. Soc. Am., 74, 3, 969-985.

Langston, C. A., Brazier, R., Nyblade, A. A., and Owens, T. J. (1998). Local magnitude scale and seismicity rate for Tanzania, East Africa. Bull. Seism. Soc. Am., 88, 3, 712-721.

Lienkaemper, J. J. (1984). Comparison of two surface-wave magnitude scales: M of Gutenberg and Richter (1954) and Ms of “Preliminary Determination of Epicenters”. Bull. Seism. Soc. Am., 74(6), 2357-2378.

Muco, B., and Minga, P. (1991). Magnitude determination of near earthquakes for the Albanian network. Bolletino di Geofisica Teorica ed Applicata., XXXIII, 129, 17-24.

Pechmann, J.C., Nava, S.J., Terra, F.M., and Bernier, J.C. (2007). Local magnitude determinations for Intermountain Seismic Belt earthquakes from broadband digital data, Bull. Seism. Soc. Am., 97, 557-574.

Rezapour, M., and Pearce, R. G. (1998). Bias in surface-wave magnitude $\mathbf { M } _ { \mathrm { S } }$ due to inadequate distance corrections. Bull. Seism. Soc. Am., 88, 1, 43-61.

Richter, C. F. (1935). An instrumental earthquake magnitude scale. Bull. Seism. Soc. Am., 25, 1-32.

Richter, C. F. (1958). Elementary seismology. W. H. Freeman and Company, San Francisco and London, viii + 768 pp.

Saunders, I., Ottemöller, L., Brandt, M. B. C., and Fourie, C. J. S. (2011). Calibration of an ML scale for Sourt Africa using tectonic earthquake data recorded by the South African National Seismograph Network: 2006 to 2009.

Soloviev, S. L. (1955). Classification of earthquakes in order of energy (in Russian). Trudy Geofiz. Inst. AN SSSR, 30, 157, 3-31.

Stange, St. (2006). M<sub>L</sub> determination for local and regional events using a sparse network in Southwestern Germany. J. Seismol., 10, 247-257.

Strauch, W., and Wylegalla, K. (1989). Potsdam network magnitudes of the 1985/86 Vogtland earthquakes and determination of Q from Sg-amplitudes and coda waves. In: Bormann, P. (Ed.), Monitoring and analysis of the earthquake swarm 1985/86 in the region Vogtland/Western Bohemia, Akad. Wiss. DDR, Zentralinstitut für Physik der Erde, Veröffentl. No. 110, 101-108.

Uhrhammer, R.A., Helweg, M., Hutton, K., Lombard, P., Walters, A.W., Hauksson, E., and Oppenheimer, D. (2011). California Integrated Seismic Network (CISN) Local Magnitude Determination in California and Vicinity, Bull. Seism. Soc. Am., 101, 2685-2693.

Vanĕk, J., Zapotek, A., Karnik, V., Kondorskaya, N.V., Riznichenko, Yu.V., Savarensky, E.F., Solov’yov, S.L., and Shebalin, N.V. (1962). Standardization of magnitude scales. Izvestiya Akad. SSSR., Ser. Geofiz., 2, 153-158.

Veith, K. F., and Clawson, G. E. (1972). Magnitude from short-period P-wave data. Bull. Seism. Soc. Am., 62, 435-452.

Vidal, A., and Munguía, L. (1999). The ML scale in Northern Baja California, México. Bull. Seism. Soc. Am., 89(3), 750-763.

Von Seggern, D. (1977). Amplitude-distance relation for 20-second Rayleigh waves. Bull. Seism. Soc. Am., 67, p. 405-411.

Wahlström, R., and Strauch, W. (1984). A regional magnitude scale for Central Europe based on crustal wave attenuation. Seismological Dep. Univ. of Uppsala, Report No. 3-84, 16 pp.

Willmore, P. L. (Ed.) (1979). Manual of Seismological Observatory Practice. World Data Center A for Solid Earth Geophysics, Report SE-20, September 1979, Boulder, Colorado, 165 pp.