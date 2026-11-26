from ursina import *
import textwrap
import random
import math
import config


class RadarConsole(Entity):
    def __init__(self, tower_env, sfx, on_level_complete, on_level_defeat):
        super().__init__(parent=camera.ui, enabled=False)
        self.tower_env = tower_env
        self.sfx = sfx
        self.on_level_complete = on_level_complete
        self.on_level_defeat = on_level_defeat

        self.current_level = 1
        self.selected_flight_id = None
        self.flights = {}
        self.resolved_count = 0
        self.sweep_angle_accum = 0.0

        self.runway_busy_timer = 0.0
        self.glitch_timer = 0.0
        self.pending_event_timer = 0.0
        self.pending_event_name = None
        self.early_scare_done = False
        self.mid_scare_done = False
        self.level_elapsed = 0.0
        self.shift_seconds = 15 * 60

        self.hud_top = Entity(parent=self)
        self.objective_text = Text(
            parent=self.hud_top,
            text="OBJETIVO: Presiona [E] para operar el radar de control aéreo.",
            position=(-0.85, 0.46),
            scale=0.92,
            color=config.COLOR_RADAR_GREEN
        )
        self.hint_text = Text(
            parent=self.hud_top,
            text="[E / TAB] Radar   |   [L] Luces Pista   |   [WASD] Moverse   |   [F] Interactuar   |   [ESC] Pausa",
            position=(-0.85, -0.46),
            scale=0.80,
            color=config.COLOR_TEXT_MUTED
        )

        self.screen_overlay = Entity(parent=self, enabled=False)
        self._build_radar_ui()

    def _wrap(self, msg, width=46):
        return "\n".join(textwrap.fill(line, width=width) for line in msg.split("\n"))

    def _build_radar_ui(self):
        Entity(
            parent=self.screen_overlay,
            model='quad',
            scale=(1.62, 0.86),
            color=config.COLOR_PANEL,
            z=1
        )

        self.radar_center = Entity(parent=self.screen_overlay, position=(-0.36, 0.01))
        Entity(
            parent=self.radar_center,
            model=Circle(64),
            scale=0.66,
            texture='assets/textures/radar_grid.png',
            z=0.5
        )

        self.glitch_overlay = Entity(
            parent=self.radar_center,
            model=Circle(48),
            scale=0.66,
            color=config.rgb(220, 25, 35, 0),
            z=-0.2,
            enabled=False
        )

        self.selection_ring = Entity(
            parent=self.radar_center,
            model=Circle(32, mode='line', thickness=2),
            scale=0.056,
            color=config.COLOR_CYAN_UI,
            z=-0.15,
            enabled=False
        )

        self.sweep_pivot = Entity(parent=self.radar_center, z=-0.1)
        Entity(
            parent=self.sweep_pivot,
            model='quad',
            position=(0, 0.162),
            scale=(0.007, 0.325),
            color=config.COLOR_RADAR_GREEN
        )
        Entity(
            parent=self.sweep_pivot,
            model='quad',
            position=(-0.036, 0.158),
            rotation=(0, 0, -12),
            scale=(0.078, 0.315),
            color=config.rgb(40, 230, 120, 42)
        )

        self.blips_layer = Entity(parent=self.radar_center, z=-0.05)

        self.info_panel = Entity(parent=self.screen_overlay, position=(0.36, 0.02))

        self.clock_header = Text(
            parent=self.info_panel,
            text="TORRE NORTE  |  02:15:00 AM  |  118.1 MHz",
            position=(-0.33, 0.36),
            scale=0.88,
            color=config.COLOR_CYAN_UI
        )

        self.runway_status_text = Text(
            parent=self.info_panel,
            text="PISTA 09/27: DESPEJADA  |  LUCES: NORMAL",
            position=(-0.33, 0.31),
            scale=0.80,
            color=config.COLOR_RADAR_GREEN
        )

        self.telemetry_text = Text(
            parent=self.info_panel,
            text="Haz clic sobre un eco luminoso en el radar para inspeccionar...",
            position=(-0.33, 0.23),
            scale=0.83,
            line_height=1.32,
            color=config.COLOR_TEXT_MAIN
        )

        Text(
            parent=self.info_panel,
            text="CANAL DE COMUNICACIONES:",
            position=(-0.33, -0.02),
            scale=0.84,
            color=config.COLOR_RADAR_GREEN
        )

        self.radio_log = Text(
            parent=self.info_panel,
            text="[SISTEMA]: Escaneo nocturno activo. Clima: Tormenta eléctrica.",
            position=(-0.33, -0.075),
            scale=0.79,
            line_height=1.26,
            color=config.COLOR_TEXT_MUTED
        )

        self.action_btn_1 = Button(
            parent=self.info_panel,
            text="",
            position=(0, -0.25),
            scale=(0.65, 0.052),
            color=config.rgb(18, 46, 36),
            text_color=config.COLOR_RADAR_GREEN,
            enabled=False
        )
        self.action_btn_2 = Button(
            parent=self.info_panel,
            text="",
            position=(0, -0.32),
            scale=(0.65, 0.052),
            color=config.rgb(55, 20, 24),
            text_color=config.COLOR_ALERT_RED,
            enabled=False
        )

    def _schedule_event(self, event_name, delay):
        self.pending_event_name = event_name
        self.pending_event_timer = delay

    def start_level(self, level_num: int):
        self.enabled = True
        self.current_level = level_num
        self.selected_flight_id = None
        self.resolved_count = 0
        self.runway_busy_timer = 0.0
        self.glitch_timer = 0.0
        self.pending_event_name = None
        self.pending_event_timer = 0.0
        self.early_scare_done = False
        self.mid_scare_done = False
        self.level_elapsed = 0.0
        self.shift_seconds = (2 + level_num - 1) * 3600 + 15 * 60
        self.screen_overlay.enabled = False
        self.selection_ring.enabled = False
        self._clear_blips()

        if level_num == 1:
            self.objective_text.text = "NIVEL 1 - EL PRIMER CONTACTO: Gestiona los vuelos nocturnos en el radar [E]."
            self.objective_text.color = config.COLOR_RADAR_GREEN
            self.radio_log.text = self._wrap("[TORRE]: Turno 02:15 AM iniciado. Dos aeronaves activas en el sector.")

            self._spawn_flight(
                fid="AVA-402",
                pos=(-0.22, 0.16),
                vel=(0.011, -0.008),
                is_anomaly=False,
                altitude=11500,
                speed_kts=235,
                fuel_sec=95.0,
                registry="REGISTRADO - AEROLÍNEA COMERCIAL",
                radio_msg="\"Torre, aquí AVA-402 en aproximación final. Solicitamos Pista 09/27.\"",
                btn1_label="AUTORIZAR ATERRIZAJE EN PISTA 09/27",
                btn1_reply="\"Copiado Torre, descendiendo a pista. ¡Mira por el ventanal!\"",
                lands_on_runway=True
            )
            self._spawn_flight(
                fid="LAN-819",
                pos=(0.20, -0.15),
                vel=(-0.009, 0.008),
                is_anomaly=False,
                altitude=18000,
                speed_kts=310,
                fuel_sec=110.0,
                registry="REGISTRADO - VUELO DE CARGA",
                radio_msg="\"Torre, LAN-819 reporta rayos al sureste. Solicitamos vector de desvío.\"",
                btn1_label="ASIGNAR VECTOR NORTE Y MANTENER NIVEL 180",
                btn1_reply="\"Recibido Torre, virando al norte fuera de la celda eléctrica.\"",
                lands_on_runway=False
            )

        elif level_num == 2:
            self.tower_env.trigger_power_flicker(duration=2.4)
            self.glitch_timer = 1.6
            self.objective_text.text = "NIVEL 2 - SEÑAL PERDIDA: Revisa radar [E] y baja por la puerta trasera [F] al Hangar Oeste."
            self.objective_text.color = config.COLOR_AMBER_UI
            self.radio_log.text = self._wrap("[ALERTA]: ECO-77 cayó fuera de línea tras un apagón. Se detectan ecos parásitos.")

            self._spawn_flight(
                fid="ECO-77",
                pos=(-0.21, 0.19),
                vel=(0.0, 0.0),
                is_anomaly=True,
                altitude=0,
                speed_kts=0,
                fuel_sec=999.0,
                registry="ÚLTIMA POSICIÓN: HANGAR OESTE",
                radio_msg="\"...interferencia en pista... hay una aeronave sin matrícula dentro del Hangar Oeste...\"",
                btn1_label="MARCAR BALIZA Y SALIR DE LA TORRE [CERRAR RADAR]",
                btn1_reply="[SISTEMA]: Ruta marcada. Camina a la puerta trasera de la torre y presiona [F]."
            )
            self._spawn_flight(
                fid="ECO-FANTASMA",
                pos=(0.14, 0.20),
                vel=(-0.015, -0.012),
                is_anomaly=True,
                is_phantom_decoy=True,
                altitude=400,
                speed_kts=640,
                fuel_sec=999.0,
                registry="ERROR DE TRANSPONDEDOR - ECO REBOTADO",
                radio_msg="\"...02:15... 1986... no bajen al hangar...\"",
                btn1_label="PURGAR INTERFERENCIA DEL RADAR",
                btn1_reply="[SISTEMA]: El eco se desvaneció, pero la señal base sigue activa en el Hangar Oeste."
            )

        elif level_num == 3:
            self.tower_env.trigger_power_flicker(duration=2.2)
            self.tower_env.spawn_window_shadow(2.4)
            self.objective_text.text = "NIVEL 3 - FRECUENCIA FANTASMA: Separa los vuelos reales de los ecos falsos."
            self.objective_text.color = config.COLOR_AMBER_UI
            self.radio_log.text = self._wrap("[ALERTA CRÍTICA]: Suplantación de identidad en 118.1 MHz. Verifica la base de datos.")

            self._spawn_flight(
                fid="COP-214",
                pos=(-0.24, -0.10),
                vel=(0.013, 0.006),
                is_anomaly=False,
                altitude=9500,
                speed_kts=250,
                fuel_sec=85.0,
                registry="REGISTRADO - VUELO INTERNACIONAL",
                radio_msg="\"Torre, COP-214 con combustible limitado. Solicitamos aterrizaje prioritario.\"",
                btn1_label="AUTORIZAR ATERRIZAJE PRIORITARIO",
                btn1_reply="\"Gracias Torre, en final corta. Luz de pista a la vista.\"",
                lands_on_runway=True
            )
            self._spawn_flight(
                fid="AER-509",
                pos=(0.23, 0.14),
                vel=(-0.012, -0.007),
                is_anomaly=False,
                altitude=10200,
                speed_kts=265,
                fuel_sec=95.0,
                registry="REGISTRADO - PUENTE AÉREO",
                radio_msg="\"Torre, AER-509 en espera sobre sector este. ¿Procedemos o mantenemos patrón?\"",
                btn1_label="MANTENER PATRÓN DE ESPERA (PISTA OCUPADA)",
                btn1_reply="\"Copiado Torre, orbitando a 10,000 pies hasta nuevo aviso.\"",
                lands_on_runway=False
            )
            self._spawn_flight(
                fid="COP-214?",
                pos=(0.02, 0.24),
                vel=(-0.006, -0.018),
                is_anomaly=True,
                altitude=39000,
                speed_kts=1120,
                fuel_sec=999.0,
                registry="ALERTA: MATRÍCULA CLONADA (1986)",
                radio_msg="\"...Somos nosotros... COP-214... déjennos bajar ahora...\"",
                btn1_label="BLOQUEAR FRECUENCIA CLONADA",
                btn1_reply="[SISTEMA]: Canal clonado bloqueado. Una sombra cruzó frente al ventanal.",
                btn2_label="CONCEDER PISTA AL CONTACTO CLONADO",
                btn2_danger=True
            )

        else:
            self.tower_env.trigger_power_flicker(duration=3.5)
            self.tower_env.spawn_window_shadow(2.8)
            self.tower_env.spawn_ghost_flyby()
            self.glitch_timer = 2.5
            self.objective_text.text = "NIVEL 4 - BLACK RADAR: Contén la incursión final antes de que alcancen la torre."
            self.objective_text.color = config.COLOR_ALERT_RED
            self.radio_log.text = self._wrap("[EMERGENCIA TOTAL]: Múltiples ecos de 1986 convergentes hacia Torre Norte.")

            self._spawn_flight(
                fid="???-000",
                pos=(-0.22, 0.20),
                vel=(0.011, -0.010),
                is_anomaly=True,
                altitude=1500,
                speed_kts=890,
                fuel_sec=70.0,
                registry="ORIGEN: DESCONOCIDO (04-NOV-1986)",
                radio_msg="\"...Ya estamos sobre el techo de la torre... abre las compuertas...\"",
                btn1_label="ACTIVAR CONTRA-SEÑAL DE AISLAMIENTO",
                btn1_reply="[SISTEMA]: Pulso de aislamiento enviado. La frecuencia empieza a colapsar.",
                btn2_label="ENCENDER LUCES DE PISTA PARA ???-000",
                btn2_danger=True
            )
            self._spawn_flight(
                fid="VUELO-86",
                pos=(0.22, -0.18),
                vel=(-0.011, 0.009),
                is_anomaly=True,
                altitude=900,
                speed_kts=940,
                fuel_sec=75.0,
                registry="ECO FANTASMA - SIN FUSELAJE",
                radio_msg="\"...Nunca salimos de la tormenta...\"",
                btn1_label="CERRAR PROTOCOLO BLACK RADAR (SELLAR TORRE)",
                btn1_reply="[SISTEMA]: Compuertas electromagnéticas selladas. Silencio en 118.1 MHz.",
                btn2_label="ABANDONAR CONSOLA",
                btn2_danger=True
            )

    def _clear_blips(self):
        for child in list(self.blips_layer.children):
            destroy(child)
        self.flights.clear()
        self.action_btn_1.enabled = False
        self.action_btn_2.enabled = False
        self.selection_ring.enabled = False

    def _spawn_flight(self, fid, pos, vel, is_anomaly, altitude, speed_kts, fuel_sec,
                      registry, radio_msg, btn1_label, btn1_reply,
                      btn2_label=None, btn2_danger=False, lands_on_runway=False, is_phantom_decoy=False):
        blip_color = config.COLOR_ALERT_RED if is_anomaly else config.COLOR_RADAR_GREEN
        blip_btn = Button(
            parent=self.blips_layer,
            model=Circle(24),
            position=pos,
            scale=0.032,
            color=blip_color,
            highlight_color=color.white
        )
        lbl = Text(
            parent=blip_btn,
            text=fid,
            position=(0.72, 0.35),
            scale=21,
            color=blip_color
        )
        blip_btn.on_click = lambda fid=fid: self.select_flight(fid)

        dist_nm = round(Vec2(pos[0], pos[1]).length() * 65.0, 1)

        self.flights[fid] = {
            "id": fid,
            "pos": Vec2(pos[0], pos[1]),
            "vel": Vec2(vel[0], vel[1]),
            "is_anomaly": is_anomaly,
            "is_phantom_decoy": is_phantom_decoy,
            "lands_on_runway": lands_on_runway,
            "altitude": float(altitude),
            "speed_kts": float(speed_kts),
            "fuel_sec": float(fuel_sec),
            "dist_nm": dist_nm,
            "registry": registry,
            "radio_msg": radio_msg,
            "btn1_label": btn1_label,
            "btn1_reply": btn1_reply,
            "btn2_label": btn2_label,
            "btn2_danger": btn2_danger,
            "resolved": False,
            "phosphor": 1.0,
            "entity": blip_btn,
            "label": lbl
        }

    def select_flight(self, fid):
        data = self.flights.get(fid)
        if not data:
            return
        if self.sfx:
            self.sfx.play("radio_static")
        self.selected_flight_id = fid
        self.selection_ring.enabled = True
        self.selection_ring.position = (data["pos"].x, data["pos"].y)
        self._refresh_telemetry(data)

        self.radio_log.text = self._wrap(f"[{data['id']}]: {data['radio_msg']}", width=46)

        if not data["resolved"]:
            self.action_btn_1.text = data["btn1_label"]
            self.action_btn_1.enabled = True
            self.action_btn_1.on_click = lambda fid=fid: self._resolve_flight(fid)

            if data["btn2_label"]:
                self.action_btn_2.text = data["btn2_label"]
                self.action_btn_2.enabled = True
                self.action_btn_2.on_click = lambda fid=fid: self._trigger_bad_decision(fid)
            else:
                self.action_btn_2.enabled = False
        else:
            self.action_btn_1.enabled = False
            self.action_btn_2.enabled = False

    def _refresh_telemetry(self, data):
        status_txt = "AUTORIZADO" if data["resolved"] else "ACTIVO"
        fuel_txt = "N/A" if data["fuel_sec"] > 500 else f"{int(data['fuel_sec'])} SEG"
        alt_txt = f"{int(data['altitude']):,} FT"
        spd_txt = f"{int(data['speed_kts'])} KTS"

        self.telemetry_text.text = self._wrap(
            f"INDICATIVO:  {data['id']}  [{status_txt}]\n"
            f"DISTANCIA:   {data['dist_nm']:.1f} NM   |   COMBUSTIBLE: {fuel_txt}\n"
            f"ALTITUD:     {alt_txt}   |   VELOCIDAD: {spd_txt}\n"
            f"REGISTRO:    {data['registry']}",
            width=45
        )

    def _trigger_bad_decision(self, fid):
        if self.sfx:
            self.sfx.play("alarm_anomaly")
        self.screen_overlay.enabled = False
        self.tower_env.set_radar_focus(False)
        self.enabled = False
        self.on_level_defeat(
            "PROTOCOLO VIOLADO - INCURSIÓN EN PISTA",
            f"Concediste acceso a {fid} sin verificación oficial.\n"
            "La anomalía cruzó el umbral de la pista provocando una falla catastrófica en la torre.",
            self.current_level
        )

    def _resolve_flight(self, fid):
        data = self.flights.get(fid)
        if not data or data["resolved"]:
            return

        # Interactividad directa con las luces de la pista
        if data["lands_on_runway"] and self.tower_env.runway_light_mode == "OFF":
            if self.sfx:
                self.sfx.play("alarm_anomaly")
            self.radio_log.text = self._wrap(
                f"[{fid}]: ¡Torre, no vemos la Pista 09/27 en la oscuridad! Presiona [L] para encender las luces de pista."
            )
            return

        if data["lands_on_runway"] and self.runway_busy_timer > 0:
            if self.sfx:
                self.sfx.play("alarm_anomaly")
            self.radio_log.text = self._wrap(
                f"[CONTROL PISTA]: ¡ESPERA! La Pista 09/27 sigue ocupada ({int(self.runway_busy_timer)}s). Mantén {fid} en espera."
            )
            return

        if self.sfx:
            self.sfx.play("ui_click")

        data["resolved"] = True
        data["entity"].color = config.COLOR_TEXT_MUTED
        data["label"].color = config.COLOR_TEXT_MUTED
        self.action_btn_1.enabled = False
        self.action_btn_2.enabled = False
        self.radio_log.text = self._wrap(f"[{fid}]: {data['btn1_reply']}", width=46)
        self.resolved_count += 1

        if data["lands_on_runway"]:
            self.runway_busy_timer = 11.0
            self.tower_env.spawn_landing_aircraft()
            to_center = Vec2(0, 0) - data["pos"]
            if to_center.length() > 0.001:
                data["vel"] = to_center.normalized() * 0.016

        if data["is_phantom_decoy"]:
            data["entity"].enabled = False
            if self.selected_flight_id == fid:
                self.selection_ring.enabled = False

        if self.current_level == 1:
            if self.resolved_count == 2 and "???-000" not in self.flights:
                self._schedule_event("LVL1_ANOMALY", 1.2)
            elif data["is_anomaly"]:
                self._schedule_event("FINISH_LVL1", 1.8)

        elif self.current_level == 2:
            if fid == "ECO-77":
                self._schedule_event("CLOSE_FOR_LVL2_WALK", 1.1)

        elif self.current_level == 3:
            if data["is_anomaly"]:
                self.tower_env.spawn_window_shadow(2.0)
                self.tower_env.trigger_power_flicker(1.5)
            if self.resolved_count >= 3:
                self._schedule_event("FINISH_LVL3", 1.6)

        elif self.current_level == 4:
            if data["is_anomaly"]:
                self.tower_env.spawn_window_shadow(2.2)
                self.tower_env.spawn_ghost_flyby()
            if self.resolved_count >= 2:
                self._schedule_event("FINISH_LVL4", 1.8)

    def _trigger_level1_anomaly(self):
        self.tower_env.trigger_power_flicker(duration=2.6)
        self.tower_env.spawn_ghost_flyby()
        self.glitch_timer = 2.0
        self.objective_text.text = "ALERTA: ¡Señal no identificada detectada en el radar!"
        self.objective_text.color = config.COLOR_ALERT_RED
        self.radio_log.text = self._wrap("[SISTEMA]: ADVERTENCIA - Contacto sin código de vuelo cruzando frente a la torre.")

        self._spawn_flight(
            fid="???-000",
            pos=(0.05, 0.22),
            vel=(-0.005, -0.014),
            is_anomaly=True,
            altitude=34000,
            speed_kts=980,
            fuel_sec=55.0,
            registry="ERROR: NO EXISTE EN REGISTROS OFICIALES",
            radio_msg="\"...Torre... ¿nos reciben?... Llevamos 40 años esperando Pista 09/27...\"",
            btn1_label="RASTREAR SEÑAL Y MANTENER EN ESPERA [PROTOCOLO]",
            btn1_reply="[SISTEMA]: Señal grabada. La aeronave desapareció del radar sin dejar rastro.",
            btn2_label="AUTORIZAR ATERRIZAJE INMEDIATO EN PISTA 09/27",
            btn2_danger=True
        )
        self.select_flight("???-000")

    def _finish_level_1(self):
        self.tower_env.set_radar_focus(False)
        self.enabled = False
        self.on_level_complete(
            "NIVEL 1 COMPLETADO: EL PRIMER CONTACTO",
            "Has confirmado que la señal ???-000 no figura en ninguna base de datos oficial.\n"
            "Las transmisiones provienen de un incidente oculto hace décadas.\n\n"
            "Prepárate para el Nivel 2: Señal Perdida.",
            True
        )

    def _finish_level_3(self):
        self.tower_env.set_radar_focus(False)
        self.enabled = False
        self.on_level_complete(
            "NIVEL 3 COMPLETADO: FRECUENCIA FANTASMA",
            "Lograste separar el tráfico comercial real de las transmisiones clonadas de 1986.\n"
            "Sin embargo, todas las antenas del aeropuerto ahora apuntan hacia Torre Norte.\n\n"
            "Prepárate para el Nivel 4: Protocolo Black Radar.",
            True
        )

    def _finish_level_4(self):
        self.tower_env.set_radar_focus(False)
        self.enabled = False
        self.on_level_complete(
            "CAMPAÑA COMPLETADA: BLACK RADAR",
            "Sellaste la frecuencia fantasma y sobreviviste al turno nocturno en Torre Norte.\n"
            "El espacio aéreo vuelve a quedar en silencio... hasta la próxima tormenta.\n\n"
            "¡Gracias por jugar BLACK RADAR!",
            False
        )

    def toggle_screen(self):
        if self.tower_env.zone != "TOWER" or self.tower_env.choice_modal_open:
            return
        if self.sfx:
            self.sfx.play("ui_click")
        new_state = not self.screen_overlay.enabled
        self.screen_overlay.enabled = new_state
        self.tower_env.set_radar_focus(new_state)

    def _trigger_early_phantom_blip(self):
        if self.sfx:
            self.sfx.play("radio_static")
        self.glitch_timer = 0.65
        phantom = Button(
            parent=self.blips_layer,
            model=Circle(16),
            position=(random.choice([-0.23, 0.23]), random.uniform(-0.18, 0.18)),
            scale=0.030,
            color=config.COLOR_ALERT_RED
        )
        Text(parent=phantom, text="¿¿??", position=(0.7, 0.3), scale=20, color=config.COLOR_ALERT_RED)
        destroy(phantom, delay=1.4)

    def update(self):
        if not self.enabled:
            return

        dt = time.dt
        self.level_elapsed += dt
        self.shift_seconds += dt

        hrs = int(self.shift_seconds // 3600) % 24
        mins = int((self.shift_seconds % 3600) // 60)
        secs = int(self.shift_seconds % 60)
        if self.glitch_timer > 0:
            self.clock_header.text = "TORRE NORTE  |  02:15:?? (1986)  |  ERR-MHz"
            self.clock_header.color = config.COLOR_ALERT_RED
        else:
            self.clock_header.text = f"TORRE NORTE  |  {hrs:02d}:{mins:02d}:{secs:02d} AM  |  118.1 MHz"
            self.clock_header.color = config.COLOR_CYAN_UI

        l_mode = self.tower_env.runway_light_mode
        if self.runway_busy_timer > 0:
            self.runway_busy_timer = max(0.0, self.runway_busy_timer - dt)
            self.runway_status_text.text = f"PISTA: OCUPADA ({int(self.runway_busy_timer)}s)  |  LUCES: {l_mode}"
            self.runway_status_text.color = config.COLOR_AMBER_UI
        else:
            self.runway_status_text.text = f"PISTA: DESPEJADA  |  LUCES [L]: {l_mode}"
            self.runway_status_text.color = config.COLOR_ALERT_RED if l_mode == "OFF" else config.COLOR_RADAR_GREEN

        if self.glitch_timer > 0:
            self.glitch_timer -= dt
            self.glitch_overlay.enabled = True
            self.glitch_overlay.color = config.rgb(220, 25, 35, random.randint(25, 85))
        else:
            self.glitch_overlay.enabled = False

        if self.pending_event_name:
            self.pending_event_timer -= dt
            if self.pending_event_timer <= 0:
                ev = self.pending_event_name
                self.pending_event_name = None
                if ev == "LVL1_ANOMALY":
                    self._trigger_level1_anomaly()
                elif ev == "FINISH_LVL1":
                    self._finish_level_1()
                elif ev == "CLOSE_FOR_LVL2_WALK":
                    if self.screen_overlay.enabled:
                        self.toggle_screen()
                elif ev == "FINISH_LVL3":
                    self._finish_level_3()
                elif ev == "FINISH_LVL4":
                    self._finish_level_4()

        if self.current_level == 1 and not self.early_scare_done and self.screen_overlay.enabled and self.level_elapsed > 9.0:
            self.early_scare_done = True
            self._trigger_early_phantom_blip()

        if self.current_level >= 3 and not self.mid_scare_done and self.level_elapsed > 11.0:
            self.mid_scare_done = True
            self.tower_env.spawn_window_shadow(2.5)
            self.tower_env.trigger_power_flicker(1.6)

        for fid, data in list(self.flights.items()):
            if not data["entity"].enabled:
                continue

            data["pos"] += data["vel"] * dt

            if not data["is_anomaly"] and data["pos"].length() > 0.275:
                normal = data["pos"].normalized()
                data["pos"] = normal * 0.275
                data["vel"] = -data["vel"]

            if data["resolved"] and data["lands_on_runway"]:
                data["altitude"] = max(0.0, data["altitude"] - 1100.0 * dt)
                data["speed_kts"] = max(135.0, data["speed_kts"] - 12.0 * dt)

            if data["is_anomaly"] and not data["resolved"] and data["speed_kts"] > 0:
                data["altitude"] = max(400.0, data["altitude"] + random.uniform(-1800, 1400) * dt)
                data["speed_kts"] = clamp(data["speed_kts"] + random.uniform(-120, 140) * dt, 450, 1450)
                if data["pos"].length() > 0.27:
                    data["vel"] = -data["vel"]

            data["entity"].position = (data["pos"].x, data["pos"].y)
            data["dist_nm"] = round(data["pos"].length() * 65.0, 1)

            if not data["resolved"] and data["fuel_sec"] < 500:
                data["fuel_sec"] -= dt
                if data["fuel_sec"] <= 0:
                    self.screen_overlay.enabled = False
                    self.tower_env.set_radar_focus(False)
                    self.enabled = False
                    self.on_level_defeat(
                        "EMERGENCIA DE COMBUSTIBLE",
                        f"El vuelo {fid} agotó su reserva de combustible esperando instrucciones de la torre.",
                        self.current_level
                    )
                    return

        if self.selected_flight_id and self.selected_flight_id in self.flights:
            sel = self.flights[self.selected_flight_id]
            if sel["entity"].enabled:
                self.selection_ring.position = (sel["pos"].x, sel["pos"].y)
                if self.screen_overlay.enabled:
                    self._refresh_telemetry(sel)

        if self.screen_overlay.enabled:
            delta_rot = 105 * dt
            self.sweep_pivot.rotation_z += delta_rot
            self.sweep_angle_accum += delta_rot
            if self.sweep_angle_accum >= 360.0:
                self.sweep_angle_accum -= 360.0
                if self.sfx:
                    self.sfx.play("radar_ping")

            sweep_deg = self.sweep_pivot.rotation_z % 360.0
            for fid, data in self.flights.items():
                if not data["entity"].enabled:
                    continue
                px, py = data["pos"].x, data["pos"].y
                blip_deg = math.degrees(math.atan2(px, py)) % 360.0
                diff = abs((sweep_deg - blip_deg + 180.0) % 360.0 - 180.0)

                if diff < 12.0:
                    if data["phosphor"] < 0.75 and data["is_anomaly"] and not data["resolved"] and data["speed_kts"] > 0:
                        data["pos"] = Vec2(
                            clamp(px + random.uniform(-0.07, 0.07), -0.24, 0.24),
                            clamp(py + random.uniform(-0.07, 0.07), -0.24, 0.24)
                        )
                        data["label"].text = random.choice([fid, "1986", "AYUDA", fid])
                    data["phosphor"] = 1.0
                else:
                    data["phosphor"] = max(0.32, data["phosphor"] - 0.42 * dt)

                alpha_val = int(data["phosphor"] * 255)
                if data["resolved"]:
                    base_c = config.rgb(125, 145, 165, alpha_val)
                elif data["is_anomaly"]:
                    base_c = config.rgb(245, 55, 65, alpha_val)
                else:
                    base_c = config.rgb(55, 245, 130, alpha_val)

                data["entity"].color = base_c
                data["label"].color = base_c
                data["entity"].scale = 0.030 + (data["phosphor"] * 0.008)