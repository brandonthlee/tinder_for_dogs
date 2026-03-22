from pathlib import Path
from PIL import Image


def pixelate(input_path: str, output_path: str, pixel_size: int = 12) -> str:
    """
    Convert an image to pixel art by downscaling then upscaling with nearest-neighbor.
    Returns the output path.
    """
    img = Image.open(input_path).convert("RGB")

    # Crop to square from center
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    target = 512
    small_size = target // pixel_size

    # Downscale to tiny size, then upscale — creates blocky pixel art look
    img = img.resize((small_size, small_size), Image.BILINEAR)
    img = img.quantize(colors=48).convert("RGB")
    img = img.resize((target, target), Image.NEAREST)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
