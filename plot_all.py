from PIL import Image    
import glob
import os 
from ins_tools.util import *
import ins_tools.visualize as visualize
from ins_tools.INS import INS

from decimal import Decimal

def plot_data(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, temp_sigma_vel, temp_acc, temp_gyro):# approx, estim):
    # Gets the imu data from csv file
    with open(os.path.join('data',trial_type,trial_speed,file_name+'.csv'), mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        imu = np.array([list(map(float, row)) for row in reader], dtype=float) 

    # sigma_a = 0.00098, sigma_w = 8.7266463e-5
    ins = INS(imu, sigma_a = a, sigma_w = w, T=freq, temp_sigma_vel=temp_sigma_vel, temp_acc=temp_acc, temp_gyro=temp_gyro) #microstrain
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
    x = ins.baseline(zv=zv)

    visualize.plot_topdown(x, title='{}'.format(file_name.replace('exportfile', '').replace('_', '')), save_dir='results/%s' % (file_name.replace('exportfile', '').replace('_', '')), zv=zv, approx=approx, estim=estim) ####
    visualize.plot_vertical(x, title='{}'.format(file_name.replace('exportfile', '').replace('_', '')), save_dir='results_vert/%s' % (file_name.replace('exportfile', '').replace('_', '')), zv=zv) ####

det = 'shoe'
thresh = 2e8 #8.5e7 #zero-velocity threshold #1.5e7
win = 5   #window size 5

trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
approx = False ####
estim = True ####
freq = 1/100

win = 5 # 5
a = 0.00098 # 0.00098
w = 8.7266463e-5 # 9.2e-5 # 
vel = 0.01 # 0.01
acc = 0.5 # 1 # 
gyr = 0.5 # 0.5

'''files = glob.glob('data/hallway/walk/*.csv')
remove = ['data/hallway/walk/exportfile.csv', 'data/hallway/walk/exportfileMAIN.csv', 'data/hallway/walk/exportfiletest.csv']
files = [os.path.basename(x).replace('.csv', '') for x in files if x not in remove]

for filename in files:
    plot_data(det, win, thresh, trial_type, trial_speed, filename, freq, a, w, vel, acc, gyr)'''

all = False

if all:
    image_files = sorted(glob.glob("results_vert/*.png"))
    image_files = sorted(image_files, key=lambda x: os.path.basename(x).lower())
    images = [Image.open(img) for img in image_files]
    img_width, img_height = images[-1].size
    cols, rows = 5, 4
    output_width = cols * img_width
    output_height = rows * img_height
    if len(image_files) != 17:
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

    final_combined_image.save("combined_graph_win5_%s.png" % ('%.2E' % Decimal(thresh)), quality=60, optimize=True)
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
    combined_image.save("combined_graph_%s.png" % ('%.2E' % Decimal(thresh)))