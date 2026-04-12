import tkinter as tk
from tkinter import DISABLED, NORMAL

import argparse
import json
import os
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageSequence

import sound_player
from sound_player import play_click_sound, play_result_sound

try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

try:
    from inventory_ui import InventoryUI
except ImportError:
    InventoryUI = None

try:
    from selection_menu_ui import SelectionMenuUI
except ImportError:
    SelectionMenuUI = None

try:
    from action_menu_ui import ActionMenuUI
except ImportError:
    ActionMenuUI = None

# Layout constants (adjust menu geometry and initial position)
ASPECT_RATIO = (9, 16)
MENU_WIDTH = 500
MENU_HEIGHT = int(MENU_WIDTH * ASPECT_RATIO[1] / ASPECT_RATIO[0])
MENU_OFFSET_X = 300
MENU_OFFSET_Y = 150

# GIF overlay config
GIF_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "images")
GIF_DEFAULT_FILENAME = "hola-que-tal-como-va-todo-loco-a.gif"
GIF_INITIAL_X = 167
GIF_INITIAL_Y = 5
GIF_INITIAL_SCALE = 0.53
GIF_MIN_SCALE = 0.53
GIF_MAX_SCALE = 1.0

# Josuncio overlay config
JOSUNCIO_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "images", "josuncio")
JOSUNCIO_DEFAULT_FILENAME = "josuncio.png"
JOSUNCIO_INITIAL_X = 5
JOSUNCIO_INITIAL_Y = 5
JOSUNCIO_INITIAL_SCALE = 0.53
JOSUNCIO_MIN_SCALE = 0.53
JOSUNCIO_MAX_SCALE = 1.0

# claucho transparent video overlay config
CLAUCHO_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "assets", "claucho")
CLAUCHO_CHROMA_COLOR = "0x00D800"
CLAUCHO_INITIAL_X = -58
CLAUCHO_INITIAL_Y = 66
CLAUCHO_INITIAL_SCALE = 1.75
CLAUCHO_MIN_SCALE = 0.3
CLAUCHO_MAX_SCALE = 2.0

# button container anchor offset (from top-left of window)
BUTTON_OFFSET_X = 272
BUTTON_OFFSET_Y = 490
BUTTON_VERTICAL_SPACING = 12
BUTTON_SCALE = 0.45

# inventory overlay config
INVENTORY_OFFSET_X = 88
INVENTORY_OFFSET_Y = 104
INVENTORY_SCALE = 0.7
INVENTORY_BORDER = 2

# selection overlay config
SELECTION_OVERLAY_INITIAL_X = 22
SELECTION_OVERLAY_INITIAL_Y = 150
SELECTION_OVERLAY_INITIAL_SCALE = 0.45
SELECTION_OVERLAY_MIN_SCALE = 0.2
SELECTION_OVERLAY_MAX_SCALE = 1.0

# action menu overlay config
ACTION_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "actions")
ACTION_MENU_INITIAL_X = 279
ACTION_MENU_INITIAL_Y = 519
ACTION_MENU_INITIAL_SCALE = 0.3
ACTION_MENU_MIN_SCALE = 0.2
ACTION_MENU_MAX_SCALE = 1.0

# background asset config
BACKGROUND_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "assets", "images")
BACKGROUND_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "assets", "videos")
BACKGROUND_DEFAULT_FILENAME = "elInvernadero_crop.png"
TRAIN_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "images", "train")
MONEY_INDICATOR_PATH = os.path.join(os.path.dirname(__file__), "assets", "images", "money_indicator.png")
MONEY_INITIAL_X = 331
MONEY_INITIAL_Y = 835
MONEY_INITIAL_SCALE = 0.4
MONEY_MIN_SCALE = 0.2
MONEY_MAX_SCALE = 1.0


def make_sprite(label: str, width: int = 360, height: int = 72, outline: int = 3):
    # Draw at higher scale then shrink with NEAREST for crisp pixel art
    scale = 3
    w2, h2 = width * scale, height * scale
    img2 = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img2)

    # Surface placement (leave room for stepped extrusion)
    pad = 8 * scale
    surf_left = pad
    surf_top = pad
    surf_right = w2 - pad - 1
    surf_bottom = h2 - pad - 1 - (6 * scale)

    # Top surface stripes (strong bands like the reference)
    bands = [(44, 176, 92), (34, 150, 76), (54, 196, 104)]
    band_h = 6 * scale
    y = surf_top
    band_index = 0
    while y <= surf_bottom:
        c = bands[band_index % len(bands)]
        draw.rectangle([surf_left, y, surf_right, min(y + band_h - 1, surf_bottom)], fill=c)
        y += band_h
        band_index += 1

    # Inner bevel / highlight at top-left and shadow at bottom-right (stepped)
    light = (220, 255, 230)
    dark = (10, 45, 20)
    steps = 3 * scale
    for s in range(steps):
        # top-left highlight
        draw.rectangle([surf_left + s, surf_top + s, surf_right - s, surf_top + s], fill=light)
        draw.rectangle([surf_left + s, surf_top + s, surf_left + s, surf_bottom - s], fill=light)
        # bottom-right shadow
        draw.rectangle([surf_left + s, surf_bottom - s, surf_right - s, surf_bottom - s], fill=dark)
        draw.rectangle([surf_right - s, surf_top + s, surf_right - s, surf_bottom - s], fill=dark)

    # Stepped extrusion layers under the button to simulate depth
    extrude_steps = 6
    for layer in range(extrude_steps):
        offset = (layer + 1) * (2 * scale)
        color_step = max(0, 90 - layer * 8)
        layer_color = (color_step, color_step, color_step)
        lx0 = surf_left + layer * (1 * scale)
        ly0 = surf_bottom + 1 + layer * (2 * scale)
        lx1 = surf_right - layer * (1 * scale)
        ly1 = surf_bottom + 1 + (layer + 1) * (2 * scale)
        if lx0 <= lx1 and ly0 <= ly1:
            draw.rectangle([lx0, ly0, lx1, ly1], fill=layer_color)

    # Small light cap below for the glossy platform bottom
    cap_top = surf_bottom + 1 + extrude_steps * (2 * scale)
    draw.rectangle([surf_left + 1, cap_top, surf_right - 1, cap_top + (2 * scale)], fill=(230, 232, 238))

    # Staircase pixel corners (rounded feel but stepped)
    corner = 6 * scale
    for i in range(corner):
        v = i // scale
        # top-left
        draw.point((surf_left + i, surf_top + v), fill=dark)
        draw.point((surf_left + v, surf_top + i), fill=dark)
        # top-right
        draw.point((surf_right - i, surf_top + v), fill=dark)
        draw.point((surf_right - v, surf_top + i), fill=dark)
        # bottom-left
        draw.point((surf_left + i, surf_bottom - v), fill=dark)
        draw.point((surf_left + v, surf_bottom - i), fill=dark)
        # bottom-right
        draw.point((surf_right - i, surf_bottom - v), fill=dark)
        draw.point((surf_right - v, surf_bottom - i), fill=dark)

    # Pixel font selection (prefer PressStart2P if available)
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/pressstart2p/PressStart2P-Regular.ttf",
        "/usr/share/fonts/truetype/pressstart2p/PressStart2P.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in font_paths:
        try:
            font = ImageFont.truetype(p, 22 * scale)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Text placement and blocky outline + shadow
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = surf_left + (surf_right - surf_left - text_w) // 2
    text_y = surf_top + (surf_bottom - surf_top - text_h) // 2

    # dark shadow offset (lower-right) to create 3D glyph
    shadow_offset = 2 * scale
    draw.text((text_x + shadow_offset, text_y + shadow_offset), label, font=font, fill=(18, 30, 20))

    # thick pixel-outline by painting neighbors
    outline_offsets = [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, -2), (-2, 2), (2, 2),
                       (-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in outline_offsets:
        draw.text((text_x + dx, text_y + dy), label, font=font, fill=(0, 0, 0))

    # main text (bright)
    draw.text((text_x, text_y), label, font=font, fill=(255, 255, 255))

    # Downscale to target with nearest neighbor to keep pixels sharp
    return img2.resize((width, height), resample=Image.NEAREST)


def make_state_images(label: str, color: str = None, bg_color=None, press_shift: int = 4, return_pil: bool = False):
    # Try loading external PNG sprites first (transparent PNGs under assets/sprites/)
    def slug(s: str):
        s = s.lower()
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^a-z0-9_-]", "", s)
        return s

    def load_external(slabel: str):
        base_dir = os.path.join(os.path.dirname(__file__), "assets", "sprites")
        name = slug(slabel)
        # Helper: try multiple candidate filenames and return first existing
        def find_file(cands):
            for p in cands:
                full = os.path.join(base_dir, p)
                if os.path.exists(full):
                    return full
            return None

        normal_candidates = []
        pressed_candidates = []
        disabled_candidates = []
        if color:
            normal_candidates += [f"button_idle_{color}.png"]
            pressed_candidates += [f"button_pressed_{color}.png"]
            disabled_candidates += [f"{name}_{color}_disabled.png", f"{color}_disabled.png"]

        normal_candidates += [f"{name}_normal.png", f"{name}_idle.png", f"{name}.png", "button_normal.png", "button_idle.png", "button.png"]
        pressed_candidates += [f"{name}_pressed.png", f"{name}_down.png", f"{name}_active.png", "button_pressed.png", "button_down.png"]
        disabled_candidates += [f"{name}_disabled.png", f"{name}_grey.png", "button_disabled.png"]

        normal_p = find_file(normal_candidates)
        if not normal_p:
            return None

        try:
            im_normal = Image.open(normal_p).convert("RGBA")
        except Exception:
            return None

        pressed_p = find_file(pressed_candidates)
        if pressed_p:
            try:
                im_pressed = Image.open(pressed_p).convert("RGBA")
            except Exception:
                im_pressed = None
        else:
            overlay = Image.new("RGBA", im_normal.size, (0, 0, 0, 120))
            im_pressed = Image.alpha_composite(im_normal, overlay)

        disabled_p = find_file(disabled_candidates)
        if disabled_p:
            try:
                im_disabled = Image.open(disabled_p).convert("RGBA")
            except Exception:
                im_disabled = None
        else:
            im_disabled = im_normal.convert("LA").convert("RGBA")
            grey_edge = Image.new("RGBA", im_disabled.size, (120, 120, 120, 120))
            im_disabled = Image.alpha_composite(im_disabled, grey_edge)

        # Return PIL images (not PhotoImage) so caller can composite and overlay text
        return {"normal": im_normal, "pressed": im_pressed, "disabled": im_disabled}

    imgs = load_external(label)
    if imgs:
        # imgs contain PIL images; ensure pressed/disabled are bottom-aligned to normal size
        im_normal = imgs["normal"]
        w, h = im_normal.size

        def ensure_same_size(base_im, other_im):
            if other_im is None:
                return None
            ow, oh = other_im.size
            if ow == w and oh == h:
                return other_im
            # create transparent canvas and bottom-align other_im
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            x = (w - ow) // 2
            y = h - oh  # bottom align
            canvas.paste(other_im, (x, y), other_im)
            return canvas

        im_pressed = ensure_same_size(im_normal, imgs.get("pressed"))
        if im_pressed is None:
            overlay = Image.new("RGBA", im_normal.size, (0, 0, 0, 120))
            im_pressed = Image.alpha_composite(im_normal, overlay)

        im_disabled = ensure_same_size(im_normal, imgs.get("disabled"))
        if im_disabled is None:
            im_disabled = im_normal.convert("LA").convert("RGBA")
            grey_edge = Image.new("RGBA", im_disabled.size, (120, 120, 120, 120))
            im_disabled = Image.alpha_composite(im_disabled, grey_edge)

        # Draw the label text on top of these images using PixeloidSans the same as the title.
        # Prefer project font, then system font by fc-match, then fallback.
        project_fonts_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
        font_size = max(10, int(h * 0.28))

        # prefer bold PixeloidSans if available
        pixeloid_bold_path = os.path.join(project_fonts_dir, "PixeloidSans-Bold.ttf")
        pixeloid_path = os.path.join(project_fonts_dir, "PixeloidSans-Regular.ttf")
        if os.path.exists(pixeloid_bold_path):
            try:
                font = ImageFont.truetype(pixeloid_bold_path, font_size)
            except Exception:
                font = None
        elif os.path.exists(pixeloid_path):
            try:
                font = ImageFont.truetype(pixeloid_path, font_size)
            except Exception:
                font = None
        else:
            font = None

        if font is None:
            # Try fc-match to locate PixeloidSans on system
            try:
                import subprocess
                candidate = subprocess.check_output(["fc-match", "-f", "%{file}", "PixeloidSans"]).decode().strip()
                if candidate and os.path.exists(candidate):
                    font = ImageFont.truetype(candidate, font_size)
            except Exception:
                font = None

        if font is None:
            # fallback to PressStart2P from project font path, system path, or finally DejaVu
            pressstart_paths = [
                os.path.join(project_fonts_dir, "PressStart2P-Regular.ttf"),
                "/usr/share/fonts/truetype/pressstart2p/PressStart2P-Regular.ttf",
                "/usr/share/fonts/truetype/pressstart2p/PressStart2P.ttf",
            ]
            for p in pressstart_paths:
                if p and os.path.exists(p):
                    try:
                        font = ImageFont.truetype(p, font_size)
                        break
                    except Exception:
                        font = None

        if font is None:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        def draw_text_on(im, shift=0):
            d = ImageDraw.Draw(im)
            bbox = d.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            tx = (w - text_w) // 2
            ty = ((h - text_h) // 2) + shift
            # shadow
            d.text((tx + 2, ty + 2), label, font=font, fill=(10, 10, 10))
            # outline
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                d.text((tx + dx, ty + dy), label, font=font, fill=(0, 0, 0))
            d.text((tx, ty), label, font=font, fill=(255, 255, 255))

        draw_text_on(im_normal, shift=-30)
        draw_text_on(im_pressed, shift=press_shift)
        draw_text_on(im_disabled, shift=0)

        # Composite over background color if provided
        if bg_color:
            bgimg = Image.new("RGBA", im_normal.size, (bg_color[0], bg_color[1], bg_color[2], 255))
            im_normal = Image.alpha_composite(bgimg, im_normal)
            im_pressed = Image.alpha_composite(bgimg, im_pressed)
            im_disabled = Image.alpha_composite(bgimg, im_disabled)

        if return_pil:
            return {"normal": im_normal, "pressed": im_pressed, "disabled": im_disabled}
        return {
            "normal": ImageTk.PhotoImage(im_normal),
            "pressed": ImageTk.PhotoImage(im_pressed),
            "disabled": ImageTk.PhotoImage(im_disabled),
        }

    # Fallback to generated sprites when external sprites unavailable
    base = make_sprite(label)
    pressed = base.copy()
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 64))
    pressed = Image.alpha_composite(pressed, overlay)

    disabled = base.copy().convert("LA").convert("RGBA")
    grey_edge = Image.new("RGBA", base.size, (120, 120, 120, 130))
    disabled = Image.alpha_composite(disabled, grey_edge)

    # If a background color was provided, composite images over it so transparency matches UI background
    if bg_color:
        bgimg = Image.new("RGBA", base.size, (bg_color[0], bg_color[1], bg_color[2], 255))
        base = Image.alpha_composite(bgimg, base)
        pressed = Image.alpha_composite(bgimg, pressed)
        disabled = Image.alpha_composite(bgimg, disabled)

    # Optionally shift pressed image (visual press) by press_shift pixels down
    if press_shift:
        w, h = base.size
        temp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        temp.paste(pressed, (0, press_shift))
        pressed = temp

    if return_pil:
        return {"normal": base, "pressed": pressed, "disabled": disabled}
    return {
        "normal": ImageTk.PhotoImage(base),
        "pressed": ImageTk.PhotoImage(pressed),
        "disabled": ImageTk.PhotoImage(disabled),
    }


class SpriteButton:
    def __init__(self, canvas: tk.Canvas, x: int, y: int, label: str, color: str = None, command=None, scale: float = 1.0):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.command = command
        self.enabled = True
        self.pressed = False
        self.color = color
        self.scale = scale

        self.pil_images = make_state_images(label, color=self.color if hasattr(self, 'color') else None, bg_color=None, press_shift=-10, return_pil=True)
        self.images = self._make_photo_images(self.scale)
        self.image_item = self.canvas.create_image(self.x, self.y, anchor="nw", image=self.images["normal"])
        self.canvas.tag_bind(self.image_item, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.image_item, "<ButtonRelease-1>", self.on_release)

    def _make_photo_images(self, scale: float):
        converted = {}
        for key, pil_img in self.pil_images.items():
            if scale != 1.0:
                new_size = (max(1, int(pil_img.width * scale)), max(1, int(pil_img.height * scale)))
                if hasattr(Image, "Resampling"):
                    resample_method = Image.Resampling.LANCZOS
                else:
                    resample_method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
                pil_img = pil_img.resize(new_size, resample_method)
            converted[key] = ImageTk.PhotoImage(pil_img)
        return converted

    @property
    def width(self):
        return self.images["normal"].width()

    @property
    def height(self):
        return self.images["normal"].height()

    def update_scale(self, scale: float):
        self.scale = scale
        self.images = self._make_photo_images(scale)
        current = "pressed" if self.pressed else "normal"
        self.canvas.itemconfigure(self.image_item, image=self.images[current])

    def on_press(self, event):
        if not self.enabled:
            return
        play_click_sound()
        self.pressed = True
        self.canvas.itemconfigure(self.image_item, image=self.images["pressed"])

    def on_release(self, event):
        if not self.enabled:
            return
        self.pressed = False
        self.canvas.itemconfigure(self.image_item, image=self.images["normal"])
        if self.command:
            self.command()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self.canvas.itemconfigure(self.image_item, image=self.images["normal"] if enabled else self.images["disabled"])


def main(debug: bool = False):
    root = tk.Tk()
    root.title("Pixel Art Button UI")
    root.configure(bg="#120f1e")
    root.geometry(f"{MENU_WIDTH}x{MENU_HEIGHT}+{MENU_OFFSET_X}+{MENU_OFFSET_Y}")
    root.resizable(False, False)

    main_frame = tk.Frame(root, bg="#120f1e")
    main_frame.pack(fill='both', expand=True)

    # background as canvas image so we can position/scale it
    canvas = tk.Canvas(main_frame, width=MENU_WIDTH, height=MENU_HEIGHT, highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    bg_original_pil = None
    bg_resized_cache = None
    bg_item = None
    background_asset_dir = BACKGROUND_IMAGE_DIR
    background_video_dir = BACKGROUND_VIDEO_DIR
    claucho_video_dir = CLAUCHO_VIDEO_DIR
    background_files = []
    if os.path.exists(background_asset_dir):
        background_files += sorted([f for f in os.listdir(background_asset_dir) if f.lower().endswith(".png")])
    if os.path.exists(background_video_dir):
        background_files += sorted([f for f in os.listdir(background_video_dir) if f.lower().endswith(".mp4")])
    background_selected_filename = background_files[0] if background_files else BACKGROUND_DEFAULT_FILENAME
    background_selected = tk.StringVar(value=background_selected_filename)
    background_photo = None
    background_video_reader = None
    background_video_running = False
    background_video_delay = 100
    background_after_id = None
    training_result_overlay = None
    gif_after_id = None
    claucho_files = sorted([f for f in os.listdir(claucho_video_dir) if f.lower().endswith(".mp4")]) if os.path.exists(claucho_video_dir) else []
    claucho_selected_filename = claucho_files[0] if claucho_files else ""
    claucho_selected = tk.StringVar(value=claucho_selected_filename)
    claucho_process = None
    claucho_width = None
    claucho_height = None
    claucho_frame_size = None
    claucho_video_running = False
    claucho_video_delay = 100
    claucho_after_id = None
    claucho_photo = None
    claucho_item = None
    claucho_last_frame = None
    claucho_has_alpha = False
    claucho_x = tk.IntVar(value=CLAUCHO_INITIAL_X)
    claucho_y = tk.IntVar(value=CLAUCHO_INITIAL_Y)
    claucho_scale = tk.DoubleVar(value=CLAUCHO_INITIAL_SCALE)
    overlays_visible = True
    menu_compact = False
    money_x = tk.IntVar(value=MONEY_INITIAL_X)
    money_y = tk.IntVar(value=MONEY_INITIAL_Y)
    money_scale = tk.DoubleVar(value=MONEY_INITIAL_SCALE)
    money_amount = tk.StringVar(value="100")
    money_original = None
    money_photo = None
    money_item = None
    money_text_item = None
    money_font = ("PressStart2P", 14)
    money_flash_after_id = None

    def background_path_for(filename):
        if not filename:
            return None
        if filename.lower().endswith(".png"):
            return os.path.join(background_asset_dir, filename)
        if filename.lower().endswith(".mp4"):
            return os.path.join(background_video_dir, filename)
        return None

    def is_training_video(filename):
        if not filename:
            return False
        return "training" in os.path.splitext(filename)[0].lower()

    def clear_training_result_overlay():
        nonlocal training_result_overlay
        if training_result_overlay is not None:
            overlay = training_result_overlay
            training_result_overlay = None
            overlay.close()

    def show_training_result_overlay():
        nonlocal training_result_overlay
        if SelectionMenuUI is None:
            print("SelectionMenuUI module not available")
            return
        if training_result_overlay is not None:
            training_result_overlay.close()
            training_result_overlay = None
        training_result_overlay = SelectionMenuUI(
            root,
            TRAIN_ASSET_DIR,
            "Training Result",
            embedded=True,
            x=SELECTION_OVERLAY_INITIAL_X,
            y=SELECTION_OVERLAY_INITIAL_Y,
            scale=SELECTION_OVERLAY_INITIAL_SCALE,
            on_close=clear_training_result_overlay,
        )
        training_result_overlay.show_result()
        play_result_sound()
        training_result_overlay.lift()

    def claucho_path_for(filename):
        return os.path.join(claucho_video_dir, filename) if filename else None

    def make_claucho_photo(image: Image.Image, scale: float = 1.0):
        if image is None:
            return None
        if scale != 1.0:
            width, height = image.size
            target_width = max(1, int(width * scale))
            target_height = max(1, int(height * scale))
            image = image.resize((target_width, target_height), Image.BILINEAR)
        # Composite onto cached background for proper alpha transparency in tkinter
        if bg_resized_cache is not None:
            composite = bg_resized_cache.copy()
            cx, cy = claucho_x.get(), claucho_y.get()
            composite.alpha_composite(image, (cx, cy))
            photo = ImageTk.PhotoImage(composite)
        else:
            photo = ImageTk.PhotoImage(image)
        root.claucho_photo = photo
        return photo

    def probe_video_info(path):
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height,avg_frame_rate,tags",
                    "-of",
                    "json",
                    path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            stream = data["streams"][0]
            width = int(stream["width"])
            height = int(stream["height"])
            fps=60
            alpha_mode = False
            tags = stream.get("tags") or {}
            if tags.get("alpha_mode") in {"1", "yes", "true"}:
                alpha_mode = True
            return width, height, fps, alpha_mode
        except Exception:
            return None, None, None, False

    def open_claucho_process(path):
        nonlocal claucho_process, claucho_width, claucho_height, claucho_frame_size, claucho_video_delay, claucho_has_alpha
        if claucho_process is not None:
            try:
                claucho_process.kill()
                claucho_process.wait()
            except Exception:
                pass
            claucho_process = None
        width, height, fps, alpha_mode = probe_video_info(path)
        claucho_width = width
        claucho_height = height
        if fps and fps > 0:
            claucho_video_delay = int(1000 / fps)
        claucho_has_alpha = alpha_mode
        if not claucho_width or not claucho_height:
            print(f"Warning: could not determine claucho video size for '{path}'")
            return
        claucho_frame_size = claucho_width * claucho_height * 4
        claucho_process = subprocess.Popen(
            [
                "ffmpeg",
                "-v",
                "error",
                "-stream_loop",
                "-1",
                "-i",
                path,
                "-vf",
                f"chromakey={CLAUCHO_CHROMA_COLOR}:0.12:0.18,format=rgba",
                "-pix_fmt",
                "rgba",
                "-f",
                "rawvideo",
                "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def read_claucho_frame():
        if claucho_process is None or claucho_frame_size is None:
            return None
        try:
            data = claucho_process.stdout.read(claucho_frame_size)
            if not data or len(data) != claucho_frame_size:
                return None
            return Image.frombuffer("RGBA", (claucho_width, claucho_height), data, "raw", "RGBA", 0, 1)
        except Exception:
            return None

    def pause_claucho_video():
        nonlocal claucho_video_running, claucho_after_id
        claucho_video_running = False
        if claucho_after_id is not None:
            try:
                root.after_cancel(claucho_after_id)
            except Exception:
                pass
        claucho_after_id = None
        if claucho_item is not None:
            canvas.itemconfigure(claucho_item, state="hidden")

    def stop_claucho_video():
        nonlocal claucho_process
        pause_claucho_video()
        if claucho_process is not None:
            try:
                claucho_process.kill()
                claucho_process.wait()
            except Exception:
                pass
        claucho_process = None

    def resume_claucho_video_if_ready():
        nonlocal claucho_video_running
        if not claucho_selected.get() or claucho_process is None:
            return
        if background_selected.get().lower().endswith(".mp4"):
            pause_claucho_video()
            return
        if claucho_item is not None:
            canvas.itemconfigure(claucho_item, state="normal")
        if not claucho_video_running:
            claucho_video_running = True
            claucho_video_tick()

    def load_claucho_video(filename):
        nonlocal claucho_item, claucho_photo, claucho_last_frame
        stop_claucho_video()
        path = claucho_path_for(filename)
        if not path or not os.path.exists(path):
            return
        open_claucho_process(path)
        if claucho_process is None:
            return
        claucho_last_frame = read_claucho_frame()
        if claucho_last_frame is None:
            return
        photo = make_claucho_photo(claucho_last_frame, claucho_scale.get())
        if photo is None:
            return
        if claucho_item is None:
            claucho_item = canvas.create_image(0, 0, anchor="nw", image=photo)
        else:
            canvas.itemconfigure(claucho_item, image=photo)
            canvas.coords(claucho_item, 0, 0)
        if bg_item is not None:
            canvas.tag_raise(claucho_item, bg_item)
        resume_claucho_video_if_ready()

    def claucho_video_tick():
        nonlocal claucho_video_running, claucho_photo, claucho_item, claucho_after_id, claucho_last_frame
        if not claucho_video_running or claucho_process is None:
            return
        claucho_last_frame = read_claucho_frame()
        if claucho_last_frame is None:
            stop_claucho_video()
            load_claucho_video(claucho_selected.get())
            return
        photo = make_claucho_photo(claucho_last_frame, claucho_scale.get())
        if photo is None:
            claucho_video_running = False
            return
        if claucho_item is not None:
            canvas.itemconfigure(claucho_item, image=photo)
            canvas.coords(claucho_item, 0, 0)
        claucho_after_id = root.after(claucho_video_delay, claucho_video_tick)

    def make_background_photo(image: Image.Image, *, video: bool = False):
        if image is None:
            return None
        if hasattr(Image, "Resampling"):
            resample_method = Image.Resampling.LANCZOS
        else:
            resample_method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
        resized = image.resize((MENU_WIDTH, MENU_HEIGHT), resample_method)
        photo = ImageTk.PhotoImage(resized)
        root.background_photo = photo
        return photo

    def stop_background_video():
        nonlocal background_video_running, background_video_reader, background_after_id
        background_video_running = False
        if background_after_id is not None:
            try:
                root.after_cancel(background_after_id)
            except Exception:
                pass
        background_after_id = None
        if background_video_reader is not None:
            try:
                background_video_reader.close()
            except Exception:
                pass
            background_video_reader = None

    def load_background_file(filename):
        nonlocal bg_original_pil, bg_resized_cache, background_photo, bg_item, background_video_reader, background_video_running, background_video_delay
        stop_background_video()
        clear_training_result_overlay()
        path = background_path_for(filename)
        if not path or not os.path.exists(path):
            return
        if filename.lower().endswith(".png"):
            try:
                bg_original_pil = Image.open(path).convert("RGBA")
            except Exception as e:
                print(f"Warning: could not load background image '{filename}': {e}")
                return
            if hasattr(Image, "Resampling"):
                _resample = Image.Resampling.LANCZOS
            else:
                _resample = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
            bg_resized_cache = bg_original_pil.resize((MENU_WIDTH, MENU_HEIGHT), _resample)
            photo = make_background_photo(bg_original_pil)
            if photo is None:
                return
            if bg_item is None:
                bg_item = canvas.create_image(0, 0, anchor="nw", image=photo)
            else:
                canvas.itemconfigure(bg_item, image=photo)
                canvas.coords(bg_item, 0, 0)
            resume_claucho_video_if_ready()
            return
        if filename.lower().endswith(".mp4"):
            if not IMAGEIO_AVAILABLE:
                print("Video support unavailable; install imageio/imageio-ffmpeg in the .venv")
                return
            try:
                reader = imageio.get_reader(path)
                meta = reader.get_meta_data()
                fps = 60
                background_video_delay = int(1000 / fps) if fps else 100
                frame = reader.get_data(0)
                background_video_reader = reader
            except Exception as e:
                print(f"Warning: could not load background video '{filename}': {e}")
                background_video_reader = None
                return
            bg_original_pil = Image.fromarray(frame)
            bg_resized_cache = bg_original_pil.resize((MENU_WIDTH, MENU_HEIGHT), Image.BILINEAR)
            photo = make_background_photo(bg_original_pil)
            if photo is None:
                return
            if bg_item is None:
                bg_item = canvas.create_image(0, 0, anchor="nw", image=photo)
            else:
                canvas.itemconfigure(bg_item, image=photo)
                canvas.coords(bg_item, 0, 0)
            pause_claucho_video()
            return

    def background_video_tick():
        nonlocal background_video_running, background_video_reader, background_photo, bg_item, background_after_id
        if not background_video_running or background_video_reader is None:
            return
        try:
            frame = background_video_reader.get_next_data()
        except Exception:
            selected = background_selected.get()
            if background_video_reader is not None:
                try:
                    background_video_reader.close()
                except Exception:
                    pass
            background_video_reader = None
            if is_training_video(selected):
                background_video_running = False
                show_training_result_overlay()
                return
            try:
                load_background_file(selected)
            except Exception:
                background_video_running = False
                return
            background_video_running = True
            background_after_id = root.after(background_video_delay, background_video_tick)
            return
        image = Image.fromarray(frame)
        photo = make_background_photo(image)
        if photo is None:
            background_video_running = False
            return
        if bg_item is not None:
            canvas.itemconfigure(bg_item, image=photo)
            canvas.coords(bg_item, 0, 0)
        background_after_id = root.after(background_video_delay, background_video_tick)

    def play_background():
        nonlocal background_video_running
        selected = background_selected.get()
        if selected.lower().endswith(".mp4"):
            if not IMAGEIO_AVAILABLE:
                print("Video support unavailable; install imageio/imageio-ffmpeg in the .venv")
                return
            stop_background_video()
            load_background_file(selected)
            if background_video_reader is None:
                return
            background_video_running = True
            background_video_tick()
        else:
            load_background_file(selected)

    if background_selected_filename:
        load_background_file(background_selected_filename)
    if claucho_selected_filename:
        load_claucho_video(claucho_selected_filename)

    gif_asset_dir = GIF_ASSET_DIR
    gif_files = sorted([f for f in os.listdir(gif_asset_dir) if f.lower().endswith(".gif")])
    gif_frames = []
    gif_durations = []
    gif_photo_frames = []
    gif_item = None
    gif_running = False
    gif_current_frame = 0
    gif_selected_filename = gif_files[0] if gif_files else GIF_DEFAULT_FILENAME
    gif_selected = tk.StringVar(value=gif_selected_filename)
    gif_x = tk.IntVar(value=GIF_INITIAL_X)
    gif_y = tk.IntVar(value=GIF_INITIAL_Y)
    gif_scale = tk.DoubleVar(value=GIF_INITIAL_SCALE)

    josuncio_asset_dir = JOSUNCIO_ASSET_DIR
    josuncio_files = sorted([f for f in os.listdir(josuncio_asset_dir) if f.lower().endswith(".png")])
    josuncio_original = None
    josuncio_photo = None
    josuncio_item = None
    josuncio_selected_filename = josuncio_files[0] if josuncio_files else JOSUNCIO_DEFAULT_FILENAME
    josuncio_selected = tk.StringVar(value=josuncio_selected_filename)
    josuncio_x = tk.IntVar(value=JOSUNCIO_INITIAL_X)
    josuncio_y = tk.IntVar(value=JOSUNCIO_INITIAL_Y)
    josuncio_scale = tk.DoubleVar(value=JOSUNCIO_INITIAL_SCALE)

    def gif_path_for(filename):
        return os.path.join(gif_asset_dir, filename) if filename else None

    def josuncio_path_for(filename):
        return os.path.join(josuncio_asset_dir, filename) if filename else None

    if josuncio_selected_filename:
        try:
            josuncio_original = Image.open(josuncio_path_for(josuncio_selected_filename)).convert("RGBA")
        except Exception as e:
            print(f"Warning: could not load Josuncio image '{josuncio_selected_filename}': {e}")

    def make_gif_photos(scale: float):
        photos = []
        if not gif_frames:
            return photos
        if hasattr(Image, "Resampling"):
            resample_method = Image.Resampling.LANCZOS
        else:
            resample_method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
        for frame in gif_frames:
            size = (max(1, int(frame.width * scale)), max(1, int(frame.height * scale)))
            resized = frame.resize(size, resample_method)
            photos.append(ImageTk.PhotoImage(resized))
        root.gif_photo_frames = photos
        return photos

    def make_josuncio_photo(scale: float):
        nonlocal josuncio_photo
        if josuncio_original is None:
            return None
        if hasattr(Image, "Resampling"):
            resample_method = Image.Resampling.LANCZOS
        else:
            resample_method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
        size = (max(1, int(josuncio_original.width * scale)), max(1, int(josuncio_original.height * scale)))
        resized = josuncio_original.resize(size, resample_method)
        josuncio_photo = ImageTk.PhotoImage(resized)
        root.josuncio_photo = josuncio_photo
        return josuncio_photo

    def animate_gif_frame(index: int):
        nonlocal gif_current_frame, gif_running, gif_item, gif_after_id
        if not gif_photo_frames or gif_item is None:
            gif_running = False
            gif_after_id = None
            return
        gif_current_frame = index
        canvas.itemconfigure(gif_item, image=gif_photo_frames[index])
        if index + 1 < len(gif_photo_frames):
            gif_running = True
            delay = gif_durations[index] if index < len(gif_durations) else 100
            gif_after_id = root.after(delay, lambda idx=index + 1: animate_gif_frame(idx))
        else:
            gif_running = False
            gif_after_id = None

    def start_gif_animation():
        nonlocal gif_current_frame, gif_running, gif_item, gif_after_id
        if not gif_photo_frames:
            return
        if gif_after_id is not None:
            try:
                root.after_cancel(gif_after_id)
            except Exception:
                pass
            gif_after_id = None
        gif_running = True
        gif_current_frame = 0
        if gif_item is None:
            create_gif_overlay()
            return
        animate_gif_frame(0)

    def update_gif_photos():
        nonlocal gif_photo_frames, gif_item
        if not gif_frames:
            return
        gif_photo_frames = make_gif_photos(gif_scale.get())
        if not gif_photo_frames:
            return
        if gif_item is None:
            gif_item = canvas.create_image(gif_x.get(), gif_y.get(), anchor="nw", image=gif_photo_frames[0])
        else:
            current = min(gif_current_frame, len(gif_photo_frames) - 1)
            canvas.itemconfigure(gif_item, image=gif_photo_frames[current])
        canvas.coords(gif_item, gif_x.get(), gif_y.get())

    def load_gif_file(filename):
        nonlocal gif_frames, gif_durations, gif_photo_frames, gif_current_frame, gif_running
        gif_frames = []
        gif_durations = []
        gif_photo_frames = []
        gif_current_frame = 0
        gif_running = False
        path = gif_path_for(filename)
        if not path or not os.path.exists(path):
            return
        try:
            gif_source = Image.open(path)
            for frame in ImageSequence.Iterator(gif_source):
                gif_frames.append(frame.convert("RGBA"))
                gif_durations.append(frame.info.get("duration", 100))
        except Exception as e:
            print(f"Warning: could not load GIF image '{filename}': {e}")
        update_gif_photos()

    if gif_selected_filename:
        load_gif_file(gif_selected_filename)

    def update_gif_layout(*args):
        if gif_item is None and gif_frames:
            create_gif_overlay()
            return
        if gif_item is None:
            return
        canvas.coords(gif_item, gif_x.get(), gif_y.get())
        update_gif_photos()

    def update_josuncio_layout(*args):
        nonlocal josuncio_item
        if josuncio_original is None:
            return
        photo = make_josuncio_photo(josuncio_scale.get())
        if photo is None:
            return
        if josuncio_item is None:
            josuncio_item = canvas.create_image(josuncio_x.get(), josuncio_y.get(), anchor="nw", image=photo)
        else:
            canvas.itemconfigure(josuncio_item, image=photo)
            canvas.coords(josuncio_item, josuncio_x.get(), josuncio_y.get())
        if not overlays_visible:
            canvas.itemconfigure(josuncio_item, state="hidden")

    def load_josuncio_file(filename):
        nonlocal josuncio_original, josuncio_photo, josuncio_item
        path = josuncio_path_for(filename)
        josuncio_original = None
        josuncio_photo = None
        if not path or not os.path.exists(path):
            return
        try:
            josuncio_original = Image.open(path).convert("RGBA")
        except Exception as e:
            print(f"Warning: could not load Josuncio image '{filename}': {e}")
        if josuncio_item is not None:
            photo = make_josuncio_photo(josuncio_scale.get())
            if photo is not None:
                canvas.itemconfigure(josuncio_item, image=photo)

    def make_money_photo(scale: float):
        nonlocal money_photo
        if money_original is None:
            return None
        if hasattr(Image, "Resampling"):
            resample_method = Image.Resampling.LANCZOS
        else:
            resample_method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC
        size = (
            max(1, int(money_original.width * scale)),
            max(1, int(money_original.height * scale)),
        )
        resized = money_original.resize(size, resample_method)
        money_photo = ImageTk.PhotoImage(resized)
        root.money_photo = money_photo
        return money_photo

    def update_money_layout(*args):
        nonlocal money_item, money_photo, money_text_item
        if money_original is None:
            return
        photo = make_money_photo(money_scale.get())
        if photo is None:
            return
        if money_item is None:
            money_item = canvas.create_image(money_x.get(), money_y.get(), anchor="nw", image=photo)
        else:
            canvas.itemconfigure(money_item, image=photo)
            canvas.coords(money_item, money_x.get(), money_y.get())
        text_x = money_x.get() + photo.width() // 2
        text_y = money_y.get() + photo.height() // 2
        if money_text_item is None:
            money_text_item = canvas.create_text(
                text_x,
                text_y,
                text=money_amount.get(),
                fill="yellow",
                font=money_font,
                anchor="center",
            )
        else:
            canvas.coords(money_text_item, text_x, text_y)
            canvas.itemconfigure(money_text_item, text=money_amount.get())

    if os.path.exists(MONEY_INDICATOR_PATH):
        try:
            money_original = Image.open(MONEY_INDICATOR_PATH).convert("RGBA")
        except Exception as e:
            print(f"Warning: could not load money indicator: {e}")

    money_amount.trace_add("write", lambda *args: update_money_layout())

    def adjust_money(delta: int):
        try:
            current = int(money_amount.get())
        except ValueError:
            current = 0
        money_amount.set(str(current + delta))
        update_money_layout()

    def flash_money_error():
        nonlocal money_flash_after_id
        if money_text_item is None:
            return
        canvas.itemconfigure(money_text_item, fill="red")
        if money_flash_after_id is not None:
            try:
                root.after_cancel(money_flash_after_id)
            except Exception:
                pass
        def restore():
            nonlocal money_flash_after_id
            if money_text_item is not None:
                canvas.itemconfigure(money_text_item, fill="yellow")
            money_flash_after_id = None
        money_flash_after_id = root.after(200, restore)

    def create_gif_overlay():
        nonlocal gif_item, gif_photo_frames
        if not gif_frames:
            return
        gif_photo_frames = make_gif_photos(gif_scale.get())
        if not gif_photo_frames:
            return
        if gif_item is None:
            gif_item = canvas.create_image(gif_x.get(), gif_y.get(), anchor="nw", image=gif_photo_frames[0])
        else:
            canvas.itemconfigure(gif_item, image=gif_photo_frames[0])
        root.gif_photo_frames = gif_photo_frames
        if overlays_visible:
            canvas.itemconfigure(gif_item, state="normal")
        else:
            canvas.itemconfigure(gif_item, state="hidden")
        start_gif_animation()

    button_x = tk.IntVar(value=BUTTON_OFFSET_X)
    button_y = tk.IntVar(value=BUTTON_OFFSET_Y)
    button_scale = tk.DoubleVar(value=BUTTON_SCALE)
    inv_x = tk.IntVar(value=INVENTORY_OFFSET_X)
    inv_y = tk.IntVar(value=INVENTORY_OFFSET_Y)
    inv_scale = tk.DoubleVar(value=INVENTORY_SCALE)
    selection_x = tk.IntVar(value=SELECTION_OVERLAY_INITIAL_X)
    selection_y = tk.IntVar(value=SELECTION_OVERLAY_INITIAL_Y)
    selection_scale = tk.DoubleVar(value=SELECTION_OVERLAY_INITIAL_SCALE)
    action_x = tk.IntVar(value=ACTION_MENU_INITIAL_X)
    action_y = tk.IntVar(value=ACTION_MENU_INITIAL_Y)
    action_scale = tk.DoubleVar(value=ACTION_MENU_INITIAL_SCALE)
    action_selected = tk.StringVar(value="None")
    gif_x = tk.IntVar(value=GIF_INITIAL_X)
    gif_y = tk.IntVar(value=GIF_INITIAL_Y)
    gif_scale = tk.DoubleVar(value=GIF_INITIAL_SCALE)
    josuncio_x = tk.IntVar(value=JOSUNCIO_INITIAL_X)
    josuncio_y = tk.IntVar(value=JOSUNCIO_INITIAL_Y)
    josuncio_scale = tk.DoubleVar(value=JOSUNCIO_INITIAL_SCALE)

    button_specs = [
        ("TRAIN", "green"),
        ("JOIN CLUB", "green"),
        ("BUY GEAR", "green"),
        ("INVENTORY", "blue"),
        ("FREESTYLE!", "red"),
    ]
    buttons = []
    inventory_frame = None
    inventory_view = None
    inventory_state = {}
    selection_overlay = None
    action_overlay = None

    def clear_action():
        nonlocal action_overlay
        action_overlay = None

    def close_action():
        nonlocal action_overlay
        if action_overlay is not None:
            overlay = action_overlay
            action_overlay = None
            overlay.close()

    def open_action_menu(menu_name):
        nonlocal action_overlay
        if ActionMenuUI is None:
            print("ActionMenuUI module not available")
            return
        close_action()
        action_overlay = ActionMenuUI(
            canvas,
            ACTION_ASSET_DIR,
            menu_name,
            x=action_x.get(),
            y=action_y.get(),
            scale=action_scale.get(),
            on_close=clear_action,
        )

    def on_action_selected(*args):
        choice = action_selected.get()
        if choice == "None":
            close_action()
        else:
            open_action_menu(choice)

    def update_action_layout(*args):
        if action_overlay is None:
            return
        action_overlay.set_transform(action_x.get(), action_y.get(), action_scale.get())

    held_keys = set()
    train_button_pressed = None

    def press_train_button():
        nonlocal train_button_pressed
        if train_button_pressed is not None:
            return
        for btn in buttons:
            if getattr(btn, "label", "") == "TRAIN":
                btn.on_press(None, play_sound=False)
                train_button_pressed = btn
                return

    def release_train_button():
        nonlocal train_button_pressed
        if train_button_pressed is None:
            return
        train_button_pressed.on_release(None)
        train_button_pressed = None

    def on_arrow_key(direction):
        if action_overlay is not None and hasattr(action_overlay, "press_direction"):
            action_overlay.press_direction(direction)
            held_keys.add(direction)
            return
        if direction == "up":
            press_train_button()
            held_keys.add(direction)

    def on_arrow_key_release(direction):
        if direction not in held_keys:
            return
        held_keys.discard(direction)
        if action_overlay is not None and hasattr(action_overlay, "release_direction"):
            action_overlay.release_direction(direction)
            return
        if direction == "up":
            release_train_button()

    def on_key_press(event):
        if event.keysym not in {"Up", "Left", "Down", "Right"}:
            return
        direction = event.keysym.lower()
        if direction in held_keys:
            return
        on_arrow_key(direction)

    def on_key_release(event):
        if event.keysym not in {"Up", "Left", "Down", "Right"}:
            return
        on_arrow_key_release(event.keysym.lower())

    def rebuild_inventory():
        nonlocal inventory_frame, inventory_view, inventory_state
        if InventoryUI is None:
            return
        if inventory_view is not None:
            inventory_state = inventory_view.get_state()
        if inventory_frame is not None:
            inventory_frame.destroy()
            inventory_frame = None
            inventory_view = None
        scale = inv_scale.get()
        inventory_frame = tk.Frame(root, bg="", bd=INVENTORY_BORDER, relief="ridge")
        inventory_frame.place(x=inv_x.get(), y=inv_y.get())

        def close_inventory():
            nonlocal inventory_frame, inventory_view, inventory_state
            if inventory_view is not None:
                inventory_state = inventory_view.get_state()
            if inventory_frame is not None:
                inventory_frame.destroy()
            inventory_frame = None
            inventory_view = None

        def on_inventory_drop(item_id, slot_id, slot_name, previous_slot, asset):
            video_map = {
                ("item_pants_cats", "legs"): "2_gatos_green_r_4.mp4",
                ("item_tshirt_pink", "chest"): "3_madriders_green_r_4.mp4",
                ("item_egg_protector", "waist"): "4_egg_green_r_4.mp4",
            }
            video = video_map.get((item_id, slot_name.lower()))
            if video:
                claucho_selected.set(video)
                load_claucho_video(video)

        inventory_view = InventoryUI(
            inventory_frame,
            debug=debug,
            embedded=True,
            scale=scale,
            item_state=inventory_state,
            on_close=close_inventory,
            on_drop=on_inventory_drop,
        )
        inventory_frame.update_idletasks()
        inventory_frame.place_configure(width=inventory_view.width, height=inventory_view.height)
        inventory_frame.lift()

    def update_inventory_layout(*args):
        if inventory_frame is None:
            return
        inventory_frame.place_configure(x=inv_x.get(), y=inv_y.get())
        if float(inv_scale.get()) != inventory_view.scale:
            rebuild_inventory()

    def update_selection_layout(*args):
        if selection_overlay is None:
            return
        selection_overlay.set_transform(selection_x.get(), selection_y.get(), selection_scale.get())

    def update_claucho_layout(*args):
        nonlocal claucho_photo
        if claucho_item is None or claucho_last_frame is None:
            return
        photo = make_claucho_photo(claucho_last_frame, claucho_scale.get())
        if photo is None:
            return
        claucho_photo = photo
        canvas.itemconfigure(claucho_item, image=photo)
        canvas.coords(claucho_item, 0, 0)

    def clear_selection():
        nonlocal selection_overlay
        selection_overlay = None

    def close_selection():
        nonlocal selection_overlay
        if selection_overlay is not None:
            overlay = selection_overlay
            selection_overlay = None
            overlay.close()

    def open_selection(asset_dir, title):
        nonlocal selection_overlay
        if SelectionMenuUI is None:
            print("SelectionMenuUI module not available")
            return
        if selection_overlay is not None:
            selection_overlay.lift()
            return

        def on_selection_result():
            if title == "Join Club":
                adjust_money(-2)
            elif title == "Shop":
                adjust_money(-10)

        selection_overlay = SelectionMenuUI(
            root,
            asset_dir,
            title,
            embedded=True,
            x=SELECTION_OVERLAY_INITIAL_X,
            y=SELECTION_OVERLAY_INITIAL_Y,
            scale=SELECTION_OVERLAY_INITIAL_SCALE,
            on_close=clear_selection,
            on_error=flash_money_error if title == "Shop" else None,
            on_result=on_selection_result,
        )

    def on_button_click(label: str):
        if label == "INVENTORY":
            if InventoryUI is None:
                print("InventoryUI module not available")
                return
            if inventory_frame is None:
                rebuild_inventory()
            else:
                inventory_frame.lift()
            return
        if label == "JOIN CLUB":
            open_selection(os.path.join(os.path.dirname(__file__), "assets", "images", "clubs"), "Join Club")
            return
        if label == "BUY GEAR":
            nonlocal overlays_visible
            overlays_visible = True
            if gif_item is not None:
                canvas.itemconfigure(gif_item, state="normal")
            if josuncio_item is not None:
                canvas.itemconfigure(josuncio_item, state="normal")
            start_gif_animation()
            open_selection(os.path.join(os.path.dirname(__file__), "assets", "images", "shop"), "Shop")
            return
        print(f"Clicked {label}")

    for label, color in button_specs:
        btn = SpriteButton(
            canvas,
            button_x.get(),
            0,
            label,
            color=color,
            command=lambda l=label: on_button_click(l),
            scale=button_scale.get(),
        )
        btn.label = label
        buttons.append(btn)

    def update_button_layout(*args):
        x = button_x.get()
        if menu_compact:
            inventory_button = None
            for btn in buttons:
                if getattr(btn, "label", "") == "INVENTORY":
                    inventory_button = btn
                else:
                    canvas.itemconfigure(btn.image_item, state="hidden")
            if inventory_button is not None:
                inventory_button.update_scale(button_scale.get())
                bottom_y = button_y.get() + (len(buttons) - 1) * (inventory_button.height + int(BUTTON_VERTICAL_SPACING * button_scale.get()))
                canvas.coords(inventory_button.image_item, x, bottom_y)
                canvas.itemconfigure(inventory_button.image_item, state="normal")
            return
        y = button_y.get()
        for btn in buttons:
            btn.update_scale(button_scale.get())
            canvas.coords(btn.image_item, x, y)
            canvas.itemconfigure(btn.image_item, state="normal")
            y += btn.height + int(BUTTON_VERTICAL_SPACING * button_scale.get())

    def update_background(*args):
        selected = background_selected.get()
        if selected.lower().endswith(".png"):
            load_background_file(selected)

    def toggle_overlays():
        nonlocal overlays_visible
        overlays_visible = not overlays_visible
        if gif_item is not None:
            canvas.itemconfigure(gif_item, state="normal" if overlays_visible else "hidden")
        if josuncio_item is not None:
            canvas.itemconfigure(josuncio_item, state="normal" if overlays_visible else "hidden")

    def toggle_menu_mode():
        nonlocal menu_compact
        menu_compact = not menu_compact
        update_button_layout()

    def update_all(*args):
        update_button_layout()
        update_background()
        update_inventory_layout()
        update_selection_layout()
        update_action_layout()
        update_claucho_layout()
        update_gif_layout()
        update_josuncio_layout()
        update_money_layout()

    update_button_layout()
    create_gif_overlay()
    update_josuncio_layout()
    update_money_layout()

    controls = tk.Toplevel(root)
    controls.title("Layout Controls")
    controls.geometry(f"+{MENU_OFFSET_X + MENU_WIDTH + 12}+{MENU_OFFSET_Y}")

    # Two-column layout: left_col and right_col side by side
    left_col = tk.Frame(controls)
    left_col.grid(row=0, column=0, sticky="nsew", padx=(4, 2))
    right_col = tk.Frame(controls)
    right_col.grid(row=0, column=1, sticky="nsew", padx=(2, 4))
    controls.columnconfigure(0, weight=1)
    controls.columnconfigure(1, weight=1)
    left_col.columnconfigure(1, weight=1)
    right_col.columnconfigure(1, weight=1)

    def make_slider(parent, label_text, variable, from_, to_, resolution=1, row=0, callback=True):
        tk.Label(parent, text=label_text, anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        if callback:
            cmd = lambda _: update_all()
        else:
            cmd = None
        scale = tk.Scale(parent, variable=variable, from_=from_, to=to_, orient="horizontal", resolution=resolution, command=cmd)
        scale.grid(row=row, column=1, sticky="ew", padx=8)
        return scale

    # ── LEFT COLUMN: Buttons, Inventory, Menu, Background, Claucho ──
    lr = 0
    if debug:
        make_slider(left_col, "Buttons X", button_x, 0, MENU_WIDTH, resolution=1, row=lr)
        lr += 1
        make_slider(left_col, "Buttons Y", button_y, 0, MENU_HEIGHT, resolution=1, row=lr)
        lr += 1
        make_slider(left_col, "Button Scale", button_scale, 0.3, 2.0, resolution=0.05, row=lr)
        lr += 1
        make_slider(left_col, "Inventory X", inv_x, 0, MENU_WIDTH, resolution=1, row=lr)
        lr += 1
        make_slider(left_col, "Inventory Y", inv_y, 0, MENU_HEIGHT, resolution=1, row=lr)
        lr += 1
        make_slider(left_col, "Inventory Scale", inv_scale, 0.3, 1.5, resolution=0.05, row=lr)
        lr += 1
        make_slider(left_col, "Menu X", selection_x, 0, MENU_WIDTH, resolution=1, row=lr)
        lr += 1
        make_slider(left_col, "Menu Y", selection_y, 0, MENU_HEIGHT, resolution=1, row=lr)
        lr += 1
        make_slider(left_col, "Menu Scale", selection_scale, SELECTION_OVERLAY_MIN_SCALE, SELECTION_OVERLAY_MAX_SCALE, resolution=0.05, row=lr)
        lr += 1

    tk.Label(left_col, text="Background Source", anchor="w").grid(row=lr, column=0, sticky="w", padx=8, pady=4)
    background_dropdown = tk.OptionMenu(left_col, background_selected, *background_files, command=lambda _: load_background_file(background_selected.get()))
    sound_player.disable_sound(background_dropdown)
    background_dropdown.grid(row=lr, column=1, sticky="ew", padx=8)
    lr += 1
    play_background_button = tk.Button(left_col, text="Play Background", command=play_background, sound_disabled=True)
    play_background_button.grid(row=lr, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 12))
    lr += 1
    if claucho_files:
        tk.Label(left_col, text="Claucho Video", anchor="w").grid(row=lr, column=0, sticky="w", padx=8, pady=4)
        claucho_dropdown = tk.OptionMenu(left_col, claucho_selected, *claucho_files, command=lambda _: load_claucho_video(claucho_selected.get()))
        sound_player.disable_sound(claucho_dropdown)
        claucho_dropdown.grid(row=lr, column=1, sticky="ew", padx=8)
        lr += 1
        if debug:
            make_slider(left_col, "Claucho X", claucho_x, -MENU_WIDTH, MENU_WIDTH, resolution=1, row=lr)
            lr += 1
            make_slider(left_col, "Claucho Y", claucho_y, 0, MENU_HEIGHT, resolution=1, row=lr)
            lr += 1
            make_slider(left_col, "Claucho Scale", claucho_scale, CLAUCHO_MIN_SCALE, CLAUCHO_MAX_SCALE, resolution=0.05, row=lr)
            lr += 1

    # ── RIGHT COLUMN: GIF, Josuncio, Action, Money, Toggles ──
    rr = 0
    tk.Label(right_col, text="Select GIF", anchor="w").grid(row=rr, column=0, sticky="w", padx=8, pady=4)
    gif_dropdown = tk.OptionMenu(right_col, gif_selected, *gif_files, command=lambda _: load_gif_file(gif_selected.get()))
    sound_player.disable_sound(gif_dropdown)
    gif_dropdown.grid(row=rr, column=1, sticky="ew", padx=8)
    rr += 1
    if debug:
        make_slider(right_col, "GIF X", gif_x, -MENU_WIDTH, MENU_WIDTH, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "GIF Y", gif_y, -MENU_HEIGHT, MENU_HEIGHT, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "GIF Scale", gif_scale, GIF_MIN_SCALE, GIF_MAX_SCALE, resolution=0.05, row=rr)
        rr += 1
    play_gif_button = tk.Button(right_col, text="Play GIF", command=start_gif_animation, sound_disabled=True)
    play_gif_button.grid(row=rr, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 12))
    rr += 1
    tk.Label(right_col, text="Josuncio Image", anchor="w").grid(row=rr, column=0, sticky="w", padx=8, pady=4)
    josuncio_dropdown = tk.OptionMenu(right_col, josuncio_selected, *josuncio_files, command=lambda _: load_josuncio_file(josuncio_selected.get()))
    sound_player.disable_sound(josuncio_dropdown)
    josuncio_dropdown.grid(row=rr, column=1, sticky="ew", padx=8)
    rr += 1
    if debug:
        make_slider(right_col, "Josuncio X", josuncio_x, -MENU_WIDTH, MENU_WIDTH, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "Josuncio Y", josuncio_y, -MENU_HEIGHT, MENU_HEIGHT, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "Josuncio Scale", josuncio_scale, JOSUNCIO_MIN_SCALE, JOSUNCIO_MAX_SCALE, resolution=0.05, row=rr)
        rr += 1

    tk.Label(right_col, text="Action Menu", anchor="w").grid(row=rr, column=0, sticky="w", padx=8, pady=4)
    action_menu_choices = ["None", "walkMenu.png", "tricksMenu.png"]
    action_dropdown = tk.OptionMenu(right_col, action_selected, *action_menu_choices, command=lambda _: on_action_selected())
    sound_player.disable_sound(action_dropdown)
    action_dropdown.grid(row=rr, column=1, sticky="ew", padx=8)
    rr += 1
    if debug:
        make_slider(right_col, "Action X", action_x, 0, MENU_WIDTH, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "Action Y", action_y, 0, MENU_HEIGHT, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "Action Scale", action_scale, ACTION_MENU_MIN_SCALE, ACTION_MENU_MAX_SCALE, resolution=0.05, row=rr)
        rr += 1

    tk.Label(right_col, text="Money Amount", anchor="w").grid(row=rr, column=0, sticky="w", padx=8, pady=4)
    money_entry = tk.Entry(right_col, textvariable=money_amount)
    money_entry.grid(row=rr, column=1, sticky="ew", padx=8)
    rr += 1
    if debug:
        make_slider(right_col, "Money X", money_x, 0, MENU_WIDTH, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "Money Y", money_y, 0, MENU_HEIGHT, resolution=1, row=rr)
        rr += 1
        make_slider(right_col, "Money Scale", money_scale, MONEY_MIN_SCALE, MONEY_MAX_SCALE, resolution=0.05, row=rr)
        rr += 1

    toggle_frame = tk.Frame(controls)
    toggle_frame.grid(row=1, column=0, columnspan=2, pady=12)
    tk.Button(
        toggle_frame,
        text="Toggle Overlays",
        command=toggle_overlays,
        font=("PixeloidSans", 10),
        padx=10,
        pady=5,
        sound_disabled=True,
    ).grid(row=0, column=0, padx=10)
    tk.Button(
        toggle_frame,
        text="Toggle Menu",
        command=toggle_menu_mode,
        font=("PixeloidSans", 10),
        padx=10,
        pady=5,
        sound_disabled=True,
    ).grid(row=0, column=1, padx=10)

    def disable_all():
        for b in buttons:
            b.set_enabled(False)

    def enable_all():
        for b in buttons:
            b.set_enabled(True)

    # tk.Button(
    #     control_frame,
    #     text="Disable All",
    #     command=disable_all,
    #     font=("PixeloidSans", 10),
    #     padx=10,
    #     pady=5,
    # ).grid(row=0, column=0, padx=10)

    # tk.Button(
    #     control_frame,
    #     text="Enable All",
    #     command=enable_all,
    #     font=("PixeloidSans", 10),
    #     padx=10,
    #     pady=5,
    # ).grid(row=0, column=1, padx=10)

    root.bind_all("<KeyPress>", on_key_press)
    root.bind_all("<KeyRelease>", on_key_release)
    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pixel art UI with optional debug controls")
    parser.add_argument("--debug", action="store_true", help="show slider controls")
    args = parser.parse_args()
    main(debug=args.debug)
