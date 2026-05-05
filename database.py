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
# AUDITORÍA — Registro inmutable de cambios críticos
# ══════════════════════════════════════════════════════════════
def registrar_auditoria(accion: str, entidad: str = "", detalle: str = "",
                        usuario: str = "", nombre_usuario: str = "", sucursal: str = ""):
    """Registra un evento crítico en la tabla auditoria de Supabase.
    Nunca lanza excepciones para no interrumpir el flujo principal.
    """
    if not supabase:
        return
    try:
        from datetime import datetime, timezone
        supabase.table("auditoria").insert({
            "fecha_hora":    datetime.now(timezone.utc).isoformat(),
            "usuario":       usuario or "desconocido",
            "nombre_usuario": nombre_usuario or usuario,
            "accion":        accion,
            "entidad":       entidad,
            "detalle":       detalle,
            "sucursal":      sucursal,
        }).execute()
        # Confirmación visual opcional
        try:
            import streamlit as st
            st.toast(f"📝 Auditoría: {accion}")
        except: pass
    except Exception as e:
        print(f"[Auditoría] Error registrando evento: {e}")


def cargar_auditoria(limit: int = 500) -> pd.DataFrame:
    """Carga los registros de auditoría más recientes para el Admin."""
    try:
        if not supabase:
            return pd.DataFrame()
        res = supabase.table("auditoria").select("*").order("fecha_hora", desc=True).limit(limit).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        print(f"Error cargar_auditoria: {e}")
        return pd.DataFrame()


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

PACIENTES_COLS = [
    "id", "identificacion", "nombre", "nombres", "apellidos", "genero", 
    "direccion", "edad", "fecha_nacimiento", "telefono", "correo", "ocupacion", "sucursal"
]

HISTORIAS_COLS = [
    "id", "paciente_id", "paciente_nombre", "fecha",
    "ant_personales", "ant_familiares", "motivo", "diabetes", "hipertension", 
    "patologia_otra", "observaciones", "lenso_od", "lenso_av_lej_od", "lenso_av_cer_od",
    "lenso_oi", "lenso_av_lej_oi", "lenso_av_cer_oi",
    "rx_od", "rx_av_lej_od", "rx_av_cer_od",
    "rx_oi", "rx_av_lej_oi", "rx_av_cer_oi",
    "estado_muscular", "seg_externo", "test_colores", "estado_refractivo",
    "diagnostico", "disposicion", "recomendaciones",
    "meses_proximo_control", "necesita_lentes", "test_color", "sucursal"
]

def migrar_estructuras():
    """Asegura que los DataFrames locales y remotos tengan todas las columnas necesarias."""
    try:
        import streamlit as st
        # 1. Migrar Pacientes
        if "df_pacientes" in st.session_state:
            df_p = st.session_state.df_pacientes
            for col in PACIENTES_COLS:
                if col not in df_p.columns:
                    # Asignar 'Matriz' a pacientes antiguos si no tienen sucursal
                    df_p[col] = "Matriz" if col == "sucursal" else ""
            
            # Limpiar sucursales vacías que pudieran haber quedado
            df_p.loc[df_p['sucursal'] == '', 'sucursal'] = 'Matriz'
            df_p.loc[df_p['sucursal'].isna(), 'sucursal'] = 'Matriz'
            st.session_state.df_pacientes = df_p[PACIENTES_COLS]
        
        # 2. Migrar Historias
        if "df_historias" in st.session_state:
            df_h = st.session_state.df_historias
            for col in HISTORIAS_COLS:
                if col not in df_h.columns:
                    # Asignar 'Matriz' a historias antiguas
                    df_h[col] = "Matriz" if col == "sucursal" else ""
            
            # Limpiar sucursales vacías que pudieran haber quedado
            df_h.loc[df_h['sucursal'] == '', 'sucursal'] = 'Matriz'
            df_h.loc[df_h['sucursal'].isna(), 'sucursal'] = 'Matriz'
            st.session_state.df_historias = df_h[HISTORIAS_COLS]
            
        print("Migración de estructuras completada exitosamente.")
    except Exception as e:
        print(f"Error en migración: {e}")

# ══════════════════════════════════════════════════════════════
# HISTORIAS CLÍNICAS
# ══════════════════════════════════════════════════════════════

def cargar_historias() -> pd.DataFrame:
    """Carga todas las historias clínicas desde Supabase."""
    try:
        if not supabase: return pd.DataFrame(columns=HISTORIAS_COLS)
        response = supabase.table("historias_clinicas").select("*").execute()
        df = pd.DataFrame(response.data)
        # Asegurar columnas tras la carga
        for col in HISTORIAS_COLS:
            if col not in df.columns:
                df[col] = ""
        return df[HISTORIAS_COLS] if not df.empty else pd.DataFrame(columns=HISTORIAS_COLS)
    except Exception as e:
        print(f"Error cargar_historias: {e}")
        return pd.DataFrame(columns=HISTORIAS_COLS)

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
    try:
        if not supabase: return
        # Asegurar limpieza total de NaNs y conversión a strings
        df_limpio = df.copy().fillna("")
        records = []
        for _, row in df_limpio.iterrows():
            rec = {str(k): (str(v) if not pd.isna(v) and str(v).lower() != "nan" else "") for k, v in row.to_dict().items()}
            records.append(rec)
            
        if records:
            supabase.table("historias_clinicas").upsert(records).execute()
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

# ══════════════════════════════════════════════════════════════
# SUCURSALES
# ══════════════════════════════════════════════════════════════
def cargar_sucursales() -> pd.DataFrame:
    """Carga todas las sucursales desde Supabase."""
    try:
        if not supabase: return pd.DataFrame(columns=["nombre", "direccion", "telefono", "ciudad"])
        response = supabase.table("sucursales").select("*").order("nombre").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=["nombre", "direccion", "telefono", "ciudad"])
    except Exception as e:
        print(f"Error cargar_sucursales: {e}")
        return pd.DataFrame(columns=["nombre", "direccion", "telefono", "ciudad"])

def guardar_sucursal(row: dict):
    """Guarda o actualiza una sucursal."""
    try:
        if not supabase: return False, "Sin conexión a Supabase"
        supabase.table("sucursales").upsert(row).execute()
        return True, "Guardado exitosamente"
    except Exception as e:
        print(f"Error guardar_sucursal: {e}")
        return False, str(e)

def eliminar_sucursal(s_id):
    """Elimina una sucursal."""
    try:
        if not supabase: return
        supabase.table("sucursales").delete().eq("id", s_id).execute()
    except Exception as e:
        print(f"Error eliminar_sucursal: {e}")
