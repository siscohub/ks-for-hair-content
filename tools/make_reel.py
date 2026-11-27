"""Make an Instagram/TikTok Reel (1080x1920 MP4, ~9.2 s) from story-size images.

Two images (classic):  python3 make_reel.py A.png B.png out.mp4 [ks|sisco|none]
  A = title only (HIDE_BODY=1 render), B = full design. A holds ~2.4 s, then crossfade to B.

Step reveal (more than two images):  python3 make_reel.py A.png S1.png S2.png ... B.png out.mp4 [set]
  A = title/question only, S1..Sn = the answer revealed line by line (REVEAL_LINES=1..n renders),
  B = full design. A holds 1.0 s, each step ~1.0 s with a short 0.25 s crossfade, B holds to the end.
  Analytics (27 Nov 2026): TikTok viewers left after 2–3 s; reels where text keeps appearing hold longer.

The music set defaults to "sisco" when out.mp4 is under siscohub/, otherwise "ks".
Tracks in tools/assets/music/ are original compositions generated for this project (no third-party rights).
"""
import pathlib, random, subprocess, sys

args = sys.argv[1:]
music_set = None
if args and args[-1] in ("ks", "sisco", "none"):
    music_set = args.pop()
*imgs, out = args
if len(imgs) < 2:
    sys.exit("need at least two images")
if music_set is None:
    music_set = "sisco" if "siscohub/" in out.replace("\\", "/") else "ks"
music_dir = pathlib.Path(__file__).resolve().parent / "assets" / "music"
tracks = sorted(music_dir.glob(f"{music_set}*.m4a")) if music_set != "none" else []
TOTAL, FPS = 9.2, 30

if len(imgs) == 2:
    durs, offsets, xd = [3, 7], [2.4], 0.8
    zooms = ["1+0.0004*on", "1.0+0.0003*on"]
else:
    hold, xd = 1.0, 0.25
    offsets = [hold * (i + 1) for i in range(len(imgs) - 1)]          # 1.0, 2.0, 3.0 ...
    durs = [offsets[0] + xd] + [hold + xd] * (len(imgs) - 2) + [TOTAL - offsets[-1] + 0.1]
    zooms = ["1"] * (len(imgs) - 1) + ["1.0+0.0003*on"]

cmd = ["ffmpeg", "-y", "-loglevel", "error"]
fc = []
for i, (im, d) in enumerate(zip(imgs, durs)):
    cmd += ["-loop", "1", "-t", f"{d:.2f}", "-i", im]
    frames = int(round(d * FPS)) + 1
    fade = ",fade=t=in:st=0:d=0.4" if i == 0 else ""
    fc.append(f"[{i}:v]scale=1080:1920,format=yuv420p,zoompan=z='{zooms[i]}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d={frames}:s=1080x1920:fps={FPS}{fade},trim=duration={d:.2f},setpts=PTS-STARTPTS[v{i}]")
prev = "v0"
for i, off in enumerate(offsets, 1):
    lab = "v" if i == len(offsets) else f"x{i}"
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={xd}:offset={off:.2f}[{lab}]")
    prev = lab
fc[-1] = fc[-1][:-3] + ",format=yuv420p[v]"
n = len(imgs)
if tracks:
    cmd += ["-i", str(random.choice(tracks))]
    fc.append(f"[{n}:a]atrim=0:{TOTAL},volume=0.8,afade=t=out:st={TOTAL-1}:d=1,asetpts=N/SR/TB[a]")
    amap = "[a]"
else:
    cmd += ["-f", "lavfi", "-t", str(TOTAL), "-i", "anullsrc=r=44100:cl=stereo"]
    amap = f"{n}:a"
cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", amap, "-t", str(TOTAL),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
