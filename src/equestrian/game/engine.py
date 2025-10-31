import random
from typing import List, Dict, Tuple, Optional

from equestrian.domain.caballo import Caballo, Yegua, PuraSangre
from equestrian.domain.jinete import Jinete
from equestrian.services.persistence import cargar_progreso, guardar_progreso
from equestrian.services.performance import guardar_grafico_performance

# --- Ajustes del juego ---
WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = HEIGHT - 90
GOAL_DISTANCE = 2000.0  # metros virtuales para ganar

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

def _draw_button(screen, font, rect, label, hovered=False, active=False):
    import pygame
    bg = (245, 245, 245) if hovered else (235, 235, 235)
    if active:
        bg = (210, 230, 255)
    pygame.draw.rect(screen, bg, rect, border_radius=8)
    pygame.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=8)
    text = font.render(label, True, BLACK)
    screen.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                       rect.y + (rect.h - text.get_height()) // 2))

def _draw_input(screen, font, rect, value, placeholder="", focused=False):
    import pygame
    bg = WHITE if focused else (248, 248, 248)
    pygame.draw.rect(screen, bg, rect, border_radius=6)
    pygame.draw.rect(screen, (170, 170, 170), rect, 2, border_radius=6)
    txt = value if value else placeholder
    col = BLACK if value else (140, 140, 140)
    render = font.render(txt, True, col)
    screen.blit(render, (rect.x + 10, rect.y + (rect.h - render.get_height()) // 2))

def _title(screen, bigfont, text, y=30):
    import pygame
    t = bigfont.render(text, True, DARK)
    screen.blit(t, ( (screen.get_width()-t.get_width())//2, y))

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
    caballo_tipo = progress.get("last_horse_type", "Yegua")
    clima_options = ["Aleatorio", "Soleado", "Lluvioso", "Ventoso", "Barro"]
    clima_idx = 0  # "Aleatorio" por default

    # Inputs y botones
    input_jinete = pygame.Rect(300, 150, 360, 40)
    input_caballo = pygame.Rect(300, 210, 360, 40)
    btn_yegua = pygame.Rect(300, 270, 160, 42)
    btn_pura = pygame.Rect(500, 270, 160, 42)
    btn_clima_prev = pygame.Rect(300, 330, 42, 42)
    btn_clima_next = pygame.Rect(618, 330, 42, 42)
    clima_box = pygame.Rect(350, 330, 260, 42)
    btn_jugar = pygame.Rect(300, 410, 220, 48)
    btn_salir = pygame.Rect(540, 410, 120, 48)

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
                elif btn_yegua.collidepoint(mx, my):
                    caballo_tipo = "Yegua"
                elif btn_pura.collidepoint(mx, my):
                    caballo_tipo = "PuraSangre"
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
                    caballo = PuraSangre(caballo_nombre) if caballo_tipo == "PuraSangre" else Yegua(caballo_nombre)
                    clima_aleatorio = clima_options[clima_idx] == "Aleatorio"
                    clima = random.choice(["Soleado", "Lluvioso", "Ventoso", "Barro"]) if clima_aleatorio else clima_options[clima_idx]
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
        screen.fill(LIGHT)
        _title(screen, bigfont, "Equestrian Challenge 🐎")

        # Etiquetas
        label1 = font.render("Nombre del Jinete", True, DARK)
        label2 = font.render("Nombre del Caballo", True, DARK)
        label3 = font.render("Tipo de Caballo", True, DARK)
        label4 = font.render("Clima", True, DARK)

        screen.blit(label1, (input_jinete.x, input_jinete.y - 24))
        screen.blit(label2, (input_caballo.x, input_caballo.y - 24))
        screen.blit(label3, (btn_yegua.x, btn_yegua.y - 24))
        screen.blit(label4, (clima_box.x, clima_box.y - 24))

        _draw_input(screen, font, input_jinete, jinete_nombre, "Ej: Oriana", focused == 'jinete')
        _draw_input(screen, font, input_caballo, caballo_nombre, "Ej: Luna", focused == 'caballo')

        mx, my = pygame.mouse.get_pos()
        _draw_button(screen, font, btn_yegua, "Yegua",
                     hovered=btn_yegua.collidepoint(mx, my),
                     active=(caballo_tipo == "Yegua"))
        _draw_button(screen, font, btn_pura, "Pura Sangre",
                     hovered=btn_pura.collidepoint(mx, my),
                     active=(caballo_tipo == "PuraSangre"))

        # Clima selector
        _draw_button(screen, font, btn_clima_prev, "<", hovered=btn_clima_prev.collidepoint(mx, my))
        _draw_button(screen, font, btn_clima_next, ">", hovered=btn_clima_next.collidepoint(mx, my))
        pygame.draw.rect(screen, WHITE, clima_box, border_radius=6)
        pygame.draw.rect(screen, (170,170,170), clima_box, 2, border_radius=6)
        ctext = font.render(clima_options[clima_idx], True, DARK)
        screen.blit(ctext, (clima_box.centerx - ctext.get_width()//2, clima_box.centery - ctext.get_height()//2))

        _draw_button(screen, font, btn_jugar, "JUGAR", hovered=btn_jugar.collidepoint(mx, my), active=True)
        _draw_button(screen, font, btn_salir, "Salir", hovered=btn_salir.collidepoint(mx, my))

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
        screen.fill((245, 245, 255))
        _title(screen, bigfont, "Modo Cuidado 🧴🪶")
        info = [
            f"Caballo: {caballo.nombre} ({caballo.raza})",
            f"Energía: {caballo.energia:.0f}%",
            f"Resistencia: {caballo.resistencia:.2f}",
            f"Tickets de cuidado: {tickets}",
            "Elegí una opción para preparar a tu caballo para la próxima carrera."
        ]
        y = 140
        for line in info:
            screen.blit(font.render(line, True, DARK), (160, y)); y += 28

        mx, my = pygame.mouse.get_pos()
        _draw_button(screen, font, btn_alimentar, "Alimentar", hovered=btn_alimentar.collidepoint(mx, my))
        _draw_button(screen, font, btn_cepillar, "Cepillar", hovered=btn_cepillar.collidepoint(mx, my))
        _draw_button(screen, font, btn_descansar, "Descansar", hovered=btn_descansar.collidepoint(mx, my))
        _draw_button(screen, font, btn_seguir, "Seguir ▶", hovered=btn_seguir.collidepoint(mx, my), active=True)

        if msg:
            screen.blit(font.render(msg, True, (20, 120, 20)), (160, 320))

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

        screen.fill((250, 250, 250))
        _title(screen, bigfont, "Pausa ⏸")
        mx, my = pygame.mouse.get_pos()
        _draw_button(screen, font, btn_cont, "Continuar", hovered=btn_cont.collidepoint(mx, my), active=True)
        _draw_button(screen, font, btn_menu, "Menú", hovered=btn_menu.collidepoint(mx, my))
        pygame.display.flip()

# -----------------------------
# CARRERA (loop del juego)
# -----------------------------
def _carrera(screen, clock, font, caballo: Caballo, jinete: Jinete, clima: str, progress) -> Tuple[bool, float, List[Dict[str, float]]]:
    import pygame

    horse_rect = pygame.Rect(120, GROUND_Y - 48, 72, 48)
    y_vel = 0.0
    gravity = 0.9
    jump_impulse = -15.5

    obstacles: List[pygame.Rect] = []
    last_spawn = 0.0
    spawn_interval = random.uniform(1.2, 2.1)

    dist = 0.0
    race_time = 0.0
    base_speed = caballo.velocidad * caballo.bonificacion_terreno(clima)
    perf_samples: List[Dict[str, float]] = []
    best_time = progress.get("best_time", None)

    if clima == "Soleado":
        friction = 0.98; obstacle_bias = 0.0
    elif clima == "Lluvioso":
        friction = 0.95; obstacle_bias = 0.15
    elif clima == "Ventoso":
        friction = 0.97; obstacle_bias = 0.10
    else:
        friction = 0.93; obstacle_bias = 0.20

    running = True
    won = False
    agua = 2
    help_lines = [
        "Controles: ←/→ Ritmo | ESPACIO Salto | SHIFT Esprint (consume) | H Hidratar | P Pausa | ESC Salir",
    ]

    while running:
        dt = clock.tick(FPS) / 1000.0
        race_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_h and agua > 0 and caballo.energia < 100:
                    caballo.recuperar_energia(15); agua -= 1
                elif event.key == pygame.K_p:
                    if not _pausa(screen, clock, font, pygame.font.SysFont("Arial", 36)):
                        # salir a menú
                        return False, race_time, perf_samples

        keys = pygame.key.get_pressed()

        # Ritmo
        target_speed = base_speed
        if keys[pygame.K_RIGHT]: target_speed += 1.0
        if keys[pygame.K_LEFT]:  target_speed -= 1.0

        # Esprint
        sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if sprinting and caballo.energia > 0:
            target_speed += 2.5
            caballo.consumir_energia(15 * dt)
        else:
            caballo.recuperar_energia(4 * dt)

        # Penal por energía
        energy_factor = 0.5 + 0.5 * (caballo.energia / 100.0)
        current_speed = max(0.0, target_speed * energy_factor)
        current_speed *= friction

        # Salto
        if keys[pygame.K_SPACE] and abs(horse_rect.bottom - GROUND_Y) < 1e-3:
            y_vel = jump_impulse
            caballo.consumir_energia(5)

        # Gravedad
        y_vel += gravity
        horse_rect.y += int(y_vel)
        if horse_rect.bottom >= GROUND_Y:
            horse_rect.bottom = GROUND_Y; y_vel = 0.0

        # Distancia
        dist += current_speed * dt * 10.0

        # Obstáculos
        last_spawn += dt
        intervalo_actual = max(0.9, spawn_interval - obstacle_bias)
        if last_spawn >= intervalo_actual:
            last_spawn = 0.0
            spawn_interval = random.uniform(1.0, 2.0)
            h = random.choice([36, 48, 60])
            w = random.choice([30, 40])
            y = GROUND_Y - h
            obstacles.append(pygame.Rect(WIDTH + random.randint(0, 40), y, w, h))

        for obs in list(obstacles):
            obs.x -= int(300 * dt)
            if obs.right < 0:
                obstacles.remove(obs)
            elif horse_rect.colliderect(obs):
                caballo.consumir_energia(25)
                dist = max(0.0, dist - 15.0)
                horse_rect.x = max(80, horse_rect.x - 20)
                obstacles.remove(obs)

        # Samples rendimiento
        if not perf_samples or race_time - perf_samples[-1]["t"] >= 0.2:
            perf_samples.append({"t": round(race_time, 2), "vel": round(current_speed, 2), "eng": round(caballo.energia, 2)})

        # Victoria
        if dist >= GOAL_DISTANCE:
            won = True; running = False

        # ---- Render ----
        screen.fill((180, 220, 255) if clima in ("Soleado", "Ventoso") else (140, 170, 200))
        import pygame
        pygame.draw.rect(screen, BROWN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))  # suelo
        meta_x = WIDTH - int((dist / GOAL_DISTANCE) * WIDTH)
        pygame.draw.rect(screen, YELLOW, (meta_x, GROUND_Y - 120, 10, 120))       # meta

        for obs in obstacles:
            pygame.draw.rect(screen, GRAY, obs)
        pygame.draw.rect(screen, BLUE, horse_rect)  # caballo

        # HUD
        def draw_text(txt, x, y, color=BLACK):
            screen.blit(font.render(txt, True, color), (x, y))

        draw_text(f"Jinete: {jinete.nombre} | Exp: {jinete.experiencia} | Puntos: {jinete.puntos}", 16, 12)
        draw_text(f"Caballo: {caballo.nombre} ({caballo.raza})  Clima: {clima}", 16, 36)
        draw_text(f"Tiempo: {race_time:5.1f}s  Distancia: {min(dist, GOAL_DISTANCE):.0f}/{int(GOAL_DISTANCE)} m", 16, 60)
        draw_text(f"Velocidad: { (perf_samples[-1]['vel'] if perf_samples else 0):4.1f} m/s  Agua(H): {agua}", 16, 84)

        # Barra de energía
        bar_w = 240
        energy_w = int(bar_w * (caballo.energia / 100.0))
        pygame.draw.rect(screen, BLACK, (16, 110, bar_w + 4, 20), 2)
        pygame.draw.rect(screen, GREEN if caballo.energia >= 35 else RED, (18, 112, energy_w, 16))

        # Ayuda
        y0 = 146
        for hl in help_lines:
            draw_text(hl, 16, y0, (30,30,30)); y0 += 20

        pygame.display.flip()

    # Guardado (si terminó por victoria o ESC)
    return won, race_time, perf_samples

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
    font = pygame.font.SysFont("Arial", 20)
    bigfont = pygame.font.SysFont("Arial", 36, bold=True)

    while True:
        # --- MENÚ INICIAL ---
        progress = cargar_progreso()
        menu = _menu_inicial(screen, clock, font, bigfont, progress)
        if menu == (None, None, "", True):
            # usuario cerró/salió
            pygame.quit()
            return
        jinete, caballo, clima, clima_aleatorio = menu

        # --- CARRERA ---
        won, race_time, perf_samples = _carrera(screen, clock, font, caballo, jinete, clima, progress)

        # --- ACTUALIZAR PROGRESO ---
        best_time = progress.get("best_time", None)
        if won:
            jinete.puntos += 100
            if best_time is None or race_time < best_time:
                best_time = round(race_time, 2)

        progress.update({
            "last_player": jinete.nombre,
            "last_horse": caballo.nombre,
            "last_horse_type": caballo.raza if caballo.raza in ("Yegua", "Pura Sangre") else "Yegua",
            "exp": jinete.experiencia,
            "puntos": jinete.puntos,
            "best_time": best_time,
            "last_climate": clima,
            "last_race_perf": perf_samples
        })
        guardar_progreso(progress)

        # Gráfico rendimiento
        guardar_grafico_performance(perf_samples)

        # --- PANTALLA RESULTADO ---
        result_running = True
        btn_nueva = pygame.Rect(250, 380, 200, 50)
        btn_cuidado = pygame.Rect(480, 380, 230, 50)
        msg = "🏆 ¡Ganaste!" if won else "Carrera terminada."
        while result_running:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
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
            stats = [
                f"Tiempo: {race_time:.2f}s",
                f"Mejor tiempo: {best_time if best_time else '—'}",
                "Se generó performance_last_race.png (si tenés matplotlib).",
                "Elegí: nueva carrera o modo cuidado."
            ]
            y = 160
            for s in stats:
                screen.blit(font.render(s, True, DARK), ( (WIDTH-700)//2, y)); y += 28

            mx, my = pygame.mouse.get_pos()
            _draw_button(screen, font, btn_nueva, "Nueva carrera", hovered=btn_nueva.collidepoint(mx, my), active=True)
            _draw_button(screen, font, btn_cuidado, "Modo Cuidado 🧴", hovered=btn_cuidado.collidepoint(mx, my))
            pygame.display.flip()

