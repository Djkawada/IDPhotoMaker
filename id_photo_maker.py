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

class IDPhotoMaker:
    def __init__(self, root):
        self.root = root
        self.root.title("French ID Photo Maker (35x45mm)")
        self.root.geometry("1000x800")

        # State
        self.original_image = None
        self.display_image = None
        self.photo_image = None  # Tkinter reference
        self.scale = 1.0
        self.angle = 0.0
        self.offset_x = 0
        self.offset_y = 0
        self.is_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # GUI Layout
        self.create_widgets()
        
    def create_widgets(self):
        # Top Control Panel
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X)

        btn_load = tk.Button(control_frame, text="Load Image", command=self.load_image, bg="#dddddd", height=2)
        btn_load.pack(side=tk.LEFT, padx=10)
        
        # Tools Frame (Rotation & Zoom)
        tools_frame = tk.Frame(control_frame)
        tools_frame.pack(side=tk.LEFT, padx=20)
        
        # Rotation
        tk.Label(tools_frame, text="Rotate:").grid(row=0, column=0, sticky="e")
        self.rot_slider = tk.Scale(tools_frame, from_=-45, to=45, orient=tk.HORIZONTAL, length=200, command=self.on_rotate_slide)
        self.rot_slider.set(0)
        self.rot_slider.grid(row=0, column=1)
        
        btn_rot90 = tk.Button(tools_frame, text="+90°", command=self.rotate_90)
        btn_rot90.grid(row=0, column=2, padx=5)

        # Zoom Slider (Alternative to scroll)
        tk.Label(tools_frame, text="Zoom:").grid(row=1, column=0, sticky="e")
        self.zoom_slider = tk.Scale(tools_frame, from_=10, to=400, orient=tk.HORIZONTAL, length=200, command=self.on_zoom_slide)
        self.zoom_slider.set(100)
        self.zoom_slider.grid(row=1, column=1)

        self.btn_save = tk.Button(control_frame, text="Save Printable Sheet (10x15cm)", command=self.save_result, bg="#4CAF50", fg="white", height=2, state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=10)
        
        # Instructions
        instr_label = tk.Label(self.root, text="Scroll or use Slider to ZOOM. Drag to MOVE.\nFit face between red lines (Chin to Top of Head).", font=("Arial", 10, "bold"))
        instr_label.pack(side=tk.TOP, pady=5)

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

    def get_px(self, mm):
        """Convert mm to pixels at current DPI"""
        return int(mm * MM_TO_INCH * DPI)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.JPG *.JPEG *.PNG *.WEBP *.BMP")])
        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path)
            # Convert to RGB if necessary
            if self.original_image.mode not in ("RGB", "RGBA"):
                self.original_image = self.original_image.convert("RGB")
            
            # Create a working preview image (max dim 1000px) for performance
            w, h = self.original_image.size
            max_dim = 1000
            if max(w, h) > max_dim:
                self.preview_ratio = max(w, h) / max_dim
                new_w = int(w / self.preview_ratio)
                new_h = int(h / self.preview_ratio)
                self.preview_image = self.original_image.resize((new_w, new_h), Image.Resampling.BILINEAR)
            else:
                self.preview_ratio = 1.0
                self.preview_image = self.original_image.copy()

            # Reset state
            self.angle = 0
            self.rot_slider.set(0)
            
            # Initial fit logic
            crop_w_px = self.get_px(PHOTO_WIDTH_MM)
            crop_h_px = self.get_px(PHOTO_HEIGHT_MM)
            
            img_w, img_h = self.preview_image.size
            scale_w = crop_w_px / img_w
            scale_h = crop_h_px / img_h
            initial_scale = max(scale_w, scale_h) * 1.5 
            
            self.scale = initial_scale
            # Update zoom slider roughly (100 = 1.0 scale relative to original, but we use internal scale)
            # Let's map zoom slider 100 to initial scale? No, simple map: 100 = 100% size?
            # Let's just update the slider value to match internal scale arbitrarily for now or just ignore consistency on load.
            # Better: Set slider to 100, and let 100 = initial_scale.
            self.base_scale = initial_scale / 1.0 # Reference
            self.zoom_slider.set(100) 
            
            # Center image
            scaled_w = img_w * self.scale
            scaled_h = img_h * self.scale
            self.offset_x = (CANVAS_WIDTH - scaled_w) / 2
            self.offset_y = (CANVAS_HEIGHT - scaled_h) / 2
            
            self.redraw()
            self.btn_save.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def on_rotate_slide(self, val):
        self.angle = float(val)
        self.redraw()
        
    def rotate_90(self):
        if self.original_image:
            self.original_image = self.original_image.rotate(-90, expand=True)
            
            # Regenerate preview from new original
            w, h = self.original_image.size
            max_dim = 1000
            if max(w, h) > max_dim:
                self.preview_ratio = max(w, h) / max_dim
                new_w = int(w / self.preview_ratio)
                new_h = int(h / self.preview_ratio)
                self.preview_image = self.original_image.resize((new_w, new_h), Image.Resampling.BILINEAR)
            else:
                self.preview_ratio = 1.0
                self.preview_image = self.original_image.copy()

            # Reset rotation slider to 0 as we changed the base image
            self.angle = 0
            self.rot_slider.set(0)
            # Re-center? Maybe keep offsets but dimensions changed.
            # Simple reset of center is safer for UX
            w, h = self.preview_image.size
            self.offset_x = (CANVAS_WIDTH - w * self.scale) / 2
            self.offset_y = (CANVAS_HEIGHT - h * self.scale) / 2
            self.redraw()

    def on_zoom_slide(self, val):
        # Slider is 10-400.
        # We need to map this to self.scale.
        # But self.scale changes via scroll too.
        # Let's say self.scale = (val / 100) * self.base_scale
        if hasattr(self, 'base_scale'):
            new_scale = (float(val) / 100.0) * self.base_scale
            # Center zoom?
            # Current center
            cx = CANVAS_WIDTH / 2
            cy = CANVAS_HEIGHT / 2
            
            # (cx - offset_x) / old_scale = image_x_center
            # new_offset_x = cx - image_x_center * new_scale
            
            img_x_center = (cx - self.offset_x) / self.scale
            img_y_center = (cy - self.offset_y) / self.scale
            
            self.scale = new_scale
            self.offset_x = cx - img_x_center * self.scale
            self.offset_y = cy - img_y_center * self.scale
            
            self.redraw()

    def redraw(self):
        if not self.original_image:
            return

        # Optimization: Use preview_image and NEAREST for fast rotation/display
        rotated = self.preview_image.rotate(self.angle, resample=Image.Resampling.NEAREST, expand=True)
        
        # 2. Calculate new size
        new_w = int(rotated.width * self.scale)
        new_h = int(rotated.height * self.scale)
        
        # 3. Resample for display
        display_img = rotated.resize((new_w, new_h), Image.Resampling.BILINEAR)
        self.photo_image = ImageTk.PhotoImage(display_img)

        # 4. Draw on Canvas
        self.canvas.delete("img")
        self.canvas.create_image(self.offset_x, self.offset_y, image=self.photo_image, anchor=tk.NW, tags="img")
        
        # 5. Bring overlay to top
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
        if self.is_dragging and self.original_image:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.offset_x += dx
            self.offset_y += dy
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
        # Update slider to match new scale
        if hasattr(self, 'base_scale') and self.base_scale > 0:
            current_slider = self.zoom_slider.get()
            new_val = current_slider * 1.1
            if new_val <= 400:
                self.zoom_slider.set(new_val)
            # redraw is called by slider command

    def on_zoom_out(self, event):
        if hasattr(self, 'base_scale') and self.base_scale > 0:
            current_slider = self.zoom_slider.get()
            new_val = current_slider / 1.1
            if new_val >= 10:
                self.zoom_slider.set(new_val)

    # --- Save Logic ---
    def save_result(self):
        if not self.original_image:
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
        if not save_path:
            return
            
        try:
            # 1. Apply Rotation to full image (High Quality)
            rotated_full = self.original_image.rotate(self.angle, resample=Image.Resampling.BICUBIC, expand=True)
            
            # 2. Crop
            # Screen Crop Box:
            cx = CANVAS_WIDTH // 2
            cy = CANVAS_HEIGHT // 2
            x1_screen = cx - self.crop_w // 2
            y1_screen = cy - self.crop_h // 2
            
            # Map screen coordinates to PREVIEW image coordinates
            # screen = preview * scale + offset
            # preview = (screen - offset) / scale
            
            crop_x_preview = (x1_screen - self.offset_x) / self.scale
            crop_y_preview = (y1_screen - self.offset_y) / self.scale
            crop_w_preview = self.crop_w / self.scale
            crop_h_preview = self.crop_h / self.scale
            
            # Map PREVIEW coordinates to ORIGINAL (Full Res) coordinates
            # original = preview * ratio
            ratio = self.preview_ratio
            
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
            final_photo = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # 3. Create Sheet (6 photos)
            sheet_w = self.get_px(PAPER_WIDTH_MM)
            sheet_h = self.get_px(PAPER_HEIGHT_MM)
            sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
            
            cols = 3
            rows = 2
            
            # Center on sheet with small gap
            gap_x = 10 
            gap_y = 10
            
            total_content_w = (cols * target_w) + ((cols - 1) * gap_x)
            total_content_h = (rows * target_h) + ((rows - 1) * gap_y)
            
            start_x = (sheet_w - total_content_w) // 2
            start_y = (sheet_h - total_content_h) // 2
            
            for r in range(rows):
                for c in range(cols):
                    px = start_x + c * (target_w + gap_x)
                    py = start_y + r * (target_h + gap_y)
                    sheet.paste(final_photo, (px, py))
            
            sheet.save(save_path, quality=95, dpi=(DPI, DPI))
            messagebox.showinfo("Success", f"Saved 6 photos to {save_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = IDPhotoMaker(root)
    root.mainloop()