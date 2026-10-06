Below is a concise, plot-by-plot summary of all visualizations in the example, including what is shown, how it is produced (matplotlib calls), the inputs and outputs (with parameters as used), and the intended interpretation. Each figure has two subplots; each subplot is summarized separately and paired with the exact code used to produce it.

Figure 1 — Synthetic data visualization (two subplots)

Left subplot: “P/S phase picks”
- What to plot:
  - All generated phase picks (P and S) as a function of time (x-axis) and station distance (y-axis).
  - If use_amplitude is True, bubble size encodes phase amplitude via s=(4**phase_amp)*1e3; otherwise a fixed size (s=12).
- How to plot:
  - Matplotlib scatter plot via plt.scatter.
  - Plot configuration: grey markers, circle marker "o", alpha=0.8, legend entry added via a dummy off-plot point at (-1, -1).
  - Axes configuration: xlim left bound at 0, ylim set to xlim variable (distance range), labels, legend, and an in-axes text annotation “(i)”.
- Inputs:
  - phase_time (x), phase_loc (y), phase_amp (for marker size when use_amplitude=True)
  - Global config and styling variables: use_amplitude, xlim, text_loc = [0.05, 0.95], box = dict(boxstyle='round', facecolor='white', alpha=1)
- Outputs:
  - A scatter plot titled “P/S phase picks” displayed in the left panel of Figure 1.

Code that produces this subplot:
```python
plt.figure()
text_loc = [0.05, 0.95]
box = dict(boxstyle='round', facecolor='white', alpha=1)
plt.subplot(121)
if use_amplitude:
    plt.scatter(phase_time, phase_loc, s=(4**np.array(phase_amp))*1e3, color="grey",  marker="o", alpha=0.8)
else:
    plt.scatter(phase_time, phase_loc, s=12, color="grey",  marker="o", alpha=0.8)
plt.scatter(-1, -1, s=24, color="grey",  marker="o", alpha=0.8, label="Picks")
plt.xlim(left=0)
plt.ylim(xlim)
ylim_ = plt.ylim()
xlim_ = plt.xlim()
plt.ylabel("Distance (km)")
plt.xlabel("Time (s)")
plt.legend()
plt.text(text_loc[0], text_loc[1], '(i)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("P/S phase picks")
```
Interpretation:
- Visual check of the simulated P/S arrival times across stations; marker size reflects amplitude if used.

Right subplot: “Ground truth”
- What to plot:
  - Picks associated with true events colored by their event index; unassociated (fake) picks in grey.
  - True event origins plotted as “Earthquakes” using a pointed “P” marker at (event_t0, event_loc), with size proportional to 5**event_mag*3.
- How to plot:
  - Matplotlib scatter; two scatter calls for associated vs fake picks; event markers plotted in a loop.
  - Y-axis tick labels removed; same x/y limits as left plot; legend and “(ii)” annotation.
- Inputs:
  - phase_time, phase_loc, phase_amp, phase_event_idx, event_t0, event_loc, event_mag, num_event, use_amplitude
  - Reuse xlim_ and ylim_ captured from the left subplot so the panels align.
- Outputs:
  - A scatter plot titled “Ground truth” displayed in the right panel of Figure 1.

Code that produces this subplot:
```python
plt.subplot(122)
if use_amplitude:
    plt.scatter(phase_time[phase_event_idx!=num_event], phase_loc[phase_event_idx!=num_event], \
                s=(4**np.array(phase_amp[phase_event_idx!=num_event]))*1e3, \
                color=[f"C{x}"for x in phase_event_idx[phase_event_idx!=num_event]],  marker="o", facecolors='none')
    plt.scatter(phase_time[phase_event_idx==num_event], phase_loc[phase_event_idx==num_event], \
                s=(4**np.array(phase_amp[phase_event_idx==num_event]))*1e3, \
                color="grey",  marker="o", alpha=0.8)
else:
    plt.scatter(phase_time[phase_event_idx!=num_event], phase_loc[phase_event_idx!=num_event], \
                s=12, \
                color=[f"C{x}"for x in phase_event_idx[phase_event_idx!=num_event]],  marker="o", facecolors='none')
    plt.scatter(phase_time[phase_event_idx==num_event], phase_loc[phase_event_idx==num_event], \
                s=12, \
                color="grey",  marker="o", alpha=0.8)
plt.scatter(-1, -1, s=24, color="C0",  marker="o", facecolors='none', label="Associated picks")
for i in range(len(event_mag)):
    plt.scatter(event_t0[i], event_loc[i], s=5**np.array(event_mag[i])*3, color=f"C{i}", marker="P")
plt.scatter(-1, -1, s=48, color="C0", marker="P", label="Earthquakes")
plt.xlim(xlim_)
plt.ylim(ylim_)
plt.xlabel("Time (s)")
# plt.ylabel("Distance (km)")
plt.gca().yaxis.set_ticklabels([])
plt.legend()
plt.text(text_loc[0], text_loc[1], '(ii)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("Ground truth")
plt.show();
```
Interpretation:
- Shows the true association of picks to events and the true event origin points; serves as a baseline for later model predictions.

Figure 2 — GaMMA results (two subplots)

Left subplot: “P/S phase picks” (repeated data view)
- What to plot:
  - Same as Figure 1, left panel; re-establishes the pick field for side-by-side comparison with model predictions.
- How to plot:
  - Identical matplotlib scatter sequence as the first panel in Figure 1.
- Inputs:
  - phase_time, phase_loc, phase_amp, use_amplitude, xlim, text_loc, box.
- Outputs:
  - A scatter plot titled “P/S phase picks” in the left panel of Figure 2.

Code that produces this subplot:
```python
plt.figure()
plt.subplot(121)
if use_amplitude:
    plt.scatter(phase_time, phase_loc, s=(4**np.array(phase_amp))*1e3, color="grey",  marker="o", alpha=0.8)
else:
    plt.scatter(phase_time, phase_loc, s=12, color="grey",  marker="o", alpha=0.8)
plt.scatter(-1, -1, s=24, color="grey",  marker="o", alpha=0.8, label="Picks")
plt.xlim(left=0)
plt.ylim(xlim)
ylim_ = plt.ylim()
xlim_ = plt.xlim()
plt.ylabel("Distance (km)")
plt.xlabel("Time (s)")
plt.legend()
plt.text(text_loc[0], text_loc[1], '(i)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("P/S phase picks")
```
Interpretation:
- Repeats the data scatter for visual consistency before overlaying model outputs.

Right subplot: “GMMA prediction”
- What to plot:
  - Model-associated picks per predicted event/component after running BayesianGaussianMixture (GaMMA), filtered to components with at least min_picks observations.
  - Event centers inferred by GaMMA (gmm.centers_) plotted as “Earthquakes” (marker "P"), sized by 4**gmm.centers_[i,2]*3 when use_amplitude=True; otherwise fixed markersize=8 via plt.plot for the center.
- How to plot:
  - Matplotlib scatter; color cycles per detected event (C0, C1, …) following a sorted order by event time gmm.centers_[:, 1].
  - Picks: plotted with hollow circles (facecolors='none'); sizes scale with amplitude if applicable.
  - Centers: plotted at (t0, loc) from gmm.centers_ with pointed “P” marker; size depends on whether amplitude is modeled.
  - Legend entries created via off-plot dummy scatters; y-tick labels hidden; “(iii)” annotation added; axes share limits with the left panel.
- Inputs:
  - data[:, 0] (time), phase_loc[:, 0] (distance), pred (cluster assignments), gmm.centers_, std_eq (covariances), filtered_idx (component filter), use_amplitude, xlim_, ylim_, text_loc, box.
  - The code uses np.argsort(gmm.centers_[:, 1]) to order components by time.
- Outputs:
  - A scatter overlay of GaMMA-associated picks and inferred event centers; printed console lines with estimated parameters per event; a titled figure “GMMA prediction”.

Code that produces this subplot:
```python
plt.subplot(122)
colors = defaultdict(int)
idx = np.argsort(gmm.centers_[:, 1])
dum = 0
print("Associated events:")
for i in idx:
    if i in filtered_idx:
        if not use_amplitude:
            plt.scatter(data[(pred==i), 0], phase_loc[(pred==i), 0], color=f"C{dum}", s=12, marker='o', facecolors='none')
            plt.plot(gmm.centers_[i, 1], gmm.centers_[i, 0], "P", c=f"C{dum}", markersize=8)
            print(f"loc={gmm.centers_[i, 0]:.1f}\tt0={gmm.centers_[i, 1]:.1f}\tsigma11={std_eq[i,0,0]:.3f}")
        else:
            plt.scatter(data[(pred==i), 0], phase_loc[(pred==i), 0], color=f"C{dum}", s=4**(data[(pred==i), 1])*1e3, marker='o', facecolors='none')
            plt.scatter(gmm.centers_[i, 1], gmm.centers_[i, 0], color=f"C{dum}", s=4**gmm.centers_[i, 2]*3, marker="P")
            print(f"loc={gmm.centers_[i, 0]:.1f}\tt0={gmm.centers_[i, 1]:.1f}\tmag={gmm.centers_[i, 2]:.1f}\tsigma11={std_eq[i,0,0]:.3f}")
        dum += 1
plt.scatter(-1, -1, s=24, color="C0",  marker="o", facecolors='none', label="Associated picks")
plt.scatter(-1, -1, s=48, color="C0", marker="P", label="Earthquakes")
plt.xlim(xlim_)
plt.ylim(ylim_)
plt.xlabel("Time (s)")
plt.gca().yaxis.set_ticklabels([])
plt.legend()
plt.text(text_loc[0], text_loc[1], '(iii)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("GMMA prediction")
plt.show()
```
Interpretation:
- Visualizes GaMMA’s association of picks to events and its estimated event centers; serves to compare model predictions to the earlier “Ground truth” view. Picks’ sizes and event marker sizes reflect modeled amplitudes when enabled.

General plotting details across figures
- Library:
  - matplotlib.pyplot as plt
- Display:
  - Figures are rendered with plt.show() at the end of each figure block.
- Legends:
  - Created using dummy scatter points at (-1, -1) to control labels and marker styles.
- Annotations:
  - Subplots are annotated with “(i)”, “(ii)”, and “(iii)” via plt.text using:
    - text_loc = [0.05, 0.95]
    - box = dict(boxstyle='round', facecolor='white', alpha=1)
- Axes:
  - Left subplots set xlim(left=0) and ylim(xlim). Right subplots reuse xlim_/ylim_ captured from the left subplot to ensure matched limits.
- Conditional sizing by amplitude:
  - When use_amplitude is True:
    - Pick size s=(4**phase_amp)*1e3
    - True event marker size s=5**event_mag*3
    - Predicted event center size s=4**gmm.centers_[i, 2]*3
  - When use_amplitude is False:
    - Pick size s=12; predicted center plotted with markersize=8.
