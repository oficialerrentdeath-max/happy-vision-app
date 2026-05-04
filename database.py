"""
╔══════════════════════════════════════════════════════════════╗
║  HAPPY VISION · database.py                                  ║
║  Capa de acceso a datos Supabase                             ║
║  Todas las operaciones de lectura/escritura en la DB en nube ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar .env si existe (entorno local)
load_dotenv()

# Intentar cargar desde variables de entorno (Streamlit Secrets o .env)
# Nota: Streamlit Cloud usa st.secrets.
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
except ImportError:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar cliente Supabase solo si hay credenciales (para evitar errores en import)
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ══════════════════════════════════════════════════════════════
# PACIENTES
# ══════════════════════════════════════════════════════════════
def cargar_pacientes() -> pd.DataFrame:
    """Carga todos los pacientes desde Supabase."""
    try:
        if not supabase: return _empty_pacientes_df()
        response = supabase.table("pacientes").select("*").execute()
        data = response.data
        if data:
            # Reemplazar None por string vacío para mantener compatibilidad con la app
            df = pd.DataFrame(data).fillna("")
            return df
        return _empty_pacientes_df()
    except Exception as e:
        print(f"Error cargar_pacientes: {e}")
        return _empty_pacientes_df()

def _empty_pacientes_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "id", "identificacion", "nombre", "nombres", "apellidos",
        "genero", "direccion", "edad", "fecha_nacimiento",
        "telefono", "correo", "ocupacion"
    ])

def guardar_paciente(row: dict):
    """Inserta o actualiza un paciente en Supabase."""
    try:
        if not supabase: return
        # Asegurar que todos los valores sean string
        row_str = {k: str(v) if v is not None else "" for k, v in row.items()}
        supabase.table("pacientes").upsert(row_str).execute()
    except Exception as e:
        print(f"Error guardar_paciente: {e}")

def guardar_todos_pacientes(df: pd.DataFrame):
    """Sincroniza el DataFrame completo de pacientes a Supabase."""
    try:
        if not supabase: return
        # Convertir todo a string
        df_str = df.astype(str)
        # Reemplazar "nan" por ""
        df_str = df_str.replace("nan", "")
        records = df_str.to_dict(orient="records")
        if records:
            supabase.table("pacientes").upsert(records).execute()
    except Exception as e:
        print(f"Error guardar_todos_pacientes: {e}")
        try:
            import streamlit as st
            st.session_state["db_error"] = f"Error guardando pacientes en la base de datos: {e}"
        except: pass
def eliminar_paciente(p_id):
    """Elimina permanentemente un paciente de Supabase."""
    try:
        if not supabase: return
        supabase.table("pacientes").delete().eq("id", str(p_id)).execute()
    except Exception as e:
        print(f"Error eliminar_paciente: {e}")


# ══════════════════════════════════════════════════════════════
# HISTORIAS CLÍNICAS
# ══════════════════════════════════════════════════════════════
HISTORIAS_COLS = [
    "id", "paciente_id", "paciente_nombre", "fecha",
    "ant_personales", "ant_familiares", "motivo",
    "diabetes", "hipertension", "patologia_otra", "observaciones",
    "lenso_od", "lenso_av_lej_od", "lenso_av_cer_od",
    "lenso_oi", "lenso_av_lej_oi", "lenso_av_cer_oi",
    "rx_od", "rx_av_lej_od", "rx_av_cer_od",
    "rx_oi", "rx_av_lej_oi", "rx_av_cer_oi",
    "estado_muscular", "seg_externo", "test_colores", "estado_refractivo",
    "diagnostico", "disposicion", "recomendaciones",
    "meses_proximo_control", "necesita_lentes", "test_color",
]

def cargar_historias() -> pd.DataFrame:
    """Carga todas las historias clínicas desde Supabase."""
    try:
        if not supabase: return _empty_historias_df()
        response = supabase.table("historias_clinicas").select("*").execute()
        data = response.data
        if data:
            df = pd.DataFrame(data).fillna("")
            # Asegurar que las columnas existan aunque falten en DB
            for col in HISTORIAS_COLS:
                if col not in df.columns:
                    df[col] = ""
            return df[HISTORIAS_COLS]
        return _empty_historias_df()
    except Exception as e:
        print(f"Error cargar_historias: {e}")
        return _empty_historias_df()

def _empty_historias_df() -> pd.DataFrame:
    return pd.DataFrame(columns=HISTORIAS_COLS)

def guardar_historia(row: dict):
    """Inserta o actualiza una historia clínica en Supabase."""
    try:
        if not supabase: return
        # Asegurar string y limpiar nulos
        row_str = {k: str(v) if v is not None else "" for k, v in row.items()}
        supabase.table("historias_clinicas").upsert(row_str).execute()
    except Exception as e:
        print(f"Error guardar_historia: {e}")

def guardar_todas_historias(df: pd.DataFrame):
    """Sincroniza el DataFrame completo de historias a Supabase."""
    try:
        if not supabase: return
        df_str = df.astype(str).replace("nan", "")
        records = df_str.to_dict(orient="records")
        if records:
            res = supabase.table("historias_clinicas").upsert(records).execute()
    except Exception as e:
        import traceback
        err_detail = traceback.format_exc()
        try:
            import streamlit as st
            st.session_state["db_error"] = f"🔥 ERROR CRÍTICO SUPABASE: {str(e)}\n\nDetalle técnico:\n{err_detail}"
        except: pass
def eliminar_historia(h_id):
    """Elimina permanentemente una historia de Supabase."""
    try:
        if not supabase: return
        supabase.table("historias_clinicas").delete().eq("id", str(h_id)).execute()
    except Exception as e:
        print(f"Error eliminar_historia: {e}")
