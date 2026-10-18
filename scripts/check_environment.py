import importlib.util, sys
required = ['fastapi','telegram','PIL','cv2','numpy','onnxruntime','insightface']
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print('Missing packages:', ', '.join(missing)); sys.exit(1)
print('Required Python packages are import-discoverable. This does not verify model weights or inference.')
