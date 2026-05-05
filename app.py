"""
╔══════════════════════════════════════════════════════════════╗
║         HAPPY VISION · SISTEMA DE GESTIÓN INTEGRAL          ║
║         Contabilidad · Facturación · Inventario             ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import base64

# ── Utilidades y vistas ────────────────────────────────────────
from utils import generate_sample_data, guardar_datos

from vistas.clinica   import render_clinica
from vistas.pacientes import render_pacientes
from vistas.usuarios  import render_usuarios


# ══════════════════════════════════════════════════════════════
# MOSTRAR ERRORES GLOBALES DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════
def mostrar_error_db():
    if "db_error" in st.session_state:
        st.error("🚨 **ALERTA CRÍTICA DE BASE DE DATOS** 🚨\n\n" + st.session_state.db_error)
        del st.session_state["db_error"]


# ══════════════════════════════════════════════════════════════
# CARGA DE USUARIOS DESDE ARCHIVO
# ══════════════════════════════════════════════════════════════
def _cargar_usuarios() -> dict:
    """Carga usuarios desde Supabase."""
    from database import supabase
    if supabase:
        try:
            res = supabase.table("usuarios").select("*").execute()
            if res.data:
                return {row["username"]: row for row in res.data}
        except Exception as e:
            print(f"Error cargando usuarios desde Supabase en app: {e}")
    # Fallback si no hay conexión
    return {"admin": {"password": "1201", "role": "Administrador", "nombre": "Opt. Anthonny Guato",
                      "cargo": "Optometrista", "registro": "2250-2024-3004584", "telefono": "+593 96 324 1158"}}


# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Happy Vision · Sistema de Gestión",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Happy Vision · Sistema de Gestión Integral v2.0",
    }
)

mostrar_error_db()

# ══════════════════════════════════════════════════════════════
# ESTILOS CSS PERSONALIZADOS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%) !important;
    border-right: 1px solid #bae6fd !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0px !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #334155 !important;
}
[data-testid="stSidebar"] button {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span {
    color: #1e293b !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] button:hover {
    background-color: #f1f5f9 !important;
    border-color: #3b82f6 !important;
}
[data-testid="stSidebarNav"] { display: none; }

/* ── Logo Block ── */
.logo-container {
    background: linear-gradient(135deg, #ffffff, #f0f9ff);
    border: 1px solid #bae6fd;
    border-radius: 14px;
    padding: 18px 14px;
    text-align: center;
    margin-bottom: 18px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: transform 0.2s ease;
}
.logo-container:hover {
    border-color: #3b82f6;
    box-shadow: 0 0 20px rgba(59,130,246,0.3);
}
.logo-hint {
    color: #2563eb !important;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0 0 6px 0;
    font-weight: 700;
}

/* ── Page Header ── */
.page-header {
    background: #ffffff;
    border-radius: 20px;
    padding: 35px 45px;
    margin-bottom: 35px;
    position: relative;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    border-left: 12px solid #2563eb;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05);
}
.page-header::after {
    content: "";
    position: absolute;
    top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.05), rgba(14, 165, 233, 0.1));
    border-radius: 50%;
}
.page-header h1 {
    margin: 0;
    font-size: 2.2rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
}
.page-header p {
    margin: 6px 0 0 0;
    color: #64748b;
    font-size: 1.05rem;
    font-weight: 500;
}

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
}
.kpi-card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 20px 18px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    cursor: default;
}
.kpi-card p {
    color: #e2e8f0 !important;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    border-color: #3b82f6;
}
.kpi-icon { font-size: 1.6rem; margin-bottom: 8px; }
.kpi-value {
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1;
}
.kpi-value-green {
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, #22c55e, #4ade80);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1;
}
.kpi-value-red {
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, #f87171, #fb923c);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1;
}
.kpi-label {
    font-size: 0.75rem; color: #94a3b8 !important; margin-top: 6px;
    font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;
}

/* ── Stock Alerts ── */
.alert-critical {
    background: linear-gradient(135deg, #450a0a, #7f1d1d);
    border: 1px solid #ef4444; border-left: 4px solid #ef4444;
    border-radius: 10px; padding: 12px 16px; margin: 6px 0;
}
.alert-warning {
    background: linear-gradient(135deg, #431407, #7c2d12);
    border: 1px solid #f97316; border-left: 4px solid #f97316;
    border-radius: 10px; padding: 12px 16px; margin: 6px 0;
}
.alert-ok {
    background: linear-gradient(135deg, #052e16, #14532d);
    border: 1px solid #22c55e; border-left: 4px solid #22c55e;
    border-radius: 10px; padding: 12px 16px; margin: 6px 0;
}
.alert-text { color: #f1f5f9 !important; font-size: 0.88rem; }
.alert-sub  { color: #94a3b8 !important; font-size: 0.78rem; margin-top: 4px; }

/* ── Section Titles ── */
.section-title {
    font-size: 1.25rem; font-weight: 800; color: #1e293b; /* Ajustado para modo claro */
    margin: 24px 0 14px 0; padding-bottom: 8px;
    border-bottom: 2px solid #cbd5e1;
}

/* ── Divider ── */
.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #94a3b8, transparent);
    margin: 20px 0;
}

/* ── Badge Status ── */
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-green  { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.badge-yellow { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a; }
.badge-red    { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.badge-blue   { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }

</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# AUTO-COPIAR FIRMA
# ══════════════════════════════════════════════════════════════
_firma_src = r"C:\Users\Antho\.gemini\antigravity\brain\c017a6da-99c2-48d2-a7ee-301aa884cb2f\media__1776186585568.png"
_firma_dst = "firma.png"
if not os.path.exists(_firma_dst) and os.path.exists(_firma_src):
    try:
        from PIL import Image as _PILimg
        _img_f = _PILimg.open(_firma_src).convert("RGBA")
        _bg_f  = _PILimg.new("RGBA", _img_f.size, (255,255,255,255))
        _bg_f.paste(_img_f, (0,0), _img_f)
        _bg_f.convert("RGB").save(_firma_dst, format="PNG")
    except Exception:
        import shutil as _shutil
        _shutil.copy2(_firma_src, _firma_dst)


# ══════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════
if "initialized_v4" not in st.session_state:
    df_t, df_i, df_g, df_p, df_h = generate_sample_data()

    # 1. Cargar desde CSV local por defecto (fallback)
    if os.path.exists("pacientes.csv"):
        try: df_p = pd.read_csv("pacientes.csv", dtype=str)
        except Exception: pass
    if os.path.exists("historias.csv"):
        try: df_h = pd.read_csv("historias.csv", dtype=str)
        except Exception: pass

    # 2. Cargar desde Supabase (sobrescribe lo local si está configurado y hay datos)
    try:
        from database import cargar_pacientes, cargar_historias, supabase
        if supabase:
            _df_pac = cargar_pacientes()
            if len(_df_pac) > 0:
                # Solo sobrescribir si Supabase tiene más o igual datos y el local no tiene columnas nuevas
                if len(_df_pac) > len(df_p) or ("nombres" in _df_pac.columns and len(_df_pac) == len(df_p)):
                    df_p = _df_pac

            _df_his = cargar_historias()
            if len(_df_his) > 0:
                # Verificar si Supabase tiene la columna nueva llena. Si el CSV local la tiene y Supabase no, priorizar CSV.
                supa_has_data = "meses_proximo_control" in _df_his.columns and not _df_his["meses_proximo_control"].replace("", pd.NA).isna().all()
                local_has_data = "meses_proximo_control" in df_h.columns and not df_h["meses_proximo_control"].replace("", pd.NA).isna().all()
                
                if len(_df_his) > len(df_h):
                    df_h = _df_his
                elif len(_df_his) == len(df_h):
                    if local_has_data and not supa_has_data:
                        pass # Mantener CSV local porque tiene la fecha de control que Supabase perdió
                    else:
                        df_h = _df_his

        # Sincronizar estructuras (Migración)
        from database import migrar_estructuras
        st.session_state.df_pacientes = df_p
        st.session_state.df_historias  = df_h
        migrar_estructuras()
        
        # Guardar cambios de migración
        guardar_datos()

    except Exception as e:
        print(f"Error inicializando Supabase: {e}")

    st.session_state.df_trabajos   = df_t
    st.session_state.df_inventario = df_i
    st.session_state.df_gastos     = df_g
    st.session_state.df_pacientes  = df_p
    st.session_state.df_historias  = df_h
    st.session_state.page          = "Dashboard"


    # Perfil del optometrista
    if os.path.exists("optometrista.json"):
        try:
            with open("optometrista.json", "r", encoding="utf-8") as f:
                d = json.load(f)
                st.session_state.opto_nombre    = d.get("opto_nombre",    "Optometrista Happy Vision")
                st.session_state.opto_registro  = d.get("opto_registro",  "N/A")
                st.session_state.opto_cargo     = d.get("opto_cargo",     "Optometrista")
                st.session_state.opto_direccion = d.get("opto_direccion", "Happy Vision")
                st.session_state.opto_telefono  = d.get("opto_telefono",  "+593 96 324 1158")
        except Exception:
            pass
    if "opto_nombre" not in st.session_state:
        st.session_state.opto_nombre    = "Optometrista Happy Vision"
        st.session_state.opto_registro  = "N/A"
        st.session_state.opto_cargo     = "Optometrista"
        st.session_state.opto_direccion = "Happy Vision"
        st.session_state.opto_telefono  = "+593 96 324 1158"

    st.session_state.initialized_v4 = True


# ══════════════════════════════════════════════════════════════
# SISTEMA DE LOGIN Y ROLES
# ══════════════════════════════════════════════════════════════
USUARIOS = _cargar_usuarios()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.user_name = ""

if not st.session_state.logged_in:
    # ── CARGA DE IMAGEN DE FONDO (Base64) ────────────────────
    bg_img_path = "login_bg.png"
    bg_style = ""
    if os.path.exists(bg_img_path):
        try:
            with open(bg_img_path, "rb") as f:
                bin_str = base64.b64encode(f.read()).decode()
            bg_style = f"background-image: url('data:image/png;base64,{bin_str}');"
        except Exception:
            bg_style = "background: linear-gradient(135deg, #ff0000 0%, #770000 100%);" # TEST ROJO
    else:
        bg_style = "background: linear-gradient(135deg, #ff0000 0%, #770000 100%);" # TEST ROJO

    # ── ESTILOS ESPECÍFICOS DEL LOGIN ────────────────────────
    st.markdown(f"""
    <style>
    /* Fondo dinámico para el area de login */
    .stApp {{
        {bg_style}
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    
    /* Ocultar elementos de navegación estándar */
    [data-testid="stSidebar"] {{ display: none !important; }}
    header {{ visibility: hidden !important; }}
    
    .login-wrapper {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 5vh;
    }}

    .glass-card {{
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 20px !important;
        padding: 15px 30px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important;
        width: 100%;
        max-width: 400px;
        height: 50mm !important;
        margin: 0 auto;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center; /* Centrado horizontal */
        overflow: hidden;
    }}

    /* Logo centrado y sin recortes extraños */
    .glass-card img {{
        display: block !important;
        margin: 0 auto 10px auto !important; /* Centrado y con espacio inferior */
        max-height: 120mm !important; /* Ajuste para que quepa con el formulario */
        width: auto !important;
        max-width: 90% !important;
        object-fit: contain !important; /* Ver logo completo */
        filter: brightness(0) invert(1) !important;
        opacity: 0.9;
    }}

    /* Espaciado súper compacto para cumplir los 50mm */
    div[data-testid="stTextInput"] {{ margin-top: -5px !important; }}
    div[kind="primary"] {{ margin-top: 5px !important; }}

    .login-header {{
        text-align: center;
        margin-bottom: 35px;
    }}

    .login-header h2 {{
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        margin-bottom: 8px !important;
        letter-spacing: -0.5px !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5) !important; /* Sombra para legibilidad */
    }}

    /* Etiquetas de los campos (Usuario/Contraseña) */
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label p,
    div[data-testid="stTextInput"] label div p {{
        color: #ffffff !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.8) !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        margin-bottom: 8px !important;
    }}

    /* Cuadro transparente para agrupar Usuario/Contraseña */
    div[data-testid="stForm"] {{
        background: rgba(0, 0, 0, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 18px !important;
        padding: 20px !important;
        margin-top: 5px !important;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.2) !important;
    }}

    /* Personalización de inputs */
    div[data-testid="stTextInput"] > div > div > input {{
        background: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 12px !important;
        color: #1e293b !important; /* Texto oscuro para legibilidad sobre blanco */
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
    }}

    div[data-testid="stTextInput"] > div > div > input:focus {{
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }}

    /* Contenedor del botón para asegurar centrado perfecto */
    div.stFormSubmitButton {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-top: 15px !important;
    }}

    /* Botón Premium centrado horizontalmente */
    button[kind="primary"], .stButton > button {{
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 10px 30px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        margin: 0 auto !important;
        display: block !important;
    }}

    button[kind="primary"]:hover {{
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 30px -5px rgba(37, 99, 235, 0.4) !important;
    }}
    
    .footer-note {{
        margin-top: 40px;
        color: #475569;
        font-size: 0.8rem;
        text-align: center;
        letter-spacing: 0.5px;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── LAYOUT DE LOGIN ──────────────────────────────────────
    _, centered_col, _ = st.columns([1, 1.2, 1])

    with centered_col:
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        
        # Carga de Logo en Base64 para inyección HTML
        logo_b64 = ""
        logo_path = "logo.png" if os.path.exists("logo.png") else ("logo.jpg" if os.path.exists("logo.jpg") else None)
        if logo_path:
            try:
                with open(logo_path, "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode()
            except Exception: pass

        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="220">' if logo_b64 else ""

        st.markdown(f"""
            <div class="glass-card">
                {logo_html}
        """, unsafe_allow_html=True)
        
        # Formulario sin borde nativo
        with st.form("login_form", border=False):
            usuario = st.text_input("Usuario", placeholder="ej: admin")
            password_inp = st.text_input("Contraseña", type="password", placeholder="••••••••")
            
            # Botón centrado horizontalmente al final
            submit_login = st.form_submit_button("Ingresar al Sistema", type="primary")
            
            if submit_login:
                _usuarios_act = _cargar_usuarios()
                if usuario in _usuarios_act and _usuarios_act[usuario]["password"] == password_inp:
                    ud = _usuarios_act[usuario]
                    raw_role = str(ud.get("role", ""))
                    
                    if raw_role.startswith("INACTIVO:"):
                        st.error("🚫 Tu cuenta ha sido bloqueada. Contacta al administrador.")
                    else:
                        st.session_state.logged_in   = True
                        st.session_state.user_role   = raw_role.replace("INACTIVO:", "")
                        st.session_state.user_name   = ud.get("nombre", usuario)
                        st.session_state.user_login  = usuario
                        st.session_state.user_cargo  = ud.get("cargo", "Optometrista")
                        st.session_state.user_registro = ud.get("registro", "")
                        st.session_state.user_telefono = ud.get("telefono", "")
                        
                        # Manejo de sucursales (Administradores siempre tienen todas)
                        assigned_branches = ud.get("sucursales_asignadas")
                        
                        if "Administrador" in raw_role:
                            assigned_branches = ["Matriz", "Sucursal 1", "Sucursal 2"]
                        
                        if not assigned_branches:
                            assigned_branches = ["Matriz"]
                        elif isinstance(assigned_branches, str):
                            assigned_branches = [assigned_branches]
                            
                        st.session_state.sucursales_asignadas = assigned_branches
                        
                        if len(assigned_branches) == 1:
                            st.session_state.sucursal_activa = assigned_branches[0]
                        else:
                            st.session_state.sucursal_activa = None
                            
                        st.rerun()
                else:
                    st.error("Credenciales invalidas. Verifica tu usuario y contrasena.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p class="footer-note">© 2024 Happy Vision Integral System</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ══════════════════════════════════════════════════════════════
# PANTALLA DE SELECCIÓN DE SUCURSAL
# ══════════════════════════════════════════════════════════════
if st.session_state.get("logged_in"):
    # Forzar que el Administrador siempre vea todas las sedes
    if "Administrador" in st.session_state.get("user_role", ""):
        st.session_state.sucursales_asignadas = ["Matriz", "Sucursal 1", "Sucursal 2"]

if st.session_state.get("logged_in") and not st.session_state.get("sucursal_activa"):
    st.markdown("<h2 style='text-align: center; margin-top: 10vh; color: #1e293b; font-weight: 800;'>🏢 Selecciona tu Entorno de Trabajo</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 5vh;'>Haz clic en el cuadro de la óptica a la que deseas acceder</p>", unsafe_allow_html=True)
    
    sucursales = st.session_state.get("sucursales_asignadas", ["Matriz"])
    
    # Asegurarnos de que las columnas queden centradas si son pocas
    if len(sucursales) == 1:
        cols = st.columns([1, 2, 1])
        work_cols = [cols[1]]
    elif len(sucursales) == 2:
        cols = st.columns([1, 2, 2, 1])
        work_cols = [cols[1], cols[2]]
    elif len(sucursales) == 3:
        cols = st.columns([1, 2, 2, 2, 1])
        work_cols = [cols[1], cols[2], cols[3]]
    else:
        work_cols = st.columns(len(sucursales))
        
    for i, sucursal in enumerate(sucursales):
        with work_cols[i]:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 16px; padding: 30px 10px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 15px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">
                    {'🏛️' if sucursal == 'Matriz' else '🏬' if '1' in sucursal else '🏪'}
                </div>
                <h3 style="color: #0f172a; margin: 0; font-size: 1.4rem;">{sucursal}</h3>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 5px;">Base de datos aislada</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Entrar a {sucursal}", key=f"btn_suc_{sucursal}", use_container_width=True, type="primary"):
                st.session_state.sucursal_activa = sucursal
                st.rerun()
                
    st.stop()


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    if os.path.exists("logo.png") or os.path.exists("logo.jpg"):
        logo_path = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
        st.markdown("<style>[data-testid='stSidebar'] img { filter: brightness(0); padding-bottom: 0px !important; margin-top: -55px !important; }</style>", unsafe_allow_html=True)
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("""
        <div class="logo-container">
            <p class="logo-hint">📌 Esperando el logo...</p>
            <p style="color:#475569; font-size:12px; margin-top:8px;">
               Guárdalo como <strong>logo.png</strong> en la carpeta del proyecto.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── NAVEGACIÓN DINÁMICA POR ROLES ────────────────────────
    st.markdown("<p style='color:#475569; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin:0 0 10px 0;'>Navegacion</p>", unsafe_allow_html=True)

    _role = st.session_state.user_role
    # Navegacion simplificada: solo Pacientes, Clinica y (para admin) Usuarios
    pages = {
        "Pacientes": ("👥", "Pacientes"),
        "Clinica":   ("🩺", "Historias Clinicas"),
    }
    if _role == "Administrador":
        pages["Usuarios"] = ("👤", "Gestion de Usuarios")

    if st.session_state.page not in pages:
        st.session_state.page = "Pacientes"

    for key, (icon, label) in pages.items():
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── INFO DEL USUARIO ──────────────────────────────────────
    n_pacientes = len(st.session_state.df_pacientes)
    n_historias = len(st.session_state.df_historias)
    st.markdown(
        f"<p style='color:#475569; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin:0 0 6px 0;'>Resumen</p>",
        unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)
    c1.metric("Pacientes", n_pacientes)
    c2.metric("Historias", n_historias)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:#1e293b; font-size:12px; text-align:center;'>👋 Hola, <b>{st.session_state.user_name}</b><br>"
        f"<span style='color:#64748b; font-size:11px;'>{st.session_state.user_role}</span><br>"
        f"<span style='color:#0ea5e9; font-size:11px; font-weight: bold;'>🏢 {st.session_state.get('sucursal_activa', '')}</span></p>",
        unsafe_allow_html=True
    )
    
    if len(st.session_state.get("sucursales_asignadas", [])) > 1 or st.session_state.get("user_role") == "Administrador":
        if st.button("🏠 Cambiar Sucursal", use_container_width=True):
            st.session_state.sucursal_activa = None
            st.rerun()
            
    if st.button("Cerrar Sesion", use_container_width=True):
        for key in ["logged_in","user_role","user_name","user_login","user_cargo","user_registro","user_telefono"]:
            st.session_state.pop(key, None)
        st.rerun()


# ══════════════════════════════════════════════════════════════
# ROUTER DE PÁGINAS
# ══════════════════════════════════════════════════════════════
page = st.session_state.page

if page == "Pacientes":
    render_pacientes()
elif page == "Clinica":
    render_clinica()
elif page == "Usuarios":
    render_usuarios()
else:
    render_pacientes()
