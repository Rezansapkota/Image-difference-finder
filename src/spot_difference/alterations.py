from abc import ABC, abstractmethod

import cv2
import numpy as np


class ImageAlteration(ABC):
    name = "Image Alteration"

    @abstractmethod
    def apply(self, image, region, random_generator):
        pass


class ColourShiftAlteration(ImageAlteration):
    name = "Colour Shift"

    def apply(self, image, region, random_generator):
        patch = image[region.y : region.y + region.height, region.x : region.x + region.width]
        hsv_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)

        hue_shift = random_generator.randint(12, 30)
        saturation_shift = random_generator.randint(8, 24)

        hsv_patch[:, :, 0] = (hsv_patch[:, :, 0].astype(np.int16) + hue_shift) % 180
        hsv_patch[:, :, 1] = np.clip(hsv_patch[:, :, 1].astype(np.int16) + saturation_shift, 0, 255)

        image[region.y : region.y + region.height, region.x : region.x + region.width] = cv2.cvtColor(
            hsv_patch, cv2.COLOR_HSV2BGR
        )


class BlurAlteration(ImageAlteration):
    name = "Blur"

    def apply(self, image, region, random_generator):
        patch = image[region.y : region.y + region.height, region.x : region.x + region.width]
        blurred_patch = cv2.GaussianBlur(patch, (15, 15), 0)

        image[region.y : region.y + region.height, region.x : region.x + region.width] = blurred_patch


class BrightnessAlteration(ImageAlteration):
    name = "Brightness Change"

    def apply(self, image, region, random_generator):
        patch = image[region.y : region.y + region.height, region.x : region.x + region.width]
        brightness_change = random_generator.choice([-35, -25, 25, 35])
        changed_patch = np.clip(patch.astype(np.int16) + brightness_change, 0, 255).astype(np.uint8)

        image[region.y : region.y + region.height, region.x : region.x + region.width] = changed_patch
