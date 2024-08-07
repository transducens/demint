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

def transcribe(audio, pipe):
    p = pipe(audio, return_timestamps=False)
    text = p["text"]
    return text

def main():
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    peft_model_id = "LoRA_Test/checkpoint-5000/adapter_model" # Use the same model ID as before.
    language = "en"
    task = "transcribe"
    peft_config = PeftConfig.from_pretrained(peft_model_id)
    model = WhisperForConditionalGeneration.from_pretrained(
      peft_config.base_model_name_or_path, load_in_8bit=False)

    model = PeftModel.from_pretrained(model, peft_model_id)

    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-large-v3", language="english", task="transcribe")
    aaa = WhisperFeatureExtractor.from_pretrained("openai/whisper-large-v3")
    pipe = pipeline(model=model, tokenizer=tokenizer, feature_extractor=aaa, task="automatic-speech-recognition", device=device)

    f = os.listdir("cache/diarized_audios")
    for y in f:
        if y[0] == ".":
            continue
        if not os.path.isdir(os.path.join("cache", "diarized_transcripts")):
            os.mkdir(os.path.join("cache", "diarized_transcripts", y))

        dir = os.path.join("cache/diarized_audios", y)
        ff = os.listdir(dir)
        content = []
        start_time = 0
        ff.sort(key=lambda x: int(x.split('_')[0]))
        for x in ff:
            name = x.split('.')[0]
            speaker = name.split('_')[1]

            audio_file = os.path.join('cache', 'diarized_audios', y, x)
            yyy, sr = librosa.load(audio_file, sr=None)
            waveform = librosa.resample(y = yyy, orig_sr = sr, target_sr = 16000)
            output_audio_file = os.path.join('cache', 'diarized_audios', y, x)
            sf.write(output_audio_file, waveform, 16000)

            samplerate, audio = wavfile.read(os.path.join('cache', 'diarized_audios', y, x))
            data = []
            """for numpyx in audio:
                for numpyy in numpyx:
                    data.append(numpyy)"""

            #audio = np.array(data)
            print(x)
            print(audio)
            print(audio.shape)
            print(samplerate)
            print(type(audio))
            transcript = transcribe(audio, pipe)
            end_time = start_time + librosa.get_duration(filename=(os.path.join('cache', 'diarized_audios', y, x)))
            print(transcript)
            
            start = str(datetime.timedelta(seconds=start_time))
            end = str(datetime.timedelta(seconds=end_time))

            result = "[" + start + "-->" + end + "] SPEAKER_" + speaker +"|| " + transcript

            start_time = end_time

            content.append(result)   

        with open(os.path.join("cache", "diarized_transcripts", y + '.json'), 'w') as f:
            json.dump(content, f) 


def transcript_audio_of_directory(
        diarized_directory="cache/diarized_transcripts", 
        sentence_collection_directory="cache/raw_sorted_sentence_collection", 
    ):
    # Loop through the files in the directory
    for diarized_transcript_file in os.listdir(diarized_directory):
        if diarized_transcript_file[0] == ".":
            continue

        diarized_transcript_path = os.path.join(diarized_directory, diarized_transcript_file)
        sentence_collection_path = os.path.join(sentence_collection_directory, diarized_transcript_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(diarized_transcript_path):
            print(f"Found diarized transcript file: {diarized_transcript_path}")

            #prepare_sorted_sentence_collection(file_manager, diarized_transcript_path, sentence_collection_path)



if __name__ == '__main__':
    main()