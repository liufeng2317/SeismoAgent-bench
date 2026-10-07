import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import torch
import os
import sys
import obspy
from obspy import Stream, Trace, UTCDateTime
import numpy as np
import torch.nn.functional as F
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

# Step1: add the seismoagent base path to the sys.path (must be done)
seismoagent_base_path = "/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/TRACE-1.1/seismoagent"
sys.path.append(os.path.join(seismoagent_base_path,'library','ai_module'))
from phase_picking.model.gpd import GPD

# Step2: define the pretrained model path
pretrained_path = os.path.join(seismoagent_base_path,"library/ai_module/phase_picking/pretrained/v3/gpd/stead.pt")


if __name__ == "__main__":
    
    # load data
    client = Client("GFZ")
    t = UTCDateTime("2007/01/02 05:48:50")
    stream = client.get_waveforms(network="CX", station="PB01", location="*", channel="HH?", starttime=t-100, endtime=t+100)

    # load model
    model = GPD()

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

    # generate random data and inference
    output = model.annotate(stream)
    print(output)