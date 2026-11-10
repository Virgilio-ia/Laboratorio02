import hashlib
import os
import pandas as pd


def calcular_sha256(ruta_archivo: str) -> str:
    """Calcula la huella criptográfica SHA-256 de un archivo mediante lectura en bloques."""
    sha256 = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        for bloque in iter(lambda: f.read(4096), b""):
            sha256.update(bloque)
    return sha256.hexdigest()


def depurar_telemetria(
    ruta_origen: str, ruta_destino: str
) -> tuple[str, str, int, int]:
    """Carga el dataset original, limpia anomalías y genera el archivo depurado."""
    # 1. Obtenemos el SHA-256 del dataset original (bruto)
    hash_original = calcular_sha256(ruta_origen)

    # 2. Lectura del CSV con Pandas
    df = pd.read_csv(ruta_origen, encoding="utf-8")
    filas_iniciales = len(df)

    # 3. Limpieza de Anomalías
    # a. Eliminación de filas completamente duplicadas
    df = df.drop_duplicates()

    # b. Eliminación de valores nulos (NaN) en variables críticas
    df = df.dropna(subset=["peso_kg", "temp_celsius", "destino"])

    # c. Filtrado de valores fuera de rango o inconsistentes:
    # - El peso no puede ser negativo (ej. -45.50 kg)
    # - La temperatura en transporte refrigerado debe ser coherente (entre -30°C y 50°C)
    # - El estado del envío debe pertenecer al catálogo oficial
    estados_validos = [
        "ENTREGADO",
        "EN_TRANSITO",
        "EN_REPARTO",
        "PENDIENTE",
        "CANCELADO",
    ]

    df = df[
        (df["peso_kg"] > 0)
        & (df["temp_celsius"] >= -30.0)
        & (df["temp_celsius"] <= 50.0)
        & (df["estado_envio"].isin(estados_validos))
    ]

    # 4. Guardar dataset saneado
    df.to_csv(ruta_destino, index=False, encoding="utf-8")
    filas_finales = len(df)

    # 5. Calcular SHA-256 del dataset depurado
    hash_limpio = calcular_sha256(ruta_destino)

    return hash_original, hash_limpio, filas_iniciales, filas_finales


if __name__ == "__main__":
    ruta_input = os.path.join("datos", "telemetria_envios.csv")
    ruta_output = os.path.join("datos", "telemetria_limpia.csv")

    if not os.path.exists(ruta_input):
        print(
            f"Error: No se encuentra el archivo original en la ruta {ruta_input}"
        )
    else:
        h_orig, h_limp, n_in, n_out = depurar_telemetria(
            ruta_input, ruta_output
        )

        print("\n================ INFORME DE INTEGRIDAD Y CALIDAD ================")
        print(f"Filas procesadas:    {n_in} -> {n_out} (Registros descartados: {n_in - n_out})")
        print(f"SHA-256 Original:  {h_orig}")
        print(f"SHA-256 Depurado:  {h_limp}")
        print("=================================================================\n")