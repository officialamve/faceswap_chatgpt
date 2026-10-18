import shutil
from pathlib import Path
import uuid

def make_workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir(mode=0o700)
    return path

def cleanup(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)

def cleanup_abandoned(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for child in root.iterdir():
        if child.is_dir(): shutil.rmtree(child, ignore_errors=True)
        else: child.unlink(missing_ok=True)
