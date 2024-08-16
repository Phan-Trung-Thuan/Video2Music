import argparse
from .constants import *

version = VERSION
split_ver = SPLIT_VER
split_path = "split_" + split_ver

def parse_train_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-dataset_dir", type=str, default="./dataset/", help="Folder of VEVO dataset")
    
    parser.add_argument("-input_dir_music", type=str, default="./dataset/vevo_chord/" + MUSIC_TYPE, help="Folder of video CNN feature files")
    parser.add_argument("-input_dir_video", type=str, default="./dataset/vevo_vis", help="Folder of video CNN feature files")

    parser.add_argument("-output_dir", type=str, default="./saved_models", help="Folder to save model weights. Saves one every epoch")
    
    parser.add_argument("-weight_modulus", type=int, default=10, help="How often to save epoch weights (ex: value of 10 means save every 10 epochs)")
    parser.add_argument("-print_modulus", type=int, default=100, help="How often to print train results for a batch (batch loss, learn rate, etc.)")
    parser.add_argument("-n_workers", type=int, default=4, help="Number of threads for the dataloader")
    parser.add_argument("--force_cpu", type=bool, default=False, help="Forces model to run on a cpu even when gpu is available")
    parser.add_argument("--no_tensorboard", type=bool, default=True, help="Turns off tensorboard result reporting")
    parser.add_argument("-continue_weights", type=str, default=None, help="Model weights to continue training based on")
    parser.add_argument("-continue_epoch", type=int, default=None, help="Epoch the continue_weights model was at")
    parser.add_argument("-lr", type=float, default=None, help="Constant learn rate. Leave as None for a custom scheduler.")
    parser.add_argument("-ce_smoothing", type=float, default=0.1, help="Smoothing parameter for smoothed cross entropy loss (defaults to no smoothing)")
    parser.add_argument("-batch_size", type=int, default=20, help="Batch size to use")
    parser.add_argument("-epochs", type=int, default=30, help="Number of epochs to use")

    parser.add_argument("-max_sequence_midi", type=int, default=2048, help="Maximum midi sequence to consider")
    parser.add_argument("-max_sequence_video", type=int, default=300, help="Maximum video sequence to consider")
    parser.add_argument("-max_sequence_chord", type=int, default=300, help="Maximum video sequence to consider")

    parser.add_argument("-n_layers", type=int, default=6, help="Number of decoder layers to use")
    parser.add_argument("-num_heads", type=int, default=8, help="Number of heads to use for multi-head attention")
    parser.add_argument("-d_model", type=int, default=512, help="Dimension of the model (output dim of embedding layers, etc.)")
    parser.add_argument("-dim_feedforward", type=int, default=1024, help="Dimension of the feedforward layer")
    parser.add_argument("-dropout", type=float, default=0.2, help="Dropout rate")

    parser.add_argument('-rms_norm', type=bool, default=False, help="Use RMSNorm instead of LayerNorm")
    parser.add_argument("-is_video", type=bool, default=IS_VIDEO, help="MusicTransformer or VideoMusicTransformer")
    parser.add_argument('-music_gen_version', type=str, default='3.1', help="Version number. None is original musgic generation AMT model")

    if IS_VIDEO:
        parser.add_argument("-vis_models", type=str, default=VIS_MODELS_SORTED, help="...")
    else:
        parser.add_argument("-vis_models", type=str, default="", help="...")

    parser.add_argument("-emo_model", type=str, default="6c_l14p", help="...")
    parser.add_argument("-rpr", type=bool, default=RPR, help="...")
    return parser.parse_known_args()

def print_train_args(args):
    print(SEPERATOR)
    
    print("dataset_dir:", args.dataset_dir )
    
    print("input_dir_music:", args.input_dir_music)
    print("input_dir_video:", args.input_dir_video)

    print("output_dir:", args.output_dir)

    print("weight_modulus:", args.weight_modulus)
    print("print_modulus:", args.print_modulus)
    print("")
    print("n_workers:", args.n_workers)
    print("force_cpu:", args.force_cpu)
    print("tensorboard:", not args.no_tensorboard)
    print("")
    print("continue_weights:", args.continue_weights)
    print("continue_epoch:", args.continue_epoch)
    print("")
    print("lr:", args.lr)
    print("ce_smoothing:", args.ce_smoothing)
    print("batch_size:", args.batch_size)
    print("epochs:", args.epochs)
    print("")
    print("rpr:", args.rpr)

    print("max_sequence_midi:", args.max_sequence_midi)
    print("max_sequence_video:", args.max_sequence_video)
    print("max_sequence_chord:", args.max_sequence_chord)
    
    print("n_layers:", args.n_layers)
    print("num_heads:", args.num_heads)
    print("d_model:", args.d_model)
    print("")
    print("dim_feedforward:", args.dim_feedforward)
    print("dropout:", args.dropout)
    print("rms_norm:", args.rms_norm)
    print("is_video:", args.is_video)
    print("music_gen_version:", args.music_gen_version)

    print(SEPERATOR)
    print("")

def parse_eval_args():
    if IS_VIDEO:
        modelpath = "./saved_models/AMT/best_loss_weights.pickle"
        # modelpath = "./saved_models/"+version+ "/"+VIS_MODELS_PATH+"/results/best_loss_weights.pickle"
    else:
        modelpath = "./saved_models/"+version+ "/no_video/results/best_loss_weights.pickle"

    parser = argparse.ArgumentParser()

    parser.add_argument("-dataset_dir", type=str, default="./dataset/", help="Folder of VEVO dataset")
    
    parser.add_argument("-input_dir_music", type=str, default="./dataset/vevo_chord/" + MUSIC_TYPE, help="Folder of video CNN feature files")
    parser.add_argument("-input_dir_video", type=str, default="./dataset/vevo_vis", help="Folder of video CNN feature files")
    
    parser.add_argument("-model_weights", type=str, default=modelpath, help="Pickled model weights file saved with torch.save and model.state_dict()")
    
    parser.add_argument("-n_workers", type=int, default=4, help="Number of threads for the dataloader")
    parser.add_argument("--force_cpu", type=bool, default=False, help="Forces model to run on a cpu even when gpu is available")
    parser.add_argument("-batch_size", type=int, default=1, help="Batch size to use")
    
    parser.add_argument("-max_sequence_midi", type=int, default=2048, help="Maximum midi sequence to consider")
    parser.add_argument("-max_sequence_video", type=int, default=300, help="Maximum video sequence to consider")
    parser.add_argument("-max_sequence_chord", type=int, default=300, help="Maximum video sequence to consider")

    parser.add_argument("-n_layers", type=int, default=6, help="Number of decoder layers to use")
    parser.add_argument("-num_heads", type=int, default=8, help="Number of heads to use for multi-head attention")
    parser.add_argument("-d_model", type=int, default=512, help="Dimension of the model (output dim of embedding layers, etc.)")
    parser.add_argument("-dim_feedforward", type=int, default=1024, help="Dimension of the feedforward layer")
    parser.add_argument('-rms_norm', type=bool, default=False, help="Use RMSNorm instead of LayerNorm")
    parser.add_argument('-music_gen_version', type=str, default='3.1', help="Version number. None is original musgic generation AMT model")
    parser.add_argument("-is_video", type=bool, default=IS_VIDEO, help="MusicTransformer or VideoMusicTransformer")

    if IS_VIDEO:
        parser.add_argument("-vis_models", type=str, default=VIS_MODELS_SORTED, help="...")
    else:
        parser.add_argument("-vis_models", type=str, default="", help="...")

    parser.add_argument("-emo_model", type=str, default="6c_l14p", help="...")
    parser.add_argument("-rpr", type=bool, default=RPR, help="...")
    return parser.parse_known_args()

def print_eval_args(args):
    print(SEPERATOR)
    print("input_dir_music:", args.input_dir_music)
    print("input_dir_video:", args.input_dir_video)

    print("model_weights:", args.model_weights)
    print("n_workers:", args.n_workers)
    print("force_cpu:", args.force_cpu)
    print("")
    print("batch_size:", args.batch_size)
    print("")
    print("rpr:", args.rpr)
    
    print("max_sequence_midi:", args.max_sequence_midi)
    print("max_sequence_video:", args.max_sequence_video)
    print("max_sequence_chord:", args.max_sequence_chord)
    
    print("n_layers:", args.n_layers)
    print("num_heads:", args.num_heads)
    print("d_model:", args.d_model)
    print("")
    print("rms_norm:", args.rms_norm)
    print("dim_feedforward:", args.dim_feedforward)    
    print("music_gen_version:", args.music_gen_version)

    print(SEPERATOR)
    print("")

# write_model_params
def write_model_params(args, output_file):
    o_stream = open(output_file, "w")

    o_stream.write("rpr: " + str(args.rpr) + "\n")
    o_stream.write("lr: " + str(args.lr) + "\n")
    o_stream.write("n_epochs: " + str(args.epochs) + "\n")
    o_stream.write("ce_smoothing: " + str(args.ce_smoothing) + "\n")
    o_stream.write("batch_size: " + str(args.batch_size) + "\n")

    o_stream.write("max_sequence_midi: " + str(args.max_sequence_midi) + "\n")
    o_stream.write("max_sequence_video: " + str(args.max_sequence_video) + "\n")
    o_stream.write("max_sequence_chord: " + str(args.max_sequence_chord) + "\n")
    
    o_stream.write("n_layers: " + str(args.n_layers) + "\n")
    o_stream.write("num_heads: " + str(args.num_heads) + "\n")
    o_stream.write("d_model: " + str(args.d_model) + "\n")
    o_stream.write("dim_feedforward: " + str(args.dim_feedforward) + "\n")
    o_stream.write("dropout: " + str(args.dropout) + "\n")
    o_stream.write("rms_norm: " + str(args.rms_norm) + "\n")
    o_stream.write("music_gen_version: " + str(args.music_gen_version) + "\n")

    o_stream.write("is_video: " + str(args.is_video) + "\n")
    o_stream.write("vis_models: " + str(args.vis_models) + "\n")
    o_stream.write("input_dir_music: " + str(args.input_dir_music) + "\n")
    o_stream.write("input_dir_video: " + str(args.input_dir_video) + "\n")

    o_stream.close()
