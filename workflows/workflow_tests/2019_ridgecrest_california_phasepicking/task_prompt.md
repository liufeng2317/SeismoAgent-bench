## 2019 Ridgecrest M7.1 phase picking

### Task objective

Process the Ridgecrest waveform data for the UTC interval `[2019-07-05T00:00:00Z, 2019-07-06T00:00:00Z)`. Preprocess the waveforms, pick P and S arrivals, and provide concise visual and tabular results that can be inspected and reproduced.

### Input data

The input data contain waveforms and corresponding station infomation. The waveform directory contains the miniSEED data. The StationXML file provides station coordinates and metadata. Read the inputs only; do not modify,rename, delete or replace them.
- Seismic waveform data: `input/waveforms/data/`
- Seismic station infomation: `input/waveforms/stations/earthscope.stationxml`

### Task procedure

1.  write a concise `task_plan.md` describing workflow planing.
2.  Then save complete, reusable processing code based on that plan and run the saved code to generate the final results.

### Required outputs

For better visualize and reproducesng, write at least the following files in the assigned output directory:

- `output/task_plan.md`: task planning and method description;
- `output/station_distribution_waveform.png`: one figure showing station distribution and some representative raw waveform data;
- `output/waveform_processing.png`: one figure showing the main waveform preprocessing stages;
- `output/phase_picks.png`: one figure showing representative P/S picking results;
- `output/picks.csv`: the phase-pick table with station, channel, phase, arrival time
  and confidence columns.
