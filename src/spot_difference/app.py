import base64
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import cv2

from src.spot_difference.game import MAX_DIFFERENCES
from src.spot_difference.game import MAX_MISTAKES
from src.spot_difference.game import SpotDifferenceGame


DISPLAY_MAX_WIDTH = 520
DISPLAY_MAX_HEIGHT = 520


class SpotDifferenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spot the Difference")
        self.minsize(980, 680)

        self.game = SpotDifferenceGame()
        self.display_width = DISPLAY_MAX_WIDTH
        self.display_height = DISPLAY_MAX_HEIGHT
        self.scale_x = 1
        self.scale_y = 1
        self.original_photo = None
        self.modified_photo = None

        self._build_interface()
        self._update_status("Load an image to start.")

    def _build_interface(self):
        toolbar = tk.Frame(self, padx=12, pady=10)
        toolbar.pack(fill=tk.X)

        tk.Button(toolbar, text="Load Image", command=self.load_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text="Reveal", command=self.reveal_unfound).pack(side=tk.LEFT, padx=(8, 0))

        self.status_text = tk.StringVar()
        tk.Label(toolbar, textvariable=self.status_text, font=("Arial", 11)).pack(side=tk.LEFT, padx=18)

        self.message_text = tk.StringVar()
        tk.Label(self, textvariable=self.message_text, font=("Arial", 12, "bold"), fg="#1f4f5f").pack(fill=tk.X)

        image_area = tk.Frame(self, padx=12, pady=12)
        image_area.pack(fill=tk.BOTH, expand=True)

        original_panel = tk.Frame(image_area)
        original_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(original_panel, text="Original", font=("Arial", 12, "bold")).pack()
        self.original_canvas = tk.Canvas(
            original_panel,
            bg="#eeeeee",
            highlightthickness=1,
            highlightbackground="#999999",
        )
        self.original_canvas.pack(fill=tk.BOTH, expand=True)

        modified_panel = tk.Frame(image_area)
        modified_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        tk.Label(modified_panel, text="Modified - click here", font=("Arial", 12, "bold")).pack()
        self.modified_canvas = tk.Canvas(
            modified_panel,
            bg="#eeeeee",
            highlightthickness=1,
            highlightbackground="#999999",
        )
        self.modified_canvas.pack(fill=tk.BOTH, expand=True)
        self.modified_canvas.bind("<Button-1>", self.handle_modified_click)

    def load_image(self):
        image_path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("Bitmap files", "*.bmp"),
                ("All files", "*.*"),
            ],
        )

        if not image_path:
            return

        try:
            self.game.load_image(image_path)
        except ValueError as error:
            messagebox.showerror("Image error", str(error))
            return

        self._prepare_display_size()
        self._draw_images()
        self._update_status("Find all 5 differences.")

    def handle_modified_click(self, event):
        if self.game.original_image is None:
            return

        image_x = int(event.x / self.scale_x)
        image_y = int(event.y / self.scale_y)
        matched_region = self.game.check_click(image_x, image_y)

        if matched_region:
            self._draw_region(matched_region, "red")

            if self.game.is_round_complete():
                self._update_status("You found every difference. Load another image to continue.")
                messagebox.showinfo("Round complete", "All 5 differences found!")
            else:
                self._update_status(f"Good catch: {matched_region.alteration_name}.")

            return

        if self.game.has_too_many_mistakes():
            self._update_status("Too many mistakes. Load a new image to restart.")
            messagebox.showwarning(
                "Round over",
                f"You made {MAX_MISTAKES} mistakes and found {self.game.found_in_current_round} differences.",
            )
        else:
            self._update_status("No difference there.")

    def reveal_unfound(self):
        unfound_regions = self.game.reveal_unfound()

        if not unfound_regions:
            return

        for region in unfound_regions:
            self._draw_region(region, "blue")

        self._update_status("Unfound differences revealed. Load a new image to restart.")

    def _prepare_display_size(self):
        image_height, image_width = self.game.original_image.shape[:2]
        scale = min(DISPLAY_MAX_WIDTH / image_width, DISPLAY_MAX_HEIGHT / image_height, 1)

        self.display_width = max(1, int(image_width * scale))
        self.display_height = max(1, int(image_height * scale))
        self.scale_x = self.display_width / image_width
        self.scale_y = self.display_height / image_height

    def _draw_images(self):
        self.original_canvas.config(width=self.display_width, height=self.display_height)
        self.modified_canvas.config(width=self.display_width, height=self.display_height)
        self.original_canvas.delete("all")
        self.modified_canvas.delete("all")

        self.original_photo = self._cv_image_to_photo(self.game.original_image)
        self.modified_photo = self._cv_image_to_photo(self.game.modified_image)

        self.original_canvas.create_image(0, 0, image=self.original_photo, anchor=tk.NW)
        self.modified_canvas.create_image(0, 0, image=self.modified_photo, anchor=tk.NW)

    def _draw_region(self, region, colour):
        center_x, center_y = region.center
        radius = region.radius + 8

        x1 = (center_x - radius) * self.scale_x
        y1 = (center_y - radius) * self.scale_y
        x2 = (center_x + radius) * self.scale_x
        y2 = (center_y + radius) * self.scale_y

        for canvas in (self.original_canvas, self.modified_canvas):
            canvas.create_oval(x1, y1, x2, y2, outline=colour, width=4)

    def _cv_image_to_photo(self, image):
        resized_image = cv2.resize(image, (self.display_width, self.display_height), interpolation=cv2.INTER_AREA)
        rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
        success, encoded_image = cv2.imencode(".png", rgb_image)

        if not success:
            raise ValueError("Could not prepare image for display.")

        image_data = base64.b64encode(encoded_image.tobytes()).decode("ascii")
        return tk.PhotoImage(data=image_data)

    def _update_status(self, message):
        self.status_text.set(
            f"Remaining: {self.game.remaining}    "
            f"Mistakes: {self.game.mistakes}/{MAX_MISTAKES}    "
            f"Total found: {self.game.total_found}"
        )
        self.message_text.set(message)
