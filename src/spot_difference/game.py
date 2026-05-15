from src.spot_difference.image_processor import ImageProcessor


MAX_DIFFERENCES = 5
MAX_MISTAKES = 3


class SpotDifferenceGame:
    def __init__(self):
        self.image_processor = ImageProcessor(difference_count=MAX_DIFFERENCES)
        self.original_image = None
        self.modified_image = None
        self.difference_regions = []
        self.mistakes = 0
        self.total_found = 0
        self.round_locked = True

    @property
    def remaining(self):
        return len([region for region in self.difference_regions if not region.found])

    @property
    def found_in_current_round(self):
        return MAX_DIFFERENCES - self.remaining

    def load_image(self, image_path):
        # Create the original and modified images for a fresh round.
        original_image, modified_image, difference_regions = self.image_processor.load_and_process(image_path)

        self.original_image = original_image
        self.modified_image = modified_image
        self.difference_regions = difference_regions
        self.mistakes = 0
        self.round_locked = False

    def check_click(self, x, y):
        # Mark a difference as found when the click lands inside its region.
        if self.round_locked:
            return None

        for region in self.difference_regions:
            if not region.found and region.contains_click(x, y):
                region.found = True
                self.total_found += 1

                if self.remaining == 0:
                    self.round_locked = True

                return region

        self.mistakes += 1

        if self.mistakes >= MAX_MISTAKES:
            self.round_locked = True

        return None

    def reveal_unfound(self):
        if self.original_image is None:
            return []

        self.round_locked = True
        return [region for region in self.difference_regions if not region.found]

    def is_round_complete(self):
        return self.original_image is not None and self.remaining == 0

    def has_too_many_mistakes(self):
        return self.mistakes >= MAX_MISTAKES
