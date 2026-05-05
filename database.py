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
# INVENTARIO
# ══════════════════════════════════════════════════════════════
def cargar_inventario(sucursal: str = None) -> pd.DataFrame:
    """Carga el inventario. Si se pasa sucursal, filtra por ella."""
    try:
        if not supabase: return pd.DataFrame()
        query = supabase.table("inventario").select("*")
        if sucursal:
            query = query.eq("sucursal", sucursal)
        res = query.order("nombre").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        print(f"Error cargar_inventario: {e}")
        return pd.DataFrame()

def guardar_producto(data: dict):
    """Guarda o actualiza un producto en el inventario."""
    try:
        if not supabase: return
        if "id" in data:
            supabase.table("inventario").update(data).eq("id", data["id"]).execute()
        else:
            supabase.table("inventario").insert(data).execute()
    except Exception as e:
        print(f"Error guardar_producto: {e}")

# ══════════════════════════════════════════════════════════════
# ÓRDENES DE TRABAJO (LABORATORIO)
# ══════════════════════════════════════════════════════════════
def cargar_ordenes_trabajo(sucursal: str = None, limit: int = 200) -> pd.DataFrame:
    """Carga las órdenes de trabajo recientes."""
    try:
        if not supabase: return pd.DataFrame()
        query = supabase.table("ordenes_trabajo").select("*")
        if sucursal:
            query = query.eq("sucursal", sucursal)
        res = query.order("creado_el", desc=True).limit(limit).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        print(f"Error cargar_ordenes_trabajo: {e}")
        return pd.DataFrame()

def guardar_orden_trabajo(data: dict):
    """Inserta una nueva orden de trabajo."""
    try:
        if not supabase: return None
        res = supabase.table("ordenes_trabajo").insert(data).execute()
        if res.data:
            # Registrar en auditoría automáticamente
            registrar_auditoria(
                accion="Nueva Orden de Trabajo",
                entidad="Laboratorio",
                detalle=f"Orden para: {data.get('paciente_nombre')} | Total: {data.get('total_venta')} | Estado: {data.get('estado')}",
                usuario=data.get("vendedor", ""),
                sucursal=data.get("sucursal", "")
            )
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error guardar_orden_trabajo: {e}")
        return None

def actualizar_estado_orden(orden_id: int, nuevo_estado: str, usuario: str = "", sucursal: str = ""):
    """Actualiza el estado de una orden (Pendiente -> Laboratorio -> etc)."""
    try:
        if not supabase: return
        supabase.table("ordenes_trabajo").update({"estado": nuevo_estado}).eq("id", orden_id).execute()
        registrar_auditoria(
            accion="Cambio Estado Orden",
            entidad="Laboratorio",
            detalle=f"Orden ID {orden_id} pasó a estado: {nuevo_estado}",
            usuario=usuario,
            sucursal=sucursal
        )
    except Exception as e:
        print(f"Error actualizar_estado_orden: {e}")

# ══════════════════════════════════════════════════════════════
# CONTABILIDAD Y CAJA
# ══════════════════════════════════════════════════════════════
def obtener_estado_caja(sucursal: str, fecha: str) -> dict:
    """Busca si hay una caja abierta para hoy en esta sucursal."""
    try:
        if not supabase: return None
        res = supabase.table("caja_diaria").select("*").eq("sucursal", sucursal).eq("fecha", fecha).execute()
        return res.data[0] if res.data else None
    except: return None

def abrir_caja(data: dict):
    """Crea el registro de apertura de caja."""
    try:
        if not supabase: return
        supabase.table("caja_diaria").insert(data).execute()
        registrar_auditoria("Apertura de Caja", "Contabilidad", f"Monto inicial: ${data['monto_apertura']}", data['abierta_por'], sucursal=data['sucursal'])
    except Exception as e: print(f"Error abrir_caja: {e}")

def registrar_gasto(data: dict):
    """Registra un egreso de dinero."""
    try:
        if not supabase: return
        supabase.table("gastos").insert(data).execute()
        registrar_auditoria("Gasto Registrado", "Contabilidad", f"{data['categoria']}: ${data['monto']}", data['usuario'], sucursal=data['sucursal'])
    except Exception as e: print(f"Error registrar_gasto: {e}")

def obtener_resumen_dia(sucursal: str, fecha: str):
    """Calcula totales de ventas y gastos del día para el cierre."""
    try:
        if not supabase: return {"Efectivo":0, "Tarjeta":0, "Transferencia":0, "Gastos":0}
        # Ventas (Abonos de nuevas órdenes + Saldos cobrados)
        # Nota: Simplificado para este MVP sumando abonos de órdenes creadas hoy
        res_v = supabase.table("ordenes_trabajo").select("total_venta, abono, metodo_pago").eq("sucursal", sucursal).filter("creado_el", "gte", f"{fecha}T00:00:00").execute()
        
        totales = {"Efectivo":0, "Tarjeta":0, "Transferencia":0, "Gastos":0}
        for v in res_v.data:
            m = v.get("metodo_pago", "Efectivo")
            totales[m] += float(v.get("abono", 0))
            
        # Gastos
        res_g = supabase.table("gastos").select("monto").eq("sucursal", sucursal).eq("fecha", fecha).execute()
        totales["Gastos"] = sum(float(g["monto"]) for g in res_g.data)
        
        return totales
    except: return {"Efectivo":0, "Tarjeta":0, "Transferencia":0, "Gastos":0}

def cerrar_caja(caja_id: int, data: dict):
    """Cierra la caja del día."""
    try:
        if not supabase: return
        supabase.table("caja_diaria").update(data).eq("id", caja_id).execute()
        registrar_auditoria("Cierre de Caja", "Contabilidad", f"Cierre final: ${data['monto_cierre']}", data['cerrada_por'], sucursal=data['sucursal'])
    except Exception as e: print(f"Error cerrar_caja: {e}")

def actualizar_historia(historia_id: int, data: dict):
    """Actualiza campos de una historia clínica en Supabase."""
    try:
        if not supabase: return
        supabase.table("historias").update(data).eq("id", historia_id).execute()
        registrar_auditoria("Actualizar Historia", "Clínica", f"ID Historia: {historia_id}", st.session_state.user_login, sucursal=st.session_state.get("sucursal_activa", ""))
    except Exception as e: print(f"Error actualizar_historia: {e}")

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
