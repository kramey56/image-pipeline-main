# Imaging Pipeline

This directory holds all the code for the imaging pipeline developed by Ken Ramey,
originally as part of the commercialization of the Gryphon platform with a Hoodtech
Alticam 14 camera payload capable of imaging in visible, SWIR, and MWIR spectrum ranges.

There are several components to the pipeline. They are written as separate modules so
that they can be used or not, depending on the requirements. The modules are:

- process_video.py
- send_to_azure.py
- send_to_aws.py
- sharpen.py
- contrast_enhance.py
- monitor.py

In addition, there are two configuration files that set the operating parameters for
some of the modules. They are:

- aws.ini
- pipeline.ini

## Requirements

This package is written to run under Python >= 3.6. In addition there are several packages
that must be installed. All required packages are documented in "requirements.txt". Using
pip, all packages can be installed with a single command. If only Python3 is installed the
command is `pip -r requirements.txt`. If both Python2 and Python3 are installed, you will
probably need to use the command `pip3 -r requirements.txt`. When the command completes all
packages needed by the pipeline will be installed and available to Python programs.

## Modules

Each section below describes a module of the imaging pipeline system and how they work together
to process video from the Alticam 14.

### process_video.py

This is the workhorse of the imaging pipeline. It can be run from the command line or can be 
triggered to run automatically based on a new file being created in the mission subdirectory
of the "incoming" directory.

If run from the command line the program takes a single argument, the name of the video file
to process. All other parameters are given in the "pipeline.ini" file. One parameter of
special interest is the `log-level` parameter. It is usually set to "ERROR", meaning that
only log messages generated as a result of execution errors will be written to the program
log file. It the `log-level` is set to "DEBUG", more data will be written to the log, including
status messages, execution traces, and messages to verify the names of files processed and
generated.

`./process_video.py ./incoming/GF21/AC14_Sample.ts`

That will initiate the processing steps:

1. Extract KLV data from the H.264 video as a separate digital file with the extension .klv.
This is done by invoking `ffmpeg` with the appropriate arguments. The process runs at the maximum
speed the processor is capable of, so the extraction is very fast. On the order of a few seconds
for a five minute long video clip. The name of the output file produced is the same as the name
of the input video file, with the .ts extension replaced with .klv.

2. OpenCV is then used to extract frames from the video at a frame interval specified by a value
in the configuration file, "pipeline.ini". Currently that value is set to 1, indicating that a
frame is extracted every second. Setting it to 60 would extract one frame for each minute of
video. The images extracted are stored in directories named after the original video file, with
the .ts extension stripped off and an suffix added of `_TIF` and `_PNG`. The frames are named
frame_ccccc.png or frame_ccccc.tif, where ccccc is replaced with the frame number.

3. The .klv file produced in step 1 is decoded into a human-readable JSON file. While the image
frames were extracted at a specified frame rate, all KLV frames are processed and tagged with
a frame number so that they can be related to the image frames extracted in step 2. The generated
JSON file is saved in the TIF directory and is also named after the input video file with an
extension of .json.

4. Each of the PNG image files has metadata added from the JSON file. Each image has a dictionary
added that specifies the longitude, latitude, and altitude of the target image as well as information
about the course and heading of the Stratolyte from which the images were captured. At the same
time a KLM file is produced that allows the image location to be mapped on Google Earth or other
mapping tools.

5. As a cleanup step, the binary .klv file produced in step one is deleted. If it is ever needed, it
can be recreated easily by rerunning this process against the original video file.

**Caveats:** The AC14 camera provides GPS coordinates for the center of the image frame. However,
Hoodtech has informed us that the camera has an inherent +/- .3 degree pointing error. This means the
AC14 data cannot be relied on for any kind of GIS application. The only way past this obstacle would
be to implement an algorithm that matches the actual image with a digital map in order to get the
correct placement and orientation of the image. There have been a few papers published in the last few
years on how to do this. They are very complex and data intensive but could be done with the proper
dedication of time and resources.

### monitor.py

This is a small utility that will monitor a directory and trigger some action when a new file
is created in the target directory or one of its subdirectories. It is currently configured to watch
the "incoming" directory, in whch subdirectories will be created for each Gryphon mission. Whenever
a video file - with the extension .ts - is created in one of the subdirectoris, it invokes 
`process_video.py` passing it the fully qualified path and name of the newly created file. The processing
described above will then be performed and the data produced will be stored in the appropriate 
subdirectories of the "processed" directory.

monitor.py can be run as a daemon, in which case it would need to be terminated with the `kill` command, or it
can be run in a dedicated command window and killed by `<CTL>-c`.

### send_to_azure.py

This utility is used to send all data produced by Gryphon imaging to World View's Azure account for archival
storage in BLOB containers. The connection string and container information are contained within the source
code since it is intended to send data only to World View's account. If it is expanded to send data to other
accounts, I recommend a configuration file so that it can easily be pointed at different containers.

### send_to_aws.py

Most of our partners at the time of this writing use AWS for cloud storage. This utility was written to send
data to various AWS accounts. All information needed to connect to these accounts is stored in "aws.ini", with
a group heading for each account to which data may be directed. 

This utility takes two command line arguments:

`./send_to_aws.py mission target`

The "mission" argument specifies which subdirectory of the "processed" directory is to be transferred to AWS. 
The "target" argument chosses which AWS account is to receive the data.

**WARNING** This function has not been thoroughly tested. It took some time to get the necessary credentials
on the World View AWS account. However, Roderick did get them and I was able to run this script to transfer
some test files and Roderick was able to verify that they were properly transferred to the AWS storage.

### contrast_enhance.py

This was one of the first programs written to enhance the images themselves. This utility uses a Contrast
Limited Adaptive Histogram Enhancement (CLAHE) algorithm to improve image contrast. It also prints a measure
of image contrast before and after enhancement.

In testing this program was found to be of little value to IR images. Overall, these images are pretty flat
and enhancing contrast tended to wash out what few details were visible. This program will probably be more 
useful on EO images.

Syntax for execution:

`./contrast_enhance.py source dest --limit 3.0 --log-level ERROR`

The "source" and "dest" arguments are mandatory and specify the name of the file to be sharpened and the name
to which the file should be written after sharpening. The "limit" parameter controls how much sharpening
is applied to the image. The default level is 3.0, which is a good starting point. You may want to experiment
with higher or lower levels of enhancement on different images. The "log-level" parameter is also optional 
and takes any of the python logging package debug levels. If thie argument is omitted, logging defaults 
to "ERROR".

### sharpen.py

This program improves sharpness of images by identifying and sharpening edges rather than applying an image-wide
sharpening. It also measures Laplacian sharpness of the image both before and after sharpening.

As with the contrast enhancing utility, this was found to be mostly ineffective on IR images. It will also
probably be more useful on EO images.

Syntax for execution:

`./sharpen.py source dest --log-level ERROR`

The "source" and "dest" arguments are mandatory and specify the name of the file to be sharpened and the name
to which the file should be written after sharpening. The "log-level" parameter is optional and takes any of the 
python logging package debug levels. If thie argument is omitted, logging defaults to "ERROR".
