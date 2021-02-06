#!/usr/bin/python3

"""
Python utility to do basic processing of H264 video files.
This program takes an H.264 file as input and produces a collection of
all the frames that made up the video and a JSON file that contains
all the metadata for each frame in a human-readable form.
"""
import os
import sys
import secrets
import string
import datetime
from functools import partial
import subprocess
import configparser
import argparse
import logging
import pathlib
import json
import pytz
import cv2
import numpy as np
from PIL.PngImagePlugin import PngImageFile, PngInfo
import simplekml
from klvblock import KLVBlock

VALID_KEY = [0x06, 0x0e, 0x2b, 0x34, 0x02, 0x0b, 0x01, 0x01, 0x0e, 0x01, 0x03, 0x01,
             0x01, 0x00, 0x00, 0x00]
INCOMING = 'incoming'
OUTGOING = 'processed'

def generate_id(id_len, _randint=np.random.randint):
    """ Generate a unique, random key to link meta_data frames to video frames """
    pickchar = partial(secrets.choice, string.ascii_lowercase + string.ascii_uppercase +
                       string.digits)
    key = ''.join([pickchar() for _ in range(id_len)])
    return key

def get_target_list(incoming_dir):
    """ Get a list of .ts video files to be processed """
    logging.debug('Processing directory %s', incoming_dir)
    target_list = [f for f in os.listdir(incoming_dir) if f.endswith('.ts')]

    return target_list

def strip_meta_data(in_file, output_directory):
    """ Seperate meta_data data from video at rate of one meta_data frame for each video frame. """
    logger = logging.getLogger()
    out_file = os.path.join(output_directory, pathlib.Path(in_file).stem + '.klv')
    logging.debug('Processing %s to produce %s', in_file, out_file)
    if logger.level == logging.DEBUG:
        subprocess.run(['ffmpeg', '-i', in_file, '-map', '0:1',
                        '-codec', 'copy', '-f', 'data', out_file], check=True)
    else:
        subprocess.run(['ffmpeg', '-i', in_file, '-map', '0:1',
                        '-codec', 'copy', '-f', 'data', out_file], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)

    return out_file

def grab_frames(in_file, interval, png_out_dir, tif_out_dir):
    """ Extract one frame image for each second of video. """
    logging.debug('Extracting frames from %s', in_file)
    vid_cap = cv2.VideoCapture(in_file)
    frame_count = 0
    if vid_cap.isOpened():
        rval = True
        logging.debug('Creating output directory: %s', tif_out_dir)
        os.makedirs(tif_out_dir, 0o777)
        os.makedirs(png_out_dir, 0o777)
    else:
        rval = False
        logging.debug('Unable to open video file: %s', in_file)

    while rval:
        rval, frame = vid_cap.read()
        if rval:
            if frame_count % (interval * 30) == 0:
                tif_outfile = os.path.join(tif_out_dir, 'frame_' + \
                    str(frame_count).zfill(5) + '.tif')
                png_outfile = os.path.join(png_out_dir, 'frame_' + \
                    str(frame_count).zfill(5) + '.png')
                rc = cv2.imwrite(tif_outfile, frame)
                rc |= cv2.imwrite(png_outfile, frame)
                if rc is False:
                    logging.error('Writing image file failed.')
                    rval = False
                    raise IOError
            frame_count += 1

    vid_cap.release()

def decode_meta_data(in_file, out_dir):
    """
    Takes a meta_data binary file as input and outputs a JSON file with the data
    records decoded.
    """
    logging.debug('Processing metadata in %s to directory %s.', in_file, out_dir)
    with open(in_file, "rb") as f:
        block_count = 0
        file_dict = {}
        file_dict['source'] = in_file
        file_dict['processing_date'] = \
            datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f UTC')
        key = list(f.read(16))
        while key:
            if key == VALID_KEY:
                ber_flag = int.from_bytes(f.read(1), byteorder='big')
                if ber_flag & 0b10000000:
                    block_size = int.from_bytes(bytes(ber_flag) + f.read(1), byteorder='big')
                else:
                    block_size = ber_flag
                data_block = list(f.read(block_size))
                logging.info('Processing meta_data frame: %i size = %i', block_count, block_size)
                meta_data_block = KLVBlock(generate_id(16))
                frame_key = 'frame_' + str(block_count).zfill(5)
                file_dict[frame_key] = meta_data_block.process_block(data_block, block_size)
                block_count += 1
                key = list(f.read(16))
            else:
                key_err_msg = f'Block Key invalid: {key}'
                logging.error(key_err_msg)
                key = None
                raise RuntimeError

    out_file = os.path.join(out_dir, pathlib.Path(in_file).stem + '.json')
    try:
        with open(out_file, 'w') as j:
            json.dump(file_dict, j, indent=4)
    except FileNotFoundError:
        logging.error('Input file %s not found.', out_file)
        raise

    return out_file

def tag_png_frames(img_dir, klv_file):
    """ Copy KLV data from the meta_data file into tEXt fields in the images """
    logging.debug('Tagging image files in %s using data in %s', img_dir, klv_file)
    img_list = os.listdir(img_dir)
    kml = simplekml.Kml()
    with open(klv_file) as f:
        d = json.load(f)

    for img in img_list:
        img_path = os.path.join(img_dir, img)
        target_image = PngImageFile(img_path)
        metadata = PngInfo()
        meta = d.get(pathlib.Path(img).stem)
        for k, v in meta.items():
            metadata.add_text(k, v)

        lon = meta.get('frame_center_longitude')
        lat = meta.get('frame_center_latitude')
        alt = meta.get('frame_center_elevation')
        kml.newpoint(name=img, coords=[(lon, lat, alt)])

        target_image.save(img_path, pnginfo=metadata)
        kml.save(os.path.join(img_dir, 'image_list.kml'))

def main():
    """ Controller for all the video and image processing """
    parser = argparse.ArgumentParser(description='Process AC14 video files.')
    parser.add_argument('source', action='store', help='Video file to be processed.')
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read('pipeline.ini')
    mission = config['GENERAL']['mission']
    interval = int(config['GENERAL']['interval'])
    loglevel = config['GENERAL']['logLevel']
    if loglevel is not None:
        numeric_level = getattr(logging, loglevel.upper(), None)
    else:
        numeric_level = logging.ERROR

    logging.basicConfig(filename='pipeline.log', format='%(asctime)s: %(levelname)s %(message)s',
                        level=numeric_level)

    logging.info('\n* * * Start of processing run for %s * * *', INCOMING)

    video_source = args.source
    logging.info('Processing input video file: %s.', video_source)

    in_file_base = pathlib.Path(video_source).stem
    tif_directory = os.path.join(OUTGOING, mission, in_file_base + '_TIF')
    png_directory = os.path.join(OUTGOING, mission, in_file_base + '_PNG')

    logging.info('Extracting binary meta_data file from %s to %s.', video_source,
                    tif_directory)

    try:
        klv_file = strip_meta_data(video_source, OUTGOING)
    except subprocess.CalledProcessError as err:
        logging.error('ffmpeg failed with return code %d.', err.returncode)
        sys.exit(1)

    logging.info('Extracting frames from %s into %s and %s.', video_source, tif_directory,
                 png_directory)
    try:
        grab_frames(video_source, interval, png_directory, tif_directory)
    except IOError:
        logging.error('Error reading or writing image frames. Exiting.')
        sys.exit(1)

    logging.info('Decoding meta_data records.')
    try:
        metadata_file = decode_meta_data(klv_file, tif_directory)
    except IOError:
        logging.error('Decoding metadata failed. Exiting.')
        sys.exit(1)

    logging.info('Tagging png frames with id and metadata')
    tag_png_frames(png_directory, metadata_file)

    os.remove(klv_file)

    logging.info('Processing complete.')

if __name__ == '__main__':
    main()
