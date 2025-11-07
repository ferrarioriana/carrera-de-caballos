import math
import random
import time
from typing import List, Dict, Tuple, Optional

from equestrian.domain.caballo import Caballo, Yegua, PuraSangre
from equestrian.domain.jinete import Jinete
from equestrian.services.persistence import cargar_progreso, guardar_progreso
from equestrian.services.performance import guardar_grafico_performance
from equestrian.services.history import load_history, append_history

# --- Ajustes del juego ---
WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = HEIGHT - 90
GOAL_DISTANCE = 3500.0  # metros virtuales para ganar
PIXELS_PER_METER = 0.35
BG_PX_PER_M = 10.0

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (220, 40, 40)
BLUE = (40, 100, 240)
YELLOW = (240, 210, 40)
BROWN = (120, 72, 32)
GRAY = (120, 120, 120)
DARK = (30, 30, 30)
LIGHT = (230, 230, 230)

CLIMATE_SETTINGS: Dict[str, Dict[str, float]] = {
    "Soleado": {"friction": 0.99, "regen": 1.05},
    "Lluvioso": {"friction": 0.96, "regen": 0.9},
    "Ventoso": {"friction": 0.97, "regen": 0.95},
    "Barro": {"friction": 0.94, "regen": 0.85},
}

PINK = (245, 115, 155)
PINK_DARK = (220, 85, 125)
PINK_SOFT = (255, 210, 225)
INK = (30, 30, 30)
PANEL_BG = (255, 255, 255)
SHADOW = (0, 0, 0)
THEME_PRIMARY = PINK
THEME_SECONDARY = PINK_DARK
THEME_PANEL = PANEL_BG
THEME_BACKGROUND = PINK_SOFT
THEME_TEXT = INK
THEME_MUTED = (120, 130, 150)
FONT_NAME = "Times New Roman"
PARALLAX_FAR = 0.2
PARALLAX_MID = 0.5
PARALLAX_NEAR = 0.8
RAZAS = ["Pura Sangre", "Criollo", "Árabe", "Cuarto de Milla", "Percherón"]

def _color_lerp(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def _gradient_rect(surface, color_start, color_end, rect):
    import pygame
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        col = _color_lerp(color_start, color_end, t)
        pygame.draw.line(surface, col, (x, y + i), (x + w, y + i))

def _draw_side_background(screen, camera_x: float, clima: str) -> None:
    import pygame

    width, height = screen.get_size()
    sky_palettes = {
        "Soleado": ((135, 195, 255), (220, 245, 255)),
        "Ventoso": ((120, 180, 240), (210, 235, 250)),
        "Lluvioso": ((110, 140, 170), (170, 190, 210)),
        "Barro": ((120, 140, 150), (180, 195, 205)),
    }
    top_color, bottom_color = sky_palettes.get(clima, ((135, 195, 255), (220, 245, 255)))

    bands = 10
    band_h = height // bands
    for i in range(bands):
        rect = pygame.Rect(0, i * band_h, width, band_h + 1)
        pygame.draw.rect(screen, _color_lerp(top_color, bottom_color, i / (bands - 1)), rect)

    if clima == "Soleado":
        pygame.draw.circle(screen, (255, 245, 160), (width - 120, 90), 36)
        pygame.draw.circle(screen, (255, 255, 210), (width - 120, 90), 50, width=6)

    camera_px = camera_x * PIXELS_PER_METER

    mountain_color_far = (150, 170, 200)
    offset = (camera_px * 0.2) % (width)
    for i in range(-1, 3):
        base_x = -offset + i * width
        points = [
            (base_x - 80, GROUND_Y - 120),
            (base_x + width * 0.25, GROUND_Y - 220),
            (base_x + width * 0.55, GROUND_Y - 160),
            (base_x + width + 80, GROUND_Y - 120),
        ]
        pygame.draw.polygon(screen, mountain_color_far, points)

    mountain_color_near = (120, 150, 190)
    offset = (camera_px * 0.35) % (width)
    for i in range(-1, 3):
        base_x = -offset + i * width
        points = [
            (base_x - 100, GROUND_Y - 80),
            (base_x + width * 0.2, GROUND_Y - 165),
            (base_x + width * 0.6, GROUND_Y - 110),
            (base_x + width + 100, GROUND_Y - 80),
        ]
        pygame.draw.polygon(screen, mountain_color_near, points)

    cloud_color = (245, 245, 250) if clima != "Lluvioso" else (210, 215, 220)
    spacing = 220
    offset = (camera_px * 0.15) % spacing
    for i in range(-2, 5):
        x = -offset + i * spacing
        y = 90 + (i % 3) * 20
        pygame.draw.ellipse(screen, cloud_color, (x, y, 120, 45))
        pygame.draw.ellipse(screen, cloud_color, (x + 50, y - 10, 90, 40))
        pygame.draw.ellipse(screen, cloud_color, (x + 70, y + 5, 80, 35))

    stand_color = (180, 90, 90)
    stand_offset = (camera_px * 0.5) % (width // 2)
    stand_y = GROUND_Y - 60
    for i in range(-3, 5):
        x = -stand_offset + i * (width // 2)
        pygame.draw.rect(screen, (80, 55, 55), (x, stand_y - 40, width // 2, 6))
        pygame.draw.rect(screen, stand_color, (x, stand_y - 34, width // 2, 34))
        for p in range(12):
            seat_x = x + 10 + p * 20
            seat_y = stand_y - 30 + (p % 2) * 4
            pygame.draw.rect(screen, (235, 235, 240), (seat_x, seat_y, 14, 8))

def _draw_horse_sprite(screen, x: int, base_y: int, scale: float, body_color: Tuple[int, int, int],
                       accent_color: Tuple[int, int, int], rider_color: Tuple[int, int, int],
                       phase: float, bob: float, is_player: bool, boost: float) -> None:
    import pygame

    body_length = int(70 * scale)
    body_height = int(28 * scale)
    leg_height = int(34 * scale)
    neck_length = int(24 * scale)

    body_rect = pygame.Rect(x - body_length // 2, base_y - body_height - leg_height + int(bob),
                            body_length, body_height)
    pygame.draw.ellipse(screen, body_color, body_rect)

    highlight = _color_lerp(body_color, (255, 255, 255), 0.28 + 0.2 * min(1.0, boost))
    highlight_rect = body_rect.inflate(-int(body_length * 0.36), -int(body_height * 0.48))
    pygame.draw.ellipse(screen, highlight, highlight_rect)

    hind_rect = pygame.Rect(body_rect.left - int(10 * scale), body_rect.top + int(6 * scale),
                            int(26 * scale), int(22 * scale))
    pygame.draw.ellipse(screen, body_color, hind_rect)

    head_rect = pygame.Rect(body_rect.right - neck_length, body_rect.top - int(16 * scale),
                            int(26 * scale), int(22 * scale))
    pygame.draw.ellipse(screen, body_color, head_rect)

    ear_points = [
        (head_rect.right - int(6 * scale), head_rect.top + int(4 * scale)),
        (head_rect.right - int(2 * scale), head_rect.top - int(10 * scale)),
        (head_rect.right - int(12 * scale), head_rect.top + int(2 * scale)),
    ]
    pygame.draw.polygon(screen, body_color, ear_points)

    muzzle = pygame.Rect(head_rect.right - int(12 * scale), head_rect.centery - int(6 * scale),
                         int(14 * scale), int(13 * scale))
    pygame.draw.ellipse(screen, _color_lerp(body_color, (60, 60, 60), 0.3), muzzle)

    eye_pos = (head_rect.right - int(10 * scale), head_rect.top + int(10 * scale))
    pygame.draw.circle(screen, (10, 10, 10), eye_pos, max(2, int(2.2 * scale)))
    pygame.draw.circle(screen, (255, 255, 255), (eye_pos[0] - 1, eye_pos[1] - 1), max(1, int(0.9 * scale)))

    tail_points = [
        (body_rect.left - int(12 * scale), body_rect.top + int(6 * scale)),
        (body_rect.left - int(20 * scale), body_rect.top + int(18 * scale)),
        (body_rect.left - int(6 * scale), body_rect.top + int(24 * scale)),
    ]
    pygame.draw.polygon(screen, accent_color, tail_points)

    mane_rect = pygame.Rect(body_rect.centerx - int(4 * scale), body_rect.top - int(10 * scale),
                            int(18 * scale), int(16 * scale))
    pygame.draw.ellipse(screen, accent_color, mane_rect)
    mane_points = [
        (body_rect.centerx - int(8 * scale), body_rect.top - int(2 * scale)),
        (body_rect.centerx - int(2 * scale), body_rect.top - int(12 * scale)),
        (body_rect.centerx + int(6 * scale), body_rect.top - int(6 * scale)),
    ]
    pygame.draw.polygon(screen, accent_color, mane_points)

    hoof_color = (60, 45, 45)
    leg_origin_y = body_rect.bottom - int(2 * scale)
    leg_color_back = _color_lerp(body_color, (40, 40, 40), 0.35)
    leg_color_front = _color_lerp(body_color, (250, 250, 250), 0.08)
    leg_thickness = max(6, int(7 * scale))
    hoof_height = max(4, int(4 * scale))

    def draw_leg(anchor_x: int, offset: float, depth_color: Tuple[int, int, int]) -> None:
        swing = math.sin(phase + offset) * 10 * scale
        knee_x = anchor_x + int(swing * 0.4)
        foot_x = anchor_x + int(swing)
        knee_y = leg_origin_y - int(leg_height * 0.55)
        pts = [
            (anchor_x - leg_thickness // 2, leg_origin_y - int(4 * scale)),
            (knee_x - leg_thickness // 3, knee_y),
            (foot_x + leg_thickness // 2, base_y - hoof_height),
            (foot_x - leg_thickness // 2, base_y - hoof_height),
            (knee_x + leg_thickness // 3, knee_y),
        ]
        pygame.draw.polygon(screen, depth_color, pts)
        pygame.draw.rect(screen, hoof_color, (foot_x - leg_thickness // 2, base_y - hoof_height, leg_thickness, hoof_height))

    rear_anchor = body_rect.left + int(18 * scale)
    front_anchor = body_rect.right - int(16 * scale)
    draw_leg(rear_anchor, 0.0, leg_color_back)
    draw_leg(rear_anchor + int(10 * scale), math.pi, leg_color_back)
    draw_leg(front_anchor, math.pi, leg_color_front)
    draw_leg(front_anchor + int(8 * scale), 0.4, leg_color_front)

    rider_base = body_rect.top - int(14 * scale)
    torso_width = int(16 * scale)
    torso_height = int(22 * scale)
    pygame.draw.rect(screen, rider_color, (body_rect.centerx - torso_width // 2, rider_base - torso_height,
                                           torso_width, torso_height))
    pygame.draw.rect(screen, (40, 40, 60), (body_rect.centerx - int(8 * scale), rider_base - int(6 * scale),
                                            int(16 * scale), int(6 * scale)))
    pygame.draw.circle(screen, (255, 224, 189), (body_rect.centerx, rider_base - torso_height - int(6 * scale)),
                       max(4, int(6 * scale)))
    helmet_color = _color_lerp(rider_color, (10, 10, 10), 0.4)
    pygame.draw.arc(screen, helmet_color,
                    (body_rect.centerx - int(9 * scale), rider_base - torso_height - int(14 * scale),
                     int(18 * scale), int(12 * scale)),
                    math.pi, 2 * math.pi, width=max(2, int(2 * scale)))

    leg_y = rider_base + int(2 * scale)
    pygame.draw.line(screen, rider_color, (body_rect.centerx - int(6 * scale), leg_y),
                     (body_rect.centerx - int(14 * scale), leg_y + int(16 * scale)), max(2, int(3 * scale)))
    pygame.draw.line(screen, rider_color, (body_rect.centerx + int(6 * scale), leg_y),
                     (body_rect.centerx + int(14 * scale), leg_y + int(16 * scale)), max(2, int(3 * scale)))
    pygame.draw.circle(screen, (40, 40, 40),
                       (body_rect.centerx - int(16 * scale), leg_y + int(18 * scale)),
                       max(2, int(3 * scale)))
    pygame.draw.circle(screen, (40, 40, 40),
                       (body_rect.centerx + int(16 * scale), leg_y + int(18 * scale)),
                       max(2, int(3 * scale)))

    bridle_color = _color_lerp(accent_color, (255, 255, 255), 0.3)
    pygame.draw.line(screen, bridle_color,
                     (body_rect.centerx, body_rect.top + int(2 * scale)),
                     (head_rect.centerx, head_rect.centery), max(2, int(2 * scale)))
    pygame.draw.line(screen, bridle_color,
                     (head_rect.centerx - int(10 * scale), head_rect.centery),
                     (head_rect.centerx + int(8 * scale), head_rect.centery + int(2 * scale)),
                     max(2, int(2 * scale)))

    # boost shading handled via colors; no additional glow to avoid halos

# -----------------------------
# Utilidades de UI (pygame)
# -----------------------------
def _ensure_pygame():
    try:
        import pygame  # noqa
        return True
    except Exception:
        print("Necesitas instalar pygame: pip install pygame")
        return False

def _draw_button(screen, font, rect, label, hovered=False, active=False, disabled=False):
    import pygame
    base = PINK
    color = PINK_SOFT if disabled else base
    if not disabled:
        if active:
            color = PINK_DARK
        elif hovered:
            color = PINK_DARK
    shadow_rect = rect.move(2, 2)
    pygame.draw.rect(screen, (*SHADOW, 40), shadow_rect, border_radius=10)
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, INK, rect, 2, border_radius=10)
    text_font = font
    text = text_font.render(label, True, PANEL_BG)
    if text.get_width() > rect.w - 16:
        size = max(12, font.get_height() - 2)
        while size >= 12:
            text_font = pygame.font.SysFont(FONT_NAME, size, bold=False)
            text = text_font.render(label, True, PANEL_BG)
            if text.get_width() <= rect.w - 16 or size == 12:
                break
            size -= 2
    screen.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                       rect.y + (rect.h - text.get_height()) // 2))

def _draw_input(screen, font, rect, value, placeholder="", focused=False):
    import pygame
    bg_color = PANEL_BG if focused else PINK_SOFT
    pygame.draw.rect(screen, bg_color, rect, border_radius=10)
    border_color = PINK if not focused else PINK_DARK
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=10)
    if focused:
        glow = rect.inflate(8, 8)
        pygame.draw.rect(screen, (*PINK, 30), glow, border_radius=12)
    txt = value if value else placeholder
    col = INK if value else THEME_MUTED
    render = font.render(txt, True, col)
    screen.blit(render, (rect.x + 14, rect.y + (rect.h - render.get_height()) // 2))

def _title(screen, bigfont, text, y=30):
    import pygame
    t = bigfont.render(text, True, PINK)
    text_rect = t.get_rect()
    pill = pygame.Rect((screen.get_width() - text_rect.width) // 2 - 24,
                       y - 12, text_rect.width + 48, text_rect.height + 24)
    shadow_rect = pill.move(4, 4)
    pygame.draw.rect(screen, (*SHADOW, 40), shadow_rect, border_radius=18)
    pygame.draw.rect(screen, PANEL_BG, pill, border_radius=18)
    pygame.draw.rect(screen, PINK_SOFT, pill, 2, border_radius=18)
    screen.blit(t, ( (screen.get_width()-t.get_width())//2, y))

def _draw_card(screen, rect, border=20):
    import pygame
    shadow = pygame.Rect(rect.x + 4, rect.y + 6, rect.w, rect.h)
    pygame.draw.rect(screen, (0, 0, 0, 35), shadow, border_radius=border)
    panel_surface = screen.subsurface(rect).copy()
    _gradient_rect(panel_surface, THEME_PANEL, _color_lerp(THEME_PANEL, (228, 232, 240), 0.3),
                   (0, 0, rect.w, rect.h))
    screen.blit(panel_surface, (rect.x, rect.y))
    pygame.draw.rect(screen, (255, 255, 255, 120), rect, 1, border_radius=border)

def _draw_band(screen, offset_x, height, color, base_y):
    import pygame
    width = screen.get_width()
    for shift in (0, width):
        rect = pygame.Rect(offset_x + shift, base_y - height, width, height)
        pygame.draw.rect(screen, color, rect)

def _draw_fence(screen, offset_x):
    import pygame
    width = screen.get_width()
    fence_y = GROUND_Y - 50
    for shift in (0, width):
        x = offset_x + shift
        pygame.draw.rect(screen, (235, 235, 235), (x, fence_y, width, 5))
        pygame.draw.rect(screen, (210, 210, 210), (x, fence_y + 16, width, 4))
        post_spacing = 80
        for i in range(-1, width // post_spacing + 2):
            post_x = x + i * post_spacing
            pygame.draw.rect(screen, (230, 230, 230), (post_x, fence_y - 4, 6, 32))

def draw_label(screen, font, text, x, y, color):
    surf = font.render(text, True, color)
    screen.blit(surf, (x, y))
    return surf.get_width(), surf.get_height()

def draw_bar(screen, x, y, w, h, frac, fg, border=(0, 0, 0)):
    import pygame
    pygame.draw.rect(screen, border, (x, y, w, h), 2)
    fill_w = int((w - 4) * max(0.0, min(1.0, frac)))
    pygame.draw.rect(screen, fg, (x + 2, y + 2, fill_w, h - 4))

def _wrap_text(font, text, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# -----------------------------
# Pantalla de MENÚ INICIAL
# -----------------------------
def _menu_inicial(screen, clock, font, bigfont, progress) -> Tuple[Jinete, Caballo, str, bool]:
    """
    Devuelve: (jinete, caballo, clima, clima_aleatorio)
    """
    import pygame

    # Defaults desde progreso
    jinete_nombre = progress.get("last_player", "Oriana")
    caballo_nombre = progress.get("last_horse", "Luna")
    sexo = progress.get("last_horse_sex", "Yegua")
    last_breed = progress.get("last_horse_breed", "Pura Sangre")
    raza_idx = RAZAS.index(last_breed) if last_breed in RAZAS else 0
    clima_options = ["Aleatorio", "Soleado", "Lluvioso", "Ventoso", "Barro"]
    clima_idx = 0  # "Aleatorio" por default

    PANEL_PAD = 24
    GAP_X = 16
    GAP_Y = 18
    COLS = 2
    LINE_H = 44
    panel_w = min(int(WIDTH * 0.92), 940)
    panel_rect = pygame.Rect((WIDTH - panel_w) // 2, 80, panel_w, 360)
    COL_W = (panel_w - PANEL_PAD * 2 - GAP_X * (COLS - 1)) // COLS

    def col_x(i: int) -> int:
        return panel_rect.x + PANEL_PAD + i * (COL_W + GAP_X)

    def line_y(n: int) -> int:
        return panel_rect.y + PANEL_PAD + n * (LINE_H + GAP_Y)

    ARROW_W = 42
    ARROW_GAP = 8

    input_jinete = pygame.Rect(col_x(0), line_y(1), COL_W, 40)
    btn_clima_prev = pygame.Rect(col_x(1), line_y(1), ARROW_W, 40)
    clima_box_w = max(100, COL_W - ARROW_W * 2 - ARROW_GAP * 2)
    clima_box = pygame.Rect(btn_clima_prev.right + ARROW_GAP, line_y(1), clima_box_w, 40)
    btn_clima_next = pygame.Rect(clima_box.right + ARROW_GAP, line_y(1), ARROW_W, 40)

    input_caballo = pygame.Rect(col_x(0), line_y(3), COL_W, 40)
    sex_btn_w = (COL_W - GAP_X) // 2
    btn_sex_yegua = pygame.Rect(col_x(1), line_y(3), sex_btn_w, 38)
    btn_sex_macho = pygame.Rect(btn_sex_yegua.right + GAP_X, line_y(3), sex_btn_w, 38)

    raza_prev = pygame.Rect(col_x(0), line_y(5), ARROW_W, 38)
    raza_box_w = max(140, COL_W - ARROW_W * 2 - ARROW_GAP * 2)
    raza_box = pygame.Rect(raza_prev.right + ARROW_GAP, line_y(5), raza_box_w, 38)
    raza_next = pygame.Rect(raza_box.right + ARROW_GAP, line_y(5), ARROW_W, 38)

    BTN_W = min((COL_W - GAP_X) // 2, 220)
    btn_jugar = pygame.Rect(col_x(0), line_y(6), BTN_W, 44)
    btn_salir = pygame.Rect(btn_jugar.right + GAP_X, line_y(6), BTN_W, 44)

    history_entries = load_history()[-5:]
    history_lines = max(1, len(history_entries) + 1)
    history_block = history_lines * 18
    content_bottom = max(line_y(6) + LINE_H, line_y(5) + history_block)
    panel_rect.h = content_bottom - panel_rect.y + PANEL_PAD

    focused = None  # 'jinete' | 'caballo' | None
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None, "", True  # señal de salida
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if input_jinete.collidepoint(mx, my):
                    focused = 'jinete'
                elif input_caballo.collidepoint(mx, my):
                    focused = 'caballo'
                elif btn_sex_yegua.collidepoint(mx, my):
                    sexo = "Yegua"
                elif btn_sex_macho.collidepoint(mx, my):
                    sexo = "Macho"
                elif raza_prev.collidepoint(mx, my):
                    raza_idx = (raza_idx - 1) % len(RAZAS)
                elif raza_next.collidepoint(mx, my):
                    raza_idx = (raza_idx + 1) % len(RAZAS)
                elif btn_clima_prev.collidepoint(mx, my):
                    clima_idx = (clima_idx - 1) % len(clima_options)
                elif btn_clima_next.collidepoint(mx, my):
                    clima_idx = (clima_idx + 1) % len(clima_options)
                elif btn_jugar.collidepoint(mx, my):
                    # Validar
                    if not jinete_nombre.strip():
                        jinete_nombre = "Jinete"
                    if not caballo_nombre.strip():
                        caballo_nombre = "Luna"
                    # Construir objetos y salir
                    jinete = Jinete(jinete_nombre, experiencia=progress.get("exp", 1), puntos=progress.get("puntos", 0))
                    raza = RAZAS[raza_idx]
                    if raza == "Pura Sangre":
                        caballo = PuraSangre(caballo_nombre)
                    else:
                        caballo = Yegua(caballo_nombre)
                        caballo.raza = raza
                        if raza == "Criollo":
                            caballo.resistencia += 0.1
                        elif raza == "Árabe":
                            caballo.velocidad += 0.3
                        elif raza == "Cuarto de Milla":
                            caballo.velocidad += 0.4
                            caballo.resistencia -= 0.05
                        elif raza == "Percherón":
                            caballo.velocidad -= 0.4
                            caballo.resistencia += 0.2
                    caballo.raza = f"{raza} ({sexo})"
                    clima_aleatorio = clima_options[clima_idx] == "Aleatorio"
                    clima = random.choice(["Soleado", "Lluvioso", "Ventoso", "Barro"]) if clima_aleatorio else clima_options[clima_idx]
                    caballo.sexo = sexo
                    caballo.raza_base = raza
                    return jinete, caballo, clima, clima_aleatorio
                elif btn_salir.collidepoint(mx, my):
                    return None, None, "", True
                else:
                    focused = None

            if event.type == pygame.KEYDOWN:
                if focused == 'jinete':
                    if event.key == pygame.K_BACKSPACE:
                        jinete_nombre = jinete_nombre[:-1]
                    elif event.key == pygame.K_RETURN:
                        focused = None
                    else:
                        ch = event.unicode
                        if ch.isprintable() and len(jinete_nombre) < 20:
                            jinete_nombre += ch
                elif focused == 'caballo':
                    if event.key == pygame.K_BACKSPACE:
                        caballo_nombre = caballo_nombre[:-1]
                    elif event.key == pygame.K_RETURN:
                        focused = None
                    else:
                        ch = event.unicode
                        if ch.isprintable() and len(caballo_nombre) < 20:
                            caballo_nombre += ch
                else:
                    if event.key == pygame.K_ESCAPE:
                        return None, None, "", True

        # Render
        screen.fill(PINK_SOFT)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (255, 255, 255, 35), (WIDTH - 160, 140), 200)
        pygame.draw.circle(overlay, (255, 255, 255, 20), (160, HEIGHT - 140), 260)
        screen.blit(overlay, (0, 0))

        _title(screen, bigfont, "Equestrian Challenge")
        pygame.draw.rect(screen, (*SHADOW, 40), panel_rect.move(3, 3), border_radius=18)
        pygame.draw.rect(screen, PINK_SOFT, panel_rect, border_radius=18)
        pygame.draw.rect(screen, INK, panel_rect, 2, border_radius=18)

        label_font = font
        hint_font = pygame.font.SysFont(FONT_NAME, max(12, font.get_height() - 2))
        history_font = pygame.font.SysFont(FONT_NAME, 18)

        draw_label(screen, font, "Nombre del Jinete", col_x(0), line_y(0) - 20, INK)
        draw_label(screen, font, "Clima", col_x(1), line_y(0) - 20, INK)
        draw_label(screen, font, "Nombre del Caballo", col_x(0), line_y(2) - 20, INK)
        draw_label(screen, font, "Sexo del Caballo", col_x(1), line_y(2) - 20, INK)
        draw_label(screen, font, "Raza del Caballo", col_x(0), line_y(4) - 20, INK)
        draw_label(screen, font, "Últimos 5 jugadores", col_x(1), line_y(4) - 20, INK)

        _draw_input(screen, label_font, input_jinete, jinete_nombre, "Ej: Oriana", focused == 'jinete')
        _draw_input(screen, label_font, input_caballo, caballo_nombre, "Ej: Luna", focused == 'caballo')

        mx, my = pygame.mouse.get_pos()
        _draw_button(screen, label_font, btn_clima_prev, "◀", hovered=btn_clima_prev.collidepoint(mx, my))
        _draw_button(screen, label_font, btn_clima_next, "▶", hovered=btn_clima_next.collidepoint(mx, my))
        pygame.draw.rect(screen, PANEL_BG, clima_box, border_radius=10)
        pygame.draw.rect(screen, INK, clima_box, 2, border_radius=10)
        ctext = label_font.render(clima_options[clima_idx], True, INK)
        screen.blit(ctext, (clima_box.centerx - ctext.get_width() // 2,
                            clima_box.centery - ctext.get_height() // 2))

        _draw_button(screen, label_font, btn_sex_yegua, "Yegua",
                     hovered=btn_sex_yegua.collidepoint(mx, my), active=(sexo == "Yegua"))
        _draw_button(screen, label_font, btn_sex_macho, "Macho",
                     hovered=btn_sex_macho.collidepoint(mx, my), active=(sexo == "Macho"))

        _draw_button(screen, label_font, raza_prev, "◀", hovered=raza_prev.collidepoint(mx, my))
        _draw_button(screen, label_font, raza_next, "▶", hovered=raza_next.collidepoint(mx, my))
        pygame.draw.rect(screen, PANEL_BG, raza_box, border_radius=10)
        pygame.draw.rect(screen, INK, raza_box, 2, border_radius=10)
        raza_text = label_font.render(RAZAS[raza_idx], True, INK)
        screen.blit(raza_text, (raza_box.centerx - raza_text.get_width() // 2,
                                raza_box.centery - raza_text.get_height() // 2))

        hist_y = line_y(5)
        hist_entries = list(reversed(history_entries))
        if not hist_entries:
            hist_entries = []
        text_y = hist_y
        for entry in hist_entries:
            txt = f"{entry.get('jugador','?')} · {entry.get('caballo','?')} ({entry.get('raza','?')}) · {entry.get('tiempo','?')}s"
            for line in _wrap_text(history_font, txt, COL_W):
                screen.blit(history_font.render(line, True, INK), (col_x(1), text_y))
                text_y += 18

        _draw_button(screen, label_font, btn_jugar, "¡A la pista!", hovered=btn_jugar.collidepoint(mx, my), active=True)
        _draw_button(screen, label_font, btn_salir, "Salir", hovered=btn_salir.collidepoint(mx, my))

        hints = [
            "Pulsa ESPACIO repetidamente para acelerar durante la carrera.",
            "Podés cambiar clima y caballo antes de cada carrera."
        ]
        for i, hint in enumerate(hints):
            text = hint_font.render(hint, True, _color_lerp(THEME_TEXT, (255, 255, 255), 0.5))
            screen.blit(text, (panel_rect.x + PANEL_PAD, panel_rect.bottom + 12 + i * 20))

        pygame.display.flip()

# -----------------------------
# MODO CUIDADO entre carreras
# -----------------------------
def _modo_cuidado(screen, clock, font, bigfont, caballo: Caballo, jinete: Jinete) -> None:
    """
    Menú simple de cuidado: Alimentar, Cepillar, Descansar.
    Cada acción mejora stats y cuesta 'tickets' de cuidado.
    """
    import pygame

    tickets = 3  # usos entre carreras
    msg = ""
    btn_alimentar = pygame.Rect(160, 360, 180, 48)
    btn_cepillar  = pygame.Rect(390, 360, 180, 48)
    btn_descansar = pygame.Rect(620, 360, 180, 48)
    btn_seguir    = pygame.Rect(380, 430, 200, 48)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if btn_alimentar.collidepoint(mx, my) and tickets > 0:
                    caballo.recuperar_energia(20)
                    tickets -= 1
                    msg = "Alimentaste: +20 energía."
                elif btn_cepillar.collidepoint(mx, my) and tickets > 0:
                    caballo.resistencia = round(min(1.6, caballo.resistencia + 0.1), 2)
                    tickets -= 1
                    msg = "Cepillaste: +0.1 resistencia (máx 1.6)."
                elif btn_descansar.collidepoint(mx, my) and tickets > 0:
                    caballo.recuperar_energia(35)
                    tickets -= 1
                    msg = "Descansó: +35 energía."
                elif btn_seguir.collidepoint(mx, my):
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        # Render
        _gradient_rect(screen, _color_lerp(THEME_PRIMARY, (255, 255, 255), 0.6),
                       _color_lerp(THEME_SECONDARY, (255, 255, 255), 0.3),
                       (0, 0, WIDTH, HEIGHT))
        _title(screen, bigfont, "Modo Cuidado 🧴🪶")
        panel_rect = pygame.Rect(140, 120, 680, 280)
        _draw_card(screen, panel_rect, border=22)

        info = [
            f"Caballo: {caballo.nombre} ({caballo.raza})",
            f"Energía: {caballo.energia:.0f}%",
            f"Resistencia: {caballo.resistencia:.2f}",
            f"Tickets de cuidado: {tickets}",
            "Elegí una opción para preparar a tu caballo antes de la próxima carrera."
        ]
        y = panel_rect.y + 30
        for line in info:
            screen.blit(font.render(line, True, THEME_TEXT), (panel_rect.x + 30, y)); y += 28

        mx, my = pygame.mouse.get_pos()
        _draw_button(screen, font, btn_alimentar, "Alimentar", hovered=btn_alimentar.collidepoint(mx, my))
        _draw_button(screen, font, btn_cepillar, "Cepillar", hovered=btn_cepillar.collidepoint(mx, my))
        _draw_button(screen, font, btn_descansar, "Descansar", hovered=btn_descansar.collidepoint(mx, my))
        _draw_button(screen, font, btn_seguir, "Volver al menú", hovered=btn_seguir.collidepoint(mx, my), active=True)

        if msg:
            tip_font = pygame.font.SysFont(FONT_NAME, font.get_height())
            screen.blit(tip_font.render(msg, True, (30, 120, 50)), (panel_rect.x + 30, panel_rect.bottom - 40))

        pygame.display.flip()

# -----------------------------
# PAUSA en carrera
# -----------------------------
def _pausa(screen, clock, font, bigfont) -> bool:
    """
    Devuelve True si se continúa, False si se sale al menú.
    """
    import pygame
    btn_cont = pygame.Rect(320, 260, 140, 48)
    btn_menu = pygame.Rect(500, 260, 140, 48)

    paused = True
    while paused:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if btn_cont.collidepoint(mx, my):
                    return True
                if btn_menu.collidepoint(mx, my):
                    return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True

        _gradient_rect(screen, _color_lerp(THEME_PRIMARY, (255, 255, 255), 0.65),
                       _color_lerp(THEME_SECONDARY, (255, 255, 255), 0.4),
                       (0, 0, WIDTH, HEIGHT))
        _title(screen, bigfont, "Pausa ⏸")
        _draw_card(screen, pygame.Rect(260, 200, 440, 140), border=24)
        mx, my = pygame.mouse.get_pos()
        _draw_button(screen, font, btn_cont, "Continuar", hovered=btn_cont.collidepoint(mx, my), active=True)
        _draw_button(screen, font, btn_menu, "Menú", hovered=btn_menu.collidepoint(mx, my))
        pygame.display.flip()

# -----------------------------
# CARRERA (loop del juego)
# -----------------------------
def _carrera(screen, clock, font, hudfont, caballo: Caballo, jinete: Jinete, clima: str, progress) -> Tuple[str, bool, float, List[Dict[str, float]]]:
    import pygame

    settings = CLIMATE_SETTINGS.get(clima, {"friction": 0.97, "regen": 1.0})
    friction = settings["friction"]
    regen_factor = settings["regen"]

    caballo.energia = max(30.0, caballo.energia)  # asegura que la segunda carrera no arranque sin energía
    base_player_speed = caballo.velocidad * caballo.bonificacion_terreno(clima)
    agua = 2
    race_time = 0.0
    perf_samples: List[Dict[str, float]] = []
    won = False
    ranking: List[Dict[str, object]] = []
    bg_t = 0.0
    camera_x = 0.0
    tap_meter = 0.0
    tap_combo = 0
    TAP_GAIN = 0.18
    TAP_DECAY = 0.75
    COMBO_DECAY = 1.6
    TAP_ENERGY_COST = 4.0

    opponent_pool = [
        ("Centella", PuraSangre),
        ("Aurora", Yegua),
        ("Relampago", PuraSangre),
        ("Canela", Yegua),
        ("Orion", PuraSangre),
        ("Bruma", Yegua),
    ]
    random.shuffle(opponent_pool)
    opponents = []
    for name, cls in opponent_pool:
        if len(opponents) >= 3:
            break
        opponents.append(cls(name))

    colors = [
        ((168, 110, 70), (130, 84, 46), (60, 90, 170)),
        ((120, 90, 70), (90, 62, 54), (150, 70, 120)),
        ((150, 96, 96), (110, 70, 70), (90, 130, 80)),
        ((140, 118, 70), (100, 88, 56), (110, 80, 150)),
    ]

    player_state = {
        "caballo": caballo,
        "dist": 0.0,
        "speed": 0.0,
        "is_player": True,
        "name": caballo.nombre,
        "body_color": (130, 92, 54),
        "accent_color": (95, 72, 46),
        "rider_color": (60, 100, 190),
        "base_speed": base_player_speed,
        "phase": 0.0,
        "lane": 0,
        "scale": 1.05,
        "tap_meter": 0.0,
        "combo": 0.0,
    }

    ai_states: List[Dict[str, object]] = []
    for idx, opp in enumerate(opponents):
        base = opp.velocidad * opp.bonificacion_terreno(clima)
        palette = colors[idx % len(colors)]
        scale = max(0.78, 1.0 - 0.08 * (idx + 1))
        ai_states.append({
            "caballo": opp,
            "dist": 0.0,
            "speed": 0.0,
            "is_player": False,
            "name": opp.nombre,
            "body_color": palette[0],
            "accent_color": palette[1],
            "rider_color": palette[2],
            "base_speed": base + random.uniform(-0.25, 0.6),
            "phase": random.uniform(0, math.tau),
            "lane": idx + 1,
            "scale": scale,
            "tap_meter": random.uniform(0.1, 0.3),
            "tap_rate": random.uniform(2.4, 3.4),
            "tap_gain": random.uniform(0.15, 0.22),
            "tap_decay": random.uniform(0.6, 0.9),
            "combo": 0.0,
        })

    competitors = [player_state] + ai_states
    lane_count = len(competitors)
    lane_spacing = 32

    help_lines = [
        "Controles: ESPACIO (tap) acelera | H Agua | P Pausa | ESC Salir",
        "Cuanto más preciso el ritmo de pulsos, mayor velocidad.",
    ]

    def world_to_screen(dist: float) -> int:
        return int(140 + (dist - camera_x) * PIXELS_PER_METER)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        race_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", False, race_time, perf_samples
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu", False, race_time, perf_samples
                elif event.key == pygame.K_SPACE:
                    tap_meter = min(1.0, tap_meter + TAP_GAIN)
                    tap_combo = min(10, tap_combo + 1)
                    caballo.consumir_energia(TAP_ENERGY_COST)
                elif event.key == pygame.K_h and agua > 0 and caballo.energia < 100:
                    caballo.recuperar_energia(20)
                    agua -= 1
                elif event.key == pygame.K_p:
                    if not _pausa(screen, clock, font, pygame.font.SysFont(FONT_NAME, 36, bold=True)):
                        return False, race_time, perf_samples

        if not running:
            break

        tap_meter = max(0.0, tap_meter - TAP_DECAY * dt)
        tap_combo = max(0.0, tap_combo - COMBO_DECAY * dt)
        player_state["tap_meter"] = tap_meter
        player_state["combo"] = tap_combo

        if caballo.energia < 100 and tap_meter < 0.4:
            caballo.recuperar_energia(5.0 * dt * regen_factor)

        combo_bonus = min(0.35, tap_combo * 0.03)
        speed_factor = 0.55 + tap_meter * 1.35 + combo_bonus
        energy_factor = 0.5 + 0.5 * (caballo.energia / 100.0)
        target_speed = player_state["base_speed"] * speed_factor
        player_speed = max(0.0, target_speed * energy_factor) * friction
        player_state["speed"] = player_speed
        player_state["dist"] += player_speed * dt * 10.0
        player_state["phase"] = (player_state["phase"] + dt * (player_speed + 12) * 0.085) % math.tau
        current_speed = player_speed
        bg_t += current_speed * dt * BG_PX_PER_M

        for state in ai_states:
            horse: Caballo = state["caballo"]  # type: ignore[assignment]
            tap_meter_ai = max(0.0, state["tap_meter"] - state["tap_decay"] * dt)  # type: ignore[index]
            if random.random() < (state["tap_rate"] + (0.8 if GOAL_DISTANCE - state["dist"] < 260 else 0)) * dt:  # type: ignore[index]
                tap_meter_ai = min(1.0, tap_meter_ai + state["tap_gain"])  # type: ignore[index]
                horse.consumir_energia(TAP_ENERGY_COST * random.uniform(0.7, 1.1))
                state["combo"] = min(10.0, state["combo"] + 1.0)
            else:
                state["combo"] = max(0.0, state["combo"] - COMBO_DECAY * dt)
            state["tap_meter"] = tap_meter_ai

            if horse.energia < 100 and tap_meter_ai < 0.4:
                horse.recuperar_energia(4.5 * dt * regen_factor * 0.9)

            combo_bonus_ai = min(0.35, state["combo"] * 0.03)  # type: ignore[index]
            speed_factor_ai = 0.55 + tap_meter_ai * 1.35 + combo_bonus_ai
            energy_factor_ai = 0.5 + 0.5 * (horse.energia / 100.0)
            speed = max(0.0, state["base_speed"] * speed_factor_ai * energy_factor_ai) * friction  # type: ignore[index]
            state["speed"] = speed
            state["dist"] += speed * dt * 10.0
            state["phase"] = (state["phase"] + dt * (speed + 10) * 0.08) % math.tau

        if not perf_samples or race_time - perf_samples[-1]["t"] >= 0.2:
            perf_samples.append({
                "t": round(race_time, 2),
                "vel": round(player_state["speed"], 2),
                "eng": round(caballo.energia, 2)
            })

        finished = [s for s in competitors if s["dist"] >= GOAL_DISTANCE]
        if finished:
            ranking = sorted(competitors, key=lambda s: s["dist"], reverse=True)
            won = ranking[0]["is_player"]  # type: ignore[index]
            running = False

        camera_target = max(player_state["dist"] - 300, 0.0)
        camera_x += (camera_target - camera_x) * min(1.0, dt * 3.2)

        sky_color = (180, 220, 255) if clima in ("Soleado", "Ventoso") else (140, 170, 200)
        screen.fill(sky_color)
        width = screen.get_width()
        far_x = -int((bg_t * PARALLAX_FAR) % width)
        mid_x = -int((bg_t * PARALLAX_MID) % width)
        near_x = -int((bg_t * PARALLAX_NEAR) % width)
        _draw_band(screen, far_x, 140, (150, 180, 210), GROUND_Y - 200)
        _draw_band(screen, mid_x, 90, (120, 190, 130), GROUND_Y - 120)
        _draw_fence(screen, near_x)

        track_top = GROUND_Y - 80
        grass_top = track_top - 70
        pygame.draw.rect(screen, (96, 150, 88), (0, grass_top, WIDTH, 70))
        pygame.draw.rect(screen, (184, 140, 96), (0, track_top, WIDTH, HEIGHT - track_top))
        pygame.draw.rect(screen, (160, 120, 80), (0, GROUND_Y - 18, WIDTH, 18))

        mark_spacing = 82
        mark_offset = int((bg_t * PARALLAX_NEAR) % mark_spacing)
        mark_y = GROUND_Y - 28
        for x in range(-mark_spacing, WIDTH + mark_spacing, mark_spacing):
            px = x - mark_offset
            pygame.draw.rect(screen, (190, 150, 110), (px, mark_y, 32, 5))

        player_ratio = min(1.0, player_state["dist"] / GOAL_DISTANCE)
        goal_screen_x = WIDTH - int(player_ratio * WIDTH)
        if -40 <= goal_screen_x <= WIDTH + 60:
            pygame.draw.rect(screen, WHITE, (goal_screen_x, GROUND_Y - 130, 18, 90))
            for stripe in range(0, 90, 12):
                color = BLACK if (stripe // 12) % 2 == 0 else WHITE
                pygame.draw.rect(screen, color, (goal_screen_x, GROUND_Y - 130 + stripe, 18, 12))

        live_ranking = sorted(competitors, key=lambda s: s["dist"], reverse=True)

        draw_order = sorted(competitors, key=lambda s: s.get("lane", 0), reverse=True)
        for state in draw_order:
            lane_idx = state.get("lane", 0)
            base_y = GROUND_Y - lane_idx * lane_spacing
            screen_x = world_to_screen(state["dist"])
            scale = state.get("scale", 1.0)
            bob = math.sin(state.get("phase", 0.0)) * 4 * scale

            if screen_x < -120 or screen_x > WIDTH + 200:
                continue

            shadow_w = int(64 * scale)
            shadow_h = int(18 * scale)
            shadow_surface = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, 90), shadow_surface.get_rect())
            screen.blit(shadow_surface, (screen_x - shadow_w // 2, base_y - shadow_h // 2 + 10))

            if state["is_player"]:
                boost_level = min(1.0, player_state["tap_meter"] + player_state["combo"] * 0.05)
            else:
                boost_level = min(1.0, state.get("tap_meter", 0.0) + state.get("combo", 0.0) * 0.05)
            _draw_horse_sprite(
                screen,
                screen_x,
                base_y,
                scale,
                state["body_color"],
                state["accent_color"],
                state["rider_color"],
                state["phase"],
                bob,
                state["is_player"],  # type: ignore[arg-type]
                boost_level,
            )

            name_label = f"{state['name']}" + (" (vos)" if state["is_player"] else "")
            screen.blit(font.render(name_label, True, BLACK), (screen_x - 40, base_y - int(70 * scale)))

        player_dist = min(GOAL_DISTANCE, player_state["dist"])
        positions_to_show = min(6, len(live_ranking))
        panel_height = 150 + positions_to_show * 18
        panel_rect = pygame.Rect(12, 8, WIDTH - 24, panel_height)
        pygame.draw.rect(screen, (*SHADOW, 40), panel_rect.move(2, 2), border_radius=12)
        pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(screen, INK, panel_rect, 2, border_radius=12)
        PAD = 12
        LEFT_X = panel_rect.x + PAD
        RIGHT_X = panel_rect.x + panel_rect.w // 2 + PAD
        COL_WIDTH = panel_rect.w // 2 - PAD * 2

        def draw_wrapped(text, x, y, max_width, color=INK):
            lines = _wrap_text(hudfont, text, max_width)
            if not lines:
                lines = [text]
            offset = 0
            for line in lines:
                _, h = draw_label(screen, hudfont, line, x, y + offset, color)
                offset += h + 2
            return offset

        left_y = panel_rect.y + PAD
        left_y += draw_wrapped(f"Jinete: {jinete.nombre}", LEFT_X, left_y, COL_WIDTH)
        left_y += draw_wrapped(f"Puntos: {jinete.puntos}", LEFT_X, left_y, COL_WIDTH)
        left_y += draw_wrapped(f"Caballo: {caballo.nombre} ({getattr(caballo, 'raza', 'Yegua')})", LEFT_X, left_y, COL_WIDTH)
        left_y += 4
        draw_label(screen, hudfont, "Energía", LEFT_X, left_y, INK); left_y += 18
        draw_bar(screen, LEFT_X, left_y, min(260, COL_WIDTH), 18, caballo.energia / 100.0, GREEN); left_y += 26
        draw_label(screen, hudfont, "Ritmo (ESPACIO)", LEFT_X, left_y, INK); left_y += 18
        draw_bar(screen, LEFT_X, left_y, min(260, COL_WIDTH), 18, min(1.0, tap_meter),
                 _color_lerp(PINK, PINK_DARK, 0.3)); left_y += 26
        draw_wrapped(f"Agua (H): {agua}", LEFT_X, left_y, COL_WIDTH, THEME_MUTED)

        right_y = panel_rect.y + PAD
        for text in (
            f"Clima: {clima}",
            f"Tiempo: {race_time:5.1f}s",
            f"Distancia: {player_dist:5.0f}/{int(GOAL_DISTANCE)} m",
            f"Velocidad: {current_speed:4.1f} m/s",
        ):
            draw_wrapped(text, RIGHT_X, right_y, COL_WIDTH, INK)
            right_y += 22

        right_y += 6
        draw_label(screen, hudfont, "Posiciones en pista", RIGHT_X, right_y, INK)
        right_y += 22
        for idx, state in enumerate(live_ranking[:positions_to_show]):
            entry = f"{idx + 1}. {state['name']}"
            color = INK if state["is_player"] else THEME_MUTED
            right_y += draw_wrapped(entry, RIGHT_X, right_y, COL_WIDTH, color)

        progress_rect = pygame.Rect(panel_rect.x + PAD, panel_rect.bottom - 24, panel_rect.w - PAD * 2, 10)
        pygame.draw.rect(screen, (220, 225, 235), progress_rect.inflate(4, 4), border_radius=6)
        progress_fill = int(progress_rect.w * (player_dist / GOAL_DISTANCE))
        pygame.draw.rect(screen, PINK, (progress_rect.x, progress_rect.y, progress_fill, progress_rect.h), border_radius=6)

        info_panel = pygame.Rect(16, panel_rect.bottom + 18, WIDTH - 32, 80)
        pygame.draw.rect(screen, PANEL_BG, info_panel, border_radius=12)
        pygame.draw.rect(screen, INK, info_panel, 2, border_radius=12)
        for i, hl in enumerate(help_lines):
            draw_label(screen, hudfont, hl, info_panel.x + 20, info_panel.y + 18 + i * 24,
                       _color_lerp(INK, (255, 255, 255), 0.15))

        pygame.display.flip()

    if ranking:
        progress["last_ranking"] = [
            f"{idx + 1}. {state['name']}" + (" (vos)" if state["is_player"] else "")
            for idx, state in enumerate(ranking)
        ]
    else:
        progress["last_ranking"] = []

    return "done", won, race_time, perf_samples

# -----------------------------
# Entry principal
# -----------------------------
def run_game():
    if not _ensure_pygame():
        return
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Equestrian Challenge 🐎")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, 22)
    bigfont = pygame.font.SysFont(FONT_NAME, 44, bold=True)
    hudfont = pygame.font.SysFont(FONT_NAME, 20)

    exit_game = False
    while not exit_game:
        # --- MENÚ INICIAL ---
        progress = cargar_progreso()
        menu = _menu_inicial(screen, clock, font, bigfont, progress)
        if menu == (None, None, "", True):
            exit_game = True
            break
        jinete, caballo, clima, clima_aleatorio = menu

        # --- CARRERA ---
        try:
            status, won, race_time, perf_samples = _carrera(screen, clock, font, hudfont, caballo, jinete, clima, progress)
        except Exception as exc:  # pragma: no cover - seguridad en runtime
            import traceback
            traceback.print_exc()
            # Espera breve para que el usuario pueda leer el error en consola antes de continuar
            pygame.time.wait(1200)
            continue
        if status == "quit":
            exit_game = True
            break
        if status == "menu":
            continue

        # --- ACTUALIZAR PROGRESO ---
        best_time = progress.get("best_time", None)
        if won:
            jinete.puntos += 100
            if best_time is None or race_time < best_time:
                best_time = round(race_time, 2)

        perf_history = perf_samples[-240:] if len(perf_samples) > 240 else perf_samples

        progress.update({
            "last_player": jinete.nombre,
            "last_horse": caballo.nombre,
            "last_horse_type": "PuraSangre" if isinstance(caballo, PuraSangre) else "Yegua",
            "last_horse_sex": getattr(caballo, "sexo", "Yegua"),
            "last_horse_breed": getattr(caballo, "raza_base", "Pura Sangre"),
            "exp": jinete.experiencia,
            "puntos": jinete.puntos,
            "best_time": best_time,
            "last_climate": clima,
            "last_race_perf": perf_history
        })
        guardar_progreso(progress)

        # Gráfico rendimiento
        guardar_grafico_performance(perf_history)
        append_history({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "jugador": jinete.nombre,
            "puntos": jinete.puntos,
            "caballo": caballo.nombre,
            "sexo": progress.get("last_horse_sex", getattr(caballo, "sexo", "Yegua")),
            "raza": progress.get("last_horse_breed", getattr(caballo, "raza_base", getattr(caballo, "raza", "Yegua"))),
            "clima": clima,
            "tiempo": round(race_time, 2),
            "gano": bool(won)
        })

        # --- PANTALLA RESULTADO ---
        result_running = True
        quit_from_results = False
        btn_nueva = pygame.Rect(250, 380, 200, 50)
        btn_cuidado = pygame.Rect(480, 380, 230, 50)
        msg = "🏆 ¡Ganaste!" if won else "Carrera terminada."
        while result_running:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_from_results = True
                    result_running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if btn_nueva.collidepoint(mx, my):
                        result_running = False   # vuelve al menú
                    elif btn_cuidado.collidepoint(mx, my):
                        _modo_cuidado(screen, clock, font, bigfont, caballo, jinete)
                        result_running = False   # vuelve al menú post-cuidado
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    result_running = False

            screen.fill((250, 250, 250))
            _title(screen, bigfont, msg)
            ranking_lines = progress.get("last_ranking", [])
            stats = [
                f"Tiempo: {race_time:.2f}s",
                f"Mejor tiempo: {best_time if best_time else '—'}",
                "Se generó performance_last_race.png (si tenés matplotlib).",
            ]
            if ranking_lines:
                stats.append("Clasificación:")
                stats.extend(ranking_lines)
            stats.append("Elegí: nueva carrera o modo cuidado.")
            y = 160
            for s in stats:
                screen.blit(font.render(s, True, DARK), ( (WIDTH-700)//2, y)); y += 28

            mx, my = pygame.mouse.get_pos()
            _draw_button(screen, font, btn_nueva, "Nueva carrera", hovered=btn_nueva.collidepoint(mx, my), active=True)
            _draw_button(screen, font, btn_cuidado, "Modo Cuidado 🧴", hovered=btn_cuidado.collidepoint(mx, my))
            pygame.display.flip()
        if quit_from_results:
            exit_game = True
            break
    pygame.quit()
