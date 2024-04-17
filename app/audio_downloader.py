import os
import requests
import yt_dlp
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
        ffmpeg_is_local = False

        # Ensure FFmpeg is downloaded before attempting to download audio
        if platform.system() == 'Windows':
            ffmpeg_is_local = self.__download_ffmpeg()

        print(f"Downloading AUDIO... {video_url}")
        # yt-dlp options for downloading audio in the best quality and converting to wav
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': output_filename,
        }

        if ffmpeg_is_local:
            ydl_opts['ffmpeg_location'] = os.path.join(self.ffmpeg_path, self.ffmpeg_v_name + "/bin")

        # Use yt-dlp to download audio from the given URL
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            print(f"Audio saved as {output_filename}")

    def get_video_info(self, video_url):
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(video_url, download=False)

        return info_dict
