#!/usr/bin/python3
""" Utility program to sharpen an image by enhancing edges """
import sys
import argparse
import logging
import cv2
import numpy as np

def measure_sharpness(lumin):
    """ Measure laplacian sharpness of image """
    sharpness = cv2.Laplacian(lumin, cv2.CV_64F).var()

    return sharpness

def sharpen(image):
    """ Apply a sharpening kernel to enhance object edges """
    sharpen_kernel = np.array([[-1, -1, -1, -1, -1],
                               [-1, 2, 2, 2, -1],
                               [-1, 2, 8, 2, -1],
                               [-1, 2, 2, 2, -1],
                               [-1, -1, -1, -1, -1]]) / 8.0
    sharp_image = cv2.filter2D(image, -1, sharpen_kernel)

    return sharp_image

def main():
    """ Driver for image sharpening process """
    parser = argparse.ArgumentParser(description='Utility to enhance Stratelite images by\
        increasing sharpness.')
    parser.add_argument('source', action='store', help='Designate file to be processed.')
    parser.add_argument('dest', action='store', help='Set name of output file.')
    parser.add_argument('--log-level', action='store', dest='loglevel', help='Set logging level.')
    args = parser.parse_args()
    loglevel = args.loglevel
    if loglevel is not None:
        numeric_level = getattr(logging, loglevel.upper(), None)
    else:
        numeric_level = logging.ERROR

    logging.basicConfig(filename='sharpen.log', format='%(asctime)s: %(levelname)s %(message)s',
                        level=numeric_level)

    source_file = args.source
    dest_file = args.dest

    logging.info('\n* * * Start of processing run for %s * * *', source_file)

    img = cv2.imread(source_file)
    if img is None:
        logging.error('Unble to read source file: %s.', source_file)
        sys.exit(1)
    sharpness = measure_sharpness(img)
    print(f'Input file sharpness = {sharpness}.')
    sharpened_image = sharpen(img)
    sharpness = measure_sharpness(sharpened_image)
    print(f'Output file sharpness = {sharpness}.')
    write_status = cv2.imwrite(dest_file, sharpened_image)
    if write_status is False:
        logging.error('Writing destinaton file: %s faled. Exiting.', dest_file)
        sys.exit(1)


if __name__ == '__main__':
    main()
