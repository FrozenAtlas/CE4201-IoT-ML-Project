# iot lab team 11 opencv face recognition 
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2

# parse inputs
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cascade", required=True,
	help = "path to where the face cascade resides")
ap.add_argument("-e", "--encodings", required=True,
	help="path to serialized db of facial encodings")
args = vars(ap.parse_args())
# load face encoding file
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(args["encodings"], "rb").read())
detector = cv2.CascadeClassifier(args["cascade"])
# turn the usb camera on
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)
fps = FPS().start()
while True:
	# take frame and resize to 500
	frame = vs.read()
	frame = imutils.resize(frame, width=500)
	
	# take frame and make it grayscale and rgb for detection methods
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	# detect faces
	rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
		minNeighbors=5, minSize=(30, 30))
	boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
	# detect the face and check our encodings
	encodings = face_recognition.face_encodings(rgb, boxes)
	names = []
  	# for each detected face check if its recognized
	for encoding in encodings:
		# check the face against our encodings
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
		name = "Unknown"
		if True in matches:
			matchedIdxs = [i for (i, b) in enumerate(matches) if b]
			counts = {}
			# check matched faces and do a counter for votes on which face it is
			for i in matchedIdxs:
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1
			# check over the faces and output the one with most votes
			name = max(counts, key=counts.get)
		
		# update the list of names
		names.append(name)
    # draw the box for faces we recognize
	for ((top, right, bottom, left), name) in zip(boxes, names):
		# draw the rectangle with their name
		cv2.rectangle(frame, (left, top), (right, bottom),
			(0, 255, 0), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
			0.75, (0, 255, 0), 2)
	# display the image to our screen
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break
	fps.update()
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
# cleanup
cv2.destroyAllWindows()
vs.stop()