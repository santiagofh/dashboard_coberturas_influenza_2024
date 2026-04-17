from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
DATA_PATH = OUTPUT_DIR / "cobertura_influenza_2024_rm.csv"

GROUP_LABELS = {
    "adultos_60_mas": "Adultos de 65 y más",
    "cronicos_11_59": "Enfermos crónicos",
    "cuidadores_adulto_mayor_eleam": "Cuidadores de adultos mayores y funcionarios ELEAM",
    "embarazadas": "Embarazadas",
    "estrategia_capullo": "Estrategia Capullo",
    "ninos_6_10_anios": "Niños de 1° a 5° básico",
    "ninos_6m_5basico": "Niños de 6 meses a 5 años",
    "otras_prioridades": "Otras prioridades",
    "salud_privado": "P. de salud privado",
    "salud_publico": "P. de salud público",
    "trab_avicolas_cerdos": "Trabajadores avícolas",
    "trab_educacion": "Trabajadores de la educación",
}

GROUP_INFO = {
    "adultos_60_mas": "Cobertura en población de residencia. Sirve para seguir el avance de protección en personas mayores.",
    "cronicos_11_59": "Cobertura en personas con patologías crónicas. Puede superar 100% por diferencias entre registros administrados y denominador oficial.",
    "cuidadores_adulto_mayor_eleam": "Cobertura en cuidadores y funcionarios de ELEAM, medida con criterio de ocurrencia.",
    "embarazadas": "Cobertura en embarazadas con criterio de residencia, clave para protección materno infantil.",
    "estrategia_capullo": "Cobertura en estrategia Capullo, orientada a proteger entornos de mayor riesgo.",
    "ninos_6_10_anios": "Cobertura en niños de 6 a 10 años con criterio de ocurrencia.",
    "ninos_6m_5basico": "Cobertura en niños desde 6 meses hasta 5° básico con criterio de residencia.",
    "otras_prioridades": "Cobertura del grupo otras prioridades, medido con criterio de ocurrencia.",
    "salud_privado": "Cobertura en personal de salud del sector privado.",
    "salud_publico": "Cobertura en personal de salud del sector público.",
    "trab_avicolas_cerdos": "Cobertura en trabajadores avícolas y criaderos de cerdo.",
    "trab_educacion": "Cobertura en trabajadores de la educación preescolar y escolar hasta 8° básico.",
}

ACCENT_REPLACEMENTS = str.maketrans(
    {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "ñ": "n",
        "Ñ": "N",
        "°": "",
    }
)

HOME_GROUP_ORDER = [
    "otras_prioridades",
    "trab_educacion",
    "estrategia_capullo",
    "trab_avicolas_cerdos",
    "ninos_6_10_anios",
    "ninos_6m_5basico",
    "adultos_60_mas",
    "cronicos_11_59",
    "embarazadas",
    "salud_privado",
    "salud_publico",
]


def slugify(text: str) -> str:
    return (
        text.lower()
        .translate(ACCENT_REPLACEMENTS)
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    required = {"COMUNA", "grupo", "vacunados", "denominador", "cobertura_pct"}
    missing = required.difference(df.columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Faltan columnas requeridas: {missing_str}")

    df = df.rename(columns={"COMUNA": "Comuna", "grupo": "grupo_id"}).copy()
    df["Grupo"] = df["grupo_id"].map(GROUP_LABELS).fillna(df["grupo_id"])
    df["vacunados"] = pd.to_numeric(df["vacunados"], errors="coerce")
    df["denominador"] = pd.to_numeric(df["denominador"], errors="coerce")
    df["cobertura_pct"] = pd.to_numeric(df["cobertura_pct"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def get_group_summary() -> pd.DataFrame:
    df = load_data()
    summary = (
        df.groupby(["grupo_id", "Grupo"], as_index=False)
        .agg(vacunados=("vacunados", "sum"), denominador=("denominador", "sum"))
    )
    summary["cobertura_pct"] = (summary["vacunados"] / summary["denominador"] * 100).round(2)
    return summary.sort_values("cobertura_pct", ascending=True).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_commune_total_summary() -> pd.DataFrame:
    df = load_data()
    summary = (
        df.groupby("Comuna", as_index=False)
        .agg(vacunados=("vacunados", "sum"), denominador=("denominador", "sum"))
    )
    summary["cobertura_pct"] = (summary["vacunados"] / summary["denominador"] * 100).round(2)
    return summary.sort_values("cobertura_pct", ascending=False).reset_index(drop=True)


def dataframe_to_excel_bytes(
    df: pd.DataFrame,
    totals_df: pd.DataFrame | None = None,
    data_sheet_name: str = "Datos",
    prepend_sheets: dict[str, pd.DataFrame] | None = None,
    extra_sheets: dict[str, pd.DataFrame] | None = None,
) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        if prepend_sheets:
            for sheet_name, sheet_df in prepend_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        df.to_excel(writer, sheet_name=data_sheet_name[:31], index=False)
        if totals_df is not None:
            totals_df.to_excel(
                writer,
                sheet_name="Totales generales",
                index=False,
            )
        if extra_sheets:
            for sheet_name, sheet_df in extra_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buffer.getvalue()


def format_int(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(value)):,}".replace(",", ".")


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.2f}%"


def build_commune_table(group_df: pd.DataFrame) -> pd.DataFrame:
    table_df = group_df.rename(
        columns={
            "Comuna": "Comuna",
            "vacunados": "Vacunas administradas",
            "denominador": "Población objetivo",
            "cobertura_pct": "Cobertura (%)",
        }
    )[["Comuna", "Cobertura (%)", "Población objetivo", "Vacunas administradas"]].copy()

    table_df.insert(0, "Marca", "")
    if not table_df.empty:
        max_idx = table_df["Cobertura (%)"].idxmax()
        min_idx = table_df["Cobertura (%)"].idxmin()
        table_df.loc[max_idx, "Marca"] = "🔴"
        table_df.loc[min_idx, "Marca"] = "🟠"

    return table_df


def build_totals_table(group_name: str, total_denominador: float, total_vacunados: float) -> pd.DataFrame:
    total_cobertura = (total_vacunados / total_denominador * 100) if total_denominador else 0
    return pd.DataFrame(
        [
            {
                "Campaña": group_name,
                "Población objetivo total": int(round(total_denominador)),
                "Vacunas administradas": int(round(total_vacunados)),
                "Cobertura total (%)": round(total_cobertura, 2),
            }
        ]
    )


def build_group_info_table(total_cobertura: float, total_denominador: float, total_vacunados: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Indicador": "Cobertura regional", "Valor": round(total_cobertura, 2)},
            {"Indicador": "Vacunas administradas", "Valor": int(round(total_vacunados))},
            {"Indicador": "Población objetivo", "Valor": int(round(total_denominador))},
        ]
    )


def build_home_totals_table(summary: pd.DataFrame) -> pd.DataFrame:
    total_vacunados = summary["vacunados"].sum()
    total_denominador = summary["denominador"].sum()
    total_cobertura = (total_vacunados / total_denominador * 100) if total_denominador else 0
    return pd.DataFrame(
        [
            {
                "Ámbito": "Región Metropolitana",
                "Grupos monitoreados": int(summary["grupo_id"].nunique()),
                "Población objetivo total": int(round(total_denominador)),
                "Vacunas administradas": int(round(total_vacunados)),
                "Cobertura total (%)": round(total_cobertura, 2),
            }
        ]
    )


def build_home_info_table(summary: pd.DataFrame) -> pd.DataFrame:
    total_vacunados = summary["vacunados"].sum()
    total_denominador = summary["denominador"].sum()
    total_groups = summary["grupo_id"].nunique()
    return pd.DataFrame(
        [
            {"Indicador": "Vacunas administradas", "Valor": int(round(total_vacunados))},
            {"Indicador": "Población objetivo", "Valor": int(round(total_denominador))},
            {"Indicador": "Grupos monitoreados", "Valor": int(total_groups)},
        ]
    )


def build_home_chart(summary: pd.DataFrame) -> go.Figure:
    ordered_groups = summary["Grupo"].tolist()
    fig = px.bar(
        summary,
        x="cobertura_pct",
        y="Grupo",
        orientation="h",
        text="cobertura_pct",
        color="cobertura_pct",
        color_continuous_scale=["#A7D3F3", "#2E75B6", "#1F4E79"],
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(
        height=620,
        margin=dict(l=20, r=20, t=20, b=20),
        coloraxis_showscale=False,
        xaxis_title="Cobertura (%)",
        yaxis_title="Grupo objetivo",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#D9E6F2")
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(reversed(ordered_groups)))
    return fig


def build_total_chart(group_name: str, total_denominador: float, total_vacunados: float) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        x=[group_name],
        y=[total_denominador],
        name="Población objetivo",
        marker_color="#9CC3E5",
        text=[format_int(total_denominador)],
        textposition="outside",
    )
    fig.add_bar(
        x=[group_name],
        y=[total_vacunados],
        name="Vacunas administradas",
        marker_color="#1F4E79",
        text=[format_int(total_vacunados)],
        textposition="outside",
    )
    fig.update_layout(
        barmode="group",
        height=430,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Campaña",
        yaxis_title="Personas",
        legend_title="Serie",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_yaxes(showgrid=True, gridcolor="#D9E6F2")
    return fig


def render_info_box(group_id: str, group_df: pd.DataFrame):
    total_vacunados = group_df["vacunados"].sum()
    total_denominador = group_df["denominador"].sum()
    total_cobertura = (total_vacunados / total_denominador * 100) if total_denominador else 0
    top_row = group_df.sort_values("cobertura_pct", ascending=False).iloc[0]
    bottom_row = group_df.sort_values("cobertura_pct", ascending=True).iloc[0]

    st.markdown(
        f"""
            <div class="info-card">
            <div class="info-card-title">Resumen del grupo</div>
            <p><strong>Descripción:</strong> {GROUP_INFO.get(group_id, "Sin descripción adicional.")}</p>
            <p><strong>Cobertura regional:</strong> {format_pct(total_cobertura)}</p>
            <p><strong>Vacunas administradas:</strong> {format_int(total_vacunados)} de {format_int(total_denominador)} personas objetivo.</p>
            <p><strong>Comuna con mayor cobertura:</strong> {top_row["Comuna"]} ({format_pct(top_row["cobertura_pct"])})</p>
            <p><strong>Comuna con menor cobertura:</strong> {bottom_row["Comuna"]} ({format_pct(bottom_row["cobertura_pct"])})</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page():
    summary = get_group_summary()
    commune_summary = get_commune_total_summary()
    home_summary = (
        summary[summary["grupo_id"].isin(HOME_GROUP_ORDER)]
        .assign(order=lambda df_: df_["grupo_id"].map({g: i for i, g in enumerate(HOME_GROUP_ORDER)}))
        .sort_values("order", ascending=True)
        .drop(columns="order")
    )

    st.title("Dashboard Campaña Influenza 2024")
    st.caption("Cobertura de vacunación contra la influenza por grupo objetivo en la Región Metropolitana.")

    col1, col2, col3, col4 = st.columns(4)
    total_vacunados = summary["vacunados"].sum()
    total_denominador = summary["denominador"].sum()
    total_groups = summary["grupo_id"].nunique()
    total_cobertura_rm = (total_vacunados / total_denominador * 100) if total_denominador else 0

    col1.metric("Vacunas administradas", format_int(total_vacunados))
    col2.metric("Población objetivo", format_int(total_denominador))
    col3.metric("Grupos monitoreados", format_int(total_groups))
    col4.metric("Cobertura total RM", format_pct(total_cobertura_rm))

    st.markdown("### Gráfico de cobertura (%) según grupo objetivo")
    st.plotly_chart(build_home_chart(home_summary), use_container_width=True)

    st.markdown("### Tabla de cobertura total por comuna")
    commune_view = commune_summary.rename(
        columns={
            "Comuna": "Comuna",
            "vacunados": "Vacunas administradas",
            "denominador": "Población objetivo",
            "cobertura_pct": "Cobertura total (%)",
        }
    )
    st.dataframe(
        commune_view,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "Comuna": st.column_config.TextColumn(width="medium"),
            "Vacunas administradas": st.column_config.NumberColumn(format="%d"),
            "Población objetivo": st.column_config.NumberColumn(format="%d"),
            "Cobertura total (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    st.markdown("### Tabla de cobertura (%) por grupo objetivo")
    summary_view = home_summary.rename(
        columns={
            "Grupo": "Grupo objetivo",
            "vacunados": "Vacunas administradas",
            "denominador": "Población objetivo",
            "cobertura_pct": "Cobertura (%)",
        }
    )
    st.dataframe(
        summary_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Grupo objetivo": st.column_config.TextColumn(width="large"),
            "Vacunas administradas": st.column_config.NumberColumn(format="%d"),
            "Población objetivo": st.column_config.NumberColumn(format="%d"),
            "Cobertura (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    home_totals_df = build_home_totals_table(home_summary)
    home_info_df = build_home_info_table(home_summary)
    home_excel_bytes = dataframe_to_excel_bytes(
        summary_view,
        totals_df=home_totals_df,
        data_sheet_name="Cobertura grupos",
        prepend_sheets={"Indicadores": home_info_df},
    )
    st.download_button(
        label="Descargar resumen en Excel",
        data=home_excel_bytes,
        file_name="influenza_2024_resumen_inicio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_group_page(group_id: str):
    df = load_data()
    group_df = df[df["grupo_id"] == group_id].copy()

    if group_df.empty:
        st.error("No hay datos disponibles para esta campaña.")
        st.stop()

    group_name = group_df["Grupo"].iloc[0]
    group_df = group_df.sort_values("cobertura_pct", ascending=False).reset_index(drop=True)

    st.title(f"Campaña Influenza 2024 · {group_name}")
    st.caption("Detalle comunal de cobertura, población objetivo y vacunas administradas.")

    total_vacunados = group_df["vacunados"].sum()
    total_denominador = group_df["denominador"].sum()
    total_cobertura = (total_vacunados / total_denominador * 100) if total_denominador else 0

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Cobertura regional", format_pct(total_cobertura))
    metric2.metric("Vacunas administradas", format_int(total_vacunados))
    metric3.metric("Población objetivo", format_int(total_denominador))

    st.markdown("### Comunas y cobertura")
    table_df = build_commune_table(group_df)

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Marca": st.column_config.TextColumn(width="small", help="🔴 Mayor cobertura · 🟠 Menor cobertura"),
            "Comuna": st.column_config.TextColumn(width="medium"),
            "Cobertura (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Población objetivo": st.column_config.NumberColumn(format="%d"),
            "Vacunas administradas": st.column_config.NumberColumn(format="%d"),
        },
    )

    st.markdown("### Población objetivo total y vacunas administradas")
    st.plotly_chart(
        build_total_chart(group_name, total_denominador, total_vacunados),
        use_container_width=True,
    )

    render_info_box(group_id, group_df)

    totals_df = build_totals_table(group_name, total_denominador, total_vacunados)
    group_info_df = build_group_info_table(total_cobertura, total_denominador, total_vacunados)
    excel_bytes = dataframe_to_excel_bytes(
        table_df,
        totals_df=totals_df,
        prepend_sheets={"Indicadores": group_info_df},
    )
    st.download_button(
        label="Descargar detalle en Excel",
        data=excel_bytes,
        file_name=f"influenza_2024_{slugify(group_name)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def get_navigation_pages():
    summary = get_group_summary().sort_values("Grupo").reset_index(drop=True)
    pages = [st.Page(render_home_page, title="Inicio", icon=":material/home:", default=True)]
    for row in summary.itertuples(index=False):
        pages.append(
            st.Page(
                lambda group_id=row.grupo_id: render_group_page(group_id),
                title=row.Grupo,
                icon=":material/vaccines:",
                url_path=slugify(row.Grupo),
            )
        )
    return pages
