from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, math, random

W, H = 1000, 340
FRAMES, FRAME_MS = 84, 65

BASE = Path(".github/scripts")
ASSETS = BASE / "assets"
OUT = Path("arcade-output")
DATA = OUT / "github-data.json"
OUT.mkdir(exist_ok=True)

# ---------- Real GitHub activity ----------
try:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    calendar = raw["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = int(calendar["totalContributions"])
    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
except Exception:
    total, days = 0, []

recent = days[-90:]
recent7 = days[-7:]
commits_7d = sum(int(d["contributionCount"]) for d in recent7)
avg_recent = sum(int(d["contributionCount"]) for d in recent) / max(1, len(recent))

level = max(1, min(99, 1 + total // 25))
enemy_count = max(4, min(14, 4 + int(avg_recent * 2)))
bullet_count = max(1, min(10, 1 + commits_7d // 3))

# ---------- Your uploaded sprites ----------
player = Image.open(ASSETS / "player.png").convert("RGBA")
enemy = Image.open(ASSETS / "enemy.png").convert("RGBA")

# Keep the pixel-art look: nearest-neighbor only.
player = player.resize((145, 145), Image.Resampling.NEAREST)
enemy = enemy.resize((105, 105), Image.Resampling.NEAREST)

def remove_black_background(img):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a and r < 8 and g < 8 and b < 8:
                px[x, y] = (r, g, b, 0)
    return img

player = remove_black_background(player)
enemy = remove_black_background(enemy)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
title_font = ImageFont.truetype(FONT, 25)
ui_font = ImageFont.truetype(FONT, 14)

random.seed(2026)
stars = [
    (random.randrange(25, W - 25), random.randrange(50, 285),
     random.choice([1, 1, 1, 2]))
    for _ in range(80)
]

def paste_center(canvas, sprite, x, y):
    canvas.alpha_composite(
        sprite,
        (int(x - sprite.width / 2), int(y - sprite.height / 2))
    )

def explosion(draw, x, y, radius):
    for angle in range(0, 360, 45):
        dx = int(math.cos(math.radians(angle)) * radius)
        dy = int(math.sin(math.radians(angle)) * radius)
        draw.line((x, y, x + dx, y + dy),
                  fill=(255, 110, 70), width=3)
    draw.rectangle(
        (x - radius // 3, y - radius // 3,
         x + radius // 3, y + radius // 3),
        fill=(255, 220, 80)
    )

positions = [
    (95 + (i * 92) % 810, 95 + (i * 43) % 105)
    for i in range(enemy_count)
]

frames = []

for frame in range(FRAMES):
    image = Image.new("RGBA", (W, H), (7, 11, 19, 255))
    draw = ImageDraw.Draw(image)

    # Arcade border
    draw.rectangle((18, 40, W - 18, 292),
                   outline=(65, 85, 110), width=2)
    draw.line((18, 43, W - 18, 43),
              fill=(90, 110, 135), width=2)

    # Stars
    for x, y, size in stars:
        yy = 52 + ((y + frame * 2) % 230)
        draw.rectangle((x, yy, x + size, yy + size),
                       fill=(105, 130, 155))

    # HUD
    draw.text((W // 2, 18), "KADDAFII CODE INVADERS",
              anchor="mm", fill=(235, 245, 255), font=title_font)
    draw.text((34, 54), f"SCORE {total:05d}",
              fill=(130, 255, 170), font=ui_font)
    draw.text((W // 2, 54), f"LEVEL {level:02d}",
              anchor="ma", fill=(255, 220, 110), font=ui_font)
    draw.text((W - 34, 54), f"7D COMMITS {commits_7d:02d}",
              anchor="ra", fill=(130, 190, 255), font=ui_font)

    # YOUR UFO sprite
    for i, (base_x, base_y) in enumerate(positions):
        x = base_x + int(18 * math.sin(frame / 8 + i))
        y = base_y + int(7 * math.sin(frame / 11 + i / 2))
        paste_center(
            image, enemy, x, y + int(3 * math.sin(frame / 5 + i))
        )

    # YOUR fighter sprite
    travel = min(330, 100 + commits_7d * 12)
    ship_x = W // 2 + int(travel * math.sin(frame / 12))
    ship_y = 260
    paste_center(image, player, ship_x, ship_y)

    # More recent commits = more bullets
    for bullet in range(bullet_count):
        bx = ship_x + int(10 * math.sin((frame + bullet * 7) / 5))
        by = ship_y - 68 - ((frame * 7 + bullet * 52) % 150)
        draw.rectangle((bx - 2, by, bx + 2, by + 12),
                       fill=(100, 235, 255))
        draw.rectangle((bx - 1, by - 3, bx + 1, by),
                       fill=(225, 255, 255))

    # Hit animation
    if frame % 28 in range(8, 14):
        idx = (frame // 28) % enemy_count
        ex, ey = positions[idx]
        ex += int(18 * math.sin(frame / 8 + idx))
        ey += int(7 * math.sin(frame / 11 + idx / 2))
        explosion(draw, ex, ey,
                  8 + abs(10 - (frame % 28)) * 2)

    # Footer
    draw.text((34, 307),
              "EVERY CONTRIBUTION IS A BULLET",
              fill=(125, 145, 170), font=ui_font)
    draw.text((W - 34, 307),
              "BUILD • SHIP • REPEAT",
              anchor="ra", fill=(125, 145, 170), font=ui_font)

    frames.append(image.convert("RGB"))

frames[0].save(
    OUT / "arcade.gif",
    save_all=True,
    append_images=frames[1:],
    duration=FRAME_MS,
    loop=0,
    optimize=False
)

try:
    DATA.unlink()
except FileNotFoundError:
    pass

print(
    f"Generated using supplied sprites: "
    f"score={total}, level={level}, commits_7d={commits_7d}, "
    f"enemies={enemy_count}, bullets={bullet_count}"
)
