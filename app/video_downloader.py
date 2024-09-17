import os
import pytube as yt
import argparse
from yt_dlp import YoutubeDL

class VideoDownloaderPytube:
    def __init__(self):
        self.video_url = ""
        self.output_directory = "./assets/videos"
        self.output_filename = ""

    def download_video(self, video_url="", output_filename=""):
        if video_url:
            self.video_url = video_url
        elif not self.video_url:
            print("No video URL provided.")
            return
        output_filename = output_filename if output_filename != "" else self.output_filename
             
        print(f"Downloading VIDEO... {self.video_url}")

        # Use pytube(yt) to download video from the given URL
        yt_handler =  yt.YouTube(self.video_url)
        # Get the best video stream
        video_stream = yt_handler.streams.first()
        # Download the video
        video_stream.download(filename=output_filename)
        print(f"Video saved as {output_filename}")

    # Use pytube(yt) to get information about the video from the given URL
    def get_video_info(self, video_url=""):
        if video_url:
            self.video_url = video_url
        elif not self.video_url:
            print("No video URL provided.")
            return

        yt_handler = yt.YouTube(self.video_url)
        # Extract the video information
        # Create a dictionary to store video information
        video_info = {
            "title": yt_handler.title,
            "author": yt_handler.author,
            "extension": "avi",
            "duration": yt_handler.length,
            "description": yt_handler.description,
            "views": yt_handler.views,
            "publish_date": yt_handler.publish_date
        }

        return video_info
    

class VideoDownloaderYTDLP:
    def __init__(self):
        self.video_url = ""
        self.output_directory = "./assets/videos"
        self.output_filename = ""

    def download_video(self, video_url="", output_filename=""):
        if video_url:
            self.video_url = video_url
        elif not self.video_url:
            print("No video URL provided.")
            return
        output_filename = output_filename if output_filename != "" else self.output_filename
             
        print(f"Downloading VIDEO... {self.video_url}")

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Best quality video and audio
            'outtmpl': output_filename,  # Output file name and path
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.video_url])

    # Use pytube(yt) to get information about the video from the given URL
    def get_video_info(self, video_url=""):
        if video_url:
            self.video_url = video_url
        elif not self.video_url:
            print("No video URL provided.")
            return
        
        ydl_opts = {
            'format': 'best',  # Best quality video and audio
        }
        info = {}
        with YoutubeDL() as ydl:
            info = ydl.extract_info(self.video_url, download=False)

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
    video_downloader = VideoDownloaderPytube()
    #video_downloader.video_url = "https://youtu.be/_Bx_x-gvLw0?si=y2Bi5cw6CizEd5Oa"
    video_downloader.video_url = url

    video_info = video_downloader.get_video_info()
    print(video_info)
    
    name = name if name else video_info['title']
    video_downloader.output_filename = os.path.join(video_downloader.output_directory, name + '.' + video_info['extension'])
    print("The path is:", video_downloader.output_filename)
    
    video_downloader.download_video()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Description of your script")

    parser.add_argument("-u", "--url", type=str, help="URL of the video to download", required=True)
    parser.add_argument("-n", "--name", type=str, help="Name set to the downloaded video file", required=False)
    args = parser.parse_args()

    url = args.url
    name = args.name if args.name else ""
    
    main(url, name)

    
    