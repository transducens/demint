import torch
import os
import re
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
from pydub.silence import split_on_silence
import librosa
import numpy as np
import argparse


input_directory = "assets/audios"
output_directory = "cache/diarized_audios"


def time_to_milliseconds(time_str):
    """Convert HH:MM:SS.sss format to milliseconds."""
    h, m, s = time_str.split(':')
    s, ms = s.split('.')
    total_milliseconds = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
    return total_milliseconds

def extract_duration_in_milliseconds(strings):
    durations_list = []
    init_milliseconds_list = []
    end_milliseconds_list = []

    for string in strings:
        # Extract the times using regex
        match = re.search(r'\[\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\]', string)
        if match:
            init_time_str, end_time_str = match.groups()

            # Convert time to milliseconds
            init_milliseconds = time_to_milliseconds(init_time_str)
            end_milliseconds = time_to_milliseconds(end_time_str)

            # Append the times to the list
            init_milliseconds_list.append(init_milliseconds)
            end_milliseconds_list.append(end_milliseconds)

            # Calculate the difference in milliseconds
            difference = end_milliseconds - init_milliseconds
            durations_list.append(difference)
        else:
            raise ValueError("Time string format is incorrect")
    
    return init_milliseconds_list, end_milliseconds_list, durations_list

def extract_speaker_id(strings):
    speaker_id_list = []

    for string in strings:
        # Extract the speaker ID using regex
        match = re.search(r'SPEAKER_(\d+)', string)
        if match:
            speaker_id = match.group(1)
            speaker_id_list.append(speaker_id)
        else:
            raise ValueError("Speaker ID format is incorrect")
    
    return speaker_id_list

# Segments longer than 29 seconds will be divided into smaller segments
def divide_long_segment(audio_segment:AudioSegment):
    sound_file = audio_segment  # Maybe neede
    silence_threshold = -55
    max_duration_milliseconds = 29000
    
    # While all chunks are not less than 29 seconds, the threshold is increased by 5 (shorter chunks)
    ready = False
    while not ready:
        silence_threshold += 5
        print("Treshold:", silence_threshold)

        # Split the original audio into chunks
        audio_chunks = split_on_silence(sound_file, 
            # must be silent for at least half a second
            min_silence_len=1000,

            # consider it silent if quieter than ... dBFS
            silence_thresh = silence_threshold,

            # Add some silence at the beginning and end of the chunk
            keep_silence=True
        )

        ready = all(len(chunk) <= max_duration_milliseconds for chunk in audio_chunks)


    # If there are too small chunks, merge them
    result = []
    current_sum = 0
    for chunk in audio_chunks:
        if current_sum + len(chunk) <= max_duration_milliseconds:
            current_sum += len(chunk)
        else:
            result.append(current_sum)
            current_sum = len(chunk)
    if current_sum > 0:
        result.append(current_sum)
    audio_chunk_lengths = result

    return audio_chunk_lengths

def cut_audio_segment(audio_path, init_times, end_times, speaker_ids, output_directory):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)

    audio_name_with_extension = os.path.basename(audio_path)
    audio_name, audio_extension = os.path.splitext(audio_name_with_extension)
    output_directory = f"{output_directory}/{audio_name}/"
    os.makedirs(output_directory, exist_ok=True)
    audio_index = 0

    for i, (start_time, end_time) in enumerate(zip(init_times, end_times)):
        # Extract the segment
        segment = audio[start_time:end_time]
        
        if end_time - start_time < 1000:
            print("Ignored segment, duration less than 1 second:", end_time - start_time)
            continue
        # If the segment is longer than 29 seconds, divide it into smaller segments
        # and save them separately
        elif end_time - start_time > 29000:
            print("Segment duration longer than 29 seconds:", end_time - start_time)
            audio_chunk_lengths = divide_long_segment(segment)
            sub_start_time = 0
            for sub_i, length in enumerate(audio_chunk_lengths):
                if length < 1000:
                    print("Ignored subsegment duration less than 1 second:", length)
                    continue
                sub_end_time = sub_start_time + length
                subsegment = segment[sub_start_time:sub_end_time]
                subsegment_path = os.path.join(output_directory, f"{audio_index}_{speaker_ids[i]}{audio_extension}")
                subsegment.export(subsegment_path, format="wav")
                print(f"Subsegment {audio_index} saved from {sub_start_time} to {sub_end_time} milliseconds.")
                audio_index += 1
                sub_start_time = sub_end_time
        else:
            # Save the segment
            segment_path = os.path.join(output_directory, f"{audio_index}_{speaker_ids[i]}{audio_extension}")
            segment.export(segment_path, format="wav")
            print(f"Segment {audio_index} saved from {start_time} to {end_time} milliseconds.")
            audio_index += 1


def perform_diarization(audio_file, output_directory, device):
    # Main method to perform diarization and transcription
    print("Diarization has started:", audio_file)

    # Check if the wav_file exists
    if not os.path.exists(audio_file):
        print(f"Error: File {audio_file} not found.")
        return None

    # If the output directory already exists, remove it first
    if os.path.exists(output_directory):
        print(f"Removing existing directory: {output_directory} before creating a new one.")
        os.system(f"rm -rf {output_directory}")

    # Load model
    diarization_model = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    if not diarization_model:
        print("Error: Diarization model could not be loaded.")
        return None
    
    diarization_model = diarization_model.to(device=device)

    # Example of diarization with a fixed number of speakers
    # diarization = pipeline("audio.wav", num_speakers=2)
    # diarization = pipeline("audio.wav", min_speakers=2, max_speakers=5)

    # Perform diarization while monitoring progress
    with ProgressHook() as hook:
        diarization = diarization_model(audio_file, hook=hook)

    # Split the original audio into segments
    diarization = str(diarization).splitlines()

    # Extract the duration of each segment in milliseconds
    init_times, end_times, durations = extract_duration_in_milliseconds(diarization)
    speaker_ids = extract_speaker_id(diarization)

    # Cut the audio segments
    cut_audio_segment(audio_file, init_times, end_times, speaker_ids, output_directory)

    # for duration in durations:
    #     if duration > 29500:
    #         print(duration)

    print("Diarization has completed.")

    return diarization

def perform_diarization_of_directory(audio_directory="assets/audios", cache_directory="cache/diarized_audios", device="cpu"):
    # Loop through the files in the directory
    for audio_file in os.listdir(audio_directory):
        if audio_file[0] == ".":
            continue

        audio_path = os.path.join(audio_directory, audio_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(audio_path):
            print(f"Found audio file: {audio_path}")

            perform_diarization(audio_path, cache_directory, device)


def get_args():
    parser = argparse.ArgumentParser(description="Diarize an audio file or a directory of audio files.")
    parser.add_argument("-af", "--audio_file", type=str, help="Path to where the input audio file is located.")
    parser.add_argument("-ad", "--audio_directory", type=str, help="Path to the directory containing the input audio files.")
    parser.add_argument("-sd", "--segments_directory", type=str, help="Path to the directory where the output audio segments will be saved.")

    return parser.parse_args()
    
    
def main():
    global input_directory, output_directory

    # Diarizaton of the audio file
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Audio device: {device}")
    audio_directory = input_directory
    cache_directory = output_directory
    args = get_args()

    if args.audio_file:
        if args.audio_directory:
            raise ValueError("Error: Please provide either an audio file or an audio directory.")
        elif args.segments_directory:
            audio_file = os.path.basename(args.audio_file)
            audio_name, audio_extension = os.path.splitext(audio_file)
            perform_diarization(args.audio_file, args.segments_directory, device)
        else:
            perform_diarization(args.audio_file, cache_directory, device)

    elif args.audio_directory:
        if args.segments_directory:
            perform_diarization_of_directory(args.audio_directory, args.segments_directory, device)
        else:
            perform_diarization_of_directory(args.audio_directory, cache_directory, device)
        
    elif args.segments_directory:
        raise ValueError("Error: Please provide an audio file or an audio directory.")

    else:
        perform_diarization_of_directory(audio_directory, cache_directory, device)


if __name__ == '__main__':
    main()