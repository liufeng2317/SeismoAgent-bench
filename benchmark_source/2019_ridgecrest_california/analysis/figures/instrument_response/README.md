# Ridgecrest instrument response audit and trial removal

Generated: 2026-09-25T00:00:04.306536+00:00; ObsPy 1.5.0.

## Availability

The previously downloaded `data/waveforms/stations/earthscope.stationxml` already contains usable response stages for **117/117 observed candidate channels**. No additional download was needed. This file is in the shared external archive through the case waveform symlink; it is not a second local copy. This result is restricted to the current candidate inventory, not every regional station or every published catalog input.

`response_audit.csv` records exact NSLC, observed time bounds, sample rate, matching epoch count, stage count, sensitivity and units, orientation, warnings and status. Each response epoch must cover the observed bounds and match the rate unambiguously. A 100-point logarithmic frequency grid from 0.5 to 20 Hz must evaluate to finite, nonzero velocity responses. This is a numerical/metadata usability check, not an independent calibration or sensor operating-range certification. Multiple epochs across an observed span are deliberately rejected for explicit review instead of silently selecting one.

## Removal trial

[Raw counts, corrected velocity and corrected spectra](01_response_removed.png) ([PDF](01_response_removed.pdf)); [response curves](02_response_curves.png) ([PDF](02_response_curves.pdf)).

Three vertical channels around the Mw 7.1 origin (2019-07-06 03:19:53.040 UTC) are processed over −120 to +240 s; plots show −30 to +120 s. Adjacent segments may merge, but a gap aborts this example. Original samples are read-only. Linear detrending precedes ObsPy `Trace.remove_response(inventory=inv, output="VEL", pre_filt=(0.5, 1, 15, 20), water_level=None, zero_mean=True, taper=True, taper_fraction=0.05)`. Output is m/s for both native HH velocity and HN acceleration inputs. No extra bandpass, resampling, normalization or rotation is applied. The frequency taper passes 1–15 Hz and tapers to zero at 0.5 and 20 Hz; these exploratory settings are not frozen processing parameters. Welch PSD uses the displayed corrected data, Hann windows of 4096 samples, 50% overlap, constant detrending and density scaling.

We use `water_level=None` with an explicit frequency taper because requesting velocity from an accelerometer can otherwise suppress wanted frequencies with a water-level cutoff; see the [ObsPy remove_response documentation](https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.remove_response.html). This does not validate the frequency band for every instrument or eliminate edge effects. The earlier 2–12 Hz counts-filtering figure uses different processing and is not a controlled response-only comparison.

`response_examples.npz` is one small derived demonstration bundle with numeric raw/corrected arrays, sample times, source paths, units and processing settings (load with `numpy.load(..., allow_pickle=False)`). It is outside the raw archive. No full-day processed waveform files or duplicate response JSON files are generated.

## Interpretation

Response removal ran successfully on all three examples, preserving sample counts and start times with finite outputs. It does not restore saturation-distorted signal. CI.CCC and CI.WRC2 mainshock intervals remain suspected saturation cases from the prior raw-waveform review; calibrated values there must not be accepted as reliable peak ground velocity. Different stations also record different propagation/site effects; matching units does not make them identical inputs. Next, validate operating ranges and select reliable intervals before amplitude analysis or freezing preprocessing.

Trial diagnostics (displayed-window maxima; not validated PGV):

- `CI.CCC..HHZ`: max |velocity| 0.0207935 m/s; warnings: none.
- `CI.APL..HNZ`: max |velocity| 0.0172179 m/s; warnings: none.
- `CI.WRC2..HHZ`: max |velocity| 0.0220167 m/s; warnings: none.
