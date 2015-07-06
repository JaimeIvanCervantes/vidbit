import cv2
import h5py
import sys
import numpy as np
import os
import math

import ufmf

AXISTAGS = '{\n  "axes": [\n    {\n      "key": "t",\n      "typeFlags": 8,\n      "resolution": 0,\n      "description": ""\n    },\n    {\n      "key": "y",\n      "typeFlags": 2,\n      "resolution": 0,\n      "description": ""\n    },\n    {\n      "key": "x",\n      "typeFlags": 2,\n      "resolution": 0,\n      "description": ""\n    },\n    {\n      "key": "c",\n      "typeFlags": 1,\n      "resolution": 0,\n      "description": ""\n    }\n  ]\n}'

def main(fileName, outFileName, frameMax, scale, sampled):
	# Get name and extension
	name, extension = os.path.splitext(fileName)

	# Detect file extension and decide if video to hdf5, or hdf5 to video.
	videoFileName = None
	if extension == '.h5' :
		videoFileName = name + '.avi'
		h5FileName = fileName
	elif extension == '.ufmf' :
		print "Processing ufmf file"
		
		videoFileName = fileName
		if outFileName == '' :
			h5FileName = name + '.h5'
		else :
			h5FileName = outFileName
		
		fmf = ufmf.FlyMovieEmulator(videoFileName)
		
		frameNum = fmf.get_n_frames()
		frameStep = int( math.ceil(frameNum/(frameMax-1) ) )
		width = fmf.get_width()
		height = fmf.get_height()
			 
		# Open h5 file and initalize dataset
		h5File = h5py.File(h5FileName,'w')
		dataset = h5File.create_dataset("data", (1,height,width,1) , maxshape=(None, height, width, 1), chunks=(1, height, width, 1) )
		dataset.attrs['axistags'] = AXISTAGS
		
	 	frameSavedCount = 0
	 	frameCount = 0
	 
		while frameCount < frameNum and (frameCount < frameMax or frameMax == 0 or sampled == 1) :
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
		#cv2.destroyAllWindows()
 
	elif extension == '.avi' :
		videoFileName = fileName
		h5FileName = name + '.h5'

		# Capture video (requires ffmpeg and cv2 installed)
		cap = cv2.VideoCapture(videoFileName)
		
		# Read first frame for memory pre-allocation and exceptions
		ret, frame = cap.read()
		if (ret == False) :
			print "Error reading .avi video file."
			exit(1)
					
		# Resize and invert color channel order in order to be compatible with ilastik
		frame = cv2.resize(frame, None, fx=scale, fy=scale)
		frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)	
		
		# Open h5 file and initalize dataset
		h5File = h5py.File(h5FileName,'w')
		dataset = h5File.create_dataset("data", (1,)+frame.shape, maxshape=(None,)+frame.shape)
		dataset[0,:,:,:] = frame
		
		# Loop through each frame
		frameCount = 1
		while(cap.isOpened() and (frameCount < frameMax or frameMax == 0) ):
			# Read frame
			ret, frame = cap.read()
			
			# Resize and invert color channel order in order to be compatible with ilastik
			frame = cv2.resize(frame, None, fx=scale, fy=scale) 
			frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)	
			
			dataset.resize((frameCount+1,) + frame.shape)
			dataset[frameCount,:,:,:] = frame
					
			#cv2.imshow('Frame', frame)
			#if cv2.waitKey(1) & 0xFF == ord('q'):
			#	break
	
			frameCount += 1
	
		# Close, deallocate and release	
		h5File.close()
		cap.release()
		#cv2.destroyAllWindows()

	print "Done"

if __name__ == "__main__":
    
    #sys.argv.append('/opt/local/primoz/CantonS_decap_dust_3_2.avi')
	#sys.argv.append('/groups/branson/home/cervantesj/public/KristinTrackingTestData/Alice/FCF_pBDPGAL4U_1500437_TrpA_Rig2Plate17BowlD_20121121T152832/movie.ufmf')
	#sys.argv.append('/groups/branson/home/cervantesj/public/KristinTrackingTestData/Alice/Courtship_Bowls/shelbyCSMH_25C_Rig1BowlA_20141111T143505/movie.ufmf')
	#sys.argv.append('/groups/branson/home/cervantesj/public/JaimeProfiling/Alice/movie.h5')
	#sys.argv.append('10')
	#sys.argv.append('1.0')
	#sys.argv.append('1')
    	 
	if len(sys.argv[1:]) < 1:
		print "Usage: {} <video-file> <out-file> <number-of-frames> <scale> <sampled-equally-spaced>".format( sys.argv[0] )
		sys.exit(1)
	elif len(sys.argv[1:]) == 1:
		sys.argv.append('')
		sys.argv.append('0')
		sys.argv.append('1.0')
		sys.argv.append('0')
	elif len(sys.argv[1:]) == 2:
		sys.argv.append('0')
		sys.argv.append('1.0')
		sys.argv.append('0')
	elif len(sys.argv[1:]) == 3:
		sys.argv.append('1.0')
		sys.argv.append('0')
	elif len(sys.argv[1:]) == 4:
		sys.argv.append('0')
	
	main( sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]) )

