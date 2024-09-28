import os
import argparse
import sys
from datetime import datetime
from PIL import Image
import numpy as np
import logging
import shutil  # To copy the image to the specified directory

class ColorImageFinder:
    def __init__(self, color, base_dir, dest_dir=None):
        self.base_directory = base_dir
        if dest_dir is None:
            self.dest_directory = dest_dir  # Directory to save images that pass the threshold
        self.color = color.lower()  # Convert color to lowercase for easier comparison
        logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        # Define RGB bounds for different colors
        self.color_bounds = {
            'red': (np.array([255, 0, 0], dtype=np.uint8), np.array([255, 250, 255], dtype=np.uint8)),
            'green': (np.array([0, 200, 0], dtype=np.uint8), np.array([100, 255, 100], dtype=np.uint8)),
            'blue': (np.array([0, 0, 200], dtype=np.uint8), np.array([100, 100, 255], dtype=np.uint8)),
            'yellow': (np.array([200, 200, 0], dtype=np.uint8), np.array([255, 255, 100], dtype=np.uint8)),
            'orange': (np.array([255, 165, 0], dtype=np.uint8), np.array([255, 255, 100], dtype=np.uint8)),
            'pink': (np.array([150, 50, 100], dtype=np.uint8), np.array([255, 200, 220], dtype=np.uint8)),
            # Add more colors as needed
        }

    def count_color_pixels(self, image_path):
        if self.color not in self.color_bounds:
            logging.error(f"Color '{self.color}' not supported.")
            return 0

        lower_bound, upper_bound = self.color_bounds[self.color]

        try:
            # Open image and convert to RGB
            image = Image.open(image_path).convert('RGB')
            image = image.resize((100, 100))  # Resize to speed up the calculation

            # Convert the image to a NumPy array
            image_data = np.array(image)

            # Create a mask for pixels that fall within the color range
            color_mask = np.all((image_data >= lower_bound) & (image_data <= upper_bound), axis=-1)

            # Calculate the number of colored pixels
            color_pixel_count = np.sum(color_mask)

            # Calculate the total number of pixels
            total_pixel_count = image_data.shape[0] * image_data.shape[1]

            # Calculate the percentage of colored pixels
            color_percentage = (color_pixel_count / total_pixel_count) * 100

            return color_percentage
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}")
            return 0  # Return 0 if there's an error processing the image

    def find_color_images(self, lower_bound: int, upper_bound: int, filetype: str):
        image_count = 0  # Count of images that pass the threshold
        # List of directories to scan, starting with the base directory
        directories_to_scan = [self.base_directory]

        while directories_to_scan:
            current_directory = directories_to_scan.pop()
            logging.info(f"Processing directory: {current_directory}")

            for item in os.listdir(current_directory):
                item_path = os.path.join(current_directory, item)

                if os.path.isdir(item_path):
                    # Add subdirectory to the list for scanning later
                    directories_to_scan.append(item_path)
                elif item.lower().endswith(filetype):
                    # Process the image file
                    color_percentage = self.count_color_pixels(item_path)

                    # If colored pixels exceed the threshold, log it and save the image
                    if lower_bound < color_percentage < upper_bound:
                        result = f"{item_path} has more than {lower_bound}% " \
                                 f"and less than {upper_bound}% {self.color} color: {color_percentage:.2f}%"
                        logging.info(result)

                        # Save the image to the target directory
                        if self.dest_directory:
                            try:
                                save_path = os.path.join(self.dest_directory, os.path.basename(item_path))
                                shutil.copy(item_path, save_path)
                                logging.info(f"Saved image to {save_path}")
                            except Exception as e:
                                logging.error(f"Error saving image {item_path}: {e}")
                        image_count += 1

        # Log and print the count of images that passed the threshold

        logging.info(f"Total images processed: {image_count}")

        logging.info(f"Total images with more than {lower_bound}% and "
                     f"less than {upper_bound}% {self.color} color: {image_count}")


def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description='Find images with % of specified color range.')
    parser.add_argument('color', type=str, help='Color to find (e.g., pink, orange)')
    parser.add_argument('lower_bound', type=int, help='minimum % of color to detect')
    parser.add_argument('upper_bound', type=int, help='maximum % of color to detect', default=100)
    parser.add_argument('filetype', type=str, help='filetype .png, .jpg, .tif')
    parser.add_argument('base_dir', type=str, help='image folder to scan')
    parser.add_argument('dest_dir', type=str, help='image folder to copy detected images to', default=None)

    args = parser.parse_args()

    # Initialize the ColorImageFinder with the specified color
    finder = ColorImageFinder(color=args.color,  base_dir=args.base_dir, dest_dir=args.dest_dir)

    # Run the finder
    finder.find_color_images(lower_bound=args.lower_bound, upper_bound=args.upper_bound, filetype=args.filetype)


if __name__ == '__main__':
    main()
