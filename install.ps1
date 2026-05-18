python -m venv venv
.\venv\Scripts\Activate.ps1
pip install vapoursynth vsrife vsrepo
vsrepo install ffms2
pip install torch torch-tensorrt torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu126