import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import sys

# Constants for French ID Photos
DPI = 300
MM_TO_INCH = 1 / 25.4
PHOTO_WIDTH_MM = 35
PHOTO_HEIGHT_MM = 45
FACE_MIN_MM = 32
FACE_MAX_MM = 36

# Canvas Dimensions (Screen display)
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 500
CROP_FRAME_SCALE = 1.0  # Scale factor for display on screen vs actual print pixels

# Paper Dimensions (10x15 cm)
PAPER_WIDTH_MM = 150
PAPER_HEIGHT_MM = 100
MARGIN_MM = 2

class PhotoState:
    def __init__(self):
        self.original = None
        self.preview = None
        self.preview_ratio = 1.0
        self.scale = 1.0
        self.angle = 0.0
        self.offset_x = 0
        self.offset_y = 0
        self.base_scale = 1.0
        self.has_image = False

class IDPhotoMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("French ID Photo Maker (35x45mm)")
        self.root.geometry("1000x850")

        # State management for 2 photos
        self.photos = {1: PhotoState(), 2: PhotoState()}
        self.current_slot = 1
        
        # Interaction state
        self.is_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.photo_image_tk = None # Keep reference

        # GUI Layout
        self.create_widgets()
        
    def create_widgets(self):
        # Top Control Panel
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X)

        # Slot Selection and Loading
        slot_frame = tk.Frame(control_frame, relief=tk.GROOVE, borderwidth=1)
        slot_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(slot_frame, text="Select Photo to Edit:").pack(anchor=tk.W, padx=5)
        
        self.btn_slot1 = tk.Button(slot_frame, text="Photo 1 (Top Row)", command=lambda: self.switch_slot(1), width=15, bg="#4CAF50", fg="white")
        self.btn_slot1.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_slot2 = tk.Button(slot_frame, text="Photo 2 (Bottom Row)", command=lambda: self.switch_slot(2), width=15, bg="#dddddd")
        self.btn_slot2.pack(side=tk.LEFT, padx=5, pady=5)

        btn_load = tk.Button(control_frame, text="Load Image", command=self.load_image, bg="#2196F3", fg="white", height=2)
        btn_load.pack(side=tk.LEFT, padx=20)
        
        # Tools Frame (Rotation & Zoom)
        tools_frame = tk.Frame(control_frame)
        tools_frame.pack(side=tk.LEFT, padx=20)
        
        # Rotation
        tk.Label(tools_frame, text="Rotate:").grid(row=0, column=0, sticky="e")
        self.rot_slider = tk.Scale(tools_frame, from_=-45, to=45, orient=tk.HORIZONTAL, length=150, command=self.on_rotate_slide)
        self.rot_slider.set(0)
        self.rot_slider.grid(row=0, column=1)
        
        btn_rot90 = tk.Button(tools_frame, text="+90°", command=self.rotate_90)
        btn_rot90.grid(row=0, column=2, padx=5)

        # Zoom Slider (Alternative to scroll)
        tk.Label(tools_frame, text="Zoom:").grid(row=1, column=0, sticky="e")
        self.zoom_slider = tk.Scale(tools_frame, from_=10, to=400, orient=tk.HORIZONTAL, length=150, command=self.on_zoom_slide)
        self.zoom_slider.set(100)
        self.zoom_slider.grid(row=1, column=1)

        self.btn_save = tk.Button(control_frame, text="Save Printable Sheet", command=self.save_result, bg="#FF5722", fg="white", height=2, state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=10)
        
        # Instructions
        instr_frame = tk.Frame(self.root)
        instr_frame.pack(side=tk.TOP, pady=5)
        tk.Label(instr_frame, text="1. Select 'Photo 1' or 'Photo 2'.  2. Click 'Load Image'.  3. Adjust (Zoom/Rotate/Drag).", font=("Arial", 10)).pack()
        tk.Label(instr_frame, text="Fit face between red lines. If 2 photos are loaded, sheet will have 3 of each.", font=("Arial", 9, "bold"), fg="#666").pack()

        # Main Canvas area
        self.canvas_frame = tk.Frame(self.root, bg="#333333")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#333333", width=CANVAS_WIDTH, height=CANVAS_HEIGHT, cursor="fleur")
        self.canvas.pack(anchor=tk.CENTER, expand=True)

        # Events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        # Mouse wheel for zoom (Linux usually Button-4/5 or MouseWheel)
        self.canvas.bind("<Button-4>", self.on_zoom_in)
        self.canvas.bind("<Button-5>", self.on_zoom_out)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        self.draw_overlay()
        self.update_ui_state()

    def get_px(self, mm):
        """Convert mm to pixels at current DPI"""
        return int(mm * MM_TO_INCH * DPI)
    
    def switch_slot(self, slot_num):
        self.current_slot = slot_num
        
        # Update buttons visual
        if slot_num == 1:
            self.btn_slot1.config(bg="#4CAF50", fg="white")
            self.btn_slot2.config(bg="#dddddd", fg="black")
        else:
            self.btn_slot1.config(bg="#dddddd", fg="black")
            self.btn_slot2.config(bg="#4CAF50", fg="white")
            
        # Update sliders to match state
        state = self.photos[self.current_slot]
        if state.has_image:
            self.rot_slider.set(state.angle)
            # Map scale back to slider? 
            # Slider = (scale / base_scale) * 100
            if state.base_scale > 0:
                slider_val = (state.scale / state.base_scale) * 100
                self.zoom_slider.set(slider_val)
        else:
            self.rot_slider.set(0)
            self.zoom_slider.set(100)
            
        self.redraw()
        self.update_ui_state()

    def update_ui_state(self):
        # Enable save if at least one photo is loaded
        if self.photos[1].has_image or self.photos[2].has_image:
            self.btn_save.config(state=tk.NORMAL)
        else:
            self.btn_save.config(state=tk.DISABLED)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.JPG *.JPEG *.PNG *.WEBP *.BMP")])
        if not file_path:
            return

        try:
            state = self.photos[self.current_slot]
            state.original = Image.open(file_path)
            # Convert to RGB if necessary
            if state.original.mode not in ("RGB", "RGBA"):
                state.original = state.original.convert("RGB")
            
            # Create a working preview image (max dim 1000px) for performance
            w, h = state.original.size
            max_dim = 1000
            if max(w, h) > max_dim:
                state.preview_ratio = max(w, h) / max_dim
                new_w = int(w / state.preview_ratio)
                new_h = int(h / state.preview_ratio)
                state.preview = state.original.resize((new_w, new_h), Image.Resampling.BILINEAR)
            else:
                state.preview_ratio = 1.0
                state.preview = state.original.copy()

            state.has_image = True
            
            # Reset state
            state.angle = 0
            self.rot_slider.set(0)
            
            # Initial fit logic
            crop_w_px = self.get_px(PHOTO_WIDTH_MM)
            crop_h_px = self.get_px(PHOTO_HEIGHT_MM)
            
            img_w, img_h = state.preview.size
            scale_w = crop_w_px / img_w
            scale_h = crop_h_px / img_h
            initial_scale = max(scale_w, scale_h) * 1.5 
            
            state.scale = initial_scale
            state.base_scale = initial_scale / 1.0
            self.zoom_slider.set(100) 
            
            # Center image
            scaled_w = img_w * state.scale
            scaled_h = img_h * state.scale
            state.offset_x = (CANVAS_WIDTH - scaled_w) / 2
            state.offset_y = (CANVAS_HEIGHT - scaled_h) / 2
            
            self.redraw()
            self.update_ui_state()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def on_rotate_slide(self, val):
        state = self.photos[self.current_slot]
        if state.has_image:
            state.angle = float(val)
            self.redraw()
        
    def rotate_90(self):
        state = self.photos[self.current_slot]
        if state.has_image and state.original:
            state.original = state.original.rotate(-90, expand=True)
            
            # Regenerate preview
            w, h = state.original.size
            max_dim = 1000
            if max(w, h) > max_dim:
                state.preview_ratio = max(w, h) / max_dim
                new_w = int(w / state.preview_ratio)
                new_h = int(h / state.preview_ratio)
                state.preview = state.original.resize((new_w, new_h), Image.Resampling.BILINEAR)
            else:
                state.preview_ratio = 1.0
                state.preview = state.original.copy()

            state.angle = 0
            self.rot_slider.set(0)
            
            # Re-center
            w, h = state.preview.size
            state.offset_x = (CANVAS_WIDTH - w * state.scale) / 2
            state.offset_y = (CANVAS_HEIGHT - h * state.scale) / 2
            self.redraw()

    def on_zoom_slide(self, val):
        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale:
            new_scale = (float(val) / 100.0) * state.base_scale
            
            # Center zoom logic
            cx = CANVAS_WIDTH / 2
            cy = CANVAS_HEIGHT / 2
            
            img_x_center = (cx - state.offset_x) / state.scale
            img_y_center = (cy - state.offset_y) / state.scale
            
            state.scale = new_scale
            state.offset_x = cx - img_x_center * state.scale
            state.offset_y = cy - img_y_center * state.scale
            
            self.redraw()

    def redraw(self):
        state = self.photos[self.current_slot]
        
        self.canvas.delete("img")
        
        if not state.has_image:
            # Show "Empty" text
            self.canvas.create_text(CANVAS_WIDTH//2, CANVAS_HEIGHT//2, text=f"Slot {self.current_slot} Empty\nClick 'Load Image'", fill="#666", font=("Arial", 20), tags="img")
        else:
            rotated = state.preview.rotate(state.angle, resample=Image.Resampling.NEAREST, expand=True)
            new_w = int(rotated.width * state.scale)
            new_h = int(rotated.height * state.scale)
            
            display_img = rotated.resize((new_w, new_h), Image.Resampling.BILINEAR)
            self.photo_image_tk = ImageTk.PhotoImage(display_img)

            self.canvas.create_image(state.offset_x, state.offset_y, image=self.photo_image_tk, anchor=tk.NW, tags="img")
        
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
        x2 = cx + self.crop_w // 2
        y2 = cy + self.crop_h // 2
        
        # Darken outside
        self.canvas.create_rectangle(0, 0, CANVAS_WIDTH, y1, fill="#000000", stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(0, y2, CANVAS_WIDTH, CANVAS_HEIGHT, fill="#000000", stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(0, y1, x1, y2, fill="#000000", stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(x2, y1, CANVAS_WIDTH, y2, fill="#000000", stipple="gray50", tags="overlay")
        
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="white", width=2, tags="overlay")
        
        px_32 = self.get_px(FACE_MIN_MM)
        px_36 = self.get_px(FACE_MAX_MM)
        
        ccx = x1 + self.crop_w // 2
        ccy = y1 + self.crop_h // 2
        
        face_w_px = self.get_px(24) 
        
        self.canvas.create_oval(ccx - face_w_px//2, ccy - px_36//2, 
                                ccx + face_w_px//2, ccy + px_36//2,
                                outline="red", width=2, dash=(4, 4), tags="guide")
        
        self.canvas.create_oval(ccx - face_w_px//2, ccy - px_32//2, 
                                ccx + face_w_px//2, ccy + px_32//2,
                                outline="cyan", width=2, dash=(4, 4), tags="guide")
                                
        self.canvas.create_text(ccx, ccy, text="Face Limit (Red=Max, Cyan=Min)", fill="white", font=("Arial", 8), tags="guide")


    # --- Interaction Handlers ---
    def on_mouse_down(self, event):
        self.is_dragging = True
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def on_mouse_drag(self, event):
        state = self.photos[self.current_slot]
        if self.is_dragging and state.has_image:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            state.offset_x += dx
            state.offset_y += dy
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.redraw()

    def on_mouse_up(self, event):
        self.is_dragging = False

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.on_zoom_in(event)
        else:
            self.on_zoom_out(event)

    def on_zoom_in(self, event):
        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale > 0:
            current_slider = self.zoom_slider.get()
            new_val = current_slider * 1.1
            if new_val <= 400:
                self.zoom_slider.set(new_val)

    def on_zoom_out(self, event):
        state = self.photos[self.current_slot]
        if state.has_image and state.base_scale > 0:
            current_slider = self.zoom_slider.get()
            new_val = current_slider / 1.1
            if new_val >= 10:
                self.zoom_slider.set(new_val)

    # --- Save Logic ---
    def process_image(self, state):
        """Processes a single PhotoState and returns the final PIL image (35x45mm at 300DPI)"""
        if not state.has_image or not state.original:
            return None
            
        # 1. High Quality Rotation
        rotated_full = state.original.rotate(state.angle, resample=Image.Resampling.BICUBIC, expand=True)
        
        # 2. Crop
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2
        x1_screen = cx - self.crop_w // 2
        y1_screen = cy - self.crop_h // 2
        
        # Map to PREVIEW coords
        crop_x_preview = (x1_screen - state.offset_x) / state.scale
        crop_y_preview = (y1_screen - state.offset_y) / state.scale
        crop_w_preview = self.crop_w / state.scale
        crop_h_preview = self.crop_h / state.scale
        
        # Map to ORIGINAL coords
        ratio = state.preview_ratio
        crop_x_final = crop_x_preview * ratio
        crop_y_final = crop_y_preview * ratio
        crop_w_final = crop_w_preview * ratio
        crop_h_final = crop_h_preview * ratio
        
        cropped = rotated_full.crop((
            crop_x_final, 
            crop_y_final, 
            crop_x_final + crop_w_final, 
            crop_y_final + crop_h_final
        ))
        
        # Resize to Target
        target_w = self.get_px(PHOTO_WIDTH_MM)
        target_h = self.get_px(PHOTO_HEIGHT_MM)
        return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def save_result(self):
        # Generate final images
        img1 = self.process_image(self.photos[1])
        img2 = self.process_image(self.photos[2])
        
        if not img1 and not img2:
            return # Should be blocked by UI state anyway
            
        save_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
        if not save_path:
            return
            
        try:
            target_w = self.get_px(PHOTO_WIDTH_MM)
            target_h = self.get_px(PHOTO_HEIGHT_MM)
            
            # Create Sheet (6 photos)
            sheet_w = self.get_px(PAPER_WIDTH_MM)
            sheet_h = self.get_px(PAPER_HEIGHT_MM)
            sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
            
            cols = 3
            rows = 2
            
            gap_x = 10 
            gap_y = 10
            
            total_content_w = (cols * target_w) + ((cols - 1) * gap_x)
            total_content_h = (rows * target_h) + ((rows - 1) * gap_y)
            
            start_x = (sheet_w - total_content_w) // 2
            start_y = (sheet_h - total_content_h) // 2
            
            # Logic: 
            # If both img1 and img2 exist: Row 1 = img1, Row 2 = img2.
            # If only img1: All 6 = img1.
            # If only img2: All 6 = img2.
            
            # Top Row
            source_top = img1 if img1 else img2
            
            # Bottom Row
            source_bottom = img2 if img2 else img1
            
            # If user explicitly loaded 2 photos, use top/bottom split.
            # If user only loaded 1 (whichever slot), duplicate it everywhere.
            if img1 and img2:
                row_sources = [img1, img2]
            elif img1:
                row_sources = [img1, img1]
            else:
                row_sources = [img2, img2]

            for r in range(rows):
                source_img = row_sources[r]
                for c in range(cols):
                    px = start_x + c * (target_w + gap_x)
                    py = start_y + r * (target_h + gap_y)
                    sheet.paste(source_img, (px, py))
            
            sheet.save(save_path, quality=95, dpi=(DPI, DPI))
            messagebox.showinfo("Success", f"Saved sheet to {save_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = IDPhotoMaker(root)
    root.mainloop()
