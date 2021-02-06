#!/usr/bin/python3
""" Utility program to transfer mission data to an AWS bucket as long as we have been
    supplied with the proper keys.
"""
import os
import configparser
import argparse
import boto3
from botocore.exceptions import NoCredentialsError

OUTBOUND = 'Processed'

def upload_to_aws(local_file, bucket, s3_file, access_key, secret_key):
    """ Upload a file to AWS S3 bucket """
    s3 = boto3.client('s3', aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
    
    try:
        s3.upload_file(local_file, bucket, s3_file)
        print(f'Upload of {local_file} to {bucket} as {s3_file} successful.')
        return True
    except FileNotFoundError:
        print(f'File {local_file} not found.')
        return False
    except NoCredentialsError:
        print('Credentials invalid or not available.')
        return False

def get_target_list(data_dir):
    """ Get a list of files to be sent to AWS """
    target_list = os.listdir(data_dir)

    return target_list

def main():
    """ Driver for transfer process """
    arg_parser = argparse.ArgumentParser(description='Transfer data files to AWS S3 bucket.')
    arg_parser.add_argument('mission', action='store', help='Mission data to be transferred.')
    arg_parser.add_argument('target', action='store', help='Which AWS account to receive data.')
    args = arg_parser.parse_args()
    mission = args.mission
    target = args.target.upper()

    config = configparser.ConfigParser()
    config.read('aws.ini')
    bucket = config[target]['bucket']
    access_key_id = config[target]['access_key']
    secret_key_id = config[target]['secret_key']

    source_dir = os.path.join(OUTBOUND, mission)
    dir_list = get_target_list(source_dir)
    for directory in dir_list:
        if directory.endswith('_TIF'):
            file_dir = os.path.join(source_dir, directory)
            files = get_target_list(file_dir)
            for file in files:
                upload_to_aws(file_dir + file, bucket, mission + f'/{directory}/{file}',
                              access_key_id, secret_key_id)

if __name__ == '__main__':
    main()
