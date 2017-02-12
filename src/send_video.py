#!/usr/bin/python
#
# python-v4l2capture
#
# This file is an example on how to capture a picture with
# python-v4l2capture.
#
# 2009, 2010 Fredrik Portstrom
#
# I, the copyright holder of this file, hereby release it into the
# public domain. This applies worldwide. In case this is not legally
# possible: I grant anyone the right to use this work for any
# purpose, without any conditions, unless such conditions are
# required by law.
import Image
import select
import v4l2capture
import cv2
import numpy
import time
import grip
import sys
import subprocess
import threading
import Queue
from networktables import NetworkTables

HEIGHT = 360
WIDTH = 640

running = True
#NetworkTables.initialize(server = "10.17.69.69")
sd = NetworkTables.getTable("CameraData")

subprocess.call(['v4l2-ctl','-c', 'exposure_auto=1'])
subprocess.call(['v4l2-ctl','-c', 'exposure_absolute=5'])

def video_proc():
        while running:
            item = video_queue.get()
            video_out.stdin.write( Image.fromarray(item).tobytes() )
            video_queue.task_done()

# Open the video device.
video = v4l2capture.Video_device("/dev/video0")

# Suggest an image size to the device. The device may choose and
# return another size if it doesn't support the suggested one.
size_x, size_y = video.set_format(WIDTH, HEIGHT)

# Create a buffer to store image data in. This must be done before
# calling 'start' if v4l2capture is compiled with libv4l2. Otherwise
# raises IOError.
video.create_buffers(30)

# Send the buffer to the device. Some devices require this to be done
# before calling 'start'.
video.queue_all_buffers()

# Start the device. This lights the LED if it's a camera that has one.
video.start()

gp = grip.GripPipeline(WIDTH, HEIGHT)
#print "starting"

video_out = subprocess.Popen(['./fdsrcrtsp.py'], stdin = subprocess.PIPE)

video_queue = Queue.Queue(maxsize = 5)

thd = threading.Thread(target = video_proc)
thd.start()

try:
    while True:
	# Wait for the device to fill the buffer.
	select.select((video,), (), ())

	# The rest is easy :-)
	image_data = video.read_and_queue()

	image = Image.frombytes("RGB", (size_x, size_y), image_data, "raw", "BGR")

	im_array = numpy.array(image)

	res = gp.process(im_array)

        if not video_queue.full():
	    video_queue.put(res[0])
	    
        point_data = res[1]
        print "["
            
        sd.putNumber('x', point_data[0])
        sd.putNumber('y', point_data[1])
        sd.putNumber('size', point_data[2])
        sd.putNumber('count', point_data[3])
            
        print "]"

        #cv2.imshow('video', im_array)	
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
except KeyboardInterrupt:
    print "ending1"
    running = False
    video_out.kill()
    video_queue.put("")

video.close()
#image.save("image.jpg")
#print "Saved image.jpg (Size: " + str(size_x) + " x " + str(size_y) + ")"
