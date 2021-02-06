#!/usr/bin/python3
""" Utility program to enhance the contrast of an image using the CLAHE algorithm """
import sys
import argparse
import logging
import cv2

def read_and_split_image(source_file):
    """ Read an image file and split into l, a, and b channels """
    test_image = cv2.imread(source_file, 1)
    if test_image is None:
        logging.error('Unable to read input file: %s.', source_file)
        raise IOError
    lab_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab_image)

    return l, a, b

def measure_contrast(lumin):
    """ Measure RMS Contrast of image """
    rms_contrast = lumin.std()

    return rms_contrast

def enhance_contrast(lumin, limit):
    """ Enhance contrast by applying Contrast Limited Adaptive Histogram Equalization (CLAHE) """
    clahe = cv2.createCLAHE(clipLimit=float(limit), tileGridSize=(8, 8))
    cl = clahe.apply(lumin)

    return cl

def write_image(l, a, b, new_file):
    """ Recombine the l, a, and b channels and write the resulting image """
    limg = cv2.merge((l, a, b))
    nimg = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    write_status = cv2.imwrite(new_file, nimg)
    if write_status is False:
        logging.error('Write of output file %s failed.', new_file)
        raise IOError

def main():
    """ Driver for enhancement functions: contrast """
    parser = argparse.ArgumentParser(description='Utility to enhance Stratollite images by boosting\
        contrast.')
    parser.add_argument('source', action='store', help='Designate file to be processed.')
    parser.add_argument('dest', action='store', help='Specify output file name.')
    parser.add_argument('--limit', action='store', help='Amount of contrast enhancement to apply.')
    parser.add_argument('--log-level', action='store', dest='loglevel', help='Set logging level.')
    args = parser.parse_args()
    loglevel = args.loglevel
    if loglevel is not None:
        numeric_level = getattr(logging, loglevel.upper(), None)
    else:
        numeric_level = logging.ERROR

    logging.basicConfig(filename='enhance.log', format='%(asctime)s: %(levelname)s %(message)s',
                        level=numeric_level)

    source_file = args.source
    dest_file = args.dest
    clipping = args.limit
    if clipping is None:
        clipping = 3.0

    logging.info('\n* * * Start of processing run for %s * * *', source_file)

    try:
        l_chan, a_chan, b_chan = read_and_split_image(source_file)
    except IOError:
        logging.error('Reading input file failed. Exiting.')
        sys.exit(1)

    contrast = measure_contrast(l_chan)

    new_lumin = enhance_contrast(l_chan, clipping)

    new_contrast = measure_contrast(new_lumin)

    print(f'Contrast before = {contrast}, Contrast after = {new_contrast}')

    try:
        write_image(new_lumin, a_chan, b_chan, dest_file)
    except IOError:
        logging.error('Write to output file failed. Exiting.')
        sys.exit(1)

if __name__ == '__main__':
    main()
