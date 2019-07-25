BearID
===
To build the UWP BearID App, copy the [ArcFace model](https://s3.amazonaws.com/onnx-model-zoo/arcface/resnet100/resnet100.onnx) to the UWP\BearID folder and rename it to **ArcFace.onnx**

## Architecture

- Capture video / picture from camera
- Get bear face using custom YOLO ONNX model (BearFace.onnx)
- Get bear embedding vector using ArcFace ONNX model (ArcFace.onnx)
- Identify bear using cosine similarity

## Reference
- [ArcFace model](https://github.com/onnx/models/tree/master/vision/body_analysis/arcface)
- [台灣黑熊保育協會｜Taiwan Black Bear Conservation Association (TBBCA)](http://www.taiwanbear.org.tw)
