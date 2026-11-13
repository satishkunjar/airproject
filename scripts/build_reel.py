#!/usr/bin/env python3
"""Build the Cebu canyoneering reel in a single ffmpeg encode pass."""
import os, subprocess, sys

S = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(S, "src")
PHOTO = "/root/.claude/uploads/0a34019c-3730-5b53-9440-f1ea5ac58eab/edc627f8-image.jpg"
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT2 = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FPS = 30
W, H = 1080, 1920
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, "reel.mp4")
CRF = sys.argv[2] if len(sys.argv) > 2 else "16"

LOWRES = {"c09", "c12", "c14"}  # 480x854 sources: a bit more sharpening

# (clip, start, end, speed, tag)   speed<1 = slow motion (sources are 60fps)
SEG = [
    # HOOK - biggest cliff jump beside the waterfall, slow-mo
    ("c10", 5.2, 5.45, 1.0, "hook"),
    ("c10", 5.45, 6.6, 0.5, None),
    # intro
    ("c12", 2.6, 4.0, 1.0, "intro"),
    ("c07", 0.4, 1.5, 1.0, None),
    # SLIDES
    ("c01", 15.6, 17.8, 1.0, "slides"),
    ("c01", 0.4, 2.2, 1.0, None),
    ("c01", 32.0, 34.0, 1.0, None),
    ("c01", 49.2, 51.2, 1.0, None),
    # ROPE SWINGS (swing out -> cut -> splash)
    ("c05", 2.4, 3.8, 1.0, "swing"),
    ("c05", 5.4, 6.4, 1.0, None),
    ("c08", 3.6, 5.0, 1.0, None),
    ("c08", 6.8, 7.6, 1.0, None),
    ("c06", 35.6, 37.4, 1.0, None),
    ("c06", 40.6, 41.4, 1.0, None),
    ("c04", 13.6, 15.0, 1.0, None),
    ("c04", 23.2, 24.6, 1.0, None),
    # CLIFF JUMPS
    ("c02", 4.0, 4.9, 1.0, "jumps"),
    ("c02", 4.9, 5.5, 0.5, None),
    ("c02", 35.8, 37.8, 1.0, None),
    ("c12", 47.2, 49.0, 1.0, None),
    ("c12", 64.2, 66.2, 1.0, None),
    ("c12", 82.6, 84.4, 1.0, None),
    ("c09", 6.8, 8.69, 1.0, None),
    ("c14", 3.0, 3.6, 1.0, None),
    ("c14", 3.6, 4.4, 0.5, None),
    # hero finale jump, arms out, slow-mo
    ("c11", 11.6, 12.4, 1.0, "finale"),
    ("c11", 12.4, 13.6, 0.5, None),
    # outro
    ("c03", 26.0, 28.0, 1.0, "outro"),
    ("c13", 8.0, 9.6, 1.0, "land"),
    ("PHOTO", 0, 3.4, 1.0, "photo"),
]

args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-stats"]
fg = []
vlabels, alabels = [], []
t = 0.0
marks = {}
for i, (clip, a, b, sp, tag) in enumerate(SEG):
    n = round((b - a) / sp * FPS)
    dur = n / FPS
    if tag:
        marks[tag] = t
    if clip == "PHOTO":
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.5:.3f}", "-i", PHOTO]
        # 1500x2000 photo -> 9:16 crop, slow push-in (Ken Burns) from a 2x canvas
        fg.append(
            f"[{i}:v]scale=2160:2880:flags=lanczos,crop=1620:2880:270:0,"
            f"eq=contrast=1.04:saturation=1.10,"
            f"zoompan=z='1.0+0.08*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
            f"trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]")
        fg.append(f"anullsrc=r=48000:cl=stereo,atrim=end={dur:.4f}[a{i}]")
    else:
        args += ["-ss", f"{a:.3f}", "-t", f"{b - a + 0.3:.3f}", "-i", os.path.join(SRC, clip + ".mov")]
        pre = f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},"
        grade = "eq=contrast=1.05:saturation=1.14"
        sharp = "unsharp=5:5:0.75:5:5:0" if clip in LOWRES else "unsharp=5:5:0.45:5:5:0"
        if clip == "c13":  # landscape: sharp foreground over blurred fill
            fg.append(pre + f"{grade},split=2[bg{i}][fgs{i}]")
            fg.append(f"[bg{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[bgb{i}]")
            fg.append(f"[fgs{i}]scale={W}:-2:flags=lanczos,{sharp}[fgx{i}]")
            fg.append(f"[bgb{i}][fgx{i}]overlay=0:(H-h)/2,trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]")
        else:
            fg.append(pre + f"scale={W}:{H}:flags=lanczos,{grade},{sharp},"
                      f"trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]")
        at = f"atempo={sp}," if sp != 1.0 else ""
        fg.append(f"[{i}:a]asetpts=PTS-STARTPTS,{at}aresample=48000,apad,atrim=end={dur:.4f},"
                  f"afade=t=in:d=0.04,afade=t=out:st={max(dur - 0.06, 0):.4f}:d=0.06,"
                  f"aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
    vlabels.append(f"[v{i}]")
    alabels.append(f"[a{i}]")
    t += dur
TOTAL = t

inter = "".join(v + a for v, a in zip(vlabels, alabels))
fg.append(f"{inter}concat=n={len(SEG)}:v=1:a=1[vc][ac]")

# ---- captions ----
txtdir = os.path.join(S, "txt"); os.makedirs(txtdir, exist_ok=True)
def cap(key, text, start, end, size, y, font=FONT):
    p = os.path.join(txtdir, key + ".txt")
    open(p, "w").write(text)
    fade = 0.18
    alpha = (f"if(lt(t,{start}+{fade}),(t-{start})/{fade},"
             f"if(gt(t,{end}-{fade}),({end}-t)/{fade},1))")
    return (f"drawtext=fontfile={font}:textfile={p}:fontsize={size}:fontcolor=white:"
            f"borderw=7:bordercolor=black@0.55:shadowx=0:shadowy=6:shadowcolor=black@0.45:"
            f"x=(w-text_w)/2:y={y}:alpha='{alpha}':enable='between(t,{start},{end})'")

m = marks
caps = [
    cap("h1", "3 FRIENDS", 0.15, m["intro"] - 0.05, 118, 150),
    cap("h2", "VS  CEBU CANYONS", 0.35, m["intro"] - 0.05, 72, 290),
    cap("i1", "CANYONEERING  ·  BADIAN, CEBU", m["intro"] + 0.1, m["slides"] - 0.1, 50, 270, FONT2),
    cap("s1", "THE SLIDES", m["slides"] + 0.05, m["slides"] + 1.9, 104, 250),
    cap("r1", "ROPE SWING", m["swing"] + 0.05, m["swing"] + 1.9, 104, 250),
    cap("j1", "CLIFF JUMPS", m["jumps"] + 0.05, m["jumps"] + 1.9, 104, 250),
    cap("f1", "SAVED THE BEST", m["finale"] + 0.05, m["outro"] - 0.05, 84, 250),
    cap("f2", "FOR LAST", m["finale"] + 0.25, m["outro"] - 0.05, 84, 360),
    cap("o1", "KAWASAN FALLS", m["photo"] + 0.15, TOTAL, 100, 250),
    cap("o2", "Cebu, Philippines", m["photo"] + 0.4, TOTAL, 56, 380, FONT2),
]
fg.append("[vc]" + ",".join(caps) + f",fade=t=out:st={TOTAL - 0.35:.3f}:d=0.35:color=black[vout]")
fg.append(f"[ac]volume=0.9,afade=t=out:st={TOTAL - 0.6:.3f}:d=0.6,alimiter=limit=0.9[aout]")

script = os.path.join(S, "graph.txt")
open(script, "w").write(";\n".join(fg))
args += ["-filter_complex_script", script, "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", CRF, "-profile:v", "high", "-level", "4.2",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-bf", "2",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-movflags", "+faststart", OUT]
print(f"segments={len(SEG)} total={TOTAL:.2f}s marks=" + ", ".join(f"{k}={v:.2f}" for k, v in marks.items()))
subprocess.run(args, check=True)
