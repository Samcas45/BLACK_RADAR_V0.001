from ursina import *
import config
from texture_gen import TextureGenerator
from sound_manager import SoundManager
from menus import MenuManager
from tower_scene import TowerEnvironment
from radar_system import RadarConsole


app = Ursina(
    title=config.GAME_TITLE,
    borderless=False,
    fullscreen=False
)

state = "MENU"  # MENU, PLAYING, PAUSED, VICTORY, DEFEAT
current_level = 1

tex_gen = TextureGenerator()
sfx = SoundManager()


def handle_level_complete(title_text, summary_text, show_next=True):
    global state
    state = "VICTORY"
    sfx.stop_ambient()
    tower.hide_overlays()
    radar.enabled = False
    mouse.locked = False
    mouse.visible = True
    menus.show_victory(
        title_text,
        summary_text,
        show_next=show_next,
        next_level=current_level + 1
    )


def handle_level_defeat(title_text, reason_text, level_num=1):
    global state
    state = "DEFEAT"
    sfx.stop_ambient()
    tower.hide_overlays()
    radar.enabled = False
    mouse.locked = False
    mouse.visible = True
    menus.show_defeat(title_text, reason_text, level_num=level_num)


tower = TowerEnvironment(
    sfx=sfx,
    on_trigger_victory=handle_level_complete,
    on_trigger_defeat=handle_level_defeat
)

radar = RadarConsole(
    tower_env=tower,
    sfx=sfx,
    on_level_complete=handle_level_complete,
    on_level_defeat=handle_level_defeat
)


def start_level(level_num):
    global state, current_level
    current_level = level_num
    state = "PLAYING"
    menus.hide_all()
    sfx.start_ambient()
    tower.activate_scene(level_num)
    radar.start_level(level_num)


def resume_game():
    global state
    state = "PLAYING"
    menus.hide_all()
    sfx.start_ambient()
    tower.enabled = True
    radar.enabled = True
    if tower.zone == "TOWER":
        tower.set_radar_focus(radar.screen_overlay.enabled)
    else:
        mouse.locked = not tower.choice_modal_open
        mouse.visible = tower.choice_modal_open


def quit_to_menu():
    global state
    state = "MENU"
    sfx.stop_ambient()
    tower.hide_overlays()
    tower.enabled = False
    radar.enabled = False
    mouse.locked = False
    mouse.visible = True
    menus.show_main()


def apply_settings():
    sfx.update_volume()
    tower.apply_visual_settings()


menus = MenuManager(
    sfx=sfx,
    on_start_level=start_level,
    on_resume_game=resume_game,
    on_quit_to_menu=quit_to_menu,
    on_settings_changed=apply_settings
)


def input(key):
    global state
    if state == "PLAYING":
        if key in ('e', 'tab'):
            radar.toggle_screen()
        elif key == 'f':
            tower.interact()
        elif key == 'l':
            tower.cycle_runway_lights()
        elif key == 'escape':
            state = "PAUSED"
            sfx.stop_ambient()
            tower.hide_overlays()
            tower.enabled = False
            radar.enabled = False
            mouse.locked = False
            mouse.visible = True
            menus.show_pause()
    elif state == "PAUSED" and key == 'escape':
        resume_game()


menus.show_main()
app.run()