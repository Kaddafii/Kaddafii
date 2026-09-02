# Kaddafii Code Invaders — Your Sprites

This package uses the two PNG files supplied in the conversation:

- `.github/scripts/assets/player.png` → your fighter jet
- `.github/scripts/assets/enemy.png` → your UFO/alien

They are only resized with nearest-neighbor scaling so the pixel-art style is retained.

## Install into Kaddafii/Kaddafii

```text
.github/
├── scripts/
│   ├── generate_arcade.py
│   └── assets/
│       ├── player.png
│       └── enemy.png
└── workflows/
    └── arcade.yml
```

Add this to README.md:

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

Then:

1. Commit and push the files to `main`.
2. Open `Actions`.
3. Select `Update Kaddafii Code Invaders`.
4. Click `Run workflow`.
5. Wait for the workflow to finish.
6. The GIF is published to the `output` branch.

The workflow also regenerates the GIF once per day.

## Activity mapping

- Total contributions → SCORE
- Total contributions → LEVEL
- Last 7 days → bullet count
- Last 7 days → player movement
- Recent activity → number of enemies
