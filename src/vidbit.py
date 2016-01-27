import cv2
import h5py
import sys
import numpy as np
import os
import math
import argparse
import ufmf
import MmfParser

AXISTAGS = '{\n  "axes": [\n    {\n      "key": "t",\n      "typeFlags": 8,\n      "resolution": 0,\n      "description": ""\n    },\n    {\n      "key": "y",\n      "typeFlags": 2,\n      "resolution": 0,\n      "description": ""\n    },\n    {\n      "key": "x",\n      "typeFlags": 2,\n      "resolution": 0,\n      "description": ""\n    },\n    {\n      "key": "c",\n      "typeFlags": 1,\n      "resolution": 0,\n      "description": ""\n    }\n  ]\n}'

def main(parsedArgs) :
	# Get arguments
	inFileName = parsedArgs.input_file
	outFileName = parsedArgs.output_file
	frameMax = parsedArgs.frames
	scale = parsedArgs.scale
	sampled = parsedArgs.spaced
	
	# Get name and extension
	name, extension = os.path.splitext(inFileName)

	# Detect file extension and decide if video to hdf5, or hdf5 to video.
	if extension == '.h5':
		if not outFileName:
			outFileName = name + '.avi'
			
		inFile = h5py.File(inFileName,'r')
		keys = inFile.keys()
		dset = inFile[keys[0]] # Get first dataset (usually data or exported_data)
		
		frameNum = dset.shape[0]
		channelNum = dset.shape[3]
		
		assert channelNum == 1, "Number of channels is more than 1 (greyscale video is required)"
		
		norm = 255/20
		
		fourcc = cv2.cv.CV_FOURCC(*'XVID')
		out = cv2.VideoWriter(outFileName,fourcc, 25.0, (dset.shape[1],dset.shape[2]))

		for i in range(frameNum):
			grayFrame = (dset[i,:,:,:,0] * norm)
			grayFrame = grayFrame.astype(np.uint8)
 			colorFrame = cv2.applyColorMap(grayFrame, cv2.COLORMAP_JET)
 		 	out.write(colorFrame)	
			# cv2.imwrite(name + '.jpg', colorFrame)
			
		out.release()
		
	elif extension == '.mmf':	
		print "Processing mmf file"
		
		if outFileName:
			h5FileName = name + '.h5'
		else :
			h5FileName = outFileName
			
		mmf = MmfParser.MmfParser(inFileName)
		
		frameNum = mmf.getNumberOfFrames()
		
		frame = mmf.getFrame(0)
		width = frame.shape[0]
		height = frame.shape[1]
		channels = 1
		
		# Open h5 file and initalize dataset
		h5File = h5py.File(h5FileName,'w')
		dataset = h5File.create_dataset("data", (1,height,width,channels) , maxshape=(None, height, width, channels), chunks=(1, height, width, channels), dtype='uint8')
		dataset.attrs['axistags'] = AXISTAGS

	 	frameSavedCount = 0
	 	frameCount = 0
	 
		while frameCount < frameNum and (frameCount < frameMax or frameMax == 0 or sampled == 1):
			frame = mmf.getFrame(frameCount)

			if sampled == 0 or frameCount % frameStep == 0:
				print "Saving frame: ", frameCount
				dataset.resize( (frameSavedCount+1,) + (height,width,1) )
				dataset[frameSavedCount,:,:,:] = frame[:,:,None]
				frameSavedCount += 1
			
		 	frameCount += 1		
		
		h5File.close()
		mmf.close()
		
	elif extension == '.ufmf':
		print "Processing ufmf file"
		
		if outFileName == '':
			h5FileName = name + '.h5'
		else :
			h5FileName = outFileName
		
		fmf = ufmf.FlyMovieEmulator(inFileName)
		
		# Get video parameters
		frameNum = fmf.get_n_frames()
		frameStep = int( math.ceil(frameNum/(frameMax-1) ) )
		width = fmf.get_width()
		height = fmf.get_height()
		channels = 1
			 
		# Open h5 file and initalize dataset
		h5File = h5py.File(h5FileName,'w')
		dataset = h5File.create_dataset("data", (1,height,width,channels) , maxshape=(None, height, width, channels), chunks=(1, height, width, channels), dtype='uint8')
		dataset.attrs['axistags'] = AXISTAGS
		
	 	frameSavedCount = 0
	 	frameCount = 0
	 
		while frameCount < frameNum and (frameCount < frameMax or frameMax == 0 or sampled == 1):
			try:
				frame,timestamp = fmf.get_next_frame()
			except FMF.NoMoreFramesException, err:
				break
									
			if sampled == 0 or frameCount % frameStep == 0:
				print "Saving frame: ", frameCount
				dataset.resize( (frameSavedCount+1,) + (height,width,1) )
				dataset[frameSavedCount,:,:,:] = frame[:,:,None]
				frameSavedCount += 1

			frameCount += 1	
			
		# Close, deallocate and release	
		h5File.close()
		fmf.close()
		#cv2.destroyAllWindows()
 
	elif extension == '.avi' or extension == '.mov':
		if outFileName == '':
			h5FileName = name + '.h5'
		else :
			h5FileName = outFileName

		# Capture video (requires ffmpeg and cv2 installed)
		cap = cv2.VideoCapture(inFileName)
		
		# Read first frame for memory pre-allocation and exceptions
		'''
		ret, frame = cap.read()
		if (ret == False) :
			print "Error reading .avi/.mov video file."
			exit(1)
		'''
					
		# Resize and invert color channel order in order to be compatible with ilastik
		# frame = cv2.resize(frame, None, fx=scale, fy=scale)
		#frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)	

		# Get video parameters
		frameNum = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
		frameStep = int( math.ceil(frameNum/(frameMax-1) ) )
		width = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
		height = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
		channels = 1
	
		# Open h5 file and initialize dataset
		h5File = h5py.File(h5FileName,'w')
		dataset = h5File.create_dataset("data", (1, height, width, channels) , maxshape=(None, height, width, channels), chunks=(1, height, width, channels), dtype='uint8')
		dataset.attrs['axistags'] = AXISTAGS
		#dataset = h5File.create_dataset("data", (1,)+frame.shape, maxshape=(None,)+frame.shape)
		#dataset[0,:,:,:] = frame
		
		# Loop through each frame
	 	frameSavedCount = 0
	 	frameCount = 0
		while(frameCount < frameNum and (frameCount < frameMax or frameMax == 0 or sampled == 1) ):
			# Read frame
			ret, frame = cap.read()
			
			if (ret == False and cap.isOpened() ) :
				break
			
			# Resize and invert color channel order in order to be compatible with ilastik
			# frame = cv2.resize(frame, None, fx=scale, fy=scale) 
			frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)	
			frame = frame[:,:,None]
			
			if sampled == 0 or frameCount % frameStep == 0:
				print "Saving frame: ", frameCount
				dataset.resize((frameSavedCount+1,) + frame.shape)
				dataset[frameSavedCount,:,:,:] = frame
				frameSavedCount += 1
	
			frameCount += 1
	
		# Close, deallocate and release	
		h5File.close()
		cap.release()
		#cv2.destroyAllWindows()

	print "Done"

if __name__ == "__main__":

	parser = argparse.ArgumentParser( description="Export video to HDF5 format." )
	
	parser.add_argument('--input-file', help='Name of video file to process.', required=True)
	parser.add_argument('--output-file', help='Name of output HDF5 file.', default = '')
	parser.add_argument('--scale', help='Scale the width and height of each frame.', default=1.0, type=float)
	parser.add_argument('--frames', help='Maximum number of frames.', default=0, type=int)
	parser.add_argument('--spaced', help='Sample at equally spaced intervals.', default=1, type=int)
	
	parsedArgs, workflowCmdlineArgs = parser.parse_known_args()
	
	main(parsedArgs)

