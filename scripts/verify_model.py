import os, sys
from pathlib import Path
analysis = Path(os.getenv('SOURCE_FACE_MODEL', 'models/face_analysis'))
swap = Path(os.getenv('SWAP_MODEL', 'models/inswapper_128.onnx'))
if not analysis.is_dir():
    print(f'Missing face-analysis model directory: {analysis}'); sys.exit(1)
if not swap.is_file():
    print(f'Missing face-swap weights: {swap}'); sys.exit(1)
print('Files exist. This check does not establish licensing, compatibility, or successful inference.')
