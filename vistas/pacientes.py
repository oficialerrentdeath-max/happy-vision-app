import streamlit as st
import pandas as pd
from datetime import date
from utils import guardar_datos


def render_pacientes():
    st.markdown("""
    <div class="page-header">
        <h1>👥 Registro de Pacientes</h1>
        <p>Directorio completo de pacientes ordenado alfabeticamente por apellidos</p>
    </div>
    """, unsafe_allow_html=True)

    df_p_page = st.session_state.df_pacientes.copy()
    df_h_page = st.session_state.df_historias

    # ── FORMULARIO AGREGAR PACIENTE (arriba del listado) ──────────────
    with st.expander("➕ Agregar Nuevo Paciente", expanded=False):
        with st.form("form_nuevo_pac_page", clear_on_submit=True):
            fc1, fc2, fc3, fc4 = st.columns([1, 1.5, 1.5, 1])
            np_id       = fc1.text_input("Cedula / ID")
            np_nombres  = fc2.text_input("Nombres *")
            np_apellidos= fc3.text_input("Apellidos *")
            np_gen      = fc4.selectbox("Genero", ["Masculino", "Femenino", "Otro"])
            fc5, fc6, fc7 = st.columns(3)
            np_fnac = fc5.date_input("Fecha Nacimiento", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today())
            np_tel  = fc6.text_input("Telefono")
            np_cor  = fc7.text_input("Correo")
            fc8, fc9 = st.columns(2)
            np_ocu = fc8.text_input("Ocupacion")
            np_dir = fc9.text_input("Direccion")
            if st.form_submit_button("Registrar Paciente", type="primary", use_container_width=True):
                if np_nombres.strip() and np_apellidos.strip():
                    hoy = date.today()
                    edad_calc = hoy.year - np_fnac.year - ((hoy.month, hoy.day) < (np_fnac.month, np_fnac.day))
                    nombre_completo = f"{np_apellidos.strip()} {np_nombres.strip()}"
                    nuevo_p = {
                        "id": len(st.session_state.df_pacientes) + 1,
                        "identificacion": np_id, "nombre": nombre_completo,
                        "nombres": np_nombres.strip(), "apellidos": np_apellidos.strip(),
                        "genero": np_gen, "edad": str(edad_calc),
                        "fecha_nacimiento": np_fnac.strftime("%Y-%m-%d"),
                        "telefono": np_tel, "correo": np_cor,
                        "ocupacion": np_ocu, "direccion": np_dir,
                    }
                    st.session_state.df_pacientes = pd.concat(
                        [st.session_state.df_pacientes, pd.DataFrame([nuevo_p])], ignore_index=True
                    )
                    guardar_datos()
                    st.success(f"Paciente {nombre_completo} registrado correctamente.")
                    st.rerun()
                else:
                    st.warning("Nombres y Apellidos son obligatorios.")

    st.markdown("---")

    # ── BUSCADOR ──────────────────────────────────────────────────────
    busq_p = st.text_input("Buscar por apellido, nombre o cedula:", placeholder="Escribe para filtrar...")

    if busq_p:
        mask_p = (
            df_p_page["nombre"].str.contains(busq_p, case=False, na=False) |
            df_p_page["identificacion"].astype(str).str.contains(busq_p, case=False, na=False) |
            (df_p_page.get("apellidos", df_p_page["nombre"]).astype(str).str.contains(busq_p, case=False, na=False))
        )
        df_vista = df_p_page[mask_p]
    else:
        # Orden alfabetico por apellidos, luego por nombres
        if "apellidos" in df_p_page.columns:
            df_vista = df_p_page.sort_values(
                by=["apellidos", "nombres"],
                key=lambda c: c.astype(str).str.upper().str.strip(),
                ascending=True
            )
        else:
            df_vista = df_p_page.sort_values(
                by="nombre",
                key=lambda c: c.astype(str).str.upper().str.strip(),
                ascending=True
            )

    # ── LISTADO DE PACIENTES ──────────────────────────────────────────
    if len(df_vista) == 0:
        st.info("No se encontraron pacientes.")
    else:
        st.markdown(f"**{len(df_vista)} paciente(s) registrado(s)**")
        for _, prow in df_vista.iterrows():
            n_hist = len(df_h_page[df_h_page["paciente_id"].astype(str) == str(prow["id"])])

            # Mostrar: Apellidos, Nombres
            _apellidos = str(prow.get("apellidos", "")).strip()
            _nombres   = str(prow.get("nombres", "")).strip()
            if _apellidos and _nombres:
                display_name = f"{_apellidos} {_nombres}"
            else:
                display_name = str(prow.get("nombre", ""))

            col_num, col_a, col_b, col_c, col_d, col_e = st.columns([0.5, 3, 2, 2, 1, 2])
            col_num.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='color:#93c5fd;font-size:18px;font-weight:800;'>"
                f"{prow.get('id','')}</span></div>",
                unsafe_allow_html=True
            )
            col_a.markdown(f"**{display_name}**")
            col_b.caption(f"ID {prow.get('identificacion','')}")
            col_c.caption(f"Tel: {prow.get('telefono','')}")
            col_d.caption(f"{n_hist} HC")
            if col_e.button("Ver Historial", key=f"verac_{prow['id']}"):
                st.session_state.page = "Clinica"
                st.session_state["clinica_buscar"] = str(prow.get("nombre", ""))
                st.rerun()
            st.divider()
