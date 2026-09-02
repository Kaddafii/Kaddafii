# Kaddafii Code Invaders — Fixed 20px Edition

This version fixes the previous workflow error and makes both supplied game sprites much smaller.

## Sprite size

```text
player.png → 20 × 20 px
enemy.png  → 20 × 20 px
```

The original uploaded PNGs are included unchanged in:

```text
.github/scripts/assets/
├── player.png
└── enemy.png
```

The generator only scales them to 20×20 at runtime using nearest-neighbor.

## Structure

```text
.github/
├── workflows/
│   └── arcade.yml
└── scripts/
    ├── generate_arcade.py
    └── assets/
        ├── player.png
        └── enemy.png
```

## README

```html
## 🎮 Kaddafii Code Invaders

<p align="center">
  <img
    src="https://raw.githubusercontent.com/Kaddafii/Kaddafii/output/arcade.gif"
    alt="Kaddafii Code Invaders"
    width="900"
  />
</p>

<p align="center">
  <sub>Every contribution is a bullet. Every project is a level.</sub>
</p>
```

## Run

1. Replace the old `.github` folder with this version.
2. Commit and push to `main`.
3. Open `Actions`.
4. Select `Update Kaddafii Code Invaders`.
5. Click `Run workflow`.

The workflow now creates `arcade-output` before fetching the GitHub contribution data.

It publishes the generated GIF to the `output` branch.

## Dynamic mapping

- Total contributions → SCORE
- Total contributions → LEVEL
- Last 7 days → bullet count
- Last 7 days → player movement
- Recent activity → enemy count
