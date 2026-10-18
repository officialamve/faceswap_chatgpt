from pathlib import Path
import pytest
from app.face_swap import InsightFaceEngine, FaceSwapError

def test_missing_weights_fail_closed(tmp_path):
    (tmp_path/'analysis').mkdir()
    with pytest.raises(RuntimeError, match='weights missing'):
        InsightFaceEngine(str(tmp_path/'analysis'), str(tmp_path/'missing.onnx'))

def test_face_swap_error_type():
    assert issubclass(FaceSwapError, RuntimeError)
