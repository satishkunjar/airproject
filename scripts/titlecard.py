#!/usr/bin/env python3
"""Render the opening title as a transparent 1080x1920 PNG (fancy fonts + colour flag emoji).

usage: titlecard.py STYLE OUT.png [FONTS_DIR]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

STYLE, OUT = sys.argv[1], sys.argv[2]
FD = sys.argv[3] if len(sys.argv) > 3 else "fonts"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1920
F = lambda name, size: ImageFont.truetype(os.path.join(FD, name), size)


def emoji(ch, height):
    f = ImageFont.truetype(EMOJI, 109)  # CBDT bitmap font: fixed 109px strike
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)


def run(text, font, fill, spacing=0, stroke=0, stroke_fill=None):
    """Render one text run tightly; returns RGBA image."""
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    chars, widths = list(text), []
    for c in chars:
        widths.append(d.textlength(c, font=font))
    asc, desc = font.getmetrics()
    w = int(sum(widths) + spacing * (len(chars) - 1) + stroke * 2 + 20)
    im = Image.new("RGBA", (w, asc + desc + stroke * 2 + 20), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = stroke + 10
    for c, cw in zip(chars, widths):
        dr.text((x, stroke + 10), c, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += cw + spacing
    return im.crop(im.getbbox())


def row(parts, gap=18):
    h = max(p.height for p in parts)
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for p in parts:
        im.alpha_composite(p, (x, (h - p.height) // 2))
        x += p.width + gap
    return im


def shadowed(layer, blur=10, offset=6, alpha=150):
    a = layer.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    pad = blur * 3
    canvas = Image.new("RGBA", (layer.width + pad * 2, layer.height + pad * 2 + offset), (0, 0, 0, 0))
    canvas.alpha_composite(sh, (pad, pad + offset))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(layer, (pad, pad))
    return canvas


def stack(lines, top, line_gap):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft dark gradient behind the title block for legibility over a busy photo
    grad = Image.new("L", (1, 760))
    for y in range(760):
        grad.putpixel((0, y), int(150 * (1 - y / 760) ** 1.6))
    shade = Image.new("RGBA", (W, 760), (0, 0, 0, 255))
    shade.putalpha(grad.resize((W, 760)))
    out.alpha_composite(shade, (0, 0))
    y = top
    for ln, extra in lines:
        s = shadowed(ln)
        out.alpha_composite(s, ((W - s.width) // 2, y))
        y += s.height + line_gap + extra
    return out


WHITE, SUN = (255, 255, 255, 255), (255, 214, 64, 255)
AQUA = (64, 232, 220, 255)

if STYLE == "A":   # script + bold condensed + flag
    l1 = run("3 Friends", F("Pacifico-Regular.ttf", 112), WHITE)
    l2 = run("CANYONEERING", F("Anton-Regular.ttf", 156), WHITE, spacing=6)
    loc = run("CEBU, PHILIPPINES", F("BebasNeue-Regular.ttf", 92), SUN, spacing=4)
    l3 = row([loc, emoji("🇵🇭", 70)], gap=20)
    img = stack([(l1, -40), (l2, -38), (l3, 0)], top=95, line_gap=0)
elif STYLE == "B":  # aqua headline, script location
    l1 = run("3 FRIENDS", F("Anton-Regular.ttf", 84), WHITE, spacing=10)
    l2 = run("CANYONEERING", F("Anton-Regular.ttf", 156), AQUA, spacing=6)
    loc = run("Cebu, Philippines", F("Pacifico-Regular.ttf", 84), WHITE)
    l3 = row([loc, emoji("🇵🇭", 66)], gap=22)
    img = stack([(l1, -32), (l2, -28), (l3, 0)], top=100, line_gap=0)
elif STYLE == "C":  # hand-drawn marker
    l1 = run("3 friends", F("PermanentMarker-Regular.ttf", 92), WHITE)
    l2 = run("CANYONEERING", F("PermanentMarker-Regular.ttf", 118), SUN)
    loc = run("Cebu, Philippines", F("PermanentMarker-Regular.ttf", 74), WHITE)
    l3 = row([loc, emoji("🇵🇭", 66)], gap=20)
    img = stack([(l1, -26), (l2, -24), (l3, 0)], top=105, line_gap=0)
else:
    raise SystemExit("style must be A, B or C")
img.save(OUT)
