from PIL import Image    
import glob
import os 
from decimal import Decimal
from tools import plot_data_temp
import numpy as np
import matplotlib.pyplot as plt

det = 'shoe'

trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
approx = False ####
estim = True ####
freq = 1/100

#2.00E+08_5_0.00098_9.20E-05_0.005_1_0.5
'''thresh = 2e8 #8.5e7 #zero-velocity threshold #1.5e7
win = 5 # 5
sig_a = 0.00098 # 0.00098
sig_w = 9.2e-5 # 8.7266463e-5
sig_vel = 0.005 # 0.01
acc = 1 # 0.5
gyr = 0.5 # 0.5'''

thresh = 1.5e6 #8.5e7 #zero-velocity threshold #1.5e7
win = 5 # 5
sig_a = 0.035234433782004124 # 0.00098
sig_w = 0.0008884048317068069 # 8.7266463e-5
sig_vel = 0.01 # 0.01
acc = 0.5 # 0.5
gyr = 0.5 # 0.5

print (sig_a)
print (sig_w)

'''
	0.007  5.2 × 10⁻⁵  0.0007
Accelerometer stat:  [0.01043317 0.01058136 0.12949975] - 0.07525733954408477
Gyroscope stat:  [0.00099735 0.00083695 0.00090819] - 0.0009165153937787042
Accelerometer stat1:  [0.01046322 0.0102999  0.05923537] - 0.035234433782004124
Gyroscope stat1:  [0.00091955 0.00086209 0.00088262] - 0.0008884048317068069
'''

files = glob.glob('data/hallway/walk/*.csv')
remove = ['data/hallway/walk/stationary.csv', 'data/hallway/walk/stationary1.csv', 'data/hallway/walk/exportfile.csv', 'data/hallway/walk/exportfileMAIN.csv', 'data/hallway/walk/exportfiletest.csv']
files = [os.path.basename(x).replace('.csv', '') for x in files if x not in remove]
#print (len(files))

for filename in files:
    #print (filename)
    plot_data_temp(det, win, thresh, trial_type, trial_speed, filename, freq, sig_a, sig_w, sig_vel, acc, gyr, approx, estim)

all = True

if all:
    image_files = sorted(glob.glob("results_vert/*.png"))
    image_files = sorted(image_files, key=lambda x: os.path.basename(x).lower())
    images = [Image.open(img) for img in image_files]
    img_width, img_height = images[-1].size
    cols, rows = 5, 4
    output_width = cols * img_width
    output_height = rows * img_height
    if len(image_files) != 17:
        plt.close('all')
        raise ValueError("Expected exactly 17 images, but found {}".format(len(image_files)))
    combined_image2 = Image.new("RGB", (output_width, output_height), (255, 255, 255))
    for index, img in enumerate(images):
        x_offset = (index % cols) * img_width
        y_offset = (index // cols) * img_height
        combined_image2.paste(img, (x_offset, y_offset))

    # Process first set of images
    image_files = sorted(glob.glob("results/*.png"))
    image_files = sorted(image_files, key=lambda x: os.path.basename(x).lower())
    images = [Image.open(img) for img in image_files]
    if len(image_files) != 17:
        plt.close('all')
        raise ValueError("Expected exactly 17 images, but found {}".format(len(image_files)))
    combined_image1 = Image.new("RGB", (output_width, output_height), (255, 255, 255))
    for index, img in enumerate(images):
        x_offset = (index % cols) * img_width
        y_offset = (index // cols) * img_height
        combined_image1.paste(img, (x_offset, y_offset))

    # Create final combined image with combined_graph1 on top of combined_graph2
    final_output_height = output_height * 2  # Double the height to stack them
    final_combined_image = Image.new("RGB", (output_width, final_output_height), (255, 255, 255))

    final_combined_image.paste(combined_image1, (0, 0))  # Place first combined image on top
    final_combined_image.paste(combined_image2, (0, output_height))  # Place second below

    final_combined_image.save("test_all/combined_graph_test2_%s.png" % ('%.2E' % Decimal(thresh)), quality=60, optimize=True)
else:
    image_files = sorted(glob.glob("results/*.png"))  # Adjust pattern to match your file names
    image_files = sorted(image_files, key=lambda x: os.path.basename(x).lower())
    print (image_files)
    if len(image_files) != 17:
        raise ValueError("Expected exactly 17 images, but found {}".format(len(image_files)))
    images = [Image.open(img) for img in image_files]
    img_width, img_height = images[0].size
    cols, rows = 5, 4
    output_width = cols * img_width
    output_height = rows * img_height
    combined_image = Image.new("RGB", (output_width, output_height), (255, 255, 255))

    for index, img in enumerate(images):
        x_offset = (index % cols) * img_width
        y_offset = (index // cols) * img_height
        combined_image.paste(img, (x_offset, y_offset))
    combined_image.save("test_all/combined_graph_%s.png" % ('%.2E' % Decimal(thresh)))