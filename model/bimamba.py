import torch
import torch.nn as nn
import torch.nn.functional as F
from mamba import Mamba, MambaConfig, RMSNorm

class BiMambaEncoder(nn.Module):
    def __init__(self, config: MambaConfig, dim_feedforward=1024):
        super().__init__
        self.config = config
        self.mamba_forward = Mamba(config)
        self.mamba_backward = Mamba(config)
        self.d_ff = dim_feedforward

        # Norm and FF_layer
        self.norm1 = RMSNorm(config.d_model, config.rms_norm_eps, config.mup)
        self.norm2 = RMSNorm(config.d_model, config.rms_norm_eps, config.mup)
        self.feed_forward = nn.Sequential(
            nn.Linear(config.d_model, dim_feedforward),
            nn.ReLU(),
            nn.Linear(dim_feedforward, config.d_model)
        )

    def forward(self, x):        
        x_flip = torch.flip(x, dims=[1])

        # Forward
        mamba_out_forward = self.mamba_forward(x)
        mamba_out_forward = self.norm1(mamba_out_forward)
        output_forward = self.feed_forward(mamba_out_forward) + mamba_out_forward

        # Backward
        mamba_out_backward = self.mamba_backward(x_flip)
        mamba_out_backward = self.norm2(mamba_out_backward)
        output_backward = self.feed_forward(mamba_out_backward) + mamba_out_backward

        # Combine output
        output = output_forward + output_backward

        return output