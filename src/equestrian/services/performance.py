from typing import List, Dict

PERF_PNG = "performance_last_race.png"

def guardar_grafico_performance(perf_samples: List[Dict[str, float]]) -> None:
    if not perf_samples:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        print("No se pudo cargar matplotlib:", e)
        return

    t = [s["t"] for s in perf_samples]
    v = [s["vel"] for s in perf_samples]
    e = [s["eng"] for s in perf_samples]

    plt.figure(figsize=(8, 4.5))
    plt.title("Rendimiento de la carrera")
    plt.plot(t, v, label="Velocidad (m/s virtual)")
    plt.plot(t, e, label="Energía (%)")
    plt.xlabel("Tiempo (s)")
    plt.ylabel("Valor")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PERF_PNG)
    plt.close()
    print(f"Gráfico de rendimiento guardado en {PERF_PNG}")
