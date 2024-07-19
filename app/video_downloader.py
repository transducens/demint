import os
import requests
import pytube as yt
from subprocess import call

class VideoDownloader:
    def __init__(self):
        self.video_url = ""
        self.output_filename = "./assets/video/extracted_video.mp4"

    def download_video(self, video_url="", output_filename=""):
        if video_url != "":
            video_url = video_url
        elif self.video_url != "":
            video_url = self.video_url
        else:
            print("No video URL provided.")
            return
        output_filename = output_filename if output_filename != "" else self.output_filename
             
        print(f"Downloading VIDEO... {video_url}")

        # Use pytube(yt) to download video from the given URL
        yt_handler =  yt.YouTube(video_url)
        # Get the best video stream
        video_stream = yt_handler.streams.first()
        # Download the video
        video_stream.download(filename=output_filename)
        print(f"Video saved as {output_filename}")

    # Use pytube(yt) to get information about the video from the given URL
    def get_video_info(self, video_url=""):
        if video_url != "":
            video_url = video_url
        elif self.video_url != "":
            video_url = self.video_url
        else:
            print("No video URL provided.")
            return

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


if __name__ == "__main__":
    video_downloader = VideoDownloader()
    video_downloader.video_url = "https://www.youtube.com/watch?v=_Bx_x-gvLw0"
    video_downloader.output_filename = "./assets/video/c2_exam_video.mp4"
    video_info = video_downloader.get_video_info()
    print(video_info)
    video_downloader.download_video()
    
    