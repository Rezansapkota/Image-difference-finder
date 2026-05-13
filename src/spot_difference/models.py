from dataclasses import dataclass


@dataclass
class DifferenceRegion:
    x: int
    y: int
    width: int
    height: int
    alteration_name: str
    found: bool = False

    @property
    def center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    @property
    def radius(self):
        return max(self.width, self.height) / 2

    def overlaps(self, other, padding=16):
        return not (
            self.x + self.width + padding < other.x
            or other.x + other.width + padding < self.x
            or self.y + self.height + padding < other.y
            or other.y + other.height + padding < self.y
        )

    def contains_click(self, x, y, tolerance=18):
        center_x, center_y = self.center
        distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
        return distance <= self.radius + tolerance
