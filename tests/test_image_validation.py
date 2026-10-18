from pathlib import Path
import pytest
from PIL import Image
from app.image_utils import validate_image, ImageValidationError

def test_valid_jpeg(tmp_path):
    p = tmp_path/'ok.jpg'; Image.new('RGB',(40,30),'white').save(p)
    assert validate_image(p, max_bytes=100000, max_pixels=10000, max_dimension=100) == (40,30)

def test_invalid_file(tmp_path):
    p = tmp_path/'bad.jpg'; p.write_text('not an image')
    with pytest.raises(ImageValidationError): validate_image(p, max_bytes=100000, max_pixels=10000, max_dimension=100)

def test_pixel_limit(tmp_path):
    p = tmp_path/'big.png'; Image.new('RGB',(40,30)).save(p)
    with pytest.raises(ImageValidationError): validate_image(p, max_bytes=100000, max_pixels=100, max_dimension=100)

def test_file_size_limit(tmp_path):
    p = tmp_path/'ok.jpg'; Image.new('RGB',(40,30)).save(p)
    with pytest.raises(ImageValidationError): validate_image(p, max_bytes=1, max_pixels=10000, max_dimension=100)
