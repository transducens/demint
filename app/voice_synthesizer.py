import scipy
from transformers import AutoProcessor, AutoModel
from IPython.display import Audio

import os
import csv
import librosa
import soundfile as sf

from scipy.io import wavfile
import scipy.signal as sps
from io import BytesIO

class Voice_Synthesizer:
    def __init__(self, model_id = "suno/bark"):
        self.__processor = AutoProcessor.from_pretrained(model_id)
        self.__model = AutoModel.from_pretrained(model_id)

        self.__model.config.sample_rate = 24_000

    def file_list(self, dir, ext):
        list = []
        for file in os.listdir(dir):
            if file.endswith(ext):
                list += [os.path.join(dir, file)]
                
        return list

    def read_tsv(self, file_list):
        name = file_list[0]
        dialog = []

        for name in file_list:
            with open(name) as f:
                for line in f:
                    l = line.split('\t')

                    if l[2] == '"student"':
                        if len(l[4].split(" ")) >= 3:
                            dialog += [l[4]]

        print(len(dialog), flush=True)
        return dialog

    def dialog_reader(self, dir, corpus):
        # Adapt to each Corpus. For the time being, it reads a .txt file to extract the dialogs between teacher and student
        lines = []
        file = open(dir, "r")
        for line in file.readlines():
            lines += line
        file.close()

        return lines

    def get_audio(self, conversation, save_dir):
        count = 0
        for dialog in conversation:
            print(count, flush=True)
            print(dialog, flush=True)
            inputs = self.__processor(
                text=dialog,
                return_tensors="pt",
            )

            speech_values = self.__model.generate(**inputs)

            print(self.__model.config.sample_rate, flush=True)
            sampling_rate = self.__model.config.sample_rate
            scipy.io.wavfile.write(os.path.join(save_dir, str(count) + ".wav"), rate = sampling_rate, data=speech_values.cpu().numpy().squeeze())

            """
            sample_rate, clip = wavfile.read((os.path.join(save_dir, str(count) + ".wav")))
            print(sample_rate, flush=True)
            number_of_samples = round(len(clip) * float(16_000) / sample_rate)
            clip = sps.resample(clip, number_of_samples)
            print(clip, flush=True)
            scipy.io.wavfile.write(os.path.join(save_dir, str(count) + ".wav"), rate = sampling_rate, data=clip)
            """
            
            audio_file = os.path.join(save_dir, str(count) + ".wav")
            y, sr = librosa.load(audio_file, sr=None)

            print("sr: ", sr, flush=True)
            print("y: ", y, flush=True)

            y_resampled = librosa.resample(y = y, orig_sr = sr, target_sr = 16000)

            output_audio_file = audio_file
            sf.write(output_audio_file, y_resampled, 16000)

            sample_rate, clip = wavfile.read((os.path.join(save_dir, str(count) + ".wav")))
            print(sample_rate, flush=True)

            count += 1

if __name__ == '__main__':
    voice = Voice_Synthesizer()

    file_list = voice.file_list("/Users/rafael/Desktop/TFM/Transformes/Demint/TSCC", ".tsv")
    print(file_list, flush=True)
    print(len(file_list), flush=True)

    dialog = voice.read_tsv(file_list)
    voice.get_audio(dialog, os.path.join(os.getcwd(), "audio"))
