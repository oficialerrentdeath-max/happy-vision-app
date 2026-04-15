import streamlit as st
from utils import guardar_datos


def render_pacientes():
    st.markdown("<div class='section-title'>👥 Registro de Pacientes</div>", unsafe_allow_html=True)

    df_p_page = st.session_state.df_pacientes
    df_h_page = st.session_state.df_historias

    busq_p = st.text_input("🔍 Buscar paciente por nombre o cedula:", placeholder="Escribe para filtrar...")

    if busq_p:
        mask_p = (
            df_p_page["nombre"].str.contains(busq_p, case=False, na=False) |
            df_p_page["identificacion"].str.contains(busq_p, case=False, na=False)
        )
        df_vista = df_p_page[mask_p]
    else:
        df_vista = df_p_page

    if len(df_vista) == 0:
        st.info("👥 No se encontraron pacientes. Agrégalos desde Historias Clínicas.")
    else:
        st.markdown(f"**{len(df_vista)} paciente(s) encontrado(s)**")
        for _, prow in df_vista.iterrows():
            n_hist = len(df_h_page[df_h_page["paciente_id"] == prow["id"]])
            col_a, col_b, col_c, col_d, col_e = st.columns([3, 2, 2, 1, 2])
            col_a.markdown(f"**{prow.get('nombre','')}**")
            col_b.caption(f"🆔 {prow.get('identificacion','')}")
            col_c.caption(f"📞 {prow.get('telefono','')}")
            col_d.caption(f"📁 {n_hist} HC")
            if col_e.button("🩺 Ver Historial", key=f"verac_{prow['id']}"):
                st.session_state.page = "Clinica"
                st.session_state["clinica_buscar"] = str(prow.get("nombre", ""))
                st.rerun()
            st.divider()

    st.markdown("---")
    import pandas as pd
    with st.expander("➕ Agregar Nuevo Paciente", expanded=False):
        with st.form("form_nuevo_pac_page", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            np_id  = fc1.text_input("Cédula / ID")
            np_nom = fc2.text_input("Nombre completo")
            fc3, fc4, fc5 = st.columns(3)
            np_gen  = fc3.selectbox("Género", ["Masculino", "Femenino", "Otro"])
            np_edad = fc4.number_input("Edad", 1, 120, 25)
            np_tel  = fc5.text_input("Teléfono")
            fc6, fc7 = st.columns(2)
            np_cor = fc6.text_input("Correo")
            np_ocu = fc7.text_input("Ocupación")
            np_dir = st.text_input("Dirección")
            if st.form_submit_button("📥 Registrar Paciente", type="primary", use_container_width=True):
                if np_nom and np_id:
                    nuevo_p = {
                        "id": len(st.session_state.df_pacientes) + 1,
                        "identificacion": np_id, "nombre": np_nom,
                        "genero": np_gen, "edad": np_edad, "telefono": np_tel,
                        "correo": np_cor, "ocupacion": np_ocu, "direccion": np_dir,
                    }
                    st.session_state.df_pacientes = pd.concat(
                        [st.session_state.df_pacientes, pd.DataFrame([nuevo_p])], ignore_index=True
                    )
                    guardar_datos()
                    st.success(f"✅ Paciente {np_nom} registrado correctamente.")
                    st.rerun()
                else:
                    st.warning("Nombre y Cédula son obligatorios.")
