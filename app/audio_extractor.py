###################################
## SOON TO BE DEPRECATED MODULE  ##
###################################


import json
import os
import re

import torch
import whisper
from nltk import deprecated
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
import re
from sentence_splitter import SentenceSplitter



class AudioExtractor:
    def __init__(self, whisper_model_name="base"):
        # Initialize the device to use for processing (GPU if available, otherwise CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Audio device: {self.device}")
        # Placeholder for transcription and diarization models, to be loaded later
        self.transcription_model = None
        self.diarization_model = None
        self.whisper_model_name = whisper_model_name
        self.audio_file = None

        # TODO: delete after debugging
        self.cache_files_paths = {'raw_result': 'cache/diarization_raw_result.json',
                                  'merged_result': 'cache/diarization_merged_result.json'}

    @staticmethod
    def __millisec(time_str):
        # Converts a time string in HH:MM:SS format to milliseconds
        hours, minutes, seconds = map(float, time_str.split(":"))
        return int((hours * 3600 + minutes * 60 + seconds) * 1000)

    @staticmethod
    def __timeStr(t):
        # Formats a time in seconds to a string in HH:MM:SS.ff format
        return '{0:02d}:{1:02d}:{2:06.2f}'.format(round(t // 3600),
                                                  round(t % 3600 // 60),
                                                  t % 60)

    @staticmethod
    def __prepare_result(result):
        # Formats transcription results, including timestamps for each segment
        def format_time(seconds):
            # Helper function to format seconds into HH:MM:SS.xxx format
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02}:{minutes:02}:{seconds:06.3f}"

        output = ""  # Initialize output string
        if "segments" in result:
            for segment in result["segments"]:
                start_time = format_time(segment['start'])
                end_time = format_time(segment['end'])
                segment_text = f"[{start_time} --> {end_time}] {segment['text']}\n"
                output += segment_text  # Append each segment's text to the output

        return output

    def __merge_segments(self, diarization):
        # Merges adjacent or overlapping segments with the same speaker ID
        merged_segments = []
        current_speaker = None
        current_start = None
        current_end = None
        end = None

        segment_pattern = re.compile(r'\[ (\d{2}:\d{2}:\d{2}\.\d{3}) -->  (\d{2}:\d{2}:\d{2}\.\d{3})\] \w+ (SPEAKER_\d+)')

        for segment in diarization:
            match = segment_pattern.search(segment)
            if match:
                start, end, speaker = match.groups()
                if speaker == current_speaker:
                    # Extend the current segment if it's the same speaker
                    current_end = end
                    continue
                else:
                    if current_speaker is not None:
                        merged_segments.append(f"[{current_start} --> {current_end}] {current_speaker}")
                    current_speaker = speaker
                    current_start = start
                    current_end = end

        # Add the last segment
        if current_speaker is not None:
            merged_segments.append(f"[{current_start} --> {end}] {current_speaker}")

        return merged_segments

    def __transcribe_audio(self, groups, audio_file):
        # Transcribes audio segments and appends transcription to the segment info
        print(f"Start transcribe audio {audio_file}")
        temp_segment = "audio/temp_segment.wav"  # Temporary file for audio segments
        transcribe_pattern = re.compile(r'\[(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\] (SPEAKER_\d+)')

        audio = AudioSegment.from_wav(audio_file)  # Load the full audio file

        gidx = -1  # Group index
        for line in groups:
            match = transcribe_pattern.search(line)
            if match:
                start, end, _ = match.groups()
                start, end = self.__millisec(start), self.__millisec(end)
                gidx += 1
                # Export the audio segment to a temporary file
                audio[start:end].export(temp_segment, format="wav")
                # Transcribe the segment
                result = self.transcription_model.transcribe(audio=temp_segment, language='en', word_timestamps=True)
                # Append transcription text to the group
                groups[gidx] += "||" + result["text"]

        # Remove the temporary audio segment file
        if os.path.exists(temp_segment):
            os.remove(temp_segment)

        return groups


    def perform_diarization(self, wav_file):
        # Main method to perform diarization and transcription
        print("Diarization has started")

        # Check if the wav_file exists
        if not os.path.exists(wav_file):
            print(f"Error: File {wav_file} not found.")
            return None

        # Load models if they are not already loaded
        if self.transcription_model is None:
            self.transcription_model = whisper.load_model(self.whisper_model_name, device=self.device)
        if self.diarization_model is None:
            self.diarization_model = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1").to(device=self.device)

        # Perform diarization
        with ProgressHook() as hook:
            diarization = self.diarization_model(wav_file, hook=hook)

        # Process and merge diarization segments, then transcribe audio
        #diarization = str(diarization).splitlines()

        # # TODO: delete after debugging
        # with open(self.cache_files_paths['raw_result'], "w", encoding="utf-8") as file:
        #     json.dump(diarization, file)
        #     print(f"Raw diarization data saved in the file: {self.cache_files_paths['raw_result']}")

        # diarization = self.__merge_segments(diarization)

        # # TODO: delete after debugging
        # with open(self.cache_files_paths['merged_result'], "w", encoding="utf-8") as file:
        #     json.dump(diarization, file)
        #     print(f"Raw diarization data saved in the file: {self.cache_files_paths['merged_result']}")

        diarization = self.__transcribe_audio(diarization, wav_file)

        return diarization

    def transcribe_audio(self, wav_file):
        # Transcribes an entire audio file without diarization
        result = self.transcription_model.transcribe(wav_file, language="en", fp16=False, verbose=False)
        return self.__prepare_result(result)
    
    

