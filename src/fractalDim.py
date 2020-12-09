#!/Users/michael/envs/bsb/bin/python
# adapted from https://trvrm.github.io/fractal-dimension.html

import numpy as np
import skimage
import matplotlib.pyplot as plt
from skimage import io
from skimage.filters import threshold_otsu
from skimage.color import rgb2gray
from skimage.util import crop, invert
from scipy.stats import linregress
import math
import os
import sys

if len(sys.argv) < 3:
	print("missing parameters!")
	print("usage: fractalDim.py seg_dir color_dir v d")
	print("seg_dir is 'path/to/segmentation/images', color_dir is 'path/to/color/images, v visualizes each result")
	print("d prints the output for each image as the fractal dimension is calculated")
	print("use `fractalDim.py seg_dir color_dir v > results.txt` to save results")
	sys.exit()

# handle args
segs = sys.argv[1]
clrs = sys.argv[2]
viz = False
disp = False
if sys.argv[3] == "v":
	viz = True
if sys.argv[4] == "d":
	disp = True

slist = sorted(os.listdir(segs))
if '.DS_Store' in slist:
	slist.remove('.DS_Store')

clist = sorted(os.listdir(clrs))
if '.DS_Store' in clist:
	clist.remove('.DS_Store')

"""
	Read the image and preprocess for fractal dimension calculation
"""
def loadImage(img):
	im = skimage.io.imread(img)
	ht, wd = im.shape[0], im.shape[1]
	imb = binaryThreshold(im)
	imn = invert(imb)
	return imn, ht, wd

"""
	Apply Otsu thresholding to the image and binarize the passed image 
"""
def binaryThreshold(img):
	thresh = threshold_otsu(img)
	binary =  img > thresh
	return binary

def fracable(img):
	return 0 in set(img.flatten())

"""
	Successively crop the image and count the number of tiles containing black pixels
"""
def countBoxes(img, length, height, width):
	h, w = height, width
	boxCount = 0
	specialCount = 0
	for x in range(w//length):
		for y in range(h//length):
			#img[b:d, a:c] === crop((a, b, c, d))
			a = x*length
			b = y*length
			c = (x+1)*length
			d = (y+1)*length
			choppedImg = img[b:d, a:c]
			boxCount+=1
			if fracable(choppedImg):
				specialCount+=1
	return specialCount

"""
	Count the number of boxes at each scale possible for the dimensions of the given image. 
	Generates a pair representing the numerator and denominator of the fractal dimension equation.
	A list of these pairs is used to calculate the slope when the loop exits.
"""
def getBoxCounts(img, height, width):
	length = min(height, width)
	while length > 5:
		special = countBoxes(img, length, height, width)
		yield math.log(1.0/length), math.log(special)
		length = (length//2)

"""
	Stores all of the (scale ,box count) pairs for the final fractal dimension calculation
"""
def allCounts(img, height, width):
	return (list(getBoxCounts(img, height, width)))

"""
	Calculate the slope between the number of boxes and scales with linregress; return fractal 
	dimension value
"""
def getFractalDimension(img, height, width):
	f = allCounts(img, height, width)
	x = [g[0] for g in f]
	y = [g[1] for g in f]
	fd = linregress(x,y).slope
	return fd

fdlist = []
for i in range(len(slist)):
	print("image ", clist[i])
	cimg = clrs + "/" + clist[i]
	simg = segs + "/" + slist[i]
	colorImg = skimage.io.imread(cimg)
	segImg, h, w = loadImage(simg)
	fd = getFractalDimension(segImg, h, w)
	fdlist.append(fd)

	if disp:
		print(f"fractal dimension of {slist[i][:-4]}: {fd}")

	if viz:
		fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), sharex=True, sharey=True)
		ax1.imshow(colorImg)
		ax1.axis('off')
		ax1.set_title('original')
		ax2.imshow(segImg, cmap='gray')
		ax2.axis('off')
		ax2.set_title('inverted segmentation')
		plt.show()
print(fdlist)
