# import IPython
from video2music import Video2music

# input_video = ""
input_video = 'NoSound_test_video.mp4'

print("Generate music for video: " + input_video)
input_primer = "C Am F G"
input_key = "C major"

video2music = Video2music(device='cpu', sf2_file='C:\Windows\System32\Video2Music\soundfonts\default_sound_font.sf2')
output_filename = video2music.generate(input_video, input_primer, input_key)
