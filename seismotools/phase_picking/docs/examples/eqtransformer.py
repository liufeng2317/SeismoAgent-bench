"""
This file shows a custom inference example. For standard usage, please refer to SeisBench standard usage (`model.classify`, and `model.annotate`).
Copy the related function like `normalize` and `detect_single_sequence` to your own code directly!!!

There are 2 different types of the inference methods, for phase picking methods: 
* First preferred: using `model.classify` to get the picks directly with given P_threshold and S_threshold
* Second preferred: using `model.annotate` to get the probability, and then manually pick the phase with given threshold (largest probability)

Details of the inference methods:
1. First Preferred (Recommended): using the model.classify method to directly get the P and S picks
    - the output is a list of picks, which contains the phase and the peak time and the peak probability value
        - method to get the picks:
            *  'peak.__str__()': transform the pick to a string
            *  'peak.peak_time': get the peak time of the pick (UTCDateTime)
            *  'peak.peak_value': get the peak probability value of the pick (float)
            *  'peak.phase': get the phase of the pick (P or S)
            *  'peak.trace_id': get the trace id of the pick (network_station)
2. Second Preferred: using the model.annotate method to get the probability
    - the input and output data are obspy stream object (construct header information with given value, or random set the head)
    - extract the **largest probability** with given threshold (if required just one pick)

Notes 
* The ouput order of the inference is based on `phases` in the model.get_model_args(), so the result should be reordered according to the NPS
* For EQTransformer and OBSTransformer, the output probability is the [Detection, P phase, S phase]
* For PhaseNet, PhaseNetlight, dpppicker, gpd, and skynet, the output probability is the [Noise, P phase, S phase]
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import torch
import os
import sys
import obspy
from obspy import Stream, Trace, UTCDateTime
import numpy as np
import torch.nn.functional as F
import json

# Step1: add the seismoagent base path to the sys.path (must be done)
seismoagent_base_path = "/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/TRACE-1.1/seismoagent"
sys.path.append(os.path.join(seismoagent_base_path,'library','ai_module'))
from phase_picking.model.eqtransformer import EQTransformer

# Step2: define the pretrained model path
pretrained_path = os.path.join(seismoagent_base_path,"library/ai_module/phase_picking/pretrained/v3/eqtransformer/stead.pt.v2")
# the config of pretrained model is saved as a json file by replace the "pt" with "json"
# e.g. ethz.pt -> ethz.json; original.pt.v2 -> original.json.v2; stead.pt.v2 -> stead.json.v2
pretrained_param_path = pretrained_path.replace("pt","json")
pretrained_args = json.load(open(pretrained_param_path))

# ------------------------------------------------------------------------------------
# recommended method: using the model.classify method (from the seisbench)
# ------------------------------------------------------------------------------------
def inference1(st, model, overlap=None, P_threshold=0.3, S_threshold=0.3, single_pick=False):
    """
    Continuous seismic phase picking (picks) using SeisBench model.

    Args:
        st (obspy.Stream): input waveform stream, any length, multi-component supported
        model (SeisBench model): pretrained phase picking model
        overlap (int): overlap length
        P_threshold (float): P threshold
        S_threshold (float): S threshold
        single_pick (bool): whether to return a single pick (largest probability pick)

    Returns:
        ppicks_list: list of P picks (UTCDateTime)
        spicks_list: list of S picks (UTCDateTime)
    """
    if overlap is None:
        output = model.classify(st, P_threshold=P_threshold, S_threshold=S_threshold)
    else:
        output = model.classify(st, overlap=overlap, P_threshold=P_threshold, S_threshold=S_threshold)
    
    # process the classify result
    ppicks_t_list, spicks_t_list = [], []
    ppicks_v_list, spicks_v_list = [], []
    for pick in output.picks:
        pick_type = pick.phase
        pick_t = pick.peak_time
        pick_v = pick.peak_value
        if pick_type.lower() in ["p"]:
            ppicks_t_list.append(UTCDateTime(pick_t))
            ppicks_v_list.append(pick_v)
        elif pick_type.lower() in ["s"]:
            spicks_t_list.append(UTCDateTime(pick_t))
            spicks_v_list.append(pick_v)
    ppicks_t_list = np.array(ppicks_t_list)
    spicks_t_list = np.array(spicks_t_list)
    ppicks_v_list = np.array(ppicks_v_list)
    spicks_v_list = np.array(spicks_v_list)
    
    # if just require one pick, return the largest probability pick
    if single_pick and len(ppicks_t_list) > 0:
        largest_p_index = np.argmax(ppicks_v_list)
        ppicks_t_list = [ppicks_t_list[largest_p_index]]
    if single_pick and len(spicks_t_list) > 0:
        largest_s_index = np.argmax(spicks_v_list)
        spicks_t_list = [spicks_t_list[largest_s_index]]
    
    return ppicks_t_list, spicks_t_list

# ------------------------------------------------------------------------------------
# second preferred method: using the model.annotate method (seisbench usage for the model)
# ------------------------------------------------------------------------------------
def normalize(data, mode = 'max'):   
    """
        Normalize waveforms
        input:
            data : 2D array like, [c,N]
        ouput:
            data : 2D array 
    """
    data -= np.mean(data, axis=1, keepdims=True)
    if mode == 'max':
        max_data = np.max(np.abs(data), axis=1, keepdims=True)
        assert(max_data.shape[0] == data.shape[0])
        max_data[max_data == 0] = 1
        data /= max_data              

    elif mode == 'std':               
        std_data = np.std(data, axis=1, keepdims=True)
        assert(std_data.shape[0] == data.shape[0])
        std_data[std_data == 0] = 1
        data /= std_data
    return data

def detect_single_sequence(prob_seq, threshold=0.3, min_sec=1.0, dt=0.01, padding=0):
    """
    Detect picks from a single probability sequence using peak detection logic.
    Consecutive above-threshold points are merged according to minimum distance in seconds.

    Args:
        prob_seq (1D np.ndarray): probability sequence
        threshold (float): minimum probability (mph in detect_peaks)
        min_sec (float): minimum distance between peaks in seconds
        dt (float): sampling interval in seconds

    Returns:
        picks_sample (np.ndarray): indices of detected peaks
        picks_prob (np.ndarray): probabilities at detected peaks
    """
    if padding > 0:
        prob_seq = np.pad(prob_seq, (padding, padding), mode='constant', constant_values=0)

    prob_seq = np.atleast_1d(prob_seq).astype('float64')
    if prob_seq.size < 3:
        return np.array([], dtype=int), np.array([], dtype=float)

    # convert min_sec to samples
    mpd = max(1, int(min_sec / dt))

    # compute derivative
    dx = prob_seq[1:] - prob_seq[:-1]

    # detect rising edges (local maxima)
    ind = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]

    # remove first/last point
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == prob_seq.size - 1:
        ind = ind[:-1]

    # filter by threshold
    if ind.size:
        ind = ind[prob_seq[ind] >= threshold]

    # apply minimum peak distance (mpd)
    if ind.size and mpd > 1:
        # sort by probability descending
        ind = ind[np.argsort(prob_seq[ind])][::-1]
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                idel = idel | ((ind >= ind[i] - mpd) & (ind <= ind[i] + mpd))
                idel[i] = 0  # keep current
        ind = np.sort(ind[~idel])

    picks_sample = np.array([int(i) for i in ind])
    picks_prob = np.array([float(prob_seq[i]) for i in ind])

    return picks_sample, picks_prob

def inference2(st, model, overlap=None):
    """
    Continuous seismic phase picking using SeisBench model
    Notes:
    * For EQTransformer, OBSTransformer, the output probability is the [Detection, P phase, S phase]
    * For other Models, the output probability is the [Noise, P phase, S phase]

    Args:
        st (obspy.Stream): input waveform stream, any length, multi-component supported
        model (SeisBench model): pretrained phase picking model

    Returns:
        output: SeisBench annotation results (probabilities or predicted labels)
        time_shift: the time shift of the probability relative to the input data
    """
    # The annotate function takes an obspy stream object as input and returns annotations as stream again. 
    # For example, for picking models the output would be the characteristic functions, 
    # i.e., the pick probabilities over time.
    if overlap is None:
        output = model.annotate(st)
    else:
        output = model.annotate(st, overlap=overlap)
        
    # calculate the time shift
    st_start_time = st[0].stats.starttime
    output_start_time = output[0].stats.starttime
    time_shift = output_start_time - st_start_time
    
    # get phases order and reorder output according to NPS (this is very important)
    phases = model.get_model_args().get("phases", "NPS")
    if phases.lower() in "ps":
        phases = "NPS"
    desired_order = [phases.index(p) for p in "NPS" if p in phases]
    reordered_output = Stream([output[i] for i in desired_order])

    return reordered_output, time_shift


if __name__ == "__main__":
    # ------------------------------------------------------------------------------------
    # load model and pretrained model
    # ------------------------------------------------------------------------------------
    model = EQTransformer(**pretrained_args["model_args"])
    # move model to cpu/gpu
    # device = 'cuda'
    device = torch.device("npu" if torch.npu.is_available() else "cpu")
    model = model.to(device)
    # load pretrained model (you should consider the state_dict key or not)
    state = torch.load(pretrained_path,map_location=device)
    state = state.get("state_dict", state)
    # load state_dict to model
    model.load_state_dict(state)
    model.eval()
    
    # ------------------------------------------------------------------------------------
    # recommended method: using the model.classify method (picks)
    # ------------------------------------------------------------------------------------
    data = np.random.rand(1, 3, 12000)
    # the seisbench requires the input data to be a obspy stream object
    # if the data is a stream, you can inference directly
    # if the data is a numpy array, you need to convert it to a stream object
    st = Stream()
    for i in range(3):
        tr = Trace()
        tr.data = np.array(data[0, i, :])
        # set the header information
        tr.stats.network = "XX"
        tr.stats.station = "TEST"
        tr.stats.location = "00"
        tr.stats.channel = f"EH{i}"          # set the channel name
        tr.stats.starttime = UTCDateTime(0)  # set the starttime
        tr.stats.sampling_rate = 100.0       # set the sampling rate, need to be adjusted according to the actual data
        st.append(tr)
    ppicks_list, spicks_list = inference1(st, model, overlap=1000,P_threshold=0.3,S_threshold=0.3)
    print(ppicks_list,spicks_list)

    # ------------------------------------------------------------------------------------
    # second preferred method: using the model.annotate method (probability output)
    # ------------------------------------------------------------------------------------
    data = np.random.rand(1, 3, 12000)
    # the seisbench requires the input data to be a obspy stream object
    # if the data is a stream, you can inference directly
    # if the data is a numpy array, you need to convert it to a stream object
    st = Stream()
    for i in range(3):
        tr = Trace()
        tr.data = np.array(data[0, i, :])
        # set the header information
        tr.stats.network = "XX"
        tr.stats.station = "TEST"
        tr.stats.location = "00"
        tr.stats.channel = f"EH{i}"          # set the channel name
        tr.stats.starttime = UTCDateTime(0)  # set the starttime
        tr.stats.sampling_rate = 100.0       # set the sampling rate, need to be adjusted according to the actual data
        st.append(tr)
    output,time_shift = inference2(st, model, overlap=100)
    sampling_rate = 100.0
    time_shift_samples = int(time_shift*sampling_rate)
    ppicks_sample, ppicks_prob = detect_single_sequence(output[1].data,threshold=0.3,min_sec=0.5,dt=1/sampling_rate, padding = time_shift_samples)
    spicks_sample, spicks_prob = detect_single_sequence(output[2].data,threshold=0.3,min_sec=0.5,dt=1/sampling_rate, padding = time_shift_samples)
    print(ppicks_sample, ppicks_prob)
    print(spicks_sample, spicks_prob)