from ursina import color


def rgb(r, g, b, a=255):
    return color.rgba(r / 255, g / 255, b / 255, a / 255)


GAME_TITLE = "BLACK RADAR"
GAME_SUBTITLE = "THE UNKNOWN IS CLOSER THAN YOU THINK"

# Configuración modificable desde el menú de Configuración
settings = {
    "volume": 0.8,        # 0.0 a 1.0
    "sensitivity": 45.0,  # 15.0 a 90.0
    "brightness": 1.0     # 0.6 a 1.6
}

# Paleta estética oscura / aeronáutica
COLOR_BG_DARK = rgb(6, 9, 14)
COLOR_PANEL = rgb(10, 16, 24, 240)
COLOR_RADAR_GREEN = rgb(40, 230, 120)
COLOR_RADAR_DIM = rgb(25, 140, 75, 110)
COLOR_ALERT_RED = rgb(235, 55, 55)
COLOR_CYAN_UI = rgb(90, 200, 240)
COLOR_AMBER_UI = rgb(245, 185, 65)
COLOR_TEXT_MAIN = rgb(225, 235, 245)
COLOR_TEXT_MUTED = rgb(130, 145, 160)
COLOR_LOCKED = rgb(45, 50, 58)

# Límites de movimiento dentro de la cabina de la torre
CABIN_LIMIT_X = 3.0
CABIN_LIMIT_Z = 2.0