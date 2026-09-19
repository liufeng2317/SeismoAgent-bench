This README describes the file KSCLP1DXC_V1.0

The file KSCLP1DXC_V1.0 contains locations for LP events beneath the Kilauea Summit Caldera using a 1D velocity model and waveform cross-correlation, as described by:

Matoza, R.S., P.M. Shearer, and P.G. Okubo (2014), High-precision relocation of long-period events beneath the summit region of Kilauea Volcano, Hawai`i, from 1986 to 2009, Geophys. Res. Lett., 41, doi:10.1002/2014GL059819

The file includes all 12,290 events classified by Matoza et al. as LP based on station-averaged frequency index, both the successfully relocated events (relocation flag=1) and the original CUSP catalog locations for the subset of events that did not correlate and were not relocated (relocation flag=0).

Using the first line as an example, the format is as follows:
1986  1  2 11 52 25.510    206290  19.43340 -155.33479   2.330  1.20 B      0     0 -99.000 -99.000 0

1986        :: year
1           :: month
2           :: day
11          :: hour
52          :: minute
25.510      :: second
206290      :: unique cuspid number
19.43340    :: latitude
-155.33479  :: longitude
2.330       :: depth (km)
1.20        :: CUSP system assigned magnitude (0.00 if unassigned)
B           :: initial CUSP catalog location quality (A, B, C, D), X=not assigned
0           :: event cluster identification number (0 if the event was not relocated)
0           :: number of events in the cluster (0 if the event was not relocated)
-99.000     :: estimated standard error (km) in horizontal position relative to other events in the cluster (-99.000 if event standard error not calculated)
-99.000     :: estimated standard error (km) in vertical position relative to other events in the cluster  (-99.000 if event standard error not calculated)
0           :: relocation flag (0 = original CUSP catalog location; 1 = event relocated)

A Fortran 90 format statement for this is: 	
format (i4,4i3,f7.3,i10,f10.5,f11.5,f8.3,f6.2,1x,a1,1x,i6,i6,2f8.3,i2)

Total number of events in file: 12,290
Number of LP events relocated: 5,199
Number of LP events retaining their original CUSP catalog locations: 7,091
