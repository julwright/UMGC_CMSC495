# Training

This directory contains the training assets and scripts used to prepare, train, and evaluate the language model for the Capstone project.

## Contents

- `model_data/` - pre-proccessed and post-processed input data.
- `scripts/` - training scripts, model definition files, and utilities.
- `cve-remediation/` - exported artifacts and json configs.

## Purpose

Use this folder to manage the model training workflow for the project. It should include sources for data preparation, model training, evaluation, and any configuration needed to reproduce results.

## Getting Started

1. Install required dependencies for training.
2. Prepare raw data and place it in the `model_data/` directory.
3. Configure training parameters in the appropriate script or configuration file.
4. Run the main training script from this directory.

## Environemnt 

### Software

- Python 3.12
- Cuda 13.0
- Unsloth
- PyTorch 2.10.0 Torchvision 0.25.0 Torchaudio 2.10.0 from https://download.pytorch.org/whl/cu130
- FlashAttention-2 built on wheel from https://huggingface.co/Wildminder/AI-windows-whl/resolve/main/flash_attn-2.8.3%2Bd20260121.cu130torch2.10.0cxx11abiTRUE-cp312-cp312-win_amd64.whl

### Hardware

- RTX 5070
- 32 GB DDR5 RAM
- Intel Core i7-11700K