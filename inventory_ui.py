import argparse
import os
import tkinter as tk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

DEFAULT_WIDTH = 560
DEFAULT_HEIGHT = 660
SLOT_SIZE = 92
ITEM_SIZE = 72
ITEM_DRAG_SCALE = 1.16
SLOT_PADDING_RATIO = 0.92
SLOT_OVERLAY_IMAGE = "inv_slots.png"
CANCEL_IMAGE = "cross_square.png"
CROSS_IMAGE = "cross_square.png"
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets", "inventory")
BACKGROUND_IMAGE = "inv_clean.png"

OVERLAY_SLOT_LABELS = [
    "head",
    "chest",
    "legs",
    "storage_left",
    "storage_center",
    "storage_right",
]

ITEMS = [
    ("item_egg_protector", "Egg Protector", "head", "egg_protector.png"),
    ("item_tshirt_pink", "T-Shirt Pink", "chest", "tshirt_pink.png"),
    ("item_pants_black", "Pants Black", "legs", "pants_black.png"),
    ("item_tshirt_white", "T-Shirt White", "storage_left", "tshirt_white.png"),
    ("item_pants_cats", "Pants Cats", "storage_center", "pants_cats.png"),
]


class InventoryUI:
    def __init__(self, root: tk.Widget, debug: bool = False, embedded: bool = False, scale: float = 1.0, on_close=None):
        self.root = root
        self.debug = debug
        self.embedded = embedded
        self.scale = max(0.1, float(scale))
        self.on_close = on_close

        self.photo_refs = []
        self.slots = {}
        self.items = {}
        self.drag_state = {"item_id": None, "x": 0, "y": 0, "orig_slot": None}
        self.cancel_id = None
        self.cancel_photo = None
        self.cancel_slot = None
        self.cancel_scale = 1.0
        self.cross_id = None
        self.cross_photo = None
        self.cross_base_width = int(DEFAULT_WIDTH / 8)
        self.cross_scale = 1.0
        self.cross_text_size = int(18 * self.scale)

        self.background_image = self._load_asset(BACKGROUND_IMAGE)
        self.base_width, self.base_height = self._background_size()
        self.width, self.height = self._scaled_size()
        self.background_image = self._load_asset(BACKGROUND_IMAGE, size=(self.width, self.height))
        self.cross_base_width = int(self.width / 8)

        if not self.embedded and isinstance(self.root, (tk.Tk, tk.Toplevel)):
            self.root.title("Inventory")
            self.root.geometry(f"{self.width}x{self.height}")
            self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._draw_background()
        self._create_top_right_cross()
        self._create_slots()
        self._create_items()
        self._bind_events()

    def _load_asset(self, name: str, size=None):
        if not PIL_AVAILABLE:
            return None
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            return None
        try:
            image = Image.open(path).convert("RGBA")
        except Exception:
            return None
        if size is not None:
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
            image = image.resize(size, resample)
        return image

    def _background_size(self):
        if self.background_image is not None:
            return self.background_image.size
        return DEFAULT_WIDTH, DEFAULT_HEIGHT

    def _scaled_size(self):
        return (max(1, int(self.base_width * self.scale)), max(1, int(self.base_height * self.scale)))

    def _scale_box(self, box):
        return (box[0] * self.scale, box[1] * self.scale, box[2] * self.scale, box[3] * self.scale)

    def _background_photo(self):
        if self.background_image is None:
            return None
        photo = ImageTk.PhotoImage(self.background_image)
        self.photo_refs.append(photo)
        return photo

    def _load_photo(self, name: str, size):
        image = self._load_asset(name, size)
        if image is None:
            return None
        photo = ImageTk.PhotoImage(image)
        self.photo_refs.append(photo)
        return photo

    def _load_cancel_image(self, slot_width: int, scale: float = 1.0):
        cancel_asset = self._load_asset(CANCEL_IMAGE)
        if cancel_asset is None:
            return None, None
        aspect = cancel_asset.width / cancel_asset.height
        target_width = int(slot_width / 4 * scale)
        target_height = int(target_width / aspect)
        photo = self._load_photo(CANCEL_IMAGE, (target_width, target_height))
        return photo, (target_width, target_height)

    def _load_slot_overlay(self):
        return self._load_asset(SLOT_OVERLAY_IMAGE)

    def _detect_slots_from_overlay(self, overlay):
        if overlay is None:
            return []
        if overlay.mode != "RGBA":
            overlay = overlay.convert("RGBA")
        width, height = overlay.size
        pixels = overlay.load()
        mask = [[False] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a > 32 and (r + g + b) / 3 < 200:
                    mask[y][x] = True

        visited = [[False] * width for _ in range(height)]
        boxes = []
        for y in range(height):
            for x in range(width):
                if not mask[y][x] or visited[y][x]:
                    continue
                stack = [(x, y)]
                visited[y][x] = True
                minx = maxx = x
                miny = maxy = y
                while stack:
                    px, py = stack.pop()
                    for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                        if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx] and mask[ny][nx]:
                            visited[ny][nx] = True
                            stack.append((nx, ny))
                            minx = min(minx, nx)
                            maxx = max(maxx, nx)
                            miny = min(miny, ny)
                            maxy = max(maxy, ny)
                if (maxx - minx + 1) * (maxy - miny + 1) >= 100:
                    boxes.append((minx, miny, maxx, maxy))
        return boxes

    def _sort_boxes_by_rows(self, boxes):
        centers = [((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, box) for box in boxes]
        centers.sort(key=lambda c: (c[1], c[0]))
        rows = []
        for cx, cy, box in centers:
            if not rows:
                rows.append([(cx, cy, box)])
                continue
            last_row = rows[-1]
            row_y = sum(item[1] for item in last_row) / len(last_row)
            if abs(cy - row_y) < 80:
                last_row.append((cx, cy, box))
            else:
                rows.append([(cx, cy, box)])
        sorted_boxes = []
        for row in rows:
            row_sorted = sorted(row, key=lambda item: item[0])
            sorted_boxes.extend([item[2] for item in row_sorted])
        return sorted_boxes

    def _map_overlay_slots(self, boxes):
        if len(boxes) < len(OVERLAY_SLOT_LABELS):
            return None

        boxes_sorted = self._sort_boxes_by_rows(boxes)
        if len(boxes_sorted) == len(OVERLAY_SLOT_LABELS):
            return {label: box for label, box in zip(OVERLAY_SLOT_LABELS, boxes_sorted)}

        slot_centers = [(box, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)) for box in boxes]
        assignments = {}
        remaining = slot_centers.copy()
        for label in OVERLAY_SLOT_LABELS:
            anchor = self._preferred_slot_anchor(label)
            best = None
            best_dist = None
            for box, center in remaining:
                dx = center[0] - anchor[0]
                dy = center[1] - anchor[1]
                dist = dx * dx + dy * dy
                if best is None or dist < best_dist:
                    best = (box, center)
                    best_dist = dist
            if best is None:
                return None
            assignments[label] = best[0]
            remaining.remove(best)
        return assignments

    def _preferred_slot_anchor(self, label: str):
        if label == "head":
            return (self.width * 0.50, self.height * 0.42)
        if label == "chest":
            return (self.width * 0.50, self.height * 0.52)
        if label == "legs":
            return (self.width * 0.50, self.height * 0.63)
        if label == "storage_left":
            return (self.width * 0.26, self.height * 0.92)
        if label == "storage_center":
            return (self.width * 0.50, self.height * 0.92)
        if label == "storage_right":
            return (self.width * 0.74, self.height * 0.92)
        return (self.width / 2, self.height / 2)

    def _draw_background(self):
        bg_photo = self._background_photo()
        if bg_photo is not None:
            self.canvas.create_image(0, 0, anchor="nw", image=bg_photo)
        else:
            self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#121025", outline="")

    def _load_cross_image(self, width: int):
        cross_asset = self._load_asset(CROSS_IMAGE)
        if cross_asset is None:
            return None, None
        aspect = cross_asset.width / cross_asset.height
        target_width = int(width)
        target_height = int(target_width / aspect)
        photo = self._load_photo(CROSS_IMAGE, (target_width, target_height))
        return photo, (target_width, target_height)

    def _create_top_right_cross(self):
        self.cross_base_width = int(self.width / 8)
        cross_width = int(self.cross_base_width * self.cross_scale)
        photo, size = self._load_cross_image(cross_width)
        if photo is None or size is None:
            padding = 12
            x = self.width - padding
            y = padding
            self.cross_id = self.canvas.create_text(
                x,
                y,
                text="✕",
                fill="#ffffff",
                font=("Arial", self.cross_text_size, "bold"),
                anchor="ne",
                tags=("top_right_cross",),
            )
            return
        x = self.width - size[0] / 2 - 8
        y = size[1] / 2 + 8
        self.cross_id = self.canvas.create_image(x, y, image=photo, anchor="center", tags=("top_right_cross",))
        self.cross_photo = photo

    def _slot_coordinates(self, x_ratio: float, y_ratio: float):
        cx = x_ratio * self.width
        cy = y_ratio * self.height
        half = (SLOT_SIZE * self.scale) / 2
        return cx, cy, cx - half, cy - half, cx + half, cy + half

    def _create_slots(self):
        overlay = self._load_slot_overlay()
        slot_assignments = None
        if overlay is not None:
            boxes = self._detect_slots_from_overlay(overlay)
            slot_assignments = self._map_overlay_slots(boxes)
        if slot_assignments is not None:
            for slot_id, box in slot_assignments.items():
                x1, y1, x2, y2 = self._scale_box(box)
                self.slots[slot_id] = {
                    "bbox": (x1, y1, x2, y2),
                    "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                }
                if self.debug:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="white", width=2)
            return

        for slot_id, x_ratio, y_ratio in CHARACTER_SLOTS + STORAGE_SLOTS:
            cx, cy, x1, y1, x2, y2 = self._slot_coordinates(x_ratio, y_ratio)
            self.slots[slot_id] = {
                "bbox": (x1, y1, x2, y2),
                "center": (cx, cy),
            }
            if self.debug:
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="white", width=2)

    def _create_items(self):
        for item_id, label, slot_id, asset in ITEMS:
            self._create_item(item_id, label, slot_id, asset)

    def _create_item(self, item_id: str, label: str, slot_id: str, asset: str | None):
        state = self.item_state.get(item_id, {})
        if state.get("slot") in self.slots:
            slot_id = state["slot"]
        x1, y1, x2, y2 = self.slots[slot_id]["bbox"]
        slot_width = int(x2 - x1)
        slot_height = int(y2 - y1)
        size = state.get("current_size", (int(slot_width * SLOT_PADDING_RATIO), int(slot_height * SLOT_PADDING_RATIO)))
        cx, cy = self.slots[slot_id]["center"]
        item = {
            "slot": slot_id,
            "slot_size": (int(slot_width * SLOT_PADDING_RATIO), int(slot_height * SLOT_PADDING_RATIO)),
            "current_size": size,
        }

        if asset and PIL_AVAILABLE:
            photo = self._load_photo(asset, size)
            original = self._load_asset(asset)
            if photo is not None and original is not None:
                image_id = self.canvas.create_image(cx, cy, image=photo, tags=("item", item_id))
                item.update({"type": "image", "image": image_id, "pil": original, "photo": photo})
                self.items[item_id] = item
                return

        halfx = size[0] / 2
        halfy = size[1] / 2
        rect = self.canvas.create_rectangle(
            cx - halfx,
            cy - halfy,
            cx + halfx,
            cy + halfy,
            fill="#6b6eff",
            outline="",
            tags=("item", item_id),
        )
        text = self.canvas.create_text(cx, cy, text=label, fill="#1b1321", font=("Arial", 10, "bold"), tags=("item", item_id))
        item.update({"type": "shape", "rect": rect, "text": text})
        self.items[item_id] = item

    def _bind_events(self):
        self.canvas.tag_bind("item", "<ButtonPress-1>", self._on_press)
        self.canvas.tag_bind("item", "<B1-Motion>", self._on_motion)
        self.canvas.tag_bind("item", "<ButtonRelease-1>", self._on_release)
        self.canvas.tag_bind("cancel", "<ButtonPress-1>", self._on_cancel_click)
        self.canvas.tag_bind("top_right_cross", "<ButtonPress-1>", self._on_cross_press)
        self.canvas.tag_bind("top_right_cross", "<ButtonRelease-1>", self._on_cross_release)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", lambda event: self._hide_cancel())

    def _find_item_id(self, event):
        current = self.canvas.find_withtag("current")
        if not current:
            return None
        tags = self.canvas.gettags(current[0])
        for tag in tags:
            if tag.startswith("item_"):
                return tag
        return None

    def _show_cancel_for_slot(self, slot_id: str, scale: float = 1.0):
        item_id = self._item_in_slot(slot_id)
        if item_id is None:
            self._hide_cancel()
            return
        x1, y1, x2, y2 = self.slots[slot_id]["bbox"]
        slot_width = int(x2 - x1)
        photo, size = self._load_cancel_image(slot_width, scale=scale)
        if photo is None or size is None:
            self._hide_cancel()
            return
        cx = x2 - size[0] / 2 - 4
        cy = y2 - size[1] / 2 - 4
        if self.cancel_id is None:
            self.cancel_id = self.canvas.create_image(cx, cy, image=photo, tags=("cancel",))
        else:
            self.canvas.itemconfigure(self.cancel_id, image=photo)
            self.canvas.coords(self.cancel_id, cx, cy)
        self.cancel_photo = photo
        self.cancel_slot = slot_id
        self.cancel_scale = scale
        self.canvas.tag_raise(self.cancel_id)

    def _hide_cancel(self):
        if self.cancel_id is not None:
            self.canvas.delete(self.cancel_id)
            self.cancel_id = None
            self.cancel_photo = None
            self.cancel_slot = None

    def _click_on_cancel(self, event):
        slot_id = self._find_slot_for_point(event.x, event.y)
        if slot_id is None:
            return False
        item_id = self._item_in_slot(slot_id)
        if item_id is None:
            return False
        x1, y1, x2, y2 = self.slots[slot_id]["bbox"]
        width = x2 - x1
        height = y2 - y1
        return event.x >= x2 - width * 0.25 and event.y >= y2 - height * 0.25

    def _on_mouse_move(self, event):
        if self.drag_state["item_id"] is not None:
            self._hide_cancel()
            return
        slot_id = self._find_slot_for_point(event.x, event.y)
        if slot_id is None:
            self._hide_cancel()
            return
        over_cancel = self.cancel_id is not None and self._click_on_cancel(event)
        scale = 1.5 if over_cancel else 1.0
        if self.cancel_slot == slot_id and self.cancel_id is not None and self.cancel_scale == scale:
            return
        self._show_cancel_for_slot(slot_id, scale=scale)

    def _on_cancel_click(self, event):
        slot_id = self._find_slot_for_point(event.x, event.y)
        if slot_id is None:
            return "break"
        item_id = self._item_in_slot(slot_id)
        if item_id is None:
            return "break"
        self._remove_item(item_id)
        self._hide_cancel()
        return "break"

    def _on_cross_press(self, event):
        self._set_cross_scale(0.8)        if self.embedded and callable(self.on_close):
            self.on_close()        return "break"

    def _on_cross_release(self, event):
        self._set_cross_scale(1.0)
        if self.embedded and callable(self.on_close):
            self.on_close()
        return "break"

    def _set_cross_scale(self, scale: float):
        if self.cross_id is None:
            return
        if self.cross_scale == scale:
            return
        self.cross_scale = scale
        cross_width = int(self.cross_base_width * scale)
        photo, size = self._load_cross_image(cross_width)
        if photo is not None and size is not None:
            self.cross_photo = photo
            self.canvas.itemconfigure(self.cross_id, image=photo)
            x = self.width - size[0] / 2 - 8
            y = size[1] / 2 + 8
            self.canvas.coords(self.cross_id, x, y)
            return
        text_size = int(self.cross_text_size * scale)
        if text_size < 8:
            text_size = 8
        self.canvas.itemconfigure(self.cross_id, font=("Arial", text_size, "bold"))

    def _remove_item(self, item_id: str):
        item = self.items.get(item_id)
        if item is None:
            return
        if item["type"] == "image":
            self.canvas.delete(item["image"])
        else:
            self.canvas.delete(item["rect"])
            self.canvas.delete(item["text"])
        del self.items[item_id]
        if self.drag_state["item_id"] == item_id:
            self.drag_state["item_id"] = None
            self.drag_state["orig_slot"] = None

    def _on_press(self, event):
        if self._click_on_cancel(event):
            slot_id = self._find_slot_for_point(event.x, event.y)
            if slot_id is not None:
                item_id = self._item_in_slot(slot_id)
                if item_id is not None:
                    self._remove_item(item_id)
                    self._hide_cancel()
            return
        item_id = self._find_item_id(event)
        if item_id is None:
            return
        self.drag_state["item_id"] = item_id
        item = self.items[item_id]
        self.drag_state["orig_slot"] = item["slot"]
        self.drag_state["x"] = event.x
        self.drag_state["y"] = event.y
        self._resize_item(item_id, ITEM_DRAG_SCALE)
        self.canvas.tag_raise(item_id)

    def _on_motion(self, event):
        item_id = self.drag_state.get("item_id")
        if item_id is None:
            return
        dx = event.x - self.drag_state["x"]
        dy = event.y - self.drag_state["y"]
        self.canvas.move(item_id, dx, dy)
        self.drag_state["x"] = event.x
        self.drag_state["y"] = event.y

    def _on_release(self, event):
        item_id = self.drag_state.get("item_id")
        if item_id is None:
            return
        target = self._find_slot_for_point(event.x, event.y)
        original_slot = self.drag_state["orig_slot"]

        if target is None:
            self._snap_item_to_slot(item_id, original_slot)
        else:
            occupying_item = self._item_in_slot(target, exclude=item_id)
            if occupying_item is not None and target != original_slot:
                self._snap_item_to_slot(occupying_item, original_slot)
                self._snap_item_to_slot(item_id, target)
            else:
                self._snap_item_to_slot(item_id, target)

        self._resize_item(item_id, 1.0)
        self.drag_state["item_id"] = None
        self.drag_state["orig_slot"] = None
        self.drag_state["x"] = 0
        self.drag_state["y"] = 0

    def _resize_item(self, item_id: str, scale: float = None, size: tuple[int, int] | None = None):
        item = self.items[item_id]
        if size is None:
            if scale is None:
                size = item["current_size"]
            else:
                size = (int(item["current_size"][0] * scale), int(item["current_size"][1] * scale))
        item["current_size"] = size
        cx, cy = self._item_center(item_id)

        if item["type"] == "image":
            pil = item["pil"].resize(
                size,
                Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS,
            )
            photo = ImageTk.PhotoImage(pil)
            self.photo_refs.append(photo)
            item["photo"] = photo
            self.canvas.itemconfigure(item["image"], image=photo)
            self.canvas.coords(item["image"], cx, cy)
        else:
            halfx = size[0] / 2
            halfy = size[1] / 2
            self.canvas.coords(item["rect"], cx - halfx, cy - halfy, cx + halfx, cy + halfy)
            self.canvas.coords(item["text"], cx, cy)

    def _item_center(self, item_id: str):
        item = self.items[item_id]
        if item["type"] == "image":
            coords = self.canvas.coords(item["image"])
            return coords[0], coords[1]
        coords = self.canvas.coords(item["rect"])
        return ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)

    def _find_slot_for_point(self, x: float, y: float):
        for slot_id, slot in self.slots.items():
            x1, y1, x2, y2 = slot["bbox"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return slot_id
        return None

    def _item_in_slot(self, slot_id: str, exclude: str | None = None):
        for item_id, item in self.items.items():
            if item_id == exclude:
                continue
            if item["slot"] == slot_id:
                return item_id
        return None

    def _slot_available(self, slot_id: str, dragged_item_id: str):
        return self._item_in_slot(slot_id, exclude=dragged_item_id) is None

    def _snap_item_to_slot(self, item_id: str, slot_id: str):
        self.items[item_id]["slot"] = slot_id
        x1, y1, x2, y2 = self.slots[slot_id]["bbox"]
        size = (int((x2 - x1) * SLOT_PADDING_RATIO), int((y2 - y1) * SLOT_PADDING_RATIO))
        self._resize_item(item_id, size=size)
        cx, cy = self.slots[slot_id]["center"]
        self._move_item_to_center(item_id, cx, cy)

    def _move_item_to_center(self, item_id: str, cx: float, cy: float):
        current_x, current_y = self._item_center(item_id)
        dx = cx - current_x
        dy = cy - current_y
        self.canvas.move(item_id, dx, dy)

    def get_state(self):
        state = {}
        for item_id, item in self.items.items():
            state[item_id] = {
                "slot": item["slot"],
                "current_size": item["current_size"],
            }
        return state


def main():
    parser = argparse.ArgumentParser(description="Inventory drag and drop UI")
    parser.add_argument("--debug", action="store_true", help="Show slot boxes with transparent fill and white outline")
    args = parser.parse_args()

    root = tk.Tk()
    InventoryUI(root, debug=args.debug)
    root.mainloop()


if __name__ == "__main__":
    main()
