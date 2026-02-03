import tkinter as tk
from screeninfo import get_monitors


class FixationDisplay:
    def __init__(self, screen_index: int = 0):
        monitors = get_monitors()

        if screen_index >= len(monitors):
            raise ValueError(f"Only {len(monitors)} monitor(s) detected.")

        mon = monitors[screen_index]

        self.root = tk.Tk()
        self.root.configure(bg="black")
        self.root.bind("<Escape>", lambda e: self.close())

        # Move window to selected monitor
        self.root.geometry(f"{mon.width}x{mon.height}+{mon.x}+{mon.y}")
        self.root.overrideredirect(True)  # remove window borders
        self.root.lift()
        self.root.focus_force()

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.root.update()

        self.center = (mon.width // 2, mon.height // 2)

    def show_fixation(self, color="white"):
        self.canvas.delete("all")
        x, y = self.center
        size = 20
        self.canvas.create_line(x, y-size, x, y+size, fill=color, width=3)
        self.canvas.create_line(x-size, y, x+size, y, fill=color, width=3)
        self.root.update()

    def show_text(self, text):
        self.canvas.delete("all")
        x, y = self.center
        self.canvas.create_text(x, y, text=text, fill="white", font=("Arial", 28))
        self.root.update()

    def close(self):
        self.root.destroy()
