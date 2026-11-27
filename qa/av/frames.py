"""Framebuffer capture and comparison."""
import numpy as np
from PIL import Image


def to_image(frame):
    return Image.fromarray(np.asarray(frame, dtype=np.uint8), 'RGB')


def save(frame, path, scale=1):
    im = to_image(frame)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)
    return path


def contact_sheet(frames, path, cols=6, scale=1, labels=None):
    """Tile frames into one PNG for human review."""
    if not frames:
        return None
    h, w = frames[0].shape[:2]
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w * scale, rows * h * scale), (40, 40, 40))
    for i, f in enumerate(frames):
        im = to_image(f)
        if scale != 1:
            im = im.resize((w * scale, h * scale), Image.NEAREST)
        sheet.paste(im, ((i % cols) * w * scale, (i // cols) * h * scale))
    sheet.save(path)
    return path


def diff(a, b, tol=24):
    """Compare two frames. Returns dict(fraction, mean, bbox): the fraction of pixels whose
    any channel differs by more than tol, the mean absolute difference, and the box
    around the differing pixels ((x0, y0, x1, y1) or None)."""
    a = np.asarray(a, dtype=np.int16)
    b = np.asarray(b, dtype=np.int16)
    d = np.abs(a - b)
    mask = (d > tol).any(axis=2)
    frac = float(mask.mean())
    if mask.any():
        ys, xs = np.where(mask)
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    else:
        bbox = None
    return dict(fraction=frac, mean=float(d.mean()), bbox=bbox)


def diff_image(a, b, tol=24):
    """A highlight image: the first frame darkened with differing pixels in red."""
    a = np.asarray(a, dtype=np.int16)
    b = np.asarray(b, dtype=np.int16)
    mask = (np.abs(a - b) > tol).any(axis=2)
    out = (a // 3).astype(np.uint8)
    out[mask] = (255, 0, 0)
    return out


def classify_blank(frame, tol=2.0):
    """'white', 'black', 'solid' (one other flat colour) or None for a normal frame."""
    f = np.asarray(frame, dtype=np.float32)
    if f.std(axis=(0, 1)).max() > tol:
        return None
    m = f.mean()
    return 'white' if m > 235 else ('black' if m < 20 else 'solid')


def luminance(frame):
    f = np.asarray(frame, dtype=np.float32)
    return float((0.299 * f[:, :, 0] + 0.587 * f[:, :, 1] + 0.114 * f[:, :, 2]).mean())
