import torch
import os
import re
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment


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

def cut_audio_segment(audio_path, init_times, end_times, output_directory):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)

    audio_name_with_extension = os.path.basename(audio_path)
    audio_name, audio_extension = os.path.splitext(audio_name_with_extension)
    output_directory = f"{output_directory}{audio_name}/"
    os.makedirs(output_directory, exist_ok=True)

    for i, (start_time, end_time) in enumerate(zip(init_times, end_times)):
        # Extract the segment
        segment = audio[start_time:end_time]
        
        # Save the segment
        segment_path = os.path.join(output_directory, f"{i}{audio_extension}")
        segment.export(segment_path, format="wav")
        print(f"Segment {i} saved from {start_time} to {end_time} milliseconds.")

def perform_diarization(audio_file, output_directory, device):
    # Main method to perform diarization and transcription
    print("Diarization has started: ", audio_file)

    # Check if the wav_file exists
    if not os.path.exists(audio_file):
        print(f"Error: File {audio_file} not found.")
        return None

    # Load model
    diarization_model = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    if not diarization_model:
        print("Error: Diarization model could not be loaded.")
        return None
    
    diarization_model = diarization_model.to(device=device)

    # diarization = pipeline("audio.wav", num_speakers=2)
    # diarization = pipeline("audio.wav", min_speakers=2, max_speakers=5)

    # Perform diarization while monitoring progress
    with ProgressHook() as hook:
        diarization = diarization_model(audio_file, hook=hook)

    # Split the original audio into segments
    diarization = str(diarization).splitlines()

    # Extract the duration of each segment in milliseconds
    init_times, end_times, durations = extract_duration_in_milliseconds(diarization)

    # Cut the audio segments
    cut_audio_segment(audio_file, init_times, end_times, output_directory)

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


if __name__ == '__main__':
    # Initialize the device to use for processing (GPU if available, otherwise CPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Audio device: {device}")

    audio_file = "assets/audios/C2_English_Conversation.wav"
    output_directory = "cache/diarized_audios/"
    perform_diarization(audio_file, device, output_directory)