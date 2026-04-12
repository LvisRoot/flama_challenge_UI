import os
import tkinter as tk
from PIL import Image, ImageOps, ImageTk

from sound_player import play_click_sound


class ActionMenuUI:
    """Overlay that composites action arrow buttons onto a parent canvas with transparency."""

    def __init__(self, canvas, asset_dir, menu_name, x=120, y=120, scale=1.0, on_close=None):
        self.canvas = canvas
        self.asset_dir = asset_dir
        self.menu_name = menu_name
        self.on_close = on_close
        self.menu_x = x
        self.menu_y = y
        self.menu_scale = max(0.1, float(scale))

        self.background_image = None
        self.composite_photo = None
        self.slot_boxes = []
        self.item_images = []  # original PIL images for arrows
        self.item_data = []    # canvas item info
        self.canvas_items = [] # all canvas item ids we own
        self.bg_item = None
        self.pressed_directions = set()

        self.load_assets()
        self.redraw()

    def load_assets(self):
        menu_path = os.path.join(self.asset_dir, self.menu_name)
        slots_path = os.path.join(self.asset_dir, "action_slots.png")

        if os.path.exists(menu_path):
            self.background_image = Image.open(menu_path).convert("RGBA")
        else:
            self.background_image = Image.new("RGBA", (400, 300), (40, 40, 60, 255))

        self.menu_base_width, self.menu_base_height = self.background_image.size
        self.slot_boxes = self._parse_slot_boxes(slots_path)

        # Collect *_arrow.png files as action buttons
        self.item_paths = []
        self.item_images = []
        if os.path.isdir(self.asset_dir):
            for filename in sorted(os.listdir(self.asset_dir)):
                if filename.lower().endswith("_arrow.png"):
                    self.item_paths.append(filename)
                    path = os.path.join(self.asset_dir, filename)
                    self.item_images.append(Image.open(path).convert("RGBA"))

    def _parse_slot_boxes(self, path):
        if not os.path.exists(path):
            return []
        image = Image.open(path).convert("RGBA")
        width, height = image.size
        pixels = image.load()
        visited = [[False] * height for _ in range(width)]
        boxes = []

        def is_slot(x, y):
            return pixels[x, y][3] > 32

        for y in range(height):
            for x in range(width):
                if visited[x][y] or not is_slot(x, y):
                    continue
                stack = [(x, y)]
                x0 = x1 = x
                y0 = y1 = y
                while stack:
                    px, py = stack.pop()
                    if visited[px][py]:
                        continue
                    visited[px][py] = True
                    if not is_slot(px, py):
                        continue
                    x0 = min(x0, px)
                    x1 = max(x1, px)
                    y0 = min(y0, py)
                    y1 = max(y1, py)
                    for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                        if 0 <= nx < width and 0 <= ny < height and not visited[nx][ny]:
                            stack.append((nx, ny))
                boxes.append((x0, y0, x1 + 1, y1 + 1))

        boxes.sort(key=lambda b: (b[1], b[0]))
        return boxes

    def _get_scaled_slots(self, scale):
        if not self.slot_boxes:
            return []
        return [tuple(int(coord * scale) for coord in box) for box in self.slot_boxes]

    def _direction_index(self, direction):
        direction = direction.lower()
        for index, filename in enumerate(self.item_paths):
            if f"_{direction}_arrow" in filename.lower():
                return index
        return None

    def press_direction(self, direction):
        direction = direction.lower()
        if direction in self.pressed_directions:
            return
        index = self._direction_index(direction)
        if index is not None:
            self.pressed_directions.add(direction)
            self._on_press(index, play_sound=False)

    def release_direction(self, direction):
        direction = direction.lower()
        if direction not in self.pressed_directions:
            return
        index = self._direction_index(direction)
        if index is not None:
            self.pressed_directions.discard(direction)
            self._on_release(index)

    def _composite_image(self, pressed_index=-1):
        """Build a single RGBA composite of background + arrow buttons."""
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        width = max(1, int(self.menu_base_width * self.menu_scale))
        height = max(1, int(self.menu_base_height * self.menu_scale))
        composite = self.background_image.resize((width, height), resample)
        composite = composite.copy()

        slots = self._get_scaled_slots(self.menu_scale)
        for index, item_pil in enumerate(self.item_images[:len(slots)]):
            slot = slots[index]
            slot_width = max(1, slot[2] - slot[0])
            slot_height = max(1, slot[3] - slot[1])

            target_size = (max(1, int(slot_width * 0.92)), max(1, int(slot_height * 0.92)))
            item_fit = ImageOps.contain(item_pil, target_size, resample)

            if index == pressed_index:
                # Shrink to 80% when pressed
                pressed_size = (max(1, int(item_fit.width * 0.80)), max(1, int(item_fit.height * 0.80)))
                item_fit = item_fit.resize(pressed_size, resample)

            cx = (slot[0] + slot[2]) // 2
            cy = (slot[1] + slot[3]) // 2
            paste_x = cx - item_fit.width // 2
            paste_y = cy - item_fit.height // 2
            composite.alpha_composite(item_fit, (paste_x, paste_y))

        return composite

    def redraw(self, pressed_index=-1):
        composite = self._composite_image(pressed_index)
        self.composite_photo = ImageTk.PhotoImage(composite)

        if self.bg_item is not None:
            # Update existing image in place
            self.canvas.itemconfigure(self.bg_item, image=self.composite_photo)
        else:
            # First draw: create image and hit regions
            self.bg_item = self.canvas.create_image(
                self.menu_x, self.menu_y, anchor="nw", image=self.composite_photo
            )
            self.canvas_items.append(self.bg_item)
            self._create_hit_regions()

    def _create_hit_regions(self):
        slots = self._get_scaled_slots(self.menu_scale)
        self.item_data = []
        for index in range(min(len(self.item_images), len(slots))):
            slot = slots[index]
            x0 = self.menu_x + slot[0]
            y0 = self.menu_y + slot[1]
            x1 = self.menu_x + slot[2]
            y1 = self.menu_y + slot[3]
            hit_id = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline="", fill="", stipple=""
            )
            self.canvas_items.append(hit_id)
            self.canvas.tag_bind(hit_id, "<ButtonPress-1>", lambda e, idx=index: self._on_press(idx))
            self.canvas.tag_bind(hit_id, "<ButtonRelease-1>", lambda e, idx=index: self._on_release(idx))
            self.item_data.append({"hit_id": hit_id, "index": index})

    def _on_press(self, index, play_sound=True):
        if play_sound:
            play_click_sound()
        self.redraw(pressed_index=index)

    def _on_release(self, index):
        self.redraw(pressed_index=-1)

    def clear_canvas_items(self):
        for item_id in self.canvas_items:
            self.canvas.delete(item_id)
        self.canvas_items = []
        self.bg_item = None
        self.item_data = []

    def close(self):
        self.clear_canvas_items()
        if callable(self.on_close):
            self.on_close()

    def lift(self):
        for item_id in self.canvas_items:
            self.canvas.tag_raise(item_id)

    def set_transform(self, x, y, scale):
        self.menu_x = x
        self.menu_y = y
        self.menu_scale = max(0.1, float(scale))
        self.clear_canvas_items()
        self.redraw()

