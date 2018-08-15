# Summary of Work and Outcomes from Image Size Detection

### Work Done

Using the square of laser dots in each image you can calculate the area of the quadrilateral covered by the laser points, an area that is defined in the cruise documentation for the survey. Thus, assuming the lasers are perpendicular to the assumedly flat seabed, you can calculate the area covered by the image using the following equation:   
Area of Seabed Covered (m^2) = Area of Laser Square (m^2) * (Size of Image (pixels) / Size of Laser Square (pixels))

Detecting Laser Points

To detect the locations of the laser points we use channel filtering to remove noise from the image that is not the colour of the laser and then the image produced by that is fed to sci-kit image's 'blob_log' (Laplacian of Gaussian) blob detection algorithm.
Although other blob detection algorithms are coded in, they are less accurate although they take up less time.  
The LoG filter outputs a list of blobs (x, y, radius) which, if there are exactly 4 of them, are taken to be the laser points.  
This could later be improved to discount blobs with a large radius and to get a 'squareness index' of how square the list of points is to check it has found the correct ones.

The best channel filtering for a red laser has been found to be the 'emphasise_red_without_green' function, which is the result of the red channel minus the green channel (with negative values set to 0). Along with the LoG filter this was 97% accurate at identifying 4 points with around 2% of those being false positives.
The best filtering for a green laser has not been decided but taking the green channel minus the blue and then thresholding it so only points above 100 are visible appears to be the better option.

### Outcomes So Far

- Red lasers are much better than green for image recognition purposes so it would be preferable for surveys to use red in the future
