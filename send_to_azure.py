#!/usr/bin/python3
"""
Bulk upload files to Azure BLOB storage. This will be used for archival
storage of video and processed image files from Gryphon flights
"""

import os
import configparser
import logging
from multiprocessing.pool import ThreadPool
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContentSettings

INCOMING = 'incoming'
OUTGOING = 'pipeline'
CONNECT_STR = r'DefaultEndpointsProtocol=https;AccountName=proto;'\
              r'AccountKey=dZCJF1UFuiyNlD5Rc/hmz0jJWUd7XWfV75MGTqUwJ0kWK/jj6H6/KM8XZlSB9ZhcK'\
              r'+IBonnq29TB+0YirFC3uQ==;EndpointSuffix=core.windows.net'

class AzureBlobFileUploader:
    """ Class to handle parallel upload of image files to Azure BLOB storage """
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(CONNECT_STR)
        self.mime_types = {'.ts': 'video/mp2t', '.tif': 'image/tiff',
                           '.png': 'image/png', '.json': 'application/json',
                           '.kml': 'application/vnd'}

    def upload_all_images_in_folder(self, source_folder):
        """ Get a list of files to be uploaded and call upload function """
        all_file_names = [os.path.join(source_folder, f) for f in os.listdir(source_folder)]
        result = self.run(all_file_names)

        logging.info(result)

    def run(self, file_list):
        """ Upload up to 10 files at one time """
        with ThreadPool(processes=int(10)) as pool:
            return pool.map(self.upload_image, file_list)

    def upload_image(self, file_name):
        """ Upload one file to Azure, maintaining source file name """
        blob_client = self.blob_service_client.get_blob_client(container=OUTGOING, blob=file_name)
        _, ext = os.path.splitext(file_name)
        mime_type = self.mime_types[ext]
        image_content_setting = ContentSettings(content_type=mime_type)
        with open(file_name, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True, content_settings=image_content_setting)
        return file_name

def get_target_list(incoming_dir, select):
    """ Get a list of files to be processed """
    logging.debug('Processing directory %s', incoming_dir)
    target_list = [f for f in os.listdir(incoming_dir) if f.endswith(select)]

    return target_list

def main():
    """ Driver for processes that copy files to Azure Blob storage """
    config = configparser.ConfigParser()
    config.read('pipeline.ini')
    mission = config['GENERAL']['mission']
    loglevel = config['GENERAL']['logLevel']
    if loglevel is not None:
        numeric_level = getattr(logging, loglevel.upper(), None)
    else:
        numeric_level = logging.ERROR

    logging.basicConfig(filename='azure_blob.log', format='%(asctime)s: %(levelname)s %(message)s',
                        level=numeric_level)

    out_dir = os.path.join('processed', mission)
    tif_dirs = get_target_list(out_dir, '_TIF')
    png_dirs = get_target_list(out_dir, '_PNG')

    # Create uploader
    file_uploader = AzureBlobFileUploader()

    # Upload source video
    logging.info('Uploading source video.')
    file_uploader.upload_all_images_in_folder(os.path.join(INCOMING, mission))

    # Upload tif files
    logging.info('Uploading tif files.')
    for tif_dir in tif_dirs:
        file_uploader.upload_all_images_in_folder(os.path.join('processed', mission, tif_dir))

    # Upload png files
    logging.info('Uploading png files.')
    for png_dir in png_dirs:
        file_uploader.upload_all_images_in_folder(os.path.join('processed', mission, png_dir))

if __name__ == '__main__':
    main()
