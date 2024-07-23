from moviepy.editor import VideoFileClip
import os


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


if "__main__" == __name__:
    # # Audio extraction from the video
    # audio_file = "assets/audios/extracted_audio_C2_English_Conversation.wav"
    # video_file = "assets/videos/C2_English_Conversation.webm"
    
    # if not extract_audio(video_file, audio_file):
    #     print(f"Error: Audio extraction failed for the video file.")
    # else:
    #     print("Audio Extraction completed: ", audio_file)
    #     print

    # Audio extraction from all the videos
    audio_directory = "assets/audios"
    video_directory = "assets/videos"
    extract_all_audios_of_directory(video_directory, audio_directory)