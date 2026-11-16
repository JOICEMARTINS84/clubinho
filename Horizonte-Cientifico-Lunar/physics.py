"""Cálculos físicos transparentes a partir das efemérides JPL e de hipóteses do painel."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

IRRADIANCIA_REFERENCIA_W_M2 = 1361.0  # convenção solar de referência a 1 UA
UA_KM = 149597870.7  # unidade astronômica exata em km (IAU)
VELOCIDADE_LUZ_KM_S = 299792.458  # valor exato no vácuo


def fator_incidencia(elevacao_graus: float, azimute_sol_graus: float, modo: str,
                    inclinacao_graus: float = 0, azimute_painel_graus: float = 0) -> float:
    """Projeção positiva dos raios solares na normal do painel.

    Horizonte geométrico plano; não considera sombras de crateras.
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


def separacao_angular_graus(alt1: float, az1: float, alt2: float, az2: float) -> float:
    """Separação de duas direções topocêntricas em coordenadas horizontais."""
    a, b = math.radians(alt1), math.radians(alt2)
    delta = math.radians(az1 - az2)
    cos_sep = math.sin(a)*math.sin(b) + math.cos(a)*math.cos(b)*math.cos(delta)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_sep))))


def add_solar_power(df: pd.DataFrame, area_m2: float, efficiency_pct: float, mode: str,
                    tilt_deg: float = 0.0, panel_az_deg: float = 0.0) -> pd.DataFrame:
    """Anexa estimativas de fluxo, potência e energia e geometria dos alvos.

    sun_dist_km e earth_dist_km são distâncias observadas pelas efemérides do JPL.
    Energia e irradiância são estimativas físicas, não medições instrumentais.
    """
    if area_m2 <= 0 or not 0 < efficiency_pct <= 100:
        raise ValueError("Área e eficiência devem ser positivas e válidas.")
    result = df.copy()
    result["incidencia"] = [
        fator_incidencia(float(e), float(a), mode, tilt_deg, panel_az_deg)
        for e, a in zip(result["sun_elev"], result["sun_az"])
    ]
    if "sun_dist_km" in result.columns:
        dist = result["sun_dist_km"].astype(float)
        if not np.isfinite(dist).all() or (dist <= 0).any():
            raise ValueError("Distâncias solares ausentes ou inválidas no resultado do JPL.")
        result["irradiancia_estim_w_m2"] = IRRADIANCIA_REFERENCIA_W_M2 * (UA_KM / dist)**2
    else:
        # Mantém compatibilidade com testes e exemplos antigos sem coluna de range.
        result["irradiancia_estim_w_m2"] = IRRADIANCIA_REFERENCIA_W_M2
    result["potencia_w"] = (
        result["irradiancia_estim_w_m2"] * area_m2 * (efficiency_pct / 100.0)
        * result["incidencia"]
    )
    if "earth_dist_km" in result.columns:
        result["retardo_terra_s"] = result["earth_dist_km"].astype(float) / VELOCIDADE_LUZ_KM_S
    else:
        result["retardo_terra_s"] = np.nan
    if {"sun_az", "sun_elev", "earth_az", "earth_elev"}.issubset(result.columns):
        result["separacao_sol_terra_deg"] = [
            separacao_angular_graus(sa, saz, ea, eaz)
            for sa, saz, ea, eaz in zip(
                result["sun_elev"], result["sun_az"],
                result["earth_elev"], result["earth_az"]
            )
        ]
    else:
        result["separacao_sol_terra_deg"] = np.nan

    result["energia_acumulada_kwh"] = 0.0
    if len(result) > 1:
        hours = (result["instante_utc"] - result["instante_utc"].iloc[0]).dt.total_seconds().to_numpy() / 3600.0
        watts = result["potencia_w"].to_numpy(dtype=float)
        if np.any(np.diff(hours) <= 0):
            raise ValueError("Os instantes precisam estar em ordem crescente e sem repetição.")
        intervals_kwh = (watts[:-1] + watts[1:]) * 0.5 * np.diff(hours) / 1000.0
        result["energia_acumulada_kwh"] = np.insert(np.cumsum(intervals_kwh), 0, 0.0)
    return result
