from tkinter import *
from tkinter import filedialog
from PIL import Image

img = Image.open('images/morsify.png')
img.show()

print(img.format, img.size, img.mode)