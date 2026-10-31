# Seismology precedent for small-batch-first (pilot window → freeze → full run)

- Scope: a limited search (about 1.5 h). The question was whether published earthquake-catalog workflows explicitly tune parameters on a short pilot window or subset before full processing, or discuss whether parameters transfer from subset to full data.
- Method:
  - arXiv API and web search, with queries on QuakeFlow, LOC-FLOW, FAST/template matching, ML-picker catalogs, parameter sensitivity and pilot windows;
  - full-text reading of the sources marked "read" below.
- Bottom line: no source found systematizes a pilot-window protocol (representative subset, adoption rules, freeze, full-scale re-validation) for catalog building. Practice is ad hoc: "trial and error", "several tests", "visual inspection", defaults. Transfer from subset to full data is either not discussed or flagged as an open problem. This is a negative result of a bounded search, not proof of absence.

## Sources read (full text)

- **QuakeFlow.**
  - Zhu, W., Hou, A. B., Yang, R., Datta, A., Mousavi, S. M., Ellsworth, W. L., Beroza, G. C. "QuakeFlow: A Scalable Machine-learning-based Earthquake Monitoring Workflow with Cloud Computing". arXiv 2208.14564v1 (GJI 2023). https://arxiv.org/abs/2208.14564
  - The paper describes a scalable cloud pipeline (PhaseNet → GaMMA → location) applied to Puerto Rico and Hawaii, plus a "simple pressure test" of compute scaling.
  - On parameters: "The exact number of earthquakes will vary depending on the hyperparameters, and there exists a trade-off between false positives and false negatives in both the standard catalog and the QuakeFlow catalog. Detailed comparison between these catalogs, and quantification of this trade-off, is an important direction for future research." (Puerto Rico results, p. 9 of the arXiv PDF).
  - There is no pilot or tuning protocol.
- **FAST.**
  - Yoon, C. E., Bergen, K. J., Rong, K., et al. (2019). "Unsupervised Large-Scale Search for Similar Earthquake Signals". BSSA. PDF https://www.its.caltech.edu/~cyoon/img/Yoon2019_BSSA_FAST_Unsupervised_LargeScale.pdf
  - Parameter choice for the most important search parameter was made on the long dataset itself: "The similarity search parameter r ... has the most significant effect on both detection performance and runtime. Through trial and error, we found that r = 6 was the best compromise for this long-duration data set (Table A2); setting r = 7 would result in too few earthquake detections, whereas setting r = 5 would increase false detections, make the output pairs files too large, and unacceptably increase the runtime."
  - The paper also notes that "Different choices of r and other similarity search parameters (Table A2) can result in nearly identical detection probabilities with very different runtimes (Rong et al., 2018)".
  - Implication: one sensitive parameter's acceptable value depends on dataset duration and noise (output size, repeating noise), so a short pilot may not transfer for such duration-dependent parameters.
- **Durrës aftershocks.**
  - Woollam, J., et al. "Machine learning event detection workflows in practice: A case study from the 2019 Durrës aftershock sequence". arXiv 2205.12033v1. https://arxiv.org/abs/2205.12033
  - Picker thresholds: "for both picking algorithms we use the default value from the original publications". Threshold sensitivity is reported after the fact in an appendix (pick counts vs. cut-off).
  - Validation used a "small subset of events" picked by two independent analysts (219 events vs. 3,551 and 1,110 ML detections). The subset is a benchmark, not a tuning pilot.
- **SeisBench picker benchmark.**
  - Münchmeyer, J., Woollam, J., Rietbrock, A., Tilmann, F., et al. "Which picker fits my data? A quantitative evaluation of deep learning based seismic pickers". arXiv 2110.13671 (JGR 2022). https://arxiv.org/abs/2110.13671
  - Closest to a tune-then-transfer rule, but for pickers on labelled benchmark data, not catalog pipelines: "For each of the tasks we select the optimal thresholds on the development sets ... For cross-dataset analysis, we select the model based on the loss on the development set of the source dataset and select the threshold on the development set of the target dataset" (Sec. 2.4).
  - Discussion: "Even though the optimal threshold will depend on the application scenario, the provided values give an orientation for threshold selection."
- **Kefalonia swarm.**
  - Anagnostou, V., Papadimitriou, E., et al. "Investigating the 2024 swarm-like activity offshore Kefalonia Island, aided by Machine Learning algorithms". arXiv 2505.17221. https://arxiv.org/abs/2505.17221
  - Typical practice: "We require at least 8 seismic phases (both P and S) from at least 4 stations ... The above constraints are chosen after multiple association tests and visual inspection of the waveforms that correspond to the lower quality associated earthquakes."
  - The paper does not say on which subset the tests were run or how they were adopted.

## Sources seen only as search snippets (not verified; do not cite without reading)

- LOC-FLOW (Zhang, M., Liu, M., Feng, T., Wang, R., Zhu, W., 2022, SRL 93(5), doi 10.1785/0220220019). The search surfaced only the abstract (a "hands-free" workflow on 16 days of Parkfield data) and independent applications (Sugan et al. 2023, GNHR; Duan et al. 2023, Earthquake Science) that report recall against manual catalogs. No pilot-tuning section was found. The CookBook on GitHub was not read.
- A Marmara template-matching study reportedly used "a particular day with a seismic swarm of 49 co-located events to define the detection threshold and templates selection". This is the nearest thing to a pilot window found, but the source was not identified precisely enough to cite.
- A "phase associator comparison for small-scale networks" abstract (SSA) reportedly needed "additional tuning ... in the location phase to prevent the inclusion of a significant number of false" events. Tuning was against analyst catalogs.
- An OSTI report titled "Variability in Performance of a Machine-Learning Seismicity Catalog" looks directly relevant to parameter sensitivity but was not read.
- Mousavi & Beroza (2023), "Machine Learning in Earthquake Seismology", Annu. Rev. Earth Planet. Sci., doi 10.1146/annurev-earth-071822-100323. A review, not read; worth checking for any best-practice statement on tuning.

## Synthesis

- **Common practice (documented):**
  - defaults from the original publications;
  - trial and error on the full dataset;
  - "several tests" plus visual inspection on unspecified subsets;
  - validation against an analyst-picked subset or an existing catalog after the fact.
- **Recognised but unquantified:** catalog size and quality depend on hyperparameters, with a false-positive/false-negative trade-off (QuakeFlow says quantifying it is future work). Some parameters' best values depend on data duration and noise (FAST).
- **Not found:**
  - a written protocol that (i) selects a representative pilot window by stated criteria, (ii) tunes with pre-registered adoption rules, (iii) freezes, and (iv) re-validates at full scale with the same diagnostics;
  - any study measuring how well pilot-window choices transfer to full sequences.

## Implication for us

- **Novelty claim.** We can claim to systematise and test a practice that seismologists perform informally. The safe wording is: "to our knowledge, published catalog workflows describe parameter choice as trial and error or default-based, and do not report pilot-to-full transfer". Avoid "no one tunes on subsets".
- **Representativeness criteria.** The pilot window should cover the regimes the parameters are sensitive to:
  - high-rate aftershock periods, where pick density drives association and false events (QuakeFlow, Durrës);
  - quiet background, for the false-positive rate;
  - the full station set.
- **Duration-dependent parameters.** Treat parameters such as FAST's r, template-matching thresholds expressed as MAD multiples over a day, and association windows under high rates as needing a full-scale re-check, not just freezing.
- **Before citing.** Read LOC-FLOW (SRL 2022) and the Mousavi & Beroza (2023) review.
