import os
import argparse
from yt_dlp import YoutubeDL

class AudioDownloaderYTDLP:
    def __init__(self):
        self.video_url = ""
        self.output_directory = "./assets/audios"
        self.output_filename = ""

    def download_audio(self, video_url="", output_filename=""):
        if video_url != "":
            video_url = video_url
        elif self.video_url != "":
            video_url = self.video_url
        else:
            print("No video URL provided.", flush=True)
            return
        output_filename = output_filename if output_filename != "" else self.output_filename
             
        print(f"Downloading VIDEO... {video_url}", flush=True)

        ydl_opts = {
            'format': 'm4a/bestaudio/best', # Best quality audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Extract audio using FFmpeg
                'preferredcodec': 'wav', # Convert audio to mp3
            }],
            'outtmpl': output_filename + '.%(ext)s',  # Output file name and path
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

    # Use pytube(yt) to get information about the video from the given URL
    def get_audio_info(self, video_url=""):
        if video_url != "":
            video_url = video_url
        elif self.video_url != "":
            video_url = self.video_url
        else:
            print("No video URL provided.", flush=True)
            return
        
        ydl_opts = {
            'format': 'best',  # Best quality video and audio
        }
        info = {}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # Extract the video information
        # Create a dictionary to store video information
        video_info = {
            "title": info['title'],
            "author": info['channel'],
            "extension": info['ext'],
            "duration": info['duration'],
            "description": info['description'],
            "views": info['view_count'],
            "publish_date": info['upload_date']
        }

        return video_info


def main(url:str, name:str):
    video_downloader = AudioDownloaderYTDLP()
    #video_downloader.video_url = "https://youtu.be/_Bx_x-gvLw0?si=y2Bi5cw6CizEd5Oa"
    video_downloader.video_url = url
    audio_info = video_downloader.get_audio_info()
    print(audio_info, flush=True)
    name = name if name else audio_info['title']
    video_downloader.output_filename = os.path.join(video_downloader.output_directory, name)
    print("The path is:", video_downloader.output_filename, flush=True)
    video_downloader.download_audio()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Description of your script")

    parser.add_argument("-u", "--url", type=str, help="URL of the video to download", required=True)
    parser.add_argument("-n", "--name", type=str, help="Name set to the downloaded video file", required=False)
    args = parser.parse_args()

    url = args.url
    name = args.name if args.name else ""
    
    main(url, name)
