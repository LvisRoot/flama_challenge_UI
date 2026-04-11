import os
import tkinter as tk
from PIL import Image, ImageOps, ImageTk

from sound_player import play_click_sound, play_error_sound, play_result_sound


class SelectionMenuUI:
    def __init__(self, master, asset_dir, title, embedded=False, x=120, y=120, scale=1.0, on_close=None, on_error=None):
        self.on_error = on_error
        self.master = master
        self.asset_dir = asset_dir
        self.title = title
        self.embedded = embedded
        self.on_close = on_close
        self.menu_x = x
        self.menu_y = y
        self.menu_scale = max(0.1, float(scale))

        self.background_image = None
        self.background_photo = None
        self.slot_boxes = []
        self.item_data = []
        self.result_photo = None
        self.result_item = None
        self.showing_result = False
        self.close_id = None

        self.load_assets()
        self.create_container()
        self.create_widgets()
        self.redraw_menu()

    def load_assets(self):
        menu_path = os.path.join(self.asset_dir, "menu.png")
        slots_path = os.path.join(self.asset_dir, "menu_slots.png")
        result_path = os.path.join(self.asset_dir, "result.png")

        if os.path.exists(menu_path):
            self.background_image = Image.open(menu_path).convert("RGBA")
        else:
            self.background_image = Image.new("RGBA", (400, 300), (40, 40, 60, 255))

        self.menu_base_width, self.menu_base_height = self.background_image.size
        self.slot_boxes = self.parse_slot_boxes(slots_path)
        self.result_image = None
        if os.path.exists(result_path):
            self.result_image = Image.open(result_path).convert("RGBA")

        paths = []
        for filename in sorted(os.listdir(self.asset_dir)):
            if filename.lower().endswith(".png"):
                if filename.lower() in {"menu.png", "menu_slots.png", "result.png"}:
                    continue
                if filename.startswith(("1_", "2_", "3_", "4_")):
                    paths.append(filename)
        self.item_paths = paths

    def parse_slot_boxes(self, path):
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

    def create_container(self):
        if self.embedded and isinstance(self.master, (tk.Tk, tk.Toplevel)):
            self.window = tk.Frame(self.master, bg="#120f1e", bd=4, relief="ridge")
            self.window.place(x=self.menu_x, y=self.menu_y)
        else:
            self.window = tk.Toplevel(self.master)
            self.window.title(self.title)
            self.window.resizable(False, False)

    def create_widgets(self):
        self.canvas = tk.Canvas(self.window, highlightthickness=0, bg="#000000")
        self.canvas.pack(fill="both", expand=True)

    def redraw_menu(self):
        self.showing_result = False
        self.canvas.delete("all")
        width = int(self.menu_base_width * self.menu_scale)
        height = int(self.menu_base_height * self.menu_scale)
        self.canvas.config(width=width, height=height)
        if self.embedded and isinstance(self.window, tk.Frame):
            self.window.place_configure(x=self.menu_x, y=self.menu_y, width=width, height=height)
        else:
            self.window.geometry(f"{width}x{height}+{self.menu_x}+{self.menu_y}")

        self.background_photo = ImageTk.PhotoImage(
            self.background_image.resize((width, height), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS)
        )
        self.canvas.create_image(0, 0, anchor="nw", image=self.background_photo)
        self.draw_close_button(width)

        slots = self.get_scaled_slots(self.menu_scale)
        self.create_item_images(slots)

    def draw_close_button(self, width):
        if self.close_id is not None:
            self.canvas.delete(self.close_id)
        self.close_id = self.canvas.create_text(
            width - 8,
            8,
            text="✕",
            fill="#ffffff",
            font=("Arial", 18, "bold"),
            anchor="ne",
            tags=("close",),
        )
        self.canvas.tag_bind("close", "<Button-1>", lambda event: (play_click_sound(), self.close()))

    def close(self):
        if self.embedded and isinstance(self.window, tk.Frame):
            self.window.destroy()
        else:
            self.window.destroy()
        if callable(self.on_close):
            self.on_close()

    def lift(self):
        if self.window is not None:
            self.window.lift()

    def set_transform(self, x, y, scale):
        self.menu_x = x
        self.menu_y = y
        self.menu_scale = max(0.1, float(scale))
        self.redraw_menu()

    def get_scaled_slots(self, scale):
        if not self.slot_boxes:
            if self.item_paths:
                stride_x = self.menu_base_width // 2
                stride_y = self.menu_base_height // 2
                return [
                    (0, 0, stride_x, stride_y),
                    (stride_x, 0, self.menu_base_width, stride_y),
                    (0, stride_y, stride_x, self.menu_base_height),
                    (stride_x, stride_y, self.menu_base_width, self.menu_base_height),
                ]
            return []
        return [tuple(int(coord * scale) for coord in box) for box in self.slot_boxes]

    def create_item_images(self, slots):
        self.item_data = []
        for index, item_name in enumerate(self.item_paths[: len(slots)]):
            path = os.path.join(self.asset_dir, item_name)
            item_image = Image.open(path).convert("RGBA")
            slot = slots[index]
            slot_width = max(1, slot[2] - slot[0])
            slot_height = max(1, slot[3] - slot[1])
            target_size = (
                max(1, int(slot_width * 0.92)),
                max(1, int(slot_height * 0.92)),
            )
            item_copy = ImageOps.contain(
                item_image,
                target_size,
                Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS,
            )
            base_photo = ImageTk.PhotoImage(item_copy)
            hover_size = (
                min(max(1, int(item_copy.width * 1.25)), int(slot_width * 1.25)),
                min(max(1, int(item_copy.height * 1.25)), int(slot_height * 1.25)),
            )
            hover_image = item_copy.resize(
                hover_size,
                Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS,
            )
            hover_photo = ImageTk.PhotoImage(hover_image)
            pressed_image = ImageOps.contain(
                item_image,
                (slot_width, slot_height),
                Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS,
            )
            pressed_photo = ImageTk.PhotoImage(pressed_image)
            cx = (slot[0] + slot[2]) // 2
            cy = (slot[1] + slot[3]) // 2
            item_id = self.canvas.create_image(cx, cy, image=base_photo, anchor="center")
            self.canvas.tag_bind(item_id, "<Enter>", lambda e, iid=item_id: self.on_item_enter(iid))
            self.canvas.tag_bind(item_id, "<Leave>", lambda e, iid=item_id: self.on_item_leave(iid))
            self.canvas.tag_bind(item_id, "<ButtonPress-1>", lambda e, iid=item_id: self.on_item_press(iid))
            self.canvas.tag_bind(item_id, "<ButtonRelease-1>", lambda e, iid=item_id, ipath=path: self.on_item_release(iid, ipath))
            self.item_data.append(
                {
                    "id": item_id,
                    "base_photo": base_photo,
                    "hover_photo": hover_photo,
                    "pressed_photo": pressed_photo,
                    "slot_center": (cx, cy),
                    "slot_box": slot,
                    "item_path": path,
                }
            )

    def on_item_enter(self, item_id):
        if self.showing_result:
            return
        for item in self.item_data:
            if item["id"] == item_id:
                self.canvas.itemconfigure(item_id, image=item["hover_photo"])
                break

    def on_item_leave(self, item_id):
        if self.showing_result:
            return
        for item in self.item_data:
            if item["id"] == item_id:
                self.canvas.itemconfigure(item_id, image=item["base_photo"])
                break

    def on_item_press(self, item_id):
        if self.showing_result:
            return
        for item in self.item_data:
            if item["id"] == item_id:
                self.canvas.itemconfigure(item_id, image=item["pressed_photo"])
                break

    def on_item_release(self, item_id, path):
        if self.showing_result:
            return
        for item in self.item_data:
            if item["id"] == item_id:
                self.canvas.itemconfigure(item_id, image=item["base_photo"])
                break
        self.on_item_click(path)

    def on_item_click(self, path):
        if self.title == "Shop" and os.path.basename(path).lower() != "3_egg.png":
            play_error_sound()
            self._flash_error(path)
            if callable(self.on_error):
                self.on_error()
            return
        play_click_sound()
        if self.result_image is None:
            return
        play_result_sound()
        self.showing_result = True
        self.canvas.delete("all")
        result_width = int(self.result_image.width * self.menu_scale)
        result_height = int(self.result_image.height * self.menu_scale)
        result_photo = ImageTk.PhotoImage(
            self.result_image.resize(
                (max(1, result_width), max(1, result_height)),
                Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS,
            )
        )
        self.result_photo = result_photo
        self.canvas.config(width=result_width, height=result_height)
        if self.embedded and isinstance(self.window, tk.Frame):
            self.window.place_configure(width=result_width, height=result_height)
        else:
            self.window.geometry(f"{result_width}x{result_height}+{self.menu_x}+{self.menu_y}")
        self.result_item = self.canvas.create_image(result_width // 2, result_height // 2, image=self.result_photo, anchor="center")
        self.draw_close_button(result_width)
        self.canvas.tag_bind(self.result_item, "<Button-1>", self.on_result_click)

    def show_result(self):
        if self.result_image is None:
            return
        self.showing_result = True
        self.canvas.delete("all")
        result_width = int(self.result_image.width * self.menu_scale)
        result_height = int(self.result_image.height * self.menu_scale)
        result_photo = ImageTk.PhotoImage(
            self.result_image.resize(
                (max(1, result_width), max(1, result_height)),
                Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS,
            )
        )
        self.result_photo = result_photo
        self.canvas.config(width=result_width, height=result_height)
        if self.embedded and isinstance(self.window, tk.Frame):
            self.window.place_configure(width=result_width, height=result_height)
        else:
            self.window.geometry(f"{result_width}x{result_height}+{self.menu_x}+{self.menu_y}")
        self.result_item = self.canvas.create_image(result_width // 2, result_height // 2, image=self.result_photo, anchor="center")
        self.draw_close_button(result_width)
        self.canvas.tag_bind(self.result_item, "<Button-1>", self.on_result_click)

    def on_result_click(self, event):
        if event.x >= self.canvas.winfo_width() - 80 and event.y <= 80:
            play_click_sound()
            self.close()

    def _flash_error(self, path):
        for item in self.item_data:
            if item["item_path"] == path:
                slot = item["slot_box"]
                red_id = self.canvas.create_rectangle(
                    slot[0],
                    slot[1],
                    slot[2],
                    slot[3],
                    fill="#ff0000",
                    outline="",
                )
                self.canvas.tag_lower(red_id, item["id"])
                self.canvas.after(200, lambda rid=red_id: self.canvas.delete(rid))
                return

