import os
import colorsys
from concurrent.futures import ProcessPoolExecutor, as_completed    # Import used libraries and multi-threading
from tqdm import tqdm
from PIL import Image

#########################################################################################################################
# We will try a simple approach to determine the health:

# Because there are some cromatic aberations that we don't want to include,
# we will use hue values to determine which pixels have the correct color and transform the images to grayscale
# in order to determine if they are coloured or not.

# The pixels will be checked in a little circle centered in the middle of each picture because that's where the magnetic
# field is being measured
#########################################################################################################################


def calculate_hue_range(image_path):            # This function can be run by the user before the actual health analysis
    image = Image.open(image_path)              # It is here so that the user gets an idea of what the average hue ranges
    pixels = image.load()                       # can be found in the images
    width, height = image.size

    min_hue = 360                               # Initialize variables
    max_hue = 0.0
    colored_pixel_count = 0

    for y in range(height):                     # Analyzing a photo
        for x in range(width):
            r, g, b = pixels[x, y]
            grayscale_value = (r + g + b) // 3  # Calculate grayscale value


            if (r, g, b) != (grayscale_value, grayscale_value, grayscale_value):     # Exclude black, white, and gray pixels

                h, _, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)             # Calculate hue value for the coloured pixel
                h_degrees = h * 360.0                                                # Convert hue to degrees


                if h_degrees != 0.0 and h_degrees != 360.0:                           # Exclude hue values of 0 and 360
                    min_hue = min(min_hue, h_degrees)
                    max_hue = max(max_hue, h_degrees)
                    colored_pixel_count += 1

    return min_hue, max_hue, colored_pixel_count




def count_pixels_with_hue_range(image_path, hue_range, center_x, center_y, radius):
    image = Image.open(image_path)
    pixels = image.load()
    width, height = image.size

    hue_count = 0

    for y in range(center_y - radius, center_y + radius + 1):                      # We're only searching the central area of the measurement
        if 0 <= y < height:                                                        # Ensure y coordinate is within image bounds
            for x in range(center_x - radius, center_x + radius + 1):
                if 0 <= x < width:                                                 # Ensure x coordinate is within image bounds
                                                                                   # Checking if the pixel is within the circular area
                    if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                        r, g, b = pixels[x, y]

                        grayscale_value = (r + g + b) // 3                         # Same operations as before

                                                                                   # Exclude black, white, and gray pixels
                        if (r, g, b) != (grayscale_value, grayscale_value, grayscale_value):
                                                                                   # Calculate hue value for the colored pixel
                            h, _, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                            h_degrees = h * 360.0                                  # Convert hue to degrees

                            if hue_range[0] <= h_degrees <= hue_range[1]:
                                hue_count += 1

    return hue_count


if __name__ == '__main__':
    image_folder = 'hue'                                                   # My folder path to the images
    image_files = [os.path.join(image_folder, filename) for filename in os.listdir(image_folder) if filename.endswith((".jpg", ".png"))]

    total_images = len(image_files)                                        # Using the functions and making a small UI for usability

    analyze_images = input("Do you want to analyze each image (~3 minutes)? (yes/no): ").lower().strip() == "yes"

    if analyze_images:
        average_min_hue = 0.0
        average_max_hue = 0.0
        colored_pixel_count_sum = 0

        with tqdm(total=total_images, desc="Analyzing Images", unit="image") as pbar:
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(calculate_hue_range, image_path) for image_path in image_files]

                for future in as_completed(futures):
                    min_hue, max_hue, colored_pixel_count = future.result()
                    average_min_hue += min_hue
                    average_max_hue += max_hue
                    colored_pixel_count_sum += colored_pixel_count
                    pbar.update(1)

        if total_images > 0:
            average_min_hue /= total_images
            average_max_hue /= total_images
            print("Average Hue Range:")
            print("Minimum Hue:", format(average_min_hue, ".10f"))
            print("Maximum Hue:", format(average_max_hue, ".10f"))
            print("Total Colored Pixels:", colored_pixel_count_sum)
        else:
            print("No images found in the folder.")

    average_min_hue = float(input("Enter the average minimum hue: "))
    average_max_hue = float(input("Enter the average maximum hue: "))
    colored_pixel_count_sum = 0


    hue_range = (average_min_hue, average_max_hue)                                      # Using the specified hue range to count pixels

                                                                                         # Calculate the center of the image
    image = Image.open(image_files[0])
    width, height = image.size
    center_x = width // 2
    center_y = height // 2


    radius = int(input("Enter the radius of the circular area to search (in pixels): ")) # Set the radius of the circular area to search

    pixel_count_list = []

    with tqdm(total=total_images, desc="Counting Pixels", unit="image") as pbar:
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(count_pixels_with_hue_range, image_path, hue_range, center_x, center_y, radius) for image_path in image_files]

            for future in as_completed(futures):
                pixel_count = future.result()
                pixel_count_list.append(pixel_count)
                pbar.update(1)

    min_pixels = min(pixel_count_list)
    max_pixels = max(pixel_count_list)

    print("Hue Range:")
    print("Minimum Hue:", format(hue_range[0], ".10f"))
    print("Maximum Hue:", format(hue_range[1], ".10f"))
    print()

    with open("scores.txt", "w") as f:
        for i, pixel_count in enumerate(pixel_count_list):
            score = 100 * (pixel_count - min_pixels) / (max_pixels - min_pixels)
            f.write(f"Image {i+1}: Score - {format(score, '.10f')}\n")

    print("Scores saved in 'scores.txt' file.")                                     # Print results
