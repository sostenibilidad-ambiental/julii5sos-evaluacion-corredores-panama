"""Punto de entrada ligero para Streamlit Community Cloud.

El armazón visual (navegación, héroes, cifras, módulos y pie) reproduce el
portal HTML de referencia «Conectividad Panamá»: azul institucional con corte
diagonal y franjas verde/amarilla, títulos azules sobre blanco, tarjetas gris
azulado y botones píldora. La lógica de análisis permanece en
``app_experiencia.py``.
"""

import json
import runpy
from functools import lru_cache
from pathlib import Path

import streamlit as st

from metodologia_indice import (
    PERIODOS_ANALISIS,
    PESOS_INDICE,
    PUNTAJE_MAXIMO,
    UMBRALES_INDICE,
)
from modos_app import (
    MODO_CORREDORES,
    MODO_INTEGRAL,
    MODO_TERRITORIAL,
    MODOS_ANALISIS,
)


st.set_page_config(
    page_title="Visor CHCP | Preevaluación territorial y conectividad",
    page_icon=":material/map:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.session_state["_pagina_configurada"] = True

SECCION_MAPA = "Mapa"
SECCION_METODO = "Metodología y ayuda"
SECCION_ACERCA = "Acerca del visor"
SECCIONES_PRINCIPALES = (
    SECCION_MAPA,
    SECCION_METODO,
    SECCION_ACERCA,
)

SITIO = {
    "nombre": "Visor CHCP",
    "subtitulo": "Cuenca Hidrográfica del Canal de Panamá",
    "atribucion": (
        "Fuentes: JRC TMF, Hansen GFC, ESRI LULC, GEDI/OpenForis y Sentinel-2 "
        "(Copernicus), procesadas en Google Earth Engine. Corredores y puntos "
        "críticos: Fundación Almanaque Azul (2024.05). Bosque y otros usos 2021: "
        "SINIA–MiAMBIENTE. Resultado indicativo: no sustituye la verificación de campo."
    ),
}

DATOS = Path(__file__).with_name("data")


# ---------------------------------------------------------------------------
# Estilos del portal
# ---------------------------------------------------------------------------

ESTILO_PORTAL = """
<style>
:root{
  --azul:#0a4393;--azul-2:#1d529b;--azul-tinta:#062a5e;--azul-suave:#eef1f7;
  --azul-linea:#d6deeb;--azul-medio:#6085b9;--verde:#77cc09;--verde-osc:#4f8f00;
  --amarillo:#fabc20;--ink:#1b2433;--muted:#566176;--line:#e1e6ee;--bg-2:#f6f8fb;
  --r:6px;--shadow:0 1px 2px rgba(10,30,70,.06),0 8px 24px rgba(10,30,70,.08);
  /* margen lateral: centra el contenido a 1180 px y permite secciones a sangre */
  --g:max(20px,calc((100vw - 1180px)/2));
  /* compatibilidad con clases heredadas */
  --verde-oscuro:var(--azul-tinta);--suave:var(--muted);--borde:var(--azul-linea);
  --fondo:#fff;--claro:var(--azul-suave);--acento:var(--verde);
}
.stApp{background:#fff;color:var(--ink);}
/* cabecera nativa: solo se conserva el botón para volver a abrir el panel lateral */
header[data-testid="stHeader"]{background:transparent;height:0;min-height:0;overflow:visible;z-index:1000;}
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],
[data-testid="stDecoration"]{display:none!important;}
[data-testid="stExpandSidebarButton"]{color:#fff!important;background:var(--azul-tinta)!important;
  border-radius:999px;margin-top:6px;}
[data-testid="stExpandSidebarButton"] *{color:#fff!important;}
/* los bloques <style> no ocupan espacio en la composición */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style){display:none;}
.stApp .wm b,.stApp .wm small{color:#fff!important;}

/* ---- panel lateral del visor (modelo «Plataforma») ---- */
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--line);}
[data-testid="stSidebarHeader"]{background:var(--azul);height:83px;margin:-5.6px -20px 18px -30px!important;
  padding:0 30px!important;width:auto!important;box-sizing:border-box;
  border-bottom:1px solid rgba(255,255,255,.18);}
[data-testid="stSidebarHeader"] button,[data-testid="stSidebarHeader"] button *{color:#fff!important;}
[data-testid="stSidebar"] h2{font-size:12.5px!important;font-weight:700!important;text-transform:uppercase;
  letter-spacing:.04em;color:var(--azul)!important;display:inline-block;padding:0 4px 10px!important;
  box-shadow:inset 0 -3px 0 var(--verde);margin-bottom:6px;}
[data-testid="stSidebar"] hr{border-color:var(--line);}
[data-testid="stSidebar"] .stButton button{border-radius:999px!important;font-weight:700;}
[data-testid="stSidebar"] .stButton button[kind="primary"]{background:var(--azul)!important;border-color:var(--azul)!important;}
[data-testid="stSidebar"] [data-testid="stExpander"] details{background:var(--azul-suave);border:0;border-radius:var(--r);}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p{font-weight:700;color:var(--azul);}
.block-container{padding:0 var(--g) 0!important;max-width:none!important;}
button,[role="button"]{min-height:44px;touch-action:manipulation;}
:focus-visible{outline:2px solid var(--verde)!important;outline-offset:2px;}
.stApp h1,.stApp h2,.stApp h3{letter-spacing:-.01em;}

/* ---- secciones a sangre ---- */
.st-key-portal_nav,[class*="st-key-heroe_"],[class*="st-key-sec_"],.st-key-pie{
  width:calc(100% + 2*var(--g))!important;max-width:none!important;margin-inline:calc(-1*var(--g))!important;
  padding-inline:var(--g);
}

/* ---- encabezado ---- */
.st-key-portal_nav{background:var(--azul);color:#fff;gap:0!important;
  position:sticky;top:0;z-index:999;}
.portal-util{display:flex;justify-content:flex-end;gap:18px;font-size:12.5px;padding-top:12px;}
.portal-util span{color:#fff;opacity:.92;}
.st-key-portal_nav [data-testid="stHorizontalBlock"]{
  padding-block:10px 12px;border-bottom:1px solid rgba(255,255,255,.18);align-items:center;}
.wm{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;}
.wm svg{width:40px;height:40px;flex:none;}
.wm b{display:block;font-size:22px;font-weight:700;letter-spacing:-.01em;line-height:1;color:#fff;}
.wm small{display:block;font-size:8.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  line-height:1.15;margin-top:4px;opacity:.9;color:#fff;}
.st-key-portal_nav [data-testid="stButtonGroup"]{justify-content:flex-end;}
.st-key-portal_nav [data-testid="stButtonGroup"] > div{gap:2px;justify-content:flex-end;flex-wrap:wrap;}
.st-key-portal_nav [data-testid="stButtonGroup"] button{
  background:transparent!important;border:0!important;border-radius:0!important;color:#fff!important;
  font-size:12.5px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:8px 10px;
  box-shadow:none!important;flex:0 0 auto!important;width:auto!important;min-height:44px;}
.st-key-portal_nav [data-testid="stButtonGroup"] button p{color:#fff!important;font-weight:700;font-size:12.5px;}
.st-key-portal_nav [data-testid="stButtonGroup"] button::after{
  content:"";display:inline-block;width:6px;height:6px;margin-left:8px;
  border-right:2px solid var(--verde);border-bottom:2px solid var(--verde);transform:rotate(45deg) translate(-2px,-2px);}
.st-key-portal_nav [data-testid="stButtonGroup"] button:hover{background:rgba(255,255,255,.1)!important;}
.st-key-portal_nav [data-testid="stButtonGroup"] button[kind*="Active"],
.st-key-portal_nav [data-testid="stButtonGroup"] button[aria-checked="true"]{
  box-shadow:inset 0 -3px 0 var(--verde)!important;}
.pill{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:8px 16px;font-size:12.5px;
  font-weight:700;white-space:nowrap;background:#fff;color:var(--azul);float:right;}
.pill svg{width:14px;height:14px;}

/* ---- héroe ---- */
[class*="st-key-heroe_"]{position:relative;overflow:hidden;background:var(--azul);color:#fff;
  padding-top:30px;padding-bottom:150px;gap:0!important;}
.st-key-heroe_pagina{padding-top:24px;padding-bottom:112px;}
[class*="st-key-heroe_"] h1{font-size:clamp(32px,4.4vw,50px)!important;font-weight:500!important;
  letter-spacing:-.02em;margin:24px 0 0;max-width:22ch;color:#fff!important;line-height:1.15;padding:0;}
[class*="st-key-heroe_"] .lead{font-size:15px;line-height:1.6;max-width:56ch;margin-top:22px;
  text-align:justify;hyphens:auto;color:#fff;}
[class*="st-key-heroe_"] .bc{font-size:13px;color:#fff;}
[class*="st-key-heroe_"] .bc a,[class*="st-key-heroe_"] .bc u{color:#fff;opacity:.85;}
[class*="st-key-heroe_"] .bc span{opacity:.6;margin:0 6px;}
[class*="st-key-heroe_"] .bc + h1{margin-top:22px;}
.hero-cut{position:absolute;left:0;right:0;bottom:-1px;width:100%;height:150px;display:block;pointer-events:none;}
.st-key-heroe_pagina .hero-cut{height:110px;}
[class*="st-key-heroe_"] [data-testid="stElementContainer"]:has(.hero-cut){position:static;}
[class*="st-key-heroe_"] [data-testid="stMarkdownContainer"]:has(.hero-cut){position:static;}
.st-key-acciones_heroe{margin-top:28px;gap:12px!important;}
.st-key-acciones_heroe button{border-radius:999px!important;padding:9px 20px!important;font-weight:700;
  border:1.5px solid rgba(255,255,255,.85)!important;background:transparent!important;color:#fff!important;}
.st-key-acciones_heroe button p{font-weight:700;font-size:13.5px;}
.st-key-acciones_heroe button:hover{background:rgba(255,255,255,.12)!important;}
.st-key-acciones_heroe button[kind="primary"]{background:#fff!important;color:var(--azul)!important;border-color:#fff!important;}
.st-key-acciones_heroe button[kind="primary"]:hover{background:var(--azul-suave)!important;}

/* ---- secciones ---- */
[class*="st-key-sec_"]{padding-block:56px;}
.st-key-sec_meta{padding-block:20px 0;}
[class*="st-key-sec_gris"]{background:var(--bg-2);}
.sec-c{text-align:center;display:flex;flex-direction:column;align-items:center;gap:14px;margin-bottom:34px;}
.sec-c h2,.sec-h2{font-size:clamp(26px,3vw,34px)!important;color:var(--azul)!important;font-weight:700!important;
  padding:0!important;margin:0;}
.sec-c p{max-width:72ch;color:var(--ink);text-align:justify;margin:0;}
.eyebrow{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--azul);}
.h-reg{font-size:22px!important;color:var(--azul)!important;font-weight:500!important;margin:0 0 14px!important;padding:0!important;}
.h-sub{font-size:26px!important;color:var(--azul)!important;font-weight:700!important;margin:0 0 14px!important;padding:0!important;}
.prose p{margin:0 0 14px;line-height:1.55;}
.meta{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));background:var(--azul-suave);border-radius:var(--r);}
.meta div{display:flex;flex-direction:column;gap:3px;padding:16px 18px;}
.meta div+div{border-left:1px solid var(--azul-linea);}
.meta span{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--azul-medio);}
.meta b{font-size:14.5px;color:var(--azul);}
.figs{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px;}
.fig{background:var(--azul-suave);border-radius:var(--r);padding:20px 20px 18px;display:flex;flex-direction:column;gap:4px;}
.fig span{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--azul-medio);}
.fig b{font-size:36px;font-weight:700;color:var(--azul);line-height:1.05;letter-spacing:-.02em;font-variant-numeric:tabular-nums;}
.fig p{font-size:12.5px;color:var(--muted);margin:0;line-height:1.5;}

/* ---- tarjetas de módulo ---- */
[class*="st-key-modulo_"]{background:var(--azul-suave);border-radius:var(--r);padding:26px 26px 14px;
  height:100%;gap:12px!important;transition:box-shadow .15s,transform .15s;}
.st-key-sec_gris_modulos [data-testid="stHorizontalBlock"]{align-items:stretch;}
.st-key-sec_gris_modulos [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
.st-key-sec_gris_modulos [data-testid="stColumn"] > div{height:100%;}
.st-key-sec_gris_modulos [data-testid="stColumn"] [data-testid="stLayoutWrapper"]{flex:1 1 auto;}
[class*="st-key-modulo_"]{flex:1 1 auto;min-height:100%;}
[class*="st-key-modulo_"]:hover{box-shadow:var(--shadow);transform:translateY(-2px);}
.card-date{font-size:11.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--azul);}
.card-h3{font-size:19px!important;color:var(--azul)!important;line-height:1.25!important;margin:12px 0 0!important;padding:0!important;font-weight:700!important;}
.stApp p.card-p{font-size:13.5px!important;color:var(--ink);margin:12px 0 0;line-height:1.55;}
.stApp p.card-q{font-size:13.5px!important;color:var(--azul-tinta);font-weight:700;margin:12px 0 0;line-height:1.45;}
.stApp p.card-res{font-size:13px!important;color:var(--muted);margin:10px 0 0;line-height:1.5;}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px;}
.tag{display:inline-block;white-space:nowrap;font-size:10.5px;font-weight:700;letter-spacing:.03em;border-radius:4px;
  padding:2px 7px;border:1px solid var(--azul-linea);color:var(--muted);background:#fff;}
.tag.demo{border-color:#f7dc95;background:#fff8e6;color:#8a6200;}
.tag.real{border-color:#cfe9ad;background:#f2fae7;color:var(--verde-osc);}
[class*="st-key-modulo_"] .stButton{margin-top:auto;}
[class*="st-key-modulo_"] .stButton button > div{flex:1;justify-content:flex-start;}
[class*="st-key-modulo_"] .stButton button{width:100%;justify-content:space-between;text-align:left;background:transparent!important;
  border:0!important;padding:0!important;color:var(--azul)!important;box-shadow:none!important;}
[class*="st-key-modulo_"] .stButton button p{font-weight:700;font-size:14px;color:var(--azul)!important;}
[class*="st-key-modulo_"] .stButton button::after{content:"";width:8px;height:8px;flex:none;
  border-right:2px solid var(--verde);border-bottom:2px solid var(--verde);transform:rotate(-45deg);margin-right:4px;}
[class*="st-key-modulo_"] .stButton button:hover p{text-decoration:underline;}
.note-p{display:flex;gap:10px;align-items:center;justify-content:center;font-size:12.5px;color:var(--muted);
  text-align:center;flex-wrap:wrap;margin-top:26px;}

/* ---- flujo circular ---- */
.flowc{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:22px;}
.flowc .st{display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px;position:relative;margin:0;}
.flowc .circ{width:120px;height:120px;border-radius:50%;background:var(--azul-suave);border:2px solid var(--azul);
  display:grid;place-items:center;color:var(--azul);position:relative;z-index:1;}
.flowc .circ svg{width:46px;height:46px;}
.flowc .st:last-child .circ{background:var(--azul);color:#fff;}
.flowc .circ::after{content:"";position:absolute;inset:-9px;border-radius:50%;border:1.5px solid var(--verde);
  clip-path:polygon(50% 0,100% 0,100% 50%,50% 50%);}
.flowc .st:not(:last-child)::after{content:"";position:absolute;top:60px;left:calc(50% + 70px);
  width:calc(100% + 22px - 140px);border-top:2px dashed var(--azul-linea);}
.flowc .eyebrow{color:var(--azul-medio);}
.flowc h3{font-size:17px!important;color:var(--azul)!important;margin:0!important;padding:0!important;font-weight:700!important;}
.flowc p{font-size:13px;color:var(--muted);max-width:26ch;margin:0;}

/* ---- listas, tablas, citas ---- */
.qlist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px;}
.qlist li{background:var(--azul-suave);border-radius:var(--r);padding:14px 16px;margin:0;}
.qlist b{display:block;color:var(--azul);}
.qlist span{color:var(--muted);font-size:13.5px;}
[class*="st-key-sec_gris"] .qlist li{background:#fff;}
.tbl{overflow-x:auto;background:#fff;}
.tbl table{border-collapse:collapse;width:100%;font-size:13.5px;border:0;}
.tbl th{text-align:left;font-size:12.5px;font-weight:700;color:var(--azul);padding:12px 14px;border:0;
  border-bottom:2px solid var(--azul);background:#fff;}
.tbl td{padding:13px 14px;border:0;border-bottom:1px solid var(--line);vertical-align:top;}
.tbl td:first-child{font-weight:700;}
.dot{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin-right:6px;}
.dot.ok{background:var(--verde);box-shadow:inset 0 0 0 3px #e9f7d6;}
.dot.ctx{background:var(--amarillo);box-shadow:inset 0 0 0 3px #fff3cf;}
.cita{background:var(--azul-suave);border-left:4px solid var(--verde);border-radius:var(--r);padding:16px 18px;
  font-size:13.5px;line-height:1.6;margin:18px 0 0;}
[class*="st-key-sec_"] [data-testid="stExpander"] details{background:var(--azul-suave);border:0;border-radius:var(--r);}
[class*="st-key-sec_"] [data-testid="stExpander"] summary{font-weight:700;color:var(--azul);font-size:16px;padding:16px 20px;}
[class*="st-key-sec_"] [data-testid="stExpander"] summary p{font-weight:700;color:var(--azul);font-size:16px;}
.st-key-sec_accion .stButton button{padding:9px 28px!important;}
.st-key-sec_accion .stButton button p{font-weight:700;}
.st-key-sec_accion .stButton button,[class*="st-key-sec_"] .stButton button[kind="primary"]{
  background:var(--azul)!important;border-color:var(--azul)!important;color:#fff!important;border-radius:999px!important;
  font-weight:700;}
[class*="st-key-sec_"] .stButton button[kind="primary"]:hover{background:var(--azul-tinta)!important;}

/* ---- pie ---- */
.st-key-pie{background:var(--azul);color:#fff;padding-block:34px;}
.foot{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;}
.foot .wm b{font-size:18px;}
.foot p{font-size:12px;opacity:.85;max-width:60ch;color:#fff;margin:0;line-height:1.55;}

/* ---- clases heredadas usadas por el visor ---- */
.nota-alcance{padding:.9rem 1rem;border-left:4px solid var(--verde);background:var(--azul-suave);
  color:var(--ink);line-height:1.6;margin:.75rem 0 1rem;border-radius:var(--r);}
.texto-legible{max-width:75ch;color:var(--muted);line-height:1.65;}

@media(max-width:1000px){.figs{grid-template-columns:repeat(2,minmax(0,1fr));}
  .flowc{grid-template-columns:1fr 1fr;row-gap:34px;}.flowc .st::after{display:none;}}
@media(max-width:900px){.meta{grid-template-columns:repeat(2,minmax(0,1fr));}
  .meta div+div{border-left:0;}.meta div{border-top:1px solid var(--azul-linea);}}
@media(max-width:640px){.portal-util{display:none;}.pill{display:none;}
  [class*="st-key-heroe_"]{padding-bottom:100px;}.hero-cut{height:90px;}
  .st-key-portal_nav{position:relative;}}
@media(max-width:440px){.figs,.flowc{grid-template-columns:1fr;}}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;
    scroll-behavior:auto!important;transition-duration:.01ms!important;}
}
</style>
"""

# Las páginas del portal (no el visor) apilan las secciones sin separación.
ESTILO_PAGINAS = """
<style>
.block-container > div > [data-testid="stVerticalBlock"],
.block-container > [data-testid="stVerticalBlock"]{gap:0!important;}
</style>
"""

# En el visor el mapa usa casi todo el ancho de la pantalla.
ESTILO_VISOR = """
<style>
:root{--g:.75rem;}
.st-key-portal_nav{margin-bottom:.6rem;}
</style>
"""

LOGO = (
    '<svg viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="20" fill="none" '
    'stroke="#ffffff" stroke-opacity=".35" stroke-width="1.5"/><path d="M8 30 C15 28 16 15 22 15 '
    'S30 26 36 12" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round"/>'
    '<circle cx="8" cy="30" r="4.6" fill="#77cc09"/><circle cx="22" cy="15" r="3.8" fill="#ffffff"/>'
    '<circle cx="36" cy="12" r="4.6" fill="#fabc20"/></svg>'
)

CORTE_HEROE = (
    '<svg class="hero-cut" viewBox="0 0 1440 150" preserveAspectRatio="none" aria-hidden="true">'
    '<polygon points="0,150 1440,40 1440,150" fill="#ffffff"/>'
    '<g fill="none" stroke="#fabc20" stroke-opacity=".7" stroke-width="1.3" vector-effect="non-scaling-stroke">'
    '<path d="M1150 150 C1210 112 1320 96 1440 92"/><path d="M1200 150 C1255 120 1340 108 1440 106"/>'
    '<path d="M1250 150 C1300 128 1365 120 1440 119"/></g>'
    '<polygon points="960,62.7 1440,26 1440,34 960,70.7" fill="#ffffff"/>'
    '<polygon points="880,78.8 1440,36 1440,46 880,88.8" fill="#77cc09"/>'
    '<polygon points="990,84.4 1440,50 1440,59 990,93.4" fill="#fabc20"/></svg>'
)

ICONOS = {
    "area": '<path d="M4 6.5 9 3l6 3 5-2.5v13L15 20l-6-3-5 3z"/><path d="M9 3v14M15 6v14"/>',
    "capas": '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
    "medir": '<path d="M3 17 17 3l4 4L7 21z"/><path d="m7 13 2 2M10 10l2 2M13 7l2 2"/>',
    "reglas": '<path d="M12 3v18M5 21h14"/><path d="m5 7 7-2 7 2"/><path d="M5 7 2 14a3 3 0 0 0 6 0L5 7ZM19 7l-3 7a3 3 0 0 0 6 0l-3-7Z"/>',
    "explicar": '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
}


def html(contenido):
    """Publica HTML sin que Markdown interprete la sangría como bloque de código."""

    limpio = " ".join(linea.strip() for linea in contenido.splitlines())
    st.markdown(limpio, unsafe_allow_html=True)


def icono(nombre):
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONOS[nombre]}</svg>'
    )


@lru_cache(maxsize=1)
def cifras_corredores():
    """Lee los GeoJSON publicados para mostrar cifras reales en la portada."""

    try:
        corredores = json.loads(
            (DATOS / "corredores_almanaque_azul.geojson").read_text(encoding="utf-8")
        )["features"]
        puntos = json.loads(
            (DATOS / "puntos_criticos_almanaque_azul.geojson").read_text(encoding="utf-8")
        )["features"]
    except (OSError, ValueError, KeyError):
        return {"corredores": "—", "puntos": "—", "mesoamericanos": "—"}
    return {
        "corredores": len(corredores),
        "puntos": len(puntos),
        "mesoamericanos": sum(
            1 for f in corredores if f.get("properties", {}).get("es_mesoamericano")
        ),
    }


# ---------------------------------------------------------------------------
# Navegación y estado
# ---------------------------------------------------------------------------

def elegir_modo(modo):
    st.session_state["modo_analisis"] = modo
    st.session_state["seccion_tablero"] = SECCION_MAPA
    st.session_state["mostrar_resultados"] = False


def abrir_vista(vista):
    st.session_state["seccion_tablero"] = vista
    if vista == SECCION_MAPA:
        st.session_state["mostrar_resultados"] = False


def mostrar_navegacion():
    """Barra azul del portal con marca, secciones y estado del resultado."""

    with st.container(key="portal_nav"):
        html(
            """
            <div class="portal-util" aria-hidden="true">
              <span>Google Earth Engine</span>
              <span>Almanaque Azul 2024.05</span>
              <span>WGS 84 · EPSG:4326</span>
            </div>
            """
        )
        marca, menu, accion = st.columns([3.1, 6, 1.6], vertical_alignment="center")
        with marca:
            html(
                f"""
                <div class="wm" role="img" aria-label="{SITIO['nombre']} · {SITIO['subtitulo']}">
                  {LOGO}<span><b>{SITIO['nombre']}</b><small>{SITIO['subtitulo']}</small></span>
                </div>
                """
            )
        with menu:
            seccion = st.segmented_control(
                "Navegación principal",
                SECCIONES_PRINCIPALES,
                default=SECCION_MAPA,
                key="seccion_tablero",
                label_visibility="collapsed",
            )
        with accion:
            html('<span class="pill">Resultado indicativo</span>')
    return seccion


def mostrar_heroe(clave, titulo, texto, miga=None, acciones=None):
    """Cabecera azul con corte diagonal y franjas verde y amarilla."""

    with st.container(key=f"heroe_{clave}"):
        miga_html = (
            f'<div class="bc"><u>Inicio</u><span>/</span>{miga}</div>' if miga else ""
        )
        html(f'{miga_html}<h1>{titulo}</h1><p class="lead">{texto}</p>')
        if acciones:
            with st.container(key="acciones_heroe", horizontal=True):
                for etiqueta, vista, primario in acciones:
                    st.button(
                        etiqueta,
                        type="primary" if primario else "secondary",
                        on_click=abrir_vista,
                        args=(vista,),
                    )
        html(CORTE_HEROE)


def mostrar_pie():
    with st.container(key="pie"):
        html(
            f"""
            <footer class="foot">
              <div class="wm">{LOGO}<span><b>{SITIO['nombre']}</b><small>{SITIO['subtitulo']}</small></span></div>
              <p>{SITIO['atribucion']}</p>
            </footer>
            """
        )


def boton_volver_al_mapa():
    with st.container(key="sec_accion"):
        st.button(
            "Abrir el mapa",
            type="primary",
            width="content",
            on_click=abrir_vista,
            args=(SECCION_MAPA,),
        )


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

def mostrar_inicio():
    mostrar_heroe(
        "inicio",
        "Preevaluación territorial y conectividad ecológica de la Cuenca del Canal",
        "Visor para reunir evidencia satelital de cambio forestal, corredores naturales "
        "publicados y estructura del bosque en una finca, una subcuenca, un polígono "
        "dibujado o la cuenca completa. Los datos se consultan en Google Earth Engine y se "
        "resumen en una orientación indicativa para decidir dónde revisar primero.",
        acciones=(
            ("Cómo funciona", SECCION_METODO, True),
            ("Acerca del visor", SECCION_ACERCA, False),
        ),
    )

    with st.container(key="sec_meta"):
        html(
            f"""
            <div class="meta">
              <div><span>Sistema de referencia</span><b>WGS 84 · EPSG:4326</b></div>
              <div><span>Resolución</span><b>10 m · 30 m</b></div>
              <div><span>Serie temporal</span><b>{PERIODOS_ANALISIS['esri_inicial']} – {PERIODOS_ANALISIS['referencia']}</b></div>
              <div><span>Unidad de análisis</span><b>Finca · subcuenca · polígono</b></div>
              <div><span>Procesamiento</span><b>Google Earth Engine</b></div>
            </div>
            """
        )

    cifras = cifras_corredores()
    with st.container(key="sec_cifras"):
        html(
            f"""
            <div class="sec-c">
              <h2>Evidencia territorial por área de interés</h2>
              <p>El visor combina cinco fuentes satelitales con los corredores naturales de
              Panamá y la capa institucional de bosque 2021. Cada lectura conserva su propia
              pregunta: los indicios de cambio orientan la urgencia, los corredores aportan
              valor estratégico y la fragmentación indica dónde mirar en campo.</p>
            </div>
            <div class="figs">
              <div class="fig"><span>Fuentes satelitales</span><b>5</b><p>JRC, Hansen, ESRI, GEDI y Sentinel-2 (NDVI).</p></div>
              <div class="fig"><span>Índice máximo</span><b>{PUNTAJE_MAXIMO:.1f}</b><p>Puntos del índice de indicios de cambio.</p></div>
              <div class="fig"><span>Corredores</span><b>{cifras['corredores']}</b><p>Polígonos publicados por Almanaque Azul.</p></div>
              <div class="fig"><span>Puntos críticos</span><b>{cifras['puntos']}</b><p>Sitios señalados para atención.</p></div>
              <div class="fig"><span>Tramos CBM</span><b>{cifras['mesoamericanos']}</b><p>Corredor Biológico Mesoamericano en Panamá.</p></div>
            </div>
            """
        )

    etiquetas = {
        MODO_TERRITORIAL: ("JRC · Hansen · ESRI", "NDVI · GEDI"),
        MODO_CORREDORES: ("Corredores", "Fragmentación"),
        MODO_INTEGRAL: ("Indicios", "Corredores", "Bosque 2021"),
    }
    with st.container(key="sec_gris_modulos"):
        html('<div class="sec-c"><h2>¿Qué desea preevaluar?</h2></div>')
        columnas = st.columns(3, gap="medium")
        for numero, (columna, (modo, contenido)) in enumerate(
            zip(columnas, MODOS_ANALISIS.items()), start=1
        ):
            with columna, st.container(key=f"modulo_{modo}"):
                tags = "".join(f'<span class="tag">{t}</span>' for t in etiquetas.get(modo, ()))
                html(
                    f"""
                    <span class="card-date">Módulo {numero}</span>
                    <h3 class="card-h3">{contenido['titulo']}</h3>
                    <p class="card-q">{contenido['pregunta']}</p>
                    <p class="card-p">{contenido['descripcion']}</p>
                    <p class="card-res"><b>Recibirá:</b> {contenido['resultado']}</p>
                    <div class="tags">{tags}</div>
                    """
                )
                st.button(
                    f"Elegir {contenido['titulo'].lower()}",
                    key=f"elegir-modo-{modo}",
                    type="tertiary",
                    width="stretch",
                    on_click=elegir_modo,
                    args=(modo,),
                )
        html(
            """
            <div class="note-p"><span class="tag demo">Indicativo</span>
            Earth Engine se conecta solo después de elegir una preevaluación. Los resultados
            orientan una revisión y requieren verificación de campo.</div>
            """
        )
    mostrar_pie()


def mostrar_metodo():
    mostrar_heroe(
        "pagina",
        "Cómo se construye la preevaluación",
        "Cada fuente responde una pregunta diferente. La aplicación conserva esas "
        "diferencias, aplica reglas documentadas y presenta una orientación que puede "
        "rastrearse hasta sus datos de origen. Los años del comparador cambian el mapa, "
        "pero no modifican las reglas del índice configurado.",
        miga="Metodología y ayuda",
    )

    pasos = (
        ("area", "Delimitar", "Área de interés", "El área elegida se recorta al límite institucional de la cuenca cuando corresponde."),
        ("capas", "Consultar", "Fuentes necesarias", "Se solicitan únicamente las fuentes necesarias para el enfoque seleccionado."),
        ("medir", "Medir", "Señales comparables", "Las señales se expresan en hectáreas, porcentajes, cambios o métricas de conectividad."),
        ("reglas", "Aplicar reglas", "Umbrales y pesos", "Los umbrales y pesos documentados convierten los indicios en una orientación comparable."),
        ("explicar", "Explicar", "Resumen trazable", "El resumen, el mapa y el registro metodológico muestran qué influyó y qué no."),
    )
    pasos_html = "".join(
        f'<li class="st"><div class="circ">{icono(ic)}</div>'
        f'<span class="eyebrow">{i} · {etapa}</span><h3>{titulo}</h3><p>{texto}</p></li>'
        for i, (ic, etapa, titulo, texto) in enumerate(pasos, start=1)
    )
    with st.container(key="sec_flujo"):
        html(
            f"""
            <div class="sec-c"><span class="eyebrow">Flujo de procesamiento</span>
            <h2>El proceso en cinco pasos</h2>
            <p>Una explicación sencilla primero; las reglas técnicas permanecen disponibles después.</p></div>
            <ol class="flowc" aria-label="Pasos del método">{pasos_html}</ol>
            """
        )

    fuentes = (
        ("JRC Tropical Moist Forest", "¿Hay indicios de degradación o deforestación en bosque tropical?", str(PERIODOS_ANALISIS["jrc_diagnostico"]), "Señal forestal principal", "ok"),
        ("Hansen Global Forest Change", "¿Se registró pérdida anual de cobertura arbórea después de 2020?", f"2021–{PERIODOS_ANALISIS['hansen_diagnostico']}", "Señal forestal principal", "ok"),
        ("ESRI Land Use/Land Cover", "¿Sectores clasificados como árboles pasaron a otra cobertura?", f"{PERIODOS_ANALISIS['esri_inicial']}–{PERIODOS_ANALISIS['esri_final']}", "Señal corroborativa", "ok"),
        ("Sentinel-2 · NDVI", "¿Disminuyó de forma importante el vigor de la vegetación?", f"{PERIODOS_ANALISIS['ndvi_inicial']}–{PERIODOS_ANALISIS['ndvi_final']}", "Señal corroborativa", "ok"),
        ("GEDI / OpenForis", "¿Qué contexto aporta la altura observada del dosel?", "Producto disponible", "Contexto estructural", "ctx"),
        ("Almanaque Azul", "¿El área coincide con corredores naturales publicados?", "Versión publicada 2024.05", "Valor estratégico", "ctx"),
        ("SINIA–MiAMBIENTE · Bosque y otros usos", "¿Cómo se distribuyen y relacionan los fragmentos de bosque?", "2021", "Estructura y conectividad", "ctx"),
    )
    filas = "".join(
        f"<tr><td>{f}</td><td>{p}</td><td>{r}</td><td><span class='dot {c}'></span>{papel}</td></tr>"
        for f, p, r, papel, c in fuentes
    )
    with st.container(key="sec_gris_fuentes"):
        html(
            f"""
            <h2 class="h-reg">Qué aporta cada fuente</h2>
            <div class="tbl"><table>
              <thead><tr><th>Fuente</th><th>Pregunta que ayuda a responder</th><th>Referencia</th><th>Papel</th></tr></thead>
              <tbody>{filas}</tbody>
            </table></div>
            <div class="note-p" style="justify-content:flex-start">
              <span><span class="dot ok"></span>Interviene en el índice de indicios</span>
              <span><span class="dot ctx"></span>Contexto, valor estratégico o estructura</span>
            </div>
            """
        )

    with st.container(key="sec_tecnico"):
        html('<h2 class="h-sub">Para usuarios técnicos</h2>')
        with st.expander("Pesos, umbrales y separación de resultados", expanded=False):
            st.markdown(
                f"""
                **Índice de indicios territoriales**

                - JRC: **{PESOS_INDICE['tmf']:.1f}** puntos.
                - Hansen: **{PESOS_INDICE['hansen']:.1f}** puntos.
                - ESRI: **{PESOS_INDICE['esri']:.1f}** puntos.
                - GEDI: **{PESOS_INDICE['gedi']:.1f}** puntos.
                - NDVI: **{PESOS_INDICE['ndvi']:.1f}** puntos.
                - Máximo configurado: **{PUNTAJE_MAXIMO:.1f}** puntos.

                La señal NDVI exige simultáneamente una disminución de
                **{abs(UMBRALES_INDICE['ndvi_delta_disminucion']):.2f}**, al menos
                **{UMBRALES_INDICE['ndvi_disminucion_ha']:.2f} ha** y
                **{UMBRALES_INDICE['ndvi_disminucion_pct']:.0f}% del área**, con una cobertura
                válida mínima de **{UMBRALES_INDICE['ndvi_cobertura_minima_pct']:.0f}%**.

                Los corredores publicados **no aumentan el índice satelital**. La opción integral
                los incorpora por separado para orientar la visita; un corredor sin indicios de
                cambio no produce por sí solo una prioridad alta. La estructura del bosque ayuda
                a decidir **dónde** revisar, pero no recibe un peso inventado.
                """
            )
        with st.expander("Alcance técnico y limitaciones", expanded=False):
            st.markdown(
                """
                - Cada producto tiene fecha, resolución, clasificación y cobertura propias.
                - Una coincidencia entre fuentes fortalece la necesidad de revisar, pero no demuestra causalidad.
                - NDVI puede responder a humedad, estacionalidad, cultivos, nubes o sombras y no identifica por sí solo bosque natural.
                - GEDI tiene cobertura espacial limitada y se interpreta como contexto, no como pérdida confirmada.
                - La red de fragmentos representa conectividad estructural potencial; no modela especies, conducta ni conectividad funcional.
                - Los resultados deben contrastarse con conocimiento local, imágenes recientes, documentos y campo.
                """
            )
        st.write("")
        boton_volver_al_mapa()
    mostrar_pie()


def mostrar_acerca():
    mostrar_heroe(
        "pagina",
        "Acerca del visor",
        "El visor reúne evidencia satelital, corredores publicados y estructura del bosque "
        "para ayudar a decidir dónde conviene profundizar, sin sustituir la verificación de "
        "campo. Preevaluación indicativa: no constituye certificación ni determinación legal.",
        miga="Acerca del visor",
    )

    with st.container(key="sec_gris_acerca"):
        html('<div class="sec-c"><h2>Qué problema ayuda a resolver</h2></div>')
        izquierda, derecha = st.columns(2, gap="large")
        with izquierda:
            html(
                """
                <h3 class="h-sub">Para personas usuarias</h3>
                <ul class="qlist">
                  <li><b>Seleccionar el área</b><span>Una finca, subcuenca, polígono o la cuenca completa.</span></li>
                  <li><b>Consultar capas</b><span>Sin necesitar experiencia previa en teledetección.</span></li>
                  <li><b>Obtener una lectura</b><span>Resumen breve y evidencia descargable.</span></li>
                  <li><b>Saber qué confirmar</b><span>Qué información debe validarse con campo o documentos.</span></li>
                </ul>
                """
            )
        with derecha:
            html(
                """
                <h3 class="h-sub">Para equipos técnicos</h3>
                <ul class="qlist">
                  <li><b>Revisar parámetros</b><span>Fuentes, períodos, pesos y umbrales.</span></li>
                  <li><b>Comparar años</b><span>Consultar capas por fuente con el comparador temporal.</span></li>
                  <li><b>Descargar resultados</b><span>Registro metodológico JSON, GeoJSON y ficha PDF.</span></li>
                  <li><b>Reproducir</b><span>Documentar la preevaluación para otras personas.</span></li>
                </ul>
                """
            )

    with st.container(key="sec_alcance"):
        izquierda, derecha = st.columns(2, gap="large")
        with izquierda:
            html(
                """
                <h2 class="h-reg">La aplicación sí permite</h2>
                <div class="prose"><p>Identificar dónde coinciden indicios satelitales de cambio,
                ubicar el área frente a corredores publicados, describir la fragmentación del bosque
                y documentar fuentes, períodos, reglas y parámetros para respaldar la conversación.</p></div>
                """
            )
        with derecha:
            html(
                """
                <h2 class="h-reg">La aplicación no pretende</h2>
                <div class="prose"><p>Confirmar en campo una pérdida, degradación o causa específica;
                demostrar conectividad funcional o movimiento de una especie; emitir una
                certificación, sanción o conclusión legal, ni determinar por sí sola cumplimiento
                de EUDR u otra norma.</p></div>
                """
            )
        html(
            """
            <div class="cita"><b>Alcance:</b> los resultados orientan una revisión.
            No confirman causas de pérdida, movimiento de fauna, cumplimiento normativo ni
            condiciones verificadas en campo.</div>
            """
        )
        st.write("")
        boton_volver_al_mapa()
    mostrar_pie()


# ---------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------

st.markdown(ESTILO_PORTAL, unsafe_allow_html=True)

if st.session_state.get("seccion_tablero") == "Análisis":
    # Migra sesiones abiertas con la navegación anterior.
    st.session_state["seccion_tablero"] = SECCION_MAPA

modo_analisis = st.session_state.get("modo_analisis")
if modo_analisis not in MODOS_ANALISIS:
    st.session_state.pop("modo_analisis", None)
    modo_analisis = None

seccion_tablero = mostrar_navegacion()

seccion_anterior = st.session_state.get("_seccion_publica_anterior")
if (
    seccion_tablero == SECCION_MAPA
    and seccion_anterior in (SECCION_METODO, SECCION_ACERCA)
):
    st.session_state["mostrar_resultados"] = False
st.session_state["_seccion_publica_anterior"] = seccion_tablero

if seccion_tablero == SECCION_METODO:
    st.markdown(ESTILO_PAGINAS, unsafe_allow_html=True)
    mostrar_metodo()
    st.stop()
if seccion_tablero == SECCION_ACERCA:
    st.markdown(ESTILO_PAGINAS, unsafe_allow_html=True)
    mostrar_acerca()
    st.stop()

if modo_analisis is None:
    st.markdown(ESTILO_PAGINAS, unsafe_allow_html=True)
    mostrar_inicio()
    st.stop()


st.markdown(ESTILO_VISOR, unsafe_allow_html=True)

APLICACION_ACTIVA = Path(__file__).with_name("app_experiencia.py")
if not APLICACION_ACTIVA.is_file():
    raise FileNotFoundError(
        "No se encontró app_experiencia.py, la implementación activa del visor."
    )

runpy.run_path(str(APLICACION_ACTIVA), run_name="__main__")
