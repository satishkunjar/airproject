#!/usr/bin/env python3
"""Cebu canyoneering reel v2: every jump/slide is one continuous take
(run-up -> takeoff -> flight -> splash) with speed ramps, a running counter,
and a photo intro/outro. Single ffmpeg encode pass.

usage: build_reel_v2.py OUT.mp4 [CRF]
Env: CLIPS_DIR (c01..c14.mov), PHOTOS_DIR (uploaded photos)
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("CLIPS_DIR", "src")
PH = os.environ.get("PHOTOS_DIR", "photos")
WORK = os.environ.get("WORK_DIR", HERE)
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT2 = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FPS, W, H = 30, 1080, 1920
OUT = sys.argv[1]
CRF = sys.argv[2] if len(sys.argv) > 2 else "17"
LOWRES = {"c09", "c12", "c14"}

# Each SHOT = (source, [(start, end, speed), ...], caption lines)
# Pieces of one shot are contiguous in the source, so the action plays
# through uninterrupted; speed <1 = slow motion (60fps source), >1 = ramp up.
P = lambda name, dur, zoom="in": ("PHOTO:" + name, [(0, dur, zoom)])
SHOTS = [
    # HOOK: biggest jump beside the waterfall, slow-mo through the fall
    ("c10", [(4.9, 5.45, 1.0), (5.45, 6.3, 0.5), (6.3, 7.0, 1.0)], "hook"),
    (*P("23bea23a-image.jpg", 1.3, "out"), "intro"),
    # SLIDES
    ("c01", [(0.0, 0.6, 1.3), (0.6, 1.9, 1.0)], ("SLIDE", 1, 4)),
    ("c01", [(15.0, 15.8, 1.3), (15.8, 17.4, 1.0)], ("SLIDE", 2, 4)),
    ("c01", [(31.0, 32.0, 1.3), (32.0, 33.7, 1.0)], ("SLIDE", 3, 4)),
    ("c01", [(48.6, 49.2, 1.3), (49.2, 51.2, 1.0)], ("SLIDE", 4, 4)),
    # ROPE SWINGS: real time on the launch and the splash, ramped in between
    ("c05", [(2.2, 3.2, 1.0), (3.2, 5.6, 3.0), (5.6, 6.2, 1.0)], ("ROPE SWING", 1, 3)),
    ("c08", [(3.4, 4.6, 1.0), (4.6, 6.8, 2.4), (6.8, 7.5, 1.0)], ("ROPE SWING", 2, 3)),
    ("c06", [(35.6, 37.0, 1.0), (37.0, 40.3, 3.5), (40.3, 41.0, 1.0)], ("ROPE SWING", 3, 3)),
    # CLIFF JUMPS
    ("c02", [(4.0, 4.6, 1.0), (4.6, 5.4, 0.5), (5.4, 6.2, 1.0)], ("CLIFF JUMP", 1, 8)),
    ("c02", [(35.8, 38.4, 1.0)], ("CLIFF JUMP", 2, 8)),
    ("c12", [(47.0, 49.4, 1.0)], ("CLIFF JUMP", 3, 8)),
    ("c12", [(64.0, 66.4, 1.0)], ("CLIFF JUMP", 4, 8)),
    ("c12", [(82.4, 83.0, 1.0), (83.0, 83.8, 0.5), (83.8, 84.6, 1.0)], ("CLIFF JUMP", 5, 8)),
    ("c09", [(6.6, 8.69, 1.0)], ("CLIFF JUMP", 6, 8)),
    ("c14", [(2.9, 3.4, 1.0), (3.4, 4.2, 0.6), (4.2, 5.2, 1.0)], ("CLIFF JUMP", 7, 8)),
    ("c11", [(11.2, 12.2, 1.0), (12.2, 13.6, 0.5), (13.6, 14.4, 1.0)], "finale"),
    # OUTRO photo montage
    (*P("3b4eff6f-image.jpg", 1.3, "in"), None),
    (*P("39ba0382-image.jpg", 1.1, "out"), None),
    (*P("4b7227b8-image.jpg", 1.4, "in"), None),
    (*P("a201a9df-image.jpg", 2.6, "in"), "end"),
]

args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
fg, vl, al = [], [], []
t, k = 0.0, 0
shot_times = []
grade = "eq=contrast=1.05:saturation=1.14"
for src, pieces, cap in SHOTS:
    st = t
    for a, b, sp in pieces:
        if src.startswith("PHOTO:"):
            n = round((b - a) * FPS); dur = n / FPS
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.5:.3f}",
                     "-i", os.path.join(PH, src[6:])]
            z = f"1.0+0.07*on/{n}" if sp == "in" else f"1.07-0.07*on/{n}"
            fg.append(f"[{k}:v]scale=2160:3840:force_original_aspect_ratio=increase:flags=lanczos,"
                      f"crop=2160:3840,eq=contrast=1.04:saturation=1.10,"
                      f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
                      f"trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{k}]")
            fg.append(f"anullsrc=r=48000:cl=stereo,atrim=end={dur:.4f}[a{k}]")
        else:
            n = round((b - a) / sp * FPS); dur = n / FPS
            args += ["-ss", f"{a:.3f}", "-t", f"{b - a + 0.3:.3f}", "-i", os.path.join(SRC, src + ".mov")]
            sharp = "unsharp=5:5:0.75:5:5:0" if src in LOWRES else "unsharp=5:5:0.45:5:5:0"
            fg.append(f"[{k}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},scale={W}:{H}:flags=lanczos,"
                      f"{grade},{sharp},trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{k}]")
            # audio: atempo handles 0.5..2.0 per stage; chain for 2.2x
            tempo = []
            s = sp
            while s > 2.0: tempo.append("atempo=2.0"); s /= 2.0
            while s < 0.5: tempo.append("atempo=0.5"); s /= 0.5
            if abs(s - 1.0) > 1e-6: tempo.append(f"atempo={s:.4f}")
            at = ",".join(tempo) + "," if tempo else ""
            fg.append(f"[{k}:a]asetpts=PTS-STARTPTS,{at}aresample=48000,apad,atrim=end={dur:.4f},"
                      f"afade=t=in:d=0.03,afade=t=out:st={max(dur - 0.04, 0):.4f}:d=0.04,"
                      f"aformat=sample_rates=48000:channel_layouts=stereo[a{k}]")
        vl.append(f"[v{k}]"); al.append(f"[a{k}]")
        k += 1; t += dur
    shot_times.append((st, t, cap))
TOTAL = t
fg.append("".join(v + a for v, a in zip(vl, al)) + f"concat=n={k}:v=1:a=1[vc][ac]")

txtdir = os.path.join(WORK, "txt2"); os.makedirs(txtdir, exist_ok=True)
caps = []
def cap(text, s, e, size, y, font=FONT, fade=0.15):
    p = os.path.join(txtdir, f"t{len(caps)}.txt"); open(p, "w").write(text)
    alpha = f"if(lt(t,{s:.3f}+{fade}),(t-{s:.3f})/{fade},if(gt(t,{e:.3f}-{fade}),({e:.3f}-t)/{fade},1))"
    caps.append(f"drawtext=fontfile={font}:textfile={p}:fontsize={size}:fontcolor=white:"
                f"borderw=7:bordercolor=black@0.55:shadowx=0:shadowy=6:shadowcolor=black@0.45:"
                f"x=(w-text_w)/2:y={y}:alpha='{alpha}':enable='between(t,{s:.3f},{e:.3f})'")

for st, en, c in shot_times:
    if c == "hook":
        cap("3 FRIENDS", st + 0.1, en - 0.03, 118, 150)
        cap("VS  CEBU CANYONS", st + 0.3, en - 0.03, 72, 290)
        cap("wait for jump 8", st + 0.6, en - 0.03, 46, 1560, FONT2)
    elif c == "intro":
        cap("CANYONEERING", st + 0.05, en - 0.03, 96, 170)
        cap("Badian, Cebu", st + 0.2, en - 0.03, 56, 290, FONT2)
    elif isinstance(c, tuple):
        name, i, nn = c
        cap(f"{name} {i}/{nn}", st + 0.03, min(st + 1.7, en - 0.03), 76, 170)
    elif c == "finale":
        cap("CLIFF JUMP 8/8", st + 0.03, en - 0.03, 76, 170)
        cap("SAVED THE BEST FOR LAST", st + 0.3, en - 0.03, 58, 275, FONT2)
    elif c == "end":
        cap("KAWASAN FALLS", st + 0.15, en, 100, 170)
        cap("Cebu, Philippines", st + 0.4, en, 56, 300, FONT2)

fg.append("[vc]" + ",".join(caps) + f",fade=t=out:st={TOTAL - 0.3:.3f}:d=0.3:color=black[vout]")
fg.append(f"[ac]volume=0.9,afade=t=out:st={TOTAL - 0.5:.3f}:d=0.5,alimiter=limit=0.9[aout]")

script = os.path.join(WORK, "graph2.txt"); open(script, "w").write(";\n".join(fg))
args += ["-filter_complex_script", script, "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", CRF, "-profile:v", "high", "-level", "4.2",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2),
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", OUT]
print(f"inputs={k} total={TOTAL:.2f}s")
for st, en, c in shot_times:
    print(f"  {st:6.2f}-{en:6.2f}  {c}")
subprocess.run(args, check=True)
