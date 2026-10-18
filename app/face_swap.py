from pathlib import Path
import cv2
import numpy as np

class FaceSwapError(RuntimeError): pass

class InsightFaceEngine:
    """Adapter for operator-supplied, properly licensed InsightFace-compatible weights.

    InsightFace code is MIT, but its commonly distributed pretrained weights have separate
    restrictions. This adapter intentionally never downloads model weights automatically.
    """
    def __init__(self, analysis_model_dir: str, swap_model_path: str):
        analysis_dir, swap_path = Path(analysis_model_dir), Path(swap_model_path)
        if not analysis_dir.is_dir():
            raise RuntimeError(f"Face analysis model directory missing: {analysis_dir}")
        if not swap_path.is_file():
            raise RuntimeError(f"Face-swap ONNX weights missing: {swap_path}. Supply weights you are licensed to use.")
        try:
            from insightface.app import FaceAnalysis
            from insightface.model_zoo import get_model
            self.analysis = FaceAnalysis(name=analysis_dir.name, root=str(analysis_dir.parent), providers=["CPUExecutionProvider"])
            self.analysis.prepare(ctx_id=-1, det_size=(640, 640))
            self.swapper = get_model(str(swap_path), providers=["CPUExecutionProvider"])
        except Exception as exc:
            raise RuntimeError("Could not initialize InsightFace models. Check model compatibility and licensing.") from exc

    def swap(self, source_path: Path, target_path: Path, output_path: Path) -> None:
        source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        target = cv2.imread(str(target_path), cv2.IMREAD_COLOR)
        if source is None or target is None: raise FaceSwapError("Could not decode one of the images.")
        src_faces = self.analysis.get(source)
        dst_faces = self.analysis.get(target)
        if len(src_faces) != 1: raise FaceSwapError("Source image must contain exactly one detectable face.")
        if len(dst_faces) != 1: raise FaceSwapError("Target image must contain exactly one detectable face.")
        result = self.swapper.get(target, dst_faces[0], src_faces[0], paste_back=True)
        if result is None or result.size == 0: raise FaceSwapError("The face-swap model returned no image.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = output_path.with_suffix(".tmp.jpg")
        if not cv2.imwrite(str(tmp), result, [int(cv2.IMWRITE_JPEG_QUALITY), 95]): raise FaceSwapError("Could not write output image.")
        check = cv2.imread(str(tmp))
        if check is None or check.shape[:2] != target.shape[:2]:
            tmp.unlink(missing_ok=True); raise FaceSwapError("Generated output failed validation.")
        tmp.replace(output_path)
