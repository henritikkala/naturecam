# -*- coding: UTF-8 -*-
'''
	Author: Henri Tikkala - tikkala.henri@gmail.com
'''
#  Libraries
import argparse
import datetime
import time
import cv2
import numpy as np
import os
import shutil
import threading
from mountusb import mount, unmount, get_media_path
from mountusb import list_media_devices
from upload import pydrive_upload
from isinternet import internet

def NatureCam(minA):

	# Arguments(if use stream or video file)
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video", help="path to the video file")
	args = vars(ap.parse_args())

	# Initialize parameters:
	framenum = 5
	frames = 0
	i=0
	kernel = np.ones((5,5),np.uint8)
	min_area = minA
	fgbg = cv2.createBackgroundSubtractorMOG2()
	devices = list_media_devices()
	pathusb = ''
	print "Press 'q' when want to quit."

	# Mount all usb devices(usb stick with raspi) and get mount path
	for device in devices:
		mount(device)
		pathusb = get_media_path(device)
		#print pathusb
	if len(pathusb) > 0:
		pathusb = os.path.join(pathusb, 'NatureCam_pics')
	else:
		pathusb = os.path.join('/home/$USER', 'NatureCam_pics')
	if not os.path.isdir(pathusb):
		os.makedirs(pathusb)
		print "Created directory: " +pathusb
	#print pathusb
	
	# Set time counter for still-image interval
	end = time.time()
	start = end - 25
	delta = 0

	# Is it stream...
	if args.get("video", None) is None:
		print "Initializing camera..."
		camera = cv2.VideoCapture(0)
		camera.set(3,640)
		camera.set(4,480)
		print "Camera max framerate " + repr(camera.get(cv2.CAP_PROP_FPS))
		# Sleep for skipping first frames
		time.sleep(3)

	# ...or file?
	else:
		print "Loading video..."
		camera = cv2.VideoCapture(args["video"])

	while (1):
		
		# Load single frame from camera
		(grapped, frame) = camera.read()
		if not grapped:
			break
		timestamp = datetime.datetime.now()
		text = "No motion"
		i = 0
		frames += 1


		# Handle background movements or noise, and find contours
		fgmask = fgbg.apply(frame)
		thresh = cv2.threshold(fgmask, 100, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
		thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
		(image, contours, hierarchy) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# Loop over the contours
		for c in contours:
			
			# Discard too small contour-areas
			if cv2.contourArea(c) > min_area:
				i = i+1
				text = "Motion detected"
				epsilon = 0.02*cv2.arcLength(c,True)
				approx = cv2.approxPolyDP(c,epsilon,True)
				#cv2.drawContours (frame, [approx],  -1, (0, 255, 0), 2)	
				# compute the bounding box for the contour, draw it on the frame, and update the text
				(x, y, w, h) = cv2.boundingRect(approx)
				cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
				framenum += 1
			else:
				framenum = 0

		# Show stream and retangles around chosen contours
		ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
		cv2.putText(frame, "Status: {}".format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
		cv2.imshow("NatureCam", frame)

		# Press q to stop program
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			break		

		#print("Frame number: " + repr(framenum))
		#print("Contours: " + repr(i))	
		
		# Save image with timestamp
		if i > 0 and framenum > 2 and delta > 30:
			#print("Frame number: " + repr(framenum))
			#print("Contours: " + repr(i))
			tmp = 'NC-' + str(timestamp.strftime('%Y_%m_%d_%H_%M')) + '.jpg'
			fname2 = os.path.join(pathusb, tmp)
			cv2.imwrite(tmp, frame)
			start = time.time()
			frames = 0
			# If Internet is online
			#shutil.move(tmp, fname2)
			if internet() == True:
				t = threading.Thread(target=pydrive_upload, args=(tmp,))
				t.start()
			else:
				shutil.move(tmp, fname2)
				print "Image saved in "+fname2
			
		end = time.time()
		delta = end - start
		#if (frames > 10 and frames/delta >5):
		#	print "%.0f " % (frames/delta) + " frames/s"
		#print delta
		
	print "Program shutting down..."
	camera.release()
	cv2.destroyAllWindows()
	unmount(device)
	
	
NatureCam(200)
