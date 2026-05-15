"""Program entry point for the Spot the Difference application."""

from src.spot_difference.app import SpotDifferenceApp


if __name__ == "__main__":
    # Start the Spot the Difference window.
    app = SpotDifferenceApp()
    app.mainloop()
