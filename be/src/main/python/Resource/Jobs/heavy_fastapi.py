from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from PIL import Image, ImageFont, ImageDraw
from moviepy.editor import *
import numpy as np
import time
import os , sys

# initialize the FastAPI app
app = FastAPI()


# enable CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


###############
# ROOT ENDPOINT
###############
@app.get("/")
async def root():
    video = video2chars()
    video.movie2movie('videos/example.MOV', 'videos/out.MP4')
    return {"Successfully saved video"}

class video2chars():
    def __init__(self):
        self.ascii_char = "@WWMMHHBBRREEZZXXGG##LL***kkkknnnssssoooocccc++++----....."

    def pixel2chars(self,r, g, b, alpha=256):
        ''' map the grayscale 256 into 70 ascii characters  '''
        length = len(self.ascii_char)
        gray = int(0.2126 * r + 0.7152 * g + 0.0722 * b)
        unit = (256.0 + 1) / length
        return self.ascii_char[int(gray / unit)]

    def frame2chars(self,img):
        font = ImageFont.truetype('videos/Arial.ttf', 10, encoding='unic')
        font_w, font_h = font.getsize(self.ascii_char[1])

        txt = ""
        colors = []
        width_raw=img.shape[1]
        height_raw=img.shape[0]
        width=int(width_raw//font_w)
        height=int(height_raw//font_h)
        img = Image.fromarray(img).resize((width,height), Image.NEAREST)

        for i in range(height):
            for j in range(width):
                pixel = img.getpixel((j, i))
                colors.append((pixel[0], pixel[1], pixel[2]))
                txt += self.pixel2chars(pixel[0], pixel[1], pixel[2])
            txt += '\n'
            colors.append((255, 255, 255))

        img_txt = Image.new("RGB", (width_raw, height_raw), (255, 255, 255))
        dr = ImageDraw.Draw(img_txt)
        x = y = 0
        for i in range(len(txt)):
            if (txt[i] == '\n'):
                x =0
                y += font_h
            else:
                dr.text((x, y), text=txt[i], font=font, fill=colors[i])
                x += font_w
        return np.array(img_txt)

    def movie2movie(self,input,output='out.MP4'):
        videoclip = VideoFileClip(input)
        videoclip_txt=videoclip.fl_image(self.frame2chars)
        videoclip_txt.write_videofile(output)

    def frame2frame(self,input,output="out.png"):
        from matplotlib import pyplot as plt
        import cv2
        img = cv2.imread(input)
        img = self.frame2chars(img)
        #plt.imshow(img)
        plt.savefig(output)
        #plt.show()