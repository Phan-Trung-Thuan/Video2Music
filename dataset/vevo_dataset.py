import os
import pickle
import random
import torch
import torch.nn as nn
import numpy as np
import pandas as pd

from torch.utils.data import Dataset
from utilities.constants import *
from utilities.device import cpu_device
from utilities.device import get_device
from gensim.models import Word2Vec

import json
from tqdm import tqdm
import copy

SEQUENCE_START = 0

key_dic = {
    'F major' : -7,
    'F# major' : -6,
    'Gb major' : -6,
    'G major' : -5,
    'G# major' : -4,
    'Ab major' : -4,
    'A major' : -3,
    'A# major' : -2,
    'Bb major' : -2,
    'B major' : -1,
    'C major' : 0,
    'C# major' : 1,
    'Db major' : 1,
    'D major' : 2,
    'D# major' : 3,
    'Eb major' : 3,
    'E major' : 4,
    'D minor' : -7,
    'D# minor' : -6,
    'Eb minor' : -6,
    'E minor' : -5,
    'F minor' : -4,
    'F# minor' : -3,
    'Gb minor' : -3,
    'G minor' : -2,
    'G# minor' : -1,
    'Ab minor' : -1,
    'A minor' : 0,
    'A# minor' : 1,
    'Bb minor' : 1,
    'B minor' : 2,
    'C minor' : 3,
    'C# minor' : 4,
    'Db minor' : 4
}

class VevoDataset(Dataset):
    def __init__(self, dataset_root = "./dataset/", split="train", split_ver="v1", vis_models="2d/clip_l14p", emo_model="6c_l14p", motion_type=0, max_seq_chord=300, max_seq_video=300, random_seq=True, is_video = True, augmentation=False):
        
        self.dataset_root       = dataset_root
        self.motion_type = motion_type
        self.augmentation = augmentation

        self.vevo_chord_root = os.path.join( dataset_root, "vevo_chord", "lab_v2_norm", "origin")
        self.vevo_chord_root_no_norm = os.path.join( dataset_root, "vevo_chord", "lab_v2", "origin")
        self.vevo_emotion_root = os.path.join( dataset_root, "vevo_emotion", emo_model, "origin")
        
        if self.motion_type == 0:
            self.vevo_motion_root = os.path.join( dataset_root, "vevo_motion", "origin") # Original
        elif self.motion_type == 1:
            self.vevo_motion_root = os.path.join( dataset_root, "vevo_motion", "option1") # Option 1
        elif self.motion_type == 2:
            self.vevo_motion_root = os.path.join( dataset_root, "vevo_motion", "option2") # Option 2
        
        self.vevo_scene_offset_root = os.path.join( dataset_root, "vevo_scene_offset", "origin")
        self.vevo_meta_split_path = os.path.join( dataset_root, "vevo_meta", "split", split_ver, split + ".txt")
        
        self.vevo_loudness_root = os.path.join( dataset_root, "vevo_loudness", "origin")
        self.vevo_note_density_root = os.path.join( dataset_root, "vevo_note_density", "origin")
        self.vevo_instrument_root = os.path.join( dataset_root, "vevo_instrument", "thresholding")

        self.max_seq_video    = max_seq_video
        self.max_seq_chord    = max_seq_chord
        self.random_seq = random_seq
        self.is_video = is_video

        self.vis_models_arr = vis_models.split(" ")
        self.vevo_semantic_root_list = []
        self.id_list = []

        self.emo_model = emo_model

        if IS_VIDEO:
            for i in range( len(self.vis_models_arr) ):
                p1 = self.vis_models_arr[i].split("/")[0]
                p2 = self.vis_models_arr[i].split("/")[1]
                vevo_semantic_root = os.path.join(dataset_root, "vevo_semantic" , "origin" , p1, p2)
                self.vevo_semantic_root_list.append( vevo_semantic_root )
            
        with open( self.vevo_meta_split_path ) as f:
            for line in f:
                self.id_list.append(line.strip())
        
        self.data_files_chord         = []
        self.data_files_chord_no_norm = []
        self.data_files_emotion       = []
        self.data_files_motion        = []
        self.data_files_scene_offset  = []
        self.data_files_semantic_list = []

        self.data_files_loudness      = []
        self.data_files_note_density  = []
        self.data_files_instrument    = []

        for i in range(len(self.vis_models_arr)):
            self.data_files_semantic_list.append([])

        for fid in self.id_list:
            fpath_chord = os.path.join( self.vevo_chord_root, fid + ".lab" )
            fpath_chord_no_norm = os.path.join( self.vevo_chord_root_no_norm, fid + ".lab" )
            fpath_emotion = os.path.join( self.vevo_emotion_root, fid + ".lab" )
            
            if self.motion_type == 0:
                fpath_motion = os.path.join( self.vevo_motion_root, fid + ".lab" ) # Original
            elif self.motion_type == 1 or self.motion_type == 2:
                fpath_motion = os.path.join( self.vevo_motion_root, fid + ".npy" ) # Option 1 and 2
            
            fpath_scene_offset = os.path.join( self.vevo_scene_offset_root, fid + ".lab" )

            fpath_loudness = os.path.join( self.vevo_loudness_root, fid + ".lab" )
            fpath_note_density = os.path.join( self.vevo_note_density_root, fid + ".lab" )
            fpath_instrument = os.path.join( self.vevo_instrument_root, fid + ".csv")

            fpath_semantic_list = []
            for vevo_semantic_root in self.vevo_semantic_root_list:
                fpath_semantic = os.path.join( vevo_semantic_root, fid + ".npy" )
                fpath_semantic_list.append(fpath_semantic)
            
            checkFile_semantic = True
            for fpath_semantic in fpath_semantic_list:
                if not os.path.exists(fpath_semantic):
                    checkFile_semantic = False
            
            checkFile_chord = os.path.exists(fpath_chord)
            checkFile_chord_no_norm = os.path.exists(fpath_chord_no_norm)
            checkFile_emotion = os.path.exists(fpath_emotion)
            checkFile_motion = os.path.exists(fpath_motion)
            checkFile_scene_offset = os.path.exists(fpath_scene_offset)

            checkFile_loudness = os.path.exists(fpath_loudness)
            checkFile_note_density = os.path.exists(fpath_note_density)
            checkFile_instrument = os.path.exists(fpath_instrument)

            if checkFile_chord and checkFile_chord_no_norm and checkFile_emotion and checkFile_motion \
                and checkFile_scene_offset and checkFile_semantic and checkFile_loudness \
                and checkFile_note_density and checkFile_instrument:

                self.data_files_chord.append(fpath_chord)
                self.data_files_chord_no_norm.append(fpath_chord_no_norm)
                self.data_files_emotion.append(fpath_emotion)
                self.data_files_motion.append(fpath_motion)
                self.data_files_scene_offset.append(fpath_scene_offset)

                self.data_files_loudness.append(fpath_loudness)
                self.data_files_note_density.append(fpath_note_density)
                self.data_files_instrument.append(fpath_instrument)

                if IS_VIDEO:
                    for i in range(len(self.vis_models_arr)):
                        self.data_files_semantic_list[i].append( fpath_semantic_list[i] )
        
        chordDicPath = os.path.join( dataset_root, "vevo_meta/chord.json")
        
        chordRootDicPath = os.path.join( dataset_root, "vevo_meta/chord_root.json")
        chordAttrDicPath = os.path.join( dataset_root, "vevo_meta/chord_attr.json")
        
        with open(chordDicPath) as json_file:
            self.chordDic = json.load(json_file)
        
        with open(chordRootDicPath) as json_file:
            self.chordRootDic = json.load(json_file)
        
        with open(chordAttrDicPath) as json_file:
            self.chordAttrDic = json.load(json_file)

        # Get all samples
        self.dataset = []
        print(f'Get all samples ({len(self.data_files_chord)})')
        for i in tqdm(range(len(self.data_files_chord))):
            self.dataset.append(self.createSample(i))

        # Augmentation
        if self.augmentation:
            print('Augmentation...')
            num_iterations = 2 * len(self.dataset)
            augmented_dataset = []
            for _ in range(num_iterations):
                a, b = random.sample(self.dataset, 2)  # Pick 2 distinct elements
                l = random.uniform(0.2, 0.8)
                c = {
                    "x": a["x"] * l + b["x"] * (l - 1),
                    "chord": a["chord"] * l + b["chord"] * (l - 1),
                    "x_root": a["x_root"] * l + b["x_root"] * (l - 1),
                    "tgt_root": a["tgt_root"] * l + b["tgt_root"] * (l - 1),
                    "chord_root": a["chord_root"] * l + b["chord_root"] * (l - 1),
                    "x_attr": a["x_attr"] * l + b["x_attr"] * (l - 1),
                    "tgt_attr": a["tgt_attr"] * l + b["tgt_attr"] * (l - 1),
                    "chord_attr": a["chord_attr"] * l + b["chord_attr"] * (l - 1),
                    "semanticList": a["semanticList"] * l + b["semanticList"] * (l - 1),
                    "key": a["key"] * l + b["key"] * (l - 1),
                    "key_val": a["key_val"] * l + b["key_val"] * (l - 1),
                    "scene_offset": a["scene_offset"] * l + b["scene_offset"] * (l - 1),
                    "motion": a["motion"] * l + b["motion"] * (l - 1),
                    "emotion": a["emotion"] * l + b["emotion"] * (l - 1),
                    "tgt_emotion": a["tgt_emotion"] * l + b["tgt_emotion"] * (l - 1),
                    "tgt_emotion_prob": a["tgt_emotion_prob"] * l + b["tgt_emotion_prob"] * (l - 1),
                    "note_density": a["note_density"] * l + b["note_density"] * (l - 1),
                    "loudness": a["loudness"] * l + b["loudness"] * (l - 1),
                    "instrument": a["instrument"] * l + b["instrument"] * (l - 1)
                }
                augmented_dataset.append(c)
            self.dataset.extend(augmented_dataset)
            print('Augmentation adchieve', len(self.dataset), 'samples')

    def __len__(self):
        return len(self.dataset)

    def emotionDistance(self, sample1, sample2, idx1=300//2, idx2=300//2, window_size=20):
        if idx1 < window_size or idx2 < window_size:
            return 100.0
        
        if idx1 + window_size > sample1['emotion'].shape[0] or idx2 + window_size > sample2['emotion'].shape[0]:
            return 100.0
        
        emo1 = sample1['emotion'][idx1 - window_size:idx1 + window_size]
        emo2 = sample2['emotion'][idx2 - window_size:idx2 + window_size]
        distance = torch.norm(emo1 - emo2, dim=1)
        return torch.mean(distance)

    def createSample(self, idx):
        #### ---- CHORD ----- ####
        feature_chord = np.empty(self.max_seq_chord)
        feature_chord.fill(CHORD_PAD)

        feature_chordRoot = np.empty(self.max_seq_chord)
        feature_chordRoot.fill(CHORD_ROOT_PAD)
        feature_chordAttr = np.empty(self.max_seq_chord)
        feature_chordAttr.fill(CHORD_ATTR_PAD)

        key = ""
        with open(self.data_files_chord[idx], encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                line_arr = line.split(" ")
                if line_arr[0] == "key":
                    key = line_arr[1] + " "+ line_arr[2]
                    continue
                time = line_arr[0]
                time = int(time)
                if time >= self.max_seq_chord:
                    break
                chord = line_arr[1]

                # Original
                chordID = self.chordDic[chord]
                feature_chord[time] = chordID
                chord_arr = chord.split(":")

                if len(chord_arr) == 1:
                    if chord_arr[0] == "N":
                        chordRootID = self.chordRootDic["N"]
                        chordAttrID = self.chordAttrDic["N"]
                        feature_chordRoot[time] = chordRootID
                        feature_chordAttr[time] = chordAttrID
                    else:
                        chordRootID = self.chordRootDic[chord_arr[0]]
                        feature_chordRoot[time] = chordRootID
                        feature_chordAttr[time] = 1
                elif len(chord_arr) == 2:
                    chordRootID = self.chordRootDic[chord_arr[0]]
                    chordAttrID = self.chordAttrDic[chord_arr[1]]
                    feature_chordRoot[time] = chordRootID
                    feature_chordAttr[time] = chordAttrID

                # CBOW in Chord Embedding
                
        if "major" in key:
            feature_key = torch.tensor([0])
        else:
            feature_key = torch.tensor([1])

        with open(self.data_files_chord_no_norm[idx], encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                line_arr = line.split(" ")
                if line_arr[0] == "key":
                    original_key = line_arr[1] + " "+ line_arr[2]
                    break

        if original_key in key_dic:
            key_val = torch.tensor([key_dic[original_key]])
        else:
            print(original_key)

        feature_chord = torch.from_numpy(feature_chord)
        feature_chord = feature_chord.to(torch.long)
        
        feature_chordRoot = torch.from_numpy(feature_chordRoot)
        feature_chordRoot = feature_chordRoot.to(torch.long)

        feature_chordAttr = torch.from_numpy(feature_chordAttr)
        feature_chordAttr = feature_chordAttr.to(torch.long)

        feature_key = feature_key.float()
        
        x = feature_chord[:self.max_seq_chord-1]
        tgt = feature_chord[1:self.max_seq_chord]

        x_root = feature_chordRoot[:self.max_seq_chord-1]
        tgt_root = feature_chordRoot[1:self.max_seq_chord]
        x_attr = feature_chordAttr[:self.max_seq_chord-1]
        tgt_attr = feature_chordAttr[1:self.max_seq_chord]

        if time < self.max_seq_chord:
            tgt[time] = CHORD_END
            tgt_root[time] = CHORD_ROOT_END
            tgt_attr[time] = CHORD_ATTR_END
        
        #### ---- SCENE OFFSET ----- ####
        feature_scene_offset = np.empty(self.max_seq_video)
        feature_scene_offset.fill(SCENE_OFFSET_PAD)
        with open(self.data_files_scene_offset[idx], encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                line_arr = line.split(" ")
                time = line_arr[0]
                time = int(time)
                if time >= self.max_seq_chord:
                    break
                sceneID = line_arr[1]
                feature_scene_offset[time] = int(sceneID)+1

        feature_scene_offset = torch.from_numpy(feature_scene_offset).squeeze()
        feature_scene_offset = feature_scene_offset.to(torch.float32)

        #### ---- MOTION ----- ####
        if self.motion_type == 0: # Original
            feature_motion = np.empty(self.max_seq_video)
            feature_motion.fill(MOTION_PAD)
            with open(self.data_files_motion[idx], encoding = 'utf-8') as f:
                for line in f:
                    line = line.strip()
                    line_arr = line.split(" ")
                    time = line_arr[0]
                    time = int(time)
                    if time >= self.max_seq_chord:
                        break
                    motion = line_arr[1]
                    feature_motion[time] = float(motion)
                    
        elif self.motion_type == 1: # Option 1
            feature_motion = np.zeros((self.max_seq_chord, 512))
            loaded_motion = np.load(self.data_files_motion[idx])
            if loaded_motion.shape[0] > self.max_seq_chord:
                feature_motion = loaded_motion[:self.max_seq_chord, :]
            else:
                feature_motion[:loaded_motion.shape[0], :] = loaded_motion

        elif self.motion_type == 2: # Option 2
            feature_motion = np.zeros((self.max_seq_chord, 768))
            loaded_motion = np.load(self.data_files_motion[idx])
            if loaded_motion.shape[0] > self.max_seq_chord:
                feature_motion = loaded_motion[:self.max_seq_chord, :]
            else:
                feature_motion[:loaded_motion.shape[0], :] = loaded_motion

        feature_motion = torch.from_numpy(feature_motion)
        feature_motion = feature_motion.to(torch.float32)

        #### ---- NOTE_DENSITY ----- ####
        feature_note_density = np.empty(self.max_seq_video)
        feature_note_density.fill(NOTE_DENSITY_PAD)
        with open(self.data_files_note_density[idx], encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                line_arr = line.split(" ")
                time = line_arr[0]
                time = int(time)
                if time >= self.max_seq_chord:
                    break
                note_density = line_arr[1]
                feature_note_density[time] = float(note_density)

        feature_note_density = torch.from_numpy(feature_note_density)
        feature_note_density = feature_note_density.to(torch.float32)

        #### ---- LOUDNESS ----- ####
        feature_loudness = np.empty(self.max_seq_video)
        feature_loudness.fill(LOUDNESS_PAD)
        with open(self.data_files_loudness[idx], encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                line_arr = line.split(" ")
                time = line_arr[0]
                time = int(time)
                if time >= self.max_seq_chord:
                    break
                loudness = line_arr[1]
                feature_loudness[time] = float(loudness)

        feature_loudness = torch.from_numpy(feature_loudness)
        feature_loudness = feature_loudness.to(torch.float32)

        #### ---- EMOTION ----- ####
        if self.emo_model.startswith("6c"):
            feature_emotion = np.empty( (self.max_seq_video, 6))
        else:
            feature_emotion = np.empty( (self.max_seq_video, 5))

        feature_emotion.fill(EMOTION_PAD)
        with open(self.data_files_emotion[idx], encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                line_arr = line.split(" ")
                if line_arr[0] == "time":
                    continue
                time = line_arr[0]
                time = int(time)
                if time >= self.max_seq_chord:
                    break

                if len(line_arr) == 7:
                    emo1, emo2, emo3, emo4, emo5, emo6 = \
                        line_arr[1],line_arr[2],line_arr[3],line_arr[4],line_arr[5],line_arr[6]                    
                    emoList = [ float(emo1), float(emo2), float(emo3), float(emo4), float(emo5), float(emo6) ]
                elif len(line_arr) == 6:
                    emo1, emo2, emo3, emo4, emo5 = \
                        line_arr[1],line_arr[2],line_arr[3],line_arr[4],line_arr[5]
                    emoList = [ float(emo1), float(emo2), float(emo3), float(emo4), float(emo5) ]
                
                emoList = np.array(emoList)
                feature_emotion[time] = emoList

        feature_emotion = torch.from_numpy(feature_emotion)
        feature_emotion = feature_emotion.to(torch.float32)

        feature_emotion_argmax = torch.argmax(feature_emotion, dim=1)
        _, max_prob_indices = torch.max(feature_emotion, dim=1)
        max_prob_values = torch.gather(feature_emotion, dim=1, index=max_prob_indices.unsqueeze(1))
        max_prob_values = max_prob_values.squeeze()

        #### ---- INSTRUMENT ----- ####
        feature_instrument = np.empty((self.max_seq_video, INSTRUMENT_SIZE))
        feature_instrument.fill(INSTRUMENT_PAD)
        data = pd.read_csv(self.data_files_instrument[idx]).to_numpy()
        if data.shape[0] > self.max_seq_chord:
            data = data[:self.max_seq_chord, :]
        feature_instrument[:data.shape[0], :] = data

        # -- emotion to chord
        #              maj dim sus4 min7 min sus2 aug dim7 maj6 hdim7 7 min6 maj7
        # 0. extcing : [1,0,1,0,0,0,0,0,0,0,1,0,0]
        # 1. fearful : [0,1,0,1,0,0,0,1,0,1,0,0,0]
        # 2. tense :   [0,1,1,1,0,0,0,0,0,0,1,0,0]
        # 3. sad :     [0,0,0,1,1,1,0,0,0,0,0,0,0]
        # 4. relaxing: [1,0,0,0,0,0,0,0,1,0,0,0,1]
        # 5. neutral : [0,0,0,0,0,0,0,0,0,0,0,0,0]

        a0 = [0]+[1,0,1,0,0,0,0,0,0,0,1,0,0]*12+[0,0]
        a1 = [0]+[0,1,0,1,0,0,0,1,0,1,0,0,0]*12+[0,0]
        a2 = [0]+[0,1,1,1,0,0,0,0,0,0,1,0,0]*12+[0,0]
        a3 = [0]+[0,0,0,1,1,1,0,0,0,0,0,0,0]*12+[0,0]
        a4 = [0]+[1,0,0,0,0,0,0,0,1,0,0,0,1]*12+[0,0]
        a5 = [0]+[0,0,0,0,0,0,0,0,0,0,0,0,0]*12+[0,0]

        aend = [0]+[0,0,0,0,0,0,0,0,0,0,0,0,0]*12+[1,0]
        apad = [0]+[0,0,0,0,0,0,0,0,0,0,0,0,0]*12+[0,1]

        a0_tensor = torch.tensor(a0)
        a1_tensor = torch.tensor(a1)
        a2_tensor = torch.tensor(a2)
        a3_tensor = torch.tensor(a3)
        a4_tensor = torch.tensor(a4)
        a5_tensor = torch.tensor(a5)

        aend_tensor = torch.tensor(aend)
        apad_tensor = torch.tensor(apad)

        mapped_tensor = torch.zeros((300, 159))
        for i, val in enumerate(feature_emotion_argmax):
            if feature_chord[i] == CHORD_PAD:
                mapped_tensor[i] = apad_tensor
            elif feature_chord[i] == CHORD_END:
                mapped_tensor[i] = aend_tensor
            elif val == 0:
                mapped_tensor[i] = a0_tensor
            elif val == 1:
                mapped_tensor[i] = a1_tensor
            elif val == 2:
                mapped_tensor[i] = a2_tensor
            elif val == 3:
                mapped_tensor[i] = a3_tensor
            elif val == 4:
                mapped_tensor[i] = a4_tensor
            elif val == 5:
                mapped_tensor[i] = a5_tensor

        # feature emotion : [1, 300, 6]
        # y : [299, 159]
        # tgt : [299]
        # tgt_emo : [299, 159]
        # tgt_emo_prob : [299]

        tgt_emotion = mapped_tensor[1:]
        tgt_emotion_prob = max_prob_values[1:]
        
        feature_semantic_list = []
        if self.is_video:
            for i in range( len(self.vis_models_arr) ):
                video_feature = np.load(self.data_files_semantic_list[i][idx])
                dim_vf = video_feature.shape[1] # 2048
                video_feature_tensor = torch.from_numpy( video_feature )
                
                feature_semantic = torch.full((self.max_seq_video, dim_vf,), SEMANTIC_PAD , dtype=torch.float32, device=cpu_device())
                if(video_feature_tensor.shape[0] < self.max_seq_video):
                    feature_semantic[:video_feature_tensor.shape[0]] = video_feature_tensor
                else:
                    feature_semantic = video_feature_tensor[:self.max_seq_video]
                feature_semantic_list.append(feature_semantic)
        feature_semantic_list = np.stack(feature_semantic_list)
        feature_semantic_list = torch.tensor(feature_semantic_list).squeeze()

        return { "x":x, 
                "tgt":tgt, 
                "chord":feature_chord,
                "x_root":x_root, 
                "tgt_root":tgt_root, 
                "chord_root":feature_chordRoot,
                "x_attr":x_attr, 
                "tgt_attr":tgt_attr,
                "chord_attr":feature_chordAttr,
                "semanticList": feature_semantic_list, 
                "key": feature_key,
                "key_val": key_val,
                "scene_offset": feature_scene_offset,
                "motion": feature_motion,
                "emotion": feature_emotion,
                "tgt_emotion" : tgt_emotion,
                "tgt_emotion_prob" : tgt_emotion_prob,
                "note_density" : feature_note_density,
                "loudness" : feature_loudness,
                "instrument": feature_instrument
                }

    def find_fit_index(self, nums, idx=0, val=1.0):
        indices = [i for i, num in enumerate(nums) if num == val]  # Get the indices of all val
        
        # print(indices, val in nums, val, nums, sep='\n')
        if not indices:
            return None  # If there are no val in the list, return None
        
        # Find the val index closest to the idx
        closest = min(indices, key=lambda x: abs(x - idx))
        
        return int(closest)

    def paddingOrCutting(self, tensor, padding_value=0.0, padding_dim=1, target_size=0):
        try:
            current_size = tensor.size[0]
        except:
            current_size = len(tensor)
    
        if current_size > target_size:
            # Cut the tensor if it is larger than the target size
            return tensor[:target_size]
        elif current_size < target_size:
            # Pad the tensor if it is smaller than the target size
            padding_size = target_size - current_size
            # Create padding with the specified padding_value
            if padding_dim != 1:
                padding = torch.full((padding_size, padding_dim), padding_value)
            else:
                padding = torch.full((padding_size,), padding_value)
            return torch.cat((tensor, padding), dim=0)
        else:
            # Return the tensor unchanged if it's already the target size
            return tensor

    def paddingSample(self, sample, key, padding_dim):
        if key in ('x', 'tgt'):
            sample[key] = self.paddingOrCutting(sample[key], padding_value=CHORD_PAD, padding_dim=padding_dim, target_size=self.max_seq_chord-1)
        elif key in ('x_root', 'tgt_root'):
            sample[key] = self.paddingOrCutting(sample[key], padding_value=CHORD_ROOT_PAD, padding_dim=padding_dim, target_size=self.max_seq_chord-1)
        elif key in ('x_attr', 'tgt_attr'):
            sample[key] = self.paddingOrCutting(sample[key], padding_value=CHORD_ATTR_PAD, padding_dim=padding_dim, target_size=self.max_seq_chord-1)
        elif key in ('tgt_emotion', 'tgt_emotion_prob'):
            sample[key] = self.paddingOrCutting(sample[key], padding_value=EMOTION_PAD, padding_dim=padding_dim, target_size=self.max_seq_chord-1)
        elif key in ('emotion'):
            sample[key] = self.paddingOrCutting(sample[key], padding_value=EMOTION_PAD, padding_dim=padding_dim, target_size=self.max_seq_chord)
        else:
            sample[key] = self.paddingOrCutting(sample[key], padding_dim=padding_dim, target_size=self.max_seq_video)
    
    def swap(self, sample1, sample2, split_point1, split_point2):
        sample1 = copy.deepcopy(sample1)
        sample2 = copy.deepcopy(sample2)

        for key in sample1.keys():
            if key == 'key':
                continue
            
            slice1 = sample1[key][split_point1:]
            slice2 = sample2[key][split_point2:]

            sample1[key] = torch.cat([sample1[key][:split_point1], slice2], dim=0)
            sample2[key] = torch.cat([sample2[key][:split_point2], slice1], dim=0)

            try:
                padding_dim = sample1[key].shape[1]
            except:
                padding_dim = 1

            self.paddingSample(sample1, key, padding_dim)
            self.paddingSample(sample2, key, padding_dim)

            if sample1[key].shape != sample2[key].shape:
                print(sample1[key].shape, sample2[key].shape)
        
        return sample1, sample2

    def __getitem__(self, idx):
        return self.dataset[idx]

def create_vevo_datasets(dataset_root = "./dataset", max_seq_chord=300, max_seq_video=300, vis_models="2d/clip_l14p", emo_model="6c_l14p", motion_type=0, split_ver="v1", random_seq=True, is_video=True, augmentation=False):

    train_dataset = VevoDataset(
        dataset_root = dataset_root, split="train", split_ver=split_ver, 
        vis_models=vis_models, emo_model =emo_model, motion_type=motion_type, max_seq_chord=max_seq_chord, max_seq_video=max_seq_video, 
        random_seq=random_seq, is_video = is_video, augmentation=augmentation)
    
    val_dataset = VevoDataset(
        dataset_root = dataset_root, split="val", split_ver=split_ver, 
        vis_models=vis_models, emo_model =emo_model, motion_type=motion_type, max_seq_chord=max_seq_chord, max_seq_video=max_seq_video, 
        random_seq=random_seq, is_video = is_video )
    
    test_dataset = VevoDataset(
        dataset_root = dataset_root, split="test", split_ver=split_ver, 
        vis_models=vis_models, emo_model =emo_model, motion_type=motion_type, max_seq_chord=max_seq_chord, max_seq_video=max_seq_video, 
        random_seq=random_seq, is_video = is_video )
    
    return train_dataset, val_dataset, test_dataset

def compute_vevo_accuracy(out, tgt):
    softmax = nn.Softmax(dim=-1)
    out = torch.argmax(softmax(out), dim=-1)

    out = out.flatten()
    tgt = tgt.flatten()

    mask = (tgt != CHORD_PAD)

    out = out[mask]
    tgt = tgt[mask]

    if(len(tgt) == 0):
        return 1.0

    num_right = (out == tgt)
    num_right = torch.sum(num_right).type(TORCH_FLOAT)

    acc = num_right / len(tgt)

    return acc

def compute_hits_k(out, tgt, k):
    softmax = nn.Softmax(dim=-1)
    out = softmax(out)
    _, topk_indices = torch.topk(out, k, dim=-1)  # Get the indices of top-k values

    tgt = tgt.flatten()

    topk_indices = torch.squeeze(topk_indices, dim = 0)

    num_right = 0 
    pt = 0
    for i, tlist in enumerate(topk_indices):
        if tgt[i] == CHORD_PAD:
            num_right += 0
        else:
            pt += 1 
            if tgt[i].item() in tlist:
                num_right += 1

    # Empty
    if len(tgt) == 0:
        return 1.0
    
    num_right = torch.tensor(num_right, dtype=torch.float32)
    hitk = num_right / pt

    return hitk

def compute_hits_k_root_attr(out_root, out_attr, tgt, k):
    softmax = nn.Softmax(dim=-1)
    out_root = softmax(out_root)
    out_attr = softmax(out_attr)

    tensor_shape = torch.Size([1, 299, 159])
    out = torch.zeros(tensor_shape)
    for i in range(out.shape[-1]):
        if i == 0 :
            out[0, :, i] = out_root[0, :, 0] * out_attr[0, :, 0] 
        elif i == 157:
            out[0, :, i] = out_root[0, :, 13] * out_attr[0, :, 14]
        elif i == 158:
            out[0, :, i] = out_root[0, :, 14] * out_attr[0, :, 15]
        else:
            rootindex =  int( (i-1)/13 ) + 1
            attrindex =  (i-1)%13 + 1
            out[0, :, i] = out_root[0, :, rootindex] * out_attr[0, :, attrindex]

    out = softmax(out)
    _, topk_indices = torch.topk(out, k, dim=-1)  # Get the indices of top-k values

    tgt = tgt.flatten()

    topk_indices = torch.squeeze(topk_indices, dim = 0)

    num_right = 0 
    pt = 0
    for i, tlist in enumerate(topk_indices):
        if tgt[i] == CHORD_PAD:
            num_right += 0
        else:
            pt += 1 
            if tgt[i].item() in tlist:
                num_right += 1

    if len(tgt) == 0:
        return 1.0
    
    num_right = torch.tensor(num_right, dtype=torch.float32)
    hitk = num_right / pt

    return hitk

def compute_vevo_correspondence(out, tgt, tgt_emotion, tgt_emotion_prob, emotion_threshold):

    tgt_emotion = tgt_emotion.squeeze()
    tgt_emotion_prob = tgt_emotion_prob.squeeze()

    dataset_root = "./dataset/"
    chordRootInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_root_inv.json")
    chordAttrInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_attr_inv.json")
    chordAttrDicPath = os.path.join( dataset_root, "vevo_meta/chord_attr.json")
    
    chordDicPath = os.path.join( dataset_root, "vevo_meta/chord.json")
    chordInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_inv.json")

    with open(chordRootInvDicPath) as json_file:
        chordRootInvDic = json.load(json_file)
    with open(chordAttrDicPath) as json_file:
        chordAttrDic = json.load(json_file)
    with open(chordAttrInvDicPath) as json_file:
        chordAttrInvDic = json.load(json_file)
    with open(chordDicPath) as json_file:
        chordDic = json.load(json_file)
    with open(chordInvDicPath) as json_file:
        chordInvDic = json.load(json_file)

    softmax = nn.Softmax(dim=-1)
    out = torch.argmax(softmax(out), dim=-1)
    out = out.flatten()

    tgt = tgt.flatten()

    num_right = 0
    tgt_emotion_quality = tgt_emotion[:, 0:14]
    pt = 0 
    for i, out_element in enumerate( out ):

        all_zeros = torch.all(tgt_emotion_quality[i] == 0)
        if tgt_emotion[i][-1] == 1 or all_zeros or tgt_emotion_prob[i] < emotion_threshold:
            num_right += 0
        else:
            pt += 1
            if out_element.item() != CHORD_END and out_element.item() != CHORD_PAD:
                gen_chord = chordInvDic[ str( out_element.item() ) ]

                chord_arr = gen_chord.split(":")
                if len(chord_arr) == 1:
                    out_quality = 1
                elif len(chord_arr) == 2:
                    chordAttrID = chordAttrDic[chord_arr[1]]
                    out_quality = chordAttrID # 0:N, 1:maj ... 13:maj7

                if tgt_emotion_quality[i][out_quality] == 1:
                    num_right += 1
                    

    if(len(tgt_emotion) == 0):
        return 1.0
    
    if(pt == 0):
        return -1
    
    num_right = torch.tensor(num_right, dtype=torch.float32)
    acc = num_right / pt

    return acc

def compute_vevo_correspondence_root_attr(y_root, y_attr, tgt, tgt_emotion, tgt_emotion_prob, emotion_threshold):

    tgt_emotion = tgt_emotion.squeeze()
    tgt_emotion_prob = tgt_emotion_prob.squeeze()

    dataset_root = "./dataset/"
    chordRootInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_root_inv.json")
    chordAttrInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_attr_inv.json")
    chordAttrDicPath = os.path.join( dataset_root, "vevo_meta/chord_attr.json")
    
    chordDicPath = os.path.join( dataset_root, "vevo_meta/chord.json")
    chordInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_inv.json")

    with open(chordRootInvDicPath) as json_file:
        chordRootInvDic = json.load(json_file)
    with open(chordAttrDicPath) as json_file:
        chordAttrDic = json.load(json_file)
    with open(chordAttrInvDicPath) as json_file:
        chordAttrInvDic = json.load(json_file)
    with open(chordDicPath) as json_file:
        chordDic = json.load(json_file)
    with open(chordInvDicPath) as json_file:
        chordInvDic = json.load(json_file)

    softmax = nn.Softmax(dim=-1)

    y_root = torch.argmax(softmax(y_root), dim=-1)
    y_attr = torch.argmax(softmax(y_attr), dim=-1)
    
    y_root = y_root.flatten()
    y_attr = y_attr.flatten()

    tgt = tgt.flatten()
    y = np.empty( len(tgt) )

    y.fill(CHORD_PAD)

    for i in range(len(tgt)):
        if y_root[i].item() == CHORD_ROOT_PAD or y_attr[i].item() == CHORD_ATTR_PAD:
            y[i] = CHORD_PAD
        elif y_root[i].item() == CHORD_ROOT_END or y_attr[i].item() == CHORD_ATTR_END:
            y[i] = CHORD_END
        else:
            chordRoot = chordRootInvDic[str(y_root[i].item())]
            chordAttr = chordAttrInvDic[str(y_attr[i].item())]
            if chordRoot == "N":
                y[i] = 0
            else:
                if chordAttr == "N" or chordAttr == "maj":
                    y[i] = chordDic[chordRoot]
                else:
                    chord = chordRoot + ":" + chordAttr
                    y[i] = chordDic[chord]

    y = torch.from_numpy(y)
    y = y.to(torch.long)
    y = y.to(get_device())
    y = y.flatten()

    num_right = 0
    tgt_emotion_quality = tgt_emotion[:, 0:14]
    pt = 0 
    for i, y_element in enumerate( y ):
        all_zeros = torch.all(tgt_emotion_quality[i] == 0)
        if tgt_emotion[i][-1] == 1 or all_zeros or tgt_emotion_prob[i] < emotion_threshold:
            num_right += 0
        else:
            pt += 1
            if y_element.item() != CHORD_END and y_element.item() != CHORD_PAD:
                gen_chord = chordInvDic[ str( y_element.item() ) ]
                chord_arr = gen_chord.split(":")
                if len(chord_arr) == 1:
                    y_quality = 1
                elif len(chord_arr) == 2:
                    chordAttrID = chordAttrDic[chord_arr[1]]
                    y_quality = chordAttrID # 0:N, 1:maj ... 13:maj7

                if tgt_emotion_quality[i][y_quality] == 1:
                    num_right += 1
                    
    if(len(tgt_emotion) == 0):
        return 1.0
    
    if(pt == 0):
        return -1
    
    num_right = torch.tensor(num_right, dtype=torch.float32)
    acc = num_right / pt
    return acc

def compute_vevo_accuracy_root_attr(y_root, y_attr, tgt):

    dataset_root = "./dataset/"
    chordRootInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_root_inv.json")
    chordAttrInvDicPath = os.path.join( dataset_root, "vevo_meta/chord_attr_inv.json")
    chordDicPath = os.path.join( dataset_root, "vevo_meta/chord.json")
    
    with open(chordRootInvDicPath) as json_file:
        chordRootInvDic = json.load(json_file)
    with open(chordAttrInvDicPath) as json_file:
        chordAttrInvDic = json.load(json_file)
    with open(chordDicPath) as json_file:
        chordDic = json.load(json_file)

    softmax = nn.Softmax(dim=-1)

    y_root = torch.argmax(softmax(y_root), dim=-1)
    y_attr = torch.argmax(softmax(y_attr), dim=-1)
    
    y_root = y_root.flatten()
    y_attr = y_attr.flatten()

    tgt = tgt.flatten()

    mask = (tgt != CHORD_PAD)
    y = np.empty( len(tgt) )
    y.fill(CHORD_PAD)

    for i in range(len(tgt)):
        if y_root[i].item() == CHORD_ROOT_PAD or y_attr[i].item() == CHORD_ATTR_PAD:
            y[i] = CHORD_PAD
        elif y_root[i].item() == CHORD_ROOT_END or y_attr[i].item() == CHORD_ATTR_END:
            y[i] = CHORD_END
        else:
            chordRoot = chordRootInvDic[str(y_root[i].item())]
            chordAttr = chordAttrInvDic[str(y_attr[i].item())]
            if chordRoot == "N":
                y[i] = 0
            else:
                if chordAttr == "N" or chordAttr == "maj":
                    y[i] = chordDic[chordRoot]
                else:
                    chord = chordRoot + ":" + chordAttr
                    y[i] = chordDic[chord]

    y = torch.from_numpy(y)
    y = y.to(torch.long)
    y = y.to(get_device())

    y = y[mask]
    tgt = tgt[mask]

    # Empty
    if(len(tgt) == 0):
        return 1.0

    num_right = (y == tgt)
    num_right = torch.sum(num_right).type(TORCH_FLOAT)

    acc = num_right / len(tgt)
    
    return acc
