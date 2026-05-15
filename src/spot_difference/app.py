import base64
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import cv2

from src.spot_difference.game import MAX_DIFFERENCES
from src.spot_difference.game import MAX_MISTAKES
from src.spot_difference.game import SpotDifferenceGame


DEFAULT_DISPLAY_WIDTH = 520
DEFAULT_DISPLAY_HEIGHT = 520
BACKGROUND_COLOUR = "#f5f7fa"
HEADER_COLOUR = "#17324d"
PANEL_COLOUR = "#ffffff"
BORDER_COLOUR = "#c8d1dc"
PRIMARY_BUTTON = "#1e6f9f"
SECONDARY_BUTTON = "#5c6670"
TEXT_COLOUR = "#1f2933"
MUTED_TEXT = "#52616f"
SUCCESS_COLOUR = "#c62828"
REVEAL_COLOUR = "#1565c0"


class SpotDifferenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spot the Difference")
        self.minsize(1080, 720)
        self.configure(bg=BACKGROUND_COLOUR)

        self.game = SpotDifferenceGame()
        self.display_width = DEFAULT_DISPLAY_WIDTH
        self.display_height = DEFAULT_DISPLAY_HEIGHT
        self.scale_x = 1
        self.scale_y = 1
        self.original_photo = None
        self.modified_photo = None

        self._configure_styles()
        self._build_interface()
        self._update_status("Load an image to start.")

    def _configure_styles(self):
        # Keep all Tkinter style settings in one place.
        self.option_add("*Font", ("Segoe UI", 10))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=BACKGROUND_COLOUR)
        style.configure("Header.TFrame", background=HEADER_COLOUR)
        style.configure("Panel.TFrame", background=PANEL_COLOUR, relief="solid", borderwidth=1)
        style.configure("Title.TLabel", background=HEADER_COLOUR, foreground="#ffffff", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background=HEADER_COLOUR, foreground="#dce7f2", font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background=PANEL_COLOUR, foreground=TEXT_COLOUR, font=("Segoe UI", 12, "bold"))
        style.configure("Message.TLabel", background=BACKGROUND_COLOUR, foreground=HEADER_COLOUR, font=("Segoe UI", 12, "bold"))
        style.configure("ScoreCard.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("ScoreLabel.TLabel", background="#ffffff", foreground=MUTED_TEXT, font=("Segoe UI", 9))
        style.configure("ScoreValue.TLabel", background="#ffffff", foreground=TEXT_COLOUR, font=("Segoe UI", 14, "bold"))

    def _build_interface(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(18, 14))
        header.pack(fill=tk.X)

        title_area = ttk.Frame(header, style="Header.TFrame")
        title_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_area, text="Spot the Difference", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_area,
            text="Load an image, find five hidden OpenCV changes, and avoid three mistakes.",
            style="Subtitle.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        button_area = ttk.Frame(header, style="Header.TFrame")
        button_area.pack(side=tk.RIGHT)
        self._create_action_button(button_area, "Load Image", self.load_image, PRIMARY_BUTTON).pack(side=tk.LEFT)
        self._create_action_button(button_area, "Reveal", self.reveal_unfound, SECONDARY_BUTTON).pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        status_area = ttk.Frame(self, style="App.TFrame", padding=(18, 12, 18, 4))
        status_area.pack(fill=tk.X)

        self.remaining_text = tk.StringVar()
        self.mistakes_text = tk.StringVar()
        self.total_found_text = tk.StringVar()
        self.message_text = tk.StringVar()

        self._create_score_card(status_area, "Remaining", self.remaining_text).pack(side=tk.LEFT)
        self._create_score_card(status_area, "Mistakes", self.mistakes_text).pack(side=tk.LEFT, padx=(10, 0))
        self._create_score_card(status_area, "Total Found", self.total_found_text).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(status_area, textvariable=self.message_text, style="Message.TLabel").pack(
            side=tk.LEFT,
            padx=18,
            fill=tk.X,
            expand=True,
        )

        image_area = ttk.Frame(self, style="App.TFrame", padding=(18, 12, 18, 18))
        image_area.pack(fill=tk.BOTH, expand=True)
        image_area.columnconfigure(0, weight=1, uniform="image_columns")
        image_area.columnconfigure(1, weight=1, uniform="image_columns")
        image_area.rowconfigure(0, weight=1)

        original_panel = ttk.Frame(image_area, style="Panel.TFrame", padding=10)
        original_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(original_panel, text="Original", style="PanelTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.original_canvas = tk.Canvas(
            original_panel,
            bg="#eef2f6",
            highlightthickness=1,
            highlightbackground=BORDER_COLOUR,
        )
        self.original_canvas.pack(fill=tk.BOTH, expand=True)

        modified_panel = ttk.Frame(image_area, style="Panel.TFrame", padding=10)
        modified_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(modified_panel, text="Modified - click here", style="PanelTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.modified_canvas = tk.Canvas(
            modified_panel,
            bg="#eef2f6",
            highlightthickness=1,
            highlightbackground=BORDER_COLOUR,
            cursor="crosshair",
        )
        self.modified_canvas.pack(fill=tk.BOTH, expand=True)
        self.modified_canvas.bind("<Button-1>", self.handle_modified_click)

    def _create_action_button(self, parent, text, command, colour):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=colour,
            fg="#ffffff",
            activebackground=colour,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=9,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )

    def _create_score_card(self, parent, label, variable):
        card = ttk.Frame(parent, style="ScoreCard.TFrame", padding=(14, 8))
        ttk.Label(card, text=label, style="ScoreLabel.TLabel").pack(anchor=tk.W)
        ttk.Label(card, textvariable=variable, style="ScoreValue.TLabel").pack(anchor=tk.W)
        return card

    def load_image(self):
        # Ask the user for an image and prepare a new game round.
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
        # Convert the canvas click position back to the original image size.
        if self.game.original_image is None:
            return

        image_x = int(event.x / self.scale_x)
        image_y = int(event.y / self.scale_y)
        matched_region = self.game.check_click(image_x, image_y)

        if matched_region:
            self._draw_region(matched_region, SUCCESS_COLOUR)

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
        # Show every difference that has not been found yet.
        unfound_regions = self.game.reveal_unfound()

        if not unfound_regions:
            return

        for region in unfound_regions:
            self._draw_region(region, REVEAL_COLOUR)

        self._update_status("Unfound differences revealed. Load a new image to restart.")

    def _prepare_display_size(self):
        self.update_idletasks()

        image_height, image_width = self.game.original_image.shape[:2]
        available_width = max(DEFAULT_DISPLAY_WIDTH, self.original_canvas.winfo_width() - 4)
        available_height = max(DEFAULT_DISPLAY_HEIGHT, self.original_canvas.winfo_height() - 4)
        scale = min(available_width / image_width, available_height / image_height)

        self.display_width = max(1, int(image_width * scale))
        self.display_height = max(1, int(image_height * scale))
        self.scale_x = self.display_width / image_width
        self.scale_y = self.display_height / image_height

    def _draw_images(self):
        for canvas in (self.original_canvas, self.modified_canvas):
            canvas.config(width=self.display_width, height=self.display_height, scrollregion=(0, 0, self.display_width, self.display_height))

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
        success, encoded_image = cv2.imencode(".png", resized_image)

        if not success:
            raise ValueError("Could not prepare image for display.")

        image_data = base64.b64encode(encoded_image.tobytes()).decode("ascii")
        return tk.PhotoImage(data=image_data)

    def _update_status(self, message):
        self.remaining_text.set(str(self.game.remaining))
        self.mistakes_text.set(f"{self.game.mistakes}/{MAX_MISTAKES}")
        self.total_found_text.set(str(self.game.total_found))
        self.message_text.set(message)
