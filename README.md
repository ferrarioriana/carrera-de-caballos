# Equestrian Challenge 🐎

Trabajo práctico integrador para **Programación III (Prof. Natalia S. Cerdá)**.  
Construimos un simulador de carreras ecuestres en Python que pone en práctica:
POO con herencia, módulos nativos/extras, CRUD completo, interfaz gráfica en
Pygame y documentación enfocada en buenas prácticas.

---

## Ejecución rápida

```bash
python -m venv .venv
source .venv/bin/activate           # macOS / Linux
.venv\Scripts\activate               # Windows
pip install -r requirements.txt
python -m equestrian.main

# scripts autocontenidos
./run_game_mac.command               # macOS
./run_game.sh                        # Linux
run_game.bat                         # Windows
```

Dependencias externas (pip):

| Librería   | Uso principal                                                   |
|------------|-----------------------------------------------------------------|
| `pygame`   | UI, animaciones, manejo de eventos y sonido.                    |
| `matplotlib` | Exporta `performance_last_race.png` con velocidad vs energía. |

---

## Estructura y modularización

```
src/equestrian/
├── main.py                     # Entry point (inicializa Pygame y llama a run_game)
├── game/engine.py              # Menú, HUD, carrera y flujo general
├── domain/
│   ├── caballo.py              # Caballo (abstracta), Yegua, PuraSangre
│   └── jinete.py               # Dataclass Jinete
├── services/
│   ├── persistence.py          # CRUD sobre equestrian_progress.json
│   ├── history.py              # Historial (equestrian_history.json)
│   ├── performance.py          # Exporta gráficos con matplotlib
│   └── __init__.py             # Re-exporta servicios
└── ...
```

- La **interfaz gráfica** (menú + carrera) vive en `engine.py`.
- Las **clases de dominio** están aisladas en `domain/`.
- La **persistencia** y los servicios auxiliares están en `services/`.
- `main.py` sólo se encarga de preparar el entorno y llamar a `run_game()`.

Esta separación cumple la consigna de “modularizar y mantener un main”.

---

## Controles del juego

| Acción | Tecla |
|--------|-------|
| Acelerar | `ESPACIO` (tapping continuo) |
| Hidratar | `H` (2 usos) |
| Pausa / Continuar | `P` |
| Volver al menú | `ESC` |
| Navegación | Mouse / `ENTER` |

---

## Cómo se satisfacen los requisitos de la facultad

### 1. POO + herencia + encapsulamiento (mínimo 2 clases)

- `Caballo` es una **clase abstracta** con cinco atributos (`nombre`, `raza`,
  `velocidad`, `resistencia`, `__energia` encapsulada) y métodos
  `consumir_energia`, `recuperar_energia`, `bonificacion_terreno()` (abstracto).
- `Yegua` y `PuraSangre` **heredan** de `Caballo` y redefinen el bono por clima.
- El menú permite crear instancias personalizadas (sexo/raza) aplicando
  polimorfismo sobre `Caballo`.
- `Jinete` (`dataclass`) acompaña al caballo y mantiene experiencia/puntos.
- Todas las clases tienen docstrings y comentarios contextuales.

### 2. Uso de al menos 3 módulos vistos en clase

| Módulo     | Por qué cuenta |
|------------|----------------|
| `json`     | `services/persistence.py` y `services/history.py` leen/escriben JSON (guardado e historial). |
| `matplotlib` | `services/performance.py` genera gráficos de la carrera. |
| `pygame`   | UI completa (menús, HUD, eventos, render). |

### 3. CRUD completo de la clase principal

Tomamos como clase principal al **Caballo** seleccionado por el jugador:

| CRUD | Implementación |
|------|----------------|
| Create | Menú inicial crea un caballo con sexo, raza y clima. |
| Read   | `cargar_progreso()` reconstruye estado previo, `load_history()` recupera últimas entradas. |
| Update | En carrera y “Modo Cuidado” se modifican energía, resistencia, nombre, puntos y se vuelve a guardar. |
| Delete | El historial se acota a 500 entradas (las más viejas se descartan) y el jugador puede reiniciar progreso eliminando el JSON. |

### 4. Interfaz gráfica / interactiva

- Hecha con **Pygame**: menús responsivos rosa, HUD escalable, animaciones laterales,
  fondo parallax, rivales IA, resultados, modo cuidado.

### 5. Documentación de librerías externas

- `README.md` + `requirements.txt` indican cómo instalar `pygame` y `matplotlib`.
- Scripts `.command/.sh/.bat` crean el entorno virtual automáticamente.

### 6. Incremento respecto de trabajos previos

- Vista lateral completa, IA rivales, tap-meter de energía, historial de jugadores,
  persistencia avanzada e informe gráfico posterior a cada carrera.

---

## Secciones destacadas

### Menú inicial (UI responsiva)

- Grilla configurable (`PANEL_PAD`, `GAP_X`, etc.) que evita superposiciones en
  960×540 o 1280×720.
- Selectores:
  - **Sexo**: Yegua/Macho.
  - **Raza**: carrusel con `Pura Sangre`, `Criollo`, `Árabe`, `Cuarto de Milla`, `Percherón`.
  - **Clima**: Aleatorio/Soleado/Lluvioso/Ventoso/Barro.
- Panel “Últimos 5 jugadores” provisto por `services/history.load_history()`.
- Docstrings en cada helper (`draw_label`, `draw_button`, `draw_bar`, etc.) para
  cumplir con la documentación solicitada.

### Carrera + HUD

- Tap meter (`ESPACIO`) alimenta barras de energía y ritmo en su propia fila.
- HUD Times New Roman, dos columnas, sin solapamientos, barras en renglón exclusivo.
- Fondo parallax: montañas, colinas, cerca (con `BG_PX_PER_M`).
- Metas y rivales IA se dibujan de forma independiente al fondo.

### Persistencia e historial

- `equestrian_progress.json`: guarda último jinete, caballo, sexo, raza, clima, récords.
- `equestrian_history.json`: se anexan las carreras (limite 500).  
- `performance_last_race.png`: gráfico exportado vía matplotlib.

### Flujo estable

- `run_game()` mantiene un loop maestro: menú → carrera → resultados → menú.
- Los sub-módulos nunca llaman `pygame.quit()`; sólo devuelven banderas (`"menu"`, `"quit"`, `"done"`).
- El juego queda abierto hasta que el usuario cierra la ventana o elige “Salir”.

---

## Buenas prácticas destacadas

- Docstrings y comentarios para funciones, clases y métodos clave.
- Variables descriptivas (en español) y tipado con anotaciones.
- Responsabilidad única en cada módulo.
- Limitación de historial a 500 entradas (evita crecimiento infinito).
- Scripts multiplataforma para correr el juego sin comandos largos.

---

## Ideas de mejora

1. Agregar audio ambiente / música usando `pygame.mixer`.
2. CRUD visual del historial (eliminar entradas desde el menú).
3. Exportar reportes en PDF o tablas (pandas) para análisis estadístico.

---

Ante cualquier ajuste adicional para la entrega, editar `src/equestrian/game/engine.py`
o los módulos de `services/`. ¡Éxitos con la presentación! 🐎🎓
