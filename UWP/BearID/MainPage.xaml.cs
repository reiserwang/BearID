using Microsoft.Toolkit.Uwp.Helpers;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Threading;
using System.Threading.Tasks;
using Windows.AI.MachineLearning;
using Windows.Foundation;
using Windows.Graphics.Imaging;
using Windows.Media;
using Windows.Storage;
using Windows.Storage.Streams;
using Windows.UI.Core;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.UI.Xaml.Media;
using Windows.UI.Xaml.Shapes;

// The Blank Page item template is documented at https://go.microsoft.com/fwlink/?LinkId=402352&clcid=0x409

// 1. Capture video / picture from camera
// 2. Get bear face using custom YOLO ONNX model (BearFace.onnx)
// 3. Get bear embedding vector using ArcFace ONNX model (ArcFace.onnx)
// 4. Identify bear using cosine similarity

namespace BearID
{
    public sealed class ImageFile
    {
        public string DisplayName { get; set; }
        public string Path { get; set; }
        public List<float> Embedding { get; set; }

        public ImageFile()
        {
        }

        public ImageFile(string displayName, string path, List<float> embedding)
        {
            DisplayName = displayName;
            Path = path;
            Embedding = embedding;
        }
    }

    /// <summary>
    /// An empty page that can be used on its own or navigated to within a Frame.
    /// </summary>
    public sealed partial class MainPage : Page
    {
        private const int ARC_FACE_INPUT = 112;
        private const int YOLO_INPUT = 416;
        private const double MIN_SIZE = 0.05;
        private const double MIN_SIMILARITY = 0.68;

        private ArcFaceModel _arcFaceModel;
        private ArcFaceInput _arcFaceInput = new ArcFaceInput();
        private ArcFaceOutput _arcFaceOutput = new ArcFaceOutput();
        private ObjectDetection objectDetection = new ObjectDetection(new List<string>() { "Face" });
        private List<string> bearList = new List<string>() { "Bingo", "Happy", "Pobi", "南安", "長治" };
        private bool _ready = false;
        private SoftwareBitmap _softwareBitmapFace;

        public MainPage()
        {
            this.InitializeComponent();

            LoadModel();

            OpenCamera();
        }

        public async void LoadFace()
        {
            IReadOnlyList<StorageFile> files = await ApplicationData.Current.LocalFolder.GetFilesAsync();

            foreach (StorageFile file in files)
            {
                GridViewImage.Items.Add(new ImageFile(file.DisplayName, file.Path, await ArcFace(file)));
            }
        }

        private async void LoadModel()
        {
            StorageFile file = await StorageFile.GetFileFromApplicationUriAsync(new Uri("ms-appx:///ArcFace.onnx"));
            _arcFaceModel = await ArcFaceModel.CreateFromStreamAsync(file as IRandomAccessStreamReference);

            await objectDetection.Init(await StorageFile.GetFileFromApplicationUriAsync(new Uri("ms-appx:///BearFace.onnx")));

            LoadFace();

            _ready = true;
        }

        public async void OpenCamera()
        {
            await CameraPreviewControl.StartAsync();
            CameraPreviewControl.CameraHelper.FrameArrived += CameraHelper_FrameArrived;
        }

        private async void CameraHelper_FrameArrived(object sender, FrameEventArgs e)
        {
            VideoFrame videoFrame = e.VideoFrame;
            SoftwareBitmap softwareBitmap = videoFrame.SoftwareBitmap;

            if (_ready)
            {
                _ready = false;

                try
                {
                    IList<PredictionModel> faces = await objectDetection.PredictImageAsync(VideoFrame.CreateWithSoftwareBitmap(await ResizeBitmap(softwareBitmap, YOLO_INPUT, YOLO_INPUT)));

                    PredictionModel face = faces[0];

                    if (faces.Count > 0 && face.BoundingBox.Height * face.BoundingBox.Width > MIN_SIZE)
                    {
                        SoftwareBitmap softwareBitmapFace = await CorpBitmap(softwareBitmap,
                            new Rect(Math.Max(0, softwareBitmap.PixelWidth * face.BoundingBox.Left),
                                Math.Max(0, softwareBitmap.PixelHeight * face.BoundingBox.Top),
                                Math.Max(0, softwareBitmap.PixelWidth * face.BoundingBox.Width),
                                Math.Max(0, softwareBitmap.PixelHeight * face.BoundingBox.Height)));

                        _softwareBitmapFace = await ResizeBitmap(softwareBitmapFace, ARC_FACE_INPUT, ARC_FACE_INPUT);

                        List<float> embedding = await ArcFace(_softwareBitmapFace);

                        List<double> result = new List<double>();

                        await Dispatcher.RunAsync(CoreDispatcherPriority.High, () =>
                        {
                            for (int i = 0; i < GridViewImage.Items.Count; i++)
                            {
                                ImageFile imageFile = (GridViewImage.Items[i] as ImageFile);

                                result.Add(GetCosineSimilarity(embedding, imageFile.Embedding));
                            }

                            CanvasPreview.Children.Clear();

                            CanvasPreview.Children.Add(new Rectangle()
                            {
                                Height = Convert.ToInt32(GridPreview.Height * face.BoundingBox.Height),
                                Margin = new Thickness(GridPreview.Width * face.BoundingBox.Left, GridPreview.Height * face.BoundingBox.Top, 0, 0),
                                Stroke = new SolidColorBrush(Windows.UI.Colors.Red),
                                StrokeThickness = 3,
                                Width = Convert.ToInt32(GridPreview.Width * face.BoundingBox.Width),
                            });

                            if (GridViewImage.Items.Count > 0)
                            {
                                var maxIndex = result.IndexOf(result.Max());

                                if (result[maxIndex] > MIN_SIMILARITY)
                                {
                                    CanvasPreview.Children.Add(new TextBlock()
                                    {
                                        FontSize = 24,
                                        Foreground = new SolidColorBrush(Windows.UI.Colors.Red),
                                        Margin = new Thickness(GridPreview.Width * face.BoundingBox.Left, GridPreview.Height * face.BoundingBox.Top - 30, 0, 0),
                                        Text = $"{(GridViewImage.Items[maxIndex] as ImageFile).DisplayName}: {result[maxIndex].ToString("N2")}"
                                    });

                                    Thread.Sleep(1000);
                                }
                            }
                        });
                    }
                    else
                    {
                        await Dispatcher.RunAsync(CoreDispatcherPriority.High, () =>
                        {
                            CanvasPreview.Children.Clear();
                        });
                    }
                }
                catch (Exception ex)
                {
                    Debug.WriteLine(ex.Message);
                }

                _ready = true;
            }
        }

        private async Task<List<float>> ArcFace(StorageFile storageFile)
        {
            SoftwareBitmap softwareBitmap;

            using (IRandomAccessStream stream = await storageFile.OpenAsync(FileAccessMode.Read))
            {
                // Create the decoder from the stream 
                BitmapDecoder decoder = await BitmapDecoder.CreateAsync(stream);
                BitmapTransform transform = new BitmapTransform();

                transform.ScaledHeight = ARC_FACE_INPUT;
                transform.ScaledWidth = ARC_FACE_INPUT;
                transform.InterpolationMode = BitmapInterpolationMode.Linear;

                // Get the SoftwareBitmap representation of the file in BGRA8 format
                softwareBitmap = await decoder.GetSoftwareBitmapAsync(BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied, transform, ExifOrientationMode.RespectExifOrientation, ColorManagementMode.DoNotColorManage);
            }

            return await ArcFace(softwareBitmap);
        }

        private async Task<List<float>> ArcFace(SoftwareBitmap softwareBitmap)
        {
            // Encapsulate the image within a VideoFrame to be bound and evaluated
            VideoFrame inputImage = VideoFrame.CreateWithSoftwareBitmap(softwareBitmap);

            int height = inputImage.SoftwareBitmap.PixelHeight;
            int width = inputImage.SoftwareBitmap.PixelWidth;

            float[] data = new float[1 * 3 * ARC_FACE_INPUT * ARC_FACE_INPUT];

            byte[] imageBytes = new byte[4 * height * width];
            inputImage.SoftwareBitmap.CopyToBuffer(imageBytes.AsBuffer());

            int id = 0;

            for (int i = 0; i < data.Length; i += 4)
            {

                float blue = (float)imageBytes[i];
                float green = (float)imageBytes[i + 1];
                float red = (float)imageBytes[i + 2];

                data[id++] = blue;
                data[id++] = green;
                data[id++] = red;
            }

            _arcFaceInput.data = TensorFloat.CreateFromArray(new List<long> { 1, 3, ARC_FACE_INPUT, ARC_FACE_INPUT }, data);

            // Process the frame with the model
            _arcFaceOutput = await _arcFaceModel.EvaluateAsync(_arcFaceInput);

            IReadOnlyList<float> vectorImage = _arcFaceOutput.fc1.GetAsVectorView();
            return vectorImage.ToList();
        }

        public static double GetCosineSimilarity(List<float> vector1, List<float> vector2)
        {
            int count = ((vector2.Count < vector1.Count) ? vector2.Count : vector1.Count);
            double dot = 0.0d;
            double magnitude1 = 0.0d;
            double magnitude2 = 0.0d;

            for (int n = 0; n < count; n++)
            {
                dot += vector1[n] * vector2[n];
                magnitude1 += Math.Pow(vector1[n], 2);
                magnitude2 += Math.Pow(vector2[n], 2);
            }

            return dot / (Math.Sqrt(magnitude1) * Math.Sqrt(magnitude2));
        }

        private async Task ClearFace()
        {
            IReadOnlyList<StorageFile> files = await ApplicationData.Current.LocalFolder.GetFilesAsync();

            foreach (StorageFile file in files)
            {
                await file.DeleteAsync();
            }

            GridViewImage.Items.Clear();
        }

        #region Bitmap Helper

        private async Task<SoftwareBitmap> CorpBitmap(SoftwareBitmap softwareBitmap, Rect rect)
        {
            SoftwareBitmap result;

            using (SoftwareBitmap encoderBitmap = SoftwareBitmap.Convert(softwareBitmap, BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied))
            {
                using (MemoryStream memoryStream = new MemoryStream())
                {
                    BitmapEncoder encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.JpegEncoderId, memoryStream.AsRandomAccessStream());

                    encoder.SetSoftwareBitmap(encoderBitmap);
                    encoder.BitmapTransform.Bounds = new BitmapBounds()
                    {
                        X = (uint)rect.X,
                        Y = (uint)rect.Y,
                        Height = (uint)rect.Height,
                        Width = (uint)rect.Width
                    };

                    await encoder.FlushAsync();

                    var decoder = await BitmapDecoder.CreateAsync(memoryStream.AsRandomAccessStream());

                    result = await decoder.GetSoftwareBitmapAsync(BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied);
                }
            }

            return result;
        }

        private async static Task<SoftwareBitmap> ResizeBitmap(SoftwareBitmap softwareBitmap, int width, int height)
        {
            SoftwareBitmap result;

            using (SoftwareBitmap encoderBitmap = SoftwareBitmap.Convert(softwareBitmap, BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied))
            {
                using (MemoryStream memoryStream = new MemoryStream())
                {
                    BitmapEncoder encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.JpegEncoderId, memoryStream.AsRandomAccessStream());

                    encoder.SetSoftwareBitmap(encoderBitmap);
                    encoder.BitmapTransform.ScaledWidth = (uint)width;
                    encoder.BitmapTransform.ScaledHeight = (uint)height;

                    await encoder.FlushAsync();

                    var decoder = await BitmapDecoder.CreateAsync(memoryStream.AsRandomAccessStream());

                    result = await decoder.GetSoftwareBitmapAsync(BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied);
                }
            }

            return result;
        }

        #endregion

        #region Button Click

        private async void ButtonAdd_Click(object sender, RoutedEventArgs e)
        {
            StorageFile file = await ApplicationData.Current.LocalFolder.CreateFileAsync(TextBoxId.Text, CreationCollisionOption.ReplaceExisting);

            using (IRandomAccessStream stream = await file.OpenAsync(FileAccessMode.ReadWrite))
            {
                // Create an encoder with the desired format
                BitmapEncoder encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.JpegEncoderId, stream);

                // Set the software bitmap
                encoder.SetSoftwareBitmap(_softwareBitmapFace);

                await encoder.FlushAsync();
            }

            GridViewImage.Items.Add(new ImageFile(file.DisplayName, file.Path, await ArcFace(file)));
        }

        private async void ButtonDelete_Click(object sender, RoutedEventArgs e)
        {
            await ClearFace();
        }

        private async void ButtonLoad_Click(object sender, RoutedEventArgs e)
        {
            await ClearFace();

            foreach (string bear in bearList)
            {
                StorageFile file = await StorageFile.GetFileFromApplicationUriAsync(new Uri($"ms-appx:///Bears//{bear}.jpg"));

                SoftwareBitmap softwareBitmap;

                using (IRandomAccessStream stream = await file.OpenAsync(FileAccessMode.Read))
                {
                    // Create the decoder from the stream 
                    BitmapDecoder decoder = await BitmapDecoder.CreateAsync(stream);
                    BitmapTransform transform = new BitmapTransform();

                    transform.ScaledHeight = ARC_FACE_INPUT;
                    transform.ScaledWidth = ARC_FACE_INPUT;
                    transform.InterpolationMode = BitmapInterpolationMode.Linear;

                    // Get the SoftwareBitmap representation of the file in BGRA8 format
                    softwareBitmap = await decoder.GetSoftwareBitmapAsync(BitmapPixelFormat.Bgra8, BitmapAlphaMode.Premultiplied, transform, ExifOrientationMode.RespectExifOrientation, ColorManagementMode.DoNotColorManage);
                }

                file = await ApplicationData.Current.LocalFolder.CreateFileAsync($"{bear}", CreationCollisionOption.ReplaceExisting);

                using (IRandomAccessStream stream = await file.OpenAsync(FileAccessMode.ReadWrite))
                {
                    // Create an encoder with the desired format
                    BitmapEncoder encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.JpegEncoderId, stream);

                    // Set the software bitmap
                    encoder.SetSoftwareBitmap(softwareBitmap);

                    await encoder.FlushAsync();
                }

                GridViewImage.Items.Add(new ImageFile(file.DisplayName, file.Path, await ArcFace(file)));
            }
        }

        private void ButtonCamera_Click(object sender, RoutedEventArgs e)
        {
            OpenCamera();
        }

        #endregion
    }
}