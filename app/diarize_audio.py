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
            # must be silent for _ miliseconds
            min_silence_len=1000,

            # consider it silent if quieter than ... dBFS
            silence_thresh = silence_threshold,

            # if True, keeps the detected silence at the beginning and end of the chunk
            # default only 100 ms 
            # When the length of the silence is less than the keep_silence duration it is split evenly between the preceding and following non-silent segments.
            keep_silence=True
        )

        ready = all(len(chunk) <= max_duration_milliseconds for chunk in audio_chunks)


    # If there are too small chunks, merge them
    #result = []
    #current_sum = 0
    #for chunk in audio_chunks:
    #    if current_sum + len(chunk) <= max_duration_milliseconds:
    #        current_sum += len(chunk)
    #    else:
    #        result.append(current_sum)
    #        current_sum = len(chunk)
    #if current_sum > 0:
    #    result.append(current_sum)
    #audio_chunk_lengths = result

    # If there are too small chunks, merge them (version 2)
    audio_chunk_lengths = group_durations([len(chunk) for chunk in audio_chunks])

    return audio_chunk_lengths

def cut_audio_segment(audio_path, diarized_segments, output_path):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)

    audio_name_with_extension = os.path.basename(audio_path)
    audio_name, audio_extension = os.path.splitext(audio_name_with_extension)
    os.makedirs(output_path, exist_ok=True)
    audio_index = 0

    for i, (start_time, end_time, speaker_id) in enumerate(diarized_segments):
        # Extract the segment
        segment = audio[start_time:end_time]
        
        time_treshold = 0   # 300
        if end_time - start_time < time_treshold:
            print(f"Ignored segment, duration less than {time_treshold} miliseconds:")
            continue

        # If the segment is longer than 29 seconds, divide it into smaller segments
        # and save them separately
        elif end_time - start_time > 29000:
            print("Segment duration longer than 29 seconds:", end_time - start_time)
            audio_chunk_lengths = divide_long_segment(segment)
            sub_start_time = 0
            for length in audio_chunk_lengths:
                if length < time_treshold:
                    print(f"Ignored segment, duration less than {time_treshold} miliseconds:")
                    continue
                sub_end_time = sub_start_time + length
                subsegment = segment[sub_start_time:sub_end_time]
                subsegment_path = os.path.join(output_path, f"{audio_index}_{speaker_id}{audio_extension}")
                subsegment.export(subsegment_path, format="wav")
                print(f"Subsegment {audio_index} saved from {sub_start_time} to {sub_end_time} milliseconds. With a duration of {length} milliseconds.")
                audio_index += 1
                sub_start_time = sub_end_time
        else:
            # Save the segment
            segment_path = os.path.join(output_path, f"{audio_index}_{speaker_id}{audio_extension}")
            segment.export(segment_path, format="wav")
            print(f"Segment {audio_index} saved from {start_time} to {end_time} milliseconds. With a duration of {end_time - start_time} milliseconds.")
            audio_index += 1

# Joins the times of the segments that belong to the same speaker and are consecutive
def join_audios_same_speaker(audio_segments:list):
    result_audio_segments = []
    temp_speaker_id = None
    for i, (init_time, end_time, speaker_id) in enumerate(audio_segments):
        if i > 0 and init_time > result_audio_segments[-1][0] and end_time < result_audio_segments[-1][1]:
            continue
        elif i > 0 and (end_time - init_time) < 300:
            temp_speaker_id = result_audio_segments[-1][2]
            result_audio_segments[-1] = (result_audio_segments[-1][0], end_time, result_audio_segments[-1][2])  # Check this
        elif speaker_id == temp_speaker_id:
            result_audio_segments[-1] = (result_audio_segments[-1][0], end_time, speaker_id)
        else:
            result_audio_segments.append((init_time, end_time, speaker_id))
            temp_speaker_id = speaker_id

    return result_audio_segments

# Algorithm that finds the shortest duration and appends it to the consecutive shortest duration segment, 

# Optimizes the duration of the segments so they are not very long nor very short
def group_durations(durations):
    max_duration = 29000

    # Initialize segments as just duration values
    segments = durations.copy()
    ignore_list = []

    # Main loop to merge segments
    while True:
        # Find the shortest segment not in the ignore list
        sorted_segments = sorted(
            [(i, segment) for i, segment in enumerate(segments) if i not in ignore_list],
            key=lambda x: x[1]
        )

        # If there are fewer than 2 segments, we can't merge anymore
        if len(sorted_segments) < 2:
            break

        # Get the two shortest segments
        shortest_index, shortest_duration = sorted_segments[0]

        # Try to merge the shortest with the next shortest
        if shortest_index == 0:
            next_shortest_index = shortest_index + 1
            next_shortest_duration = segments[next_shortest_index]
        elif shortest_index == len(segments) - 1:
            next_shortest_index = shortest_index - 1
            next_shortest_duration = segments[next_shortest_index]
        elif segments[shortest_index - 1] < segments[shortest_index + 1]:
            next_shortest_index = shortest_index - 1
            next_shortest_duration = segments[next_shortest_index]
        else:
            next_shortest_index = shortest_index + 1
            next_shortest_duration = segments[next_shortest_index]
            
        if shortest_duration + next_shortest_duration <= max_duration:
            # Merge the segments by summing the durations
            merged_duration = shortest_duration + next_shortest_duration
            segments[shortest_index] = merged_duration
            del segments[next_shortest_index]

            # Clear the ignore list after a successful merge
            ignore_list.clear()
        else:
            # If merging is not possible, add the index to the ignore list
            ignore_list.append(shortest_index)

        # Stop if half of the total durations have been processed
        if len(ignore_list) >= len(durations) // 2:
            break

    return segments



def perform_diarization(audio_file, output_path, device):
    # Main method to perform diarization and transcription
    print("Diarization has started:", audio_file)

    # Check if the wav_file exists
    if not os.path.exists(audio_file):
        print(f"Error: File {audio_file} not found.")
        return None

    # If the output directory already exists, remove it first
    if os.path.exists(output_path):
        print(f"Removing existing directory: {output_path} before creating a new one.")
        os.system(f"rm -rf {output_path}")

    # Load model
    diarization_model = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0")
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

    #diarized_segments = join_audios_same_speaker( list(zip(init_times, end_times, speaker_ids)) )
    diarized_segments = join_audios_same_speaker( list(zip(init_times, end_times, speaker_ids)) )


    # Cut the audio segments
    cut_audio_segment(audio_file, diarized_segments, output_path)

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

            audio_name, _ = os.path.splitext(audio_file)
            output_path = os.path.join(cache_directory, audio_name)
            perform_diarization(audio_path, output_path, device)


def get_args():
    parser = argparse.ArgumentParser(description="Diarize an audio file or a directory of audio files.")
    parser.add_argument("-af", "--audio_file", type=str, help="Path to where the input audio file is located.")
    parser.add_argument("-ad", "--audio_directory", type=str, help="Path to the input directory containing the audio files.")
    parser.add_argument("-sd", "--segments_directory", type=str, help="Path to the output directory where all the diarized audios will be saved.")

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
            output_path = os.path.join(args.segments_directory, audio_name)
            perform_diarization(args.audio_file, output_path, device)
        else:
            audio_file = os.path.basename(args.audio_file)
            audio_name, audio_extension = os.path.splitext(audio_file)
            output_path = os.path.join(cache_directory, audio_name)
            perform_diarization(args.audio_file, output_path, device)

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