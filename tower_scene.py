import os
from ursina import *
import random
import math
import config


def is_valid_glb(path):
    """Verifica que el archivo .glb exista y tenga cabecera binaria glTF válida."""
    if not os.path.exists(path) or os.path.getsize(path) < 64:
        return False
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"glTF"
    except Exception:
        return False


def make_tube_mesh(sections, sides=12):
    """Genera una malla 3D suavizada a partir de secciones transversales (z, y_center, rx, ry)."""
    verts = []
    tris = []
    for z, yc, rx, ry in sections:
        for i in range(sides):
            ang = (i / sides) * 2.0 * math.pi
            verts.append(Vec3(math.cos(ang) * rx, yc + math.sin(ang) * ry, z))

    for s in range(len(sections) - 1):
        row1 = s * sides
        row2 = (s + 1) * sides
        for i in range(sides):
            nxt = (i + 1) % sides
            tris.append((row1 + i, row2 + i, row2 + nxt))
            tris.append((row1 + i, row2 + nxt, row1 + nxt))

    c_start = len(verts)
    verts.append(Vec3(0, sections[0][1], sections[0][0]))
    for i in range(sides):
        nxt = (i + 1) % sides
        tris.append((c_start, nxt, i))

    c_end = len(verts)
    last_row = (len(sections) - 1) * sides
    verts.append(Vec3(0, sections[-1][1], sections[-1][0]))
    for i in range(sides):
        nxt = (i + 1) % sides
        tris.append((c_end, last_row + i, last_row + nxt))

    m = Mesh(vertices=verts, triangles=tris, mode='triangle')
    m.generate_normals()
    return m


def make_swept_wing_mesh(side=1):
    """Malla 3D de ala en flecha con perfil aerodinámico y winglet (side: -1 izq, 1 der)."""
    s = side
    verts = [
        Vec3(0.35 * s, -0.05, 0.95),
        Vec3(0.35 * s, -0.05, -0.85),
        Vec3(0.35 * s, 0.14, 0.15),
        Vec3(4.55 * s, 0.12, -0.85),
        Vec3(4.55 * s, 0.12, -1.65),
        Vec3(4.55 * s, 0.22, -1.25),
        Vec3(4.78 * s, 0.68, -1.35),
        Vec3(4.78 * s, 0.68, -1.78),
    ]
    tris = [
        (0, 2, 3), (2, 5, 3),
        (2, 1, 5), (1, 4, 5),
        (0, 3, 1), (1, 3, 4),
        (3, 5, 6), (5, 7, 6),
        (3, 6, 4), (4, 6, 7),
    ]
    m = Mesh(vertices=verts, triangles=tris, mode='triangle')
    m.generate_normals()
    return m


def make_tail_fin_mesh():
    """Malla 3D del estabilizador vertical de cola."""
    verts = [
        Vec3(-0.06, 0.32, -2.15),
        Vec3(0.06, 0.32, -2.15),
        Vec3(-0.06, 0.32, -3.75),
        Vec3(0.06, 0.32, -3.75),
        Vec3(-0.03, 1.92, -3.25),
        Vec3(0.03, 1.92, -3.25),
        Vec3(-0.03, 1.92, -4.05),
        Vec3(0.03, 1.92, -4.05),
    ]
    tris = [
        (0, 4, 2), (2, 4, 6),
        (1, 3, 5), (3, 7, 5),
        (0, 1, 4), (1, 5, 4),
        (2, 6, 3), (3, 6, 7),
        (4, 5, 6), (5, 7, 6),
    ]
    m = Mesh(vertices=verts, triangles=tris, mode='triangle')
    m.generate_normals()
    return m


class Airplane3D(Entity):
    """Aeronave 3D esculpida con fuselaje, alas en flecha, turbinas, tren y rodaje en pista."""
    def __init__(self, parent, is_ghost=False, parked=False, craft_scale=2.45):
        super().__init__(parent=parent, scale=craft_scale)
        self.is_ghost = is_ghost
        body_col = config.rgb(26, 18, 22) if is_ghost else config.rgb(228, 235, 244)
        wing_col = config.rgb(38, 22, 28) if is_ghost else config.rgb(180, 190, 205)
        tail_col = config.rgb(165, 22, 28) if is_ghost else config.rgb(24, 88, 165)

        fuselage_sections = [
            (-4.05, 0.22, 0.05, 0.05),
            (-2.40, 0.06, 0.44, 0.46),
            (-1.20, 0.00, 0.56, 0.58),
            (1.90,  0.00, 0.56, 0.58),
            (2.85, -0.04, 0.42, 0.44),
            (3.75, -0.09, 0.18, 0.19),
            (4.15, -0.11, 0.03, 0.03),
        ]
        Entity(parent=self, model=make_tube_mesh(fuselage_sections, 14), color=body_col, double_sided=True)

        Entity(parent=self, model='cube', position=(0, 0.24, 2.75), rotation=(24, 0, 0), scale=(0.56, 0.16, 0.58), color=config.rgb(14, 24, 36))
        if not is_ghost:
            Entity(parent=self, model='cube', position=(0, 0.14, 0.25), scale=(1.13, 0.11, 3.6), color=config.rgb(195, 230, 255), unlit=True)

        Entity(parent=self, model=make_swept_wing_mesh(-1), color=wing_col, double_sided=True)
        Entity(parent=self, model=make_swept_wing_mesh(1), color=wing_col, double_sided=True)

        Entity(parent=self, model=make_tail_fin_mesh(), color=tail_col, double_sided=True)
        Entity(parent=self, model='cube', position=(0, 0.24, -3.45), scale=(3.1, 0.06, 0.68), color=wing_col)

        nacelle_sec = [
            (-0.65, 0, 0.22, 0.22),
            (0.0,   0, 0.27, 0.27),
            (0.65,  0, 0.24, 0.24),
        ]
        for side in (-1.75, 1.75):
            Entity(parent=self, model=make_tube_mesh(nacelle_sec, 10), position=(side, -0.32, 0.35), color=config.rgb(110, 120, 135), double_sided=True)
            glow_col = config.COLOR_ALERT_RED if is_ghost else config.rgb(255, 175, 85)
            Entity(parent=self, model='sphere', position=(side, -0.32, 0.96), scale=0.34, color=glow_col, unlit=True)

        # Tren de aterrizaje desplegado
        for gx, gz in [(0, 2.35), (-0.75, -0.35), (0.75, -0.35)]:
            Entity(parent=self, model='cube', position=(gx, -0.62, gz), scale=(0.08, 0.48, 0.08), color=config.rgb(65, 72, 82))
            Entity(parent=self, model='sphere', position=(gx, -0.84, gz), scale=(0.16, 0.24, 0.24), color=config.rgb(22, 24, 28))

        if is_ghost:
            Entity(parent=self, model='sphere', position=(-4.72, 0.68, -1.55), scale=0.26, color=config.COLOR_ALERT_RED, unlit=True)
            Entity(parent=self, model='sphere', position=(4.72, 0.68, -1.55), scale=0.26, color=config.COLOR_ALERT_RED, unlit=True)
            Entity(parent=self, model='sphere', position=(0, -0.10, 4.15), scale=0.40, color=config.COLOR_ALERT_RED, unlit=True)
        else:
            Entity(parent=self, model='sphere', position=(-4.72, 0.68, -1.55), scale=0.14, color=config.COLOR_ALERT_RED, unlit=True)
            Entity(parent=self, model='sphere', position=(4.72, 0.68, -1.55), scale=0.14, color=config.COLOR_RADAR_GREEN, unlit=True)
            if not parked:
                Entity(parent=self, model='sphere', position=(0, -0.12, 4.15), scale=0.28, color=config.rgb(255, 248, 215), unlit=True)

        self.anim_mode = "STATIC" if parked else "LANDING"
        self.speed = 26.0
        self.taxiing = False

    def update(self):
        if self.anim_mode == "LANDING":
            if not self.taxiing:
                self.x += self.speed * time.dt
                if self.y > -5.86:
                    self.y -= 2.5 * time.dt
                    self.rotation_z = -5
                else:
                    self.y = -5.86
                    self.rotation_z = 0
                    self.speed = max(5.5, self.speed - 3.6 * time.dt)
                    # Al llegar a la salida este de la pista, gira hacia la plataforma
                    if self.x >= 16.0 and self.speed <= 9.0:
                        self.taxiing = True
            else:
                self.rotation_y = lerp(self.rotation_y, 180, 2.2 * time.dt)
                self.z -= 5.5 * time.dt
                if self.z <= 28.0:
                    destroy(self)

        elif self.anim_mode == "FLYBY":
            self.x += 44.0 * time.dt
            if self.x > 95:
                destroy(self)


class TowerEnvironment(Entity):
    def __init__(self, sfx, on_trigger_victory, on_trigger_defeat):
        super().__init__(enabled=False)
        self.sfx = sfx
        self.on_trigger_victory = on_trigger_victory
        self.on_trigger_defeat = on_trigger_defeat

        window.color = config.rgb(10, 16, 28)
        scene.fog_color = config.rgb(15, 23, 38)
        scene.fog_density = 0.0065

        self.zone = "TOWER"
        self.current_level = 1
        self.camera_locked_to_radar = False
        self.yaw = 0.0
        self.pitch = -6.0
        self.raindrops = []
        self.runway_lights = []
        self.flares = []
        self.runway_light_mode = "NORMAL"  # NORMAL, OFF, EMERGENCY

        self.flicker_timer = 0.0
        self.shadow_timer = 0.0
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.lightning_timer = 11.0
        self.lightning_flash = 0.0
        self.active_aircraft = []
        self.radar_dish = None

        self.lvl2_stage = 0
        self.choice_modal_open = False

        self._build_lighting_and_sky()
        self._build_tower_cabin()
        self._build_exterior_airport()
        self._build_rain()
        self._build_exploration_hud()

    def _build_lighting_and_sky(self):
        self.moon_light = DirectionalLight(
            parent=self,
            color=config.rgb(155, 182, 225),
            rotation=(38, -28, 0),
            shadows=False
        )
        self.ambient_light = AmbientLight(
            parent=self,
            color=config.rgb(92, 108, 138)
        )

        self.sky_dome = Entity(
            parent=self,
            model='sphere',
            scale=420,
            color=config.rgb(12, 19, 34),
            double_sided=True,
            unlit=True
        )

        for _ in range(30):
            sx = random.uniform(-160, 160)
            sy = random.uniform(42, 115)
            sz = random.uniform(60, 180)
            Entity(
                parent=self,
                model='quad',
                position=(sx, sy, sz),
                rotation=(75, 0, 0),
                scale=random.uniform(0.35, 0.65),
                color=config.rgb(210, 228, 255, random.randint(130, 230)),
                unlit=True
            )

        Entity(
            parent=self,
            model='sphere',
            position=(58, 54, 165),
            scale=9.5,
            color=config.rgb(230, 240, 255),
            unlit=True
        )
        Entity(
            parent=self,
            model='sphere',
            position=(58, 54, 165),
            scale=19.0,
            color=config.rgb(135, 175, 235, 32),
            unlit=True
        )

        for i in range(28):
            angle = (i / 28.0) * 2 * math.pi
            dist = random.uniform(140, 170)
            mx = math.cos(angle) * dist
            mz = math.sin(angle) * dist + 35
            peak = random.uniform(28, 56)
            Entity(
                parent=self,
                model='cube',
                position=(mx, -14, mz),
                rotation=(random.uniform(-12, 12), random.uniform(0, 90), 45),
                scale=(peak, peak, peak * 0.75),
                color=config.rgb(20, 29, 46)
            )

        for _ in range(36):
            cx = random.uniform(-125, 125)
            cz = random.uniform(118, 138)
            Entity(
                parent=self,
                model='cube',
                position=(cx, -7.2 + random.uniform(0, 2.4), cz),
                scale=(random.uniform(0.7, 1.5), random.uniform(0.3, 0.7), 0.4),
                color=random.choice([config.rgb(255, 200, 110), config.rgb(160, 215, 255), config.rgb(255, 155, 90)]),
                unlit=True
            )

    def _build_tower_cabin(self):
        tex_metal = 'assets/textures/metal_panel.png'
        tex_rack = 'assets/textures/server_rack.png'
        tex_hazard = 'assets/textures/hazard_stripe.png'
        tex_radar = 'assets/textures/radar_grid.png'

        Entity(parent=self, model='cube', position=(0, 0, 0), scale=(8.0, 0.2, 6.4), texture=tex_metal, texture_scale=(4, 4), color=config.rgb(170, 180, 195))
        Entity(parent=self, model='cube', position=(0, 3.65, 0), scale=(8.0, 0.2, 6.4), texture=tex_metal, texture_scale=(3, 3), color=config.rgb(125, 135, 150))

        for lx in (-2.0, 2.0):
            Entity(parent=self, model='cube', position=(lx, 3.53, 0.4), scale=(0.4, 0.04, 2.8), color=config.rgb(175, 215, 245), unlit=True)

        Entity(parent=self, model='cube', position=(0, 1.8, -3.05), scale=(8.0, 3.6, 0.2), texture=tex_metal, texture_scale=(4, 2), color=config.rgb(155, 165, 180))
        Entity(parent=self, model='cube', position=(-3.9, 1.8, 0), scale=(0.2, 3.6, 6.4), texture=tex_metal, texture_scale=(3, 2), color=config.rgb(155, 165, 180))
        Entity(parent=self, model='cube', position=(3.9, 1.8, 0), scale=(0.2, 3.6, 6.4), texture=tex_metal, texture_scale=(3, 2), color=config.rgb(155, 165, 180))

        Entity(parent=self, model='cube', position=(-3.4, 1.45, -1.6), scale=(0.75, 2.7, 1.1), texture=tex_rack, unlit=True)
        Entity(parent=self, model='cube', position=(3.4, 1.45, -1.6), scale=(0.75, 2.7, 1.1), texture=tex_rack, unlit=True)

        self.tower_exit_door = Entity(
            parent=self,
            model='cube',
            position=(0, 1.2, -2.90),
            scale=(1.35, 2.35, 0.14),
            texture=tex_metal,
            color=config.rgb(95, 175, 210)
        )
        Entity(parent=self, model='cube', position=(0, 0.08, -2.85), scale=(1.5, 0.04, 0.35), texture=tex_hazard, unlit=True)
        Text(
            parent=self.tower_exit_door,
            text="SALIDA A PISTA [F]",
            position=(0, 0.35, -0.6),
            origin=(0, 0),
            scale=4.5,
            color=config.COLOR_CYAN_UI
        )

        Entity(parent=self, model='cube', position=(0, 0.48, 2.95), scale=(8.0, 0.96, 0.25), texture=tex_metal, texture_scale=(4, 1), color=config.rgb(145, 155, 170))
        for x_col in (-3.8, -1.6, 1.6, 3.8):
            Entity(parent=self, model='cube', position=(x_col, 2.3, 3.12), rotation=(-8, 0, 0), scale=(0.10, 2.65, 0.10), color=config.rgb(22, 28, 36))

        Entity(
            parent=self,
            model='quad',
            position=(0, 2.3, 3.1),
            rotation=(-8, 0, 0),
            scale=(7.7, 2.55),
            color=config.rgb(110, 170, 220, 12),
            double_sided=True
        )

        # Silueta paranormal que aparece tras el ventanal en Niveles 3 y 4
        self.window_shadow = Entity(parent=self, position=(0.8, 1.35, 3.55), enabled=False)
        Entity(parent=self.window_shadow, model='cube', position=(0, 0, 0), scale=(0.55, 1.55, 0.25), color=config.rgb(8, 10, 14))
        Entity(parent=self.window_shadow, model='sphere', position=(0, 0.92, 0), scale=0.34, color=config.rgb(8, 10, 14))
        Entity(parent=self.window_shadow, model='sphere', position=(-0.07, 0.94, -0.16), scale=0.045, color=config.COLOR_ALERT_RED, unlit=True)
        Entity(parent=self.window_shadow, model='sphere', position=(0.07, 0.94, -0.16), scale=0.045, color=config.COLOR_ALERT_RED, unlit=True)

        Entity(parent=self, model='cube', position=(0, 0.84, 2.15), scale=(4.6, 0.70, 0.94), texture=tex_metal, texture_scale=(3, 1), color=config.rgb(140, 150, 165))
        Entity(parent=self, model='cube', position=(0, 1.20, 1.68), scale=(4.62, 0.05, 0.06), texture=tex_hazard, unlit=True)

        # Monitor central (Radar)
        Entity(parent=self, model='cube', position=(0, 1.52, 2.28), rotation=(12, 0, 0), scale=(1.12, 0.74, 0.08), color=config.rgb(14, 20, 28))
        self.desk_radar_screen = Entity(
            parent=self,
            model='quad',
            position=(0, 1.52, 2.23),
            rotation=(12, 0, 0),
            scale=(0.98, 0.64),
            texture=tex_radar,
            unlit=True
        )

        # Panel izquierdo interactivo: Control de Luces de Pista [L / F]
        self.runway_control_panel = Entity(parent=self, model='cube', position=(-1.28, 1.46, 2.20), rotation=(10, 20, 0), scale=(0.82, 0.54, 0.08), color=config.rgb(14, 20, 28))
        self.runway_panel_screen = Entity(parent=self, model='quad', position=(-1.26, 1.46, 2.15), rotation=(10, 20, 0), scale=(0.74, 0.46), color=config.rgb(22, 95, 135), unlit=True)

        # Monitor derecho: Telemetría meteorológica
        Entity(parent=self, model='cube', position=(1.28, 1.46, 2.20), rotation=(10, -20, 0), scale=(0.82, 0.54, 0.08), color=config.rgb(14, 20, 28))
        Entity(parent=self, model='quad', position=(1.26, 1.46, 2.15), rotation=(10, -20, 0), scale=(0.74, 0.46), color=config.rgb(26, 118, 90), unlit=True)

        Entity(parent=self, model='cube', position=(0, 1.22, 1.92), scale=(0.55, 0.03, 0.22), color=config.rgb(32, 38, 46))
        Entity(parent=self, model='cube', position=(-0.55, 1.35, 1.98), rotation=(0, 0, -15), scale=(0.03, 0.32, 0.03), color=config.rgb(45, 52, 60))
        Entity(parent=self, model='cube', position=(-1.78, 1.22, 1.94), rotation=(0, 18, 0), scale=(0.35, 0.04, 0.26), color=config.rgb(210, 185, 110))
        Entity(parent=self, model='cube', position=(0.70, 1.26, 1.90), scale=(0.10, 0.13, 0.10), color=config.rgb(215, 220, 230))

        seat_loaded = False
        seat_path = 'assets/models/airliner_seat.glb'
        if is_valid_glb(seat_path):
            try:
                Entity(parent=self, model=seat_path, position=(1.65, 0.10, 1.15), rotation=(0, -145, 0), scale=1.15)
                seat_loaded = True
            except Exception:
                seat_loaded = False

        if not seat_loaded:
            Entity(parent=self, model='cube', position=(1.65, 0.52, 1.15), rotation=(0, -35, 0), scale=(0.55, 0.08, 0.55), color=config.rgb(30, 36, 44))
            Entity(parent=self, model='cube', position=(1.82, 0.92, 0.92), rotation=(-8, -35, 0), scale=(0.52, 0.72, 0.08), color=config.rgb(30, 36, 44))
            Entity(parent=self, model='cube', position=(1.65, 0.28, 1.15), scale=(0.08, 0.45, 0.08), color=config.rgb(65, 72, 82))

        self.cabin_light = PointLight(parent=self, position=(0, 3.2, 0.5), color=config.rgb(175, 210, 245))
        self.flashlight = PointLight(parent=camera, position=(0, 0, 0.4), color=config.rgb(235, 245, 255), enabled=False)
        self.flashlight_beam = Entity(parent=camera, enabled=False)

    def _build_floodlight_tower(self, x, z, rot_y=0):
        pole = Entity(parent=self, position=(x, -8.0, z), rotation=(0, rot_y, 0))
        Entity(parent=pole, model='cube', position=(0, 6.5, 0), scale=(0.30, 13.0, 0.30), color=config.rgb(95, 105, 120))
        Entity(parent=pole, model='cube', position=(0, 13.0, 0), scale=(2.8, 1.1, 0.4), color=config.rgb(45, 52, 62))
        for fx in (-0.9, 0.0, 0.9):
            Entity(parent=pole, model='quad', position=(fx, 13.0, -0.22), scale=(0.72, 0.72), color=config.rgb(240, 248, 255), unlit=True)
        Entity(parent=pole, model='quad', position=(0, 0.06, -4.5), rotation=(90, 0, 0), scale=(12, 12), color=config.rgb(185, 215, 250, 32), unlit=True)
        PointLight(parent=pole, position=(0, 11.5, -3.5), color=config.rgb(195, 218, 245))

    def _build_exterior_airport(self):
        tex_runway = 'assets/textures/asphalt_runway.png'
        tex_apron = 'assets/textures/apron_concrete.png'
        tex_metal = 'assets/textures/metal_panel.png'
        tex_hangar = 'assets/textures/corrugated_hangar.png'
        tex_terminal = 'assets/textures/terminal_windows.png'
        tex_hazard = 'assets/textures/hazard_stripe.png'
        tex_rack = 'assets/textures/server_rack.png'

        Entity(parent=self, model='plane', position=(0, -8, 45), scale=(320, 1, 320), color=config.rgb(18, 28, 32))

        Entity(parent=self, model='cube', position=(0, -4.0, 0), scale=(5.4, 8.0, 4.8), texture=tex_metal, texture_scale=(2, 3), color=config.rgb(165, 175, 190))
        self.exterior_tower_door = Entity(
            parent=self,
            model='cube',
            position=(0, -6.8, 2.48),
            scale=(1.6, 2.4, 0.16),
            texture=tex_metal,
            color=config.rgb(95, 175, 210)
        )

        Entity(
            parent=self,
            model='cube',
            position=(16, -7.97, 16),
            scale=(46, 0.06, 46),
            texture=tex_apron,
            texture_scale=(6, 6)
        )

        for tx in (-14, 16):
            Entity(
                parent=self,
                model='cube',
                position=(tx, -7.97, 39.5),
                scale=(7.5, 0.06, 6),
                texture=tex_apron,
                texture_scale=(1, 1)
            )
            for tz in (37.5, 40.0):
                for side in (-3.6, 3.6):
                    Entity(parent=self, model='sphere', position=(tx + side, -7.82, tz), scale=0.18, color=config.rgb(60, 165, 255), unlit=True)

        Entity(
            parent=self,
            model='cube',
            position=(0, -7.95, 49),
            rotation=(0, 90, 0),
            scale=(14, 0.08, 190),
            texture=tex_runway,
            texture_scale=(1, 7)
        )

        # Luces interactivas de balizamiento de la pista
        for x_pos in range(-88, 92, 12):
            for z_side in (42.4, 55.6):
                bulb = Entity(
                    parent=self,
                    model='sphere',
                    position=(x_pos, -7.76, z_side),
                    scale=0.30,
                    color=config.rgb(255, 215, 115),
                    unlit=True
                )
                self.runway_lights.append(bulb)

        # Caja eléctrica interactiva junto a la pista (permite cambiar luces o lanzar bengala afuera)
        self.runway_gen_box = Entity(
            parent=self,
            model='cube',
            position=(10.5, -7.35, 39.2),
            scale=(1.1, 1.2, 0.8),
            texture=tex_metal,
            color=config.rgb(195, 160, 60)
        )
        Entity(parent=self.runway_gen_box, model='sphere', position=(0, 0.72, 0), scale=0.22, color=config.COLOR_CYAN_UI, unlit=True)

        # Marca de quemadura anómala en el asfalto de la pista
        self.runway_scorch_mark = Entity(
            parent=self,
            model='quad',
            position=(-4.0, -7.89, 49.0),
            rotation=(90, 18, 0),
            scale=(4.5, 2.2),
            color=config.rgb(12, 10, 14, 210),
            unlit=True
        )

        for idx, p_col in enumerate([config.COLOR_ALERT_RED, config.COLOR_ALERT_RED, color.white, color.white]):
            Entity(
                parent=self,
                model='sphere',
                position=(-52, -7.72, 40.2 - idx * 0.7),
                scale=0.26,
                color=p_col,
                unlit=True
            )

        Entity(
            parent=self,
            model='cube',
            position=(39, -4.4, 14.5),
            scale=(10, 7.5, 42),
            texture=tex_terminal,
            texture_scale=(4, 1),
            color=config.rgb(215, 230, 250)
        )

        for gate_z in (2.0, 27.0):
            Entity(parent=self, model='cube', position=(31.5, -5.2, gate_z), scale=(5.8, 1.2, 1.3), texture=tex_metal, color=config.rgb(175, 185, 195))
            parked = Airplane3D(parent=self, is_ghost=False, parked=True, craft_scale=2.2)
            parked.position = (22.0, -5.86, gate_z)
            parked.rotation = (0, 90, 0)

        Entity(parent=self, model='cube', position=(-16, -6.2, 14), scale=(7, 3.6, 7), texture=tex_metal, color=config.rgb(155, 165, 180))
        Entity(parent=self, model='cube', position=(-16, -3.6, 14), scale=(0.45, 1.6, 0.45), color=config.rgb(120, 130, 145))
        self.radar_dish = Entity(
            parent=self,
            model='cube',
            position=(-16, -2.6, 14),
            scale=(3.6, 0.85, 0.25),
            color=config.rgb(215, 225, 235)
        )
        Entity(parent=self.radar_dish, model='sphere', position=(0, 0.65, 0), scale=(0.12, 0.55, 0.8), color=config.COLOR_ALERT_RED, unlit=True)

        trucks_loaded = False
        truck_path = 'assets/models/truck.glb'
        if is_valid_glb(truck_path):
            try:
                Entity(parent=self, model=truck_path, position=(14.5, -7.95, 14.5), rotation=(0, 75, 0), scale=0.52, color=config.rgb(175, 185, 195))
                Entity(parent=self, model=truck_path, position=(9.5, -7.95, 22.0), rotation=(0, -30, 0), scale=0.52, color=config.rgb(175, 185, 195))
                trucks_loaded = True
            except Exception:
                trucks_loaded = False

        if not trucks_loaded:
            for tx, tz, trot in [(14.5, 14.5, 75), (9.5, 22.0, -30)]:
                Entity(parent=self, model='cube', position=(tx, -7.45, tz), rotation=(0, trot, 0), scale=(1.2, 0.95, 2.8), color=config.rgb(200, 205, 215))
                Entity(parent=self, model='cube', position=(tx, -7.35, tz - 0.5), rotation=(0, trot, 0), scale=(1.25, 0.30, 1.6), texture=tex_hazard, unlit=True)

        self._build_floodlight_tower(33, 37, rot_y=155)
        self._build_floodlight_tower(-6, 28, rot_y=180)
        self._build_floodlight_tower(-26, 36, rot_y=-145)

        self.clue_beacon = Entity(
            parent=self,
            model='cube',
            position=(-11, -7.55, 26),
            scale=(1.15, 0.72, 1.15),
            texture=tex_hazard
        )
        self.beacon_light = Entity(
            parent=self.clue_beacon,
            model='sphere',
            position=(0, 0.75, 0),
            scale=0.35,
            color=config.COLOR_ALERT_RED,
            unlit=True
        )

        hx, hz = -18.0, 74.0
        Entity(parent=self, model='cube', position=(hx - 7.0, -5.0, hz), scale=(0.5, 6.0, 20), texture=tex_hangar, texture_scale=(4, 2))
        Entity(parent=self, model='cube', position=(hx + 7.0, -5.0, hz), scale=(0.5, 6.0, 20), texture=tex_hangar, texture_scale=(4, 2))
        Entity(parent=self, model='cube', position=(hx, -5.0, hz + 9.8), scale=(14.5, 6.0, 0.5), texture=tex_hangar, texture_scale=(3, 2))
        Entity(parent=self, model='cube', position=(hx, -1.9, hz), scale=(14.8, 0.45, 20.4), texture=tex_hangar, texture_scale=(3, 4))
        Entity(parent=self, model='cube', position=(hx - 5.2, -5.0, hz - 9.8), scale=(3.6, 6.0, 0.4), texture=tex_hazard)
        Entity(parent=self, model='cube', position=(hx + 5.2, -5.0, hz - 9.8), scale=(3.6, 6.0, 0.4), texture=tex_hazard)

        self.hangar_beacon = Entity(
            parent=self,
            model='sphere',
            position=(hx, -1.5, hz - 9.8),
            scale=0.55,
            color=config.COLOR_ALERT_RED,
            unlit=True
        )
        PointLight(parent=self, position=(hx, -3.5, hz), color=config.rgb(235, 55, 55))

        anomalous_craft = Airplane3D(parent=self, is_ghost=True, parked=True, craft_scale=1.7)
        anomalous_craft.position = (hx, -6.3, hz + 2.5)
        anomalous_craft.rotation = (6, 155, -14)

        self.clue_blackbox = Entity(
            parent=self,
            model='cube',
            position=(hx + 2.5, -7.45, hz - 4.5),
            rotation=(0, 28, 8),
            scale=(1.4, 0.9, 1.1),
            texture=tex_hazard
        )

        self.clue_terminal = Entity(
            parent=self,
            model='cube',
            position=(hx - 3.2, -7.0, hz - 3.0),
            rotation=(0, -35, 0),
            scale=(1.25, 1.85, 0.85),
            texture=tex_rack,
            unlit=True
        )

    def _build_rain(self):
        for _ in range(50):
            drop = Entity(
                parent=self,
                model='cube',
                position=(random.uniform(-38, 38), random.uniform(-7.5, 14), random.uniform(4, 75)),
                scale=(0.018, 0.58, 0.018),
                color=config.rgb(175, 205, 240, 75),
                unlit=True
            )
            self.raindrops.append(drop)

    def _build_exploration_hud(self):
        self.interact_prompt = Text(
            parent=camera.ui,
            text="",
            position=(0, -0.22),
            origin=(0, 0),
            scale=1.1,
            color=config.COLOR_CYAN_UI,
            enabled=False
        )

        self.field_log = Text(
            parent=camera.ui,
            text="",
            position=(-0.85, 0.38),
            scale=0.86,
            color=config.COLOR_AMBER_UI,
            enabled=False
        )

        self.hangar_modal = Entity(parent=camera.ui, enabled=False)
        Entity(parent=self.hangar_modal, model='quad', scale=(1.28, 0.64), color=config.COLOR_PANEL, z=1)
        Text(
            parent=self.hangar_modal,
            text="TRANSMISOR DEL HANGAR OESTE - SEÑAL ACTIVA (1986 -> 2026)",
            position=(0, 0.22),
            origin=(0, 0),
            scale=1.12,
            color=config.COLOR_ALERT_RED
        )
        Text(
            parent=self.hangar_modal,
            text=(
                "La caja negra confirma que el vuelo ???-000 desapareció en una tormenta hace 40 años.\n"
                "El transmisor está rebotando su llamada de auxilio hacia nuestro radar.\n\n"
                "¿Qué orden ejecutarás como controlador de turno?"
            ),
            position=(0, 0.06),
            origin=(0, 0),
            scale=0.92,
            line_height=1.35,
            color=config.COLOR_TEXT_MAIN
        )

        b_opt1 = Button(
            parent=self.hangar_modal,
            text="OPCIÓN A: AISLAR Y SELLAR LA FRECUENCIA (CONTENER ANOMALÍA)",
            position=(0, -0.12),
            scale=(0.98, 0.058),
            color=config.rgb(16, 48, 36),
            text_color=config.COLOR_RADAR_GREEN
        )
        b_opt1.on_click = lambda: self._resolve_hangar_decision("CONTAIN")

        b_opt2 = Button(
            parent=self.hangar_modal,
            text="OPCIÓN B: ENVIAR SEÑAL DE RETORNO AL VUELO ???-000",
            position=(0, -0.20),
            scale=(0.98, 0.058),
            color=config.rgb(55, 22, 26),
            text_color=config.COLOR_AMBER_UI
        )
        b_opt2.on_click = lambda: self._resolve_hangar_decision("ANSWER")

    def cycle_runway_lights(self):
        """Alterna las luces de la pista entre NORMAL, OFF y EMERGENCY."""
        if not self.enabled:
            return
        modes = ["NORMAL", "OFF", "EMERGENCY"]
        idx = (modes.index(self.runway_light_mode) + 1) % len(modes)
        self.runway_light_mode = modes[idx]

        if self.sfx:
            self.sfx.play("ui_click")

        if self.runway_light_mode == "NORMAL":
            self.runway_panel_screen.color = config.rgb(22, 95, 135)
            msg = "[PISTA 09/27]: Luces de aproximación ENCENDIDAS (Operación normal)."
        elif self.runway_light_mode == "OFF":
            self.runway_panel_screen.color = config.rgb(24, 28, 36)
            msg = "[PISTA 09/27]: Luces APAGADAS (Modo oscurecimiento táctico)."
        else:
            self.runway_panel_screen.color = config.COLOR_ALERT_RED
            if self.sfx:
                self.sfx.play("alarm_anomaly")
            msg = "[PISTA 09/27]: ¡BALIZAS EN MODO EMERGENCIA ROJO!"

        self.field_log.enabled = True
        self.field_log.text = msg

    def launch_runway_flare(self):
        """Dispara una bengala iluminadora sobre la pista desde el exterior."""
        if self.sfx:
            self.sfx.play("thunder")
        flare = Entity(
            parent=self,
            model='sphere',
            position=(10.5, -6.5, 42.0),
            scale=0.45,
            color=config.COLOR_ALERT_RED,
            unlit=True
        )
        PointLight(parent=flare, position=(0, 0, 0), color=config.rgb(255, 70, 70))
        self.flares.append(flare)
        self.field_log.enabled = True
        self.field_log.text = "[PISTA]: Bengala de emergencia disparada sobre el umbral de la Pista 09/27."

    def spawn_window_shadow(self, duration=2.2):
        """Hace aparecer una sombra inquietante tras el vidrio de la torre."""
        self.window_shadow.x = random.choice([-1.9, -0.7, 0.9, 2.1])
        self.window_shadow.enabled = True
        self.shadow_timer = duration
        if self.sfx:
            self.sfx.play("radio_static")

    def trigger_camera_shake(self, intensity=0.05, duration=0.8):
        self.shake_intensity = intensity
        self.shake_timer = duration

    def spawn_landing_aircraft(self):
        plane = Airplane3D(parent=self, is_ghost=False, parked=False, craft_scale=2.45)
        plane.anim_mode = "LANDING"
        plane.position = (-92, 6.5, 49)
        plane.rotation = (0, 90, -5)
        self.active_aircraft.append(plane)

    def spawn_ghost_flyby(self):
        ghost = Airplane3D(parent=self, is_ghost=True, parked=False, craft_scale=2.2)
        ghost.anim_mode = "FLYBY"
        ghost.position = (-80, 3.8, 22)
        ghost.rotation = (0, 90, -16)
        self.active_aircraft.append(ghost)
        self.trigger_camera_shake(0.06, 1.1)

    def _clear_aircraft(self):
        for p in self.active_aircraft:
            if p:
                destroy(p)
        self.active_aircraft.clear()

    def apply_visual_settings(self):
        b = config.settings["brightness"]
        scene.fog_density = clamp(0.0065 / b, 0.003, 0.015)
        self.ambient_light.color = config.rgb(
            min(255, int(92 * b)),
            min(255, int(108 * b)),
            min(255, int(138 * b))
        )
        self.moon_light.color = config.rgb(
            min(255, int(155 * b)),
            min(255, int(182 * b)),
            min(255, int(225 * b))
        )
        self.cabin_light.color = config.rgb(
            min(255, int(175 * b)),
            min(255, int(210 * b)),
            min(255, int(245 * b))
        )

    def activate_scene(self, level_num=1):
        self.enabled = True
        self.current_level = level_num
        self.lvl2_stage = 0
        self.runway_light_mode = "NORMAL"
        self.runway_panel_screen.color = config.rgb(22, 95, 135)
        self.window_shadow.enabled = False
        self.shadow_timer = 0.0
        self.shake_timer = 0.0
        self.choice_modal_open = False
        self.hangar_modal.enabled = False
        self.field_log.enabled = False
        self.interact_prompt.enabled = False
        self._clear_aircraft()
        self.apply_visual_settings()
        self.enter_tower()

    def enter_tower(self):
        self.zone = "TOWER"
        self.flashlight.enabled = False
        self.flashlight_beam.enabled = False
        camera.position = (0, 1.85, 0.4)
        self.yaw = 0.0
        self.pitch = -6.0
        camera.rotation = (self.pitch, self.yaw, 0)
        self.set_radar_focus(False)

    def exit_to_airport(self):
        self.zone = "EXTERIOR"
        self.camera_locked_to_radar = False
        self.flashlight.enabled = True
        self.flashlight_beam.enabled = True
        mouse.locked = True
        mouse.visible = False
        camera.position = (0, -6.2, 6.0)
        self.yaw = 0.0
        self.pitch = -4.0
        camera.rotation = (self.pitch, self.yaw, 0)
        self.field_log.enabled = True
        self.field_log.text = "[EXTERIOR]: Estás en la plataforma.\nExplora la pista, la caja eléctrica o la baliza ECO-77."
        if self.sfx:
            self.sfx.play("thunder")

    def set_radar_focus(self, focused: bool):
        if self.zone != "TOWER":
            return
        self.camera_locked_to_radar = focused
        mouse.locked = not focused
        mouse.visible = focused
        if focused:
            camera.animate_position((0, 1.62, 1.32), duration=0.25)
            camera.animate_rotation((8, 0, 0), duration=0.25)

    def trigger_power_flicker(self, duration=2.2):
        self.flicker_timer = duration
        if self.sfx:
            self.sfx.play("alarm_anomaly")

    def interact(self):
        if not self.enabled or self.camera_locked_to_radar or self.choice_modal_open:
            return

        if self.zone == "TOWER":
            if distance(camera.position, self.tower_exit_door.position) < 2.6:
                if self.current_level == 1:
                    self.field_log.enabled = True
                    self.field_log.text = "[PROTOCOLO]: No puedes abandonar la torre durante el Nivel 1."
                else:
                    self.exit_to_airport()
            elif distance(camera.position, self.runway_control_panel.position) < 2.3:
                self.cycle_runway_lights()

        elif self.zone == "EXTERIOR":
            if distance(camera.position, self.exterior_tower_door.position) < 3.4:
                self.enter_tower()
                self.field_log.enabled = False
                return

            if distance(camera.position, self.runway_gen_box.position) < 3.6:
                self.cycle_runway_lights()
                self.launch_runway_flare()
            elif distance(camera.position, self.runway_scorch_mark.position) < 5.0:
                if self.sfx:
                    self.sfx.play("radio_static")
                self.field_log.enabled = True
                self.field_log.text = (
                    "[PISTA 09/27 - HUELLA TÉRMICA]: Marcas de aterrizaje vitrificadas en el asfalto.\n"
                    "El acero está frío al tacto, pero emite interferencia en 118.1 MHz."
                )
            elif distance(camera.position, self.clue_beacon.position) < 4.2:
                if self.sfx:
                    self.sfx.play("radio_static")
                self.lvl2_stage = max(self.lvl2_stage, 1)
                self.field_log.enabled = True
                self.field_log.text = (
                    "[PISTA 1/3 - BALIZA ECO-77]: \"La señal no viene del cielo...\n"
                    "cruza la pista hacia el Hangar Oeste (luz roja al fondo).\""
                )
            elif distance(camera.position, self.clue_blackbox.position) < 4.5:
                if self.sfx:
                    self.sfx.play("radio_static")
                self.lvl2_stage = max(self.lvl2_stage, 2)
                self.field_log.enabled = True
                self.field_log.text = (
                    "[PISTA 2/3 - CAJA NEGRA 1986]: Registro intacto del vuelo ???-000.\n"
                    "Opera el terminal iluminado dentro del hangar."
                )
            elif distance(camera.position, self.clue_terminal.position) < 4.5:
                if self.sfx:
                    self.sfx.play("alarm_anomaly")
                self.choice_modal_open = True
                mouse.locked = False
                mouse.visible = True
                self.hangar_modal.enabled = True

    def _resolve_hangar_decision(self, choice):
        self.choice_modal_open = False
        self.hangar_modal.enabled = False
        self.interact_prompt.enabled = False
        self.field_log.enabled = False
        self.enabled = False
        mouse.locked = False
        mouse.visible = True

        if choice == "CONTAIN":
            self.on_trigger_victory(
                "NIVEL 2 COMPLETADO: FRECUENCIA SELLADA",
                "Aislaste el transmisor del Hangar Oeste y detuviste la interferencia en el espacio aéreo.\n"
                "El aeropuerto vuelve a operar con normalidad, aunque el misterio de 1986 sigue vivo.\n\n"
                "Prepárate para el Nivel 3: Frecuencia Fantasma.",
                True
            )
        else:
            self.on_trigger_victory(
                "NIVEL 2 COMPLETADO: CONTACTO ESTABLECIDO",
                "Enviaste una señal de retorno hacia ???-000. En el radar apareció una respuesta:\n"
                "\"GRACIAS TORRE... YA VEMOS LAS LUCES DE LA PISTA.\"\n\n"
                "Prepárate para el Nivel 3: Frecuencia Fantasma.",
                True
            )

    def hide_overlays(self):
        self.interact_prompt.enabled = False
        self.field_log.enabled = False
        self.hangar_modal.enabled = False

    def update(self):
        if not self.enabled:
            return

        dt = time.dt

        if self.radar_dish:
            self.radar_dish.rotation_y += 38 * dt

        for drop in self.raindrops:
            drop.y -= 21 * dt
            if drop.y < -7.8:
                drop.y = random.uniform(10, 15)

        # Actualizar bengalas lanzadas en pista
        for fl in list(self.flares):
            fl.y += 14.0 * dt
            if fl.y > 38.0:
                self.flares.remove(fl)
                destroy(fl)

        # Actualizar luces dinámicas de la pista 09/27
        has_landing = any(p and p.anim_mode == "LANDING" for p in self.active_aircraft)
        chase_idx = int(time.time() * 14) % max(1, len(self.runway_lights))
        for idx, bulb in enumerate(self.runway_lights):
            if self.runway_light_mode == "OFF":
                bulb.color = config.rgb(28, 32, 40)
            elif self.runway_light_mode == "EMERGENCY":
                blink = int(time.time() * 6) % 2 == 0
                bulb.color = config.COLOR_ALERT_RED if blink else config.rgb(75, 14, 18)
            else:
                if has_landing and abs(idx - chase_idx) <= 2:
                    bulb.color = color.white
                else:
                    bulb.color = config.rgb(255, 215, 115)

        self.lightning_timer -= dt
        if self.lightning_timer <= 0:
            self.lightning_timer = random.uniform(12.0, 20.0)
            self.lightning_flash = 0.22
            if self.sfx:
                self.sfx.play("thunder")

        if self.lightning_flash > 0:
            self.lightning_flash -= dt
            scene.fog_color = config.rgb(65, 82, 115)
            self.sky_dome.color = config.rgb(48, 65, 96)
        else:
            scene.fog_color = config.rgb(15, 23, 38)
            self.sky_dome.color = config.rgb(12, 19, 34)

        pulse = (math.sin(time.time() * 4.5) + 1) * 0.5
        self.hangar_beacon.color = config.rgb(235, 45, 45, int(110 + pulse * 145))
        self.beacon_light.color = config.rgb(245, 165, 40, int(110 + pulse * 145))

        # Sombra tras el ventanal
        if self.shadow_timer > 0:
            self.shadow_timer -= dt
            if self.shadow_timer <= 0:
                self.window_shadow.enabled = False

        # Apagones / luces rojas de emergencia en la torre
        if self.flicker_timer > 0:
            self.flicker_timer -= dt
            is_on = random.random() > 0.45
            if self.current_level >= 3:
                self.cabin_light.color = config.rgb(220, 32, 38) if is_on else config.rgb(18, 12, 16)
            else:
                self.cabin_light.color = config.rgb(175, 210, 245) if is_on else config.rgb(18, 24, 32)
            self.desk_radar_screen.color = color.white if is_on else config.COLOR_ALERT_RED
        else:
            self.apply_visual_settings()
            self.desk_radar_screen.color = color.white

        # Temblor de cámara durante eventos de terror
        if self.shake_timer > 0:
            self.shake_timer -= dt
            camera.rotation_z = random.uniform(-self.shake_intensity, self.shake_intensity) * 35.0
        else:
            camera.rotation_z = 0.0

        if self.camera_locked_to_radar or self.choice_modal_open:
            self.interact_prompt.enabled = False
            return

        sens = config.settings["sensitivity"]
        self.yaw += mouse.velocity[0] * sens
        self.pitch -= mouse.velocity[1] * sens
        self.pitch = clamp(self.pitch, -50, 50)
        camera.rotation_x = self.pitch
        camera.rotation_y = self.yaw

        forward = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
        right = Vec3(camera.right.x, 0, camera.right.z).normalized()

        if self.zone == "TOWER":
            move_speed = 3.2 * dt
            next_pos = camera.position
            if held_keys['w']:
                next_pos += forward * move_speed
            if held_keys['s']:
                next_pos -= forward * move_speed
            if held_keys['d']:
                next_pos += right * move_speed
            if held_keys['a']:
                next_pos -= right * move_speed

            camera.x = clamp(next_pos.x, -config.CABIN_LIMIT_X, config.CABIN_LIMIT_X)
            camera.z = clamp(next_pos.z, -config.CABIN_LIMIT_Z, 1.35)

            if distance(camera.position, self.tower_exit_door.position) < 2.6:
                self.interact_prompt.text = "[F] Bajar a la plataforma del aeropuerto"
                self.interact_prompt.enabled = True
            elif distance(camera.position, self.runway_control_panel.position) < 2.3:
                self.interact_prompt.text = f"[F / L] Cambiar luces de pista (Actual: {self.runway_light_mode})"
                self.interact_prompt.enabled = True
            else:
                self.interact_prompt.enabled = False

        elif self.zone == "EXTERIOR":
            move_speed = 7.0 * dt
            next_pos = camera.position
            if held_keys['w']:
                next_pos += forward * move_speed
            if held_keys['s']:
                next_pos -= forward * move_speed
            if held_keys['d']:
                next_pos += right * move_speed
            if held_keys['a']:
                next_pos -= right * move_speed

            camera.x = clamp(next_pos.x, -30.0, 26.0)
            camera.z = clamp(next_pos.z, 4.5, 80.0)
            camera.y = -6.2

            if distance(camera.position, self.exterior_tower_door.position) < 3.4:
                self.interact_prompt.text = "[F] Subir a la Torre de Control"
                self.interact_prompt.enabled = True
            elif distance(camera.position, self.runway_gen_box.position) < 3.6:
                self.interact_prompt.text = "[F] Alternar circuito de pista y lanzar bengala"
                self.interact_prompt.enabled = True
            elif distance(camera.position, self.runway_scorch_mark.position) < 5.0:
                self.interact_prompt.text = "[F] Inspeccionar huella térmica en la Pista 09/27"
                self.interact_prompt.enabled = True
            elif distance(camera.position, self.clue_beacon.position) < 4.2:
                self.interact_prompt.text = "[F] Inspeccionar baliza de emergencia ECO-77"
                self.interact_prompt.enabled = True
            elif distance(camera.position, self.clue_blackbox.position) < 4.5:
                self.interact_prompt.text = "[F] Examinar Caja Negra (1986) dentro del hangar"
                self.interact_prompt.enabled = True
            elif distance(camera.position, self.clue_terminal.position) < 4.5:
                self.interact_prompt.text = "[F] Operar terminal transmisor del Hangar Oeste"
                self.interact_prompt.enabled = True
            else:
                self.interact_prompt.enabled = False