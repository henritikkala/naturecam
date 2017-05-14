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
	print "Press 'q' when want to quit."
	
	# Set time counter for still-image interval
	end = time.time()
	start = end #end - 57
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
		if i > 0 and framenum > 2 and delta > 10:
			#print("Frame number: " + repr(framenum))
			#print("Contours: " + repr(i))
			fname = "smthng-" + str(timestamp.strftime("%Y_%m_%d_%H:%M")) + ".jpg"
			cv2.imwrite(fname, frame)
			start = time.time()
			frames = 0
			print "Image saved..."
			# If Internet is online
			if internet() == True:
				pydrive_upload(fname)
			
		end = time.time()
		delta = end - start
		if (frames > 10 and frames/delta >5):
			print "%.0f " % (frames/delta) + " frames/s"
		#print delta
		
	print "Program shutting down..."
	camera.release()
	cv2.destroyAllWindows()
	
	#return fname
	
NatureCam(200)
