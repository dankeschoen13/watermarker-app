import os
import platform
import subprocess
from tkinter import *
import tkinter as tk
from tkinter import filedialog
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageFont, ImageDraw

WINDOW_BG_COLOR = "#D9C4B0"
CANVAS_BG_COLOR = "#ECEEDF"
BUTTON_COLOR = "#BBDCE5"

home_dir = os.path.expanduser("~")
photos_dir = os.path.join(home_dir, "Pictures/Photos")

THUMBNAIL_SIZE = (300, 300)


class Utilities:

    def __init__(self):
        self.widget = None

    # MOUSEWHEEL EVENT (bind mousewheel to widget)
    def _on_mousewheel(self, event):
        if self.widget.tk.call("tk", "windowingsystem") == "aqua":  # macOS
            self.widget.yview_scroll(-1 * event.delta, "units")
        else:
            self.widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_mousewheel(self, widget):
        self.widget = widget
        widget.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows / Mac
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))  # Linux
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

    @staticmethod
    def unbind_mousewheel(widget):
        widget.unbind("<MouseWheel>")
        widget.unbind("<Button-4>")
        widget.unbind("<Button-5>")

    # CLICK EVENT (show full image via system-default viewer)
    @staticmethod
    def on_thumbnail_click(event):
        system = platform.system()

        if getattr(event.widget, "watermarked_image", None):  # case: modified
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            event.widget.watermarked_image.save(tmp.name)
            img_path = tmp.name
        else:  # case: original
            img_path = event.widget.img_path

        if system == "Darwin":
            subprocess.run(["open", img_path])
        elif system == "Windows":
            os.startfile(img_path)
        else:
            subprocess.run(["xdg-open", img_path])

    # MISC HELPERS
    @staticmethod
    def cols_config(widget, total, expand=None, default_weight=0, expand_weight=1):
        expand = expand or []
        for col in range(total):
            weight = expand_weight if col in expand else default_weight
            widget.grid_columnconfigure(col, weight=weight)


class Watermarker(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Watermark-er")
        self.minsize(800, 500)
        self.config(padx=50, pady=50)

        self.images = dict()
        self.images_out = dict()
        self.utils = Utilities()

        self.UI = dict()
        self.UI['toolbar'] = self.render_toolbar()
        self.UI['body'] = self.render_body()

        self.thumbnails = []


    def render_toolbar(self):
        toolbar = tk.Frame(
            self,
            highlightthickness=1,
            highlightbackground=WINDOW_BG_COLOR
        )
        toolbar.pack(side="top", fill="x")

        self.utils.cols_config(
            widget=toolbar,
            total=6,
            expand=[1, 4]
        )

        upload_button = tk.Button(
            toolbar,
            text="Select files",
            command=self.open_files,
        )
        upload_button.grid(column=0, row=0, padx=5, pady=10)

        wm_label = tk.Label(
            toolbar,
            text="Watermark:"
        )
        wm_label.grid(column=2, row=0, padx=5, pady=10)

        font = tkfont.Font(size=14)
        wm_text = tk.Text(
            toolbar,
            height=1,
            width=30,
            font=font
        )
        wm_text.insert('1.0', "marcobernacer@me.com")
        wm_text.grid(column=3, row=0, padx=5, pady=10)

        apply_button = tk.Button(
            toolbar,
            text="Apply watermark",
            command=self.apply_watermark
        )
        apply_button.grid(column=5, row=0, padx=5, pady=10)

        return {'upload':upload_button, 'watermark': wm_text, 'apply':apply_button}


    def render_body(self):
        preview = tk.Canvas(
            self,
            bg="white",
            highlightthickness=0
        )
        preview.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=preview.yview
        )
        scrollbar.pack(side="right", fill="y")
        preview.configure(yscrollcommand=scrollbar.set)  # assign the scrollbar

        preview_frame = tk.Frame(
            preview,
            bg="white"
        )
        preview.create_window((0, 0), window=preview_frame, anchor="nw")

        self.utils.bind_mousewheel(preview)
        preview_frame.bind("<Configure>", lambda e: self.update_scroll_region(preview))

        preview.bind("<Configure>", self.relayout)

        return {'preview': preview, 'preview_frame': preview_frame}


    @staticmethod
    def update_scroll_region(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))
        print("bbox:", canvas.bbox("all"))


    def relayout(self, event=None):
        if not self.thumbnails:
            return

        width = self.UI['body']['preview'].winfo_width()
        cols = max(1, width // (THUMBNAIL_SIZE[0] + 10))  # max(1, 800 // (200 + 10)) --> max(1, 3)

        for idx, label in enumerate(self.thumbnails):
            row = idx // cols # example idx: 1. row = 1 // 3 --> row = 0
            col = idx % cols # example idx: 1. col = 1 % 3 --> col = 1
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        for col in range(cols):
            self.UI['body']['preview_frame'].grid_columnconfigure(col, weight=1)


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
                master=self.UI['body']['preview_frame'],
                image=tk_thumb,  # type: ignore
                text=f"Image: {os.path.basename(path)}",
                compound='top',
                background='white',
                width=THUMBNAIL_SIZE[0], height=THUMBNAIL_SIZE[1]
            )
            label.img_path = path
            label.bind('<Button-1>', self.utils.on_thumbnail_click)
            self.thumbnails.append(label)

        self.relayout()


    def apply_watermark(self):
        watermark =  self.UI['toolbar']['watermark'].get('1.0', tk.END)

        for idx, data in self.images.items():
            full_image = data['full'].convert('RGBA')

            size = full_image.size
            w, h = size

            txt_layer = Image.new('RGBA', size, (255, 255, 255, 0))

            draw = ImageDraw.Draw(txt_layer)
            font_size = int(min(w, h) * 0.05)
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size=font_size)
            draw.text(
                xy=(w - 90, h - 90),
                text=watermark,
                fill=(255, 255, 255, 150),
                font=font,
                anchor='rs'
            )
            watermarked_image = Image.alpha_composite(full_image, txt_layer)
            wmarked_thumb = watermarked_image.copy()
            wmarked_thumb.thumbnail(THUMBNAIL_SIZE)
            tk_wmarked_thumb = ImageTk.PhotoImage(wmarked_thumb)

            self.images_out[idx] = {
                'watermarked': watermarked_image,
                'thumb': tk_wmarked_thumb
            }

        for idx, label in enumerate(self.thumbnails):
            label.config(image=self.images_out[idx]['thumb'])
            label.watermarked_image = self.images_out[idx]['watermarked']


        # print(watermark)



if __name__ == "__main__":
    app = Watermarker()
    app.mainloop()