#!/Users/michael/envs/bsb/bin/python

import itk
import sys
import os

if len(sys.argv) < 3:
	print("missing parameters!")
	print("usage: preprocess.py input_dir output_dir s sigmaSmall sigmaMedium sigmaLarge a | h")
	print("s smooths with sigma1,sigma2,sigma3; a averages the smoothed image")
	print("h gets the Hessian image ")
	print("example: preprocess.py input_dir output_dir s 1 2 3 a")
	sys.exit()

# handle args
srcdir = argv[1]
dstdir = argv[2]
smooth = False
avg = False
hess = False
if argv[3] == "s":
	smooth = True
	sigma1 = int(argv[4])
	sigma2 = int(argv[5])
	sigma3 = int(argv[6])
	if argv[7] == "a":
		avg = True
		if argv[8] == "h":
			hess = True
elif argv[3] == "h":
	hess = True

# file list
flist = sorted(os.listdir(srcdir))
if '.DS_Store' in slist:
	slist.remove('.DS_Store')

Dims = 2
# pixel and image
InputPixelType = itk.RGBPixel[itk.UC]
InputImageType = itk.Image[InputPixelType, Dims]
IndexType = itk.Index[Dims]
OutputPixelType = itk.UC  
OutputImageType = itk.Image[OutputPixelType, Dims]

# filters
LuminanceFilterType = itk.RGBToLuminanceImageFilter[InputImageType, OutputImageType]
SmoothFilterType = itk.SmoothingRecursiveGaussianImageFilter[OutputImageType, OutputImageType]
AddImageFilterType = itk.AddImageFilter[OutputImageType, OutputImageType, OutputImageType]
RescaleIntensityFilterType = itk.RescaleIntensityImageFilter[OutputImageType, OutputImageType]
ThresholdFilterType = itk.ThresholdImageFilter[OutputImageType]
MeanFilterType = itk.MeanImageFilter[OutputImageType, OutputImageType]
IntensityWindowType = itk.IntensityWindowingImageFilter[OutputImageType, OutputImageType]
MinMaxIntensity = itk.MinimumMaximumImageCalculator[OutputImageType]
IsolateImageFilter = itk.IsolatedConnectedImageFilter[OutputImageType, OutputImageType]

# Hessian things
HessianPixelType = itk.SymmetricSecondRankTensor[itk.D, Dims]
HessianImageType = itk.Image[HessianPixelType, Dims]
HessianToObjectnessFilterType = itk.HessianToObjectnessMeasureImageFilter[HessianImageType, OutputImageType]
HessianMultiScaleFilterType = itk.MultiScaleHessianBasedMeasureImageFilter[OutputImageType, HessianImageType, OutputImageType]


"""
	Smooth the grayscale image at 3 levels with user specified sigma values 
"""
def smoothWithDifferentSigmas(grayImage, smSigma, mdSigma, lgSigma):
	gauss1 = SmoothFilterType.New()
	gauss1.SetInput(grayImage)
	gauss1.SetSigma(smSigma)
	gauss1.Update()
	gauss2 = SmoothFilterType.New()
	gauss2.SetInput(grayImage)
	gauss2.SetSigma(mdSigma)
	gauss2.Update()
	gauss3 = SmoothFilterType.New()
	gauss3.SetInput(grayImage)
	gauss3.SetSigma(lgSigma)
	gauss3.Update()
	return gauss1.GetOutput(), gauss2.GetOutput(), gauss3.GetOutput()

"""
	Add together 3 smoothed images for each of the feature size categories- 
	small and thin vessels up to large and tubular
"""
def addImagesOfSigmas(smSigmaImage, mdSigmaImage, lgSigmaImage):
	adder1 = AddImageFilterType.New()
	adder2 = AddImageFilterType.New()
	adder1.SetInput1(smSigmaImage)
	adder1.SetInput2(mdSigmaImage)
	adder1.Update()
	adder2.SetInput1(adder1.GetOutput())
	adder2.SetInput2(lgSigmaImage)
	adder2.Update()
	return adder2.GetOutput()

"""
	Get the average image from a set of added images
"""
def getMeanImage(addedImg):
	me = MeanFilterType.New()
	me.SetInput(addedImg)
	me.Update()
	return me.GetOutput()

"""
	Get the grayscale image from a color image
"""
def getGrayImage(rgbImage):
	grayFilter = LuminanceFilterType.New()
	grayFilter.SetInput(rgbImage)
	grayFilter.Update()
	return grayFilter.GetOutput()

"""
	Apply a linear transformation to the pixel intensities of the input image - min and max calculated 
	internally thus no user input parameters
"""
def rescaleIntensity(img):
	rs = RescaleIntensityFilterType.New()
	rs.SetInput(img)
	rs.Update()
	return rs.GetOutput()

"""
	Apply a linear transformation to the pixel intensities of the input image with user specified min/max intensities
	in the output image 
"""
def rescaleIntensityWindow(img, omin, omax, wmin, wmax):
	win = IntensityWindowType.New()
	win.SetInput(img)
	win.SetOutputMinimum(omin)
	win.SetOutputMaximum(omax)
	win.SetWindowMinimum(wmin)
	win.SetWindowMaximum(wmax)
	return win.GetOutput()

"""
	Threshold the input image with the property that intensities greater than "above" are set to "value", intensities
	less than "below" are set to "value", intensities i < "below" or i > "above" are also set to "value"
"""
def threshold(img, below, above, outside, value):
	th = ThresholdFilterType.New()
	th.SetInput( img )
	th.ThresholdBelow(below)
	th.ThresholdAbove(above)
	th.ThresholdOutside(outside)
	th.SetOutsideValue(value)
	th.Update()
	return th.GetOutput()

"""
	Get the isolated connected image using 2 locations on the image specified by (x1, y1) and (x2, y2)
	set the limit on the lower threshold value with lower and the value with which to replace thresholded pixels with replacement
"""
def getIsolatedConnectedImage(img, x1, y1, x2, y2, lower, replacement):
	iso = IsolateImageFilter.New()
	ind = IndexType()
	ind2 = IndexType()
	# seed 1 e.g. optical nerve head location 
	ind = [x1, x2]
	# seed 2 e.g. fovea location
	ind2 = [y1, y2]
	iso.FindUpperThresholdOff()
	iso.SetLower(lower)
	iso.AddSeed1(ind)
	iso.AddSeed2(ind2)
	iso.SetReplaceValue(replacement)
	iso.SetInput(img)
	iso.Update()
	return iso.GetOutput()

"""
	Get the hessian image of the fundus image. alpha, beta = 0.5, 0.5 seems to work well for vessel-like structure
"""
def getHessianObjectness(img):
	ob = HessianToObjectnessFilterType.New()
	ob.SetBrightObject(False)
	ob.SetScaleObjectnessMeasure(True)
	ob.SetAlpha(0.5)
	ob.SetBeta(0.5)
	ob.SetGamma(2.0)
	ms = HessianMultiScaleFilterType.New()
	ms.SetInput(img)
	ms.SetHessianToMeasureFilter(ob)
	ms.SetSigmaStepMethodToLogarithmic()
	ms.SetSigmaMinimum(1.0)
	ms.SetSigmaMaximum(2.0)
	ms.SetNumberOfSigmaSteps(10)
	ms.Update()
	return ms.GetOutput()

# main loop
for fname in flist:
	rd = itk.ImageFileReader[InputImageType].New()
	if srcdir[-1] != "/":
		srcdir += "/"
	f = srcdir + fname
	rd.SetFileName(f)
	rd.Update()
	gr = getGrayImage(rd.GetOutput())
	if smooth:
		s,m,l = smoothWithDifferentSigmas(gr, sigma1, sigma2, sigma3)
		allf = addImagesOfSigmas(s, m, l)
		if avg:
			mea = getMeanImage(allf)
			grr = rescaleIntensity(mea)
		grr = rescaleIntensity(allf)
	if hess:
		h = getHessianObjectness(grr)

	wt = itk.ImageFileWriter[OutputImageType].New()
	if dstdir[-1] != "/":
		dstdir += "/"
	o = dstdir + fname + "_out.jpg"
	wt.SetFileName(o)
	if hess:
		wt.SetInput(h)
	else:
		wt.SetInput(grr)
	wt.Update()
# done 
print("done")
