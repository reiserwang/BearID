BearID
===

#  Research Notes
- https://hypraptive.github.io/2017/01/21/facenet-for-bears.html
-  https://www.researchgate.net/post/Anyone_engaged_in_animal_face_recognition
-  [AI for Earth - Species Classification API backend source](https://github.com/Microsoft/AIforEarth-API-Development)
#  Project URL
-  [GitHub](https://github.com/reiserwang/BearID.git)
-  [Onedrive with photos from TBBCA](https://onedrive.live.com/?authkey=%21AGSPL7g4tPcfiNE&id=64764C69DDC0124C%21451761&cid=64764C69DDC0124C) (confidential)

#  Proposed Workflow
1. Collect bear face photos
2. Train face detection labeled with [VoTT](https://github.com/microsoft/VoTT)
3. Encode/train faces Faster R-CNN or [FaceNet](https://github.com/davidsandberg/facenet)
4. Match the faces

##  Face Detection Algorithms
1. Viola-Jones (decision tree, for very low performance device)
2. Histogram of oriented gradients (HOG) - black and white gradients
3. CNN

##  Reference
https://machinelearningmastery.com/how-to-perform-face-recognition-with-vggface2-convolutional-neural-network-in-keras/
