// This file was automatically generated by VS extension Windows Machine Learning Code Generator VS 2017 v2.6
// from model file BearFace.onnx
// Warning: This file may get overwritten if you add add an onnx file with the same name
using System;
using System.Threading.Tasks;
using Windows.AI.MachineLearning;
using Windows.Storage.Streams;
namespace BearID
{

    public sealed class BearFaceInput
    {
        public ImageFeatureValue data; // BitmapPixelFormat: Bgra8, BitmapAlphaMode: Premultiplied, width: 416, height: 416
    }
    
    public sealed class BearFaceOutput
    {
        public TensorFloat model_outputs0; // shape(-1,30,13,13)
    }
    
    public sealed class BearFaceModel
    {
        private LearningModel model;
        private LearningModelSession session;
        private LearningModelBinding binding;
        public static async Task<BearFaceModel> CreateFromStreamAsync(IRandomAccessStreamReference stream)
        {
            BearFaceModel learningModel = new BearFaceModel();
            learningModel.model = await LearningModel.LoadFromStreamAsync(stream);
            learningModel.session = new LearningModelSession(learningModel.model);
            learningModel.binding = new LearningModelBinding(learningModel.session);
            return learningModel;
        }
        public async Task<BearFaceOutput> EvaluateAsync(BearFaceInput input)
        {
            binding.Bind("data", input.data);
            var result = await session.EvaluateAsync(binding, "0");
            var output = new BearFaceOutput();
            output.model_outputs0 = result.Outputs["model_outputs0"] as TensorFloat;
            return output;
        }
    }
}

