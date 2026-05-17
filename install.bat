@echo off
python -m venv venv
call venv\Scripts\activate.bat
pip install vapoursynth vsrife vsrepo
vsrepo install ffms2
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install torch-tensorrt --extra-index-url https://download.pytorch.org/whl/cu126