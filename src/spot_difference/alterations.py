from abc import ABC, abstractmethod

import cv2
import numpy as np


def get_patch(image, region):
    return image[region.y : region.y + region.height, region.x : region.x + region.width]


def set_patch(image, region, patch):
    image[region.y : region.y + region.height, region.x : region.x + region.width] = patch


class ImageAlteration(ABC):
    name = "Image Alteration"

    @abstractmethod
    def apply(self, image, region, random_generator):
        pass


class ColourShiftAlteration(ImageAlteration):
    name = "Colour Shift"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        hsv_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)

        hue_shift = random_generator.randint(28, 55)
        saturation_shift = random_generator.randint(25, 55)

        hsv_patch[:, :, 0] = (hsv_patch[:, :, 0].astype(np.int16) + hue_shift) % 180
        hsv_patch[:, :, 1] = np.clip(hsv_patch[:, :, 1].astype(np.int16) + saturation_shift, 0, 255)

        set_patch(image, region, cv2.cvtColor(hsv_patch, cv2.COLOR_HSV2BGR))


class BlurAlteration(ImageAlteration):
    name = "Strong Blur"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        blurred_patch = cv2.GaussianBlur(patch, (25, 25), 0)

        set_patch(image, region, blurred_patch)


class BrightnessAlteration(ImageAlteration):
    name = "Brightness Change"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        brightness_change = random_generator.choice([-70, -55, 55, 70])
        changed_patch = np.clip(patch.astype(np.int16) + brightness_change, 0, 255).astype(np.uint8)

        set_patch(image, region, changed_patch)


class ContrastAlteration(ImageAlteration):
    name = "Contrast Change"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        contrast = random_generator.choice([1.45, 1.65, 1.85])
        adjusted_patch = cv2.convertScaleAbs(patch, alpha=contrast, beta=0)

        set_patch(image, region, adjusted_patch)


class TintOverlayAlteration(ImageAlteration):
    name = "Tint Overlay"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        tint_colour = random_generator.choice(
            [
                (45, 45, 160),
                (45, 150, 45),
                (150, 80, 30),
                (30, 140, 170),
            ]
        )
        overlay = np.full_like(patch, tint_colour)
        tinted_patch = cv2.addWeighted(patch, 0.65, overlay, 0.35, 0)

        set_patch(image, region, tinted_patch)


class ShiftPatchAlteration(ImageAlteration):
    name = "Patch Shift"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        shift_x = random_generator.choice([-8, -6, 6, 8])
        shift_y = random_generator.choice([-8, -6, 6, 8])
        transform = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        shifted_patch = cv2.warpAffine(
            patch,
            transform,
            (region.width, region.height),
            borderMode=cv2.BORDER_REFLECT,
        )

        set_patch(image, region, shifted_patch)


class SharpenAlteration(ImageAlteration):
    name = "Sharpen Detail"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        kernel = np.array([[0, -1, 0], [-1, 5.8, -1], [0, -1, 0]])
        sharpened_patch = cv2.filter2D(patch, -1, kernel)

        set_patch(image, region, sharpened_patch)


class PixelateAlteration(ImageAlteration):
    name = "Pixelate"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        block_size = random_generator.choice([7, 9, 11])
        small_width = max(1, region.width // block_size)
        small_height = max(1, region.height // block_size)
        small_patch = cv2.resize(patch, (small_width, small_height), interpolation=cv2.INTER_LINEAR)
        pixelated_patch = cv2.resize(small_patch, (region.width, region.height), interpolation=cv2.INTER_NEAREST)

        set_patch(image, region, pixelated_patch)


class NoiseGrainAlteration(ImageAlteration):
    name = "Noise Grain"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        strength = random_generator.randint(18, 34)
        noise = np.random.default_rng().normal(0, strength, patch.shape)
        noisy_patch = np.clip(patch.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        set_patch(image, region, noisy_patch)


class EdgeGlowAlteration(ImageAlteration):
    name = "Edge Glow"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        gray_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_patch, 80, 160)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        glow_colour = random_generator.choice([(0, 210, 255), (255, 180, 0), (80, 255, 120)])
        glow_layer = np.zeros_like(patch)
        glow_layer[edges > 0] = glow_colour
        glowing_patch = cv2.addWeighted(patch, 0.82, glow_layer, 0.55, 0)

        set_patch(image, region, glowing_patch)


class DesaturateAlteration(ImageAlteration):
    name = "Desaturate"

    def apply(self, image, region, random_generator):
        patch = get_patch(image, region)
        gray_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        gray_patch = cv2.cvtColor(gray_patch, cv2.COLOR_GRAY2BGR)
        desaturated_patch = cv2.addWeighted(patch, 0.25, gray_patch, 0.75, 0)

        set_patch(image, region, desaturated_patch)
