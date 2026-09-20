<!-- Stable sidecar generated from the MinerU supplementary bundle. The original bundle remains under parsed/supplement/mineru/. -->

# Supporting Information for “Next Generation Seismic Source Detection by Computer Vision: Untangling the Complexity of the 2016 Kaikōura Earthquake Sequence”

Fengzhou Tan<sup>1,2</sup>, Honn Kao<sup>1,2</sup>, Kwang Moo Yi<sup>3</sup>, Edwin Nissen<sup>1</sup>, Chet

Goerzen<sup>1,2</sup>, Jesse Hutchinson<sup>4</sup>, Dawei Gao<sup>5</sup>, Amir M. Farahbod<sup>2</sup>

<sup>1</sup>School of Earth and Ocean Sciences, University of Victoria, Victoria, BC, Canada.

<sup>2</sup>Geological Survey of Canada, Pacific Geoscience Centre, Sidney, BC, Canada.

<sup>3</sup>Department of Computer Science, University of British Columbia, Vancouver, BC, Canada.

<sup>4</sup>Ocean Networks Canada, University of Victoria, Victoria, BC, Canada.

<sup>5</sup>School of Geosciences and Info-physics, Central South University, Changsha, Hunan, China.

## Contents of this file

1. Text S1 to S3

2. Figures S1 to S24

3. Tables S1 to S8

Additional Supporting Information (Files uploaded separately)

1. Captions for large Tables S9 to S12

2. Caption for Movie S1

Introduction

The supplementary materials include 3 supporting text, 24 figures, 8 tables, 4 large tables and a movie.

## Text S1. Training the 3D U-Net.

The 3D U-Net used in this study follows the structure in Çiçek, Abdulkadir, Lienkamp, Brox, and Ronneberger (2016) but only has two steps in both the contracting and expanding paths (encoder depth = 2) (Figure 2c). This trimmed network is already powerful enough for our purpose while the original network (encoder depth = 3) will require much larger GPU memory and more computation time. A linear normalization to input images is applied at the beginning. Each step of contracting consists of two sets of $3 \times 3 \times 3$ convolutional layer, batch normalization (BN), and rectified linear unit (ReLu). $\mathrm { ~ A ~ 2 ~ } \times \mathrm { ~ 2 ~ } \times \mathrm { ~ 2 ~ }$ max pooling with strides of two is applied afterwards. Each step in the expansion path consists of a transposed convolutional layer (up-convolutional layer) of $2 \times 2 \times 2$ by strides of two in each dimension, followed by two sets of $3 \times 3 \times 3$ convolutional layers, BN, and ReLu. Cropping and concatenation are applied as shown in Figure 2c. The last layer is a $1 \times 1 \times 1$ convolutional layer which reduces the number of output channels to one.

The steps to generate the synthetic training dataset with labels are as follows. The first step is to generate synthetic waveforms to mimic an aftershock sequence recorded by a regional seismic array. We take 46 real seismic station locations (Figure 1 and Table S9) and assume 1,000 earthquakes in the Kaikōura area, 900 of which are taken from the GeoNet catalog (GNS Science, 1970) after the 2016 Kaikoura mainshock and the rest are randomly assigned within the study area (Figure S1). Their magnitude values are generated randomly following the Gutenberg-Richter law (Gutenberg & Richter, 1944) with the smallest magnitude to be 3.0. By summarizing the results in Harrington and

Brodsky (2009) and testing with various cases, we empirically define the total source duration $T _ { s o u r c e }$ (s) to be a function of magnitude M:

$$
T _ {s o u r c e} = \left\{ \begin{array}{l l} (M - 3) \times 0. 3 + 0. 1, & \mathrm{if} 3 \geq M <   4 \\ (M - 4) \times 0. 6 + 0. 4, & \mathrm{if} 4 \geq M <   5 \\ (M - 5) \times 3 + 1, & \mathrm{if} M \geq 5 \end{array} \right.\tag{1}
$$

and the source time function has a triangle shape. We take 13 representative focal mechanisms (Table S1) according to the fault geometry in the Kaikōura region and assign them randomly to the 1,000 earthquakes. Finally, the FK program (Zhu & Rivera, 2002) uses a one-dimensional (1D) velocity model extracted from the New Zealand wide 3D seismic velocity model 2.2 (Eberhart-Phillips et al., 2020) around the Kaikōura area to calculate the waveform for individual event at each station with the sampling rate of 40. These parameter settings look sophisticated; however, the details do not matter much because the stacking process will result in similar brightness videos regardless of the shape of the waveforms (Kao & Shan, 2004).

Then, we randomly assign origin times to the 1,000 events and superimpose the individual waveforms together to mimic the continuous seismograms recorded at each station. We set diferent number of events per hour ( 20 to 500) when generating origin times. Each event’s waveforms are used multiple times to construct a total of 101 hours continuous data which contain 22,400 earthquakes. We add a wide range of Gaussian noise with standard deviation from 0.00004 $\mathrm { c m / s }$ to 0.0003 cm/s to the 101 hours, which creates diferent situations, including those weak earthquakes that can only be seen at nearby stations and big events that are clear at all stations. The presence of varying noise levels in the data also reflects a common scenario where a small portion of stations may be temporarily unavailable. The choice of noise levels may influence the trained model: higher noise level will emphasize on weak events and enhance recall whereas lower noise level will let the model learn to recognize clear events. We note that the diferent combination of events in space and time as well as the random noise make the final seismograms unique in all times.

The next step is to generate a continuous brightness video over the study area for the 101 hours. We apply the source-scanning algorithm (Kao & Shan, 2004; Tan et al., 2020) with a presumed source depth of 10 km, a 0.5 second time interval, a 4 km spacing in both latitude and longitude, and a frequency band of 5–20 Hz. These parameters remain unchanged through training, testing and the real application. The valid study area is 240 km  240 km and the margin is 20 pixels (80 km). Therefore, the brightness video of one hour covers 400 km  400 km and has 7 $, 2 0 0 \times 1 0 0 \times 1 0 0$ pixels. We use a diferent velocity model, “iasp91” (Kennett & Engdahl, 1991), to generate the brightness video in order to mimic the real condition that the velocity model we use for analysis is imperfect.

Then, we create the score video as the label. The synthesized earthquake locations and origin times are ground truth. The pixel values are labeled as zeros if there is no earthquake. When an earthquake epicenter and its origin time correspond to a pixel, we label that pixel a score which is equal to the earthquake’s magnitude value. The usage of magnitude as the score is just for convenience and it does not mean the neural network will output the accurate magnitude after training. The prediction output is considered score and an additional magnitude determination process is required (see Section 2.2.4). For one hour, the score video has $6 0 \times 6 0 \times 7 , 1 6 0 = 2 5 , 7 7 6 , 0 0 0$ pixels (the score video does not have the margin). Even with 500 earthquake per hour, the non-zero labels are still much sparser in the 3D image $( 5 0 0 \div 2 5 , 7 7 6 , 0 0 0 \approx 0 . 0 0 0 0 2 )$ compared with original

3D U-Net applications (Çiçek et al., 2016). Thus, we apply a 3D Gaussian filter to create a smoother distribution of non-zeros labels.

Finally, we cut out blocks of $6 0 \times 6 0 \times 6 0$ pixels from the 101-hour brightness video and corresponding blocks of $2 0 \times 2 0 \times 2 0$ pixels from the score video to form the training dataset. For each cataloged event, we cut eight blocks around it with a random shift in all three dimensions to make eight diferent training samples by putting it in diferent locations relative to the block. Then we have additional blocks cut completely randomly. <sup>In</sup> <sup>the</sup> <sup>end,</sup> <sup>a</sup> <sup>total</sup> <sup>of</sup> <sup>194,559</sup> <sup>block</sup> <sup>pairs</sup> <sup>are</sup> <sup>taken,</sup> ∼ <sup>88%</sup> <sup>of</sup> <sup>which</sup> <sup>include</sup> <sup>earthquake</sup> epicenters and origin times in the label block. About 90% of the block pairs are used for training and the remaining 10% for validation.

We use a mean-square-error loss function and the Adam optimizer (Kingma & Ba, 2014) with a batch size of 25 to train the network for 140,440 iterations (20 epochs). The training time is 60 hours on an 8G GeForce RTX 2080 graphic card.

Text S2. Visual inspection examples of synthetic data.

Visual inspection of seismograms is the most common way to verify earthquake detections. However, in some cases, analysts are unable to judge whether a seismogram record contains an earthquake or whether the proposed earthquake location is correct. Here we show synthetic examples where such visual inspection either works or fails. Figure S7 show filtered (5–20 Hz) waveforms of five SUGAR detections while corresponding spectrograms are shown in Figures S8–S12. Generally, the waveforms and spectrograms agree with each other with picks visible in both plots. But the picks are usually clearer in filtered waveforms because the calculation of spectrogram loses some time resolution. Figures S7a and S8 show the event No. 4 in Section 3.2. Red and blue marks show that

SUGAR has accurate picks for this event at most stations, making it a clear detection. The analyst has also identified this event correctly. Figures S7b and S9 show the event No. 1 in Section 3.2; though missed by the analyst, we can clearly verify this event when plotting the waveforms and picks by epicentral distance. Figures S7c and S10 show the event No. 2 in Section 3.2. Looking at the plots, picks are still aligned nicely with the expected arrival times. But due to the low number of associate picks, one usually cannot confidently confirm it to be a true detection. Figure S7d is a more extreme example that only seven phases are associated and it is very likely that an analyst would assess this detection as false. Only when comparing with the ground truth do we know this to be a valid detection, albeit with larger uncertainties. This is not uncommon through our visual inspection of SUGAR detections. Moreover, Figure S7e shows an example that a false positive detection by SUGAR associates a number of phases nicely, even though it is achieved purely by coincidence. This event is likely to be confirmed by an analyst seeing all these picks, raising significant concerns about the efectiveness of visual inspection.

Text S3. Example detections in real data.

We show four example events in the real testing hour with various qualities. The first one is an M3.6 event that appears in all catalogs (Figure S14a). The brightness video shows a global maximum that is much larger than other local maxima and the AI score at the corresponding location is >3. SUGAR has accurate P and S picks at most stations shown in the vertical channels (Figure S14a) and horizontal channels (Figure S15), respectively. We note that a strong reflection phase is observed in the vertical channel at many stations (e.g., PLWZ, PWES, BMTS) 7–8 s after the P phase. This is sometimes recognized as the S wave by the Earthquake Transformer with high probability; however, it will be discarded by SUGAR because they do not fall in the predicted arrival window of the S wave. The second example is a M 2.4 event that has been detected only by analyst B and SUGAR (Figure S14b). The brightness video shows a global maximum but its value is very close to that of the patch in the lower left corner. The AI score is ${ > } 2 .$ , indicating a detection with high probability. The phases are only clear at three nearby stations, with some additional possible phases at distant stations. This explains why it has been missed by the other two analysts and other workflows. The third one is a M 3.4 event that has only been detected by SUGAR (Figure S14c). The brightness video again shows a global maximum but with its value close to other local maxima patches. The AI score is ∼<sup>1.7,</sup> <sup>indicating</sup> <sup>a</sup> <sup>weaker</sup> <sup>detection</sup> <sup>than</sup> <sup>the</sup> <sup>previous</sup> <sup>two</sup> <sup>but</sup> <sup>still</sup> <sup>much</sup> <sup>higher</sup> <sup>than</sup> <sup>the</sup> threshold of 1.0. Clear P and S picks are made at three nearby stations. Therefore, we agree that this is a true detection, but missed by all analysts and other workflows. The last one is a low-quality event (M 3.4) that has only been detected by SUGAR (Figure S14d). The brightness video does not show a global maximum or a local maximum, but the AI score is ${ > } 2 .$ indicating a decent detection. It does have a few picks aligned with the expected arrival times, but we cannot confirm it because too few phases are associated. However, this may still be a valid detection, similar to the synthetic examples in Figure S7c and S7d. The spectrograms of the 10 closest stations for the four events are shown in Figure S16–S19. The phase picks agree well with the spectrograms in all cases.

Movie S1. The complete brightness and score videos for the example in the section 3.2 “Solving the phase association ambiguity”.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/6e0d94f39abbfbb7eb76fe7d47e6479cfd0df2e0da05375ca265b34a7d27bf7a.jpg)  
Figure S1. Synthetic training events distribution. Color represents the focal depth.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/81783553100c72e5792891fd90987a4cc304482ae697d283db73d09961c4be9f.jpg)  
Figure S2. Mean $F _ { 1 }$ value for all five testing hours. Each black dot represents a test with the corresponding score threshold. The y coordinate of the star represents the analyst’s mean $F _ { 1 }$ value for the five hours. While the analyst does not have a threshold, the x coordinate of the star represents the score threshold which maximizes the $F _ { 1 }$ value of SUGAR.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/2e60c24d584237de98098f3d10a918c2e1ea0b89815ffe89be169cc913253e8d.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/d48c8b5bbbe1282d278ee158a84558092d16a4d707bad16185651b79390f604a.jpg)  
Figure S3. A comparison between the analyst and the SUGAR in testing hour No. 2. Symbols and layout are the same as that in Figure 5.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/c222401a695f7ed0860e12c93e1756f6c8746153530b79704ecc17e1ca3ea570.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/5ea775ada1cea1f106002fdba171864b00a23bda5da891952cb2430693f7c275.jpg)  
Figure S4. A comparison between the analyst and the SUGAR in testing hour No. 3. Symbols and layout are the same as that in Figure 5.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/d7f9ad3892e4110b216dc030ac2b8e29503ef1c008297e4ab94b9076c5b019c7.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/3dea7effdaa9d3266b8d80f011267d0d77ed1865d4da19428bbcdad181736655.jpg)  
Figure S5. A comparison between the analyst and the SUGAR in testing hour No. 4. Symbols and layout are the same as that in Figure 5.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/bd67254f0c4e7fa84313d56dcd6a80114241a80329502cc074d8e9ef88fbcb59.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/6a760bf3f8a616a7f56fd7fba67734ed39ff1b00d6afba3ffd4cacf6f121f0af.jpg)  
Figure S6. A comparison between the analyst and the SUGAR in testing hour No. 5. Symbols and layout are the same as that in Figure 5.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/51965b2e000e26cef0ad9df99249c66b4578f97d1de6628d05818d8169553ae1.jpg)  
Figure S7.

Example synthetic waveforms (filtered to 5–20 Hz) for visual inspection. (a), waveforms of the event No. 4 in Figure 6. Red and blue marks show SUGAR P and S picks, respectively. Curves with corresponding colors indicate expected arrival times. The title writes the AI score, origin time and epicentral errors of the SUGAR detection compared with the ground truth. (b), waveforms of the event No. 1 in Figure 6. (c), waveforms of the event No. 2 in Figure 6. (d), waveforms of the $8 2 ^ { t h }$ SUGAR detection in the testing hour No. 1. (e), waveforms of the 398<sup>th</sup> SUGAR detection in the testing hour No. 1.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/fb42530309c8d060f488a2ba6775438e1e538ac2544811188b834eea77f0224b.jpg)  
Figure S8. Spectrograms of the nearest 10 stations in Figure S7a. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/ea5c7eaf64eac4d813b802a849fbeea0a62e3937e082263b4551ff03320aeba2.jpg)  
Figure S9. Spectrograms of the nearest 10 stations in Figure S7b. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/6a7d49ffa520a5d7397adba90159197a3ad09bf650892b27fe38bb4482d83d1f.jpg)  
Figure S10. Spectrograms of the nearest 10 stations in Figure S7c. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/51ab9976d29aaaba4878d20e931da2c2722459d34b3ef92fa103b0d3fe274843.jpg)  
Figure S11. Spectrograms of the nearest 10 stations in Figure S7d. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/80aef79e2a9ef1b030900187963b34393ba2f207fb41742d73d9ba1503ae9fa8.jpg)  
Figure S12. Spectrograms of the nearest 10 stations in Figure S7e. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/0eeccde0354b119a0cbd027c41aa8e5905dc39c3970e49d7e8fcae27e9073a73.jpg)  
Figure S13. Station coverage for analyst A in the real data test. Purple dots represent stations used for SUGAR. Blue triangles represent additional stations for analyst A. The red star shows the epicenter location of the $M _ { w }$ 7.8 mainshock.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/8c6d00cbc46cb638310a3c3d9aa5313a6b7bf17a1a656e68ab8301dcc7e9b060.jpg)  
Figure S14.  
April 10, 2024, 2:14pm

Four example events in the real testing hour. (a), an event at 340 s that has been detected by all the workflows and analysts. The left panel shows the vertical channel (filtered to 5–20 Hz) of the closest stations sorted by epicentral distance. Red and blue marks indicate P and S phases picked by SUGAR, respectively. Curves with corresponding colors indicate expected arrival times. The middle panel is the brightness video snapshot of the time that the event has been detected by SUGAR. The right panel is the corresponding AI score video snapshot. (b), an event at 564 s that has been detected only by SUGAR and analyst B. (c), an event at 1463 s that has only been detected by SUGAR. (d), an event at 177 s that has only been detected by SUGAR.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/439729ec07cb9165ea6b38453c149482625873e5a5bd7fc22e91a89fd654a5cb.jpg)  
Figure S15. Horizontal channels of the event in Figure S14a. The closest 25 stations are sorted by epicentral distance. Red and blue marks indicate P and S phases picked by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/4d5717700ffb857586dd8462a07642287b1d6f00cf68a4e71b784fa705a9f916.jpg)  
Figure S16. Spectrograms of the nearest 10 stations in Figure S14a. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/8ef30ae1a5909ddc145d4260563a3121658a108f09642f0be7e3e82a532a3236.jpg)  
Figure S17. Spectrograms of the nearest 10 stations in Figure S14b. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/df82ad8c04910f8966f7feac1b27f7f8cba27c34e4f8596c6f8b64db1b636e13.jpg)  
Figure S18. Spectrograms of the nearest 10 stations in Figure S14c. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/78a50527f215749da62b22d0418c260df65cdf9254b3f5a9a39e8b3325a750c1.jpg)  
Figure S19. Spectrograms of the nearest 10 stations in Figure S14d. Red and blue dashed lines mark P and S picks made by SUGAR, respectively.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/cae5602a38baf59108cf5c5f506b1b1eba0df4c6f3fc7eb0fd24d0ec5bacfca9.jpg)  
Figure S20. The raw SUGAR-derived catalog of the Kaikōura aftershocks from Nov. 13, 2016, to Dec. 31, 2016. Red lines are mainshock surface ruptures (Litchfield et al., 2018).

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/0a76209af8a4eceee1e89ecb858c5220b1392608fdde76aeaa10448e1807150a.jpg)  
Figure S21. A comparison between the SUGAR magnitude and Hutchinson et al. (2024) magnitude. The Hutchinson et al. (2024) magnitude is 0.15 larger than the SUGAR magnitude on average.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/1b405283ebd46f7cf80c45ef65ddab22722405e73f91985b908d7871c355525f.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/8e89e6fbcaf81b97362485d800d3342b3e213387e6335f7ccd29ad95cc8a5575.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/3820fadf52c6c5a21152609df411df4b5357385a41995bb01b2caa835c44bd6b.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/2430b2c2c0236adbb98994d39b652acdeeed56753df57beb89e419663779de07.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/9021a823068f1b58e9c84a22cdb9714706ca804843e9c46cf8c641650f882c7b.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/33ba799123de24c1344fe4dc3be17dde49e5b3c39995fb8c65e27be48929b1bf.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/6c856c3065ac30bf1ccdc92b7d6c8e6487a2d519b7c64dc061a801764a313a77.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/8992910cf5ebc436239f531b485819dfd58893276545471a9423203642f5541c.jpg)

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/c492f51cfd028ef62d3ef4f55cc5d8b3ea69f4a001108c64f2554f8046168736.jpg)  
Figure S22. The magnitude distribution of events in SUGAR and GeoNet catalogs. The magnitude of the GeoNet catalog is from Hutchinson et al. (2024) and the systematic magnitude diference of 0.15 has been removed. Vertical lines show the magnitude of completeness for the two catalogs. The lines connecting to dots indicate the magnitude range that is used to calculate the b value.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/0af3bd7f3dda12221d1a1d510c7d3a99981f82c6697e0a232cc0bf6fa027bcde.jpg)  
Figure S23. Waveforms and SUGAR picks of an M 4.8 earthquake 4 m after the mainshock.

![](mineru/2024jb028735-sup-0001-supporting information si-s01/images/f47e83f13eb4dac5576e505264b57f3ec606cad0a82b7d48e88ceee196fa1a79.jpg)  
Figure S24. Waveforms and SUGAR picks of an M 4.6 earthquake 23 m after the mainshock.

Table S1. Focal mechanisms used in the synthetic dataset

<table><tr><td>Strike</td><td>Dip</td><td>Rake</td></tr><tr><td>258</td><td>80</td><td>180</td></tr><tr><td>188</td><td>45</td><td>45</td></tr><tr><td>228</td><td>45</td><td>90</td></tr><tr><td>148</td><td>45</td><td>180</td></tr><tr><td>192</td><td>45</td><td>90</td></tr><tr><td>235</td><td>50</td><td>180</td></tr><tr><td>213</td><td>60</td><td>90</td></tr><tr><td>225</td><td>70</td><td>135</td></tr><tr><td>240</td><td>70</td><td>180</td></tr><tr><td>220</td><td>70</td><td>180</td></tr><tr><td>155</td><td>45</td><td>0</td></tr><tr><td>226</td><td>25</td><td>135</td></tr><tr><td>219</td><td>38</td><td>128</td></tr></table>

Table S2. Summary of the synthetic test results for hour No. 1

<table><tr><td>Catalog</td><td>Number of Events</td><td>Precisian</td><td>Recall</td><td> $F_1$  value</td></tr><tr><td>Ground Truth</td><td>511</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Analyst</td><td>151</td><td>0.72</td><td>0.21</td><td>0.33</td></tr><tr><td>SUGAR 1.0</td><td>423</td><td>0.94</td><td>0.78</td><td>0.85</td></tr><tr><td>SUGAR 2.3</td><td>385</td><td>0.98</td><td>0.74</td><td>0.84</td></tr></table>

Table S3. Summary of the synthetic test results for hour No. 2

<table><tr><td>Catalog</td><td>Number of Events</td><td>Precisian</td><td>Recall</td><td> $F_1$  value</td></tr><tr><td>Ground Truth</td><td>356</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Analyst</td><td>165</td><td>0.78</td><td>0.36</td><td>0.50</td></tr><tr><td>SUGAR 1.0</td><td>326</td><td>0.94</td><td>0.86</td><td>0.90</td></tr><tr><td>SUGAR 2.3</td><td>302</td><td>0.99</td><td>0.84</td><td>0.91</td></tr></table>

Table S4. Summary of the synthetic test results for hour No. 3

<table><tr><td>Catalog</td><td>Number of Events</td><td>Precisian</td><td>Recall</td><td> $F_1$  value</td></tr><tr><td>Ground Truth</td><td>190</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Analyst</td><td>115</td><td>0.88</td><td>0.53</td><td>0.66</td></tr><tr><td>SUGAR 1.0</td><td>188</td><td>0.93</td><td>0.92</td><td>0.93</td></tr><tr><td>SUGAR 2.3</td><td>177</td><td>0.97</td><td>0.91</td><td>0.94</td></tr></table>

Table S5. Summary of the synthetic test results for hour No. 4

<table><tr><td>Catalog</td><td>Number of Events</td><td>Precisian</td><td>Recall</td><td> $F_1$  value</td></tr><tr><td>Ground Truth</td><td>118</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Analyst</td><td>89</td><td>0.88</td><td>0.66</td><td>0.75</td></tr><tr><td>SUGAR 1.0</td><td>116</td><td>0.95</td><td>0.93</td><td>0.94</td></tr><tr><td>SUGAR 2.3</td><td>111</td><td>0.98</td><td>0.92</td><td>0.95</td></tr></table>

April 10, 2024, 2:14pm

Table S6. Summary of the synthetic test results for hour No. 5

<table><tr><td>Catalog</td><td>Number of Events</td><td>Precisian</td><td>Recall</td><td> $F_1$  value</td></tr><tr><td>Ground Truth</td><td>21</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Analyst</td><td>21</td><td>0.95</td><td>0.95</td><td>0.95</td></tr><tr><td>SUGAR 1.0</td><td>22</td><td>0.95</td><td>1.00</td><td>0.98</td></tr><tr><td>SUGAR 2.3</td><td>21</td><td>1.00</td><td>1.00</td><td>1.00</td></tr></table>

Table S7. The catalog of the eight closely-timed synthetic events discussed in the section 3.2

<table><tr><td>No.</td><td>Origin time (s)</td><td>Latitude</td><td>Longitude</td><td>Dep (km)</td><td>Magnitude</td></tr><tr><td>1</td><td>0.8</td><td>-41.7311</td><td>174.2873</td><td>9.6</td><td>4.0</td></tr><tr><td>2</td><td>1.0</td><td>-42.3622</td><td>173.7185</td><td>3.8</td><td>3.1</td></tr><tr><td>3</td><td>1.4</td><td>-41.9137</td><td>174.0227</td><td>11.8</td><td>3.6</td></tr><tr><td>4</td><td>27.2</td><td>-41.6824</td><td>174.2815</td><td>10.8</td><td>4.6</td></tr><tr><td>5</td><td>36.0</td><td>-42.4960</td><td>173.3521</td><td>5.0</td><td>3.5</td></tr><tr><td>6</td><td>36.2</td><td>-41.8427</td><td>174.0101</td><td>12.4</td><td>3.1</td></tr><tr><td>7</td><td>38.0</td><td>-41.7174</td><td>174.1468</td><td>7.5</td><td>3.8</td></tr><tr><td>8</td><td>43.3</td><td>-42.3293</td><td>173.9274</td><td>12.2</td><td>3.3</td></tr></table>

Table S8. Parameter setting of SUGAR in the application to the 2016 Kaikōura sequence

<table><tr><td>Process</td><td>Parameter</td><td>Value</td></tr><tr><td rowspan="7">1</td><td>Frequency band</td><td>5–20 Hz</td></tr><tr><td>Window duration</td><td>6 s</td></tr><tr><td>Stacking increment</td><td>0.5 s</td></tr><tr><td>Sampling rate</td><td>50 Hz</td></tr><tr><td>Scanning depth</td><td>10 km</td></tr><tr><td>Scanning grid spacing</td><td>4 km</td></tr><tr><td>Velocity model</td><td>3D</td></tr><tr><td>2</td><td>Score threshold</td><td>1.0</td></tr><tr><td rowspan="8">3</td><td>EQT overlap</td><td>0.7</td></tr><tr><td>EQT detection threshold</td><td>0.3</td></tr><tr><td>EQT P/S threshold</td><td>0.1</td></tr><tr><td>Brightness threshold</td><td>50</td></tr><tr><td>Initial locating grid spacing</td><td>2 km</td></tr><tr><td>Locating depth range</td><td>0–60 km</td></tr><tr><td>Initial locating depth spacing</td><td>4 km</td></tr><tr><td>Velocity model</td><td>3D</td></tr><tr><td>4</td><td>Amplitude searching duration</td><td>30 s</td></tr></table>

Table S9. The detailed station information of the 46 stations used in the study (Figure 1)  
Table S10. The original SUGAR catalog from Nov. 13 to Dec. 31, 2016

Table S11. The relocated SUGAR catalog from Nov. 13 to Dec. 31, 2016

Table S12. Focal mechanism solutions of the 55 additional earthquakes in this study

## References

Çiçek, O., Abdulkadir, A., Lienkamp, S. S., Brox, T., & Ronneberger, O. (2016). 3D U-Net: learning dense volumetric segmentation from sparse annotation. arXiv:1606.06650 [cs.CV]. Eberhart-Phillips, D., Bannister, S., Reyners, M., & Henrys, S. (2020). New Zealand wide model 2.2 seismic velocity and Qs and Qp models for New Zealand [Data set]. Zenodo. [Dataset]. Retrieved from https://zenodo.org/records/3779523

GNS Science. (1970). GeoNet Aotearoa New Zealand Earthquake Catalogue. [Dataset]. GNS Science, GeoNet. Retrieved from https://www.geonet.org.nz/data/types/eq\_catalogue doi: 10.21420/0S8P-TZ38

Gutenberg, B., & Richter, C. F. (1944). Frequency of earthquakes in California. Bulletin of the Seismological Society of America, 34, 185–188.

Harrington, R. M., & Brodsky, E. E. (2009). Source Duration Scales with Magnitude Diferently for Earthquakes on the San Andreas Fault and on Secondary Faults in Parkfield, CaliforniaSource Duration Scales with Magnitude Diferently on the San Andreas Fault and on Secondary Faults. Bulletin of the Seismological Society of America, 99(4), 2323–2334. doi: 10.1785/0120080216

Kao, H., & Shan, S.-J. (2004). The Source-Scanning Algorithm: mapping the distribution of seismic sources in time and space. Geophysical Journal International, 157(2), 589–594.

Kennett, B. L. N., & Engdahl, E. R. (1991). Traveltimes for global earthquake location and phase identification. Geophysical Journal International, 105(2), 429–465. doi: 10.1111/ j.1365-246X.1991.tb06724.x

Kingma, D. P., & Ba, J. (2014). Adam: a method for stochastic optimization. arXiv:1412.6980 [cs.LG].

Litchfield, N. J., Villamor, P., Dissen, R. J. V., Nicol, A., Barnes, P. M., A. Barrell, D. J., … Zinke, R. (2018). Surface rupture of multiple crustal faults in the 2016 Mw 7.8 Kaikōura, New Zealand, earthquake. Bulletin of the Seismological Society of America, 108(3B), 1496– 1520.

Tan, F., Kao, H., Nissen, E., & Visser, R. (2020). Tracking earthquake sequences in real time: application of Seismicity-Scanning based on Navigated Automatic Phase-picking (S-SNAP) to the 2019 Ridgecrest, California sequence. Geophysical Journal International, 223(3), 1511–1524. doi: 10.1093/gji/ggaa387

Zhu, L., & Rivera, L. A. (2002). A note on the dynamic and static displacements from a point source in multilayered media. Geophysical Journal International, 148(3), 619–627.