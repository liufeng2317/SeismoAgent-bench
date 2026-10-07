"""
This file is used to run the inference of the phase picking model.
You can manually inference the model as follows:
1. manually inference the model
    - manually segment the data
    - must normalize the data before the using the version2 inference
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
from phase_picking.model.dpppickers import DPPPicker

# Step2: define the pretrained model path
pretrained_path = os.path.join(seismoagent_base_path,"library/ai_module/phase_picking/pretrained/v3/dpppickers/ethz.pt")
# the config of pretrained model is saved as a json file by replace the "pt" with "json"
# e.g. ethz.pt -> ethz.json; original.pt.v2 -> original.json.v2; stead.pt.v2 -> stead.json.v2
pretrained_param_path = pretrained_path.replace("pt","json")
pretrained_args = json.load(open(pretrained_param_path))

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

# ------------------------------------------------------------------------------------
# inference method 2: manually inference the model
# ------------------------------------------------------------------------------------
def inference(data, model, classes = 3, seg_length=3001, overlap_points=1000):
    """
    Sliding-window inference for continuous 3-component seismic data with probability outputs.

    Args:
        data (torch.Tensor): [N, 3, L] input waveform
        model (nn.Module): pretrained model
        classes (int): number of classes (model output)
        seg_length (int): sliding window length
        overlap_points (int): overlap points

    Returns:
        torch.Tensor: [N, 3, L] probability outputs for each task, aligned with input
    """
    N, _, L = data.shape
    device = model.device
    output = torch.zeros(N, classes, L, device=device)
    weight = torch.zeros(L, device=device)

    w = torch.hann_window(seg_length, device=device, dtype=torch.float32)

    # right pad to ensure the last window can be taken completely
    pad_right = seg_length
    data_padded = F.pad(data, (0, pad_right), mode='constant', value=0)
    padded_L = data_padded.shape[2]

    slide_length = max(1, seg_length - overlap_points)

    for start in range(0, padded_L - seg_length + 1, slide_length):
        end = start + seg_length
        data_seg = data_padded[:, :, start:end]
        data_seg = data_seg.to(device)
        with torch.no_grad():
            out_seg = model(data_seg)
            if isinstance(out_seg, tuple):
                out_seg = torch.cat(out_seg, dim=0).unsqueeze(0)
            elif len(out_seg.shape) == 2:
                out_seg = out_seg.unsqueeze(0)

        # map back to the original sequence
        orig_start = start
        orig_end = min(end, L)
        valid_len = orig_end - orig_start

        # valid part in the window
        w_seg = w[:valid_len]

        output[:, :, orig_start:orig_end] += out_seg[:, :, :valid_len] * w_seg
        weight[orig_start:orig_end] += w_seg

    weight = weight.clamp(min=1e-6)
    output = output / weight.unsqueeze(0).unsqueeze(0)
    output = output.clamp(0, 1)

    return output

if __name__ == "__main__":
    # ------------------------------------------------------------------------------------
    # load model and pretrained model
    # ------------------------------------------------------------------------------------
    model = DPPPicker(mode="S")
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
    # inference method 2: manually inference the model
    # ------------------------------------------------------------------------------------
    data = np.random.rand(2, 6000)
    # you must normalize the data before the using the version2 inference
    data = normalize(data, mode='max')
    data = torch.tensor(data,dtype=torch.float32)
    data = data.unsqueeze(0)
    output = inference(data, model, classes = 2, seg_length=3001, overlap_points=1000).cpu().numpy()
    sampling_rate = 100.0
    spicks_sample, spicks_prob = detect_single_sequence(output[0,1],threshold=0.3,min_sec=0.5,dt=1/sampling_rate)
    print(spicks_sample, spicks_prob)