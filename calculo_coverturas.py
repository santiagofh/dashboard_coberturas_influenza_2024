#%%
import pandas as pd

# ── CARGAR DATOS ──────────────────────────────────────────────────────────────

numerador = pd.read_csv("output/numerador_influenza_2024_rm.csv")
denominador = pd.read_csv("output/denominador_influenza_2024.csv")

# ── MAPEO CRITERIO → GRUPO DENOMINADOR ───────────────────────────────────────

excluir = [
    'Vacunación privada (No población objetivo)',
    'Población general',
    'GES',
    'Ley Ricarte Soto'
]

# Mapeo corregido
map_criterio_grupo = {
    'Niños y niñas de 6 meses a 5 años de edad':                        'ninos_6m_5basico',
    'Escolares de 1° a 5° año básico':                                   'ninos_6_10_anios',
    'Enfermos cronicos de 11 a 59 años de edad':                         'cronicos_11_59',
    'Embarazadas':                                                        'embarazadas',
    'Personas mayores de 60 años y más':                                  'adultos_60_mas',
    'Otras prioridades':                                                  'otras_prioridades',
    'P. de salud: Privado':                                               'salud_privado',
    'P. de salud: Público':                                               'salud_publico',
    'Trabajadores de la educación  preescolar y escolar hasta 8° basico': 'trab_educacion',
    'Cuidadores de adultos mayores y funcionarios de los ELEAM':          'cuidadores_adulto_mayor_eleam',
    'Trabajadores de avícolas y de criaderos de cerdo':                   'trab_avicolas_cerdos',
    'Estrategia Capullo':                                                 'estrategia_capullo',
}

# Y elimina este bloque del denominador — ya no es necesario:
# den["campana"] = den["campana"].replace({
#     "ninos_6m_5basico": "ninos_0_10",
#     "ninos_6_10_anios": "ninos_0_10",
# })
# den = den.groupby(["comuna", "campana"], as_index=False)["denominador"].sum()
# ── PREPARAR NUMERADOR ────────────────────────────────────────────────────────

num = numerador[~numerador["CRITERIO_ELEGIBILIDAD"].isin(excluir)].copy()
num["grupo"] = num["CRITERIO_ELEGIBILIDAD"].map(map_criterio_grupo)
num = num.dropna(subset=["grupo"])

# Contar vacunados por comuna + grupo
num_agr = (
    num.groupby(["COMUNA", "grupo"])
    .size()
    .reset_index(name="vacunados")
)

# ── PREPARAR DENOMINADOR ──────────────────────────────────────────────────────

# Combinar ninos_6m_5basico + ninos_6_10_anios → ninos_0_10
den = denominador.copy()
den = den.groupby(["comuna", "campana"], as_index=False)["denominador"].sum()
den = den.rename(columns={"campana": "grupo"})

# ── MERGE Y COBERTURA ─────────────────────────────────────────────────────────

cobertura = num_agr.merge(
    den,
    left_on=["COMUNA", "grupo"],
    right_on=["comuna", "grupo"],
    how="left"
).drop(columns="comuna")

cobertura["cobertura_pct"] = (
    cobertura["vacunados"] / cobertura["denominador"] * 100
).round(2)

# ── GUARDAR ───────────────────────────────────────────────────────────────────

cobertura.to_csv("output/cobertura_influenza_2024_rm.csv", index=False)

print(cobertura.sort_values(["COMUNA", "grupo"]).to_string(index=False))
print("\nShape:", cobertura.shape)
# %%
