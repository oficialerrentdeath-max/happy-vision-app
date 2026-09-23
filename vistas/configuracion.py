import streamlit as st
import pandas as pd
import tempfile
import os
from database import (
    cargar_sucursales, guardar_sucursal, eliminar_sucursal,
    cargar_auditoria, obtener_resumen_dia,
    actualizar_logo_sucursal
)

def render_configuracion():
    st.title("⚙️ Configuración del Sistema")
    
    if "suc_msg" in st.session_state:
        st.toast(st.session_state.pop("suc_msg"))

    tabs_names = ["🏢 Gestión de Sedes", "👤 Mi Perfil"]
    is_admin = st.session_state.get("user_role") == "Administrador"
    if is_admin:
        tabs_names.append("📋 Auditoría")

    st_tabs = st.tabs(tabs_names)
    tab1 = st_tabs[0]
    tab2 = st_tabs[1]
    
    with tab1:
        st.subheader("Locales y Sucursales")
        st.info("Aquí puedes definir las direcciones, teléfonos y logo de cada local para que aparezcan en los certificados PDF.")
        
        df_suc = cargar_sucursales()
        
        with st.expander("➕ Añadir Nueva Sede", expanded=False):
            with st.form("form_nueva_sede", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_nombre = c1.text_input("Nombre de la Sede", placeholder="Ej: Sucursal Centro")
                n_ciudad = c2.text_input("Ciudad", value="Quito")
                n_direccion = st.text_input("Dirección Exacta", placeholder="Av. Principal y Calle Secundaria")
                n_telefono = st.text_input("Teléfono de la Sede", placeholder="02-XXXX-XXX")
                
                if st.form_submit_button("💾 Guardar Sede", type="primary"):
                    if n_nombre and n_direccion:
                        success, msg = guardar_sucursal({
                            "nombre": n_nombre,
                            "direccion": n_direccion,
                            "telefono": n_telefono,
                            "ciudad": n_ciudad
                        })
                        if success:
                            st.session_state["suc_msg"] = f"✅ Sede '{n_nombre}' guardada correctamente."
                            st.rerun()
                        else:
                            st.error(f"❌ Error al guardar: {msg}")
                    else:
                        st.error("Nombre y Dirección son obligatorios.")

        if not df_suc.empty:
            for _, row in df_suc.iterrows():
                logo_url = row.get("logo_url") or ""
                tiene_logo = bool(logo_url)

                with st.container():
                    st.markdown(f"""
                    <div style='background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; margin-bottom: 10px;'>
                        <h4 style='margin:0; color:#1e293b;'>🏢 {row['nombre']}</h4>
                        <p style='margin:5px 0; font-size:14px; color:#64748b;'>📍 {row['direccion']} — {row['ciudad']}</p>
                        <p style='margin:0; font-size:13px; color:#94a3b8;'>📞 {row.get('telefono', 'N/A')} &nbsp;|&nbsp; 🖼️ Logo: {'<b style="color:#16a34a;">Personalizado ✓</b>' if tiene_logo else '<span style="color:#94a3b8;">Predeterminado</span>'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3, c4 = st.columns([3, 1.2, 1.2, 1])

                    # ─── EDITAR DATOS ───────────────────────────────────
                    with c2:
                        with st.popover("✏️ Editar"):
                            with st.form(f"edit_suc_{row['id']}"):
                                e_nombre = st.text_input("Nombre", value=row['nombre'])
                                e_ciudad = st.text_input("Ciudad", value=row.get('ciudad', 'Quito'))
                                e_direccion = st.text_input("Dirección", value=row['direccion'])
                                e_telefono = st.text_input("Teléfono", value=row.get('telefono', ''))
                                
                                if st.form_submit_button("Actualizar"):
                                    success, msg = guardar_sucursal({
                                        "id": row['id'],
                                        "nombre": e_nombre,
                                        "direccion": e_direccion,
                                        "telefono": e_telefono,
                                        "ciudad": e_ciudad
                                    })
                                    if success:
                                        st.session_state["suc_msg"] = f"✅ Sede '{e_nombre}' actualizada con éxito."
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {msg}")

                    # ─── GESTIONAR LOGO ─────────────────────────────────
                    with c3:
                        with st.popover("🖼️ Logo"):
                            st.markdown(f"**Logo para:** `{row['nombre']}`")
                            st.caption("Este logo aparecerá en certificados, facturas y tickets de esta sucursal.")

                            # Vista previa del logo actual
                            if tiene_logo:
                                # Intentar mostrar desde caché local o descarga
                                try:
                                    from supabase_client import get_logo_sucursal_path
                                    logo_preview = get_logo_sucursal_path(row['nombre'])
                                    if logo_preview and os.path.exists(logo_preview):
                                        st.image(logo_preview, caption="Logo actual", width=200)
                                    else:
                                        st.info("Logo guardado en nube ✓")
                                except Exception:
                                    st.info("Logo guardado en nube ✓")
                            else:
                                st.warning("Sin logo personalizado. Se usará el logo predeterminado (`logo.png`).")

                            st.divider()

                            # Subir nuevo logo
                            nuevo_logo = st.file_uploader(
                                "📤 Subir nuevo logo",
                                type=["png", "jpg", "jpeg"],
                                key=f"logo_upload_{row['id']}",
                                help="PNG recomendado con fondo transparente. Máx. 2 MB."
                            )

                            if nuevo_logo is not None:
                                # Validar tamaño (2 MB)
                                if nuevo_logo.size > 2 * 1024 * 1024:
                                    st.error("❌ El archivo supera el límite de 2 MB.")
                                else:
                                    st.image(nuevo_logo, caption="Vista previa del nuevo logo", width=200)

                                    if st.button("💾 Guardar Logo", key=f"btn_save_logo_{row['id']}", type="primary", use_container_width=True):
                                        with st.spinner("Subiendo logo..."):
                                            try:
                                                from supabase_client import upload_logo_sucursal

                                                # Guardar temporalmente en disco
                                                ext = os.path.splitext(nuevo_logo.name)[1].lower() or ".png"
                                                tmp_path = os.path.join(
                                                    os.getcwd(),
                                                    "_logos_cache",
                                                    f"_upload_tmp_{row['id']}{ext}"
                                                )
                                                os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
                                                with open(tmp_path, "wb") as f:
                                                    f.write(nuevo_logo.getbuffer())

                                                # Subir a Supabase Storage
                                                remote_path = upload_logo_sucursal(tmp_path, row['nombre'])

                                                # Limpiar temporal de upload
                                                try:
                                                    os.remove(tmp_path)
                                                except Exception:
                                                    pass

                                                if remote_path:
                                                    # Guardar ruta en la tabla sucursales
                                                    ok = actualizar_logo_sucursal(row['nombre'], remote_path)
                                                    if ok:
                                                        # Limpiar caché del logo anterior
                                                        nombre_limpio = row['nombre'].lower().replace(" ", "_").replace("/", "-")
                                                        cache_dir = os.path.join(os.getcwd(), "_logos_cache")
                                                        for old_ext in [".png", ".jpg", ".jpeg"]:
                                                            old_cache = os.path.join(cache_dir, f"{nombre_limpio}{old_ext}")
                                                            if os.path.exists(old_cache):
                                                                try:
                                                                    os.remove(old_cache)
                                                                except Exception:
                                                                    pass
                                                        st.session_state["suc_msg"] = f"✅ Logo de '{row['nombre']}' actualizado correctamente."
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Logo subido pero no se pudo registrar en la base de datos.")
                                                else:
                                                    st.error("❌ Error al subir el logo a Supabase Storage.")
                                            except Exception as e:
                                                st.error(f"❌ Error inesperado: {e}")

                            # Eliminar logo personalizado
                            if tiene_logo:
                                st.divider()
                                if st.button("🗑️ Eliminar Logo Personalizado", key=f"btn_del_logo_{row['id']}", use_container_width=True):
                                    with st.spinner("Eliminando logo..."):
                                        try:
                                            from supabase_client import delete_logo_sucursal
                                            delete_logo_sucursal(row['nombre'])
                                            actualizar_logo_sucursal(row['nombre'], "")
                                            st.session_state["suc_msg"] = f"✅ Logo de '{row['nombre']}' eliminado. Se usará el logo predeterminado."
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error al eliminar: {e}")

                    # ─── ELIMINAR SEDE ──────────────────────────────────
                    with c4:
                        if st.button("🗑️", key=f"del_suc_{row['id']}", use_container_width=True, help="Eliminar sede"):
                            eliminar_sucursal(row['id'])
                            st.success("Sede eliminada.")
                            st.rerun()
        else:
            st.warning("No hay sedes registradas. Por favor añade la 'Matriz' primero.")

    with tab2:
        st.subheader("Información del Usuario")
        st.write(f"**Usuario:** {st.session_state.get('user_login')}")
        st.write(f"**Nombre:** {st.session_state.get('user_name')}")
        st.write(f"**Rol:** {st.session_state.get('user_role')}")
        st.write(f"**Cargo:** {st.session_state.get('user_cargo')}")

    if is_admin:
        with st_tabs[2]:
            st.subheader("📋 Registro de Auditoría")
            tabs_admin = st.tabs(["📊 Auditoría de Cambios", "👤 Control de Sesiones"])
            
            with tabs_admin[0]:
                st.info("Registro inmutable de cambios en Pacientes, Historias, Inventario y Laboratorio.")
                
                # RESUMEN CONTABLE GLOBAL (TODAS LAS SEDES)
                df_s = cargar_sucursales()
                sedes = df_s["nombre"].tolist() if not df_s.empty else ["Matriz"]
                hoy = pd.Timestamp.now().strftime("%Y-%m-%d")
                
                t_ventas = 0
                t_gastos = 0
                for s in sedes:
                    res = obtener_resumen_dia(s, hoy)
                    t_ventas += (res["Efectivo"] + res["Tarjeta"] + res["Transferencia"])
                    t_gastos += res["Gastos"]
                
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("💰 Ventas Globales (Hoy)", f"${t_ventas:.2f}")
                c_m2.metric("📉 Gastos Globales (Hoy)", f"${t_gastos:.2f}")
                c_m3.metric("📈 Utilidad Bruta", f"${t_ventas - t_gastos:.2f}")
                st.markdown("---")
                
                df_auditoria = cargar_auditoria(limit=2000)
                if not df_auditoria.empty:
                    # Filtrar para NO mostrar seguridad aquí
                    df_cambios = df_auditoria[df_auditoria["entidad"] != "Seguridad"]
                    
                    if "fecha_hora" in df_cambios.columns:
                        df_cambios["fecha_hora"] = pd.to_datetime(df_cambios["fecha_hora"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    c1, c2 = st.columns(2)
                    filtro_usr = c1.selectbox("Filtrar por Usuario", ["Todos"] + df_cambios["usuario"].unique().tolist(), key="f_usr_aud")
                    filtro_acc = c2.selectbox("Filtrar por Acción", ["Todas"] + df_cambios["accion"].unique().tolist(), key="f_acc_aud")
                    
                    df_view = df_cambios.copy()
                    if filtro_usr != "Todos": df_view = df_view[df_view["usuario"] == filtro_usr]
                    if filtro_acc != "Todas": df_view = df_view[df_view["accion"] == filtro_acc]
                    
                    st.dataframe(df_view[["fecha_hora", "nombre_usuario", "accion", "entidad", "detalle", "sucursal"]], use_container_width=True, hide_index=True)
                else:
                    st.warning("No hay registros de cambios.")

            with tabs_admin[1]:
                st.info("Registro de accesos al sistema (Inicios de sesión, salidas e intentos fallidos).")
                if not df_auditoria.empty:
                    # Filtrar para mostrar SOLO seguridad aquí
                    df_sesiones = df_auditoria[df_auditoria["entidad"] == "Seguridad"]
                    
                    if "fecha_hora" in df_sesiones.columns:
                        df_sesiones["fecha_hora"] = pd.to_datetime(df_sesiones["fecha_hora"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.dataframe(df_sesiones[["fecha_hora", "usuario", "accion", "detalle", "sucursal"]], use_container_width=True, hide_index=True)
                else:
                    st.warning("No hay registros de sesiones.")
