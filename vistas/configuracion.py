import streamlit as st
import pandas as pd
from database import cargar_sucursales, guardar_sucursal, eliminar_sucursal

def render_configuracion():
    st.title("⚙️ Configuración del Sistema")
    
    if "suc_msg" in st.session_state:
        st.success(st.session_state.pop("suc_msg"))
        st.balloons()

    tab1, tab2 = st.tabs(["🏢 Gestión de Sedes", "👤 Mi Perfil"])
    
    with tab1:
        st.subheader("Locales y Sucursales")
        st.info("Aquí puedes definir las direcciones y teléfonos de cada local para que aparezcan en los certificados PDF.")
        
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
                with st.container():
                    st.markdown(f"""
                    <div style='background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; margin-bottom: 10px;'>
                        <h4 style='margin:0; color:#1e293b;'>🏢 {row['nombre']}</h4>
                        <p style='margin:5px 0; font-size:14px; color:#64748b;'>📍 {row['direccion']} — {row['ciudad']}</p>
                        <p style='margin:0; font-size:13px; color:#94a3b8;'>📞 {row.get('telefono', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
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
                    with c3:
                        if st.button("🗑️ Eliminar", key=f"del_suc_{row['id']}", use_container_width=True):
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
