# Pixel Art UI Demo

Python GUI project using `tkinter` + `Pillow`, with pixel-art sprite buttons.

## Run

```bash
pip install pillow
python pixel_ui.py
```

## Features

- custom `SpriteButton` with real generated image sprites
- text labels: `TRAIN`, `JOIN CLUB`, `BUY GEAR`, `FREESTYLE!`
- pressed state
- disabled state
- enable/disable all controls

## Requirements

- Python 3
- `tkinter` (built-in)
- `Pillow`

## Using your own sprites

Place transparent PNG sprites into `assets/sprites/` with filenames using a slug of the label:

- `<label>_normal.png`
- `<label>_pressed.png` (optional)
- `<label>_disabled.png` (optional)

Examples:

`TRAIN_normal.png`, `join_club_normal.png`, `buy_gear_normal.png`, `freestyle_normal.png`

If `*_pressed.png` or `*_disabled.png` are missing, the program will synthesize pressed/disabled states from the normal image.

## Font setup (PixeloidSans)

Put the font file at:

- `assets/fonts/PixeloidSans-Bold.ttf` (preferred)
- `assets/fonts/PixeloidSans-Regular.ttf`

If it exists there, it will be used for button labels. Otherwise it falls back to PressStart2P or DejaVu.
