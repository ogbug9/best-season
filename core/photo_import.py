"""Checksum and perceptual comparison without additional dependencies."""
import math
from hashlib import sha256
from statistics import median

from PIL import Image, ImageOps


def file_digest(source):
    digest = sha256()
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        digest.update(chunk)
    return digest.hexdigest()


def perceptual_hash(source):
    with Image.open(source) as image:
        pixels = list(ImageOps.exif_transpose(image).convert('L').resize((32, 32)).getdata())
    if max(pixels) - min(pixels) < 2:
        return None
    cosine = [[math.cos(math.pi * (2*x+1) * k / 64) for x in range(32)] for k in range(8)]
    rows = [[sum(pixels[y*32+x] * cosine[k][x] for x in range(32)) for k in range(8)] for y in range(32)]
    coefficients = [sum(rows[y][kx] * cosine[ky][y] for y in range(32)) for ky in range(8) for kx in range(8)]
    threshold = median(coefficients[1:])
    return sum((value > threshold) << i for i, value in enumerate(coefficients))
