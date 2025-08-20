import os
import platform
import subprocess
from tkinter import *
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

WINDOW_BG_COLOR = "#D9C4B0"
CANVAS_BG_COLOR = "#ECEEDF"
BUTTON_COLOR = "#BBDCE5"

home_dir = os.path.expanduser("~")
photos_dir = os.path.join(home_dir, "Pictures/Photos")

THUMBNAIL_SIZE = (200, 200)

class Watermarker(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Watermark-er")
        self.geometry("800x600")
        self.config(padx=50, pady=50)
        self.images = dict()
        # TOOLBAR
        self.toolbar = tk.Frame(
            self,
            highlightthickness=1,
            highlightbackground=WINDOW_BG_COLOR
        )
        self.toolbar.pack(side="top", fill="x")
        # TOOLBAR buttons
        self.upload_button = tk.Button(
            self.toolbar,
            text="Select files",
            command=self.open_files,
            relief="flat",
            highlightthickness=0
        )
        self.upload_button.pack(side="left", padx=5, pady=10)
        self.apply_button = tk.Button(
            self.toolbar,
            text="Apply watermark",
            command=self.open_files
        )
        self.apply_button.pack(side="left", padx=5, pady=10)

        #PREVIEW BOX
        self.preview = tk.Canvas(self, bg="white", highlightthickness=0)
        self.preview.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.preview.yview)
        scrollbar.pack(side="right", fill="y")
        self.preview.configure(yscrollcommand=scrollbar.set)
        self.preview_frame = tk.Frame(self.preview, bg="white")
        self.preview.create_window((0, 0), window=self.preview_frame, anchor="nw")

        self.preview.bind("<Enter>", self._bind_mousewheel)
        self.preview.bind("<Leave>", self._unbind_mousewheel)
        self.preview.bind("<Configure>", self.relayout)
        self.preview_frame.bind("<Configure>", self.update_scroll_region)

        self.thumbnails = []

    def update_scroll_region(self, event=None):
        self.preview.configure(scrollregion=self.preview.bbox("all"))

    def _on_mousewheel(self, event):
        if self.preview.tk.call("tk", "windowingsystem") == "aqua":  # macOS
            self.preview.yview_scroll(-1 * event.delta, "units")
        else:  # Windows / X11
            self.preview.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self, event):
        self.preview.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows / Mac
        self.preview.bind_all("<Button-4>", lambda e: self.preview.yview_scroll(-1, "units"))  # Linux
        self.preview.bind_all("<Button-5>", lambda e: self.preview.yview_scroll(1, "units"))

    def _unbind_mousewheel(self, event):
        self.preview.unbind_all("<MouseWheel>")
        self.preview.unbind_all("<Button-4>")
        self.preview.unbind_all("<Button-5>")

    def relayout(self, event=None):
        if not self.thumbnails:
            return

        width = self.preview.winfo_width()
        cols = max(1, width // (THUMBNAIL_SIZE[0] + 10))  # max(1, 800 // (200 + 10)) --> max(1, 3)

        for idx, label in enumerate(self.thumbnails):
            row = idx // cols # example idx: 1. row = 1 // 3 --> row = 0
            col = idx % cols # example idx: 1. col = 1 % 3 --> col = 1
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        for col in range(cols):
            self.preview_frame.grid_columnconfigure(col, weight=1)

    def open_files(self):
        file_paths = filedialog.askopenfilenames(
            parent=self,
            title="Choose photos to watermark",
            initialdir=photos_dir,
            filetypes=[("Images", ("*.png", "*.jpg", "*.jpeg"))],
        )

        if not file_paths:
            return

        for i, path in enumerate(file_paths):
            img_full = Image.open(path)

            img_thumb = img_full.copy()
            img_thumb.thumbnail(THUMBNAIL_SIZE)
            tk_thumb = ImageTk.PhotoImage(img_thumb)  # type: ignore

            self.images[i] = {
                'thumb': tk_thumb,
                'full': img_full,
                'path': path
            }

            label = tk.Label(
                master=self.preview_frame,
                image=tk_thumb,  # type: ignore
                text=f"Image: {os.path.basename(path)}",
                compound='top',
                background='white'
            )
            label.img_path = path
            label.bind('<Button-1>', on_thumbnail_click)
            self.thumbnails.append(label)

        self.relayout()


def on_thumbnail_click(event):
    system = platform.system()
    img_path = event.widget.img_path

    if system == "Darwin":
        subprocess.run(["open", img_path])
    elif system == "Windows":
        os.startfile(img_path)
    else:
        subprocess.run(["xdg-open", img_path])


if __name__ == "__main__":
    app = Watermarker()
    app.mainloop()