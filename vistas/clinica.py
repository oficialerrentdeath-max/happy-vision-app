import streamlit as st
import pandas as pd
from datetime import date
from utils import wa_link, guardar_datos, generar_pdf_historia


def render_clinica():
    st.markdown("""
    <div class="page-header">
        <h1>🩺 Historias Clínicas</h1>
        <p>Registro y seguimiento de evaluaciones optométricas de cada paciente</p>
    </div>
    """, unsafe_allow_html=True)

    # ── CONFIGURACIÓN DEL OPTOMETRISTA ────────────────────
    with st.expander("⚙️ Configuración del Optometrista (Sello del PDF)", expanded=False):
        cola, colb, colc = st.columns(3)
        st.session_state.opto_nombre   = cola.text_input("Nombre del Optometrista", value=st.session_state.opto_nombre)
        st.session_state.opto_cargo    = colb.text_input("Cargo / Título",           value=st.session_state.opto_cargo)
        st.session_state.opto_registro = colc.text_input("N° de Registro",           value=st.session_state.opto_registro)
        cold, cole = st.columns(2)
        if "opto_direccion" not in st.session_state:
            st.session_state.opto_direccion = "Happy Vision"
        if "opto_telefono" not in st.session_state:
            st.session_state.opto_telefono = "+593 96 324 1158"
        st.session_state.opto_direccion = cold.text_input("Dirección (pie de página)", value=st.session_state.opto_direccion)
        st.session_state.opto_telefono  = cole.text_input("Teléfono (pie de página)", value=st.session_state.opto_telefono)
        st.caption("Estos datos aparecerán en el Certificado Visual PDF.")
        if st.button("💾 Guardar Datos del Optometrista", use_container_width=True, type="primary"):
            guardar_datos()
            st.success("✅ Configuración guardada.")

    st.markdown("---")

    # ── BUSCADOR ────────────────────────────────────────────
    st.markdown("<div class='section-title'>🔍 Buscar Paciente</div>", unsafe_allow_html=True)
    busca_col, nuevo_col = st.columns([3, 1])
    with busca_col:
        if "clinica_buscar" in st.session_state and st.session_state["clinica_buscar"]:
            st.session_state["buscador_act"] = st.session_state["clinica_buscar"]
            st.session_state["clinica_buscar"] = ""
        q = st.text_input("Buscador", key="buscador_act", placeholder="Escribe el nombre o cédula del paciente...", label_visibility="collapsed")
    with nuevo_col:
        mostrar_form_nuevo = st.button("➕ Nuevo Paciente", use_container_width=True, type="secondary")

    df_p_all = st.session_state.df_pacientes.copy()

    # ── Formulario NUEVO PACIENTE ────────────────────────────
    if mostrar_form_nuevo:
        st.session_state["mostrar_nuevo_p"] = not st.session_state.get("mostrar_nuevo_p", False)

    if st.session_state.get("mostrar_nuevo_p", False):
        with st.form("nuevo_paciente", clear_on_submit=True):
            st.markdown("<div class='section-title'>Registrar Nuevo Paciente</div>", unsafe_allow_html=True)
            col_p1, col_p2, col_p3 = st.columns(3)
            p_id     = col_p1.text_input("Cédula/ID")
            p_nombre = col_p2.text_input("Nombre Completo")
            p_genero = col_p3.selectbox("Género", ["Masculino", "Femenino", "Otro"])

            col_p4, col_p5, col_p6 = st.columns(3)
            p_fnac  = col_p4.date_input("Fecha de Nacimiento", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today())
            p_tel   = col_p5.text_input("Teléfono")
            p_email = col_p6.text_input("Correo")
            col_p7, col_p8 = st.columns(2)
            p_dir   = col_p7.text_input("Dirección")
            p_ocupa = col_p8.text_input("Ocupación")

            colbtn1, _ = st.columns([2, 1])
            with colbtn1:
                guardar_p = st.form_submit_button("✅ Guardar Paciente", type="primary", use_container_width=True)
            if guardar_p:
                if p_nombre.strip():
                    hoy = date.today()
                    p_edad_calc = hoy.year - p_fnac.year - ((hoy.month, hoy.day) < (p_fnac.month, p_fnac.day))
                    nuevo_p = {
                        "id": str(len(st.session_state.df_pacientes) + 1),
                        "identificacion": str(p_id), "nombre": p_nombre, "genero": p_genero,
                        "direccion": p_dir, "edad": str(p_edad_calc),
                        "fecha_nacimiento": p_fnac.strftime("%Y-%m-%d"),
                        "telefono": p_tel, "correo": p_email, "ocupacion": p_ocupa,
                    }
                    st.session_state.df_pacientes = pd.concat([st.session_state.df_pacientes, pd.DataFrame([nuevo_p])], ignore_index=True)
                    guardar_datos()
                    st.success(f"✅ Paciente **{p_nombre}** registrado.")
                    st.session_state["mostrar_nuevo_p"] = False
                    st.rerun()
                else:
                    st.error("⚠️ El Nombre es obligatorio.")

    # ── RESULTADOS DE BÚSQUEDA ────────────────────────
    if q:
        resultados = df_p_all[
            df_p_all["nombre"].str.contains(q, case=False, na=False) |
            df_p_all["identificacion"].astype(str).str.contains(q, case=False, na=False)
        ]
        if len(resultados) == 0:
            st.info(f"No se encontró '«{q}»'. Usa ➕ Nuevo Paciente.")
        else:
            for _, pac in resultados.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style='background:#1e293b; border-radius:10px; padding:14px 18px; margin-bottom:10px; border-left:4px solid #3b82f6;'>
                    <b style='font-size:16px; color:#e2e8f0;'>{pac.get('nombre','')}</b>
                    <span style='color:#475569; margin-left:12px; font-size:12px;'>
                    🆔 {pac.get('identificacion','')} &nbsp;| 📅 {pac.get('edad','')} años &nbsp;| 📞 {pac.get('telefono','')} &nbsp;| {pac.get('genero','')}</span></div>
                    """, unsafe_allow_html=True)

                    hist_pac = st.session_state.df_historias[
                        st.session_state.df_historias["paciente_id"] == pac["id"]
                    ].sort_values("fecha", ascending=False)

                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.caption(f"🗂️ {len(hist_pac)} consulta(s)")

                    with cb:
                        if st.button("📋 Nueva Consulta", key=f"new_h_{pac['id']}", use_container_width=True, type="primary"):
                            st.session_state["nueva_consulta_paciente"] = pac["nombre"]
                            st.rerun()

                    with cc:
                        if st.button("✏️ Editar Datos", key=f"edit_p_{pac['id']}", use_container_width=True):
                            st.session_state["editar_paciente_id"] = pac["id"]

                    # Editar datos del paciente
                    if st.session_state.get("editar_paciente_id") == pac["id"]:
                        with st.form(f"edit_pac_{pac['id']}", clear_on_submit=False):
                            ec1, ec2, ec3 = st.columns(3)
                            e_id  = ec1.text_input("Cédula", value=str(pac.get("identificacion", "")))
                            e_nom = ec2.text_input("Nombre", value=str(pac.get("nombre", "")))
                            e_gen = ec3.selectbox("Género", ["Masculino","Femenino","Otro"],
                                index=["Masculino","Femenino","Otro"].index(pac.get("genero","Masculino"))
                                      if pac.get("genero","Masculino") in ["Masculino","Femenino","Otro"] else 0)
                            ec4, ec5, ec6 = st.columns(3)
                            fnac_val  = pac.get("fecha_nacimiento", "")
                            default_d = date(1990,1,1)
                            if fnac_val:
                                try: default_d = date.fromisoformat(str(fnac_val))
                                except: pass
                            e_fnac = ec4.date_input("Fecha de Nacimiento", value=default_d, min_value=date(1900,1,1), max_value=date.today())
                            e_tel  = ec5.text_input("Teléfono", value=str(pac.get("telefono", "")))
                            e_mail = ec6.text_input("Correo",   value=str(pac.get("correo", "")))
                            ec7, ec8 = st.columns(2)
                            e_dir = ec7.text_input("Dirección", value=str(pac.get("direccion", "")))
                            e_ocu = ec8.text_input("Ocupación", value=str(pac.get("ocupacion", "")))
                            if st.form_submit_button("💾 Actualizar", type="primary"):
                                idx_p = st.session_state.df_pacientes[st.session_state.df_pacientes["id"] == pac["id"]].index[0]
                                hoy   = date.today()
                                new_edad = hoy.year - e_fnac.year - ((hoy.month, hoy.day) < (e_fnac.month, e_fnac.day))
                                st.session_state.df_pacientes.at[idx_p, "identificacion"]  = str(e_id)
                                st.session_state.df_pacientes.at[idx_p, "nombre"]          = str(e_nom)
                                st.session_state.df_pacientes.at[idx_p, "genero"]          = str(e_gen)
                                st.session_state.df_pacientes.at[idx_p, "fecha_nacimiento"] = e_fnac.strftime("%Y-%m-%d")
                                st.session_state.df_pacientes.at[idx_p, "edad"]            = str(new_edad)
                                st.session_state.df_pacientes.at[idx_p, "telefono"]        = str(e_tel)
                                st.session_state.df_pacientes.at[idx_p, "correo"]          = str(e_mail)
                                st.session_state.df_pacientes.at[idx_p, "direccion"]       = str(e_dir)
                                st.session_state.df_pacientes.at[idx_p, "ocupacion"]       = e_ocu
                                guardar_datos()
                                st.success("✅ Datos actualizados.")
                                st.session_state["editar_paciente_id"] = None
                                st.rerun()

                    # Historias del paciente
                    if len(hist_pac) == 0:
                        st.caption("💭 No hay consultas registradas todavía.")
                    else:
                        for _, hrow in hist_pac.iterrows():
                            h_id = hrow.get('id','')
                            with st.expander(f"📅 Consulta: {hrow.get('fecha','')} — {hrow.get('motivo','Sin motivo')}"):
                                hc1, hc2 = st.columns(2)
                                with hc1:
                                    st.markdown("**Antecedentes**")
                                    st.write(f"Personales: {hrow.get('ant_personales','')}")
                                    st.write(f"Observaciones: {hrow.get('observaciones','')}")
                                with hc2:
                                    st.markdown("**Lensometría (AV SC)**")
                                    st.code(f"OD: {hrow.get('lenso_od','')}  AV lej: {hrow.get('lenso_av_lej_od','')}  AV cer: {hrow.get('lenso_av_cer_od','')}\nOI: {hrow.get('lenso_oi','')}  AV lej: {hrow.get('lenso_av_lej_oi','')}  AV cer: {hrow.get('lenso_av_cer_oi','')}")
                                    st.markdown("**Rx Final (AV CC)**")
                                    st.code(f"OD: {hrow.get('rx_od','')}  AV lej: {hrow.get('rx_av_lej_od','')}  AV cer: {hrow.get('rx_av_cer_od','')}\nOI: {hrow.get('rx_oi','')}  AV lej: {hrow.get('rx_av_lej_oi','')}  AV cer: {hrow.get('rx_av_cer_oi','')}")

                                hact1, hact2 = st.columns(2)
                                with hact1:
                                    if st.button(f"✏️ Editar Historia", key=f"edit_h_{h_id}"):
                                        st.session_state[f"editando_historia_{h_id}"] = True
                                with hact2:
                                    if st.button(f"🗑️ Eliminar Historia", key=f"del_h_{h_id}", type="secondary"):
                                        st.session_state.df_historias = st.session_state.df_historias[
                                            st.session_state.df_historias["id"].astype(str) != str(h_id)
                                        ].reset_index(drop=True)
                                        guardar_datos()
                                        st.success("Historia eliminada.")
                                        st.rerun()

                                if st.session_state.get(f"editando_historia_{h_id}", False):
                                    with st.form(key=f"edit_h_form_{h_id}"):
                                        st.markdown("**✏️ Editar Consulta**")
                                        eh_motivo = st.text_input("Motivo", value=str(hrow.get('motivo','')))
                                        eh_diag   = st.text_input("Diagnóstico", value=str(hrow.get('diagnostico','')))
                                        eh_obs    = st.text_area("Observaciones", value=str(hrow.get('observaciones','')))
                                        eh_lenso_od = st.text_input("Lensometría OD", value=str(hrow.get('lenso_od','')))
                                        eh_lenso_oi = st.text_input("Lensometría OI", value=str(hrow.get('lenso_oi','')))
                                        eh_rx_od    = st.text_input("Rx OD", value=str(hrow.get('rx_od','')))
                                        eh_rx_oi    = st.text_input("Rx OI", value=str(hrow.get('rx_oi','')))
                                        eh_lav_lej_od = st.text_input("AV lej SC OD", value=str(hrow.get('lenso_av_lej_od','')))
                                        eh_lav_lej_oi = st.text_input("AV lej SC OI", value=str(hrow.get('lenso_av_lej_oi','')))
                                        eh_rav_lej_od = st.text_input("AV lej CC OD", value=str(hrow.get('rx_av_lej_od','')))
                                        eh_rav_lej_oi = st.text_input("AV lej CC OI", value=str(hrow.get('rx_av_lej_oi','')))
                                        if st.form_submit_button("💾 Guardar Cambios", type="primary"):
                                            idx_h = st.session_state.df_historias[
                                                st.session_state.df_historias["id"].astype(str) == str(h_id)
                                            ].index
                                            if len(idx_h) > 0:
                                                i = idx_h[0]
                                                for campo, val in [
                                                    ("motivo", eh_motivo), ("diagnostico", eh_diag), ("observaciones", eh_obs),
                                                    ("lenso_od", eh_lenso_od), ("lenso_oi", eh_lenso_oi),
                                                    ("rx_od", eh_rx_od), ("rx_oi", eh_rx_oi),
                                                    ("lenso_av_lej_od", eh_lav_lej_od), ("lenso_av_lej_oi", eh_lav_lej_oi),
                                                    ("rx_av_lej_od", eh_rav_lej_od), ("rx_av_lej_oi", eh_rav_lej_oi),
                                                ]:
                                                    st.session_state.df_historias.at[i, campo] = val
                                                guardar_datos()
                                                st.session_state[f"editando_historia_{h_id}"] = False
                                                st.success("✅ Historia actualizada.")
                                                st.rerun()

                                st.markdown("**💡 Recomendaciones / Lo que se llevó el paciente:**")
                                rec_val     = hrow.get("recomendaciones", "")
                                rec_editado = st.text_area("Recomendaciones", value=str(rec_val) if rec_val else "",
                                    key=f"rec_{hrow['id']}", label_visibility="collapsed", height=80)
                                if st.button("💾 Guardar recomendación", key=f"save_rec_{hrow['id']}"):
                                    idx_h = st.session_state.df_historias[
                                        st.session_state.df_historias["id"] == hrow["id"]
                                    ].index[0]
                                    st.session_state.df_historias.at[idx_h, "recomendaciones"] = rec_editado
                                    guardar_datos()
                                    st.success("✅ Recomendación guardada.")
                                    st.rerun()

                                st.markdown("---")
                                bacc1, bacc2, bacc3 = st.columns(3)

                                with bacc1:
                                    opto_info = {
                                        "nombre":    st.session_state.opto_nombre,
                                        "cargo":     st.session_state.opto_cargo,
                                        "registro":  st.session_state.opto_registro,
                                        "direccion": st.session_state.get("opto_direccion", "Happy Vision"),
                                        "telefono":  st.session_state.get("opto_telefono", "+593 96 324 1158"),
                                    }
                                    try:
                                        pdf_bytes = generar_pdf_historia(hrow.to_dict(), pac.to_dict(), opto_info)
                                        st.download_button(
                                            label="⬇️ Descargar PDF",
                                            data=pdf_bytes,
                                            file_name=f"CertificadoVisual_{pac.get('nombre','').replace(' ','_')}_{hrow.get('fecha','')}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True,
                                            key=f"pdf_{hrow['id']}",
                                        )
                                    except Exception as e:
                                        st.error(f"Error PDF: {e}")

                                with bacc2:
                                    num_wa = str(pac.get("telefono", "")).strip()
                                    if num_wa:
                                        msg_wa = (
                                            f"Hola {pac.get('nombre','')}, adjunto encontraras tu *Certificado Visual* "
                                            f"de la consulta del {hrow.get('fecha','')}. "
                                            f"Happy Vision +593 96 324 1158"
                                        )
                                        link_wa = wa_link(num_wa, msg_wa)
                                        st.markdown(
                                            f'<a href="{link_wa}" target="_blank" style="text-decoration:none;">'
                                            f'<button style="width:100%;background:#25D366;color:white;border:none;'
                                            f'border-radius:8px;padding:8px 0;cursor:pointer;font-size:13px;font-weight:600;">'
                                            f'📲 WhatsApp (adjuntar PDF)</button></a>',
                                            unsafe_allow_html=True
                                        )
                                        st.caption("Descarga el PDF ⬆️ y adjúntalo en WhatsApp")
                                    else:
                                        st.caption("⚠️ Sin número registrado")

                                with bacc3:
                                    with st.popover("💊 Enviar Indicacion"):
                                        st.markdown("**Enviar indicación/medicación al paciente**")
                                        ind_texto = st.text_area("Indicación:", key=f"ind_{hrow['id']}", height=120,
                                            placeholder="Ej: Aplicar 1 gota de Systane Ultra cada 8 horas.")
                                        num_ind = str(pac.get("telefono", "")).strip()
                                        if st.button("📤 Enviar por WhatsApp", key=f"send_ind_{hrow['id']}"):
                                            if num_ind and ind_texto.strip():
                                                msg_ind = (
                                                    f"*👁️ Happy Vision - Indicaciones Medicas*\n\n"
                                                    f"👤 Paciente: {pac.get('nombre','')}\n"
                                                    f"📅 Fecha: {hrow.get('fecha','')}\n\n"
                                                    f"*Indicaciones:*\n{ind_texto}\n\n"
                                                    f"Conéctate: +593 96 324 1158"
                                                )
                                                link_ind = wa_link(num_ind, msg_ind)
                                                st.markdown(
                                                    f'<a href="{link_ind}" target="_blank">'
                                                    f'<button style="background:#25D366;color:white;border:none;border-radius:6px;padding:8px 16px;cursor:pointer;">✅ Abrir WhatsApp</button></a>',
                                                    unsafe_allow_html=True
                                                )
                                            elif not num_ind:
                                                st.error("⚠️ Sin número registrado.")
                                            else:
                                                st.warning("Escribe la indicación primero.")

    elif not q:
        st.info("🔍 Escribe el nombre o cédula en el buscador. Si es nuevo, usa ➕ Nuevo Paciente.")
        if len(df_p_all) > 0:
            st.markdown("<div class='section-title'>Pacientes registrados recientemente</div>", unsafe_allow_html=True)
            ultimos = df_p_all.tail(10).iloc[::-1]
            for _, rp in ultimos.iterrows():
                rc1, rc2, rc3, rc4, rc5 = st.columns([3, 2, 1, 1, 1])
                rc1.markdown(
                    f"**{rp.get('nombre','')}**  \n"
                    f"<span style='font-size:12px;color:#64748b'>🆔 {rp.get('identificacion','')} · "
                    f"{rp.get('genero','')} · {rp.get('edad','')} años · 📞 {rp.get('telefono','')}</span>",
                    unsafe_allow_html=True
                )
                with rc3:
                    if st.button("📋 Consulta", key=f"rap_cons_{rp['id']}", use_container_width=True):
                        st.session_state["nueva_consulta_paciente"] = rp.get("nombre","")
                        st.rerun()
                with rc4:
                    if st.button("✏️ Editar", key=f"rap_edit_{rp['id']}", use_container_width=True):
                        st.session_state["editar_paciente_id"] = rp["id"]
                        st.session_state["clinica_buscar"] = rp.get("nombre","")
                        st.rerun()
                with rc5:
                    if st.button("🔍 Ver", key=f"rap_ver_{rp['id']}", use_container_width=True):
                        st.session_state["clinica_buscar"] = rp.get("nombre","")
                        st.rerun()
                st.divider()

    # ── FORMULARIO DE NUEVA CONSULTA ─────────────────────────────────
    if st.session_state.get("nueva_consulta_paciente"):
        c_pac_sel = st.session_state["nueva_consulta_paciente"]
        st.markdown(f"<div class='section-title'>📝 Nueva Consulta para: <b>{c_pac_sel}</b></div>", unsafe_allow_html=True)
        with st.form("nueva_consulta_form", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            c_fecha = col_c1.date_input("📅 Fecha", value=date.today())
            col_c2.markdown(f"<p style='margin-top:28px; color:#93c5fd;'>Paciente: <b>{c_pac_sel}</b></p>", unsafe_allow_html=True)

            st.markdown("**(1) Datos de la Consulta**")
            c_motivo = st.text_input("Motivo de la consulta")

            st.markdown("**(2) Antecedentes**")
            ant_col1, ant_col2 = st.columns(2)
            c_ant_per = ant_col1.text_input("Antecedentes Personales", placeholder="Ej: Diabetes, cirugias...")
            c_ant_fam = ant_col2.text_input("Antecedentes Familiares", placeholder="Ej: Glaucoma familiar...")
            c_obs     = st.text_area("Observaciones adicionales", height=60)

            st.markdown("**(2) Agudezas Visuales**")
            ac1, ac2, ac3, ac4, ac5, ac6 = st.columns([1,2,2,1,2,2])
            ac1.markdown("<p style='margin-top:30px;'><b>S/C</b></p>", unsafe_allow_html=True)
            c_av_lej_sc_od = ac2.text_input("Lejos OD (S/C)")
            c_av_cer_sc_od = ac3.text_input("Cerca OD (S/C)")
            c_av_lej_sc_oi = ac2.text_input("Lejos OI (S/C)")
            c_av_cer_sc_oi = ac3.text_input("Cerca OI (S/C)")
            ac4.markdown("<p style='margin-top:30px;'><b>C/C</b></p>", unsafe_allow_html=True)
            c_rx_av_lej_od = ac5.text_input("Lejos OD (C/C)")
            c_rx_av_cer_od = ac6.text_input("Cerca OD (C/C)")
            c_rx_av_lej_oi = ac5.text_input("Lejos OI (C/C)")
            c_rx_av_cer_oi = ac6.text_input("Cerca OI (C/C)")

            st.markdown("**(3) LENSOMETRÍA (RX EN USO)**")
            lc1, lc2, lc3, lc4, lc5, lc6 = st.columns([1,2,2,2,2,2])
            lc1.write(" "); lc2.write("**ESF**"); lc3.write("**CYL**"); lc4.write("**EJE**"); lc5.write("**ADD**"); lc6.write(" ")
            lc1.write("**OD**")
            lo2 = lc2.text_input("LE o1", label_visibility="collapsed", placeholder="Esf")
            lo3 = lc3.text_input("LC o1", label_visibility="collapsed", placeholder="Cyl")
            lo4 = lc4.text_input("LJ o1", label_visibility="collapsed", placeholder="Eje")
            lo5 = lc5.text_input("LA o1", label_visibility="collapsed", placeholder="Add")
            lc6.write(" ")
            lc1.write("**OI**")
            li2 = lc2.text_input("LE i1", label_visibility="collapsed", placeholder="Esf")
            li3 = lc3.text_input("LC i1", label_visibility="collapsed", placeholder="Cyl")
            li4 = lc4.text_input("LJ i1", label_visibility="collapsed", placeholder="Eje")
            li5 = lc5.text_input("LA i1", label_visibility="collapsed", placeholder="Add")
            lc6.write(" ")
            c_lenso_od = f"{lo2}|{lo3}|{lo4}|{lo5}"
            c_lenso_oi = f"{li2}|{li3}|{li4}|{li5}"

            st.markdown("**(4) REFRACCIÓN (RX ACTUAL)**")
            rc1, rc2, rc3, rc4, rc5, rc6, rc7, rc8, rc9, rc10 = st.columns([1,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5])
            rc1.write(" "); rc2.write("**ESF**"); rc3.write("**CYL**"); rc4.write("**EJE**"); rc5.write("**ADD**")
            rc6.write("**DNP**"); rc7.write("**ALT**"); rc8.write("**DP**"); rc9.write("**A/V**"); rc10.write(" ")
            rc1.write("**OD**")
            ro2 = rc2.text_input("RE o1", label_visibility="collapsed", placeholder="Esf")
            ro3 = rc3.text_input("RC o1", label_visibility="collapsed", placeholder="Cyl")
            ro4 = rc4.text_input("RJ o1", label_visibility="collapsed", placeholder="Eje")
            ro5 = rc5.text_input("RA o1", label_visibility="collapsed", placeholder="Add")
            ro7 = rc6.text_input("RDP o1", label_visibility="collapsed", placeholder="DNP")
            ro8 = rc7.text_input("RAL o1", label_visibility="collapsed", placeholder="Alt")
            ro9 = rc8.text_input("RD p1",  label_visibility="collapsed", placeholder="DP")
            ro10= rc9.text_input("RAV o1", label_visibility="collapsed", placeholder="A/V")
            rc10.write(" ")
            rc1.write("**OI**")
            ri2 = rc2.text_input("RE i1", label_visibility="collapsed", placeholder="Esf")
            ri3 = rc3.text_input("RC i1", label_visibility="collapsed", placeholder="Cyl")
            ri4 = rc4.text_input("RJ i1", label_visibility="collapsed", placeholder="Eje")
            ri5 = rc5.text_input("RA i1", label_visibility="collapsed", placeholder="Add")
            ri7 = rc6.text_input("RDP i1", label_visibility="collapsed", placeholder="DNP")
            ri8 = rc7.text_input("RAL i1", label_visibility="collapsed", placeholder="Alt")
            ri9 = rc8.text_input("RD p2",  label_visibility="collapsed", placeholder="DP")
            ri10= rc9.text_input("RAV i1", label_visibility="collapsed", placeholder="A/V")
            rc10.write(" ")
            c_rx_od = f"{ro2}|{ro3}|{ro4}|{ro5}|{ro7}|{ro8}|{ro9}|{ro10}"
            c_rx_oi = f"{ri2}|{ri3}|{ri4}|{ri5}|{ri7}|{ri8}|{ri9}|{ri10}"

            st.markdown("**(5) Diagnóstico y Observaciones**")
            c_diag = st.text_input("Diagnóstico Principal", placeholder="Ej: ASTIGMATISMO MIOPICO COMPUESTO")
            dcol1, dcol2, dcol3 = st.columns(3)
            c_necesita_lentes = dcol1.radio("Paciente necesita lentes", ["SI", "NO"], horizontal=True)
            c_test_color      = dcol2.radio("Test de Color", ["Normal", "Se detecta daltonismo"], horizontal=True)
            c_meses_control   = dcol3.number_input("📅 Meses para próximo control", min_value=1, max_value=36, value=12)

            c_obs = st.text_area("Observaciones / Recomendaciones (Opcional)", placeholder="Escribe observaciones adicionales...")
            c_ant_per, c_ant_fam, c_diab, c_hiper, c_otra = "", "", "NO", "NO", ""
            c_est_mus, c_seg_ext, c_test_col, c_est_ref, c_disp, c_recom = "", "", "", "", "", ""

            fcols = st.columns([2, 1])
            if fcols[0].form_submit_button("💾 Guardar Historia Clínica", type="primary", use_container_width=True):
                p_match = st.session_state.df_pacientes[st.session_state.df_pacientes["nombre"] == c_pac_sel]
                if len(p_match) > 0:
                    p_id_match = p_match.iloc[0]["id"]
                    nueva_h = {
                        "id": len(st.session_state.df_historias) + 1,
                        "paciente_id": p_id_match, "paciente_nombre": c_pac_sel,
                        "fecha": c_fecha.strftime("%Y-%m-%d"),
                        "ant_personales": c_ant_per, "ant_familiares": c_ant_fam, "motivo": c_motivo,
                        "diabetes": c_diab, "hipertension": c_hiper, "patologia_otra": c_otra, "observaciones": c_obs,
                        "lenso_od": c_lenso_od, "lenso_av_lej_od": c_av_lej_sc_od, "lenso_av_cer_od": c_av_cer_sc_od,
                        "lenso_oi": c_lenso_oi, "lenso_av_lej_oi": c_av_lej_sc_oi, "lenso_av_cer_oi": c_av_cer_sc_oi,
                        "rx_od": c_rx_od, "rx_av_lej_od": c_rx_av_lej_od, "rx_av_cer_od": c_rx_av_cer_od,
                        "rx_oi": c_rx_oi, "rx_av_lej_oi": c_rx_av_lej_oi, "rx_av_cer_oi": c_rx_av_cer_oi,
                        "estado_muscular": c_est_mus, "seg_externo": c_seg_ext,
                        "test_colores": c_test_col, "estado_refractivo": c_est_ref,
                        "diagnostico": c_diag, "disposicion": c_disp,
                        "recomendaciones": c_recom,
                        "necesita_lentes": c_necesita_lentes,
                        "test_color": c_test_color,
                        "meses_proximo_control": int(c_meses_control),
                    }
                    st.session_state.df_historias = pd.concat(
                        [st.session_state.df_historias, pd.DataFrame([nueva_h])], ignore_index=True
                    )
                    guardar_datos()
                    st.session_state["nueva_consulta_paciente"] = None
                    st.success(f"✅ Consulta guardada para {c_pac_sel}")
                    st.rerun()
            if fcols[1].form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state["nueva_consulta_paciente"] = None
                st.rerun()
