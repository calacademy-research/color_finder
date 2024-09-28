import os
import argparse
import sys
from datetime import datetime
from PIL import Image
import numpy as np
import logging
import shutil  # To copy the image to the specified directory

class ColorImageFinder:
    def __init__(self, color, base_dir: str, dest_dir: str):
        # Hardcoded base directory
        self.base_directory = base_dir
        self.dest_directory = dest_dir  # Directory to save images that pass the threshold
        self.color = color.lower()  # Convert color to lowercase for easier comparison
        logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Define RGB bounds for different colors feel free to adjust bounds
        self.color_bounds = {
            'red': (np.array([255, 0, 0], dtype=np.uint8), np.array([255, 250, 255], dtype=np.uint8)),
            'green': (np.array([0, 200, 0], dtype=np.uint8), np.array([100, 255, 100], dtype=np.uint8)),
            'blue': (np.array([0, 0, 200], dtype=np.uint8), np.array([100, 100, 255], dtype=np.uint8)),
            'yellow': (np.array([200, 200, 0], dtype=np.uint8), np.array([255, 255, 100], dtype=np.uint8)),
            'orange': (np.array([255, 165, 0], dtype=np.uint8), np.array([255, 255, 100], dtype=np.uint8)),
            'pink': (np.array([150, 50, 100], dtype=np.uint8), np.array([255, 200, 220], dtype=np.uint8)),
            # Add more colors as needed
        }

    def is_within_date_range(self, folder_name, start_date, end_date):
        try:
            folder_date_str = folder_name.split('_')[1]  # Assuming date is in the second part: CP1_YYYYMMDD_BATCH
            folder_date = datetime.strptime(folder_date_str, '%Y%m%d')
            return start_date <= folder_date <= end_date
        except (IndexError, ValueError):
            return False

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

    def find_color_images(self, start_date: str, end_date: str, lower_bound: int, upper_bound: int):
        start_date = datetime.strptime(start_date, '%Y%m%d')
        end_date = datetime.strptime(end_date, '%Y%m%d')
        image_count = 0  # Count of images that pass the threshold

        # Walk through all directories in the base directory
        for folder in os.listdir(self.base_directory):
            folder_path = os.path.join(self.base_directory, folder)
            if os.path.isdir(folder_path) and self.is_within_date_range(folder, start_date, end_date):
                logging.info(f"Processing folder: {folder}")

                # Check both "undatabased" and "databased" subdirectories
                for subfolder in ["undatabased", "databased"]:
                    subfolder_path = os.path.join(folder_path, subfolder)
                    if os.path.exists(subfolder_path):
                        for root, _, files in os.walk(subfolder_path):
                            for file in files:
                                if "Cover" in file and file.lower().endswith('.tif'):
                                    image_path = os.path.join(root, file)
                                    color_percentage = self.count_color_pixels(image_path)

                                    # If colored pixels exceed the threshold, log it and save the image
                                    if lower_bound < color_percentage < upper_bound:
                                        result = f"{image_path} has more than {lower_bound}% " \
                                                 f"and less than {upper_bound}% {self.color} color: {color_percentage:.2f}%"
                                        logging.info(result)

                                        # Save the image to the target directory
                                        if self.dest_directory:
                                            try:
                                                save_path = os.path.join(self.dest_directory,
                                                                         os.path.basename(image_path))
                                                shutil.copy(image_path, save_path)
                                                logging.info(f"Saved image to {save_path}")
                                            except Exception as e:
                                                logging.error(f"Error saving image {image_path}: {e}")
                                        image_count += 1

                # Log and print the count of images that passed the threshold

            logging.info(f"Total images processed: {image_count}")

            logging.info(f"Total images with more than {lower_bound}% and "
                         f"less than {upper_bound}% {self.color} color: {image_count}")


def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description='Find images with more than 1% specified color.')
    parser.add_argument('lower_bound', type=int, help='minimum % of color to detect')
    parser.add_argument('upper_bound', type=int, help='maximum % of color to detect', default=100)
    parser.add_argument('filetype', type=str, help='filetype .png, .jpg, .tif', default=".tif")
    parser.add_argument('start_date', type=str, help='Start date in YYYYMMDD format')
    parser.add_argument('end_date', type=str, help='End date in YYYYMMDD format')
    parser.add_argument('color', type=str, help='Color to find (e.g., pink, orange)')

    args = parser.parse_args()

    base_directory = '/path/to/image/tree'
    dest_directory = '/path/to/shared/drive/folder'


    # Initialize the ColorImageFinder with the specified color
    finder = ColorImageFinder(color=args.color, base_dir=base_directory, dest_dir=dest_directory)

    # Run the finder
    finder.find_color_images(start_date=args.start_date,end_date=args.end_date, lower_bound=args.lower_bound,
                             upper_bound=args.upper_bound)


if __name__ == '__main__':
    main()
