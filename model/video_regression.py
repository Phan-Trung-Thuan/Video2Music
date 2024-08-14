import torch
import torch.nn as nn
from torch.nn.modules.normalization import LayerNorm
# from torchtune.modules import RMSNorm
import random
import numpy as np
from utilities.constants import *
from utilities.device import get_device
from datetime import datetime
from .moe import *
# from .custom_lstm import LSTM
# from .custom_gru import GRU
# from .custom_reg_model import myRNN
import torch.nn.functional as F
from efficient_kan import KANLinear

from .mamba import Mamba, MoEMamba, MambaConfig
from .bimamba import BiMambaEncoder


class advancedRNNBlock(nn.Module):
    def __init__(self, rnn_type='gru', ff_type='mlp', d_model=256, d_hidden=1024, dropout=0.1, bidirectional=True):
        super(advancedRNNBlock, self).__init__()

        self.d_model = d_model
        self.d_hidden = d_hidden
        self.dropout = dropout
        self.bidirectional = bidirectional

        if rnn_type == None:
            self.rnn_layer = nn.RNN(self.d_model, self.d_model, num_layers=1, bidirectional=bidirectional, batch_first=True)
        elif rnn_type == 'gru':
            self.rnn_layer = nn.GRU(self.d_model, self.d_model, num_layers=1, bidirectional=bidirectional, batch_first=True)
        elif rnn_type == 'lstm':
            self.rnn_layer = nn.LSTM(self.d_model, self.d_model, num_layers=1, bidirectional=bidirectional, batch_first=True)

        if ff_type == 'mlp':
            self.ff_layer = nn.Sequential(
                nn.Linear(self.d_model * (2 if bidirectional else 1), self.d_hidden),
                nn.SiLU(),
                nn.Linear(self.d_hidden, self.d_model)
            )
        elif ff_type == 'moe':
            expert = nn.Sequential(
                GLUExpert(self.d_model * (2 if bidirectional else 1), self.d_hidden),
                nn.Linear(self.d_model * (2 if bidirectional else 1), self.d_model)
            )

            self.ff_layer = MoELayer(expert, self.d_model * (2 if bidirectional else 1), d_ff=self.d_hidden, n_experts=6, n_experts_per_token=1, dropout=dropout)

        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.last_layer = nn.Linear(self.d_model * (2 if bidirectional else 1), self.d_model)

    def forward(self, x):
        x_rnn, _ = self.rnn_layer(x)
        x_double = torch.cat((x, x), dim=-1)
        x = self.dropout1(x_rnn + x_double)

        x_ff = self.ff_layer(x)
        x_double = torch.cat((x, x), dim=-1)
        print(x.shape, x_ff.shape, x_double.shape)
        x = self.dropout2(x_ff + x_double)

        x = self.last_layer(x)
        return x
class VideoRegression(nn.Module):
    def __init__(self, n_layers=2, d_model=64, d_hidden=1024, dropout=0.1, use_KAN=False, max_sequence_video=300, total_vf_dim=0, regModel="bilstm"):
        super(VideoRegression, self).__init__()
        self.n_layers    = n_layers
        self.d_model    = d_model
        self.d_hidden = d_hidden
        self.dropout    = nn.Dropout(dropout)
        self.max_seq_video    = max_sequence_video
        self.total_vf_dim = total_vf_dim
        self.regModel = regModel
        if self.regModel == "bilstm":
            self.bilstm = nn.LSTM(self.total_vf_dim, self.d_model, self.n_layers, bidirectional=True)
        elif self.regModel == "bigru":
            # ORIGIN
            # self.bigru = nn.GRU(self.total_vf_dim, self.d_model, self.n_layers, bidirectional=True)
            # MODIFY
            self.bigru = nn.GRU(self.total_vf_dim, self.d_model, self.n_layers, bidirectional=True, dropout=dropout)
        elif self.regModel == "lstm":
            self.lstm = nn.LSTM(self.total_vf_dim, self.d_model, self.n_layers)
        elif self.regModel == "gru":
            self.gru = nn.GRU(self.total_vf_dim, self.d_model, self.n_layers)          
        elif self.regModel == "mamba":
            config = MambaConfig(d_model=self.d_model, n_layers=self.n_layers, use_KAN=use_KAN, bias=True)
            self.model = Mamba(config)           
        elif self.regModel == "mamba+":
            config = MambaConfig(d_model=self.d_model, n_layers=self.n_layers, use_KAN=use_KAN, bias=True, use_version=1)
            self.model = Mamba(config)
        elif self.regModel == "moemamba":
            config = MambaConfig(d_model=self.d_model, n_layers=self.n_layers, d_state=self.d_hidden, d_conv=8, dropout=dropout, use_KAN=use_KAN, bias=True)
            expert = GLUExpert(self.d_model, self.d_model * 2 + 1)
            moe_layer = SharedMoELayer(expert, self.d_model, n_experts=6, n_experts_per_token=2, dropout=dropout)
            self.model = MoEMamba(moe_layer, config)
        elif self.regModel == "bimamba":
            config = MambaConfig(d_model=self.d_model, n_layers=1, dropout=dropout, use_KAN=use_KAN, bias=True, use_version=0)
            self.model = BiMambaEncoder(config, self.d_hidden, n_encoder_layers=self.n_layers)
        elif self.regModel == "bimamba+":
            config = MambaConfig(d_model=self.d_model, n_layers=1, dropout=dropout, use_KAN=use_KAN, bias=True, use_version=1)
            self.model = BiMambaEncoder(config, self.d_hidden, n_encoder_layers=self.n_layers)
    
        if self.regModel in ('gru', 'lstm'):
            self.fc = nn.Linear(self.d_model, 2)
            
        if self.regModel in ('bigru', 'bilstm'):
            self.bifc = nn.Linear(self.d_model * 2, 2)
        
        projection = nn.Linear
        # projection = KANLinear
        
        if self.regModel in ('mamba', 'moemamba', 'mamba+', 'bimamba', 'bimamba+'):
            self.fc3 = projection(self.total_vf_dim, self.d_model)
            self.fc4 = projection(self.d_model, 2)            

    def forward(self, feature_semantic_list, feature_scene_offset, feature_motion, feature_emotion):
        ### Video (SemanticList + SceneOffset + Motion + Emotion) (ENCODER) ###
        vf_concat = feature_semantic_list[0].float()
        for i in range(1, len(feature_semantic_list)):
            vf_concat = torch.cat( (vf_concat, feature_semantic_list[i].float()), dim=2)            

        vf_concat = torch.cat([vf_concat, feature_scene_offset.unsqueeze(-1).float()], dim=-1) 
        vf_concat = torch.cat([vf_concat, feature_motion.unsqueeze(-1).float()], dim=-1) 
        vf_concat = torch.cat([vf_concat, feature_emotion.float()], dim=-1)
        vf_concat = vf_concat.permute(1,0,2)

        if self.regModel == "bilstm":
            out, _ = self.bilstm(vf_concat)
            out = out.permute(1,0,2)
            out = self.bifc(out)
        elif self.regModel == "bigru":
            out, _ = self.bigru(vf_concat)
            out = out.permute(1,0,2)
            out = self.bifc(out)
        elif self.regModel == "lstm":
            out, _ = self.lstm(vf_concat)
            out = out.permute(1,0,2)
            out = self.fc(out)
        elif self.regModel == "gru":
            out, _ = self.gru(vf_concat)
            out = out.permute(1,0,2)
            out = self.fc(out)
        elif self.regModel in ("mamba", "moemamba", "mamba+"):
            vf_concat = vf_concat.permute(1,0,2)
            vf_concat = self.fc3(vf_concat)
            
            out = self.model(vf_concat)

            out = self.dropout(out)           
            out = self.fc4(out)
        elif self.regModel in ('bimamba', 'bimamba+'):
            vf_concat = vf_concat.permute(1,0,2)
            vf_concat = self.fc3(vf_concat)
            
            out = self.model(vf_concat)

            out = self.dropout(out)
            out = self.fc4(out)
        return out
