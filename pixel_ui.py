import tkinter as tk
from tkinter import DISABLED, NORMAL

import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageSequence

try:
    from inventory_ui import InventoryUI
except ImportError:
    InventoryUI = None

# Layout constants (adjust menu geometry and initial position)
ASPECT_RATIO = (9, 16)
MENU_WIDTH = 500
MENU_HEIGHT = int(MENU_WIDTH * ASPECT_RATIO[1] / ASPECT_RATIO[0])
MENU_OFFSET_X = 300
MENU_OFFSET_Y = 150

# GIF overlay config
GIF_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "assets", "images", "hola-que-tal-como-va-todo-loco-a.gif")
GIF_INITIAL_X = 167
GIF_INITIAL_Y = 5
GIF_INITIAL_SCALE = 0.53
GIF_MIN_SCALE = 0.2
GIF_MAX_SCALE = 3.0

# Josuncio overlay config
JOSUNCIO_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "assets", "images", "josuncio.png")
JOSUNCIO_INITIAL_X = 5
JOSUNCIO_INITIAL_Y = 5
JOSUNCIO_INITIAL_SCALE = 0.53
JOSUNCIO_MIN_SCALE = 0.2
JOSUNCIO_MAX_SCALE = 2.5

# button container anchor offset (from top-left of window)
BUTTON_OFFSET_X = 272
BUTTON_OFFSET_Y = 535
BUTTON_VERTICAL_SPACING = 12
BUTTON_SCALE = 0.45

# inventory overlay config
INVENTORY_OFFSET_X = 88
INVENTORY_OFFSET_Y = 104
INVENTORY_SCALE = 0.7
INVENTORY_BORDER = 2

# background image config (assets/images/elInvernadero.png)
BACKGROUND_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "assets", "images", "elInvernadero.png")
BACKGROUND_IMAGE_WIDTH = 520
BACKGROUND_IMAGE_HEIGHT = 880
BACKGROUND_IMAGE_X = -29
BACKGROUND_IMAGE_Y = -78
BACKGROUND_SCALE = 1.15


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


def main():
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
    bg_item = None
    if os.path.exists(BACKGROUND_IMAGE_PATH):
        try:
            bg_original_pil = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
            if hasattr(Image, "Resampling"):
                resample_method = Image.Resampling.LANCZOS
            else:
                resample_method = Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.BICUBIC

            def make_bg_photo(scale: float):
                size = (max(1, int(BACKGROUND_IMAGE_WIDTH * scale)), max(1, int(BACKGROUND_IMAGE_HEIGHT * scale)))
                img = bg_original_pil.resize(size, resample_method)
                return ImageTk.PhotoImage(img)

            bg_photo = make_bg_photo(BACKGROUND_SCALE)
            bg_item = canvas.create_image(BACKGROUND_IMAGE_X, BACKGROUND_IMAGE_Y, anchor="nw", image=bg_photo)
            root.bg_photo = bg_photo  # keep reference so image persists
        except Exception as e:
            print(f"Warning: could not load background image: {e}")
    else:
        def make_bg_photo(scale: float):
            return None

    gif_frames = []
    gif_durations = []
    gif_photo_frames = []
    gif_item = None
    gif_running = False
    gif_current_frame = 0

    josuncio_original = None
    josuncio_photo = None
    josuncio_item = None

    if os.path.exists(GIF_IMAGE_PATH):
        try:
            gif_source = Image.open(GIF_IMAGE_PATH)
            for frame in ImageSequence.Iterator(gif_source):
                gif_frames.append(frame.convert("RGBA"))
                gif_durations.append(frame.info.get("duration", 100))
        except Exception as e:
            print(f"Warning: could not load GIF image: {e}")

    if os.path.exists(JOSUNCIO_IMAGE_PATH):
        try:
            josuncio_original = Image.open(JOSUNCIO_IMAGE_PATH).convert("RGBA")
        except Exception as e:
            print(f"Warning: could not load Josuncio image: {e}")

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
        nonlocal gif_current_frame, gif_running, gif_item
        if not gif_photo_frames or gif_item is None:
            gif_running = False
            return
        gif_current_frame = index
        canvas.itemconfigure(gif_item, image=gif_photo_frames[index])
        if index + 1 < len(gif_photo_frames):
            gif_running = True
            delay = gif_durations[index] if index < len(gif_durations) else 100
            root.after(delay, lambda idx=index + 1: animate_gif_frame(idx))
        else:
            gif_running = False

    def start_gif_animation():
        nonlocal gif_current_frame, gif_running, gif_item
        if not gif_photo_frames or gif_running:
            return
        gif_current_frame = 0
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

    def create_gif_overlay():
        nonlocal gif_item, gif_photo_frames
        if not gif_frames:
            return
        gif_photo_frames = make_gif_photos(gif_scale.get())
        if not gif_photo_frames:
            return
        gif_item = canvas.create_image(gif_x.get(), gif_y.get(), anchor="nw", image=gif_photo_frames[0])
        root.gif_photo_frames = gif_photo_frames
        start_gif_animation()

    button_x = tk.IntVar(value=BUTTON_OFFSET_X)
    button_y = tk.IntVar(value=BUTTON_OFFSET_Y)
    button_scale = tk.DoubleVar(value=BUTTON_SCALE)
    bg_x = tk.IntVar(value=BACKGROUND_IMAGE_X)
    bg_y = tk.IntVar(value=BACKGROUND_IMAGE_Y)
    bg_scale = tk.DoubleVar(value=BACKGROUND_SCALE)
    inv_x = tk.IntVar(value=INVENTORY_OFFSET_X)
    inv_y = tk.IntVar(value=INVENTORY_OFFSET_Y)
    inv_scale = tk.DoubleVar(value=INVENTORY_SCALE)
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

        inventory_view = InventoryUI(
            inventory_frame,
            embedded=True,
            scale=scale,
            item_state=inventory_state,
            on_close=close_inventory,
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
        buttons.append(btn)

    def update_button_layout(*args):
        x = button_x.get()
        y = button_y.get()
        for btn in buttons:
            btn.update_scale(button_scale.get())
            canvas.coords(btn.image_item, x, y)
            y += btn.height + int(BUTTON_VERTICAL_SPACING * button_scale.get())

    def update_background(*args):
        if bg_item is None or bg_original_pil is None:
            return
        photo = make_bg_photo(bg_scale.get())
        canvas.itemconfigure(bg_item, image=photo)
        canvas.coords(bg_item, bg_x.get(), bg_y.get())
        root.bg_photo = photo

    def update_all(*args):
        update_button_layout()
        update_background()
        update_inventory_layout()
        update_gif_layout()
        update_josuncio_layout()

    update_button_layout()
    create_gif_overlay()
    update_josuncio_layout()

    controls = tk.Toplevel(root)
    controls.title("Layout Controls")
    controls.geometry(f"+{MENU_OFFSET_X + MENU_WIDTH + 12}+{MENU_OFFSET_Y}")

    def make_slider(parent, label_text, variable, from_, to_, resolution=1, row=0, callback=True):
        tk.Label(parent, text=label_text, anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        if callback:
            cmd = lambda _: update_all()
        else:
            cmd = None
        scale = tk.Scale(parent, variable=variable, from_=from_, to=to_, orient="horizontal", resolution=resolution, command=cmd)
        scale.grid(row=row, column=1, sticky="ew", padx=8)
        return scale

    controls.columnconfigure(1, weight=1)
    make_slider(controls, "Buttons X", button_x, 0, MENU_WIDTH, resolution=1, row=0)
    make_slider(controls, "Buttons Y", button_y, 0, MENU_HEIGHT, resolution=1, row=1)
    make_slider(controls, "Button Scale", button_scale, 0.3, 2.0, resolution=0.05, row=2)
    make_slider(controls, "BG X", bg_x, -MENU_WIDTH, MENU_WIDTH, resolution=1, row=3)
    make_slider(controls, "BG Y", bg_y, -MENU_HEIGHT, MENU_HEIGHT, resolution=1, row=4)
    make_slider(controls, "BG Scale", bg_scale, 0.5, 2.0, resolution=0.05, row=5)
    make_slider(controls, "Inventory X", inv_x, 0, MENU_WIDTH, resolution=1, row=6)
    make_slider(controls, "Inventory Y", inv_y, 0, MENU_HEIGHT, resolution=1, row=7)
    make_slider(controls, "Inventory Scale", inv_scale, 0.3, 1.5, resolution=0.05, row=8)
    make_slider(controls, "GIF X", gif_x, -MENU_WIDTH, MENU_WIDTH, resolution=1, row=9)
    make_slider(controls, "GIF Y", gif_y, -MENU_HEIGHT, MENU_HEIGHT, resolution=1, row=10)
    make_slider(controls, "GIF Scale", gif_scale, GIF_MIN_SCALE, GIF_MAX_SCALE, resolution=0.05, row=11)
    make_slider(controls, "Josuncio X", josuncio_x, -MENU_WIDTH, MENU_WIDTH, resolution=1, row=12)
    make_slider(controls, "Josuncio Y", josuncio_y, -MENU_HEIGHT, MENU_HEIGHT, resolution=1, row=13)
    make_slider(controls, "Josuncio Scale", josuncio_scale, JOSUNCIO_MIN_SCALE, JOSUNCIO_MAX_SCALE, resolution=0.05, row=14)

    control_frame = tk.Frame(root, bg="#120f1e")
    control_frame.pack(pady=14)

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

    root.mainloop()


if __name__ == "__main__":
    main()
