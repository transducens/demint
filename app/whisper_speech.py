from transformers import WhisperForConditionalGeneration, pipeline
import csv
from transformers import WhisperTokenizer, WhisperFeatureExtractor
from transformers import WhisperForConditionalGeneration
from peft import PeftModel, PeftConfig

import torch
import os
import re
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
from pydub.silence import split_on_silence
import librosa
import numpy as np
import datetime
import json
from scipy.io import wavfile
import soundfile as sf
import argparse


input_directory = "./cache/diarized_audios"
output_directory = "./cache/diarized_transcripts"


def transcribe(audio, pipe):
    p = pipe(audio, return_timestamps=False)
    text = p["text"]
    return text

def transcribe_audio(input_path, output_path, pipe):
    print(f"Starting to transcribe audio files of {input_path} and saving the transcript to {output_path} ")

    if not os.path.isdir(input_path):
        print(f"Failed to open {input_path}. It is not a directory.")
        return

    ff = os.listdir(input_path)
    content = []
    start_time = 0
    ff.sort(key=lambda x: int(x.split('_')[0]))
    for x in ff:
        name = x.split('.')[0]
        speaker = name.split('_')[1]

        audio_file = os.path.join(input_path, x)
        yyy, sr = librosa.load(audio_file, sr=None)
        waveform = librosa.resample(y = yyy, orig_sr = sr, target_sr = 16000)
        output_audio_file = os.path.join(input_path, x)
        sf.write(output_audio_file, waveform, 16000)

        samplerate, audio = wavfile.read(os.path.join(input_path, x))
        data = []
        """for numpyx in audio:
            for numpyy in numpyx:
                data.append(numpyy)"""

        #audio = np.array(data)
        print(x)
        #print(audio)
        #print(audio.shape)
        #print(samplerate)
        #print(type(audio))
        transcript = transcribe(audio, pipe)
        end_time = start_time + librosa.get_duration(filename=(os.path.join(input_path, x)))
        print(transcript)
        
        start = str(datetime.timedelta(seconds=start_time))
        end = str(datetime.timedelta(seconds=end_time))

        result = "[" + start + "-->" + end + "] SPEAKER_" + speaker +"|| " + transcript

        start_time = end_time

        content.append(result)   

    with open(os.path.join(output_path), 'w') as f:
        json.dump(content, f) 
    

def transcribe_audio_of_all_directory(
        all_diarized_audios_dir="cache/diarized_audios", 
        diarized_transcript_dir="cache/diarized_transcripts",
        pipe=None, 
    ):

    # Loop through the files in the directory
    for diarized_audio_file in os.listdir(all_diarized_audios_dir):
        if diarized_audio_file[0] == ".":
            continue

        diarized_audio_path = os.path.join(all_diarized_audios_dir, diarized_audio_file)
        diarized_transcript_path = os.path.join(diarized_transcript_dir, diarized_audio_file)

        # Check if it's a directory and not a file
        if os.path.isdir(diarized_audio_path):
            print(f"Found diarized audio directory: {diarized_audio_path}")

            transcribe_audio(diarized_audio_path, diarized_transcript_path + '.json', pipe)


def get_args():
    parser = argparse.ArgumentParser(description="Transcribe the audio files of a directory.")
    parser.add_argument("-ad", "--audio_directory", type=str, help="Path to where the audio input directory of is located.")
    parser.add_argument("-tf", "--transcript_file", type=str, help="Path to where the output transcript file will be saved.")
    parser.add_argument("-aad", "--all_audios_directory", type=str, help="Path to the directory containing the input audio directories.")
    parser.add_argument("-td", "--transcript_directory", type=str, help="Path to the directory where the output transcript files will be saved.")

    return parser.parse_args()

def main():
    global input_directory, output_directory

    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    peft_model_id = "LoRA_Test/checkpoint-5000/adapter_model" # Use the same model ID as before.
    peft_config = PeftConfig.from_pretrained(peft_model_id)
    model = WhisperForConditionalGeneration.from_pretrained(
      peft_config.base_model_name_or_path, load_in_8bit=False)

    model = PeftModel.from_pretrained(model, peft_model_id)
    model.generation_config.language = "<|en|>"
    model.generation_config.task = "transcribe"

    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-large-v3", task="transcribe")
    feature_extractor = WhisperFeatureExtractor.from_pretrained("openai/whisper-large-v3")
    pipe = pipeline(model=model, tokenizer=tokenizer, feature_extractor=feature_extractor, task="automatic-speech-recognition", device=device)

    all_diarized_audios_dir = input_directory
    diarized_transcript_dir = output_directory
    args = get_args()

    if args.audio_directory:
        if args.all_audios_directory:
            raise ValueError("Error: Please provide either an audio directory or a directory of all audio directories.")
        elif args.transcript_file:
            transcribe_audio(args.audio_directory, args.transcript_file, pipe)
        elif args.transcript_directory:
            audio_name = os.path.basename(args.audio_directory)
            transcribe_audio(args.audio_directory, os.path.join(args.transcript_directory, audio_name + '.json'), pipe)
        else:
            audio_name = os.path.basename(args.audio_directory)
            transcribe_audio(args.audio_directory, os.path.join(diarized_transcript_dir, audio_name + '.json'), pipe)

    elif args.all_audios_directory:
        if args.transcript_directory:
            transcribe_audio_of_all_directory(args.all_audios_directory, args.transcript_directory, pipe)
        elif args.transcript_file:
            raise ValueError("Error: Please provide a directory to save the transcript files.")
        else:
            transcribe_audio_of_all_directory(args.all_audios_directory, diarized_transcript_dir, pipe)
        
    elif args.transcript_directory or args.transcript_file:
        raise ValueError("Error: Please provide a video file or a video directory.")

    else:
        transcribe_audio_of_all_directory(all_diarized_audios_dir, diarized_transcript_dir, pipe)


if __name__ == '__main__':
    main()