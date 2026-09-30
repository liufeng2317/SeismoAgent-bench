## Earthquake Catalog: Quality Control (QC)

• I created a custom (deep-learning) enhanced earthquake catalog automatically. How good is it?

• No ground truth available

• Before using or interpreting your enhanced catalog, do this first:

• Compare with a reference catalog

• Data visualization (make plots!) to check for quality

## What is a reference catalog?

• Authoritative, high-quality earthquake catalog for a region

• Good baseline for comparison: manually reviewed, meets performance standards

• United States: Comprehensive Catalog (ComCat), complete to M2.5-3.0, https://earthquake.usgs.gov/earthquakes/search/ , https://earthquake.usgs.gov/data/comcat/

• International: ComCat is complete to M4.5 globally. For more complete catalogs, refer to the country/region's authoritative monitoring website.

• Turkey: https://deprem.afad.gov.tr/event-catalog

• New Zealand: https://quakesearch.geonet.org.nz/

• Italy: https://terremoti.ingv.it/bsi

Event comparison: reference catalog vs. enhanced catalog (Need locations) (small circle) (big circle)

MISSED events (only in reference catalog)

Manually detected and/or picked by analysts

Check why they were missed (esp. larger events?)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c7971792674c51342f7d8737d8aa2894548a5790e695a1720f47270b738d6277.jpg)

MATCH events (common to both catalogs)

Origin times match within X\~5 seconds

Hypocenters match within Y\~25 km (only in enhanced catalog)

Newly detected small local earthquakes? �

False detections from noise? ☹

Other signals (quarry blasts, sonic booms, explosions)? �

Regional or teleseismic earthquakes? �

Date

## Event comparison example: SW Puerto Rico sequence

Yoon et al. (2023), BSSA

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/72e42c413a3f7cfa66af37d2945c9a57677f21bf5ddfe655771bbd0be71e2758.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/38d5a466b7683337863369f4e41531af330b7dd48b6b8bfe4cc68a33371a60b4.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/92d7e00e14e1f8348448af8e93b2d370c678f8ba4cb845fb6c42d2d2055cd579.jpg)

Times with many missed ComCat earthquakes: PRSN\* analyst review complete  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/cdd33e54a4d54d4fff26fb00af3ee00e61c5fb1d66fdd7d77a057bbfbca5c877.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/394c43ff4d4f45936e2a90bb50153ae593b4aaf43fc7c0179685555561b3b318.jpg)  
\*PRSN: Puerto Rico Seismic Network  
2021-01-01  
2022-12-01

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/d7b311ee66276660a669839055751b328c3dcde9dd92598cc0cdcc1bfd8447b7.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/ad17c397d3d7d9ba6401ee7f13db410df00a8750476c59161f6ff5b142d1cd36.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/a453ac4439f7e954d2921943bf831fd59afab865689a568486ac0bf18e9cd7af.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/fdd3d10340749b5765edfd528401250097400df3f55f61086ddc76a314771fff.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/1ca6aa1c9e6695d650c717e7879537c4d10161042b36f3a52df0efe7ba7d8c6c.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/6538740eb7635c36e00eccf9208822560f324c1845ac4680189170973e9cafa5.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/fe59a79be101aa6fe0f6ce5a801a437b6be59f47f6e7913506d8fde133429432.jpg)

## MATCH events: location, magnitude comparison

Horizontal axis: ComCat (reference catalog) Vertical axis: Enhanced catalog 5

## MATCH events: Pick time comparison for each station

à residual histograms

EQTransformer on Puerto Rico seismic data: less accurate pick times than Mousavi et al. (2020) on STEAD test dataset … but good enough for automatic catalog workflow

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/0d1d5737ed2d745173d5b4fc56f15e1edb3e7ca044d447b075aa6cf3bb4bffa9.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/b2540b75776fccc36ceed18c73cd1ea06bf67789d12c2d62b5bd9d6cfd17e5ea.jpg)

EQT pick quality (number of picks, pick accuracy) degrades with increasing event-station distance

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/777338c34f6790e42cfbbb3ac06e27c183991100e333dd9ebbe31aaad675835e.jpg)

In practice: use only picks out to a maximum distance (\~100 km?) for location

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/89c2fd946c5c3a222ee1bdbd54bbcae7bc56a12afa037b2386e71dc2f26cc7cd.jpg)

## Reference Catalog Tip: Select boundaries carefully Example: Mendocino Triple Junction, CA

Region big enough: includes most seismicity and all stations used

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7b150cdfee58b876db2f81e1d47b4aae060ed00934930c2ff71d0c74d6eaddf2.jpg)

Yoon and Shelly (2024), TSR

Region too small: missing some regions with seismicity; not all stations

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7f1dfdec776c4277f3184d2225d96046e1509179d61924e847ff29bba3a577bd.jpg)

## Reference Catalog Tip: It changes over time

• Reference catalog changes over time due to analyst review

• New or deleted events; updated location/magnitude for existing events

• Expect frequent changes to catalog: hours to days after large earthquake

• Complete analyst review for active aftershock sequence: months to years

• July 2019 M7.1 Ridgecrest CA sequence

• 2019-07-07: 45% complete, 2019-07-08 to 2019-07-31: <10% complete each day

Catalog processing status (updated daily): https://service.scedc.caltech.edu/ftp/catalogs/catalog\_status/

Times with many missed ComCat earthquakes: PRSN\* analyst review complete (back in 2023)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/538171d9c5a7917d68f8ab8c8a240099be22bc2a6f7010012adcfe45f9f54da3.jpg)

## Reference Catalog Tip: It changes over time

• Save the reference catalog file itself, with filename including the date you downloaded it.

• When reference catalog changes in the future, you still have the original version, so you can easily reproduce your results.

## Earthquake Catalog: Quality Control (QC)

• I created a custom (deep-learning) enhanced earthquake catalog automatically. How good is it?

• No ground truth available

• Before using or interpreting your enhanced catalog, do this first:

Compare with a reference catalog

• Data visualization (make plots!) to check for quality

## Catalog QC: Most false detections drop out at each step of automatic workflow, but not all.

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/3e1d6b791fc34eb9ba45c5c7639fa519009d4a518ea0008a8da5949fb5372c62.jpg)

Few false detections at this stage

final earthquake catalog

No false detections (hopefully)

## Earthquake Catalog QC: Think like an analyst

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/6788adc17e9b7669a4efce6d531d95e223c0d94680a2674d5036627979bea9dc.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/27042ccab8deab63e070b0d1e55ae99e2ab95f2e94101379686af78efca8c587.jpg)

## AQMS Jiggle manual review and picking interface at SCSN

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/a6bb5bbfccb371b15501349e783ae3a3a8990574a9e72755a955dd58380148dd.jpg)

## Earthquake Catalog QC Tips: Check Parameters

• Compare enhanced catalog with reference catalog on plots

• Plot reference & enhanced catalogs side-by-side

• Separate plots for MATCH, NEW, MISSED category events

• Visualize enhanced catalog à are results reasonable for earthquakes?

• Locations (epicenters) in map view

• Are events near known seismogenic areas, past seismicity, faults? Known quarries?

• Depth cross-sections

• Are events at expected seismogenic depths (0-30 km, unless in subduction zone)?

• Magnitude-frequency distribution

• Do event magnitudes follow Gutenberg-Richter distribution (lots of small events)?

• Magnitude vs. time, Seismicity rate (number of events vs. time)

• If aftershock sequence, does number of events decrease as 1/time after mainshock (Omori decay)?

Enhanced catalog: events are on known faults with active seismicity

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7a82ee24ebaff4e70cc9ab33a6c2c56b1a5b6489365106124bc0159bf3dd695b.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/a925edd63ac67d1ff075d7ef3944653222080a1db7554b8ba5334379c78c00a2.jpg)

## Catalog QC, zoomed locations in map view & depth cross-section: SCSN 2020-09-30 00:00:00 UTC to 2020-10-01 00:00:00 UTC (24 hours)

Enhanced catalog: Similar epicenters. Larger range of depths, but still reasonable

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/cc0a3b50cf482fd4be91269d64dee968c2edcedf2c2e8994626676932c8f8e51.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f585f72541a477c881e577daab973931ac842c0eddffcfd057f2c060851b6e57.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/5cd5912aad109f411cf680cb62bd5dbac7b9c0d698e3368f71dadf6f57d91312.jpg)  
Reference catalog: SCSN/ComCat (manually reviewed)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7ab8ac9da03a4ec8f61f7d4e1e35ebf225518c5dc0ebb5ca5f6be7e78c6b004a.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/21f75054678092df1a09b090115825b6a81d315900981a54897cf36cd0d56f92.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f85d76943810fd74ff87298918a50ff2a51b84f2aa418ebd2107700c4baef259.jpg)  
Enhanced catalog (automatic)

Ridgecrest first 3 days $( \mathsf { M } _ { \mathsf { w } } 6 . 4 \& 7 . 1$ , aftershocks), enhanced catalog: association errors à false detections with bad locations/magnitudes

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/e2d3a07e7906dd312d683b33d5400baa151d240b71ebc7ccbbef0bb10034d09d.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/e754a2eac4ced4a5bf9761c8bdbcb79f714d861865f007701f25ad06fb2b75f4.jpg)

## Earthquake Catalog QC Tips: Check Parameters

• Compare enhanced catalog with reference catalog on plots

• Plot reference & enhanced catalogs side-by-side

• Separate plots for MATCH, NEW, MISSED category events

## • Visualize enhanced catalog à are results reasonable for earthquakes?

• Locations (epicenters) in map view

• Are events near known seismogenic areas, past seismicity, faults? Known quarries?

• Depth cross-sections

• Are events at expected seismogenic depths (0-30 km, unless in subduction zone)?

• Magnitude-frequency distribution

• Do event magnitudes follow Gutenberg-Richter distribution (lots of small events)?

• Magnitude vs. time, Seismicity rate (number of events vs. time)

• If aftershock sequence, does number of events decrease as 1/time after mainshock (Omori decay)?

Magnitude-frequency distribution (MFD)

## Catalog QC: Puerto Rico

MATCH, MISSED, NEW

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/9d448b3cf53aeead6f925f7954791bc7de49a94ed090c17d5336b01675c9180b.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c1be0b6ff956e9838a4b0768f9057a837286160509204c8b84815503270293e4.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/5c475e6b60a283e13171d234618b00751ac39aef1e4a775cdd0434961eb538c0.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/21d7a447077493fcfbb0c99f2cc29b677fd5f7e86ef6a5f6dbc7e5941611ca92.jpg)

# Earthquake Catalog QC Tips: Check Waveforms

## • When in doubt, plot event waveforms

• Overlay picks on event waveforms, ordered by event-station distance, especially for “NEW” events not in reference catalog

• Earthquake or noise?

• Distance from event to nearest station?

• Frequency content & time duration – local, regional, or teleseismic earthquake? Quarry blast?

Moveout (from P, S pick times) & attenuation (from amplitudes) with distance?

• Do actual picks match predicted arrival times (from ray-tracing through velocity model)?

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/73ca8c26423204ac07114a4fa8b576052916a358d1b9f87189ad93974fa4f905.jpg)

## Check “NEW” events in enhanced catalog, not in reference catalog Sorted by magnitude (Southwest Puerto Rico)

<table><tr><td>Origin time (UTC)</td><td>OT (seconds)</td><td>Latitude</td><td>Longitude</td><td>Depth</td><td>Magnitude</td><td>EventID</td></tr><tr><td>2020-01-07T08:35:15.030000</td><td>30915.030000</td><td>17.871833</td><td>-66.721667</td><td>6.420000</td><td>4.320000</td><td>1000335</td></tr><tr><td>2020-01-07T11:21:01.620000</td><td>40861.620000</td><td>18.034167</td><td>-66.800000</td><td>13.780000</td><td>4.360000</td><td>1000569</td></tr><tr><td>2020-01-07T08:29:18.320000</td><td>30558.320000</td><td>18.139667</td><td>-66.810000</td><td>7.660000</td><td>4.440000</td><td>1000328</td></tr><tr><td>2020-01-07T08:29:36.930000</td><td>30576.930000</td><td>17.963500</td><td>-66.752333</td><td>29.160000</td><td>4.480000</td><td>1000330</td></tr><tr><td>2020-01-07T08:51:09.400000</td><td>31869.400000</td><td>17.676333</td><td>-66.773667</td><td>27.610000</td><td>4.760000</td><td>1000356</td></tr></table>

## Catalog QC: False detection in coda of larger earthquake (also, too deep?)

2020-01-07T08:51:09.400000 31869.400000 17.676333 -66.773667 27.610000 4.760000

Earthquake 2020-01-07 08:51:09.396302640 +/- 0.50s Hyp=[-66.77,17.68,27.61]- Hyp Uncertainty (km) +/- [0.35,0.84,1.97]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/49d5706ac0f1d9056aeeb08c9ee63dc446105055a13ee0546a1aaca845f3bcef.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/1b38869d443cab46d6b3151e85f7aae7589aed1674be13213c32e7ac5a51025c.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/6a901383684e5d78546e97d61a11d24bc408c0b1b34359ad21bdff5e9de111c2.jpg)

1000356

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c99325ce916136a5520bd95b91bc7e48f20dd24476298d50ad8378c4d1b25d7b.jpg)

Event waveforms with P, S picks

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/b957b51d7ec6994fef74986cea2b1ac76cd0a288830d390b97581375880532b7.jpg)

Earthquake 2020-01-07 08:35:15.029341138 +/- 0.05s Hyp=[-66.72,17.87,6.42]- Hyp Uncertainty (km) +/- [4.13,1.33,2.41]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/90c06ec1c8dd7d4f2dd80eb18163aec5510de3d05e9990bf75bdbcccd058a4b4.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/27a39d538e31ae9d9201447832b8702e387ddcd1b6107a646c2805cd69aa7475.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/3620af19bbc0639f648629dbd6ff5d99576a7dfd1051ca1c5ca384746516667d.jpg)

Event waveforms with P, S picks

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/5875189058d93351ff30dc0b946f6fc8a590c2d18a3bd27df4aaa816c2b7f408.jpg)

<table><tr><td>Origin time (UTC)</td><td>OT (seconds)</td><td>Latitude</td><td>Longitude</td><td>Depth</td><td>Magnitude</td><td>EventID</td></tr><tr><td>2020-01-07T16:19:28.490000</td><td>58768.490000</td><td>18.146667</td><td>-66.835500</td><td>37.840000</td><td>2.980000</td><td>1001012</td></tr><tr><td>2020-01-07T20:43:26.700000</td><td>74606.700000</td><td>17.933500</td><td>-66.923333</td><td>38.810000</td><td>1.570000</td><td>1001342</td></tr><tr><td>2020-01-07T15:58:52.370000</td><td>57532.370000</td><td>18.353667</td><td>-67.028000</td><td>39.160000</td><td>1.310000</td><td>1000980</td></tr><tr><td>2020-01-07T20:27:22.970000</td><td>73642.970000</td><td>17.931000</td><td>-66.846500</td><td>39.800000</td><td>1.560000</td><td>1001320</td></tr><tr><td>2020-01-07T22:21:53.870000</td><td>80513.870000</td><td>18.466000</td><td>-66.986833</td><td>40.580000</td><td>2.170000</td><td>1001466</td></tr><tr><td colspan="7">Unrealistic depths for the region? (SW Puerto Rico)</td></tr></table>

# Check “NEW” events in enhanced catalog, not in reference catalog Sorted by depth (Southwest Puerto Rico)

## Catalog QC: False detection in coda of larger earthquake (also, too deep?)

2020-01-07T16:19:28.490000 58768.490000 18.146667 -66.835500 37.840000 2.980000

Earthquake 2020-01-07 16:19:28.491959877 +/- 0.20s Hyp=[-66.84,18.15,37.84] - Hyp Uncertainty (km) +/- [2.08,2.71,0.58]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/af35d46779115170471d87fafe7339dfc4570ab85a552f59ae65d324fcda0f86.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/d56f6bdae994a42f32726ce9707fd6eb3861c700d729a066679323fe75c0718d.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/e6a1b76576e7584a6995f967da4bd3be35305233ada35b83769892ce61ed179c.jpg)

1001012

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/1e827f044335fea894a7192cebf05186c0451c017a83bd9645a1d8c1b73347da.jpg)

Event waveforms with P, S picks

Solid: auto-picks, Dashed: predicted arrivals

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/726ecd0bff7f91c6c16a9429935e85212d3849138e272267343016851ca4534c.jpg)

## Post-processing: automatic removal of false detections in coda of larger earthquakes

• Visual detection of event waveforms with unrealistic depths (30- 40 km): false detections in coda of larger earthquakes

EQTransformer (Mousavi et al., 2020) with low thresholds for event detection and P, S picks

• Devised an empirical algorithm to remove these specific false detections (Yoon et al., 2023, BSSA)

• Apply only to NEW events not in reference catalog, not to MATCH events. Must meet ALL 4 criteria below for removal.

• 1) current event was within 45 seconds of the previous event in time;

• 2) current event had 14 or fewer phases;

• 3) previous event had at least 5 more phases than the current event;

• 4) current & previous events within 1 local magnitude unit of each other

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/9f132b48eb44642aea8851db72baa69d13301842da9ea5ed16842a4022a32c57.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/216df05047bff889ffaec1d996a01ddd97935cc6172be23b7d5f7304dcddc7dd.jpg)

## • Catalog QC: West Texas

• After event association

• (Left) new local earthquake �

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/5cf949a74e3e2049a36f1d9c84ef088add74ecf9fabcfb987ff3c9b8ad53dfc2.jpg)

## • (Right) false detection

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/ab18dea878544c33f539e4d8ef65b66fbb07b076bd951bced57756a6acd06ab7.jpg)

o large distance (307 km) to nearest station; IM network?

2-minute waveforms Vertical lines: Origin time, P, S

## Problem: Incorrect association/location due to uneven station distribution (array far from rest of network & seismic sources)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/17cbb42df2c79d76c122d89e058ef4e8af884db67472bbf3aabf64cea34b0337.jpg)  
Solution: Use only one station from array (IM.TX01) for event association

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/3efb31c8681c72fed56d66031ddc7b9ffcb1a66ca12d61c6d4044da937973974.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/926bc9fe1002060297e5aa65932dca5590532b60d2f0f86beeccc112299604a9.jpg)

• Catalog QC: West Texas

• Bad event association

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/99f771ca5cbd529ae86a6debd14c68bb36549a8d55b135461cc31b3098173ead.jpg)

• (Left) P, S picks from 2 di@erent earthquakes associated as one event

• (Right) Noise picks associated as event à wrong moveout

2-minute waveforms Vertical lines: Origin time, P, S29

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/947b4b358c1393510f9c06c61123a91a06efc1e3a361370b54f831dd8dfc9124.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/98161e479cd81478c08d971f0a73fcfd970fdacc7c236a8a5454ce2e3d940340.jpg)

• Catalog QC: Central CA

• Filtered 3-12 Hz

• Non-earthquake signals: active-source survey

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/b9023b96fef396d4a9faa6ea956ef8642e81f7e99e288f7f4acceb1040f4b74f.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/6330b8d9ddefb43acd229fce1020538f35140e9e800b4864a4e95594e26f6f7c.jpg)  
3 minutes

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c53ab1d88480667055ea9fc5c3b5fe644dd61ba4758d2a1110e6326e6241bac1.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7ba5eec04bd00d0fdc8dd3ff2441a9fc2c75a298077c6ac7fc508d03c64ce6e1.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f621ca2e1f8d4fea4c2afc075e737952c58c471844cb3d72b9ed073f11fffbd2.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/aedc5e35d8a9bb96ff73d4f16af0791fad25533f659f9ca43937526dd2abdb32.jpg)  
Very little moveout (waves hit all stations at same time)

2013-08-16T00:22:53.57 - 2013-08-16T00:25:53.57

## Infrasound signals recorded in Central CA

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/41fa237eedec0b4ef4785dd1a6a6e567e3969b8d91e28841c29ab17ba7502419.jpg)  
3 minutes

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/139802eabc281990561c6e281857ce452d1b679233a7d99ee06fd8bbfbccf3da.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/9cb85608e93cbb5357e51611e640885da13482c4882168112f7c67c2fabec5b3.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/2cf5e8103d336a240e13f35ec4dcb2b6beb321410719573f9d5c38d6e2f7b56b.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/d653c0011c8f38aff533b40623657f95a6cbd02d8211fcc8b05b9ce955953992.jpg)  
Slower moveout from sound waves

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/825c2af843bf67b961bf3afc820872ec315e369d8dac2686105d5a2f1a888c81.jpg)

## Quarry blasts: often in enhanced catalogs, but not 'interesting' to many seismologists <sub>Check</sub> <sub>ComCat</sub> <sub>for</sub> <sub>blast</sub> <sub>events</sub>

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/85964b8491766285dcfec17b9216f2a24dfbbb93071cdf985808c7f580db9a29.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/067f3f7651be27fdc083b7adc680807f6b55516da12471e6a2f4d43f02b01392.jpg)  
Check waveform plots: lower frequency content?  
Events located near known quarry?  
Events occur only in local daytime?

## Automated post-processing strategies to remove false detections & unwanted signals from catalog

[Machine-learning] classifiers: discriminate diierent seismic signals

Teleseismic earthquakes, quarry blasts, cultural noise sources, infrasound, ...

Assemble training data set, create classifier model

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/29627460e95143fca92332bb2f0d87e858628cf3d35ec944ee2aed6920d897d3.jpg)

Empirical algorithms: remove specific false detections after visual inspection

e.g. false detections in coda of larger earthquakes

may be specific to network geometry & source distribution

Simple thresholding & filtering to discard non-earthquake signals

• easy & e\ective, but be aware of tradeo\s

## Simple thresholding & filtering to discard non-earthquake signals

## - easy & eiective, but be aware of tradeois

• Restrict locations to a certain region and/or depth range

• Set minimum threshold on:

o Number of (P, S) picks

o Number of stations per event

o Output probabilities for P, S picks

• Set maximum bound on:

o Distance to nearest station

o Distance to farthest contributing station with picks

o Azimuthal gap

o RMS residual

o Travel time residual for P, S pick at given station

## Magnitude of Completeness (Mc)

Magnitude-frequency distribution (MFD) (Gutenberg-Richter)  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c375cf9ad17470e0ce647f26ae83d8b18e67f6a0be73077947d5a75aa652bf31.jpg)

Mc: lowest magnitude above which the earthquake catalog is "complete"

Lower Mc is better (more complete)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/3e3e5c7938eb029f9db910f9279ef2b110cebb8a64d7a8e10b88d8c69ce46b3b.jpg)

Many diferent methods to get catalog Mc

\- Maximum Curvature (MAXC): max value of 1st deriva1ve of MFD (typically, max of binned MFD) most reliable for small sample sizes (\~50-100 events) \* works best with local datasets with fewer heterogenei1es

## - Goodness-of-fit Test (GFT): lowest magnitude cut-of where Gutenberg-Richter rela1on holds

\- Mc by b-value Stability (MBS): first magnitude increment where |b<sub>avg</sub> - b| < uncertainty of b \* tends to produce the highest (i.e., most conserva1ve) Mc

\* More info and original R codes from CORSSA: https://corssa.org/ https://doi.org/10.5078/corssa-39071657

\* Matlab codes available on Github: https://github.com/gtepp/research\_codes

\* Other methods to get Mc: ZMAP (Wiemer, 2001)

b+ positive (van der Elst, 2021)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/a4f6fd22b9ad2f073dcb95419285999c2e27935868b29848363bddfc783deb01.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/3b2f0abed0d06644322ca60cebd86684394c93ca4840236530b899e692314b0d.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/6baecbe0d0e2f78b67251550937a74034572d6b976c68a0d7d1235d1246cfc1e.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/741a99f3c56a61ba20a651de4970fc51319a69c824b720c3f47d5ea75e10a296.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/98e3e71fc28b3f3a5903528d6ee35397004e1759d98166ec13297667c4dd5e5d.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/b85940fdeb3c519110028d993533d627f874f4c457c0639efcf151611df8b47e.jpg)

## Spa1al Mc Changes

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/a866c47d3b07e9748e5aff06719c6ce4fff50949c005850d604242688be668e9.jpg)

\- Bins: 0.5° (\~50 km) squares

\- 1932-1972: 20 years

\- 1973-2022: 10 years

\- Maximum curvature method

\- Minimum 30 EQs/bin

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/d885071a0c4975de42041d7044d4cf7f29c1fe272b26d0a22a1dedbcf31cf6e0.jpg)

Past 90 years: SCSN Mc has decreased from \~3 to \~1, but not uniformly throughout the region

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c7222fb15ee52e6277bad76ddeef05fed390ddcf7af106c50593c6742786c181.jpg)

2010 M<sub>w</sub> 7.2 El Mayor-Cucapah sequence  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/8e99e0cb8254616f87e45e327e2dfc104cbbd4f732801cb792a62894d67cddde.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/b1b5c0b3b9bcc793d9a143c7b186ff38b008c71f1b2e96bf78dd86303f7fb489.jpg)  
Expect higher Mc earlier in aftershock sequence

Ridgecrest Mc is \~1 mag. unit lower than El Mayor-Cucapah Mc  
2019 M<sub>w</sub> 6.4 & 7.1 Ridgecrest sequence  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/777117bbe4e3dc6111f867b817322e2d5c8faba2acd6093514dbcf16c86ab202.jpg)  
magnitude

## Catalog QC: Summary of things to check in plots Compare against a reference catalog!

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f61306fb874ec85daa65f1cb82900ebe4beccc2195e43bfcaad2337482aa0fa6.jpg)  
Mag-Freq Distribution, Mc Magnitude vs. Time

## Extra slides

## Earthquake Catalog QC General Tips

• Make plots - think like an analyst – use visual tools. Waveforms!

• Use seismology domain expertise

• If enhanced catalog events don’t look like real earthquakes, figure out why.

• Rule out all sources of noise (background or cultural). Be sure it’s not an artifact.

• Check it’s not a regional/teleseismic earthquake.

• Check it’s not a quarry blast, sonic boom, infrasound, active-source explosion, or other unwanted seismic signal.

• Only then have you discovered new earthquakes.

## Reference Catalog: How to download?

• For bulk downloads of catalog events from ComCat

• ComCat search API: https://earthquake.usgs.gov/fdsnws/event/1/ • (I create the URL string, then call wget with a bash script)

• Python libcomcat: https://code.usgs.gov/ghsc/esi/libcomcat-python

• ObsPy get\_events() with USGS Client (I save QuakeML files with picks): https://docs.obspy.org/packages/obspy.clients.fdsn.html

• For ANSS networks, all finalized local events are sent to ComCat. Can also download reference catalog from regional seismic network, which may contain extra events.

• SCSN: Quarry blasts, teleseismic/regional events.

• https://scedc.caltech.edu/

• NCSN: Extra events – not all events are submitted to ComCat; catalogs available in other formats.

• https://www.ncedc.org/ncedc/catalog-search.html

## Alternative (non-authoritative) reference catalogs

• Regional seismic network websites (for ANSS networks) also have alternative (non-authoritative) earthquake catalogs and data sets for download, to use as reference catalogs

• SCSN: template-matching, relocated, deep-learning, focal-mechanism, https://scedc.caltech.edu/eq-catalogs/altcatalogs.html, https://scedc.caltech.edu/data/deeplearning.html

• NCSN: real-time double-diierence. https://www.ncedc.org/ncedc/catalog-search.html

## MATCH events: location, magnitude comparison

## • Compare enhanced vs. reference catalog

• Location (latitude, longitude, depth, origin-time)

• Magnitude

• Distribution of residuals (ideally zero) – are they low enough for you?

• It's dieicult to exactly reproduce locations & magnitudes from ComCat (or other reference catalog)

Diierences in monitoring software, velocity model, manual pick times/weights, filtering before amplitudes, ...

• Just check that these values are close enough for your needs.

## Reference Catalog Tip: Select boundaries carefully

• Carefully select the bounding box or circular radius for downloading your reference catalog, before comparing it to enhanced catalog. It should include:

• Entire seismogenic region of interest to you

• Check past seismicity locations on web map: http://ds.iris.edu/ieb/ or https://earthquake.usgs.gov/earthquakes/map/

• All seismic stations you plan to use for catalog generation

• Check station locations and availability on web map: http://ds.iris.edu/gmap/ or https://www.fdsn.org/networks/

NEW events in your enhanced catalog might be from reference catalog events outside your selected bounding region

• Check waveforms: could be a regional distance earthquake if higher duration and amplitude

## Catalog QC, locations in map view: TexNet

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/75628bf245cc13eb63c70d51df996994e90275f5447dc819f1e47d9a54c3c7af.jpg)  
Reference catalog: TexNet (2015-2024: 9 years)

Many scattered event locations – possible false detections?

Enhanced catalog: 2023-12-31 (1 day) GaMMA associator (3 P, 3 S, 6 total picks)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/203644a86d6d4928618d877bc55a58af9c1816a04ca8d10d7560f979ef42b6b3.jpg)

## Catalog QC, locations in map view: TexNet

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c79529d9191949820906d658422c2f09a39650b551a14b085c9562612c0f33c0.jpg)  
Reference catalog: TexNet (2015-2024: 9 years)

Removed false detections (fewer scattered events) with stricter association criteria

Enhanced catalog: 2023-12-31 (1 day) GaMMA associator (4 P, 4 S, 8 total picks)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/65190dfd75cb42e2dbc33e34530b6112d692b8d96d5c3c2fdd8060769b7d9137.jpg)

2.48,2.14] Event waveforms with P, S picks Solid: auto-picks, Dashed: predicted arrivals

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f8bac23ba78e4509901aa6f746fe8b3007e0812a0e2170d9a3634de649e17466.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/b2584b926b56304bfa666f64af0c50eed5c30484455ce54f3d9e92e2cc12db10.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/8ff805fcefa62f4c3809b744ddda302d22488ec90f78aa18df973e22b509909c.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/2a5e11281d6f92165667ab873d6c39bef9f746585c081752174b238c22e6677f.jpg)

Catalog QC: False detection in coda of larger earthquake (also, too deep?) 2020-01-07T08:29:36.930000 30576.930000 17.963500 -66.752333 29.160000 4.480000 1000330

Earthquake 2020-01-07 08:29:36.925860007 +/-1.21s Hyp=[-66.75,17.96,29.16] - Hyp Uncertainty (km) +/- [4.69,2.51,0.93] 2.51,0.93]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/2b0a4e19c15f195dea8c8d6b501ccf0c3852b2f610059fb56fbad312391fb5ba.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/8fb6190786260f0571ea37198e5c7bd23f6768834eacddb323f4dba98241db93.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/2e35ecd5e59f810ff3b0295f4bac3e6b255852e08f8238a560f27bc8a51da710.jpg)

Event waveforms with P, S picks Solid: auto-picks, Dashed: predicted arrivals

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/ee888240afafa3497dec4f7cc6fdb3734ff51aeadc5b7e93b2bb830a5468a7eb.jpg)

## Catalog QC: Real (newly detected) earthquake

2020-01-07T08:29:18.320000 30558.320000 18.139667 -66.810000 7.660000 4.440000 1000328

Earthquake 2020-01-07 08:29:18.318609738 +/- 1.01s Hyp=[-66.81,18.14,7.66]- Hyp Uncertainty (km) +/- [2.00,3.72,2.12] 3.72,2.12]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/9b0c7cc03f3a829da034e68f437f78239610e2b1c5ed6032f4a2d7ec4b646cd3.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7ce9cad3baaf847116dddc4d5754a624ff41207ea67e3f471834d4c770be9762.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/d3486494b6e5f168d6752466d118f4b0403906f3e598c65d1000aaa8a0ae57a8.jpg)

Event waveforms with P, S picks Solid: auto-picks, Dashed: predicted arrivals  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/0b469111f44398a2e7fed0f0ba1aeb7d88fcec90a6129ffed2df2c42c4b77015.jpg)

Catalog QC: False detection in coda of larger earthquake (also, too deep?) 2020-01-07T22:21:53.870000 80513.870000 18.466000 -66.986833 40.580000 2.170000 1001466

Earthquake 2020-01-07 22:21:53.871442969 +/- 2.08s Hyp=[-66.99,18.47,40.58] - Hyp Uncertainty (km) +/-[3.84,8.85,0.59] 8.85,0.59]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/5e1c7aa5d0526af06331897dd6d0bc854a113739838c1db988cd3f156da947b4.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/a80a5141bef348fabe2edfed1e01647b490cfa42f9a992d038830b58aa66b144.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/ea70f72130e80935ae6063dc537a9b0dd295c03b0fd53a9ff4707d83c05a814a.jpg)

Event waveforms with P, S picks Solid: auto-picks, Dashed: predicted arrivals

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/94ebb60212bbe0f4e7b49054dc8104c040e4986986172d459a3efe9ce0ba3a79.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/7e10ac96bb184ef698fabee061150e1b81dd4d8abe78ba7ffc1f33bb16313e49.jpg)

Catalog QC: False detection in coda of larger earthquake (also, too deep?) 2020-01-07T20:27:22.970000 73642.970000 17.931000 -66.846500 39.800000 1.560000 1001320

Earthquake 2020-01-07 20:27:22.965268426 +/- 0.97s Hyp=[-66.85,17.93,39.80] - Hyp Uncertainty (km) +/- [0.36,0.59,0.24] 0.59,0.24]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/4812135202cdbecbf9b1612003e988635d173949e83f7b65c7fc1e0a73653ab3.jpg)

Event waveforms with P, S picks Solid: auto-picks, Dashed: predicted arrivals

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/eef48a84764d405acbddfcb09b84dd79a1dc0f2c220281232d487f59e44ced35.jpg)

## Catalog QC: False detection in noise (also, too deep?)

2020-01-07T15:58:52.370000 57532.370000 18.353667 -67.028000 39.160000 1.310000 1000980

Earthquake 2020-01-07 15:58:52.367385814 +/- 0.17s Hyp=[-67.03,18.35,39.16] - Hyp Uncertainty (km) +/-[5.86,6.19,1.22] 6.19,1.22]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/4eb784622e34af86005e9d8599347c70bead994a9006d6a12563dc35199bef2c.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f83773f60b8b6f4ee263ed3435ff255b7184bb35055c5de2899e1ccf7afaacb8.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/3ff1dc73b820e396a84a77c5c1be4939240a4918a23b9b8d3113e8e5cc04328b.jpg)

Event waveforms with P, S picks Solid: auto-picks, Dashed: predicted arrivals  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/29be20dc2c7d043bdedb790eb3b098513f4ea63ff1a21b946e0712de54304cbc.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/91333fceca7f60bbd6817b41c0f89e2d15b88374804f613fee3293be5bade3b2.jpg)

Catalog QC: False detection in coda of larger earthquake (also, too deep?) 2020-01-07T20:43:26.700000 74606.700000 17.933500 -66.923333 38.810000 1.570000 1001342

Earthquake 2020-01-07 20:43:26.699477316 +/- 0.08s Hyp=[-66.92,17.93,38.81]- Hyp Uncertainty (km) +/-[0.27,0.82,0.48]

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/f3e1a39e2d29ca02cb3a5d66b35c3d2e29009c9c113fe45ac3ee2e52143e919c.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/cdb94f10f152e6c04298481e79b818861e13612acb0fda7bbfa0fd90af590fba.jpg)

<table><tr><td colspan="2">TX.PECS.00.HHZ D=190.76km</td></tr><tr><td colspan="2">TX.MB02.00.HHZ D=321.99km</td></tr><tr><td colspan="2">IM.TX08..SHZ D=407.85km</td></tr><tr><td colspan="2">IM.TX07..SHZ D=408.67km</td></tr><tr><td colspan="2">IM.TX09..SHZ D=409.04km</td></tr><tr><td colspan="2">IM.TX04..SHZ D=409.27km</td></tr><tr><td colspan="2">IM.TX10..SHZ D=409.38km</td></tr><tr><td colspan="2">IM.TX31..BHZ D=409.86km</td></tr><tr><td colspan="2">IM.TX01..SHZ D=409.89km</td></tr><tr><td colspan="2">IM.TX03..SHZ D=410.01km</td></tr><tr><td colspan="2">IM.TX02..SHZ D=410.58km</td></tr><tr><td colspan="2">IM.TX06..SHZ D=411.15km</td></tr></table>

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/880dc9ed510d3293b812e4b21d38d7971ad4c34cdd02fa095ba6eb68e5bea528.jpg)

## • Catalog QC: West Texas

• Bad event associations – dominated by array

• Notice large distance to nearest station

2-minute waveforms

Vertical lines: Origin time, P, S

PyOcto Event #213 : 5/5/10 No Match to TexNet, Match to GaMMA, NSD<75.0 Red: Event, Blue: P Pick, Green: S Pick

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/abededa3200dd0c79f8135f685c57a2ebf4432fa7950bbbba43e09aaf05e8626.jpg)

• Catalog QC: West Texas

• Good event association examples

• P, S picks on earthquake signals with expected moveout

2-minute waveforms

Vertical lines: Origin time, P, S

## Magnitude of Completeness

\- lowest magnitude at which the catalog is “complete” (based on Gutenberg-Richter rela1on)

\- examine frequency-magnitude distribu1on obtained by binning earthquake magnitudes

\- one approach for evalua1ng the quality of a catalog

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/92fed72147210392331346b5ba0a1034aed1da55bdfe650f2a0817ae55d1417d.jpg)

## Can consider:

\- temporal changes of Mc

\- spa6al varia6ons of Mc across region

\* More info and original R codes from CORSSA: doi:10.5078/corssa-0018080

\* Matlab codes available on Github:

## Calculated with diferent methods, including - Maximum Curvature: max value of 1st deriva1ve of FMD (typically, max bin of non-cum FMD) most reliable for small sample sizes (<\~50-100 events) \* works best with local datasets with fewer heterogenei1es

## - Goodness-of-fit Test: lowest magnitude cut-of where Gutenberg-Richter rela1on holds

\- Mc by b-value Stability: first magnitude increment where $\mathbb { P }$ < uncertainty of b \* tends to produce the highest (i.e., most conserva1ve) Mc

## Bootstrapping

\- gives sense of varia1on from sampling

\- 200 sets with resampling

\- mean and st. dev.

original: 1, 1, 1, 2, 2, 3

sample A: 1, 2, 2, 2, 3, 3

sample B: 1, 1, 1, 1, 2, 2

sample C: 1, 1, 2, 2, 2, 3

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/903526dc34c4acc71e1b007b16e2b08a144caddf32c5a25f3e549a287cbc0f98.jpg)

Difference between 1993-2003 and 2003-2013  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/c8811258a8c6d56e1862426bf05749a5c64ffeba5c52aa41bbd51ad0d23709ec.jpg)

Difference between 2003-2013 and 2013-2023  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/668086f5879f75e60b6b328e2fef5132fa1dce37fa64e8b828230e29a4da67ca.jpg)

Better: 1994 Northridge -> regions with worse Mc typically have fewer earthquakes

Difference between 1993-2003 and 2013-2022  
![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/561ac6510e9abb5e1d2b0c62077a09673a5a21e70a46681b22e590f07ceaebc3.jpg)

![](mineru/QUAKEFLOW_GJI_GGAC355__evaluation/images/4c3aa5acfb7418384b93eedb109100eb1d8d43d21ef588bf3453a990a6e981b8.jpg)  
-> small improvement (\~0.2-0.7 m.u.) in most areas over past 30 years