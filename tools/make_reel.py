"""Make an Instagram/TikTok Reel (1080x1920 MP4, ~9 s) from two story-size images:
A = title only (HIDE_BODY=1 render), B = full design. Slow zoom + crossfade + background music.
Usage: python3 make_reel.py A.png B.png out.mp4 [ks|sisco|none]
The music set defaults to "sisco" when out.mp4 is under siscohub/, otherwise "ks".
Tracks in tools/assets/music/ are original compositions generated for this project (no third-party rights).
"""
import pathlib, random, subprocess, sys

a, b, out = sys.argv[1:4]
music_set = sys.argv[4] if len(sys.argv) > 4 else ("sisco" if "siscohub/" in out.replace("\\", "/") else "ks")
music_dir = pathlib.Path(__file__).resolve().parent / "assets" / "music"
tracks = sorted(music_dir.glob(f"{music_set}*.m4a")) if music_set != "none" else []

fc = ("[0:v]scale=1080:1920,format=yuv420p,zoompan=z='1+0.0004*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=1080x1920:fps=30,fade=t=in:st=0:d=0.6[v0];"
      "[1:v]scale=1080:1920,format=yuv420p,zoompan=z='1.0+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=210:s=1080x1920:fps=30[v1];"
      "[v0][v1]xfade=transition=fade:duration=0.8:offset=2.4,format=yuv420p[v]")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", "3", "-i", a, "-loop", "1", "-t", "7", "-i", b]
if tracks:
    cmd += ["-i", str(random.choice(tracks))]
    fc += ";[2:a]atrim=0:9.2,volume=0.8,afade=t=out:st=8.2:d=1,asetpts=N/SR/TB[a]"
    amap = "[a]"
else:
    cmd += ["-f", "lavfi", "-t", "9.2", "-i", "anullsrc=r=44100:cl=stereo"]
    amap = "2:a"
cmd += ["-filter_complex", fc, "-map", "[v]", "-map", amap, "-t", "9.2",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
