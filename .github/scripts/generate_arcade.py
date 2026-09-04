from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import math
import random

W, H = 1000, 340
FRAMES = 84
FRAME_MS = 65

SHIP_Y = 260
TOP_BOUND = 60
BULLET_SPEED = 8          # px per frame
HIT_RADIUS = 12           # px, collision distance between bullet and enemy center
EXPLOSION_FRAMES = 10     # how long an enemy stays "destroyed" before respawning

BASE = Path(".github/scripts")
ASSETS = BASE / "assets"
OUT = Path("arcade-output")
DATA = OUT / "github-data.json"
OUT.mkdir(exist_ok=True)

# ---------------- GitHub contribution data ----------------
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
average_recent = (
    sum(int(d["contributionCount"]) for d in recent)
    / max(1, len(recent))
)

level = max(1, min(99, 1 + total // 25))
enemy_count = max(8, min(24, 8 + int(average_recent * 2)))
bullet_count = max(1, min(10, 1 + commits_7d // 3))

# ---------------- EXACT supplied sprites ----------------
player = Image.open(ASSETS / "player.png").convert("RGBA")
enemy = Image.open(ASSETS / "enemy.png").convert("RGBA")

# Both game sprites are intentionally rendered at EXACTLY 20x20 px.
# Nearest-neighbor preserves the pixel-art character. Both source PNGs
# already ship with a proper transparent background, so no cleanup
# pass is applied -- the sprites are used exactly as supplied.
player = player.resize((20, 20), Image.Resampling.NEAREST)
enemy = enemy.resize((20, 20), Image.Resampling.NEAREST)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


title_font = load_font(FONT, 25)
ui_font = load_font(FONT, 14)

random.seed(2026)
stars = [
    (random.randrange(25, W - 25),
     random.randrange(50, 285),
     random.choice([1, 1, 1, 2]))
    for _ in range(80)
]


def paste_center(canvas, sprite, x, y):
    canvas.alpha_composite(
        sprite,
        (int(x - sprite.width / 2),
         int(y - sprite.height / 2))
    )


def draw_explosion(draw, x, y, age):
    # Radius pulses from 0 -> peak -> 0 across the explosion's lifetime,
    # so it visually "happens" exactly when the collision occurs and
    # fades out, instead of an arbitrary decorative loop.
    progress = min(age, EXPLOSION_FRAMES) / EXPLOSION_FRAMES
    radius = max(2, int(3 + 11 * math.sin(math.pi * progress)))

    for angle in range(0, 360, 45):
        dx = int(math.cos(math.radians(angle)) * radius)
        dy = int(math.sin(math.radians(angle)) * radius)
        draw.line((x, y, x + dx, y + dy), fill=(255, 110, 70), width=2)

    draw.rectangle(
        (x - radius // 3, y - radius // 3,
         x + radius // 3, y + radius // 3),
        fill=(255, 220, 80)
    )


# ---------------- Deterministic ship / enemy trajectories ----------------
travel = min(370, 140 + commits_7d * 12)


def ship_x_at(frame):
    return W // 2 + int(travel * math.sin(frame / 12))


enemy_positions = [
    (70 + (i * 83) % 860, 80 + (i * 31) % 115)
    for i in range(enemy_count)
]


def enemy_pos_at(i, frame):
    base_x, base_y = enemy_positions[i]
    x = base_x + int(18 * math.sin(frame / 8 + i))
    y = base_y + int(6 * math.sin(frame / 11 + i / 2)) + int(2 * math.sin(frame / 5 + i))
    return x, y


# ---------------- Bullet spawn schedule ----------------
travel_frames = max(1, (SHIP_Y - 15 - TOP_BOUND) // BULLET_SPEED)
fire_interval = max(2, round(travel_frames / max(1, bullet_count)))

bullets = []
for spawn_frame in range(0, FRAMES, fire_interval):
    bullets.append({
        "spawn": spawn_frame,
        "x0": ship_x_at(spawn_frame),
        "resolved": False,   # True once it has hit an enemy or left the screen
    })

# ---------------- Simulate collisions frame by frame ----------------
# An enemy that has been hit stops being drawn normally and can't be hit
# again while it's "exploding"; once the explosion finishes it respawns
# in its normal orbit. Bullets stop being drawn the instant they hit --
# they never pass through an enemy.
enemy_explosion_start = {}   # enemy_index -> frame the explosion started
enemy_explosion_pos = {}     # enemy_index -> (x, y) fixed explosion location

frame_bullets = {f: [] for f in range(FRAMES)}
frame_enemies = {f: [] for f in range(FRAMES)}   # (idx, x, y, exploding, age)

for frame in range(FRAMES):
    # 1) Advance/resolve bullets first so a hit this frame is reflected
    #    in the same frame's enemy state (explosion appears immediately,
    #    not one frame late).
    for b in bullets:
        if b["resolved"] or frame < b["spawn"]:
            continue

        by = SHIP_Y - 15 - BULLET_SPEED * (frame - b["spawn"])
        if by < TOP_BOUND:
            b["resolved"] = True
            continue

        bx = b["x0"] + int(4 * math.sin((frame - b["spawn"]) / 4))

        hit_idx = None
        hit_pos = None
        for i in range(enemy_count):
            if i in enemy_explosion_start:
                continue  # currently exploding -- can't be hit again yet
            ex, ey = enemy_pos_at(i, frame)
            if (bx - ex) ** 2 + (by - ey) ** 2 <= HIT_RADIUS ** 2:
                hit_idx = i
                hit_pos = (ex, ey)
                break

        if hit_idx is not None:
            b["resolved"] = True
            enemy_explosion_start[hit_idx] = frame
            enemy_explosion_pos[hit_idx] = hit_pos
            frame_bullets[frame].append((bx, by))  # last visible position, right at impact
        else:
            frame_bullets[frame].append((bx, by))

    # 2) Now that this frame's hits are known, build the enemy draw list.
    for i in range(enemy_count):
        if i in enemy_explosion_start:
            age = frame - enemy_explosion_start[i]
            if age < EXPLOSION_FRAMES:
                ex, ey = enemy_explosion_pos[i]
                frame_enemies[frame].append((i, ex, ey, True, age))
                continue
            else:
                del enemy_explosion_start[i]
                del enemy_explosion_pos[i]
        ex, ey = enemy_pos_at(i, frame)
        frame_enemies[frame].append((i, ex, ey, False, 0))

# ---------------- Render frames ----------------
frames = []

for frame in range(FRAMES):
    image = Image.new("RGBA", (W, H), (7, 11, 19, 255))
    draw = ImageDraw.Draw(image)

    draw.rectangle((18, 40, W - 18, 292), outline=(65, 85, 110), width=2)
    draw.line((18, 43, W - 18, 43), fill=(90, 110, 135), width=2)

    for x, y, size in stars:
        yy = 52 + ((y + frame * 2) % 230)
        draw.rectangle((x, yy, x + size, yy + size), fill=(105, 130, 155))

    draw.text((W // 2, 18), "KADDAFII CODE INVADERS", anchor="mm",
              fill=(235, 245, 255), font=title_font)
    draw.text((34, 54), f"SCORE {total:05d}", fill=(130, 255, 170), font=ui_font)
    draw.text((W // 2, 54), f"LEVEL {level:02d}", anchor="ma",
              fill=(255, 220, 110), font=ui_font)
    draw.text((W - 34, 54), f"7D COMMITS {commits_7d:02d}", anchor="ra",
              fill=(130, 190, 255), font=ui_font)

    # Enemies (normal sprite, or explosion if just hit)
    for i, x, y, exploding, age in frame_enemies[frame]:
        if exploding:
            draw_explosion(draw, x, y, age)
        else:
            paste_center(image, enemy, x, y)

    # Player
    ship_x = ship_x_at(frame)
    paste_center(image, player, ship_x, SHIP_Y)

    # Bullets -- only the ones still alive this frame; a bullet that hit
    # something on an earlier frame is simply absent from now on.
    for bx, by in frame_bullets[frame]:
        draw.rectangle((bx - 1, by, bx + 1, by + 6), fill=(100, 235, 255))

    draw.text((34, 307), "EVERY CONTRIBUTION IS A BULLET",
              fill=(125, 145, 170), font=ui_font)
    draw.text((W - 34, 307), "BUILD • SHIP • REPEAT", anchor="ra",
              fill=(125, 145, 170), font=ui_font)

    frames.append(image.convert("RGB"))

# ---------------- Encode as a compact, shared-palette GIF ----------------
# Saving RGB frames directly lets Pillow pick a fresh palette per frame,
# which bloats file size and can cause color flicker. Large GIFs are also
# more likely to be shown by GitHub as a static "click to play" thumbnail
# instead of autoplaying. Quantizing every frame to one shared palette
# keeps colors stable and the file small enough to autoplay normally.
sample_count = min(8, len(frames))
step = max(1, len(frames) // sample_count)
strip = Image.new("RGB", (W, H * sample_count))
for idx, i in enumerate(range(0, len(frames), step)):
    if idx >= sample_count:
        break
    strip.paste(frames[i], (0, idx * H))

palette_source = strip.quantize(colors=160, method=Image.MEDIANCUT)
quantized = [f.quantize(palette=palette_source, dither=Image.FLOYDSTEINBERG) for f in frames]

quantized[0].save(
    OUT / "arcade.gif",
    save_all=True,
    append_images=quantized[1:],
    duration=FRAME_MS,
    loop=0,
    optimize=True,
)

try:
    DATA.unlink()
except FileNotFoundError:
    pass

print(
    f"Generated with real collisions | "
    f"score={total}, level={level}, commits_7d={commits_7d}, "
    f"enemies={enemy_count}, bullets_fired={len(bullets)}, "
    f"fire_interval={fire_interval}"
)
