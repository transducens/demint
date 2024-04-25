import os
import requests
import pytube as yt
from subprocess import call
import platform

class AudioDownloader:
    def __init__(self):
        # Set the path to the FFmpeg binaries
        self.ffmpeg_path = "./ffmpeg/bin"
        self.ffmpeg_v_name = "ffmpeg-master-latest-win64-gpl"

    def __download_ffmpeg(self):
        try:
            call(["7z", "--help"])
        except FileNotFoundError:
            print("7z is not found")

        try:
            # Try to call FFmpeg to check if it is installed
            call(["ffmpeg", "-version"])
            return False
        except FileNotFoundError:
            # If FFmpeg is not found, print a message indicating it needs to be downloaded
            print("FFmpeg globally is not found, attempting to download locally...")

            # Check if FFmpeg is already installed by trying to call its version
            try:
                call([os.path.join(self.ffmpeg_path, self.ffmpeg_v_name + "/bin/ffmpeg.exe"), "-version"])
                print("FFmpeg is already installed.")
                return True
            except FileNotFoundError:
                print("Downloading FFmpeg...")
                # Download FFmpeg from the GitHub releases
                url = f"https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/{self.ffmpeg_v_name}.zip"
                response = requests.get(url, stream=True)
                zip_path = "ffmpeg.zip"

                # Save the downloaded zip file
                with open(zip_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=128):
                        file.write(chunk)

                # Use 7z to unpack the zip file
                call(["7z", "x", zip_path, f"-o{self.ffmpeg_path}"])
                # Remove the zip file after unpacking
                os.remove(zip_path)
                print("FFmpeg downloaded and installed.")
                return True

    def download_audio(self, video_url, output_filename="audio/extracted_audio.wav"):
        print(f"Downloading AUDIO... {video_url}")

        # Use pytube(yt) to download audio from the given URL
        yt_handler =  yt.YouTube(video_url)
        # Get the best audio stream
        audio_stream = yt_handler.streams.filter(only_audio=True).first()
        # Download the audio
        audio_stream.download(filename=output_filename)
        print(f"Audio saved as {output_filename}")

    # Use pytube(yt) to get information about the video from the given URL
    def get_video_info(self, video_url):
            yt_handler = yt.YouTube(video_url)
            # Extract the video information
            # Create a dictionary to store video information
            video_info = {
                "title": yt_handler.title,
                "author": yt_handler.author,
                "duration": yt_handler.length,
                "thumbnail_url": yt_handler.thumbnail_url,
                "description": yt_handler.description,
                "views": yt_handler.views,
                "publish_date": yt_handler.publish_date
            }

            return video_info
