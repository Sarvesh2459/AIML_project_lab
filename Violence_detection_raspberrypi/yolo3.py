# YOLO object detection
import cv2 as cv
import numpy as np
import time
import torch
import torchvision
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils import data
import PIL
import numpy as np
from torch import nn
from torchinfo import summary
import torch.nn.functional as F
import time
from torch.autograd import Variable
from sklearn.metrics import f1_score
from torcheval.metrics.functional import multiclass_f1_score
from models import NeuralNetwork
# from picamera2 import Picamera2

device = "cuda" if torch.cuda.is_available() else "cpu"

# Grab images as numpy arrays and leave everything else to OpenCV.
cv.startWindowThread()

WHITE = (255, 255, 255)
img = None
img0 = None
outputs = None

# Load names of classes and get random colors
classes = open("coco.names").read().strip().split("\n")
np.random.seed(42)
colors = np.random.randint(0, 255, size=(len(classes), 3), dtype="uint8")

# Give the configuration and weight files for the model and load the network.
net = cv.dnn.readNetFromDarknet("yolov3-tiny.cfg", "yolov3-tiny.weights")
# net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

model = NeuralNetwork().to(device)
model.load_state_dict(torch.load('model_weights.pth'))
model.eval()

# determine the output layer
ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

labels = ['nonviolence', 'violence']

def load_image(image):
    global img, img0, outputs, ln

    img0 = image
    img = img0.copy()

    blob = cv.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    net.setInput(blob)
    t0 = time.time()
    outputs = net.forward(ln)
    t = time.time() - t0

    # combine the 3 output groups into 1 (10647, 85)
    # large objects (507, 85)
    # medium objects (2028, 85)
    # small objects (8112, 85)
    outputs = np.vstack(outputs)

    post_process(img, outputs, 0.5)
    cv.imshow("window", img)
    # cv.displayOverlay("window", f"forward propagation time={t:.3}")
    # cv.waitKey(0)


def post_process(img, outputs, conf):
    H, W = img.shape[:2]

    boxes = []
    confidences = []
    classIDs = []

    for output in outputs:
        scores = output[5:]
        classID = np.argmax(scores)
        confidence = scores[classID]
        if confidence > conf and classes[classID] == "knife" or classes[classID] == "person":
            x, y, w, h = output[:4] * np.array([W, H, W, H])
            p0 = int(x - w // 2), int(y - h // 2)
            p1 = int(x + w // 2), int(y + h // 2)
            boxes.append([*p0, int(w), int(h)])
            confidences.append(float(confidence))
            classIDs.append(classID)
            # cv.rectangle(img, p0, p1, WHITE, 1)

    indices = cv.dnn.NMSBoxes(boxes, confidences, conf, conf - 0.1)
    if len(indices) > 0:
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            color = [int(c) for c in colors[classIDs[i]]]
            cv.rectangle(img, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(classes[classIDs[i]], confidences[i])
            cv.putText(img, text, (x, y - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            # Use model to predict whether is violence or not
            roi = img0[y:y+h, x:x+w]
            roi = cv.resize(roi, (224, 224))
            roi = transforms.ToTensor()(roi).unsqueeze(0).to(device)
            output = model(roi)
            _, predicted = torch.max(output, 1)
            print(labels[predicted.item()]) 




# define a video capture object
vid = cv.VideoCapture("vid.mp4")
## Create an instance of the PiCamera2 object
## Initialize and start realtime video capture
## Set the resolution of the camera preview
# picam2 = Picamera2()
# picam2.configure(
#     picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
# )

# cam = Picamera2()
# cam.preview_configuration.main.size = (640, 360)
# cam.preview_configuration.main.format = "RGB888"
# cam.preview_configuration.controls.FrameRate = 30
# cam.preview_configuration.align()
# cam.configure("preview")
# cam.start()
while True:
    ret, image = vid.read()
    if ret:
        load_image(image)

    # image = cam.capture_array()
    # load_image(image)
    if cv.waitKey(1) & 0xFF == ord("q"):
        break
# cam.stop
vid.release()
cv.destroyAllWindows()
