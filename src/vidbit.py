import cv2
import h5py
import sys
import numpy as np
import os

import ufmf

def main(fileName, frameMax, scale):

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
		h5FileName = name + '.h5'
		
		fmf = ufmf.FlyMovieEmulator(videoFileName)
			
		width = fmf.get_width()
		height = fmf.get_height()
	 
		# Open h5 file and initalize dataset
		h5File = h5py.File("/opt/local/kristin/buffer.h5",'w')
		dataset = h5File.create_dataset("data", (1,width,height,1) , maxshape=(None,width,height,1) )
	 
	 	frameCount = 0
	 
		while frameCount < frameMax or frameMax == 0 :
			try:
				frame,timestamp = fmf.get_next_frame()
			except FMF.NoMoreFramesException, err:
				break
			
			dataset.resize( (frameCount+1,) + (width,height,1) )
			dataset[frameCount,:,:,:] = frame[:,:,None]
			
			frameCount += 1
			
		# Close, deallocate and release	
		h5File.close()
		cv2.destroyAllWindows()
 
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
					
			cv2.imshow('Frame', frame)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
	
			frameCount += 1
	
		# Close, deallocate and release	
		h5File.close()
		cap.release()
		cv2.destroyAllWindows()

if __name__ == "__main__":
    
	sys.argv.append('/groups/branson/home/cervantesj/public/KristinTrackingTestData/Alice/Fly_Bowl/GMR_71G01_AE_01_TrpA_Rig2Plate14BowlC_20110707T154934/movie.ufmf')
	#sys.argv.append('/opt/local/primoz/CantonS_decap_dust_3_2.avi')
	sys.argv.append('10')
	sys.argv.append('0.2')
    	 
	if len(sys.argv[1:]) < 1:
		print "Usage: {} <video/HDF5-file> <file-type> <number-of-frames> <scale>".format( sys.argv[0] )
		sys.exit(1)
	elif len(sys.argv[1:]) == 1:
		sys.argv.append('0')
		sys.argv.append('1.0')
	elif len(sys.argv[1:]) == 2:
		sys.argv.append('1.0')
	
	main( sys.argv[1], int(sys.argv[2]), float(sys.argv[3]) )

