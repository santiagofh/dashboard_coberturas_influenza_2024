#%%
import pandas as pd
import os
from glob import glob
#%%
# 📁 Ruta del folder
ruta = r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\RNI\INFLUENZA\2024"

# 📂 Obtener archivos
archivos = glob(os.path.join(ruta, "*.csv"))
archivos = [f for f in archivos if not os.path.basename(f).startswith("~")]
df_columnas = pd.read_csv(
        archivos[0],
        encoding="LATIN1",
        sep="|",
        nrows=0,
        low_memory=False
    )
columnas=df_columnas.columns
#%%
# 🎯 Columnas necesarias
columnas_necesarias = [
    'RUN', 'PASAPORTE', 'OTRO',
    'CAMPANA',
    "ID_INMUNIZACION",
    "COD_COMUNA_OCURR",
    "COMUNA_OCURR",
    "COD_COMUNA_RESID",
    "COMUNA_RESIDENCIA",
    "CRITERIO_ELEGIBILIDAD",
    "DOSIS",
    "VACUNA_ADMINISTRADA",
    "REGISTRO_ELIMINADO",
    "SEXO",
    "FECHA_NACIMIENTO"
]

# 🧩 Función optimizada
def transformar_y_filtrar(path):

    df = pd.read_csv(
        path,
        encoding="LATIN1",
        sep="|",
        usecols=columnas_necesarias,
        low_memory=False
    )

    # 🔎 Filtrar inmediatamente (reduce RAM drásticamente)
    df = df[
        (
            (df["COD_COMUNA_RESID"].between(13000, 13999)) |
            (df["COD_COMUNA_OCURR"].between(13000, 13999))
        ) &
        # (df["DOSIS"].isin(["1° dosis", "Única"])) &
        (df["VACUNA_ADMINISTRADA"] == "SI") &
        (df["REGISTRO_ELIMINADO"] == "NO") &
        (df["CRITERIO_ELEGIBILIDAD"] != "EPRO")
        

    ]

    return df

# 🔁 Leer + filtrar archivo por archivo
lista_df = []

for archivo in archivos:
    print(f"Leyendo {os.path.basename(archivo)}...")
    df_temp = transformar_y_filtrar(archivo)
    lista_df.append(df_temp)

# 🔗 Concatenar SOLO data ya filtrada
df_final = pd.concat(lista_df, ignore_index=True)
#%% FILTRAR CAMPAÑA 2024

df_final=df_final.loc[df_final.CAMPANA=='Influenza 2024']
#%%
# 🧼 Limpiar y estandarizar primero
for col in ["RUN", "PASAPORTE", "OTRO"]:
    df_final[col] = (
        df_final[col]
        .astype(str)
        .str.strip()
        .replace(["nan", "None", ""], pd.NA)
    )

# 🚀 Crear identificador final con prioridad RUN > PASAPORTE > OTRO
df_final["IDENTIFICACION_FINAL"] = (
    "RUN_" + df_final["RUN"]
)

mask_run = df_final["RUN"].notna()
mask_pas = df_final["PASAPORTE"].notna() & ~mask_run
mask_otro = df_final["OTRO"].notna() & ~mask_run & ~mask_pas

df_final.loc[mask_pas, "IDENTIFICACION_FINAL"] = "PAS_" + df_final.loc[mask_pas, "PASAPORTE"]
df_final.loc[mask_otro, "IDENTIFICACION_FINAL"] = "OTRO_" + df_final.loc[mask_otro, "OTRO"]

# Opcional: eliminar los que quedaron sin identificación válida
df_final = df_final[df_final["IDENTIFICACION_FINAL"].notna()]

#%%
df_final["IDENTIFICACION_FINAL"].duplicated().sum()

#%%
duplicados_unicos_influenza=df_final[df_final["IDENTIFICACION_FINAL"].duplicated(keep=False)] \
    .sort_values("IDENTIFICACION_FINAL")
duplicados_unicos_influenza.to_excel("duplicados_unicos_influenza.xlsx")
#%%
df_final = df_final.drop_duplicates(
    subset="IDENTIFICACION_FINAL",
    keep="first"
)
#%%
# 🧠 Tipos (ahora sobre dataset pequeño)
df_final["ID_INMUNIZACION"] = pd.to_numeric(df_final["ID_INMUNIZACION"], errors="coerce")
df_final["FECHA_NACIMIENTO"] = pd.to_datetime(df_final["FECHA_NACIMIENTO"], errors="coerce")

#%%
def limpiar_comuna(col):
    return (
        col
        .str.strip()                           # quitar espacios al inicio/final
        .str.replace('\xa0', ' ', regex=False) # reemplazar espacio duro
        .str.title()                           # capitalización uniforme
        .str.replace(" De ", " de ", regex=False)
        .replace({"Curacavi": "Curacaví"})
    )

df_final["COMUNA_RESIDENCIA"] = limpiar_comuna(df_final["COMUNA_RESIDENCIA"])
df_final["COMUNA_OCURR"] = limpiar_comuna(df_final["COMUNA_OCURR"])
#%%

# 🎯 Mapeo criterio → tipo comuna
map_criterio = {
    'Escolares de 1° a 5° año básico': 'OCURRENCIA',
    'Enfermos cronicos de 11 a 59 años de edad': 'RESIDENCIA',
    'Embarazadas': 'RESIDENCIA',
    'Personas mayores de 60 años y más': 'RESIDENCIA',
    'Otras prioridades': 'OCURRENCIA',
    'P. de salud: Privado': 'OCURRENCIA',
    'Niños y niñas de 6 meses a 5 años de edad': 'RESIDENCIA',
    'Trabajadores de la educación  preescolar y escolar hasta 8° basico': 'OCURRENCIA',
    'P. de salud: Público': 'OCURRENCIA',
    'Cuidadores de adultos mayores y funcionarios de los ELEAM': 'OCURRENCIA',
    'Trabajadores de avícolas y de criaderos de cerdo': 'OCURRENCIA',
    'Estrategia Capullo': 'RESIDENCIA'
}

# Crear tipo comuna
df_final["TIPO_COMUNA"] = df_final["CRITERIO_ELEGIBILIDAD"].map(map_criterio)

# Crear comuna final según tipo
df_final["COMUNA_FINAL"] = df_final.apply(
    lambda row: row["COMUNA_OCURR"] if row["TIPO_COMUNA"] == 'OCURRENCIA'
    else row["COMUNA_RESIDENCIA"],
    axis=1
)

df_final["COD_COMUNA_FINAL"] = df_final.apply(
    lambda row: row["COD_COMUNA_OCURR"] if row["TIPO_COMUNA"] == 'OCURRENCIA'
    else row["COD_COMUNA_RESID"],
    axis=1
)
df_final = df_final[
    df_final["COD_COMUNA_FINAL"].between(13000, 13999)
]
#%%
df_final = df_final.rename(columns={
    "COMUNA_FINAL": "COMUNA",
    "COD_COMUNA_FINAL": "COD_COMUNA"
})

# 🧹 Eliminar comunas originales para evitar confusión
df_final = df_final.drop(columns=[
    "COMUNA_RESIDENCIA",
    "COMUNA_OCURR",
    "COD_COMUNA_RESID",
    "COD_COMUNA_OCURR"
])

# (Opcional) Reordenar columnas dejando COMUNA más visible
column_order = [
    "ID_INMUNIZACION",
    "TIPO_COMUNA",
    "COD_COMUNA",
    "COMUNA",
    "CRITERIO_ELEGIBILIDAD",
    "DOSIS",
    "VACUNA_ADMINISTRADA",
    "SEXO",
    "FECHA_NACIMIENTO",
    "REGISTRO_ELIMINADO"
]

df_final = df_final[column_order]

#%%
# 💾 Guardar
df_final.to_csv("output/numerador_influenza_2024_rm.csv", index=False)

print("Shape final:", df_final.shape)

# %%
