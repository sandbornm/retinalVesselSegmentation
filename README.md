## Retinal Blood Vessel Segmentation from Fundus images

### Data
[STARE](https://cecas.clemson.edu/~ahoover/stare/)
[DRIVE](https://drive.grand-challenge.org/)

### Random walk segmentation examples

#### DRIVE Image 03
**Diagnosis**: Background Diabetic Retinopathy
![Drive03rw](https://github.com/sandbornm/cs8395Final/blob/master/results/randomWalk/drive03rwBoardNoHalo.png?raw=true)
#### DRIVE Image 04
**Diagnosis**: Normal
![Drive04rw](https://github.com/sandbornm/cs8395Final/blob/master/results/randomWalk/drive04rwBoardNoHalo.png?raw=true)


### Fractal dimension examples

#### STARE Image 255
**Diagnosis**: Normal **Fractal dimension**: 1.8024 
![Stare255fd](https://github.com/sandbornm/cs8395Final/blob/master/results/fractalDimension/stare255FracNormal.png?raw=true)

#### STARE Image 324
**Diagnosis**: Hollenhorst Plaque **Fractal dimension**: 1.6461
![Stare324fd](https://github.com/sandbornm/cs8395Final/blob/master/results/fractalDimension/stare324FracNormal.png?raw=true)

### Usage

#### preprocess.py
A preprocessing script to handle rgb to grayscale, multi-level Gaussian smoothing, and Hessian image extraction.\
**Usage:** `usage: preprocess.py input_dir output_dir s sigmaSmall sigmaMedium sigmaLarge | a | h`\
Option s smooths with sigmaSmall, sigmaMedium, sigmaLarge and adds the 3 smoothed images; option a averages the smoothed image, and h extracts the Hessian image using ITK's HessianToObjectnessMeasureImageFilter. Gray image is calculated by default.\
**Example usage:** `python preprocess.py input_dir output_dir s 1 2 4 a h`\
**Example meaning:** for all images in input_dir, calculate the grayscale image, smooth with sigmas 1,2,4 and add the 3 images together, average the result, use this image to extract the Hessian image, and finally write the Hessian image to output_dir.\
**Note:** functionality for thresholding and connected components is also included

#### randomWalkSeg.py
Get the segmentation of the input images using the random walker algorithm.\
**Usage:** `randomWalkSeg.py input_dir seg_dir v | d`\
Option v visualizes each stage of the segmentation by opening a matplotlib figure containing the input Hessian image, the random walk result, and the cleaned final result. Intensity scaling, denoising, and small object removal are all completed internally. Option d lists the pairwise Dice scores between each of the following stages: random walk result vs. input Hessian, ground truth vs. input Hessian, and random walk result vs. ground truth.\
**Example usage:** `python randomWalkSeg.py input_dir seg_dir v d  > results.txt`\
**Example meaning:** get the random walk segmentation for each file in input_dir, visualize each stage, and calculate Dice scores. Additionally, the output is redirected to `results.txt`.\
**Assumptions**: the number of files in each of the directories is the same

#### fractalDim.py
Calculate the fractal dimension for the input color image using its input segmentation image. Implements the counting boxes algorithm for covering an image in boxes and counting the boxes containing self-similarity detail at successively smaller scales. The fractal dimension is given by the log ratio of the number of boxes containing self-similarity detail, N, at scale r. 
**Usage:** `fractalDim.py seg_dir color_dir v | d`\
Option v visualizes the 2 images with the color input image on the left and the inverted (black foreground, white background) segmentation on the right. Option d prints the fractal dimension as it's calculated for each image.\
**Example usage:** `python fractalDim.py seg_dir color_dir v d > results.txt`\
**Example meaning:** get the fractal dimension for each file in seg_dir, visualize the result and write the fractal dimension values to `results.txt`\
**Assumptions:** the number of files in each of the directories is the same

