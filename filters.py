"""
Filtres de traitement d'image pour UVSQolor.

Ce fichier ne contient aucune fonction Tkinter : il transforme uniquement des
objets PIL.Image. Cette séparation permet de garder le code plus clair :
- gui.py gère l'interface, les menus, les fichiers et l'historique ;
- filters.py gère les algorithmes de traitement d'image.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from PIL import Image

try:
    import numpy as np
except Exception:  # numpy est optionnel : le code fonctionne aussi sans lui.
    np = None


RGBPixel = Tuple[int, int, int]


def clamp(value: float) -> int:
    """Ramène une valeur dans l'intervalle [0, 255]."""
    return max(0, min(255, int(round(value))))


def to_rgb(image: Image.Image) -> Image.Image:
    """Retourne une copie RGB de l'image."""
    return image.convert("RGB")


# ---------------------------------------------------------------------------
# Filtres simples demandés dans le sujet
# ---------------------------------------------------------------------------


def sepia(image: Image.Image) -> Image.Image:
    """Applique un filtre sépia à l'image."""
    img = to_rgb(image)
    width, height = img.size
    result = Image.new("RGB", (width, height))

    pixels = img.load()
    output = result.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            new_r = 0.393 * r + 0.769 * g + 0.189 * b
            new_g = 0.349 * r + 0.686 * g + 0.168 * b
            new_b = 0.272 * r + 0.534 * g + 0.131 * b
            output[x, y] = (clamp(new_r), clamp(new_g), clamp(new_b))

    return result


def brightness(image: Image.Image, value: int) -> Image.Image:
    """
    Modifie la luminosité par addition.

    value > 0 éclaircit l'image, value < 0 l'assombrit.
    """
    img = to_rgb(image)
    width, height = img.size
    result = Image.new("RGB", (width, height))

    pixels = img.load()
    output = result.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            output[x, y] = (
                clamp(r + value),
                clamp(g + value),
                clamp(b + value),
            )

    return result


def contrast(image: Image.Image, value: int) -> Image.Image:
    """
    Modifie le contraste.

    La formule utilisée éloigne ou rapproche les valeurs de 128, qui représente
    le gris moyen. value doit idéalement être compris entre -254 et 254.
    """
    img = to_rgb(image)
    width, height = img.size
    result = Image.new("RGB", (width, height))

    value = max(-254, min(254, int(value)))
    factor = (259 * (value + 255)) / (255 * (259 - value))

    pixels = img.load()
    output = result.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            output[x, y] = (
                clamp(factor * (r - 128) + 128),
                clamp(factor * (g - 128) + 128),
                clamp(factor * (b - 128) + 128),
            )

    return result


def blend(image1: Image.Image, image2: Image.Image, alpha: float = 0.5) -> Image.Image:
    """
    Fusionne deux images de même taille.

    alpha = 0.0 : uniquement image1
    alpha = 1.0 : uniquement image2
    """
    img1 = to_rgb(image1)
    img2 = to_rgb(image2)

    if img1.size != img2.size:
        raise ValueError("Les deux images doivent avoir la même taille pour la fusion.")

    alpha = max(0.0, min(1.0, float(alpha)))
    width, height = img1.size
    result = Image.new("RGB", (width, height))

    p1 = img1.load()
    p2 = img2.load()
    out = result.load()

    for y in range(height):
        for x in range(width):
            r1, g1, b1 = p1[x, y]
            r2, g2, b2 = p2[x, y]
            out[x, y] = (
                clamp((1 - alpha) * r1 + alpha * r2),
                clamp((1 - alpha) * g1 + alpha * g2),
                clamp((1 - alpha) * b1 + alpha * b2),
            )

    return result


# ---------------------------------------------------------------------------
# Convolution et flous
# ---------------------------------------------------------------------------


def _normalise_kernel(kernel: Sequence[float]) -> List[float]:
    total = float(sum(kernel))
    if total == 0:
        return list(kernel)
    return [float(value) / total for value in kernel]


def box_kernel_1d(radius: int) -> List[float]:
    """Noyau 1D pour un flou moyen."""
    radius = max(0, int(radius))
    size = 2 * radius + 1
    return [1.0 / size for _ in range(size)]


def gaussian_kernel_1d(radius: int, sigma: Optional[float] = None) -> List[float]:
    """
    Crée un noyau gaussien 1D normalisé.

    Le flou gaussien 2D est appliqué en deux passages : horizontal puis vertical.
    C'est équivalent mathématiquement à un noyau 2D gaussien, mais plus rapide.
    """
    radius = max(0, int(radius))
    if radius == 0:
        return [1.0]

    if sigma is None:
        sigma = max(radius / 2.0, 1.0)

    values = []
    for x in range(-radius, radius + 1):
        values.append(math.exp(-(x * x) / (2 * sigma * sigma)))

    return _normalise_kernel(values)


def _separable_convolution_numpy(image: Image.Image, kernel: Sequence[float]) -> Image.Image:
    """Version rapide avec numpy, si numpy est disponible."""
    assert np is not None

    img = to_rgb(image)
    arr = np.asarray(img, dtype=np.float32)
    radius = len(kernel) // 2

    if radius == 0:
        return img.copy()

    weights = np.asarray(kernel, dtype=np.float32)

    padded_horizontal = np.pad(arr, ((0, 0), (radius, radius), (0, 0)), mode="edge")
    temp = np.zeros_like(arr, dtype=np.float32)
    for i, weight in enumerate(weights):
        temp += weight * padded_horizontal[:, i:i + arr.shape[1], :]

    padded_vertical = np.pad(temp, ((radius, radius), (0, 0), (0, 0)), mode="edge")
    output = np.zeros_like(arr, dtype=np.float32)
    for i, weight in enumerate(weights):
        output += weight * padded_vertical[i:i + arr.shape[0], :, :]

    output = np.clip(output, 0, 255).astype("uint8")
    return Image.fromarray(output, "RGB")


def _separable_convolution_python(image: Image.Image, kernel: Sequence[float]) -> Image.Image:
    """Version sans dépendance externe, plus lente mais très lisible."""
    img = to_rgb(image)
    width, height = img.size
    radius = len(kernel) // 2

    if radius == 0:
        return img.copy()

    source = img.load()
    temp: List[List[Tuple[float, float, float]]] = [
        [(0.0, 0.0, 0.0) for _ in range(width)] for _ in range(height)
    ]

    # Passage horizontal
    for y in range(height):
        for x in range(width):
            total_r = total_g = total_b = 0.0
            for k, weight in enumerate(kernel):
                px = x + k - radius
                px = max(0, min(width - 1, px))
                r, g, b = source[px, y]
                total_r += r * weight
                total_g += g * weight
                total_b += b * weight
            temp[y][x] = (total_r, total_g, total_b)

    result = Image.new("RGB", (width, height))
    output = result.load()

    # Passage vertical
    for y in range(height):
        for x in range(width):
            total_r = total_g = total_b = 0.0
            for k, weight in enumerate(kernel):
                py = y + k - radius
                py = max(0, min(height - 1, py))
                r, g, b = temp[py][x]
                total_r += r * weight
                total_g += g * weight
                total_b += b * weight
            output[x, y] = (clamp(total_r), clamp(total_g), clamp(total_b))

    return result


def separable_convolution(image: Image.Image, kernel: Sequence[float]) -> Image.Image:
    """Applique une convolution séparable horizontalement puis verticalement."""
    if np is not None:
        return _separable_convolution_numpy(image, kernel)
    return _separable_convolution_python(image, kernel)


def blur(image: Image.Image, radius: int = 1) -> Image.Image:
    """Flou uniforme par moyenne des voisins."""
    radius = max(1, int(radius))
    return separable_convolution(image, box_kernel_1d(radius))


def gaussian_blur(image: Image.Image, radius: int = 2) -> Image.Image:
    """Flou gaussien réglable par rayon."""
    radius = max(0, int(radius))
    return separable_convolution(image, gaussian_kernel_1d(radius))


def _convolution_3x3_numpy(image: Image.Image, kernel: Sequence[Sequence[float]]) -> Image.Image:
    assert np is not None

    img = to_rgb(image)
    arr = np.asarray(img, dtype=np.float32)
    padded = np.pad(arr, ((1, 1), (1, 1), (0, 0)), mode="edge")
    output = np.zeros_like(arr, dtype=np.float32)

    for ky in range(3):
        for kx in range(3):
            output += float(kernel[ky][kx]) * padded[ky:ky + arr.shape[0], kx:kx + arr.shape[1], :]

    output = np.clip(output, 0, 255).astype("uint8")
    return Image.fromarray(output, "RGB")


def _convolution_3x3_python(image: Image.Image, kernel: Sequence[Sequence[float]]) -> Image.Image:
    img = to_rgb(image)
    width, height = img.size
    result = Image.new("RGB", (width, height))

    pixels = img.load()
    output = result.load()

    for y in range(height):
        for x in range(width):
            total_r = total_g = total_b = 0.0
            for ky in range(3):
                for kx in range(3):
                    px = x + kx - 1
                    py = y + ky - 1
                    px = max(0, min(width - 1, px))
                    py = max(0, min(height - 1, py))
                    r, g, b = pixels[px, py]
                    coef = kernel[ky][kx]
                    total_r += r * coef
                    total_g += g * coef
                    total_b += b * coef
            output[x, y] = (clamp(total_r), clamp(total_g), clamp(total_b))

    return result


def convolution_3x3(image: Image.Image, kernel: Sequence[Sequence[float]]) -> Image.Image:
    """Applique une convolution 3x3."""
    if np is not None:
        return _convolution_3x3_numpy(image, kernel)
    return _convolution_3x3_python(image, kernel)


def sharpen(image: Image.Image) -> Image.Image:
    """Netteté simple avec un noyau de convolution 3x3."""
    kernel = [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0],
    ]
    return convolution_3x3(image, kernel)


def gaussian_sharpen(
    image: Image.Image,
    radius: int = 2,
    amount: float = 1.0,
    threshold: int = 0,
) -> Image.Image:
    """
    Netteté basée sur le flou gaussien, aussi appelée masque flou.

    details = image_originale - image_floutee
    resultat = image_originale + amount * details
    """
    original = to_rgb(image)
    blurred = gaussian_blur(original, radius)
    amount = max(0.0, float(amount))
    threshold = max(0, int(threshold))

    if np is not None:
        orig = np.asarray(original, dtype=np.float32)
        blur_arr = np.asarray(blurred, dtype=np.float32)
        details = orig - blur_arr

        if threshold > 0:
            mask = np.abs(details) >= threshold
            result = np.where(mask, orig + amount * details, orig)
        else:
            result = orig + amount * details

        result = np.clip(result, 0, 255).astype("uint8")
        return Image.fromarray(result, "RGB")

    width, height = original.size
    result = Image.new("RGB", (width, height))
    po = original.load()
    pb = blurred.load()
    out = result.load()

    for y in range(height):
        for x in range(width):
            r, g, b = po[x, y]
            br, bg, bb = pb[x, y]
            dr, dg, db = r - br, g - bg, b - bb

            out[x, y] = (
                clamp(r + amount * dr) if abs(dr) >= threshold else r,
                clamp(g + amount * dg) if abs(dg) >= threshold else g,
                clamp(b + amount * db) if abs(db) >= threshold else b,
            )

    return result


# ---------------------------------------------------------------------------
# Bonus utiles, non prioritaires
# ---------------------------------------------------------------------------


def grayscale(image: Image.Image) -> Image.Image:
    """Convertit l'image en niveaux de gris, puis la garde en RGB."""
    img = to_rgb(image)
    width, height = img.size
    result = Image.new("RGB", (width, height))
    pixels = img.load()
    output = result.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            grey = clamp(0.299 * r + 0.587 * g + 0.114 * b)
            output[x, y] = (grey, grey, grey)

    return result


def edge_detection(image: Image.Image) -> Image.Image:
    """Détection de bords avec l'opérateur de Sobel."""
    gray = grayscale(image).convert("L")
    width, height = gray.size
    pixels = gray.load()
    result = Image.new("RGB", (width, height))
    output = result.load()

    sobel_x = [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1],
    ]
    sobel_y = [
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1],
    ]

    for y in range(height):
        for x in range(width):
            gx = gy = 0.0
            for ky in range(3):
                for kx in range(3):
                    px = x + kx - 1
                    py = y + ky - 1
                    px = max(0, min(width - 1, px))
                    py = max(0, min(height - 1, py))
                    value = pixels[px, py]
                    gx += value * sobel_x[ky][kx]
                    gy += value * sobel_y[ky][kx]
            magnitude = clamp(math.sqrt(gx * gx + gy * gy))
            output[x, y] = (magnitude, magnitude, magnitude)

    return result
