from ursina import *
import textwrap
import config


class MenuManager(Entity):
    def __init__(self, sfx, on_start_level, on_resume_game, on_quit_to_menu, on_settings_changed):
        super().__init__(parent=camera.ui)
        self.sfx = sfx
        self.on_start_level = on_start_level
        self.on_resume_game = on_resume_game
        self.on_quit_to_menu = on_quit_to_menu
        self.on_settings_changed = on_settings_changed

        self.bg = Entity(
            parent=self,
            model='quad',
            scale=(2.2, 1.3),
            color=config.rgb(8, 12, 18),
            z=2
        )

        self.main_panel = Entity(parent=self, enabled=False)
        self.levels_panel = Entity(parent=self, enabled=False)
        self.settings_panel = Entity(parent=self, enabled=False)
        self.credits_panel = Entity(parent=self, enabled=False)
        self.pause_panel = Entity(parent=self, enabled=False)
        self.victory_panel = Entity(parent=self, enabled=False)
        self.defeat_panel = Entity(parent=self, enabled=False)

        self._build_main_menu()
        self._build_levels_menu()
        self._build_settings_menu()
        self._build_credits_menu()
        self._build_pause_menu()
        self._build_victory_menu()
        self._build_defeat_menu()

    def _wrap(self, msg, width=64):
        return "\n".join(textwrap.fill(line, width=width) for line in msg.split("\n"))

    def _make_button(self, parent, text, y, action, scale=(0.48, 0.058),
                     bg_color=None, txt_color=None):
        btn = Button(
            parent=parent,
            text=text,
            position=(0, y),
            scale=scale,
            color=bg_color or config.rgb(20, 28, 38),
            highlight_color=config.rgb(34, 52, 68),
            text_color=txt_color or config.COLOR_TEXT_MAIN
        )

        def _clicked():
            if self.sfx:
                self.sfx.play("ui_click")
            action()

        btn.on_click = _clicked
        return btn

    def _build_main_menu(self):
        Text(
            parent=self.main_panel,
            text="BLACK RADAR",
            position=(0, 0.30),
            origin=(0, 0),
            scale=3.0,
            color=config.COLOR_RADAR_GREEN
        )
        Text(
            parent=self.main_panel,
            text="SIMULADOR DE CONTROL AÉREO NOCTURNO  //  TORRE NORTE",
            position=(0, 0.21),
            origin=(0, 0),
            scale=0.95,
            color=config.COLOR_CYAN_UI
        )

        self._make_button(
            self.main_panel, "INICIAR TURNO (NIVEL 1)", 0.06,
            lambda: self.on_start_level(1),
            bg_color=config.rgb(16, 48, 34),
            txt_color=config.COLOR_RADAR_GREEN
        )
        self._make_button(self.main_panel, "SELECCIONAR NIVEL", -0.02, self.show_levels)
        self._make_button(self.main_panel, "AJUSTES", -0.10, self.show_settings)
        self._make_button(self.main_panel, "CRÉDITOS", -0.18, self.show_credits)
        self._make_button(
            self.main_panel, "SALIR DEL JUEGO", -0.26, application.quit,
            bg_color=config.rgb(52, 20, 24),
            txt_color=config.COLOR_ALERT_RED
        )

    def _build_levels_menu(self):
        Text(
            parent=self.levels_panel,
            text="SELECCIÓN DE TURNO",
            position=(0, 0.32),
            origin=(0, 0),
            scale=1.9,
            color=config.COLOR_CYAN_UI
        )

        self._make_button(
            self.levels_panel, "NIVEL 1: EL PRIMER CONTACTO", 0.16,
            lambda: self.on_start_level(1), scale=(0.64, 0.058),
            txt_color=config.COLOR_RADAR_GREEN
        )
        self._make_button(
            self.levels_panel, "NIVEL 2: SEÑAL PERDIDA (HANGAR OESTE)", 0.07,
            lambda: self.on_start_level(2), scale=(0.64, 0.058),
            txt_color=config.COLOR_AMBER_UI
        )
        self._make_button(
            self.levels_panel, "NIVEL 3: FRECUENCIA FANTASMA", -0.02,
            lambda: self.on_start_level(3), scale=(0.64, 0.058),
            txt_color=config.COLOR_AMBER_UI
        )
        self._make_button(
            self.levels_panel, "NIVEL 4: PROTOCOLO BLACK RADAR", -0.11,
            lambda: self.on_start_level(4), scale=(0.64, 0.058),
            bg_color=config.rgb(52, 20, 24),
            txt_color=config.COLOR_ALERT_RED
        )
        self._make_button(self.levels_panel, "VOLVER", -0.26, self.show_main, scale=(0.36, 0.056))

    def _build_settings_menu(self):
        Text(
            parent=self.settings_panel,
            text="AJUSTES DEL SISTEMA",
            position=(0, 0.32),
            origin=(0, 0),
            scale=1.8,
            color=config.COLOR_CYAN_UI
        )

        self.vol_text = Text(parent=self.settings_panel, text="", position=(0, 0.16), origin=(0, 0), scale=1.05)
        self._make_button(self.settings_panel, "VOLUMEN  - / +", 0.09, self._cycle_volume, scale=(0.42, 0.052))

        self.bright_text = Text(parent=self.settings_panel, text="", position=(0, -0.01), origin=(0, 0), scale=1.05)
        self._make_button(self.settings_panel, "BRILLO  - / +", -0.08, self._cycle_brightness, scale=(0.42, 0.052))

        self.sens_text = Text(parent=self.settings_panel, text="", position=(0, -0.18), origin=(0, 0), scale=1.05)
        self._make_button(self.settings_panel, "SENSIBILIDAD RATÓN  - / +", -0.25, self._cycle_sensitivity, scale=(0.46, 0.052))

        self._make_button(self.settings_panel, "VOLVER", -0.36, self.show_main, scale=(0.35, 0.054))
        self._refresh_settings_labels()

    def _refresh_settings_labels(self):
        vol = config.settings.get("volume", config.settings.get("master_volume", 0.8))
        bright = config.settings.get("brightness", 1.0)
        sens = config.settings.get("sensitivity", 40.0)
        self.vol_text.text = f"VOLUMEN DE AUDIO: {int(vol * 100)}%"
        self.bright_text.text = f"BRILLO NOCTURNO: {int(bright * 100)}%"
        self.sens_text.text = f"SENSIBILIDAD DE CÁMARA: {int(sens)}"

    def _cycle_volume(self):
        key = "volume" if "volume" in config.settings else "master_volume"
        cur = config.settings.get(key, 0.8)
        nxt = round(cur + 0.2, 1)
        if nxt > 1.0:
            nxt = 0.0
        config.settings[key] = nxt
        self._refresh_settings_labels()
        self.on_settings_changed()

    def _cycle_brightness(self):
        cur = config.settings.get("brightness", 1.0)
        nxt = round(cur + 0.25, 2)
        if nxt > 1.5:
            nxt = 0.75
        config.settings["brightness"] = nxt
        self._refresh_settings_labels()
        self.on_settings_changed()

    def _cycle_sensitivity(self):
        cur = config.settings.get("sensitivity", 40.0)
        nxt = cur + 15.0
        if nxt > 85.0:
            nxt = 25.0
        config.settings["sensitivity"] = nxt
        self._refresh_settings_labels()

    def _build_credits_menu(self):
        Text(
            parent=self.credits_panel,
            text="BLACK RADAR - CRÉDITOS",
            position=(0, 0.32),
            origin=(0, 0),
            scale=1.8,
            color=config.COLOR_RADAR_GREEN
        )
        Text(
            parent=self.credits_panel,
            text=(
                "Proyecto de Videojuego 3D - Programación en Python\n"
                "Motor Gráfico: Ursina Engine / Panda3D\n"
                "Audio: Síntesis Procedural PCM en Python\n\n"
                "MODELOS 3D DE TERCEROS:\n"
                "CesiumMilkTruck & SheenChair [CC-BY 4.0] via Khronos glTF Sample Assets\n"
                "Airplane by Poly by Google [CC-BY] via Poly Pizza\n\n"
                "\"Algunas señales nunca debieron ser respondidas.\""
            ),
            position=(0, 0.03),
            origin=(0, 0),
            scale=0.98,
            line_height=1.42,
            color=config.COLOR_TEXT_MAIN
        )
        self._make_button(self.credits_panel, "VOLVER", -0.30, self.show_main, scale=(0.35, 0.058))

    def _build_pause_menu(self):
        Text(
            parent=self.pause_panel,
            text="TURNO EN PAUSA",
            position=(0, 0.24),
            origin=(0, 0),
            scale=2.0,
            color=config.COLOR_CYAN_UI
        )
        self._make_button(
            self.pause_panel, "REANUDAR TURNO", 0.05, self.on_resume_game,
            bg_color=config.rgb(16, 48, 34), txt_color=config.COLOR_RADAR_GREEN
        )
        self._make_button(self.pause_panel, "VOLVER AL MENÚ PRINCIPAL", -0.05, self.on_quit_to_menu)

    def _build_victory_menu(self):
        self.victory_title = Text(
            parent=self.victory_panel,
            text="",
            position=(0, 0.26),
            origin=(0, 0),
            scale=1.75,
            color=config.COLOR_RADAR_GREEN
        )
        self.victory_summary = Text(
            parent=self.victory_panel,
            text="",
            position=(0, 0.06),
            origin=(0, 0),
            scale=1.02,
            line_height=1.35,
            color=config.COLOR_TEXT_MAIN
        )
        self.victory_next_btn = self._make_button(
            self.victory_panel, "SIGUIENTE TURNO", -0.15,
            lambda: self.on_start_level(2),
            bg_color=config.rgb(16, 48, 34),
            txt_color=config.COLOR_RADAR_GREEN
        )
        self._make_button(self.victory_panel, "VOLVER AL MENÚ", -0.24, self.on_quit_to_menu)

    def _build_defeat_menu(self):
        self.defeat_title = Text(
            parent=self.defeat_panel,
            text="",
            position=(0, 0.26),
            origin=(0, 0),
            scale=1.75,
            color=config.COLOR_ALERT_RED
        )
        self.defeat_reason = Text(
            parent=self.defeat_panel,
            text="",
            position=(0, 0.06),
            origin=(0, 0),
            scale=1.02,
            line_height=1.35,
            color=config.COLOR_TEXT_MAIN
        )
        self.defeat_retry_btn = self._make_button(
            self.defeat_panel, "REINTENTAR TURNO", -0.15,
            lambda: self.on_start_level(1),
            bg_color=config.rgb(52, 20, 24),
            txt_color=config.COLOR_AMBER_UI
        )
        self._make_button(self.defeat_panel, "VOLVER AL MENÚ", -0.24, self.on_quit_to_menu)

    def hide_all(self):
        self.bg.enabled = False
        self.main_panel.enabled = False
        self.levels_panel.enabled = False
        self.settings_panel.enabled = False
        self.credits_panel.enabled = False
        self.pause_panel.enabled = False
        self.victory_panel.enabled = False
        self.defeat_panel.enabled = False

    def show_main(self):
        self.hide_all()
        self.bg.enabled = True
        self.main_panel.enabled = True

    def show_levels(self):
        self.hide_all()
        self.bg.enabled = True
        self.levels_panel.enabled = True

    def show_settings(self):
        self.hide_all()
        self.bg.enabled = True
        self.settings_panel.enabled = True

    def show_credits(self):
        self.hide_all()
        self.bg.enabled = True
        self.credits_panel.enabled = True

    def show_pause(self):
        self.hide_all()
        self.bg.enabled = True
        self.bg.color = config.rgb(8, 12, 18, 215)
        self.pause_panel.enabled = True

    def show_victory(self, title_text, summary_text, show_next=True, next_level=2):
        self.hide_all()
        self.bg.enabled = True
        self.bg.color = config.rgb(8, 12, 18)
        self.victory_title.text = title_text
        self.victory_summary.text = self._wrap(summary_text, width=68)

        if show_next and next_level <= 4:
            self.victory_next_btn.enabled = True
            self.victory_next_btn.text = f"SIGUIENTE TURNO (NIVEL {next_level})"

            def _go_next():
                if self.sfx:
                    self.sfx.play("ui_click")
                self.on_start_level(next_level)

            self.victory_next_btn.on_click = _go_next
        else:
            self.victory_next_btn.enabled = False

        self.victory_panel.enabled = True

    def show_defeat(self, title_text, reason_text, level_num=1):
        self.hide_all()
        self.bg.enabled = True
        self.bg.color = config.rgb(8, 12, 18)
        self.defeat_title.text = title_text
        self.defeat_reason.text = self._wrap(reason_text, width=68)
        self.defeat_retry_btn.text = f"REINTENTAR NIVEL {level_num}"

        def _retry():
            if self.sfx:
                self.sfx.play("ui_click")
            self.on_start_level(level_num)

        self.defeat_retry_btn.on_click = _retry
        self.defeat_panel.enabled = True