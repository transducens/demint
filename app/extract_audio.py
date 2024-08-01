from moviepy.editor import VideoFileClip
import os
import argparse

input_directory = "assets/videos"
output_directory = "assets/audios"

def extract_audio(video_file="", audio_file=""):
    if not os.path.exists(video_file):
        print(f"Error: File {video_file} not found.")
        return 0
    
    # Load the video file
    video = VideoFileClip(video_file)
    
    # Extract the audio
    audio = video.audio
    
    # Write the audio to a file
    audio.write_audiofile(audio_file)

    print(f"Audio extraction completed: {audio_file}")

    return 1


def extract_all_audios_of_directory(video_directory="assets/videos", audio_directory="assets/audios"):
    # Loop through the files in the directory
    for video_file in os.listdir(video_directory):
        if video_file[0] == ".":
            continue

        video_path = os.path.join(video_directory, video_file)

        # Check if it's a file (not a directory)
        if os.path.isfile(video_path):
            print(f"Found video file: {video_path}")

            video_name, video_extension = os.path.splitext(video_file)
            audio_path = os.path.join(audio_directory, video_name + ".wav")
            extract_audio(video_path, audio_path)


def get_args():
    parser = argparse.ArgumentParser(description="Extract audio from a video file.")
    parser.add_argument("-vf", "--video_file", type=str, help="Path to where the input video file is located.")
    parser.add_argument("-af", "--audio_file", type=str, help="Path to where the output audio file will be saved.")
    parser.add_argument("-vd", "--video_directory", type=str, help="Path to the directory containing the input video files.")
    parser.add_argument("-ad", "--audio_directory", type=str, help="Path to the directory where the output audio files will be saved.")

    return parser.parse_args()


def main():
    global input_directory, output_directory

    # Audio extraction from all the videos
    audio_directory = input_directory
    video_directory = output_directory
    args = get_args()

    if args.video_file:
        if args.video_directory:
            raise ValueError("Error: Please provide either a video file or a video directory.")
        elif args.audio_file:
            extract_audio(args.video_file, args.audio_file)
        elif args.audio_directory:
            video_file = os.path.basename(args.video_file)
            video_name, video_extension = os.path.splitext(video_file)
            extract_audio(args.video_file, os.path.join(args.audio_directory, video_name + ".wav"))
        else:
            video_file = os.path.basename(args.video_file)
            video_name, video_extension = os.path.splitext(video_file)
            extract_audio(args.video_file, os.path.join(audio_directory, video_name + ".wav"))

    elif args.video_directory:
        if args.audio_directory:
            extract_all_audios_of_directory(args.video_directory, args.audio_directory)
        elif args.audio_file:
            raise ValueError("Error: Please provide a directory to save the audio files.")
        else:
            extract_all_audios_of_directory(args.video_directory, audio_directory)
        
    elif args.audio_file or args.audio_directory:
        raise ValueError("Error: Please provide a video file or a video directory.")

    else:
        extract_all_audios_of_directory(video_directory, audio_directory)


if "__main__" == __name__:
    main()


