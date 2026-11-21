"""
Inventario de Tecnología (ITAM) · Dashboard ejecutivo en Streamlit
Mismo caso de negocio que el dashboard de Power BI, con los mismos CSV.
Cada pestaña está pensada para verse en una sola pantalla, sin scroll.

Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ================================================================== Config
st.set_page_config(page_title="ITAM · Dashboard ejecutivo", page_icon="🛰️", layout="wide",
                   initial_sidebar_state="auto")

CORTE = pd.Timestamp("2026-10-31")
AUTOR = "Ing. Juan Prieto"
APP_DIR = Path(__file__).parent
DATA_DIR = next((d for d in (APP_DIR / "datos", APP_DIR.parent / "datos") if d.exists()), APP_DIR / "datos")

CIAN, INDIGO, TEAL, AMBAR, ROSA, PIZARRA = "#38BDF8", "#818CF8", "#2DD4BF", "#FBBF24", "#FB7185", "#475569"
TEXTO, TENUE, REJILLA = "#E2E8F0", "#94A3B8", "rgba(148,163,184,0.12)"

TILDES = {
    "Portatil": "Portátil", "Movil": "Móvil", "Critica": "Crítica", "Bateria": "Batería",
    "Basica": "Básica", "Estandar": "Estándar", "reparacion": "reparación", "Perifericos": "Periféricos",
    "Telefono": "Teléfono", "Direccion": "Dirección", "Atencion": "Atención", "Espana": "España",
    "Mexico": "México", "Peru": "Perú", "Bogota": "Bogotá", "Distribucion": "Distribución",
    "Diseno": "Diseño", "Analitica": "Analítica", "Comunicacion": "Comunicación", "Gestion": "Gestión",
    "Colaboracion": "Colaboración", "Ofimatica": "Ofimática", "Logistica": "Logística", "Tecnico": "Técnico",
    "Disenador": "Diseñador", "Seleccion": "Selección", "Maria": "María", "Lucia": "Lucía", "Sofia": "Sofía",
    "Andres": "Andrés", "Raul": "Raúl", "Tomas": "Tomás", "Garcia": "García", "Rodriguez": "Rodríguez",
    "Lopez": "López", "Martinez": "Martínez", "Gonzalez": "González", "Perez": "Pérez", "Sanchez": "Sánchez",
    "Ramirez": "Ramírez", "Gomez": "Gómez", "Diaz": "Díaz", "Suarez": "Suárez",
}

# ================================================================== Estilos
# --ch = alto de un gráfico estándar. Se calcula con la altura de la ventana (100vh)
# para que cabeceras + KPIs + 2 filas de gráficos ocupen exactamente una pantalla.
CARD = ('[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]'
        ' > [data-testid="stElementContainer"] .card-h{})')
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..500,0..1,0&display=block');

:root { --card: rgba(13, 23, 42, 0.82); --borde: rgba(148, 163, 184, 0.30); --tenue: #94A3B8;
        --sombra: inset 0 1px 0 rgba(255,255,255,0.05), 0 6px 20px rgba(0,0,0,0.35);
        --ch: clamp(110px, calc((100vh - 432px) / 2), 420px); }

.stApp {
  font-family: 'Inter', sans-serif;
  background:
    radial-gradient(1200px 500px at 10% -10%, rgba(56, 189, 248, 0.14), transparent 60%),
    radial-gradient(900px 500px at 95% 0%, rgba(129, 140, 248, 0.14), transparent 60%),
    radial-gradient(700px 400px at 50% 110%, rgba(45, 212, 191, 0.08), transparent 60%),
    linear-gradient(rgba(148, 163, 184, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.045) 1px, transparent 1px),
    #070D1A;
  background-size: auto, auto, auto, 36px 36px, 36px 36px, auto;
  background-attachment: fixed;
}
[data-testid="stHeader"] { background: transparent; height: 2.2rem; }
.block-container { padding: 0.8rem 1.4rem 0.6rem; max-width: 1680px; }
.block-container [data-testid="stVerticalBlock"] { gap: 0.6rem; }
[data-testid="stSidebar"] { background: rgba(7, 13, 26, 0.94); border-right: 1px solid var(--borde); }
/* Streamlit resta 1rem bajo cada bloque de texto: lo compensamos para que nada se monte encima */
.hero, .kpi-grid, .card-h { margin-bottom: 1rem; }

.msr { font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; line-height: 1;
       display: inline-block; white-space: nowrap; letter-spacing: normal; text-transform: none;
       font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; vertical-align: middle; }

/* ---------- Cabecera compacta ---------- */
.hero { display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: center; justify-content: space-between;
        padding: 10px 18px; border-radius: 14px;
        background: linear-gradient(135deg, rgba(56,189,248,0.10), rgba(129,140,248,0.06) 60%, rgba(15,26,46,0.6));
        border: 1px solid var(--borde); }
.eyebrow { color: #38BDF8; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase;
           display: flex; align-items: center; gap: 6px; }
.hero-title { font-size: clamp(1.2rem, 1.9vw, 1.55rem); font-weight: 700; color: #F8FAFC; line-height: 1.2; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 0.76rem;
        color: #CBD5E1; background: rgba(15,23,42,0.7); border: 1px solid var(--borde); }

/* ---------- KPIs ---------- */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr)); gap: 10px; }
.kpi { background: var(--card); border: 1px solid var(--borde); border-radius: 12px; padding: 9px 12px; box-shadow: var(--sombra);
       position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: center; }
.kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--acc); }
.kpi-top { display: flex; align-items: center; gap: 8px; color: var(--tenue); font-size: 0.76rem; font-weight: 500;
           white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi-ico { width: 24px; height: 24px; border-radius: 7px; display: grid; place-items: center; font-size: 16px;
           color: var(--acc); background: color-mix(in srgb, var(--acc) 14%, transparent); flex: none; }
.kpi-val { font-size: clamp(1.15rem, 1.5vw, 1.4rem); font-weight: 700; color: #F8FAFC; margin: 3px 0 0; line-height: 1.25; }
.kpi-foot { font-size: 0.7rem; color: var(--tenue); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi-foot.bad { color: #FB7185; } .kpi-foot.good { color: #2DD4BF; } .kpi-foot.warn { color: #FBBF24; }
.kpi-grid.fill { height: calc(var(--ch) + 16px); grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: 1fr; gap: 8px; }
.kpi-grid.fill .kpi { padding: 6px 12px; }
@media (max-height: 760px) { .kpi-grid.fill .kpi-foot { display: none; } }

/* ---------- Tarjetas de gráficos ---------- */
.card-h { display: flex; gap: 8px; align-items: flex-start; padding-bottom: 6px;
          border-bottom: 1px solid rgba(148, 163, 184, 0.16); }
.card-h > div { flex: 1; }
.firma { flex: none !important; display: inline-flex; align-items: center; gap: 4px; font-size: 0.66rem;
         color: #7DD3FC; background: rgba(56,189,248,0.08); border: 1px solid rgba(56,189,248,0.25);
         padding: 2px 8px; border-radius: 999px; white-space: nowrap; margin-top: 1px; }
.card-ico { color: #38BDF8; font-size: 18px; margin-top: 1px; }
.card-t { color: #F1F5F9; font-weight: 600; font-size: 0.9rem; line-height: 1.25; }
.card-s { color: var(--tenue); font-size: 0.74rem; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-h > div { min-width: 0; }
.stPlotlyChart, .stPlotlyChart > div { height: var(--ch) !important; min-height: 0 !important; }
/* Nivelar: la última tarjeta de cada columna se estira hasta el fondo de la fila */
[data-testid="stColumn"] > [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stColumn"] > [data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stColumn"] > [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] { height: 100%; }
[data-testid="stColumn"] > [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"]
  > [data-testid="stVerticalBlockBorderWrapper"]:last-child { flex: 1 1 auto; }
.foot { color: #64748B; font-size: 0.72rem; text-align: center; margin-top: 12px; }

/* ---------- Pestañas ---------- */
[data-baseweb="tab-list"] { gap: 4px; background: rgba(15,23,42,0.65); padding: 4px; border-radius: 11px;
                            border: 1px solid var(--borde); flex-wrap: wrap; }
[data-baseweb="tab"] { border-radius: 8px; padding: 5px 12px; height: auto; }
[data-baseweb="tab"] p { font-size: 0.85rem; }
[data-baseweb="tab"][aria-selected="true"] { background: rgba(56,189,248,0.14); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }
[data-baseweb="tab-panel"] { padding-top: 0.6rem; }

/* ---------- Sidebar ---------- */
.brand { display: flex; align-items: center; gap: 10px; }
.brand-ico { width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center; font-size: 22px;
             background: linear-gradient(135deg, #38BDF8, #818CF8); color: #04121F; }
.brand-t { font-weight: 700; color: #F8FAFC; font-size: 1.05rem; line-height: 1.1; }
.brand-s { color: var(--tenue); font-size: 0.75rem; }

/* ---------- Móvil y tablet: scroll normal, gráficos de alto fijo ---------- */
@media (max-width: 900px), (max-height: 560px) {
  :root { --ch: 260px; }
}
@media (max-width: 640px) {
  .block-container { padding: 2.6rem 0.8rem 0.8rem; }
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .kpi-grid.fill { height: auto; }
  .chips { display: none; }
}
"""
CSS += CARD.format("") + """ {
  background: var(--card); border: 1px solid var(--borde) !important; border-radius: 14px !important;
  padding: 10px 14px !important; box-shadow: var(--sombra); }
""" + CARD.format("") + """ [data-testid="stVerticalBlock"] { gap: 0.3rem; }
""" + CARD.format(".tall") + """ .stPlotlyChart, """ + CARD.format(".tall") + """ .stPlotlyChart > div {
  height: calc(2 * var(--ch) + 78px) !important; }
""" + CARD.format(".half") + """ .stPlotlyChart, """ + CARD.format(".half") + """ .stPlotlyChart > div {
  height: calc(0.75 * var(--ch)) !important; }
""" + CARD.format(".tbl") + """ [data-testid="stDataFrameResizable"] { height: calc(var(--ch) - 8px) !important; }
""" + CARD.format(".tbl-l") + """ [data-testid="stDataFrameResizable"] { height: calc(1.25 * var(--ch) + 3px) !important; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ================================================================== Helpers de UI
def ico(nombre, tam=18):
    return f'<span class="msr" style="font-size:{tam}px">{nombre}</span>'


def kpis(items, clase=""):
    """items: lista de (icono, etiqueta, valor, pie, estado, color)."""
    html = "".join(
        f'<div class="kpi" style="--acc:{c}"><div class="kpi-top"><span class="kpi-ico msr">{i}</span>{l}</div>'
        f'<div class="kpi-val">{v}</div><div class="kpi-foot {e}">{p}</div></div>'
        for i, l, v, p, e, c in items)
    st.markdown(f'<div class="kpi-grid {clase}">{html}</div>', unsafe_allow_html=True)


def tarjeta(icono, titulo, sub="", clase=""):
    """Contenedor con borde + cabecera. clase: '' | 'tall' | 'half' | 'tbl' | 'tbl-l'."""
    cont = st.container(border=True)
    cont.markdown(
        f'<div class="card-h {clase}"><span class="card-ico msr">{icono}</span><div><div class="card-t">{titulo}</div>'
        f'<div class="card-s">{sub}</div></div></div>',
        unsafe_allow_html=True)
    return cont


def grafico(fig, leyenda="arriba"):
    """Sin alto fijo: el alto lo pone el CSS (--ch) y Plotly se adapta al contenedor."""
    pos = {
        "derecha": dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01),
        "dentro": dict(orientation="v", yanchor="top", y=1.0, xanchor="right", x=1.0, bgcolor="rgba(7,13,26,0.6)"),
        "dentro-izq": dict(orientation="h", yanchor="top", y=1.0, xanchor="left", x=0.0, bgcolor="rgba(7,13,26,0.6)"),
    }.get(leyenda, dict(orientation="h", yanchor="bottom", y=1.0, x=0))
    fig.update_layout(
        template="plotly_dark", autosize=True, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=6, r=6, t=6, b=6), font=dict(family="Inter, sans-serif", size=11, color=TENUE),
        legend=dict(**pos, title=None, font=dict(color=TEXTO, size=11)),
        hoverlabel=dict(bgcolor="#0F1A2E", bordercolor=CIAN, font=dict(color=TEXTO)),
    )
    fig.update_xaxes(gridcolor=REJILLA, zeroline=False, linecolor=REJILLA)
    fig.update_yaxes(gridcolor=REJILLA, zeroline=False, linecolor=REJILLA, tickfont_size=10)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


# ================================================================== Formato
def num(x, dec=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def eur(x):
    if abs(x) >= 1_000_000:
        return f"{num(x / 1_000_000, 2)} M€"
    if abs(x) >= 10_000:
        return f"{num(x / 1_000)} k€"
    return f"{num(x)} €"


def pct(x, dec=0):
    return "–" if x is None or np.isnan(x) else f"{num(x * 100, dec)} %"


def tildes(s: pd.Series) -> pd.Series:
    return s.map(lambda t: " ".join(TILDES.get(w, w) for w in t.split(" ")) if isinstance(t, str) else t)


# ================================================================== Datos
@st.cache_data
def cargar():
    leer = lambda f, **kw: pd.read_csv(DATA_DIR / f, encoding="utf-8-sig", **kw)
    act = leer("Activos.csv", parse_dates=["FechaCompra", "FinGarantia"], dtype={"EmpleadoID": str})
    inc = leer("Incidencias.csv", parse_dates=["FechaApertura", "FechaCierre"])
    emp = leer("Empleados.csv", dtype={"EmpleadoID": str})
    dep = leer("Departamentos.csv")
    ubi = leer("Ubicaciones.csv")
    sla = leer("SLA.csv")
    lic = leer("Licencias.csv", parse_dates=["FechaRenovacion"])

    for df, cols in [(act, ["TipoActivo", "Modelo", "Gama", "Estado"]), (inc, ["Categoria", "Prioridad", "Canal"]),
                     (emp, ["Empleado", "Puesto"]), (dep, ["Departamento"]), (ubi, ["Sede", "Ciudad", "Pais"]),
                     (sla, ["Prioridad"]), (lic, ["Categoria", "TipoLicencia"])]:
        for c in cols:
            df[c] = tildes(df[c])

    act = (act.merge(dep[["DeptoID", "Departamento"]], on="DeptoID", how="left")
              .merge(ubi[["UbicacionID", "Sede", "Ciudad"]], on="UbicacionID", how="left")
              .merge(emp[["EmpleadoID", "Empleado", "EstadoEmpleado"]], on="EmpleadoID", how="left"))
    act["Ciudad"] = act["Ciudad"].replace({"Ciudad de México": "CDMX"})  # etiqueta corta para gráficos
    act["Edad"] = (CORTE - act["FechaCompra"]).dt.days / 365.25
    act["FinVidaUtil"] = [f + pd.DateOffset(years=int(v)) for f, v in zip(act["FechaCompra"], act["VidaUtilAnios"])]
    act["Operativo"] = ~act["Estado"].isin(["Retirado", "Extraviado"])
    act["Renovar"] = act["Operativo"] & (act["FinVidaUtil"] <= CORTE)
    act["ValorContable"] = act["CosteCompra"] * (1 - act["Edad"] / act["VidaUtilAnios"]).clip(lower=0)
    act["Garantia"] = np.where(act["FinGarantia"] >= CORTE, "En garantía", "Fuera de garantía")
    act["RangoEdad"] = pd.cut(act["Edad"], [-np.inf, 1, 3, 5, np.inf],
                              labels=["0-1 años", "1-3 años", "3-5 años", "5+ años"])

    inc = (inc.merge(act[["ActivoID", "TipoActivo", "Modelo", "Fabricante", "Gama", "Sede", "Ciudad",
                          "Departamento", "FinGarantia"]], on="ActivoID", how="left")
              .merge(sla, on="Prioridad", how="left"))
    inc["CumpleSLA"] = np.where(inc["HorasResolucion"].notna(),
                                (inc["HorasResolucion"] <= inc["HorasSLA"]).astype(float), np.nan)

    lic = lic.merge(dep[["DeptoID", "Departamento"]], on="DeptoID", how="left")
    lic["CosteAnual"] = lic["LicenciasCompradas"] * lic["CosteUnitarioAnual"]
    lic["Ahorro"] = ((lic["LicenciasCompradas"] - np.ceil(lic["UsuariosActivos30d"] * 1.1)).clip(lower=0)
                     * lic["CosteUnitarioAnual"])
    lic["UsoReal"] = lic["UsuariosActivos30d"] / lic["LicenciasCompradas"]
    return act, inc, lic, sla


if not (DATA_DIR / "Activos.csv").exists():
    st.error(f"No encuentro los CSV. Copia la carpeta `datos` junto a app.py (buscado en: {DATA_DIR}).")
    st.stop()

act_all, inc_all, lic_all, sla = cargar()

# ================================================================== Sidebar
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-ico msr">hub</div><div><div class="brand-t">ITAM Control</div>'
        '<div class="brand-s">Grupo Andino Retail</div></div></div>', unsafe_allow_html=True)
    st.divider()
    sedes = st.multiselect(":material/location_on: Sede", sorted(act_all["Sede"].unique()), placeholder="Todas")
    deptos = st.multiselect(":material/apartment: Departamento", sorted(act_all["Departamento"].unique()),
                            placeholder="Todos")
    tipos = st.multiselect(":material/devices: Tipo de activo", sorted(act_all["TipoActivo"].unique()),
                           placeholder="Todos")
    anios = st.slider(":material/calendar_month: Años de incidencias", 2019, 2026, (2019, 2026))
    st.divider()
    with st.expander(":material/info: Definiciones"):
        st.markdown(
            "- **Operativo**: ni retirado ni extraviado.\n"
            "- **A renovar**: operativo y fuera de su vida útil.\n"
            "- **Valor contable**: depreciación lineal.\n"
            "- **SLA**: resuelta dentro de las horas objetivo de su prioridad.\n"
            "- **Ahorro**: licencias por encima de usuarios activos 30 días + 10 %."
        )
    st.markdown(f'<div class="foot">Elaborado por {AUTOR}<br>Datos ficticios · proyecto de portfolio</div>',
                unsafe_allow_html=True)


def filtrar(df, con_tipo=True):
    m = pd.Series(True, index=df.index)
    if sedes:
        m &= df["Sede"].isin(sedes)
    if deptos:
        m &= df["Departamento"].isin(deptos)
    if tipos and con_tipo:
        m &= df["TipoActivo"].isin(tipos)
    return df[m]


act = filtrar(act_all)
inc = filtrar(inc_all)
inc = inc[inc["FechaApertura"].dt.year.between(*anios)]
lic = lic_all[lic_all["Departamento"].isin(deptos)] if deptos else lic_all
op = act[act["Operativo"]]

# ================================================================== Cabecera
n_filtros = len(sedes) + len(deptos) + len(tipos)
txt_filtros = (f"{n_filtros} filtro{'s' if n_filtros != 1 else ''} activo{'s' if n_filtros != 1 else ''}"
               if n_filtros else "Sin filtros")
st.markdown(
    f"""<div class="hero"><div>
      <div class="eyebrow">{ico('monitoring', 14)} IT Asset Management · Informe para dirección</div>
      <div class="hero-title">Inventario de tecnología</div>
    </div><div class="chips">
      <span class="chip">{ico('event', 15)} Corte 31/10/2026</span>
      <span class="chip">{ico('filter_alt', 15)} {txt_filtros}</span>
    </div></div>""",
    unsafe_allow_html=True,
)

if op.empty:
    st.warning("No hay activos con esta combinación de filtros.", icon=":material/search_off:")
    st.stop()

t1, t2, t3, t4 = st.tabs([":material/space_dashboard: Resumen ejecutivo", ":material/autorenew: Ciclo de vida",
                          ":material/support_agent: Soporte", ":material/key: Licencias"])

port_act = act[act["TipoActivo"] == "Portátil"].groupby("Modelo").size()
port_inc = inc[inc["TipoActivo"] == "Portátil"].groupby("Modelo").size()
fuera_gar = (op["Garantia"] == "Fuera de garantía").mean()

# ================================================================== 1. Resumen
with t1:
    sla_global = inc["CumpleSLA"].mean()
    kpis([
        ("devices", "Activos operativos", num(len(op)), f"de {num(len(act))} registrados", "", CIAN),
        ("account_balance_wallet", "Valor contable", eur(op["ValorContable"].sum()),
         f"{pct(1 - op['ValorContable'].sum() / op['CosteCompra'].sum())} depreciado", "", INDIGO),
        ("gpp_maybe", "Fuera de garantía", pct(fuera_gar), "objetivo < 40 %", "bad" if fuera_gar > .4 else "good", ROSA),
        ("autorenew", "A renovar", num(op["Renovar"].sum()),
         eur(op.loc[op["Renovar"], "CosteCompra"].sum()) + " reposición", "warn", AMBAR),
        ("timer", "Cumplimiento SLA", pct(sla_global), "objetivo 90 %", "bad" if sla_global < .9 else "good", TEAL),
        ("savings", "Ahorro licencias", eur(lic["Ahorro"].sum()), "potencial anual", "good", TEAL),
    ])

    a, b = st.columns(2, gap="small")
    with a:
        por_sede = op.groupby("Ciudad").size().sort_values()
        with tarjeta("location_on", "Distribución del parque por sede",
                     f"{por_sede.idxmax()} concentra el {pct(por_sede.max() / por_sede.sum())} de los activos"):
            fig = px.bar(por_sede, orientation="h", text_auto=True, labels={"value": "", "Ciudad": ""})
            fig.update_traces(marker_color=[CIAN if s == por_sede.idxmax() else PIZARRA for s in por_sede.index],
                              textfont_color=TEXTO, marker_line_width=0)
            fig.update_layout(showlegend=False)
            fig.update_xaxes(visible=False)
            grafico(fig)
    with b:
        with tarjeta("category", "Composición del parque", "Activos operativos por tipo y estado"):
            estado = op.assign(Estado=op["Estado"].replace({"En servicio": "En uso", "Asignado": "En uso"}))
            tabla = estado.groupby(["TipoActivo", "Estado"]).size().reset_index(name="Activos")
            orden = op["TipoActivo"].value_counts().index.tolist()
            fig = px.bar(tabla, x="TipoActivo", y="Activos", color="Estado",
                         category_orders={"TipoActivo": orden, "Estado": ["En uso", "En stock", "En reparación"]},
                         color_discrete_map={"En uso": CIAN, "En stock": PIZARRA, "En reparación": AMBAR},
                         labels={"TipoActivo": "", "Activos": ""})
            fig.update_traces(marker_line_width=0)
            fig.update_xaxes(tickangle=0, tickfont_size=10)
            grafico(fig, leyenda="dentro")

    a, b = st.columns([3, 2], gap="small")
    with a:
        with tarjeta("payments", "Inversión anual en tecnología", "Compras por año · 2026 hasta octubre"):
            inv = act.groupby(act["FechaCompra"].dt.year)["CosteCompra"].sum().reset_index()
            inv.columns = ["Año", "Inversión"]
            fig = px.bar(inv, x="Año", y="Inversión", text=inv["Inversión"].map(eur))
            fig.update_traces(marker_color=[PIZARRA if y == 2026 else INDIGO for y in inv["Año"]],
                              textposition="inside", insidetextanchor="end", textfont_color=TEXTO,
                              marker_line_width=0)
            fig.update_yaxes(visible=False)
            fig.update_xaxes(dtick=1, title=None)
            grafico(fig)
    with b:
        with tarjeta("warning", "Riesgos a vigilar", "Requieren acción inmediata"):
            kpis([
                ("desktop_windows", "Windows 10 sin soporte", num((op["SistemaOperativo"] == "Windows 10").sum()),
                 "Riesgo de seguridad", "bad", ROSA),
                ("person_off", "Asignados a ex-empleados", num((op["EstadoEmpleado"] == "Baja").sum()),
                 "Recuperar en offboarding", "warn", AMBAR),
                ("location_off", "Extraviados", num((act["Estado"] == "Extraviado").sum()), "Revisar inventario",
                 "warn", AMBAR),
                ("pending_actions", "Incidencias abiertas", num(inc["FechaCierre"].isna().sum()), "En curso", "", CIAN),
            ], clase="fill")

# ================================================================== 2. Ciclo de vida
with t2:
    ren = op[op["Renovar"]]
    kpis([
        ("autorenew", "Activos a renovar", num(len(ren)), f"{pct(len(ren) / len(op))} del parque", "warn", AMBAR),
        ("euro", "Coste de reposición", eur(ren["CosteCompra"].sum()), "presupuesto estimado", "", INDIGO),
        ("hourglass", "Edad media", f"{num(op['Edad'].mean(), 1)} años", "parque operativo", "", CIAN),
        ("desktop_windows", "Windows 10", num((op["SistemaOperativo"] == "Windows 10").sum()),
         "sin soporte desde oct-2025", "bad", ROSA),
        ("gpp_maybe", "Fuera de garantía", pct(fuera_gar), "del parque operativo", "bad", ROSA),
    ])
    a, b = st.columns(2, gap="small")
    with a:
        pct_dep = op.groupby("Departamento")["Renovar"].mean().sort_values(ascending=False)
        with tarjeta("grid_view", "Antigüedad del parque por departamento",
                     f"{pct_dep.index[0]} tiene el parque más antiguo ({pct(pct_dep.iloc[0])} a renovar)"):
            mapa = pd.crosstab(op["Departamento"], op["RangoEdad"], normalize="index").T
            mapa.columns = [d.replace(" ", "<br>", 1) for d in mapa.columns]
            fig = px.imshow(mapa, text_auto=".0%", aspect="auto",
                            color_continuous_scale=[[0, "#0B1730"], [0.5, "#1E4E8C"], [1, CIAN]],
                            labels=dict(x="", y="", color=""))
            fig.update_layout(coloraxis_showscale=False)
            fig.update_xaxes(tickangle=0, tickfont_size=10, side="bottom")
            fig.update_traces(textfont_size=10)
            grafico(fig)
    with b:
        cr = ren.groupby("Departamento")["CosteCompra"].sum().sort_values()
        with tarjeta("request_quote", "Presupuesto de renovación por departamento",
                     "Coste de reposición de los equipos a renovar"):
            if cr.empty:
                st.info("No hay equipos a renovar con los filtros actuales.")
            else:
                cr = cr.sort_values(ascending=False)
                fig = go.Figure(go.Bar(x=[d.replace(" ", "<br>", 1) for d in cr.index], y=cr.values,
                                       text=cr.map(eur), textposition="inside", insidetextanchor="end",
                                       textfont=dict(color=TEXTO, size=10), marker_line_width=0,
                                       marker_color=[AMBAR if d == cr.idxmax() else PIZARRA for d in cr.index]))
                fig.update_yaxes(visible=False)
                fig.update_xaxes(tickangle=0, tickfont_size=10)
                grafico(fig)

    a, b = st.columns([1, 2], gap="small")
    with a:
        with tarjeta("verified_user", "Cobertura de garantía",
                     f"<span style='color:{ROSA}'>■</span> Sin garantía · <span style='color:{TEAL}'>■</span> Con garantía"):
            g = op["Garantia"].value_counts()
            fig = go.Figure(go.Pie(values=g.values, labels=g.index, hole=0.7, sort=False, textinfo="none",
                                   marker=dict(colors=[ROSA if x == "Fuera de garantía" else TEAL for x in g.index],
                                               line=dict(color="#070D1A", width=2))))
            fig.add_annotation(text=f"<b>{pct(fuera_gar)}</b>", showarrow=False, font=dict(size=18, color=ROSA))
            fig.update_layout(showlegend=False)
            grafico(fig)
    with b:
        with tarjeta("list_alt", "Equipos a renovar", "Ordenados por antigüedad", clase="tbl"):
            st.dataframe(
                ren.sort_values("Edad", ascending=False)[
                    ["ActivoID", "Modelo", "Departamento", "Sede", "Empleado", "SistemaOperativo", "Edad", "CosteCompra"]],
                hide_index=True, use_container_width=True,
                column_config={
                    "Edad": st.column_config.NumberColumn("Edad (años)", format="%.1f"),
                    "CosteCompra": st.column_config.NumberColumn("Coste", format="%d €"),
                    "SistemaOperativo": "Sistema operativo",
                },
            )

# ================================================================== 3. Soporte
with t3:
    base = inc_all.pipe(filtrar)
    ult12 = base[base["FechaApertura"] > CORTE - pd.Timedelta(days=365)]
    prev12 = base[base["FechaApertura"].between(CORTE - pd.Timedelta(days=730), CORTE - pd.Timedelta(days=365))]
    var = (len(ult12) - len(prev12)) / len(prev12) if len(prev12) else np.nan
    kpis([
        ("confirmation_number", "Incidencias", num(len(inc)), f"{anios[0]}–{anios[1]}", "", CIAN),
        ("pending_actions", "Abiertas", num(inc["FechaCierre"].isna().sum()), "pendientes de cierre", "", AMBAR),
        ("timer", "MTTR", f"{num(inc['HorasResolucion'].mean(), 1)} h", "tiempo medio de resolución", "", INDIGO),
        ("verified", "Cumplimiento SLA", pct(inc["CumpleSLA"].mean(), 1), "objetivo 90 %",
         "bad" if inc["CumpleSLA"].mean() < .9 else "good", TEAL),
        ("build", "Coste reparaciones", eur(inc["CosteReparacion"].sum()), "equipos sin garantía", "", ROSA),
        ("trending_up", "Últimos 12 meses", num(len(ult12)), f"{'+' if var > 0 else ''}{pct(var, 1)} vs año anterior",
         "bad" if var > 0 else "good", CIAN),
    ])
    a, b = st.columns(2, gap="small")
    with a:
        with tarjeta("show_chart", "Evolución mensual de incidencias", "Tickets abiertos por mes"):
            mens = inc.groupby(inc["FechaApertura"].dt.to_period("M")).size()
            mens.index = mens.index.to_timestamp()
            fig = go.Figure(go.Scatter(x=mens.index, y=mens.values, mode="lines", line=dict(color=CIAN, width=2),
                                       fill="tozeroy", fillcolor="rgba(56,189,248,0.12)"))
            grafico(fig)
    with b:
        tasa = (port_inc.reindex(port_act.index).fillna(0) / port_act * 100).sort_values()
        peor = tasa.idxmax() if len(tasa) else None
        if peor and len(tasa) > 1:
            veces = tasa.max() / tasa.drop(peor).mean()
            sub = f"{peor}: {num(veces, 1)}× más fallos que la media del resto"
        else:
            sub = peor or "Sin portátiles con estos filtros"
        with tarjeta("report", "Incidencias por cada 100 portátiles", sub):
            if peor:
                t = tasa.sort_values(ascending=False)
                etiquetas = [m.replace(" Portátil ", "<br>") for m in t.index]
                fig = go.Figure(go.Bar(x=etiquetas, y=t.values, text=[f"{v:.0f}" for v in t.values],
                                       textposition="inside", insidetextanchor="end",
                                       textfont=dict(color=TEXTO, size=10), marker_line_width=0,
                                       marker_color=[ROSA if m == peor else PIZARRA for m in t.index]))
                fig.update_layout(bargap=0.25)
                fig.update_yaxes(visible=False)
                fig.update_xaxes(tickangle=0, tickfont_size=9)
                grafico(fig)

    cerradas = inc[inc["HorasResolucion"].notna()]
    a, b = st.columns(2, gap="small")
    if cerradas.empty:
        a.info("No hay incidencias cerradas con los filtros actuales.")
    else:
        with a:
            ps = cerradas.groupby("Ciudad").agg(MTTR=("HorasResolucion", "mean"),
                                              SLA=("CumpleSLA", "mean")).sort_values("MTTR")
            lenta = ps["MTTR"].idxmax()
            with tarjeta("speed", "Velocidad de resolución por sede",
                         f"{lenta}: {num(ps['MTTR'].max())} h de media y {pct(ps.loc[lenta, 'SLA'])} de SLA"):
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_bar(x=ps.index, y=ps["MTTR"], name="MTTR (h)", marker_line_width=0,
                            marker_color=[ROSA if s == lenta else INDIGO for s in ps.index])
                fig.add_scatter(x=ps.index, y=ps["SLA"] * 100, name="% SLA", mode="lines+markers",
                                line=dict(color=AMBAR, width=2), marker=dict(size=7), secondary_y=True)
                fig.update_yaxes(title_text=None, secondary_y=False)
                fig.update_yaxes(title_text=None, range=[0, 100], ticksuffix=" %", secondary_y=True, showgrid=False)
                fig.update_xaxes(tickangle=0)
                fig.update_yaxes(range=[0, ps["MTTR"].max() * 1.35], secondary_y=False)
                grafico(fig, leyenda="dentro-izq")
        with b:
            with tarjeta("table_chart", "Cumplimiento del SLA", "Por prioridad y sede"):
                orden_p = [p for p in sla.sort_values("OrdenPrioridad")["Prioridad"] if p in set(cerradas["Prioridad"])]
                piv = cerradas.pivot_table(index="Prioridad", columns="Ciudad", values="CumpleSLA",
                                           aggfunc="mean").reindex(orden_p)
                fig = px.imshow(piv, text_auto=".0%", zmin=0, zmax=1, aspect="auto",
                                color_continuous_scale=[[0, "#7F1D3A"], [0.5, "#92400E"], [1, "#0F766E"]],
                                labels=dict(x="", y="", color=""))
                fig.update_layout(coloraxis_showscale=False)
                fig.update_xaxes(tickangle=0, side="bottom")
                fig.update_traces(textfont_size=10)
                grafico(fig)

# ================================================================== 4. Licencias
with t4:
    ventana = lic["FechaRenovacion"].between(CORTE + pd.Timedelta(days=1), CORTE + pd.Timedelta(days=90))
    uso = lic["UsuariosActivos30d"].sum() / lic["LicenciasCompradas"].sum() if len(lic) else np.nan
    coste = lic["CosteAnual"].sum()
    kpis([
        ("receipt_long", "Coste anual", eur(coste), f"{len(lic)} productos", "", INDIGO),
        ("savings", "Ahorro potencial", eur(lic["Ahorro"].sum()),
         f"{pct(lic['Ahorro'].sum() / coste)} del gasto" if coste else "", "good", TEAL),
        ("group", "Uso real", pct(uso, 1), "objetivo 85 %", "bad" if uso < .85 else "good", CIAN),
        ("event_upcoming", "Renovaciones 90 días", num(ventana.sum()), eur(lic.loc[ventana, "CosteAnual"].sum()),
         "warn", AMBAR),
    ])
    a, b = st.columns([3, 2], gap="small")
    with a:
        top = lic.sort_values("Ahorro", ascending=False).head(3)["Software"].tolist()
        with tarjeta("key", "Licencias compradas frente a uso real",
                     ("Mayor ahorro en " + ", ".join(top[:-1]) + " y " + top[-1]) if len(top) > 1 else "",
                     clase="tall"):
            d = lic.sort_values("Ahorro")
            fig = go.Figure()
            fig.add_bar(y=d["Software"], x=d["LicenciasCompradas"], orientation="h", name="Compradas",
                        marker_color=PIZARRA, marker_line_width=0)
            fig.add_bar(y=d["Software"], x=d["UsuariosActivos30d"], orientation="h", name="Usuarios activos 30 días",
                        marker_color=CIAN, marker_line_width=0)
            fig.update_layout(barmode="overlay", bargap=0.3)
            fig.update_xaxes(type="log", title=None)
            grafico(fig)
    with b:
        with tarjeta("speed", "Uso real frente a objetivo", "Usuarios activos / licencias compradas", clase="half"):
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=(uso or 0) * 100, domain={"x": [0.02, 0.74], "y": [0.15, 0.85]},
                number={"suffix": " %", "valueformat": ".1f", "font": {"color": TEXTO, "size": 26}},
                gauge={"shape": "bullet", "axis": {"range": [0, 100], "tickcolor": TENUE, "ticksuffix": "%"},
                       "bar": {"color": CIAN, "thickness": 0.45},
                       "bgcolor": "rgba(148,163,184,0.08)", "borderwidth": 0,
                       "steps": [{"range": [0, 60], "color": "rgba(251,113,133,0.18)"},
                                 {"range": [60, 85], "color": "rgba(251,191,36,0.15)"},
                                 {"range": [85, 100], "color": "rgba(45,212,191,0.18)"}],
                       "threshold": {"line": {"color": TEAL, "width": 3}, "thickness": 0.9, "value": 85}}))
            fig.update_layout(margin=dict(l=8, r=16, t=6, b=6))
            grafico(fig)
        with tarjeta("savings", "Detalle por software", "Ordenado por ahorro potencial", clase="tbl-l"):
            st.dataframe(
                lic.sort_values("Ahorro", ascending=False).assign(Uso=lic["UsoReal"] * 100)[
                    ["Software", "Uso", "Ahorro"]],
                hide_index=True, use_container_width=True,
                column_config={
                    "Software": st.column_config.TextColumn("Software", width="medium"),
                    "Uso": st.column_config.ProgressColumn("Uso", format="%.0f %%", min_value=0, max_value=100,
                                                           width="small"),
                    "Ahorro": st.column_config.NumberColumn("Ahorro", format="%d €", width="small"),
                },
            )
