import tkinter as tk

class FixationDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.bind("<Escape>", lambda e: self.close())

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.root.update()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.center = (w // 2, h // 2)

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
