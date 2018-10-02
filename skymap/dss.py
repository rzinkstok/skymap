import sys
from Tkinter import *
from PIL import Image, ImageTk
from astroquery.skyview import SkyView
import numpy

from skymap.database import SkyMapDatabase

sv = SkyView()

db = SkyMapDatabase()
object = "M 104"
res = db.query_one("""SELECT * FROM ngc_ngc2000 WHERE Name=(SELECT name FROM ngc_names WHERE object LIKE '%{}%')""".format(object))
rah = res['RAh']
ram = res['RAm']
ra = rah*15.0 + 15*ram/60.0

des = res['DE-']
ded = res['DEd']
dem = res['DEm']

dec = ded + dem/60.0
if des == "-":
    dec *= -1
print("{}h {}m -> {}".format(rah, ram, ra))
print("{}{}deg {}m -> {}".format(des, ded, dem, dec))



image = sv.get_images(position="{}, {}".format(ra, dec), survey="DSS", pixels=(1000, 1000), projection="Car")[0][0]
imdata = image.data
max = numpy.max(numpy.max(imdata))
imdata = numpy.rint(255*imdata/max).astype(numpy.int8)

img = Image.fromarray(imdata, 'L')

root = Tk()
canvas = Canvas(root, width=1000,height=1000)
canvas.pack()
image = ImageTk.PhotoImage(img)
imagesprite = canvas.create_image(500,500, image=image)
root.mainloop()


