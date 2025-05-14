# from pytube import YouTube
from pytubefix import YouTube

# Download video from youtube
youtube_link = 'https://www.youtube.com/watch?v=75IMChOtf9s'
yt = YouTube(youtube_link)
yt.streams.get_highest_resolution().download()

# =========================================
video_name = 'The Show Must Go On  Hazbin Hotel  Prime Video.mp4'
no_sound_video_name = "NoSound_" + video_name

from moviepy.editor import *

clip = VideoFileClip(video_name)

max_duration = 300 #in seconds
if clip.duration > 300:
    clip = clip.subclip(0, max_duration)

input_video_path = video_name
output_video_path = no_sound_video_name # input for testing model

video = VideoFileClip(input_video_path)
# Delete sound
video_no_sound = video.set_audio(None)
# Save video
video_no_sound.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
