# Video Background Music Generation (CTU Student Research THS2024-82)

<div align="center">
  <img src="v2m.png" width="400"/>
</div>

## Introduction

This repository is an extended branch of the original [Video2Music](https://github.com/AMAAI-Lab/Video2Music) framework by Kang et al. (2024). It is developed as part of a Student Scientific Research Project at **Can Tho University (CTU)**.

**Project Title:** Phát triển mô hình sinh nhạc tự động dựa trên đoạn phim ngắn (Developing model for video background music generation)  
**Project Code:** THS2024-82  
**Project Leader:** Phan Trung Thuận  
**Members:** Dương Minh Khang, Nguyễn Phương Thụy, Phạm Trần Anh Tài  
**Advisor:** Dr. Lâm Nhựt Khang

Our research introduces significant architectural improvements to the original Affective Multimodal Transformer (AMT) to achieve higher compatibility between the input short video and the generated music.

### Key Improvements:

1. **Transformer Architecture Enhancements:**
   - Replaced the standard Feedforward layer with a **Shared Mixture of Experts (SharedMoE)**, combining MoE and Shared Expert Isolation.
   - Utilized **SwiGLU experts**, optimized with **TopK Scheduling** and **Auxiliary-Loss-Free Load Balancing**.
   - Integrated **Rotary Positional Embedding (RoPE)** into the attention mechanism to better capture relative positions.
2. **Regression Model Enhancements:**
   - Applied the **Bidirectional Mamba+ (Bi-Mamba+)** model for the note density and loudness estimation phase, replacing the traditional Bi-LSTM, leading to improved efficiency and performance.
3. **Optimization:**
   - Utilized **RAdamW** optimizer with **LambdaLR** scheduling for better convergence.

## Experimental Results

### Music Generation Model Performance

Comparison of the original Affective Multimodal Transformer (AMT) and our proposed **Hybrid SharedMoE-MT**.

| Model                          | Hits@1     | Hits@3     | Hits@5     | Emotion Loss |
| ------------------------------ | ---------- | ---------- | ---------- | ------------ |
| AMT (Kang et al.)              | 0.5164     | 0.7579     | 0.8571     | 0.4497       |
| **Hybrid SharedMoE-MT (Ours)** | **0.5429** | **0.8101** | **0.8935** | **0.3859**   |

### Music Analysis (Regression) Model Performance

Comparison of various recurrent models for predicting note density, loudness, and instruments.

| Model                 | Note Density (RMSE) | Loudness (RMSE) | Instrument (BCE) |
| --------------------- | ------------------- | --------------- | ---------------- |
| LSTM (Ours)           | 4.6500              | 0.0866          | 0.1554           |
| Bi-LSTM (Kang et al.) | 4.5279              | 0.0906          | -                |
| Bi-LSTM (Ours)        | 4.5250              | 0.0868          | 0.1492           |
| GRU (Ours)            | 4.6841              | 0.0870          | 0.1547           |
| Bi-GRU (Kang et al.)  | 4.5095              | 0.0867          | -                |
| Bi-GRU (Ours)         | 4.4757              | 0.0873          | 0.1526           |
| CNN-GRU (Ours)        | 4.6123              | 0.0860          | 0.1526           |
| CNN-Bi-GRU (Ours)     | 4.4828              | 0.0840          | 0.1517           |
| Mamba+ (Ours)         | 4.7270              | 0.1089          | 0.1477           |
| **Bi-Mamba+ (Ours)**  | **4.4748**          | **0.0861**      | **0.1503**       |

## Quickstart Guide

Generate music from video:

```python
import IPython
from video2music import Video2music

input_video = "input.mp4"

input_primer = "C Am F G"
input_key = "C major"

video2music = Video2music()
output_filename = video2music.generate(input_video, primer=input_primer, key=input_key)

IPython.display.Video(output_filename)
```

## Installation

**For training**

```bash
git clone https://github.com/Phan-Trung-Thuan/Video2Music.git
cd Video2Music
pip install -r requirements.txt
pip install --upgrade gensim
```

**For inference**

```bash
apt-get update -y
apt-get install ffmpeg -y
apt-get install fluidsynth -y
pip install -r requirements.txt
pip install --upgrade gensim
apt install imagemagick -y
apt install libmagick++-dev -y
cat /etc/ImageMagick-6/policy.xml | sed 's/none/read,write/g'> /etc/ImageMagick-6/policy.xml
```

- Download the default soundfont file [default_sound_font.sf2](https://drive.google.com/file/d/1B9qjgimW9h6Gg5k8PZNt_ArWwSMJ4WuJ/view?usp=drive_link) or using custom soundfonts processed by us [soundfonts.zip](https://drive.google.com/uc?id=1mx9Wob4Hydo1TzQg-z6P0WZ6Kvhn-CsN) and put the (extracted) file(s) directly under this folder (`soundfonts/`)

  Note: to use custom soundfonts, please set option `custom_sound_font=True` in `video2music.generate()` (`video2music.py`)

- Our code is built on PyTorch version 2.3.1 (`torch==2.3.1` in the `requirements.txt`). Choose the correct version of `torch` based on your CUDA version.

## Dataset

- Obtain the dataset:
  - MuVi-Sync-dataset-v3 [(Link)](https://kaggle.com/datasets/a4a8f326fe8985d9aac2d69ec8d06dac49e7147ee36cc60752634b037fdc596c)

- Put all directories starting with `vevo` in the dataset under this folder (`dataset/`)

## Directory Structure

- `saved_models/`: saved model files
- `utilities/`
  - `run_model_vevo.py`: code for running model (AMT/SharedMoE-MT)
  - `run_model_regression.py`: code for running regression model
  - `argument_funcs.py`: code for parameters for model during training
  - `argument_reg_funcs.py`: code for parameters for regression model during training
  - `argument_generate_funcs.py`: code for parameters for both model during inference
- `model/`
  - `video_music_transformer.py`: Improved Multimodal Transformer model architectures (V1, V2, V3) featuring SharedMoE, SwiGLU, and RoPE.
  - `video_regression.py`: Regression model used for predicting note density/loudness featuring Bi-Mamba+.
  - `moe.py`, `mamba.py`, `bimamba.py`: Implementation of MoE and Mamba variants.
- `dataset/`
  - `vevo_dataset.py`: Dataset loader
- `script/` : code for extracting video/music features (semantic, motion, emotion, scene offset, loudness, and note density)
- `train.py`: training script (Transformer)
- `train_regression.py`: training script (regression model)
- `evaluate.py`: evaluation script
- `generate.py`: inference script
- `video2music.py`: Video2Music module that outputs video with generated background music from input video
- `demo_training.ipynb`: demo notebook for training model
- `demo_generate.ipynb`: demo notebook for inference

## Training

```shell
python train.py
```

or

```shell
python train_regression.py
```

## Inference

We provide a Jupyter notebook (`video2music-generate.ipynb`) that demonstrates the full inference pipeline, including setting up the environment, downloading pre-trained weights, and rendering the final video. You can run this notebook locally or on cloud platforms like Kaggle or Google Colab.

### 1. Download Pre-trained Weights

Before running inference, you need to download the pre-trained model weights and place them in the `saved_models/AMT/` directory:

- **Transformer Model Weights:** [Download](https://drive.google.com/file/d/1BzcWcoxojdWw1aEfx8945fPQtkqNGUnz/view?usp=sharing) (`best_loss_weights.pickle`)
- **Regression Model Weights:** [Download](https://drive.google.com/file/d/1N6qp_-neSRRhwCTt-NBqlnpElCjOpYoK/view?usp=sharing) (`best_rmse_weights.pickle`)
  If those links are broken then try [this link](https://drive.google.com/drive/folders/1KUiQ_rsRP5X3TyZSRqUmzIy1O6-EKtIb?usp=sharing)

You can download them directly via command line using `gdown`:

```bash
mkdir -p saved_models/AMT
gdown 1BzcWcoxojdWw1aEfx8945fPQtkqNGUnz -O saved_models/AMT/best_loss_weights.pickle
gdown 1N6qp_-neSRRhwCTt-NBqlnpElCjOpYoK -O saved_models/AMT/best_rmse_weights.pickle
```

### 2. Run Inference

You can run inference using the `generate.py` script:

```shell
python generate.py
```

Alternatively, you can use the `Video2music` class programmatically as shown in the **Quickstart Guide**, or follow the step-by-step execution in `video2music-generate.ipynb`.

## Original Citation

If you find the base resource useful, please cite the original work:

```bibtex
@article{KANG2024123640,
  title = {Video2Music: Suitable music generation from videos using an Affective Multimodal Transformer model},
  author = {Jaeyong Kang and Soujanya Poria and Dorien Herremans},
  journal = {Expert Systems with Applications},
  pages = {123640},
  year = {2024},
  issn = {0957-4174},
  doi = {https://doi.org/10.1016/j.eswa.2024.123640},
}
```

Kang, J., Poria, S. & Herremans, D. (2024). Video2Music: Suitable Music Generation from Videos using an Affective Multimodal Transformer model, Expert Systems with Applications (in press).

## Acknowledgements

- Our code is an extension of [Video2Music](https://github.com/AMAAI-Lab/Video2Music) and based on [Music Transformer](https://github.com/gwinndr/MusicTransformer-Pytorch).
- This project is supported by Can Tho University (CTU) under the Student Scientific Research Program (Project THS2024-82).
