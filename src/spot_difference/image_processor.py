import random

import cv2

from src.spot_difference.alterations import BlurAlteration
from src.spot_difference.alterations import BrightnessAlteration
from src.spot_difference.alterations import ContrastAlteration
from src.spot_difference.alterations import ColourShiftAlteration
from src.spot_difference.alterations import DesaturateAlteration
from src.spot_difference.alterations import EdgeGlowAlteration
from src.spot_difference.alterations import NoiseGrainAlteration
from src.spot_difference.alterations import PixelateAlteration
from src.spot_difference.alterations import SharpenAlteration
from src.spot_difference.alterations import ShiftPatchAlteration
from src.spot_difference.alterations import TintOverlayAlteration
from src.spot_difference.models import DifferenceRegion


class ImageProcessor:
    def __init__(self, difference_count=5):
        self.difference_count = difference_count
        self.random_generator = random.Random()
        self.alterations = [
            ColourShiftAlteration(),
            BlurAlteration(),
            BrightnessAlteration(),
            ContrastAlteration(),
            TintOverlayAlteration(),
            ShiftPatchAlteration(),
            SharpenAlteration(),
            PixelateAlteration(),
            NoiseGrainAlteration(),
            EdgeGlowAlteration(),
            DesaturateAlteration(),
        ]

    def load_image(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("The selected file could not be loaded as an image.")

        if image.shape[0] < 140 or image.shape[1] < 140:
            raise ValueError("Please choose an image at least 140 x 140 pixels.")

        return image

    def create_modified_image(self, original_image):
        # Apply one random alteration to each hidden difference region.
        modified_image = original_image.copy()
        difference_regions = self._create_difference_regions(original_image)

        for region in difference_regions:
            alteration = self.random_generator.choice(self.alterations)
            region.alteration_name = alteration.name
            alteration.apply(modified_image, region, self.random_generator)

        return modified_image, difference_regions

    def load_and_process(self, image_path):
        original_image = self.load_image(image_path)
        modified_image, difference_regions = self.create_modified_image(original_image)

        return original_image, modified_image, difference_regions

    def _create_difference_regions(self, image):
        # Pick non-overlapping areas where changes will be hidden.
        image_height, image_width = image.shape[:2]
        minimum_side = min(image_width, image_height)
        minimum_size = max(36, int(minimum_side * 0.09))
        maximum_size = max(minimum_size + 10, int(minimum_side * 0.18))

        regions = []
        attempts = 0
        maximum_attempts = 500

        while len(regions) < self.difference_count and attempts < maximum_attempts:
            attempts += 1

            region_width = self.random_generator.randint(minimum_size, maximum_size)
            region_height = self.random_generator.randint(minimum_size, maximum_size)
            x = self.random_generator.randint(0, image_width - region_width - 1)
            y = self.random_generator.randint(0, image_height - region_height - 1)

            candidate = DifferenceRegion(
                x=x,
                y=y,
                width=region_width,
                height=region_height,
                alteration_name="",
            )

            if any(candidate.overlaps(region) for region in regions):
                continue

            regions.append(candidate)

        if len(regions) < self.difference_count:
            raise ValueError("Could not place 5 non-overlapping differences on this image.")

        return regions
