import os
import random
import math
from PIL import Image, ImageDraw


class TextureGenerator:
    def __init__(self):
        self.tex_dir = os.path.join("assets", "textures")
        os.makedirs(self.tex_dir, exist_ok=True)
        self._build_all_textures()

    def _build_all_textures(self):
        self._make_runway_texture()
        self._make_apron_texture()
        self._make_metal_panel_texture()
        self._make_corrugated_hangar_texture()
        self._make_terminal_windows_texture()
        self._make_server_rack_texture()
        self._make_hazard_texture()
        self._make_radar_grid_texture()

    def _make_runway_texture(self):
        path = os.path.join(self.tex_dir, "asphalt_runway.png")
        if os.path.exists(path):
            return
        w, h = 512, 1024
        img = Image.new("RGB", (w, h), (28, 32, 39))
        pixels = img.load()
        for y in range(h):
            for x in range(w):
                n = random.randint(-7, 7)
                pixels[x, y] = (max(0, 28 + n), max(0, 32 + n), max(0, 39 + n))

        draw = ImageDraw.Draw(img)
        draw.rectangle([24, 0, 36, h], fill=(210, 215, 225))
        draw.rectangle([w - 36, 0, w - 24, h], fill=(210, 215, 225))

        for x_bar in range(56, w - 56, 36):
            draw.rectangle([x_bar, 40, x_bar + 18, 135], fill=(205, 210, 220))
            draw.rectangle([x_bar, h - 135, x_bar + 18, h - 40], fill=(205, 210, 220))

        for y_dash in range(180, h - 180, 95):
            draw.rectangle([w // 2 - 7, y_dash, w // 2 + 7, y_dash + 52], fill=(215, 220, 225))

        for _ in range(45):
            sx = random.randint(w // 2 - 75, w // 2 + 75)
            sy = random.randint(170, 420)
            draw.line([(sx, sy), (sx, sy + random.randint(35, 90))], fill=(14, 16, 20), width=3)

        img.save(path)

    def _make_apron_texture(self):
        path = os.path.join(self.tex_dir, "apron_concrete.png")
        if os.path.exists(path):
            return
        size = 512
        img = Image.new("RGB", (size, size), (34, 39, 46))
        pixels = img.load()
        for y in range(size):
            for x in range(size):
                n = random.randint(-6, 6)
                pixels[x, y] = (34 + n, 39 + n, 46 + n)

        draw = ImageDraw.Draw(img)
        for g in range(0, size, 128):
            draw.line([(g, 0), (g, size)], fill=(22, 26, 32), width=2)
            draw.line([(0, g), (size, g)], fill=(22, 26, 32), width=2)
        # Línea guía amarilla de rodaje
        draw.rectangle([size // 2 - 5, 0, size // 2 + 5, size], fill=(215, 175, 45))
        img.save(path)

    def _make_metal_panel_texture(self):
        path = os.path.join(self.tex_dir, "metal_panel.png")
        if os.path.exists(path):
            return
        size = 512
        img = Image.new("RGB", (size, size), (36, 42, 52))
        pixels = img.load()
        for y in range(size):
            for x in range(size):
                n = random.randint(-5, 5)
                pixels[x, y] = (36 + n, 42 + n, 52 + n)

        draw = ImageDraw.Draw(img)
        for step in (0, 256):
            draw.rectangle([step, 0, step + 3, size], fill=(18, 22, 28))
            draw.rectangle([0, step, size, step + 3], fill=(18, 22, 28))
            for offset in range(24, 240, 48):
                draw.ellipse([step + 10, offset, step + 15, offset + 5], fill=(68, 78, 92))
                draw.ellipse([offset, step + 10, offset + 5, step + 15], fill=(68, 78, 92))

        img.save(path)

    def _make_corrugated_hangar_texture(self):
        path = os.path.join(self.tex_dir, "corrugated_hangar.png")
        if os.path.exists(path):
            return
        size = 512
        img = Image.new("RGB", (size, size), (32, 38, 48))
        draw = ImageDraw.Draw(img)
        for x in range(0, size, 16):
            shade = 46 if (x // 16) % 2 == 0 else 26
            draw.rectangle([x, 0, x + 15, size], fill=(shade, shade + 6, shade + 14))
        for y in range(size - 90, size):
            alpha_factor = (y - (size - 90)) / 90.0
            r_tint = int(32 + alpha_factor * 22)
            draw.line([(0, y), (size, y)], fill=(r_tint, 28, 30))
        img.save(path)

    def _make_terminal_windows_texture(self):
        path = os.path.join(self.tex_dir, "terminal_windows.png")
        if os.path.exists(path):
            return
        w, h = 512, 256
        img = Image.new("RGB", (w, h), (22, 28, 38))
        draw = ImageDraw.Draw(img)

        # Franjas de ventanales iluminados de la terminal
        for row_y in (36, 138):
            draw.rectangle([0, row_y - 8, w, row_y + 76], fill=(14, 18, 26))
            for col_x in range(16, w - 16, 48):
                lit = random.random() > 0.22
                win_col = (155, 205, 235) if lit else (28, 42, 58)
                draw.rectangle([col_x, row_y, col_x + 36, row_y + 68], fill=win_col)
                # Silueta interior sutil
                if lit and random.random() > 0.5:
                    draw.rectangle([col_x + 8, row_y + 38, col_x + 28, row_y + 68], fill=(85, 125, 155))
        img.save(path)

    def _make_server_rack_texture(self):
        path = os.path.join(self.tex_dir, "server_rack.png")
        if os.path.exists(path):
            return
        w, h = 256, 512
        img = Image.new("RGB", (w, h), (14, 18, 24))
        draw = ImageDraw.Draw(img)
        led_colors = [(40, 235, 120), (60, 190, 245), (245, 175, 50), (235, 55, 55)]
        for y in range(16, h - 16, 28):
            draw.rectangle([14, y, w - 14, y + 20], fill=(24, 30, 38), outline=(40, 48, 60))
            for lx in range(24, w - 30, 18):
                if random.random() > 0.35:
                    c = random.choice(led_colors)
                    draw.rectangle([lx, y + 7, lx + 6, y + 12], fill=c)
        img.save(path)

    def _make_hazard_texture(self):
        path = os.path.join(self.tex_dir, "hazard_stripe.png")
        if os.path.exists(path):
            return
        size = 256
        img = Image.new("RGB", (size, size), (225, 170, 35))
        draw = ImageDraw.Draw(img)
        for i in range(-size, size * 2, 48):
            draw.polygon([(i, 0), (i + 24, 0), (i - size + 24, size), (i - size, size)], fill=(22, 24, 28))
        img.save(path)

    def _make_radar_grid_texture(self):
        path = os.path.join(self.tex_dir, "radar_grid.png")
        if os.path.exists(path):
            return
        size = 768
        cx = cy = size // 2
        img = Image.new("RGBA", (size, size), (6, 20, 14, 255))
        draw = ImageDraw.Draw(img)

        for r in range(360, 10, -8):
            g_val = int(18 + (1 - r / 360) * 26)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(6, g_val, 14, 255))

        for r in (110, 220, 330, 368):
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(35, 180, 95, 160), width=2)

        draw.line([(cx - 368, cy), (cx + 368, cy)], fill=(30, 150, 80, 130), width=2)
        draw.line([(cx, cy - 368), (cx, cy + 368)], fill=(30, 150, 80, 130), width=2)
        diag = int(368 * 0.707)
        draw.line([(cx - diag, cy - diag), (cx + diag, cy + diag)], fill=(25, 120, 65, 80), width=1)
        draw.line([(cx - diag, cy + diag), (cx + diag, cy - diag)], fill=(25, 120, 65, 80), width=1)

        for deg in range(0, 360, 15):
            rad = math.radians(deg)
            inner = 352 if deg % 45 == 0 else 360
            x1, y1 = cx + math.cos(rad) * inner, cy + math.sin(rad) * inner
            x2, y2 = cx + math.cos(rad) * 368, cy + math.sin(rad) * 368
            draw.line([(x1, y1), (x2, y2)], fill=(45, 220, 120, 200), width=2)

        img.save(path)