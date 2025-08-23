from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageFont, ImageDraw

img = Image.open('images/morsify.png').convert('RGBA')
w, h = img.size

txt_layer =  Image.new('RGBA', img.size, (255, 255, 255, 0))
draw = ImageDraw.Draw(txt_layer)

font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size=22)

draw.text(
    (w - 90, h - 90),
    "marcobernacer@gmail.com",
    fill=(255, 255, 255, 128),
    font=font,
    anchor='rs'
)
watermarked_image = Image.alpha_composite(img.copy(), txt_layer)
watermarked_image.show()

# print(img.format, img.size, img.mode)