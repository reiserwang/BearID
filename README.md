BearID
===

Referenced to https://github.com/hypraptive/bearid and create a Dockerfile with OpenCV, dlib, and built binaries. The model referes to [existing DNN dlib model of dog faces](https://github.com/davisking/dlib-models/blob/master/mmod_dog_hipsterizer.dat.bz2). For execution please refre to [README.md](https://github.com/hypraptive/bearid/blob/master/README.md).


#  Research Notes
- https://hypraptive.github.io/2017/01/21/facenet-for-bears.html
-  https://www.researchgate.net/post/Anyone_engaged_in_animal_face_recognition
-  [AI for Earth - Species Classification API backend source](https://github.com/Microsoft/AIforEarth-API-Development)


#  Proposed Workflow
<p><img src="http://bearresearch.org/wp-content/uploads/2018/04/data-flow.png" />


##  Face Detection Algorithms
1. Viola-Jones (decision tree, for very low performance device)
2. Histogram of oriented gradients (HOG) - black and white gradients
3. CNN

##  Reference
https://machinelearningmastery.com/how-to-perform-face-recognition-with-vggface2-convolutional-neural-network-in-keras/
