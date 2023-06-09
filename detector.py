# ALL REQUIRED PACKAGES
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import imutils
import time
import cv2
import os

def detectnpredict_mask(frame, faceNet, maskNet):
	
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (224, 224),
		(104.0, 177.0, 123.0))

	
	faceNet.setInput(blob)
	detections = faceNet.forward()
	print(detections.shape)

	
	faces = []
	locs = []
	predicts = []

	for i in range(0, detections.shape[2]):
		
		confidence = detections[0, 0, i, 2]

		
		if confidence > 0.5:
			
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			
			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			
			face = frame[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (224, 224))
			face = img_to_array(face)
			face = preprocess_input(face)

		
			faces.append(face)
			locs.append((startX, startY, endX, endY))

	
	if len(faces) > 0:
		faces = np.array(faces, dtype="float32")
		predicts = maskNet.predict(faces, batch_size=32)

	
	return (locs, predicts)


prototxt_Path = r"face_detector\deploy.prototxt"
weights_Path = r"face_detector\res10_300x300_ssd_iter_140000.caffemodel"
faceNet = cv2.dnn.readNet(prototxt_Path, weights_Path)


maskNet = load_model("mask__detect.model")


print("STARTING VIDEO STREAM.....")
vs = VideoStream(src=0).start()

# loop 
while True:
	
	frame = vs.read()
	frame = imutils.resize(frame, width=400)

	# detect faces and determine if they are wearing a face mask or not
	(locs, predicts) = detectnpredict_mask(frame, faceNet, maskNet)
	
	for (box, pred) in zip(locs, predicts):
		(startX, startY, endX, endY) = box
		(mask, withoutMask) = pred

		
		label = "Mask" if mask > withoutMask else "No Mask"
		color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

		
		label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)

		
		cv2.putText(frame, label, (startX, startY - 10),
			cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
		cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

	#output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break


cv2.destroyAllWindows()
vs.stop()