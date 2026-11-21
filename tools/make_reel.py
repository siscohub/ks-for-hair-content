"""Make an Instagram Reel (1080x1920 MP4, ~9 s) from two story-size images:
A = title only (HIDE_BODY=1 render), B = full design. Slow zoom + crossfade + silent audio track.
Usage: python3 make_reel.py A.png B.png out.mp4
"""
import subprocess, sys
a, b, out = sys.argv[1:4]
fc = ("[0:v]scale=1080:1920,format=yuv420p,zoompan=z='1+0.0004*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=1080x1920:fps=30,fade=t=in:st=0:d=0.6[v0];"
      "[1:v]scale=1080:1920,format=yuv420p,zoompan=z='1.0+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=210:s=1080x1920:fps=30[v1];"
      "[v0][v1]xfade=transition=fade:duration=0.8:offset=2.4,format=yuv420p[v]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", "3", "-i", a, "-loop", "1", "-t", "7", "-i", b,
                "-f", "lavfi", "-t", "9.2", "-i", "anullsrc=r=44100:cl=stereo",
                "-filter_complex", fc, "-map", "[v]", "-map", "2:a", "-shortest",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
