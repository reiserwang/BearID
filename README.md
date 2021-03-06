BearID
===
To build the UWP BearID App, copy the [ArcFace model](https://s3.amazonaws.com/onnx-model-zoo/arcface/resnet100/resnet100.onnx) to the UWP\BearID folder and rename it to **ArcFace.onnx**

## Architecture

- Capture video / picture from camera
- Get bear face using custom YOLO ONNX model ([BearFace.onnx](https://github.com/reiserwang/BearID/blob/master/UWP/BearID/BearFace.onnx))
- Get bear embedding vector using [ArcFace](https://arxiv.org/abs/1801.07698) ONNX model (ArcFace.onnx)
- Identify bear using cosine similarity

## Code Structure
- UWP/          Implementations based on aboce architecture, contributed by Tony.
- bearid_dlib/  *Deprecated codes based on https://github.com/hypraptive/bearid*
- Dockerfile    *Deprecated.* Dockerfile for bearid_dlib.

## Reference
- [ArcFace model](https://github.com/onnx/models/tree/master/vision/body_analysis/arcface)
- [台灣黑熊保育協會｜Taiwan Black Bear Conservation Association (TBBCA)](http://www.taiwanbear.org.tw)
