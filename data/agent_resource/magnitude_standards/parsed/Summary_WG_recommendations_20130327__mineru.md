# SUMMARY OF MAGNITUDE WORKING GROUP RECOMMENDATIONS ON STANDARD PROCEDURES FOR DETERMINING EARTHQUAKE MAGNITUDES FROM DIGITAL DATA

[2013 March 27]

The Working Group on Magnitudes (Magnitude WG\*) of the International Association of Seismology and Physics of the Earth’s Interior (IASPEI) Commission on Seismological Observation and Interpretation (CoSOI) was established to recommend standard procedures for making measurements from digital data to be used in calculating several widely used types of earthquake magnitude. The recommended procedures from the Magnitude WG have been approved by the IASPEI Commission on Seismological Observations and Interpretations. We henceforth refer to the proposed procedures as the IASPEI standard procedures for magnitude determination.

The IASPEI standard procedures address the measurement of amplitudes and periods from digital data for use in calculating the generic magnitude types ML, Ms, mb, mB, and mb\_Lg. For Ms, standard procedures are proposed for two different traditions -- Ms measured from waves with periods near 20s here denoted Ms\_20 and Ms measured from waves in a much broader period-range here denoted Ms\_BB . For the generic intermediate-period/broadband body-wave magnitude mB, we propose a procedure based on the maximum amplitude of the P-wave measured on a velocity-proportional trace: we denote the resulting magnitude mB\_BB. The IASPEI standard procedures also specify a standard equation for Mw from among several slightly different equations. Abbreviated descriptions of the procedures are described below. More detailed descriptions of the standard procedures, the relationships of the IASPEI magnitudes to other magnitudes and discussion of acceptable alternatives to specific steps in the application of individual procedures are discussed in Chapter 3 and related datasheets, exercises, and information sheets, IS 3.3 in particular, of the New Manual of Seismological Observatory Practice (NMSOP-2) (http://nmsop.gfz-potsdam.de).

Some of the IASPEI standard procedures require the use of broadband (BB) records that are proportional to ground motion velocity at least within the period range that has been recommended for the measurement of the respective magnitudes: BB records that have been restituted from originally more band-limited data would also be suitable for these procedures. Other procedures require filtering BB records so that they replicate the response of classical standard seismographs, such as the Wood-Anderson (WA) seismograph or the short-period (SP) and long-period (LP) seismographs that were used in the World-Wide Standardized Seismograph Network (WWSSN) (next section).

\* As of the time of this revision, Magnitude WG members are Peter Bormann (cochairman), James W. Dewey (co-chairman), Irina Gabsatarova, Søren Gregersen, Alexander A. Gusev, Won-Yon Kim, Howard J. Patton, Bruce W. Presgrave, Liu Ruifeng, Joachim Saul, Dmitry Storchak (ex officio), Robert A. Uhrhammer, and Siegfried Wendt. Former members are Peter Firbas, Jens Havskov (ex officio), Klaus Klinge, and Karl Veith.

## POLES AND ZEROES FOR WOOD-ANDERSON, WWSSN-SP, AND WWSSN-LP SEISMOGRAPHS

Poles and zeroes corresponding to the displacement transfer functions for representative “average” classical analog standard seismographs WWSSN-SP, WWSSN-LP and Wood Anderson with their equivalent eigenperiod and damping of the seismometer and galvanometer and coupling factor $\sigma ^ { 2 }$ (where applicable) are given in Table 1 (courtesy of Charles R. Hutt, U. S. Geological Survey, who also provided much of the immediately following documentation). Note that the number of zeroes determines the slope of the response at the low-frequency end and that this slope changes towards higher frequencies at the frequencies determined by the poles. At the frequency of a conjugate complex pole the slope is reduced by two orders, while at a single pole with real part only, the slope is reduced by one order only. The left number in brackets is the value of the real part; the right number that of the imaginary part. The normalized amplitude responses corresponding to the poles and zeroes of Table 1 are shown in Figure 1.

At magnifications of 50,000 and higher, transfer functions for the WWSSN short-period seismograph differed somewhat for different magnification settings, due to galvanometerseismometer reaction. The response shown in Table 1 and recommended for use with mb is appropriate to a “100,000 magnification” short-period WWSSN seismograph.

Transfer functions for the WWSSN long-period seismograph also differed somewhat for different magnification settings, due to galvanometer-seismometer reaction. The response shown in Table 1 is appropriate to a “1500 magnification” long-period vertical WWSSN seismograph. The transfer functions of the WWSSN LP horizontal seismograph also differed from that of the WWSSN-LP vertical seismograph. One should note that the coupling which exists in electromagnetic seismographs with galvanometric recording between the seismometer and galvanometer has been taken into account in the listed poles in such a way as to make the coupling factor $\sigma ^ { 2 }$ effectively zero. Accordingly, the resulting free periods and damping values given for the equivalent seismometer $( T _ { \mathrm { s } }$ and $h _ { \mathrm { s } } )$ and galvanometer $( T _ { \mathrm { g } }$ and $h _ { \mathrm { g } } )$ in Table 1 are somewhat different from the nominal values of the uncoupled system components of classical seismographs and the respective coupling factors are reported as zero. The nominal free periods of the uncoupled components are $T _ { \mathrm { s } } = 1 . 0 0 ~ \mathrm { s }$ and $T _ { \mathrm { g } } = 0 . 7 5 ~ \mathrm { s }$ for WWSSN-SP and $T _ { \mathrm { s } } = 1 5 . 0$ s and $T \mathrm { g } = 1 0 0 . 0 \mathrm { s }$ for WWSSN-LP.

The frequency response of the Wood-Anderson seismograph (Table 1) is based on the paper of Uhrhammer and Collins (1990).

<table><tr><td>Seismograph</td><td>Zeros</td><td colspan="2">Poles</td><td> $T_s/s$ </td><td> $h_s$ </td><td> $T_g/s$ </td><td> $h_g$ </td><td> $σ^2$ </td></tr><tr><td>WWSSN-SP</td><td>(0.0, 0.0)(0.0, 0.0)(0.0, 0.0)</td><td>(-3.72500, -6.22000)(=p1)(-3.72500, 6.22000)(=p2)(-5.61200, 0.00000)(=p3)(-13.2400, 0.00000)(=p4)(-21.0800, 0.00000)(=p5)</td><td>(=p1)</td><td>0.867</td><td>0.5138</td><td>0.729</td><td>1.0935</td><td></td></tr><tr><td>WWSSN-LP</td><td>(0.0, 0.0)(0.0, 0.0)(0.0, 0.0)</td><td>(-0.40180, -0.08559)(-0.40180, 0.08559)(-0.04841, 0.00000)(-0.08816, 0.00000)</td><td></td><td>15.29</td><td>0.978</td><td>96.18</td><td>1.045</td><td></td></tr><tr><td>WA</td><td>(0.0, 0.0)(0.0, 0.0)</td><td>(-5.49779, -5.60886)(-5.49779, 5.60886)</td><td></td><td>0.8</td><td>0.7</td><td></td><td></td><td></td></tr></table>

Table 1. Zeroes and poles corresponding to the displacement transfer function of the WWSSN-SP seismograph, WWSSN-LP seismograph, and the Wood-Anderson (WA) seismograph. Zeroes and poles are represented in angular frequency (radians per second). $\mathrm { T _ { S } } = \mathrm { s e i s m o m e t e r }$ free period; $\mathrm { h } _ { \mathrm { s } } = \mathrm { s e i s m o m e t e r }$ damping constant; $\mathrm { { T } _ { g } = }$ galvanometer free period; h<sub>g</sub> = galvanometer damping constant; $\sigma ^ { 2 } = \mathrm { c o u p l i n g }$ factor. In this representation, free periods and damping constants have been adjusted slightly so that response can be correctly modeled with $\bar { \mathsf { \sigma } } ^ { 2 } = 0$ . The displacement-response functions implied by the poles and zeroes are commonly normalized with respect to the following frequencies $( \mathrm { f _ { n } } )$ using the associated normalization factors $( \mathsf { A } _ { 0 } )$ as follows: WWSSN-SP, $\mathrm { f _ { n } } = 1 \ \mathrm { H z } , \mathrm { A _ { o } } = 5 3 2 . 1 4$ ; WWSSN-LP, $\mathrm { f _ { n } } = 0 . 0 4$ Hz, $\mathbf { A _ { 0 } } = 0 . 9 7 8 6 6 ;$ WA, $\mathrm { f _ { n } } = 4$ Hz, $\mathbf { A } _ { 0 } =$ 1.0028.

![](images/5eb9de1436ecd483109987a796bdcf9c1edf2dfa36494c541353513ef1fc8215.jpg)  
Figure 1. Displacement amplitude-frequency responses of the classical seismographs: WWSSN-SP, WWSSN-LP and Wood-Anderson (WA), normalized at the frequencies (f<sub>n</sub>) in the caption of Table 1.

## IASPEI STANDARD PROCEDURES FOR WIDELY USED MAGNITUDE TYPES

The amplitudes used in the magnitude formulas below are in most circumstances to be measured as one-half the maximum deflection of the seismogram trace, peak-to-adjacenttrough or trough-to-adjacent-peak, where peak and trough are separated by one crossing of the zero-line: the measurement is sometimes described as “one-half peak-to-peak amplitude.” None of the magnitude formulas presented in this article are intended to be used with the full peak-to-trough deflection as the amplitude. The periods are to be measured as twice the time-intervals separating the peak and adjacent-trough from which the amplitudes are measured. The amplitude-phase arrival-times are to be measured as the time of the zero-crossing between the peak and adjacent-trough from which the amplitudes are measured.

Modern digital seismogram analysis programs commonly measure amplitudes in units of nm (for displacement) or nm/s (for velocity), respectively, and not, as assumed by the

classical magnitude formulas, in m. The commonly known classical calibration relationships have been modified to be consistent with displacements measured in nm.

## ML – local magnitude consistent with the magnitude of Richter (1935)

For crustal earthquakes in regions with attenuative properties similar to those of Southern California, the proposed standard equation is

$$
M L = \log_ {1 0} (A) + 1. 1 1 \log_ {1 0} R + 0. 0 0 1 8 9 * R - 2. 0 9, \tag {1}
$$

where:

A = maximum trace amplitude in nm that is measured on output from a horizontal-component instrument that is filtered so that the response of the seismograph/filter system replicates that of a Wood-Anderson standard seismograph but with a static magnification of 1 (see Table 1 and Figure 1);

R = hypocentral distance in km, typically less than 1000 km.

Equation (1) is an expansion of that of Hutton and Boore (1987). The constant term in equation (1), -2.09, is based on an experimentally determined static magnification of the Wood-Anderson of 2080, rather than the theoretical magnification of 2800 that was specified by the seismograph´s manufacturer. The formulation of equation (1) reflects the intent of the Magnitude WG that reported ML amplitude data not be affected by uncertainty in the static magnification of the Wood-Anderson seismograph.

For seismographic stations containing two horizontal components, amplitudes are measured independently from each horizontal component, and each amplitude is treated as a single datum. There is no effort to measure the two observations at the same time, and there is no attempt to compute a vector average.

For crustal earthquakes in regions with attenuative properties that are different than those of coastal California, and for measuring magnitudes with vertical-component seismographs, the standard equation is of the form:

$$
(2) M L = \log_ {1 0} (A) + C (R) + D,
$$

where A and R are as defined in equation (1), except that A may be measured from a vertical-component instrument, and where C(R) and D have been calibrated to adjust for the different regional attenuation and to adjust for any systematic differences between amplitudes measured on horizontal seismographs and those measured on vertical seismographs.

Ms\_20 – teleseismic surface-wave magnitude at period $o f \sim 2 O$ s

$$
(3) M s \_ 2 0 = \log_ {1 0} (A / T) + 1. 6 6 \log_ {1 0} \Delta + 0. 3,
$$

where:

A = vertical-component ground displacement in nm measured from the maximum trace-amplitude of a surface-wave phase having a period between 18 s and 22 s on a waveform that has been filtered so that the frequency response of the seismograph/filter system replicates that of a World-Wide Standardized Seismograph Network (WWSSN) long-period seismograph (see Table 1), with A being determined by dividing the maximum trace amplitude by the magnification of the simulated WWSSN-LP response at period $T ;$

T = period in seconds $( 1 8 ~ \mathrm { s } \leq T \leq 2 2 ~ \mathrm { s } ) ;$

= epicentral distance in degrees, $2 0 ^ { \circ } \leq \Delta \leq 1 6 0 ^ { \circ }$

Some agencies compute Ms\_20 only for shallow-focus earthquakes (typically those whose confidence-intervals on focal-depth would allow them to be shallower than 50 or 60 km). Ms\_20 would be expected to significantly underrepresent the energy of intermediate- and deep-focus earthquakes, due to their less effective generation of surface waves, unless an adjustment is made to account for their large focal-depths, e.g., according to Herak et al. (2001).

Equation (3) is formally equivalent to the Ms equation proposed by Vaněk et al. (1962) but is here applied to vertical motion measurements in a narrow range of periods.

Ms\_BB – surface-wave magnitude from broad-band instruments.

$$
(4) M s \_ B B = \log_ {1 0} (V _ {\max} / 2 \pi) + 1. 6 6 \log_ {1 0} \Delta + 0. 3,
$$

where:

V = ground velocity in nm/s associated with the maximum trace-amplitude in the surface-wave train, as recorded on a vertical-component seismogram that is proportional to velocity, where the period of the surface-wave, T, should satisfy the condition $3 \mathrm { { s } } < T < 6 0 \mathrm { { s } }$ , and where T should be preserved together with $V _ { m a x }$ in bulletin data-bases;

= epicentral distance in degrees, $2 ^ { \circ } \leq \Delta \leq 1 6 0 ^ { \circ }$

As with $M s \_ { 2 0 } ,$ some agencies compute Ms\_BB only for shallow-focus earthquakes.

Equation (4) is based on the Ms equation proposed by Vaněk et al. (1962), but is here applied to vertical motion measurements and is used with the $\log _ { 1 0 } ( V _ { m a x } / 2 \pi )$ term replacing the $\log _ { 1 0 } ( A T \ ) _ { \mathrm { m a x } }$ term of the original.

mb – short-period body-wave magnitude

$$
m b = \log_ {1 0} (A / T) + Q (\Delta , h) - 3. 0 \tag {5}
$$

where:

A = P-wave ground amplitude in nm calculated from the maximum trace-amplitude in the entire P-phase train (time spanned by P, pP, sP, and possibly PcP and their codas, and ending preferably before PP);

T = period in seconds, T < 3 s; of the maximum P-wave trace amplitude.

Q( , h) = attenuation function for PZ (P-waves recorded on vertical component seismographs) established by Gutenberg and Richter (1956) in the tabulated or algorithmic form as used by the U.S. Geological Survey/National Earthquake Information Center (USGS/NEIC) (Table 2);

= epicentral distance in degrees, $2 0 ^ { \circ } \leq \Delta \leq 1 0 0 ^ { \circ }$

h = focal depth in km;

and where both T and the maximum trace amplitude are measured on output from a vertical-component instrument that is filtered so that the frequency response of the seismograph/filter system replicates that of a WWSSN short-period seismograph (Table 1), with A being determined by dividing the maximum trace amplitude by the magnification of the simulated WWSSN-SP response at period T.

Table 2. Attenuation (Q) function to be used with mb (equation 5) and mB\_BB (equation 6). This version of Q( , focal-depth) was digitized in the 1960’s from Figure 5 of Gutenberg and Richter (1956) and is used at the USGS/NEIC. This is a comma-delimited file, intended to be copied into applications, with the first two rows being header rows. The first column is epicentral distance D (= ) in degrees, and the following columns give Q for distance D and depths 0, 25, …700 km. For D and focal-depth lying between tabulated values, Q is obtained by linear interpolation from the four neighboring tabulated values.

<table><tr><td>D,Focal Depth (km),, , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , , ,</td></tr><tr><td>0.0, 25, 50, 75,100,150,200,250,300,350,400,450,500,550,600,650,700</td></tr><tr><td>20,6.1,6.1,6.1,6.1,6.1,6.2,6.3,6.3,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.2,6.0</td></tr><tr><td>21,6.1,6.2,6.1,6.1,6.1,6.2,6.3,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.2,6.0</td></tr><tr><td>22,6.2,6.2,6.2,6.2,6.1,6.2,6.3,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.3,6.1</td></tr><tr><td>23,6.3,6.3,6.2,6.2,6.1,6.2,6.4,6.3,6.2,6.1,6.2,6.3,6.4,6.4,6.4,6.3,6.1</td></tr><tr><td>24,6.4,6.3,6.3,6.2,6.2,6.3,6.4,6.3,6.2,6.1,6.2,6.3,6.3,6.4,6.4,6.4,6.1</td></tr><tr><td>25,6.5,6.4,6.3,6.2,6.2,6.3,6.4,6.3,6.2,6.1,6.2,6.3,6.3,6.4,6.4,6.4,6.2</td></tr><tr><td>26,6.5,6.4,6.3,6.3,6.3,6.4,6.5,6.4,6.2,6.1,6.2,6.2,6.3,6.4,6.4,6.4,6.2</td></tr><tr><td>27,6.5,6.4,6.4,6.3,6.3,6.4,6.5,6.4,6.2,6.1,6.2,6.2,6.3,6.4,6.4,6.4,6.3</td></tr><tr><td>28,6.6,6.5,6.4,6.4,6.4,6.5,6.5,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.3</td></tr><tr><td>29,6.6,6.5,6.4,6.4,6.4,6.5,6.5,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.3</td></tr><tr><td>30,6.6,6.6,6.5,6.5,6.5,6.5,6.5,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.3</td></tr><tr><td>31,6.7,6.6,6.5,6.5,6.5,6.5,6.5,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.3</td></tr><tr><td>32,6.7,6.7,6.6,6.6,6.5,6.6,6.4,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.4</td></tr><tr><td>33,6.7,6.7,6.6,6.6,6.6,6.5,6.4,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.4</td></tr><tr><td>34,6.7,6.7,6.7,6.7,6.6,6.5,6.4,6.4,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.4,6.3</td></tr><tr><td>35,6.6,6.7,6.7,6.7,6.7,6.5,6.4,6.3,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.3,6.3</td></tr><tr><td>36,6.6,6.7,6.7,6.7,6.7,6.5,6.4,6.3,6.3,6.1,6.1,6.2,6.3,6.4,6.4,6.3,6.3</td></tr><tr><td>37,6.5,6.6,6.7,6.7,6.7,6.5,6.4,6.3,6.2,6.1,6.1,6.2,6.3,6.4,6.4,6.3,6.3</td></tr><tr><td>38,6.5,6.6,6.7,6.7,6.7,6.5,6.4,6.3,6.2,6.1,6.1,6.2,6.3,6.4,6.3,6.3,6.3</td></tr><tr><td>39,6.4,6.5,6.6,6.7,6.6,6.5,6.4,6.3,6.1,6.0,6.1,6.2,6.3,6.4,6.3,6.3,6.3</td></tr><tr><td>40,6.4,6.5,6.6,6.7,6.6,6.5,6.3,6.2,6.1,6.0,6.1,6.2,6.3,6.4,6.3,6.2,6.3</td></tr><tr><td>41,6.5,6.5,6.5,6.6,6.6,6.4,6.3,6.2,6.0,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.3</td></tr><tr><td>42,6.5,6.5,6.5,6.6,6.6,6.4,6.3,6.2,6.0,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.3</td></tr><tr><td>43,6.5,6.5,6.5,6.6,6.6,6.4,6.3,6.1,6.0,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.3</td></tr><tr><td>44,6.6,6.6,6.5,6.6,6.6,6.4,6.3,6.1,6.1,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.2</td></tr><tr><td>45,6.7,6.7,6.6,6.6,6.6,6.4,6.2,6.1,6.1,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.2</td></tr><tr><td>46,6.8,6.7,6.7,6.7,6.6,6.4,6.2,6.1,6.1,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.2</td></tr><tr><td>47,6.9,6.8,6.7,6.7,6.6,6.4,6.2,6.1,6.1,6.0,6.1,6.2,6.3,6.3,6.3,6.2,6.2</td></tr><tr><td>48,6.9,6.8,6.8,6.7,6.6,6.5,6.2,6.1,6.1,6.0,6.1,6.2,6.2,6.3,6.3,6.2,6.2</td></tr><tr><td>49,6.8,6.8,6.8,6.8,6.7,6.5,6.2,6.2,6.1,6.1,6.1,6.2,6.2,6.3,6.3,6.2,6.2</td></tr><tr><td>50,6.7,6.8,6.8,6.8,6.8,6.5,6.3,6.2,6.1,6.1,6.1,6.1,6.2,6.3,6.3,6.1,6.1</td></tr><tr><td>51,6.7,6.7,6.8,6.8,6.8,6.5,6.3,6.2,6.2,6.1,6.1,6.1,6.2,6.2,6.2,6.1,6.1</td></tr><tr><td>52,6.7,6.7,6.8,6.8,6.8,6.5,6.4,6.2,6.2,6.1,6.1,6.1,6.1,6.1,6.2,6.2,6.1,6.1</td></tr><tr><td>53,6.7,6.7,6.8,6.8,6.8,6.6,6.4,6.2,6.2,6.1,6.1,6.1,6.1,6.1,6.2,6.1,6.1</td></tr><tr><td>54,6.8,6.8,6.8,6.8,6.8,6.6,6.4,6.3,6.2,6.1,6.1,6.1,6.1,6.1,6.1,6.1,6.0</td></tr><tr><td>55,6.8,6.8,6.8,6.8,6.8,6.6,6.5,6.3,6.2,6.2,6.1,6.1,6.1,6.1,6.1,6.0,6.0</td></tr><tr><td>56,6.8,6.8,6.8,6.8,6.8,6.7,6.5,6.3,6.2,6.2,6.1,6.1,6.1,6.1,6.1,6.0,6.0</td></tr><tr><td>57,6.8,6.8,6.8,6.9,6.8,6.7,6.5,6.4,6.2,6.2,6.2,6.2,6.1,6.1,6.0,6.0,6.0</td></tr><tr><td>58,6.8,6.8,6.9,6.9,6.8,6.7,6.5,6.4,6.3,6.2,6.2,6.2,6.1,6.1,6.0,6.0,6.0</td></tr><tr><td>59,6.9,6.9,6.9,6.9,6.9,6.7,6.5,6.4,6.3,6.2,6.2,6.2,6.2,6.1,6.0,6.0,6.0</td></tr><tr><td>60,6.9,6.9,6.9,6.9,6.9,6.7,6.5,6.4,6.3,6.3,6.2,6.2,6.2,6.1,6.0,6.0,6.0</td></tr><tr><td>61,6.9,6.9,6.9,6.9,6.8,6.7,6.5,6.4,6.3,6.3,6.3,6.3,6.2,6.2,6.1,6.0,6.0</td></tr><tr><td>62,7.0,6.9,6.9,6.9,6.8,6.7,6.6,6.4,6.4,6.3,6.3,6.3,6.3,6.2,6.1,6.1,6.0</td></tr><tr><td>63,7.0,6.9,6.9,6.8,6.7,6.7,6.6,6.5,6.4,6.4,6.4,6.3,6.3,6.2,6.2,6.1,6.0</td></tr><tr><td>64,7.0,6.9,6.8,6.7,6.7,6.7,6.6,6.5,6.5,6.4,6.4,6.4,6.4,6.3,6.2,6.1,6.1</td></tr><tr><td>65,7.0,6.9,6.8,6.7,6.7,6.7,6.6,6.5,6.5,6.5,6.4,6.4,6.4,6.3,6.2,6.1,6.1</td></tr><tr><td>66,7.0,6.9,6.8,6.7,6.7,6.7,6.5,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.2,6.2,6.1</td></tr><tr><td>67,7.0,6.9,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.2,6.1</td></tr><tr><td>68,7.0,6.9,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.2,6.2</td></tr><tr><td>69,7.0,6.9,6.7,6.7,6.6,6.6,6.5,6.5,6.5,6.5,6.4,6.4,6.4,6.3,6.3,6.2,6.2</td></tr><tr><td>70,6.9,6.9,6.7,6.7,6.6,6.6,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.3,6.2,6.2</td></tr><tr><td>71,6.9,6.9,6.7,6.7,6.6,6.6,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.3,6.3,6.2</td></tr><tr><td>72,6.9,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.3,6.3,6.2</td></tr><tr><td>73,6.9,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.3,6.3,6.3</td></tr><tr><td>74,6.8,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.4,6.4,6.3,6.3,6.3,6.3</td></tr><tr><td>75,6.8,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.5,6.4,6.3,6.2,6.3,6.3,6.3</td></tr><tr><td>76,6.9,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.5,6.4,6.3,6.2,6.3,6.3,6.3</td></tr><tr><td>77,6.9,6.8,6.8,6.7,6.6,6.5,6.5,6.5,6.5,6.6,6.5,6.4,6.2,6.2,6.2,6.3,6.3</td></tr><tr><td>78,6.9,6.8,6.8,6.7,6.6,6.5,6.5,6.5,6.5,6.6,6.5,6.4,6.2,6.2,6.2,6.3,6.3</td></tr><tr><td>79,6.8,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.6,6.6,6.5,6.4,6.2,6.2,6.2,6.3,6.3</td></tr><tr><td>80,6.7,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.6,6.6,6.5,6.4,6.2,6.2,6.2,6.3,6.3</td></tr><tr><td>81,6.8,6.8,6.7,6.7,6.6,6.5,6.5,6.5,6.6,6.6,6.5,6.4,6.3,6.3,6.3,6.3</td></tr><tr><td>82,6.9,6.8,6.8,6.7,6.6,6.5,6.5,6.5,6.6,6.6,6.5,6.4,6.3,6.3,6.3,6.3</td></tr><tr><td>83,7.0,6.9,6.8,6.7,6.7,6.6,6.5,6.5,6.6,6.6,6.5,6.5,6.3,6.3,6.3,6.4,6.3</td></tr><tr><td>84,7.0,7.0,6.8,6.8,6.7,6.6,6.5,6.6,6.6,6.6,6.5,6.5,6.4,6.4,6.4,6.4</td></tr><tr><td>85,7.0,7.0,6.9,6.8,6.7,6.6,6.5,6.6,6.6,6.6,6.6,6.5,6.4,6.4,6.4,6.4</td></tr><tr><td>86,6.9,7.0,7.0,6.8,6.8,6.6,6.6,6.6,6.6,6.7,6.6,6.5,6.5,6.5,6.5,6.5</td></tr><tr><td>87,7.0,7.0,7.0,6.9,6.8,6.7,6.6,6.6,6.7,6.7,6.6,6.5,6.5,6.5,6.5,6.5</td></tr><tr><td>88,7.1,7.1,7.0,6.9,6.8,6.8,6.6,6.6,6.7,6.7,6.6,6.6,6.6,6.6,6.6,6.5</td></tr><tr><td>89,7.0,7.1,7.1,7.0,6.9,6.8,6.7,6.7,6.7,6.7,6.6,6.6,6.6,6.7,6.7,6.6</td></tr><tr><td>90,7.0,7.0,7.1,7.0,6.9,6.8,6.7,6.7,6.7,6.7,6.6,6.7,6.7,6.7,6.7</td></tr><tr><td>91,7.1,7.1,7.2,7.1,7.0,6.9,6.8,6.7,6.7,6.7,6.7,6.7,6.7,6.8,6.8</td></tr><tr><td>92,7.1,7.2,7.2,7.2,7.1,6.9,6.8,6.8,6.7,6.8,6.7,6.8,6.8,6.8,6.8</td></tr><tr><td>93,7.2,7.2,7.2,7.2,7.1,7.0,6.9,6.8,6.8,6.8,6.8,6.8,6.8,6.8,6.9</td></tr><tr><td>94,7.1,7.2,7.2,7.2,7.2,7.0,6.9,6.9,6.9,6.9,6.9,6.9,6.9,7.0,6.9</td></tr><tr><td>95,7.2,7.2,7.2,7.2,7.2,7.1,7.0,7.0,6.9,6.9,6.9,6.9,7.0,7.0</td></tr><tr><td>96,7.3,7.2,7.3,7.3,7.3,7.2,7.1,7.0,7.0,7.0,6.9</td></tr><tr><td>97,7.4,7.3,7.3,7.3,7.3,7.2,7.1,7.1,7.0,7.0,7.0,7.1,7.1</td></tr><tr><td>98,7.5,7.3,7.3,7.3,7.3,7.3,7.2,7.1,7.1,7.1,7.1,7.1</td></tr><tr><td>99,7.5,7.3,7.3,7.3,7.4,7.3,7.2,7.2,7.2,7.1,7.1,7.2,7.2</td></tr><tr><td>100,7.3,7.3,7.3,7.4,7.4,7.3,7.2,7.2,7.2,7.2,7.2</td></tr></table>

## mB\_BB – broadband body-wave magnitude

$$
m B \_ B B = \log_ {1 0} (V _ {\max} / 2 \pi) + Q (\Delta , h) - 3. 0 \tag {6}
$$

where:

V<sub>max</sub> = ground velocity in nm/s associated with the maximum trace-amplitude in the entire P-phase train (time spanned by P, pP, sP, and possibly PcP and their codas, but ending preferably before PP), as recorded on a vertical-component seismogram that is proportional to velocity, where the period of the measured phase, T, should satisfy the condition $0 . 2 \ \mathrm { s } < T < 3 0$ s, and where T should be preserved together with $V _ { m a x }$ in bulletin data-bases;

Q( , h) = attenuation function for PZ established by Gutenberg and Richter (1956), (Table 2);

= epicentral distance in degrees, $2 0 ^ { \circ } \leq \Delta \leq 1 0 0 ^ { \circ }$

h = focal depth in km.

Equation (6) differs from the equation for $m _ { B }$ of Gutenberg and Richter (1956) by virtue of the $\log _ { 1 0 } ( V _ { m a x } / 2 \pi )$ term, which replaces the classical $\log _ { 1 0 } ( A T \ ) _ { \mathrm { m a x } }$ term.

Mw – moment magnitude

$$
(7 \mathrm{a}) M w = (\log_ {1 0} M _ {0} - 9. 1) / 1. 5,
$$

where $M _ { O } = \mathrm { s c a l a r }$ moment in N·m, determined from waveform modeling or from the long-period asymptote of spectra.

or its CGS equivalent $( M _ { O }$ in dyne cm),

$$
(7 \mathrm{b}) M w = \cdot (\log_ {1 0} M _ {0} - 1 6. 1) / 1. 5.
$$

mb\_Lg– regional magnitude based on the amplitude of Lg measured in a narrow period range around 1 s.

$$
(8) m b \_ L g = \log_ {1 0} (A) + 0. 8 3 3 \log_ {1 0} [ r ] + 0. 4 3 4 3 \gamma (r - 1 0) - 0. 8 7
$$

where:

$A = ^ { \circ \circ }$ “sustained ground-motion amplitude” in nm, defined as the third largest amplitude in the time window corresponding to group velocities of 3.6 to 3.2 km/s, in the period (T) range 0.7 s to 1.3 s;

r = epicentral distance in km

= coefficient of attenuation in $\mathrm { k m } ^ { - 1 }$ . is related to the quality factor Q through the equation $\gamma = \pi / ( Q \cdot U \cdot T )$ , where U is group velocity and T is the wave period of the $\mathrm { L _ { g } }$ wave. is a strong function of crustal structure and should be determined specifically for the region in which the mb $\_ L g$ is to be used.

A and T are measured on output from a vertical-component instrument that is filtered so that the frequency response of the seismograph/filter system replicates that of a WWSSN short-period seismograph. Arrival times with respect to the origin-time of the seismic disturbance are used, along with epicentral distance, to compute group velocity U.

## MAGNITUDE NOMENCLATURE

The “ML, Ms\_20, Ms\_BB, mb, mB\_BB, Mw, mb\_Lg” nomenclature used in this document is defined to facilitate data transmission in the IASPEI Seismic Format (ISF) (International Seismological Centre, 2008, http://www.isc.ac.uk/doc/code/isf/isf.pdf). In the ISF format, magnitude nomenclature is restricted to five characters. The recommended magnitude nomenclature is intended to be consistent with nomenclature that has been used by editorial boards of the Bulletin of the Seismological Society of America, except that the recommended nomenclature does not subscript characters and uses a hyphen in place of parentheses in order to reduce character count. The representation of the magnitude names in italics is for the purpose of distinguishing nomenclature from regular text in this article; we do not consider italics an element of nomenclature. The recommended nomenclature differs from other widely used current nomenclatures. Relationships between nomenclatures are illustrated in Table 3.

<table><tr><td>This report</td><td>BSSA editorial style</td><td>NMSOP generic</td><td>NMSOP specific</td><td>USGS Search</td><td>USGS EDR</td><td>ISC</td></tr><tr><td>ML</td><td> $M_L$ </td><td>Ml</td><td>MH(WA;CF), MV(WA;CF)</td><td>ML</td><td>ML</td><td> $M_L$ </td></tr><tr><td>Ms_20</td><td> $M_S(20)$ </td><td>Ms</td><td>MLV(B)</td><td>Ms</td><td>MSZ</td><td>Ms</td></tr><tr><td>Ms_BB</td><td> $M_S(BB)$ </td><td>Ms</td><td>MLV(D)</td><td>--</td><td>--</td><td>Ms</td></tr><tr><td>mb</td><td> $m_b$ </td><td>mb</td><td>MPV(A)</td><td>mb</td><td>MB</td><td>Mb</td></tr><tr><td>mB_BB</td><td> $m_B(BB)$ </td><td>mB</td><td>MPV(D)</td><td>--</td><td>--</td><td>mB</td></tr><tr><td>mb_Lg</td><td> $m_b(L_g)$ </td><td>mbLg</td><td>MLgV(A;Author)</td><td>Lg</td><td>LG</td><td>MN</td></tr></table>

Table 3. A sample of alternative nomenclatures for the magnitude types that are considered in this report. “BSSA editorial style” is the nomenclature that seems to us most representative of style recommended in recent decades by editors of the Bulletin of the Seismological Society of America. “NMSOP generic” and “NMSOP specific” are respectively the “generic” and “specific” nomenclature used in the first edition of the IASPEI New Manual of Seismological Observatory Practice (Bormann , 2002a, 2002b). In the specific nomenclature the general magnitude symbol M is followed by the symbol of the seismic phase and then by the symbol of the component (V – vertical; H – horizontal) on which amplitude is measured. Then the first letter(s) in brackets stand(s) for the instrument type on which magnitude is measured: e.g., A – WWSSN-SP, B-WWSSN-LP, D – velocity broadband, WA – Wood Anderson. Further symbols/names stand for specific calibration functions used, e.g., “CF” for California and “Author” for author- or agency specific calibration function. “USGS Search” is the nomenclature used by the USGS/NEIC in its Earthquake Catalog Search (http://neic.usgs.gov/neis/epic/). “USGS EDR” is the nomenclature used by the USGS/NEIC in its on-line machinereadable Earthquake Data Reports (ftp://hazards.cr.usgs.gov/edr/). “ISC” is the nomenclature used by the International Seismological Centre.

In conjunction with the full-fledged implementation of the new IASPEI standards, the WG encourages seismological agencies to work toward harmonizing their nomenclatures in order to minimize misunderstanding on the side of data users and to better guide users search for standard magnitude data.

## NOMENCLATURE FOR AMPLITUDES, PERIODS, AND AMPLITUDE-MEASUREMENT TIMES

The ISF (IASPEI Seismic Format) data-exchange format that was discussed in the previous section allows for data lines (the ARRIVAL data type) to convey stationspecific magnitude data. The amplitude, period, and amplitude-measurement time that is associated with a single magnitude measurement is transmitted on a single line, along with the calculated station-magnitude value. A “phase name” (Table 4) must generally be associated with the data.

<table><tr><td>Magnitude type</td><td>Phase Name</td></tr><tr><td>ML</td><td>IAML</td></tr><tr><td>Ms_20</td><td>IAMs_20</td></tr><tr><td>Ms_BB</td><td>IVMs_BB</td></tr><tr><td>mb</td><td>IAmb</td></tr><tr><td>mB_BB</td><td>IVmB_BB</td></tr><tr><td>mb_Lg</td><td>IAmb_Lg</td></tr></table>

Table 4. Phase names to be used for transmittal of amplitudes, periods, and amplitudemeasurement times for the standard magnitude types considered in this paper. “I” stands for “International” or “IASPEI”, “A” for displacement amplitude, and $\Im ^ { \Im }$ for velocity amplitude.

# AGENCY-SPECIFIC CIRCUMSTANCES THAT MAY LEAD TO MODIFICATION OF STANDARD PROCEDURES

The IASPEI Standard Procedures are proposed for implementation by seismological agencies in general. Adoption of the Standard Procedures by an agency will make that agency’s magnitudes more useful to global seismological research and will enable the agency to directly compare its own results with IASPEI standard magnitudes produced by other agencies. The Magnitude WG recognizes, however, that agency-specific circumstances may make it desirable for individual agencies to use procedures that differ from the Standard Procedures. In this case, agency documentation and agency-produced bulletins should contain sufficient information to allow a user to understand how the agency’s magnitudes can be related to magnitudes produced by the Standard Procedures. For situations in which data demand modifications to the attenuation equations that are specified in the Standard Procedures, we recommend the practice that has been followed in the historic development of magnitude scales: the current standard equations are to be used as baselines for defining otherwise arbitrary constants in the improved equations. An agency magnitude-type that is commonly, or in certain magnitude ranges, biased by more than 0.1 magnitude unit with respect to the magnitude produced by an IASPEI Standard Procedure should be identified by nomenclature that is distinct from the IASPEI magnitude nomenclature.

## DOCUMENTATION OF STATION/AGENCY MAGNITUDE PROCEDURES

Documentation of procedures for amplitude/period based magnitudes by seismographic stations/analysis centers should generally address the following points:

1. Phase-type from which the amplitude measurement is made.

2. Units of the reported amplitude. Specify if amplitudes are reported in units of trace-amplitude motion instead of ground motion.

3. Time-window in which the amplitude measurement is made.

a. For example, a flexible time-interval between the P onset and the PP onset or a fixed time window after the first P onset (e.g. 5 s, 10s or other). b. For example, the time-interval spanned by waves having group-velocities between 3.2 and 3.8 km/s.

4. Amplitude-response, filter characteristics, or transfer-function of the seismograph or simulated seismograph through which the amplitude measurement is made.

5. Orientation of seismograph (horizontal or vertical) from which the measurement is made.

6. Details of measuring amplitude

a. For example, does the amplitude correspond to 0.5\*(peak-to-trough amplitude), where “peak-to-trough amplitude” corresponds to difference between a maximum positive excursion and a maximum negative excursion of the trace, or is the amplitude instead measured as the maximum absolute excursion from the “zero” position of the seismograph trace?

b. For example, if the amplitude corresponds to 0.5\*(peak-to-trough amplitude), are the “peak” and “trough” respectively the absolute maximum and absolute minimum values of the entire wave-group, or are they the adjacent peak and trough corresponding to the maximum trace excursion that is associated with a single zerocrossing?

c. For example, are displacement amplitude(A) and period(T) measured at the time of maximum A or at the time of the maximum of the quotient (A/T)?

d. For example, any way in which station/agency procedure differs from the corresponding IASPEI standard procedure

7. Details of measuring period. For example, is it the period the time between the neighboring peaks, respectively troughs or twice the time span measured between the largest peak and adjacent trough at which the double amplitude has been measured, or is it estimated by yet another procedure.

8. To what part of a phase the amplitude-measurement time refers. For example, is the amplitude-measurement time the time of the zero-crossing associated with a peakto-adjacent trough measurement or is it the time of an absolute maximum or absolute minimum?

9. The equations that are used for calculating particular types of magnitudes a. Specify if distance is measured as epicentral distance or hypocentral distance. b Specify the distance range for which the equation is applied

c. Specify restrictions on hypocentral focal-depth, if any

10. Other restrictions on the calculation of the magnitude a. For example, must signal-amplitude satisfy a signal-to-noise ratio criterion? b. For example, is the magnitude measured only for earthquakes of a certain size, as defined by an independent measure of earthquake size?

11. Any way in which the magnitude procedure departs from an IASPEI standard procedure if the procedure is intended to produce the IASPEI standard magnitude.

a. For example, if measurements are made over a somewhat different distance or depth range than specified in the IASPEI procedure. b. For example, if non-standard filtering is applied in some situations in which the non-standard filtering is not expected to affect the magnitude (e.g., when measuring magnitudes for very small events for which standard-filtering would produce records of too small signal-to-noise ratio).

12. How data are averaged for a network average. a. For example, is the network average a simple arithmetic mean, a trimmed mean, the median value, or some other average? b. If, as for example might be the case for ML, data from each of two horizontal components at a single station are used, are data from each component treated as a separate observation in the network average, or are the two components first averaged into a station magnitude, which is then treated as a single observation in the network average?

For some magnitude types (e.g., coda-based magnitudes) the procedures to be documented will have to be substantially altered from the preceding to better reflect the measurements that are critical to those magnitude-types, but the level of detail should be analogous to what is proposed above for amplitude/period based magnitudes.

## REFERENCES

Bormann, P. (2002a). Magnitude of seismic events (Section 3.2, in P. Bormann (Editor), New Manual of Seismological Observatory Practice (NMSOP), GeoForschungs Zentrum Potsdam, Volume 1, Chapter 3, p. 16-49.

Bormann, P. (2002b). DS 3.1, Magnitude calibration functions and complementary data, in P. Bormann (Editor), New Manual of Seismological Observatory Practice (NMSOP), GeoForschungs Zentrum Potsdam, Volume 2, 8pp.

Gutenberg, B., and C. F. Richter (1956). Magnitude and energy of earthquakes. Annali di Geofisica, 9, 1-15.

Herak, M., G. Panza, and G. Costa (2001). Theoretical and observed depth corrections for Ms. Pure Appl. Geophys., 158, 1517-1530.

Hutton, L.K. and D.M. Boore (1987). The M scale in southern California, Bull. Seism. Soc. Am., 77, 2074-2094.

Richter, C. F. (1935). An instrumental earthquake magnitude scale, Bull. Seism. Soc. Am., 25, 1-32.

Uhrhammer, R.A. and E.R. Collins (1990). Synthesis of Wood-Anderson seismograms from broadband digital records, Bull. Seism. Soc. Am., 80, 702-716.

Vaněk, J., A. Zátopek, V. Kárnik, N. Kondorskaya, Y. Riznichenko, E. Savarenski, S. Solov’ev, and N. Shebalin, 1962, Standardization of magnitude scales, Izv. Acad. Sci. USSR, Geophys. Ser., 153-158 [p. 108-111 in English translation].