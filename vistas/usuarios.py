"""
vistas/usuarios.py — Gestión de Usuarios (solo Administrador)
Permite crear/eliminar optometristas con sus datos para el certificado en Supabase.
"""
import os
import streamlit as st
import base64
from database import supabase

def _cargar_usuarios() -> dict:
    """Carga los usuarios desde Supabase y los retorna como diccionario."""
    if not supabase: return {}
    try:
        res = supabase.table("usuarios").select("*").execute()
        if res.data:
            # Convertir a formato dict con username como key
            return {row["username"]: row for row in res.data}
    except Exception as e:
        print(f"Error cargando usuarios: {e}")
    return {}

def _guardar_usuarios(data: dict):
    """Guarda/Actualiza múltiples usuarios en Supabase."""
    if not supabase: return
    try:
        records = []
        for username, udata in data.items():
            record = udata.copy()
            record["username"] = username
            records.append(record)
        if records:
            supabase.table("usuarios").upsert(records).execute()
    except Exception as e:
        print(f"Error guardando usuarios: {e}")

def _guardar_usuario(username: str, data: dict):
    """Guarda/Actualiza un solo usuario en Supabase."""
    if not supabase: return
    try:
        record = data.copy()
        record["username"] = username
        supabase.table("usuarios").upsert(record).execute()
    except Exception as e:
        print(f"Error guardando usuario: {e}")

def _eliminar_usuario(username: str):
    """Elimina un usuario de Supabase."""
    if not supabase: return
    try:
        supabase.table("usuarios").delete().eq("username", username).execute()
    except Exception as e:
        print(f"Error eliminando usuario: {e}")


def render_usuarios():
    # Solo el admin puede ver esta página
    if st.session_state.get("user_role") != "Administrador":
        st.error("Acceso restringido. Solo el Administrador puede gestionar usuarios.")
        return

    st.markdown("""
    <div class="page-header">
        <h1>👤 Gestión de Usuarios</h1>
        <p>Crea y administra los optometristas del sistema (Supabase)</p>
    </div>
    """, unsafe_allow_html=True)

    usuarios = _cargar_usuarios()

    # ── LISTA DE USUARIOS ──────────────────────────────────────────
    st.markdown("<div class='section-title'>Usuarios registrados</div>", unsafe_allow_html=True)

    for username, data in usuarios.items():
        is_admin = username == "admin"
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.markdown(
                f"**{data.get('nombre', username)}**  \\n"
                f"<span style='font-size:12.5px;color:#334155;font-weight:500;'>👤 `{username}` · {data.get('role','')}</span>",
                unsafe_allow_html=True
            )
            c2.caption(f"🏷️ {data.get('cargo', '—')}")
            c3.caption(f"📋 Reg: {data.get('registro', '—')}")
            with c4:
                if not is_admin:
                    if st.button("🗑️ Eliminar", key=f"del_usr_{username}", type="secondary"):
                        _eliminar_usuario(username)
                        st.success(f"Usuario '{username}' eliminado.")
                        st.rerun()
                else:
                    if st.button("✏️ Editar Admin", key=f"edit_usr_{username}", type="secondary"):
                        st.session_state[f"editando_admin"] = True
                
                if st.session_state.get("editando_admin") and is_admin:
                    with st.form("edit_admin_form"):
                        st.markdown("**Editar datos del Administrador**")
                        ead1, ead2 = st.columns(2)
                        en_nombre   = ead1.text_input("Nombre Completo", value=data.get("nombre", ""))
                        en_cargo    = ead2.text_input("Cargo", value=data.get("cargo", ""))
                        ead3, ead4 = st.columns(2)
                        en_registro = ead3.text_input("N° Registro Professional", value=data.get("registro", ""))
                        en_telefono = ead4.text_input("Teléfono", value=data.get("telefono", ""))
                        
                        ecol1, ecol2 = st.columns(2)
                        if ecol1.form_submit_button("Guardar Cambios Admin"):
                            data["nombre"] = en_nombre.strip()
                            data["cargo"] = en_cargo.strip()
                            data["registro"] = en_registro.strip()
                            data["telefono"] = en_telefono.strip()
                            _guardar_usuario(username, data)
                            
                            if st.session_state.get("user_login") == "admin":
                                st.session_state.user_name = en_nombre.strip()
                                st.session_state.user_cargo = en_cargo.strip()
                                st.session_state.user_registro = en_registro.strip()
                                st.session_state.user_telefono = en_telefono.strip()
                                
                            st.session_state["editando_admin"] = False
                            st.success("Datos de Administrador actualizados.")
                            st.rerun()
                        if ecol2.form_submit_button("Cancelar"):
                            st.session_state["editando_admin"] = False
                            st.rerun()
            st.divider()

    # ── CREAR NUEVO USUARIO ────────────────────────────────────────
    st.markdown("<div class='section-title'>➕ Crear Nuevo Optometrista</div>", unsafe_allow_html=True)

    with st.form("form_nuevo_usuario", clear_on_submit=True):
        nc1, nc2 = st.columns(2)
        nu_username = nc1.text_input("Nombre de usuario (login) *", placeholder="ej: anthonny")
        nu_password = nc2.text_input("Contraseña *", type="password", placeholder="••••••••")

        nd1, nd2, nd3 = st.columns(3)
        nu_nombre   = nd1.text_input("Nombre Completo *", placeholder="Dr. Juan Pérez")
        nu_cargo    = nd2.text_input("Cargo / Título", placeholder="Optometrista", value="Optometrista")
        nu_registro = nd3.text_input("N° Registro Profesional", placeholder="OP-1234")

        ne1, ne2 = st.columns(2)
        nu_telefono = ne1.text_input("Teléfono", placeholder="+593 98 765 4321")
        nu_role     = ne2.selectbox("Rol en el sistema", ["Optometrista", "Administrador"])

        st.caption("Firma para el certificado PDF (opcional)")
        nu_firma = st.file_uploader(
            "Subir imagen de firma (PNG recomendado, fondo blanco)",
            type=["png", "jpg", "jpeg"],
            key="firma_upload"
        )

        submitted = st.form_submit_button("✅ Crear Usuario", type="primary", use_container_width=True)
        if submitted:
            if not nu_username.strip() or not nu_password.strip() or not nu_nombre.strip():
                st.error("⚠️ Usuario, contraseña y nombre son obligatorios.")
            elif nu_username.strip() in usuarios:
                st.error(f"⚠️ El usuario '{nu_username}' ya existe.")
            else:
                firma_b64 = None
                if nu_firma is not None:
                    # Convertir a Base64
                    try:
                        firma_b64 = base64.b64encode(nu_firma.getvalue()).decode()
                    except Exception as e:
                        st.warning(f"No se pudo procesar la firma: {e}")

                new_user = {
                    "password":  nu_password.strip(),
                    "role":      nu_role,
                    "nombre":    nu_nombre.strip(),
                    "cargo":     nu_cargo.strip() or "Optometrista",
                    "registro":  nu_registro.strip(),
                    "telefono":  nu_telefono.strip(),
                    "firma_base64": firma_b64
                }
                
                _guardar_usuario(nu_username.strip(), new_user)
                st.success(f"✅ Usuario **{nu_nombre.strip()}** (`{nu_username.strip()}`) creado exitosamente en Supabase.")
                st.rerun()
