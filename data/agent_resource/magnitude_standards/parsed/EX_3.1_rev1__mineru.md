<table><tr><td>Exercise</td><td>EX 3.1</td></tr></table>

<table><tr><td>Topic</td><td>Magnitude determinations</td></tr><tr><td>Author</td><td>Peter Bormann (formerly GFZ German Research Centre for Geosciences, 14473 Potsdam, Germany); E-mail: pb65@gmx.net</td></tr><tr><td>Version</td><td>October 2011; DOI: 10.2312/GFZ.NMSOP-2_EX_3.1</td></tr></table>

## 1 Aim

The exercises aim at making you familiar with the measurement of seismic amplitudes and periods in analog and digital records and the determination of related classical magnitude values for local and teleseismic events by using the related procedures and relationships outlined in Chapter 3, and the relevant classical magnitude calibration functions given in DS 3.1. For international measurement standards, recently adopted by IASPEI (2011) for local, regional and teleseismic magnitudes, see IS 3.3 and

http://www.iaspei.org/commissions/CSOI/Summary\_WG-Recommendations\_20110909.pdf. Guidelines and waveform data for an interactive training to measure these standard amplitude, period and magnitudes parameters by using the analysis program SEISAN are given in IS 3.4. This IS will be updated in future when other analysis programs suitable for measuring the standard data become available.

## 2 Procedures

The general relationship

$$
\mathbf {M} = \log (\mathrm{A} / \mathrm{T}) + \sigma (\Delta , \mathrm{h})\tag{1}
$$

is used for magnitude determination, with A – maximum “ground motion” amplitude in µm $( 1 0 ^ { - 6 } \mathrm { m } )$ or nm $\left( 1 0 ^ { - 9 } \mathrm { m } \right)$ , respectively, measured for the considered wave group, T – period of that maximum amplitude in seconds. Examples, how to measure the related trace amplitudes B and period T in seismic records are depicted in Fig. 3.9. Trace amplitudes B have to be divided by the respective magnification Mag(T) of the seismograph at the considered period T in order to get the “ground motion” amplitude in either µm or nm, i.e., A = B/Mag(T).

$\sigma ( \Delta , \mathrm { h } ) = - \log \mathrm { A } _ { \mathrm { o } }$ is the magnitude calibration function where ∆ = epicentral distance and h = source depth. For teleseismic body waves the calibration function is usually termed Q(∆, h), according to Gutenberg and Richter (1956), who published respective calibration values for medium-period vertical as well as horizontal component amplitude readings of P and PP waves and for horizontal component S-wave amplitudes. Another calibration function for short-period vertical component P-wave amplitude readings, termed P(∆, h), has been published by Veith and Clawson (1972). For teleseismic events (distance >1000-2000 km) ∆ is generally given in degree $( 1 ^ { \circ } = 1 1 1 . 1 9 \mathrm { k m } )$ , for local/near regional events (distance usually <1000 km), however, in km. For local events often the “slant range” or hypocentral distance R (in km) is used instead of ∆. All calibration functions used in the exercise are given in DS 3.1.

Note: According to the original definition of the local magnitude scale Ml by Richter (1935) only the maximum trace amplitude B in mm as recorded in standard records of a Wood-Anderson seismometer is measured (see Fig. 3.11 and section 3.2.4), i.e.,

$$
\mathrm{Ml} = \log \mathrm{B} (\mathrm{WA}) - \log \mathrm{A} _ {\mathrm{o}} (\Delta).\tag{2}
$$

Accordingly, no period T is measured, and no conversion to “ground motion” amplitude is made. However, when applying Ml calibration functions to trace amplitudes B measured (in mm too) in records of another seismograph (SM) with a frequency-magnification curve Mag(T) different from that of the Wood-Anderson seismograph (WA) then this frequencydependent difference in magnification has to be corrected. Equation (2) then becomes

$$
\mathrm{Ml} = \log \mathrm{B} (\mathrm{SM}) + \log \operatorname{Mag} (\mathrm{WA}) - \log \operatorname{Mag} (\mathrm{SM}) - \log \mathrm{A} _ {\mathrm{o}}.\tag{3}
$$

## 3 Data

The data used in the exercise are given in the following figures and tables.

![](images/a533eab5674d9277202c3814da08d2c02f5d6b746e623ac471b5445a8715b708.jpg)  
Figure 1 Vertical component records of a local seismic event in Poland at the stations CLL and MOX in Germany at scale 1:1. The magnification values Mag(SM) as a function of period T for this short-period seismograph are given in Table 1 below.

Table 1 Magnification values Mag(SM) as a function of period T in s for the short-period seismograph used for the records in Figure 1 together with the respective values Mag(WA) for the Wood-Anderson standard seismograph for Ml determinations.

<table><tr><td>T (in s)</td><td>Mag(SM)</td><td>Mag(WA)</td><td>T (in s)</td><td>Mag(SM)</td><td>Mag(WA)</td></tr><tr><td>0.1</td><td>35,000</td><td>2,800</td><td>1.1</td><td>190,000</td><td>1,100</td></tr><tr><td>0.2</td><td>92,000</td><td>2,700</td><td>1.2</td><td>180,000</td><td>950</td></tr><tr><td>0.3</td><td>125,000</td><td>2,600</td><td>1.3</td><td>170,000</td><td>850</td></tr><tr><td>0.4</td><td>150,000</td><td>2,400</td><td>1.4</td><td>155,000</td><td>750</td></tr><tr><td>0.5</td><td>170,000</td><td>2,200</td><td>1.5</td><td>140,000</td><td>700</td></tr><tr><td>0.6</td><td>190,000</td><td>2,000</td><td>1.6</td><td>120,000</td><td></td></tr><tr><td>0.7</td><td>200,000</td><td>1,800</td><td>1.7</td><td>90,000</td><td></td></tr><tr><td>0.8</td><td>201,000</td><td>1,600</td><td>1.8</td><td>80,000</td><td></td></tr><tr><td>0.9</td><td>201,000</td><td>1,400</td><td>1.9</td><td>70,000</td><td></td></tr></table>

![](images/af9762b2fd6320771a27e486bf78171efca90ff0b8569406575b4f2cbc353e11.jpg)

<table><tr><td>1.0</td><td>200,000</td><td>1,200</td><td>2.0</td><td>60,000</td><td></td></tr></table>

<table><tr><td>T [s]</td><td>V</td></tr><tr><td>0.3 - 15</td><td>1100</td></tr><tr><td>17</td><td>1000</td></tr><tr><td>18</td><td>950</td></tr><tr><td>19</td><td>900</td></tr><tr><td>20</td><td>820</td></tr><tr><td>22</td><td>700</td></tr><tr><td>24</td><td>550</td></tr><tr><td>26</td><td>400</td></tr></table>

![](images/73dd7d022cd2288d52d82e9a06ebde6a137c241847a92ee5cc5ea2598c0cb074.jpg)

Figure 2 Analog record at scale 1:1 of a Kirnos-type seismograph from a surface-wave group of a teleseismic event. Scale: 1 mm = 4 s; for displacement Mag = V see inserted table.

<table><tr><td colspan="4">O← Seismogram Manipulations HELP Setting Markers → -18↓ Use of F-keys &amp; Commands Routine Analysis ↓</td></tr><tr><td rowspan="2">E</td><td>P</td><td>PP</td><td>S</td></tr><tr><td></td><td></td><td></td></tr><tr><td>N</td><td></td><td></td><td></td></tr><tr><td>Z</td><td></td><td></td><td></td></tr><tr><td colspan="4">MOXLN ONSET ON 21:41:29.801</td></tr></table>

Figure 3 Display of the long-period (10 to 30 s) filtered section of a broadband 3-component record of the Uttarkasi earthquake in India (19 Oct. 1991; h = 10 km) at station MOX in Germany. The record traces are, from top to bottom: E, N, Z. Marked are the positions, from where the computer program has determined automatically the ground displacement amplitudes A and related periods T for the onsets (from left to right) of P, PP and S. For S the respective cycle is shown as a bold trace. The respective values of A and T for all these phases are saved component-wise in the data-pick file. They are reproduced in the box on the right together with the computer picked onset-time difference S - P and the epicentral distance ∆ as published for station MOX by the ISC.

<table><tr><td>O</td><td>← Seismogram Manipulations↓ Use of F-keys &amp; Commands</td><td>HELP Setting Markers →Routine Analysis ↓</td><td>-810T</td><td>A</td></tr><tr><td>E</td><td></td><td></td><td></td><td></td></tr><tr><td>N</td><td></td><td></td><td></td><td></td></tr><tr><td>Z</td><td>P</td><td></td><td></td><td></td></tr><tr><td rowspan="2" colspan="3">MOXSN ONSET ON 21:33:50.201</td><td>Z 2.0 s</td><td>1,300 nm</td></tr><tr><td colspan="2">Δ ≈ 53°</td></tr></table>

Figure 4 As for Figure 3, however short-period (0.5 to 3 Hz) filtered record section of the Pwave group only. Note that the amplitudes are given here in nm $( 1 0 ^ { - 9 } \mathrm { m } )$

## 4 Tasks

## Task 1:

1.1 Identify and mark in the records of Figure 1 the onsets Pn, Pg and Sg. Note that Pn amplitudes are for distances < 400 km usually smaller than that of Pg! Then determine the hypocentral (“slant”) distance R in km from the rule of thumb $\mathrm { \sf t ( S g - P g ) [ s ] } \times 8 = \mathrm { \bf R }$ [km] for both station CLL and MOX. Note, that for this shallow event the epicentral distance ∆ and the hypocentral distance R are practically the same.

1.2 Determine for the stations CLL and MOX the max. trace amplitude B(SM) and related period T and then, according to Equation (3), the equivalent log trace amplitude when recorded with a Wood-Anderson seismometer, i.e., log $\mathrm { { B } ( W A ) = \log \ B ( S M ) \ + \ \log }$ Mag(WA) – log Mag(SM).

1.3 Use Equation (2) above, and the values determined under task 1.2, for determination of the local magnitude Ml for the event in Figure 1 for both station CLL and MOX using the calibration functions –logA<sub>o</sub>:

a) by Richter (1958) for California (see Table 1 in DS 3.1);

b) by Kim (1998) for Eastern North America (vertical comp.; see Table 2 in DS 3.1);

c) by Alsaker et al. (1991) for Norway (vertical comp., see Table 2 in DS 3.1).

1.4 Discuss the differences in terms of:

a) differences in regional attenuation in the three regions from which Ml calibrations functions were used;

b) amplitude differences within a seismic network;

c) uncertainties of period reading in analog records with low time resolution and thus uncertainties in the calculation of the equivalent Wood-Anderson trace amplitude B(WA).

## Task 2:

2.1 Measure the maximum horizontal and vertical trace amplitudes B in mm and related periods in s from the 3-component surface-wave records in Figure 2. Note, that the maximum horizontal component has to be calculated by combining vectorially $\mathtt { B _ { N } }$ and $\mathtt { B _ { E } }$ , measured at the same record time, i.e., ${ \bf B } _ { \mathrm { H } } = \sqrt { ( { \bf B } _ { \mathrm { N } } { } ^ { 2 } + { \bf B } _ { \mathrm { E } } { } ^ { 2 } ) }$

2.2 Calculate the respective maximum ground amplitudes $\mathbf { A } _ { \mathrm { H } }$ and A<sub>V</sub> (in µm; vertical V = Z) by taking into account the period-dependent magnification of the seismograph (see table inserted in Figure 2)

2.3 Calculate the respective surface-wave magnitudes Ms according to the calibration function

a) σ(∆) as published by Richter (1958) (see Table 3 in DS 3.1, for horizontal component H only);

b) σ(∆) as given by the Prague-Moscow formula $\mathrm { M s } = \log ( \mathrm { A } / \mathrm { T } ) _ { \mathrm { m a x } } + 1 . 6 6 \log \Delta + 3 . 3$ (Vanĕk et al., 1962), which has been accepted by IASPEI in 1967 as the standard formula for surface-wave magnitude determinations. Apply it to both the horizontal and the vertical component amplitude and period readings.

Note: Differentiate between surface-wave magnitudes from horizontal and vertical component records by annotating them unambiguously as MLH and MLV, respectively.

## Task 3:

Use the computer determined periods and amplitudes given in the right boxes of Figures 3 and 4 for the body-wave phases P, PP and S recorded from the shallow $( \mathbf { h } \ = \ 1 0 $ km) teleseismic earthquake in India in order to determine the respective body-wave magnitudes according to the general relationship (1):

3.1 Compare the epicentral distance calculated by the ISC for MOX $( \Delta = 5 2 . 7 6 ^ { \circ } )$ with your own quick determination of ∆ using the “rule of thumb” $\Delta { \mathrm { ( i n ~ } ^ { \circ } \mathrm { ) } } = [ \mathrm { t } _ { \mathrm { S - P } } ( \mathrm { i n ~ m i n } ) \cdot 2 ] \times 1 0$

3.2 Compare the differences in Q(∆) according to Table 7 in DS 3.1 when using the “exact” distance given by the ISC with your quick “rule of thumb” estimation of ∆. Assess the influence of the distance error on the magnitude estimate and draw conclusions.

3.3 Calculate MPV, MPH; MPPV, MPPH and MSH using the calibration functions Q(∆) given in Table 7 of DS 3.1, the amplitude-period values given in Figure 3 and $\Delta = 5 3 ^ { \circ }$ Discuss the degree of agreement/disagreement and possible reasons.

3.4 Calculate $\mathrm { m } _ { \mathrm { b } }$ for the short-period P-wave recording in Figure 4 using

a) Q(∆, h) as depicted in Figure 1a of DS 3.1 for the vertical component of P and

b) P(∆, h) as depicted in Figure 2 of DS 3.1.

c) Discuss the difference between a) and b).

## 5 Solutions

Note: Your individual readings of times, periods and amplitudes should not deviate more than 10 % and your magnitude estimates should be within about ± 0.2 units of the values given below.

## Task 1:

![](images/bd0e020f0143feb249447b63deed0ee0be10f7b15adc4230d955ec7332ef9cc0.jpg)

## Exercise

1.1 CLL MOX

$$
\begin{array}{l l} 1. 2 \text {CLL:} & \mathrm{B(MS)} = 1 0 \mathrm{mm} \\ \text {MOX:} & \mathrm{B(MS)} = 1 8 \mathrm{mm} \end{array} \qquad \begin{array}{l l} \mathrm{T} = (0. 5 \mathrm{s?}) & \log \mathrm{B(WA)} = - 0. 8 8 8 \\ \mathrm{T} = 1 \mathrm{s} & \log \mathrm{B(WA)} = - 0. 9 6 7 \end{array}
$$

$$
\begin{array}{l l l l} 1. 3 \text {CLL:} & \mathrm{Ml(Richter)} = 2. 7 & \mathrm{Ml(Kim)} = 2. 6 & \mathrm{Ml(Alsaker)} = 2. 4 \\ \text {MOX:} & \mathrm{Ml(Richter)} = 3. 1 & \mathrm{Ml(Kim)} = 2. 8 & \mathrm{Ml(Alsaker)} = 2. 6 \end{array}
$$

1.5 California is a tectonically younger region and with higher heat flow than Eastern North America and Scandinavia. Accordingly, seismic waves are more strongly attenuated with distance. This has to be compensated by larger magnitude calibration values – logA<sub>o</sub> for California. But even within a seismic network amplitude variations may be, depending on different conditions in local underground and azimuth dependent wave propagation, in the order of a factor 2 to 3 in amplitude, thus accounting for magnitude differences in the order of up to about ± 0.5 magnitude units between the various stations. This scatter can be reduced by determining station corrections for different source regions. Note also, that the period reading is rather uncertain for CLL. If we assume, as for MOX, also T = 1 s then log B(WA) = -1.222, i.e., the magnitudes values for CLL would be even smaller by 0.3 units.

Task 2:

$$
2. 1 \quad \mathrm{B} _ {\mathrm{N}} = 2 0. 5 \mathrm{mm}, \mathrm{T} _ {\mathrm{N}} = 2 2 \mathrm{s}; \mathrm{B} _ {\mathrm{E}} = 1 2 \mathrm{mm}, \mathrm{T} _ {\mathrm{N}} = 2 0 \mathrm{s} \quad \rightarrow \mathrm{B} _ {\mathrm{H}} = 2 3. 8 \mathrm{mm}, \overline {{\mathrm{T}}} = 2 1
$$

$$
\mathrm{B} _ {\mathrm{Z}} = 2 3 \mathrm{mm}, \mathrm{T} _ {\mathrm{Z}} = 1 8 \mathrm{s}
$$

2.2 A<sub>H</sub> = 31.3 µm for T = 21 s A<sub>Z</sub> = A<sub>V</sub> = 24.2 µm for T = 18 s

2.3 a) Ms = MLH(Richter) = log A<sub>Hmax</sub> + σ(∆)<sub>Richter</sub> = 1.5 + 5.15 = 6.65

$$
\begin{array}{r l}\text {b)} \mathrm{Ms} = \log (\mathrm{A} / \mathrm{T}) _ {\max} + 1. 6 6 \log \Delta + 3. 3&\rightarrow \mathrm{Ms} = \mathrm{MLH} = 6. 8 2 \text {and}\\&\quad \mathrm{Ms} = \mathrm{MLV} = 6. 7 8\end{array}
$$

Discussion: For the given record example Ms(Richter, 1958) yields somewhat smaller values than Ms(Vanĕk et al., 1962). The latter formula, although derived for horizontal component surface-wave amplitude readings, yields comparable magnitude values also when applied to vertical component readings (here difference < 0.05 magnitude units).

## Task 3:

3.1 The “rule of thumb” yields $\Delta = 5 4 { , } 5 ^ { \circ }$ . This is only $1 . 7 ^ { \circ }$ off the ISC determination. Generally, the rule-of-thumbs allows to estimate ∆ in the range $2 5 ^ { \circ } < \Delta < 1 0 0 ^ { \circ }$ with an error not larger than ± 2.5°.

3.2 The deviations in Q(∆) and thus between magnitude estimates based on either ∆ values from NEIC/ISC calculations or quick S-P determinations at the individual stations and using the “rule of thumb” are generally less than 0.2 units. They are even smaller, when correct travel-time (difference) curves are available. This permits sufficiently accurate quick teleseismic magnitude estimates at individual stations even with very modest tools and without prior knowledge of the event locations and distance determinations of the world data centers.

$$
3. 3 \mathrm{MPV} = 6. 4 5, \mathrm{MPH} = 6. 3 6, \mathrm{MPPV} = 6. 3 6, \mathrm{MPPH} = 6. 2 4; \mathrm{MSH} = 6. 7 5
$$

The magnitude values for vertical and horizontal component amplitude readings of P and PP, respectively, agree within 0.1 magnitude units. This speaks of a good scaling of the respective $\mathrm { Q } ( \Delta )$ calibration functions. MSH is in the given case significantly larger. This is obviously related to the different azimuthal radiation pattern for P and S waves and was one of the reasons, why Gutenberg strongly recommended the determination of the bodywave magnitudes for all these phases and averaging them to a unified body-wave magnitude value m. The latter provides more stable and less azimuth-dependent individual magnitude estimates.

$$
3. 4 \mathrm{a)} \mathrm{Q} _ {\mathrm{PZ}} (5 3 ^ {\circ}, 1 0 \mathrm{km}) = 7. 0, \log (\mathrm{A} / \mathrm{T}) = - 0. 1 9 (\text {with A in \mu m!}) \rightarrow \mathrm{MPV} = \mathrm{mb} = 6. 8
$$

$$
\mathrm{b)} \quad \mathrm{P} _ {\mathrm{Z}} (5 3 ^ {\circ}; 1 0 \mathrm{km}) = 3. 4, \log (\mathrm{A} / \mathrm{T}) = 3. 1 (\text {with 2A in nm!}) \rightarrow \mathrm{MPV} = \mathrm{mb} = 6. 5
$$

c) ${ \mathrm { P } } _ { Z } ( \Delta ,$ h) yields, for the same ratio log(A/T), slightly lower magnitude values as compared to $\mathrm { Q } _ { \mathrm { P Z } } ( \Delta , \ \mathrm { h } )$ , for deep events, in particular. This also applies for other distance ranges (see Figures 1a and 2 in DS 3.1). Note that $\mathrm { P } _ { \mathrm { Z } , }$ although specifically developed for the calibration of short-period P-wave amplitudes, is not yet a recommended standard calibration functions.

## References

Alsaker, A., Kvamme, L. B., Hansen, R. A., Dahle, A., and Bungum, H. (1991). The $\mathbf { M } _ { \mathrm { L } }$ scale in Norway. Bull. Seism. Soc. Am., 81, 2, 379-389.

IASPEI (2011). Summary of Magnitude Working Group recommendations on standard procedures for determining earthquake magnitudes from digital data. Preliminary version October 2005, updated version September 2011; http://www.iaspei.org/commissions/CSOI/Summary\_WG-Recommendations\_20110909.pdf.

Gutenberg, B., and Richter, C. F. (1956). Magnitude and energy of earthquakes. Annali di Geofisica, 9, 1-15.

Kim, W.-Y. (1998). The M<sub>L</sub> scale in Eastern North America. Bull. Seism. Soc. Am., 88, 4, 935-951.

Richter, C. F. (1935). An instrumental earthquake magnitude scale. Bull. Seism. Soc. Am., 25, 1-32.

Richter, C. F. (1958). Elementary seismology. W. H. Freeman and Company, San Francisco and London, viii + 768 pp.

Vanĕk, J., Zapotek, A., Karnik, V., Kondorskaya, N.V., Riznichenko, Yu.V., Savarensky, E.F., Solov’yov, S.L., and Shebalin, N.V. (1962). Standardization of magnitude scales. Izvestiya Akad. SSSR., Ser. Geofiz., 2, 153-158.

Veith, K. F., and Clawson, G. E. (1972). Magnitude from short-period P-wave data. Bull. Seism. Soc. Am., 62, 435-452.