import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps, ImageTk

# Constants for French ID Photos (35x45mm @ 300 DPI)
DPI = 300
MM_TO_INCH = 1 / 25.4
PHOTO_WIDTH_MM = 35
PHOTO_HEIGHT_MM = 45
FACE_MIN_MM = 32
FACE_MAX_MM = 36

# Canvas Dimensions (Screen display)
CANVAS_WIDTH = 620
CANVAS_HEIGHT = 590

# Paper Dimensions (10x15 cm)
PAPER_WIDTH_MM = 150
PAPER_HEIGHT_MM = 100

# Modern Dark Palette
BG_APP = "#16181d"
BG_PANEL = "#1f232b"
BG_CARD = "#262b36"
BG_CANVAS = "#111317"
FG_TEXT = "#e5e7eb"
FG_MUTED = "#9ca3af"
ACCENT_BLUE = "#3b82f6"
ACCENT_GREEN = "#10b981"
ACCENT_ORANGE = "#f97316"
ACCENT_RED = "#ef4444"
BTN_NEUTRAL = "#2d333f"


def _flatten_to_rgb(img: Image.Image) -> Image.Image:
    """Applies EXIF orientation and composites any alpha channel onto white RGB."""
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        white_bg = Image.new("RGB", rgba.size, (255, 255, 255))
        white_bg.paste(rgba, mask=rgba.split()[3])
        return white_bg
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


class PhotoState:
    def __init__(self):
        self.original: Image.Image | None = None
        self.preview: Image.Image | None = None
        self.preview_ratio: float = 1.0
        self.scale: float = 1.0
        self.base_scale: float = 1.0
        self.angle: float = 0.0
        # Center of the rotated image in canvas coordinates
        self.center_x: float = CANVAS_WIDTH / 2
        self.center_y: float = CANVAS_HEIGHT / 2
        self.has_image: bool = False

    def reset(self):
        self.original = None
        self.preview = None
        self.preview_ratio = 1.0
        self.scale = 1.0
        self.base_scale = 1.0
        self.angle = 0.0
        self.center_x = CANVAS_WIDTH / 2
        self.center_y = CANVAS_HEIGHT / 2
        self.has_image = False


class IDPhotoMaker:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("French ID Photo Maker (35x45mm)")
        self.root.geometry("1040x760")
        self.root.minsize(880, 640)
        self.root.configure(bg=BG_APP)

        self.photos = {1: PhotoState(), 2: PhotoState()}
        self.current_slot = 1

        self.is_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.photo_image_tk = None
        self.preview_sheet_tk = None
        self.crop_w = self.get_px(PHOTO_WIDTH_MM)
        self.crop_h = self.get_px(PHOTO_HEIGHT_MM)

        self.create_widgets()

    def get_px(self, mm: float) -> int:
        """Convert mm to pixels at current DPI."""
        return int(round(mm * MM_TO_INCH * DPI))

    def _make_button(self, parent, text, command, bg=BTN_NEUTRAL, fg=FG_TEXT, **kwargs):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
            **kwargs,
        )

    def create_widgets(self):
        # Main container: Left Sidebar + Right Canvas
        main_frame = tk.Frame(self.root, bg=BG_APP)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(14, 6))

        # --- Left Sidebar ---
        sidebar = tk.Frame(main_frame, bg=BG_PANEL, width=300, padx=14, pady=14)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="ID Photo Maker",
            bg=BG_PANEL,
            fg=FG_TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor=tk.W)
        tk.Label(
            sidebar,
            text="French 35×45 mm • 300 DPI • 10×15 cm sheet",
            bg=BG_PANEL,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, pady=(0, 14))

        # Slot Selection Card
        slot_card = tk.Frame(sidebar, bg=BG_CARD, padx=10, pady=10)
        slot_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            slot_card,
            text="PHOTO SLOTS",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        slot_btn_row = tk.Frame(slot_card, bg=BG_CARD)
        slot_btn_row.pack(fill=tk.X)
        self.btn_slot1 = self._make_button(
            slot_btn_row, "Photo 1 (Top)", lambda: self.switch_slot(1), bg=ACCENT_GREEN, fg="white"
        )
        self.btn_slot1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_slot2 = self._make_button(
            slot_btn_row, "Photo 2 (Bottom)", lambda: self.switch_slot(2), bg=BTN_NEUTRAL, fg=FG_TEXT
        )
        self.btn_slot2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        file_btn_row = tk.Frame(slot_card, bg=BG_CARD)
        file_btn_row.pack(fill=tk.X, pady=(8, 0))
        self.btn_load = self._make_button(
            file_btn_row, "Load Image", self.load_image, bg=ACCENT_BLUE, fg="white"
        )
        self.btn_load.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_clear = self._make_button(
            file_btn_row, "Clear Slot", self.clear_slot, bg=BTN_NEUTRAL, fg=ACCENT_RED
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(4, 0))

        # Adjustments Card
        adj_card = tk.Frame(sidebar, bg=BG_CARD, padx=10, pady=10)
        adj_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            adj_card,
            text="ADJUSTMENTS",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        tk.Label(adj_card, text="Rotate (°):", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9)).pack(anchor=tk.W)
        self.rot_slider = tk.Scale(
            adj_card,
            from_=-45,
            to=45,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            command=self.on_rotate_slide,
            bg=BG_CARD,
            fg=FG_TEXT,
            troughcolor=BG_CANVAS,
            highlightthickness=0,
            bd=0,
        )
        self.rot_slider.set(0)
        self.rot_slider.pack(fill=tk.X, pady=(0, 6))

        rot_btns = tk.Frame(adj_card, bg=BG_CARD)
        rot_btns.pack(fill=tk.X, pady=(0, 10))
        self._make_button(rot_btns, "-90°", lambda: self.rotate_90(90)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3)
        )
        self._make_button(rot_btns, "Reset", self.reset_transform).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=3
        )
        self._make_button(rot_btns, "+90°", lambda: self.rotate_90(-90)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0)
        )

        tk.Label(adj_card, text="Zoom (%):", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 9)).pack(anchor=tk.W)
        self.zoom_slider = tk.Scale(
            adj_card,
            from_=10,
            to=400,
            orient=tk.HORIZONTAL,
            command=self.on_zoom_slide,
            bg=BG_CARD,
            fg=FG_TEXT,
            troughcolor=BG_CANVAS,
            highlightthickness=0,
            bd=0,
        )
        self.zoom_slider.set(100)
        self.zoom_slider.pack(fill=tk.X)

        # Guide Legend Card
        guide_card = tk.Frame(sidebar, bg=BG_CARD, padx=10, pady=10)
        guide_card.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            guide_card,
            text="COMPLIANCE GUIDE",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=tk.W, pady=(0, 4))
        tk.Label(
            guide_card,
            text="• Drag to position, scroll to zoom.\n• Fit chin-to-crown between Cyan (32mm) and Red (36mm) ovals.\n• If 2 photos are loaded: 3 top + 3 bottom.",
            bg=BG_CARD,
            fg=FG_MUTED,
            justify=tk.LEFT,
            wraplength=250,
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W)

        # Export Buttons (bottom of sidebar)
        export_frame = tk.Frame(sidebar, bg=BG_PANEL)
        export_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_preview = self._make_button(
            export_frame, "Preview 10×15 Sheet", self.preview_sheet, bg=BTN_NEUTRAL, fg=FG_TEXT, state=tk.DISABLED
        )
        self.btn_preview.pack(fill=tk.X, pady=(0, 6))

        self.btn_save = self._make_button(
            export_frame, "Save Printable Sheet", self.save_result, bg=ACCENT_ORANGE, fg="white", state=tk.DISABLED
        )
        self.btn_save.pack(fill=tk.X)

        # --- Right Canvas Area ---
        canvas_container = tk.Frame(main_frame, bg=BG_PANEL, padx=10, pady=10)
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_container,
            bg=BG_CANVAS,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            highlightthickness=1,
            highlightbackground="#2d333f",
            cursor="fleur",
        )
        self.canvas.pack(anchor=tk.CENTER, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-4>", self.on_zoom_in)
        self.canvas.bind("<Button-5>", self.on_zoom_out)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready — Load a photo into Slot 1 or Slot 2.")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=BG_PANEL,
            fg=FG_MUTED,
            anchor=tk.W,
            padx=14,
            pady=5,
            font=("Segoe UI", 8),
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.draw_overlay()
        self.redraw()
        self.update_ui_state()

    def switch_slot(self, slot_num: int):
        self.current_slot = slot_num
        if slot_num == 1:
            self.btn_slot1.config(bg=ACCENT_GREEN, fg="white")
            self.btn_slot2.config(bg=BTN_NEUTRAL, fg=FG_TEXT)
        else:
            self.btn_slot1.config(bg=BTN_NEUTRAL, fg=FG_TEXT)
            self.btn_slot2.config(bg=ACCENT_GREEN, fg="white")

        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale > 0:
            self.rot_slider.set(state.angle)
            self.zoom_slider.set(max(10, min(400, (state.scale / state.base_scale) * 100)))
        else:
            self.rot_slider.set(0)
            self.zoom_slider.set(100)

        self.redraw()
        self.update_ui_state()

    def update_ui_state(self):
        has_any = self.photos[1].has_image or self.photos[2].has_image
        export_state = tk.NORMAL if has_any else tk.DISABLED
        self.btn_save.config(state=export_state)
        self.btn_preview.config(state=export_state)
        cur_has = self.photos[self.current_slot].has_image
        self.btn_clear.config(state=tk.NORMAL if cur_has else tk.DISABLED)

    def _build_preview(self, state: PhotoState):
        assert state.original is not None
        w, h = state.original.size
        max_dim = 1000
        if max(w, h) > max_dim:
            state.preview_ratio = max(w, h) / max_dim
            new_w = max(1, int(round(w / state.preview_ratio)))
            new_h = max(1, int(round(h / state.preview_ratio)))
            state.preview = state.original.resize((new_w, new_h), Image.Resampling.BILINEAR)
        else:
            state.preview_ratio = 1.0
            state.preview = state.original.copy()

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.JPG *.JPEG *.PNG *.WEBP *.BMP")]
        )
        if not file_path:
            return

        try:
            with Image.open(file_path) as raw:
                rgb_img = _flatten_to_rgb(raw)

            state = self.photos[self.current_slot]
            state.original = rgb_img
            self._build_preview(state)
            state.has_image = True
            state.angle = 0.0
            self.rot_slider.set(0)

            img_w, img_h = state.preview.size
            initial_scale = max(self.crop_w / img_w, self.crop_h / img_h) * 1.35
            state.scale = initial_scale
            state.base_scale = initial_scale
            self.zoom_slider.set(100)

            state.center_x = CANVAS_WIDTH / 2
            state.center_y = CANVAS_HEIGHT / 2

            self.status_var.set(f"Loaded photo into Slot {self.current_slot} ({rgb_img.width}×{rgb_img.height}px).")
            self.redraw()
            self.update_ui_state()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def clear_slot(self):
        self.photos[self.current_slot].reset()
        self.rot_slider.set(0)
        self.zoom_slider.set(100)
        self.status_var.set(f"Cleared Slot {self.current_slot}.")
        self.redraw()
        self.update_ui_state()

    def reset_transform(self):
        state = self.photos[self.current_slot]
        if not state.has_image:
            return
        state.angle = 0.0
        state.scale = state.base_scale
        state.center_x = CANVAS_WIDTH / 2
        state.center_y = CANVAS_HEIGHT / 2
        self.rot_slider.set(0)
        self.zoom_slider.set(100)
        self.redraw()

    def on_rotate_slide(self, val):
        state = self.photos[self.current_slot]
        if state.has_image:
            state.angle = float(val)
            self.redraw()

    def rotate_90(self, degrees: int):
        state = self.photos[self.current_slot]
        if state.has_image and state.original:
            state.original = state.original.rotate(degrees, expand=True)
            self._build_preview(state)
            state.angle = 0.0
            self.rot_slider.set(0)
            state.center_x = CANVAS_WIDTH / 2
            state.center_y = CANVAS_HEIGHT / 2
            self.redraw()

    def on_zoom_slide(self, val):
        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale > 0:
            state.scale = (float(val) / 100.0) * state.base_scale
            self.redraw()

    def redraw(self):
        state = self.photos[self.current_slot]
        self.canvas.delete("img")

        if not state.has_image or state.preview is None:
            self.canvas.create_text(
                CANVAS_WIDTH // 2,
                CANVAS_HEIGHT // 2,
                text=f"Slot {self.current_slot} Empty\nClick 'Load Image' to begin",
                fill=FG_MUTED,
                font=("Segoe UI", 16),
                justify=tk.CENTER,
                tags="img",
            )
        else:
            rotated = state.preview.rotate(
                state.angle, resample=Image.Resampling.BILINEAR, expand=True, fillcolor=(255, 255, 255)
            )
            new_w = max(1, int(round(rotated.width * state.scale)))
            new_h = max(1, int(round(rotated.height * state.scale)))
            display_img = rotated.resize((new_w, new_h), Image.Resampling.BILINEAR)
            self.photo_image_tk = ImageTk.PhotoImage(display_img)
            self.canvas.create_image(
                state.center_x, state.center_y, image=self.photo_image_tk, anchor=tk.CENTER, tags="img"
            )

        self.canvas.tag_raise("overlay")
        self.canvas.tag_raise("guide")

    def draw_overlay(self):
        self.canvas.delete("overlay")
        self.canvas.delete("guide")

        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2
        self.crop_w = self.get_px(PHOTO_WIDTH_MM)
        self.crop_h = self.get_px(PHOTO_HEIGHT_MM)

        x1 = cx - self.crop_w // 2
        y1 = cy - self.crop_h // 2
        x2 = x1 + self.crop_w
        y2 = y1 + self.crop_h

        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, y1, fill="#000000", stipple="gray50", width=0, tags="overlay")
        self.canvas.create_rectangle(0, y2, CANVAS_WIDTH, CANVAS_HEIGHT, fill="#000000", stipple="gray50", width=0, tags="overlay")
        self.canvas.create_rectangle(0, y1, x1, y2, fill="#000000", stipple="gray50", width=0, tags="overlay")
        self.canvas.create_rectangle(x2, y1, CANVAS_WIDTH, y2, fill="#000000", stipple="gray50", width=0, tags="overlay")

        self.canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2, tags="overlay")
        self.canvas.create_line(cx, y1, cx, y2, fill="#ffffff", dash=(2, 6), tags="guide")

        px_32 = self.get_px(FACE_MIN_MM)
        px_36 = self.get_px(FACE_MAX_MM)
        face_w_px = self.get_px(24)

        self.canvas.create_oval(
            cx - face_w_px // 2, cy - px_36 // 2, cx + face_w_px // 2, cy + px_36 // 2,
            outline="#ef4444", width=2, dash=(4, 4), tags="guide",
        )
        self.canvas.create_oval(
            cx - face_w_px // 2, cy - px_32 // 2, cx + face_w_px // 2, cy + px_32 // 2,
            outline="#22d3ee", width=2, dash=(4, 4), tags="guide",
        )
        self.canvas.create_text(
            cx, y2 + 16, text="Face Height: Red = 36mm Max  |  Cyan = 32mm Min",
            fill=FG_TEXT, font=("Segoe UI", 8, "bold"), tags="guide",
        )

    # --- Interaction Handlers ---
    def on_mouse_down(self, event):
        self.is_dragging = True
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def on_mouse_drag(self, event):
        state = self.photos[self.current_slot]
        if self.is_dragging and state.has_image:
            state.center_x += event.x - self.last_mouse_x
            state.center_y += event.y - self.last_mouse_y
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.redraw()

    def on_mouse_up(self, event):
        self.is_dragging = False

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.on_zoom_in(event)
        elif event.delta < 0:
            self.on_zoom_out(event)

    def on_zoom_in(self, event):
        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale > 0:
            new_val = min(400.0, self.zoom_slider.get() * 1.1)
            self.zoom_slider.set(new_val)

    def on_zoom_out(self, event):
        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale > 0:
            new_val = max(10.0, self.zoom_slider.get() / 1.1)
            self.zoom_slider.set(new_val)

    # --- Export / Sheet Generation ---
    def process_image(self, state: PhotoState) -> Image.Image | None:
        """Processes a PhotoState into a 35x45mm 300 DPI RGB image with white padding."""
        if not state.has_image or not state.original:
            return None

        rotated_full = state.original.rotate(
            state.angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255)
        )

        # Crop box center relative to rotated image center in screen pixels
        cx_screen = CANVAS_WIDTH // 2
        cy_screen = CANVAS_HEIGHT // 2
        dx_screen = cx_screen - state.center_x
        dy_screen = cy_screen - state.center_y

        # Convert screen offset & crop size into original-resolution pixels
        factor = state.preview_ratio / state.scale
        crop_w_orig = self.crop_w * factor
        crop_h_orig = self.crop_h * factor
        crop_cx_orig = (rotated_full.width / 2.0) + (dx_screen * factor)
        crop_cy_orig = (rotated_full.height / 2.0) + (dy_screen * factor)

        left = int(round(crop_cx_orig - crop_w_orig / 2.0))
        top = int(round(crop_cy_orig - crop_h_orig / 2.0))
        right = left + max(1, int(round(crop_w_orig)))
        bottom = top + max(1, int(round(crop_h_orig)))

        # Composite onto white background so out-of-bounds areas are white, never black
        canvas = Image.new("RGB", (right - left, bottom - top), (255, 255, 255))
        src_left = max(0, left)
        src_top = max(0, top)
        src_right = min(rotated_full.width, right)
        src_bottom = min(rotated_full.height, bottom)

        if src_right > src_left and src_bottom > src_top:
            region = rotated_full.crop((src_left, src_top, src_right, src_bottom))
            canvas.paste(region, (src_left - left, src_top - top))

        return canvas.resize((self.crop_w, self.crop_h), Image.Resampling.LANCZOS)

    def build_sheet(self) -> Image.Image | None:
        img1 = self.process_image(self.photos[1])
        img2 = self.process_image(self.photos[2])
        if not img1 and not img2:
            return None

        sheet_w = self.get_px(PAPER_WIDTH_MM)
        sheet_h = self.get_px(PAPER_HEIGHT_MM)
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")

        cols, rows = 3, 2
        gap_x, gap_y = 10, 10
        total_w = (cols * self.crop_w) + ((cols - 1) * gap_x)
        total_h = (rows * self.crop_h) + ((rows - 1) * gap_y)
        start_x = (sheet_w - total_w) // 2
        start_y = (sheet_h - total_h) // 2

        if img1 and img2:
            row_sources = [img1, img2]
        elif img1:
            row_sources = [img1, img1]
        else:
            row_sources = [img2, img2]

        for r in range(rows):
            for c in range(cols):
                px = start_x + c * (self.crop_w + gap_x)
                py = start_y + r * (self.crop_h + gap_y)
                sheet.paste(row_sources[r], (px, py))

        return sheet

    def preview_sheet(self):
        sheet = self.build_sheet()
        if sheet is None:
            return

        popup = tk.Toplevel(self.root)
        popup.title("10×15 cm Sheet Preview")
        popup.configure(bg=BG_PANEL)
        popup.transient(self.root)

        preview_img = sheet.copy()
        preview_img.thumbnail((720, 480), Image.Resampling.LANCZOS)
        self.preview_sheet_tk = ImageTk.PhotoImage(preview_img)

        tk.Label(popup, image=self.preview_sheet_tk, bg=BG_PANEL).pack(padx=14, pady=(14, 8))
        self._make_button(popup, "Close", popup.destroy, bg=BTN_NEUTRAL).pack(pady=(0, 12))

    def save_result(self):
        sheet = self.build_sheet()
        if sheet is None:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg *.jpeg"), ("PNG", "*.png")],
        )
        if not save_path:
            return

        try:
            if save_path.lower().endswith(".png"):
                sheet.save(save_path, dpi=(DPI, DPI))
            else:
                sheet.save(save_path, quality=95, dpi=(DPI, DPI))
            self.status_var.set(f"Saved printable sheet to {save_path}")
            messagebox.showinfo("Success", f"Saved sheet to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = IDPhotoMaker(root)
    root.mainloop()
