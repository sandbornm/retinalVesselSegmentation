#!/Users/michael/envs/bsb/bin/python

import numpy as np
import matplotlib.pyplot as plt

from skimage.segmentation import random_walker
from skimage.exposure import rescale_intensity
from skimage.filters import threshold_otsu
from skimage.restoration import denoise_bilateral
from skimage.morphology import remove_small_objects, erosion, disk
from skimage import io
import skimage
import cv2
import sys
import pandas
import math
import os
from scipy.stats import linregress

if len(sys.argv) < 3:
	print("missing parameters!")
	print("usage: randomWalkSeg.py input_dir seg_dir v d")
	print("input_dir is 'path/to/input/images' for segmentation, seg_dir is 'path/to/ground/truth/segmentations'")
	print("v visualizes each stage of the segmentation, d lists the pairwise Dice score between each step of the segmentation")
	print("use `randomWalkSeg.py input_dir seg_dir v d  > results.txt` to save results")
	print("note: number of files in each directory should be the same")
	sys.exit()

imgdir = sys.argv[1]
segdir = sys.argv[2]

ilist = sorted(os.listdir(imgdir))
if '.DS_Store' in ilist:
	slist.remove('.DS_Store')
print(ilist)
slist = sorted(os.listdir(segdir))
if '.DS_Store' in slist:
	slist.remove('.DS_Store')
print(slist)

viz = False
disp = False
if sys.argv[3] == "v":
	viz = True
if sys.argv[4] == "d":
	disp = True

"""
	Load the Hessian image and ground truth segmentation and rescale intensity.
"""
def loadImages(hessian, groundTruth):
	lhessian = skimage.io.imread(hessian, as_gray=True)
	lseg = skimage.io.imread(groundTruth, as_gray=True)
	hes = rescaleIntensity(lhessian)
	seg = np.asarray(lseg).astype(np.bool)
	return lhessian, hes, seg

"""
	Rescale the intensity of the image between 0 and 1
"""
def rescaleIntensity(img):
	return rescale_intensity(img, in_range=(-.35,1.35), out_range=(-1,1))

"""
	Obtain the markers for the random walk segmentation. Create 2 seed groups around normalized
	intensity values between [-1,1]
"""
def getMarkers(img):
	markers = np.zeros(img.shape, dtype=np.uint8)
	# mark by highest and lowest intensity pixels after rescaling image to [0,1]
	markers[img < -.98] = 1
	markers[img > .98] = 2
	return markers

"""
	Do the segmentation and invert the result to match the ground truth
"""
def getRandomWalkSegmentation(img):
	markers = getMarkers(img)
	seg = random_walker(img, markers, mode='bf')
	return cv2.bitwise_not(seg)

"""
	Denoise the segmentation with bilateral filter which replaces intensity with weighted average
	neighborhood intensity values
"""
def denoiseSegmentation(seg):
	return denoise_bilateral(seg, sigma_color=0.05, sigma_spatial=1, multichannel=False)

"""
	Binary threshold the segmented and denoised image with otsu thresholding
"""
def binaryThreshold(seg):
	thresh = threshold_otsu(seg)
	binary =  seg > thresh
	# boolean array
	return binary

"""
	Remove small objects from the resulting segmentation leaving connected vessels
"""
def removeSmallObjects(seg, min_size=5):
	return remove_small_objects(seg, min_size=min_size)

"""
	Implementation of the dice score for the ground truth and random walk segmentation
	adapted from https://gist.github.com/brunodoamaral/e130b4e97aa4ebc468225b7ce39b3137
"""
def getDiceScore(img, seg):
	img = np.asarray(img).astype(np.bool)
	seg = np.asarray(seg).astype(np.bool)

	if img.shape != seg.shape:	
		raise ValueError(f"img {img.shape} and seg {seg.shape} have different shapes!")

	# Dice equation
	sumImgSeg = img.sum() + seg.sum()
	if sumImgSeg == 0:
		# images are empty, default to 1
		return 1

	# Dice formula
	overlap = np.logical_and(img, seg)
	dice = 2. * overlap.sum() / sumImgSeg
	return dice

# main loop
results = []
for i in range(len(ilist)):
	# prepare images
	imf = imgdir + "/" + ilist[i]
	sgf = segdir + "/" + slist[i]

	print("current image: ", ilist[i])

	lhes, hes, seg = loadImages(imf, sgf)

	print(ilist[i])

	rwseg = getRandomWalkSegmentation(hes)

	den = denoise_bilateral(rwseg, sigma_color=0, sigma_spatial=0.5, multichannel=False)

	thresh = threshold_otsu(den)
	binary = den > thresh

	rm = remove_small_objects(binary, min_size=25)
	hbin = binaryThreshold(hes)
	rhbin = remove_small_objects(hbin, min_size=25)


	randomWalkVsHess = getDiceScore(rm, hbin)
	groundTruthVsHess = getDiceScore(seg, hbin)
	randomWalkVsGroundTruth = getDiceScore(seg, rm)
	results.append([randomWalkVsHess, groundTruthVsHess, randomWalkVsHess])

	if disp:
		print("dice between rwseg and input hessian ", randomWalkVsHess)
		print("dice between ground truth seg and input hessian ", groundTruthVsHess)
		print("dice between rwseg and ground truth seg ", randomWalkVsGroundTruth)

	if viz:
		fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 2, figsize=(8, 3.2), sharex=True, sharey=True)

		ax1.imshow(lhes, cmap='gray')
		ax1.axis('off')
		ax1.set_title('input')
		ax2.imshow(rwseg, cmap='magma')
		ax2.axis('off')
		ax2.set_title('random walk')
		ax3.imshow(rm, cmap='gray')
		ax3.axis('off')
		ax3.set_title('cleaned')
		ax4.imshow(seg, cmap='gray')
		ax4.axis('off')
		ax4.set_title('ground truth')
		fig.tight_layout()
		plt.show()
print("results are tuples consisting of Dice scores between the pairs [randomWalkVsHess, groundTruthVsHess, randomWalkVsHess]")
print(results)
print("done")


