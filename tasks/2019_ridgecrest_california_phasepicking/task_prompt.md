### Task objective

Process the Ridgecrest waveform data for the UTC interval `[2019-07-05T00:00:00Z, 2019-07-06T00:00:00Z)`. Preprocess the waveforms, pick P and S arrivals, and provide concise visual and tabular results that can be inspected and reproduced.

### Input data

The input data contain waveforms and corresponding station infomation. The waveform directory contains the miniSEED data. The StationXML file provides station coordinates and metadata. Read the inputs only; do not modify,rename, delete or replace them.
- Seismic waveform data: `input/data/`
- Seismic station infomation: `input/stations/earthscope.stationxml`

### Task procedure

First write a concise `task_plan.md` describing the selected time window, input files, preprocessing steps, phase-picking method and quality checks. Then write a complete, reusable `processing_script.py` based on that plan and run the saved script to generate the final results. Record the method, parameters, assumptions and unresolved data quality issues in the plan or in the result files.

### Required outputs

For better visualize and reproducesng, write at least the following files in the assigned output directory:

- `task_plan.md`: task planning and method description;
- `processing_script.py`: the executable code used to produce the results;
- `station_distribution_waveform.png`: one figure showing station
  distribution and representative raw waveform data;
- `preprocessing.png`: one figure showing the main waveform preprocessing
  stages;
- `phase_picks.png`: one figure showing representative P/S picking results;
- `picks.csv`: the phase-pick table with station, channel, phase, arrival time
  and confidence columns.

Keep missing or uncertain picks explicit. Do not invent arrivals to fill gaps. The saved script and the recorded runtime environment must be sufficient to reproduce the outputs from the declared input data.
