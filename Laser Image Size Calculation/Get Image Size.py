from PIL import Image, ImageChops
import numpy as np
import os
from scipy.spatial import ConvexHull
from math import sqrt
from skimage.feature import blob_log, blob_dog, blob_doh
import rawpy

path_to_images = ''
faint_green_image_path = ''

laser_area = 0.17 * 0.17 # m^2


def iter_through_folder_for_images(folder_path):
    """
    Iterates through a folders and returns any .jpg or .CR2 images found
    :param folder_path: Top level folder path
    :return: List of paths to images
    """
    directory = os.fsencode(folder_path)
    images = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            filename = os.fsdecode(file)
            if filename.endswith(".jpg") or filename.endswith(".CR2"):
                images.append(os.path.join(str(root, 'UTF-8'), filename))

    return images


def only_red(im):
    """
    Strips out all channels apart from red.
    """
    data = np.array(im)
    red, green, blue = data.T
    im2 = Image.fromarray(red.T)
    return im2


def difference_between_red_and_green(im):
    """
    Returns an image of the difference between the red and green channels.
    :param im: Original image
    :return: Difference between channels
    """
    data = np.array(im)
    red, green, blue = data.T
    redder = Image.fromarray(red.T)
    greener = Image.fromarray(green.T)
    difference = ImageChops.difference(redder, greener)
    return difference


@np.vectorize
def emphasise_difference(a, b):
    """
    Vectorised version of function allowing it to be performed on an numpy array (of which an image can take the form)
    """
    return a - b if a > b else 0

@np.vectorize
def abs_difference(a, b):
    return abs(a - b)


def emphasise_red_without_green(im):
    """
    Emphasises areas with high levels of red and less green
    """
    data = np.array(im)
    red, green, blue = data.T
    difference = emphasise_difference(red.T, green.T)
    return Image.fromarray(difference)


def emphasise_green_without_red_or_blue(im):
    """
    Emphasises areas with high levels of green and less red or blue
    """
    data = np.array(im)
    red, green, blue = data.T
    difference = emphasise_difference(green.T, (red.T + blue.T) / 2)
    return Image.fromarray(difference)


def emphasise_green_without_blue(im):
    """
    Emphasises areas with high levels of green and less red or blue
    """
    data = np.array(im)
    red, green, blue = data.T
    difference = emphasise_difference(green.T, blue.T)
    return Image.fromarray(difference)


def emphasise_red_without_others(im):
    """
    Emphasises areas with high levels of red and less green or blue
    """
    data = np.array(im)
    red, green, blue = data.T
    difference = emphasise_difference(red.T, (green.T + blue.T) / 2)
    return Image.fromarray(difference)


def threshold_image(im, target, maximum=255, minimum=0):
    """
    If an image's pixel is not within the bounds of the minimum and maximum then set it to the target
    """
    data = np.array(im)
    for row_index, row in enumerate(np.array(data)):
        for item_index, item in enumerate(row):
            if item > maximum or item < minimum:
                data[row_index][item_index] = target
    new_image = Image.fromarray(data)
    return new_image


# See 'http://scikit-image.org/docs/dev/auto_examples/features_detection/plot_blob.html' for an explanation of the
# blob detection algorithms below and their various merits and demerits.

# On images from [FILE_PATH_REDACTED]
# the Laplacian of Gaussian detection algorithm identified 4 points for 97% of the images, taking almost a day for the
# whole directory


def get_convex_hull_of_blobs_log(im):
    """
    Uses the Laplacian of Gaussian blob detection algorithm from scikit-image to identify the laser points and returns
    a ConvexHull of the points found.
    :param im: Image with laser points in
    :return: ConvexHull of points
    """
    threshold = .2
    tries = 5
    # Get blobs using Laplacian of Gaussian
    blobs_log = blob_log(im, max_sigma=10, threshold=threshold)
    # Compute radii in the 3rd column.
    blobs_log[:, 2] = blobs_log[:, 2] * sqrt(2)  # ToDo: Discount blobs with large radii

    while (len(blobs_log) > 4 or 4 > len(blobs_log) >= 0) and tries > 0:
        if len(blobs_log) < 4:
            threshold -= 0.05
        elif len(blobs_log) > 4:
            threshold += 0.05
        blobs_log = blob_log(im, max_sigma=10, threshold=threshold)
        tries -= 1

    assert len(blobs_log) == 4, len(blobs_log)

    return ConvexHull([(blob[0], blob[1]) for blob in blobs_log])


def get_convex_hull_of_blobs_dog(im):
    """
    Uses the Difference of Gaussian blob detection algorithm from scikit-image to identify the laser points and returns
    a ConvexHull of the points found.
    :param im: Image with laser points in
    :return: ConvexHull of points
    """
    threshold = .15
    tries = 5
    # Get blobs using Difference of Gaussian
    blobs_dog = blob_dog(im, max_sigma=30, threshold=threshold)
    # Compute radii in the 3rd column.
    blobs_dog[:, 2] = blobs_dog[:, 2] * sqrt(2) # ToDo: Discount blobs with large radii

    while (len(blobs_dog) > 4 or 4 > len(blobs_dog) >= 0) and tries > 0:
        if 2 <= len(blobs_dog) < 4:
            threshold -= 0.05
        elif 6 >= len(blobs_dog) > 4:
            threshold += 0.05
        blobs_dog = blob_dog(im, max_sigma=30, threshold=threshold)
        tries -= 1

    assert len(blobs_dog) == 4, len(blobs_dog)

    return ConvexHull([(blob[0], blob[1]) for blob in blobs_dog])


def get_convex_hull_of_blobs_doh(im):
    """
    Uses the Difference of Hessian blob detection algorithm from scikit-image to identify the laser points and returns
    a ConvexHull of the points found.
    :param im: Image with laser points in
    :return: ConvexHull of points
    """
    # Get blobs using Difference of Hessian
    blobs_doh = blob_doh(im, max_sigma=10, num_sigma=1, threshold=.005)
    # Compute radii in the 3rd column.
    blobs_doh[:, 2] = blobs_doh[:, 2] * sqrt(2) # ToDo: Discount blobs with large radii

    if 0 <= len(blobs_doh) < 4:
        blobs_doh = blob_doh(im, max_sigma=10, num_sigma=1, threshold=.0025)
    elif len(blobs_doh) > 4:
        blobs_doh = blob_doh(im, max_sigma=10, num_sigma=1, threshold=.0075)
    assert len(blobs_doh) == 4, len(blobs_doh)

    return ConvexHull([(blob[0], blob[1]) for blob in blobs_doh])


if __name__ == '__main__':
    try:
        dodgy_images_paths = []
        success = 0
        for image_path in iter_through_folder_for_images(faint_green_image_path)[1:]:
            # Discount the first image of each box so as to discount the test cards
            if image_path.endswith('.jpg') and not image_path.endswith('01.jpg'):
                current_image = Image.open(image_path, 'r')
            # PIL cannot open .CR2 images so use 'rawpy' instead
            elif image_path.endswith('.CR2') and not image_path.endswith('01.CR2'):
                with rawpy.imread(image_path) as raw:
                    current_image = raw.postprocess()
            else:
                continue

            green_without_blue = emphasise_green_without_blue(current_image)
            green_without_blue = threshold_image(green_without_blue, 0, minimum=100)
            green_without_blue = np.array(green_without_blue.convert('RGB'))

            try:
                convex = get_convex_hull_of_blobs_log(green_without_blue)
            except AssertionError as e:
                # If exactly four laser points have not been found, spit out the path and how many were found and save
                # the red_without_green image in this folder.
                print('Could not find exactly four laser points in image with path {}\n Found {} points'.format(image_path, e))
                out_name = image_path.split('\\')[-1]
                if out_name.endswith('.CR2'):
                    Image.fromarray(green_without_blue).save('EMPHASISED-{}.png'.format(out_name[:-4]))
                else:
                    Image.fromarray(green_without_blue).save('EMPHASISED-{}'.format(out_name[:-4]))
                dodgy_images_paths.append(image_path)
                continue
            else:
                success += 1

            # Calculate the size of the image in pixels
            size = green_without_blue.shape
            area_of_image = size[0] * size[1]

            # Calculate the area of the image overall using the area covered by the lasers in pixels and knowing that
            # in real life. Assumes the lasers are perpendicular to the seabed which is assuemed to be flat.
            # Note: convex.volume results in the area of the shape, convex.area results in the perimeter (a.k.a. surface
            #       area in 3D)
            area_covered_in_image = laser_area * area_of_image / convex.volume

            print(area_covered_in_image)

            current_image.close()

            # Every ten images print the accuracy
            if (success + len(dodgy_images_paths)) % 10 == 0:
                print('Percentage accuracy {}%'.format(success / (success + len(dodgy_images_paths)) * 100))
                print(dodgy_images_paths)
    except SystemExit:
        print('Percentage accuracy {}%'.format(success / (success + len(dodgy_images_paths)) * 100))
        print(dodgy_images_paths)
