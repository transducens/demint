from transformers import WhisperForConditionalGeneration, pipeline
from transformers import WhisperTokenizer, WhisperFeatureExtractor
from transformers import WhisperForConditionalGeneration
from peft import PeftModel, PeftConfig

import torch
import os
import librosa
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

    model = PeftModel.from_pretrained(model, peft_model_id, language=language)

    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-large-v3", language="english", task="transcribe")
    aaa = WhisperFeatureExtractor.from_pretrained("openai/whisper-large-v3", language=language)
    pipe = pipeline(model=model, tokenizer=tokenizer, feature_extractor=aaa, task="automatic-speech-recognition", device=device)

    f = os.listdir("cache/diarized_audios")
    for y in f:
        if not os.path.isdir(os.path.join("cache", "diarized_transcripts", y)):
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

            print(x)
            if audio.shape[0] > 7000:
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

        with open(os.path.join("cache", "diarized_transcripts", y, y + '.json'), 'w') as f:
            json.dump(content, f) 

if __name__ == '__main__':
    main()