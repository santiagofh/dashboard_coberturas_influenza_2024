#%%
import pandas as pd

df = pd.read_excel(r"data/ORDEN1_Población-objetivoCampaña-influenza-2024oficial - copia.xlsx", sheet_name="RM", header=0)

df.columns = [
    "codigo_comuna", "comuna", "poblacion_objetivo",
    "ninos_6m_5basico", "ninos_6_10_anios", "adultos_60_mas",
    "cronicos_11_59", "embarazadas", "estrategia_capullo",
    "salud_privado", "salud_publico", "trab_educacion",
    "trab_avicolas_cerdos", "otras_prioridades", "cuidadores_adulto_mayor_eleam"
]

df = df[pd.to_numeric(df["codigo_comuna"], errors="coerce").notna()]

# Agregar esto acá
df["comuna"] = (
    df["comuna"]
    .str.strip()
    .str.replace('\xa0', ' ', regex=False)
    .str.title()
    .str.replace(" De ", " de ", regex=False)
)

grupos = ["ninos_6m_5basico", "ninos_6_10_anios", "adultos_60_mas", "cronicos_11_59",
          "embarazadas", "estrategia_capullo", "salud_privado", "salud_publico",
          "trab_educacion", "trab_avicolas_cerdos", "otras_prioridades", "cuidadores_adulto_mayor_eleam"]

df_long = df.melt(id_vars="comuna", value_vars=grupos, var_name="campana", value_name="denominador")
df_long.to_csv(r"output/denominador_influenza_2024.csv", index=False)
# %%
