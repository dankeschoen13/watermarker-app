import os
import platform
import subprocess
from tkinter import *
import tkinter as tk
from tkinter import filedialog, font, messagebox
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageFont, ImageDraw

WINDOW_BG_COLOR = "#D9C4B0"
CANVAS_BG_COLOR = "#ECEEDF"
BUTTON_COLOR = "#BBDCE5"


home_dir = os.path.expanduser("~")
photos_dir = os.path.join(home_dir, "Pictures/Photos")

THUMBNAIL_SIZE = (200, 200)


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

        self.BOLD_FONT = font.Font(weight='bold')
        self.utils = Utilities()

        self.title("Watermark-er")
        self.minsize(800, 500)
        self.config(padx=50, pady=50)

        self.UI = dict()
        self.UI['toolbar'] = self.render_toolbar()
        self.UI['body'] = self.render_body()
        self.UI['options'] = self.render_options()

        self.images = dict()
        self.images_out = dict()
        self.thumbnails = [] # list of tk.Label widgets

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
        body_frame = tk.Frame(self)
        body_frame.pack(fill='both', expand=True)

        preview = tk.Canvas(
            body_frame,
            bg="white",
            highlightthickness=0
        )
        preview.pack(side='left', fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            body_frame,
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

    def render_options(self):
        options = tk.Frame(
            self,
            highlightthickness=1,
            highlightbackground='white'
        )
        options.pack(side="bottom", fill="x")

        clear_button = tk.Button(
            options,
            text="Clear",
            font=self.BOLD_FONT,
            fg='red',
            command=self.clear,
            state='disabled'
        )
        clear_button.pack(side='left', padx=10, pady=10)

        save_button = tk.Button(
            options,
            text="Save",
            font=self.BOLD_FONT,
            fg='green',
            command=self.save,
            state='disabled'
        )
        save_button.pack(side='right', padx=10, pady=10)

        return {'clear': clear_button, 'save': save_button}

    @staticmethod
    def update_scroll_region(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

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
                wraplength=THUMBNAIL_SIZE[0],
                justify='center',
                fg='black',
                width=THUMBNAIL_SIZE[0]+20, height=THUMBNAIL_SIZE[1]+20
            )
            label.img_path = path
            label.bind('<Button-1>', self.utils.on_thumbnail_click)
            self.thumbnails.append(label)

        self.relayout()
        self.UI['options']['clear'].config(state='normal')

    def apply_watermark(self):
        if self.images_out:
            if not messagebox.askyesno('Overwrite?','Images are already watermarked. Overwrite changes?'):
                return

        watermark =  self.UI['toolbar']['watermark'].get('1.0', tk.END)

        for idx, data in self.images.items():
            full_image = data['full'].convert('RGBA')

            size = full_image.size
            w, h = size

            txt_layer = Image.new('RGBA', size, (255, 255, 255, 0))

            draw = ImageDraw.Draw(txt_layer)
            font_size = int(min(w, h) * 0.05)
            font_style = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size=font_size)
            draw.text(
                xy=(w - 90, h - 90),
                text=watermark,
                fill=(255, 255, 255, 150),
                font=font_style,
                anchor='rs'
            )
            watermarked_image = Image.alpha_composite(full_image, txt_layer)
            wmarked_thumb = watermarked_image.copy()
            wmarked_thumb.thumbnail(THUMBNAIL_SIZE)
            tk_wmarked_thumb = ImageTk.PhotoImage(wmarked_thumb)

            self.images_out[idx] = {
                'watermarked': watermarked_image,
                'thumb': tk_wmarked_thumb,
                'label_out': f"Watermarked_image_{idx+1}"
            }

        for idx, label in enumerate(self.thumbnails):
            label.config(
                image=self.images_out[idx]['thumb'],
                text=f"✅ {self.images_out[idx]['label_out']}",
            )
            label.watermarked_image = self.images_out[idx]['watermarked']

        self.UI['options']['save'].config(state='normal')

    def save(self):
        folder_loc = filedialog.askdirectory(
            parent=self,
            initialdir=photos_dir,
            title="Select a Folder"
        )

        if not folder_loc:  # user canceled
            return

        for idx, image in self.images_out.items():
            output_label = image['label_out']
            im = image['watermarked']

            if im.mode in ('RGBA', 'P'):
                im = im.convert('RGB')

            output_path = os.path.join(folder_loc, f"{output_label}.jpg")

            im.save(output_path, format="JPEG")

        messagebox.showinfo('Success!', 'Your watermarked photos are saved to the chosen directory.')

    def clear(self):
        for label in self.thumbnails:
            label.destroy()

        self.thumbnails.clear()
        self.images.clear()
        self.images_out.clear()
        self.UI['options']['save'].config(state='disabled')
        self.UI['options']['clear'].config(state='disabled')



if __name__ == "__main__":
    app = Watermarker()
    app.mainloop()