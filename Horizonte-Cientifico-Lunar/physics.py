"""Modelo físico explícito e testável da potência de um painel solar ideal."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

IRRADIANCIA_REFERENCIA_W_M2 = 1361.0  # valor de referência, não medição local


def fator_incidencia(elevacao_graus: float, azimute_sol_graus: float, modo: str,
                    inclinacao_graus: float = 0, azimute_painel_graus: float = 0) -> float:
    """Cosseno positivo do ângulo de incidência para a normal do painel.

    Se a altitude do centro do Sol for <= 0°, considera disco solar oculto.
    O horizonte é geométrico e plano; não há sombras das elevações lunares.
    """
    if elevacao_graus <= 0:
        return 0.0
    alt = math.radians(elevacao_graus)
    if modo == "Rastreamento ideal":
        return 1.0
    if modo == "Horizontal":
        return max(0.0, math.sin(alt))
    if modo == "Inclinado fixo":
        tilt = math.radians(inclinacao_graus)
        delta_az = math.radians(azimute_sol_graus - azimute_painel_graus)
        return max(0.0, math.sin(alt) * math.cos(tilt) + math.cos(alt) * math.sin(tilt) * math.cos(delta_az))
    raise ValueError("Modo de orientação inválido.")


def add_solar_power(df: pd.DataFrame, area_m2: float, efficiency_pct: float, mode: str,
                    tilt_deg: float = 0.0, panel_az_deg: float = 0.0) -> pd.DataFrame:
    if area_m2 <= 0 or not 0 < efficiency_pct <= 100:
        raise ValueError("Área e eficiência devem ser positivas e válidas.")
    result = df.copy()
    result["incidencia"] = [
        fator_incidencia(float(e), float(a), mode, tilt_deg, panel_az_deg)
        for e, a in zip(result["sun_elev"], result["sun_az"])
    ]
    result["potencia_w"] = IRRADIANCIA_REFERENCIA_W_M2 * area_m2 * (efficiency_pct / 100.0) * result["incidencia"]
    result["energia_acumulada_kwh"] = 0.0
    if len(result) > 1:
        hours = (result["instante_utc"] - result["instante_utc"].iloc[0]).dt.total_seconds().to_numpy() / 3600.0
        watts = result["potencia_w"].to_numpy(dtype=float)
        intervals_kwh = (watts[:-1] + watts[1:]) / 2 * np.diff(hours) / 1000
        result["energia_acumulada_kwh"] = np.insert(np.cumsum(intervals_kwh), 0, 0.0)
    return result
