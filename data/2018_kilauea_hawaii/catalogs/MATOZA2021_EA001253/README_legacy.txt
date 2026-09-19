7/30/2025 Robin Matoza; University of California, Santa Barbara

Catalog file HVO1DXC8618_V2.0.txt contains a major revision. 

:: Overview ::
The file includes all 347,446 events, both the successfully relocated events (299,966 events) and the original starting catalog locations.


:: File format ::
The file format closely follows the GrowClust [Trugman & Shearer, 2017] relocated catalog output file format (see section 4.1 of the GrowClust user guide at: https://github.com/dttrugman/GrowClust), but with some minor format differences in column spacing to accommodate the larger numbers required for this dataset.

The fortran 90 fixed format statement used here is: 
(i4, 4i3, f7.3, i10, f10.5, f11.5, f8.3, f6.2, 3i8, 1x, i6, 1x, i6, 1x, i6, 2f6.2, 3f8.3, 2x, f10.5, f11.5, f8.3, 2x, i2)

The catalog contains one line per event and each line has the following 26 columns:

(-) yr, mon, day, hr, min, sec :: relocated origin time [columns 1-6]
(-) eID :: event ID [column 7]
(-) latR, lonR, depR :: relocated latitude, longitude, and depth (decimal degrees and km) [columns 8-10]
(-) mag :: event magnitude [column 11]
(-) qID, cID, nbranch :: event serial ID number, cluster serial ID number, total number of events in this cluster [columns 12–14]
(-) qnpair, qndiffP, qndiffS :: number of event pairs, P-phase differential times, and S-phase differential times used to relocate this event [columns 15-17]
(-) rmsP, rmsS :: RMS residual differential times for this event for P- and S-phases (sec) [columns 18-19]
(-) eh, ez, et :: estimated location errors in horizontal (km), vertical (km), and origin time (sec) (-1.000 value indicates location error not computed) [columns 20-22]
(-) latC, lonC, depC :: initial (starting catalog) latitude, longitude, and depth (decimal degrees and km) [columns 23-25]
(-) polynum :: polygon number [column 26]
	
Total number of events in file: 347,446
Number of relocated events: 299,966


:: Notes ::

(1) Events that were not successfully relocated and retain their starting catalog locations can be identified as having values of nbranch = 1 [column 14]. Relocated events have values of nbranch [column 14] greater than 1. 

The relocated events can be parsed from the catalog file with, for example:

awk '{if($14 != 1) print $0}' HVO1DXC8618_V2.0.txt > ! HVO1DXC8618_relocated.txt

(2) Starting catalog locations for all events are given in columns 23-25. For successfully relocated events, columns 8-10 (relocated latitude, longitude, and depth) differ from columns 23-25 (starting latitude, longitude, and depth). For events that were not successfully relocated, columns 8-10 and columns 23-25 are the same.

(3) polynum [column 26] (value 1, 2, or 3) refers to the polygon used to divide initial seismicity for separate processing (see Figure 1a of Matoza et al., 2020). Separate processing was performed for each polygon. Cluster serial ID number cID [column 13] is only unique within a polygon. Thus, to isolate a unique cluster, use both cID [column 13] and polynum [column 26]. e.g., to isolate similar-event cluster #51 from polygon #2:

awk '{if($13==51 && $26==2) print $0}' HVO1DXC8618_V2.0.txt > ! HVO1DXC8618_cid51_poly2.txt

