import streamlit as st
import pandas as pd
from datetime import date
from utils import wa_link, guardar_datos, generar_pdf_historia, generar_msg_indicaciones


def render_clinica():
    st.markdown("""
    <div class="page-header">
        <h1>🩺 Historias Clínicas</h1>
        <p>Registro y seguimiento de evaluaciones optométricas de cada paciente</p>
    </div>
    """, unsafe_allow_html=True)

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
            c1, c2, c3, c4 = st.columns([1, 1.5, 1.5, 1])
            p_id        = c1.text_input("Cédula/ID")
            p_nombres   = c2.text_input("Nombres *")
            p_apellidos = c3.text_input("Apellidos *")
            p_genero    = c4.selectbox("Género", ["Masculino", "Femenino", "Otro"])

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
                if p_nombres.strip() and p_apellidos.strip():
                    hoy = date.today()
                    p_edad_calc = hoy.year - p_fnac.year - ((hoy.month, hoy.day) < (p_fnac.month, p_fnac.day))
                    p_nombre_completo = f"{p_apellidos.strip()} {p_nombres.strip()}"
                    nuevo_p = {
                        "id": str(len(st.session_state.df_pacientes) + 1),
                        "identificacion": str(p_id), "nombre": p_nombre_completo,
                        "nombres": p_nombres.strip(), "apellidos": p_apellidos.strip(),
                        "genero": p_genero, "direccion": p_dir, "edad": str(p_edad_calc),
                        "fecha_nacimiento": p_fnac.strftime("%Y-%m-%d"),
                        "telefono": p_tel, "correo": p_email, "ocupacion": p_ocupa,
                    }
                    st.session_state.df_pacientes = pd.concat([st.session_state.df_pacientes, pd.DataFrame([nuevo_p])], ignore_index=True)
                    guardar_datos()
                    st.success(f"✅ Paciente **{p_nombre_completo}** registrado.")
                    st.session_state["mostrar_nuevo_p"] = False
                    st.rerun()
                else:
                    st.error("⚠️ Nombres y Apellidos son obligatorios.")

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
                            ec1, ec2, ec3, ec4 = st.columns([1, 1.5, 1.5, 1])
                            e_id  = ec1.text_input("Cédula", value=str(pac.get("identificacion", "")))
                            e_nom = ec2.text_input("Nombres", value=str(pac.get("nombres", pac.get("nombre","").split()[-1] if pac.get("nombre") else "")))
                            e_ape = ec3.text_input("Apellidos", value=str(pac.get("apellidos", pac.get("nombre","").split()[0] if pac.get("nombre") else "")))
                            e_gen = ec4.selectbox("Género", ["Masculino","Femenino","Otro"],
                                index=["Masculino","Femenino","Otro"].index(pac.get("genero","Masculino"))
                                      if pac.get("genero","Masculino") in ["Masculino","Femenino","Otro"] else 0)
                            ec5, ec6, ec7 = st.columns(3)
                            fnac_val  = pac.get("fecha_nacimiento", "")
                            default_d = date(1990,1,1)
                            if fnac_val and str(fnac_val) not in ("", "nan", "None", "NaT"):
                                try: default_d = date.fromisoformat(str(fnac_val)[:10])
                                except: pass
                            e_fnac = ec5.date_input("Fecha de Nacimiento", value=default_d, min_value=date(1900,1,1), max_value=date.today())
                            e_tel  = ec6.text_input("Teléfono", value=str(pac.get("telefono", "")))
                            e_mail = ec7.text_input("Correo",   value=str(pac.get("correo", "")))
                            ec8, ec9 = st.columns(2)
                            e_dir = ec8.text_input("Dirección", value=str(pac.get("direccion", "")))
                            e_ocu = ec9.text_input("Ocupación", value=str(pac.get("ocupacion", "")))
                            if st.form_submit_button("💾 Actualizar", type="primary"):
                                idx_p = st.session_state.df_pacientes[st.session_state.df_pacientes["id"] == pac["id"]].index[0]
                                hoy   = date.today()
                                new_edad = hoy.year - e_fnac.year - ((hoy.month, hoy.day) < (e_fnac.month, e_fnac.day))
                                nombre_nuevo = f"{e_ape.strip()} {e_nom.strip()}"
                                st.session_state.df_pacientes.at[idx_p, "identificacion"]   = str(e_id)
                                st.session_state.df_pacientes.at[idx_p, "nombre"]           = nombre_nuevo
                                st.session_state.df_pacientes.at[idx_p, "nombres"]          = e_nom.strip()
                                st.session_state.df_pacientes.at[idx_p, "apellidos"]        = e_ape.strip()
                                st.session_state.df_pacientes.at[idx_p, "genero"]           = str(e_gen)
                                st.session_state.df_pacientes.at[idx_p, "fecha_nacimiento"] = e_fnac.strftime("%Y-%m-%d")
                                st.session_state.df_pacientes.at[idx_p, "edad"]             = str(new_edad)
                                st.session_state.df_pacientes.at[idx_p, "telefono"]         = str(e_tel)
                                st.session_state.df_pacientes.at[idx_p, "correo"]           = str(e_mail)
                                st.session_state.df_pacientes.at[idx_p, "direccion"]        = str(e_dir)
                                st.session_state.df_pacientes.at[idx_p, "ocupacion"]        = e_ocu
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
                                    _def = hrow.to_dict()
                                    with st.form(key=f"edit_h_form_{h_id}"):
                                        st.markdown("**Editar Consulta Completa**")
                                        eh_col1, eh_col2 = st.columns(2)
                                        eh_fecha  = eh_col1.date_input("Fecha", value=date.fromisoformat(str(_def.get('fecha', str(date.today())))[:10]))
                                        eh_motivo = eh_col2.text_input("Motivo de la consulta", value=str(_def.get('motivo','')))

                                        st.markdown("**(2) Antecedentes**")
                                        ea1, ea2 = st.columns(2)
                                        eh_ant_per = ea1.text_input("Antecedentes Personales", value=str(_def.get('ant_personales','')))
                                        eh_ant_fam = ea2.text_input("Antecedentes Familiares", value=str(_def.get('ant_familiares','')))

                                        st.markdown("**(3) Agudezas Visuales S/C y C/C)**")
                                        eav1,eav2,eav3,eav4,eav5,eav6 = st.columns([1,2,2,1,2,2])
                                        eav1.markdown("<p style='margin-top:28px;'><b>S/C</b></p>", unsafe_allow_html=True)
                                        eh_av_lej_sc_od = eav2.text_input("Lejos OD S/C", value=str(_def.get('lenso_av_lej_od','')))
                                        eh_av_cer_sc_od = eav3.text_input("Cerca OD S/C", value=str(_def.get('lenso_av_cer_od','')))
                                        eh_av_lej_sc_oi = eav2.text_input("Lejos OI S/C", value=str(_def.get('lenso_av_lej_oi','')))
                                        eh_av_cer_sc_oi = eav3.text_input("Cerca OI S/C", value=str(_def.get('lenso_av_cer_oi','')))
                                        eav4.markdown("<p style='margin-top:28px;'><b>C/C</b></p>", unsafe_allow_html=True)
                                        eh_rx_av_lej_od = eav5.text_input("Lejos OD C/C", value=str(_def.get('rx_av_lej_od','')))
                                        eh_rx_av_cer_od = eav6.text_input("Cerca OD C/C", value=str(_def.get('rx_av_cer_od','')))
                                        eh_rx_av_lej_oi = eav5.text_input("Lejos OI C/C", value=str(_def.get('rx_av_lej_oi','')))
                                        eh_rx_av_cer_oi = eav6.text_input("Cerca OI C/C", value=str(_def.get('rx_av_cer_oi','')))

                                        # Parse lenso existente
                                        def _p(s, i):
                                            pts = str(s).split("|") if s else []
                                            return pts[i].strip() if i < len(pts) else ""

                                        st.markdown("**(4) Lensometria (Rx en uso)**")
                                        el1,el2,el3,el4,el5 = st.columns([1,2,2,2,2])
                                        el1.write(" "); el2.write("**ESF**"); el3.write("**CYL**"); el4.write("**EJE**"); el5.write("**ADD**")
                                        el1.write("**OD**")
                                        elo2 = el2.text_input("LE o1e", label_visibility="collapsed", value=_p(_def.get('lenso_od'),0), placeholder="Esf")
                                        elo3 = el3.text_input("LC o1e", label_visibility="collapsed", value=_p(_def.get('lenso_od'),1), placeholder="Cyl")
                                        elo4 = el4.text_input("LJ o1e", label_visibility="collapsed", value=_p(_def.get('lenso_od'),2), placeholder="Eje")
                                        elo5 = el5.text_input("LA o1e", label_visibility="collapsed", value=_p(_def.get('lenso_od'),3), placeholder="Add")
                                        el1.write("**OI**")
                                        eli2 = el2.text_input("LE i1e", label_visibility="collapsed", value=_p(_def.get('lenso_oi'),0), placeholder="Esf")
                                        eli3 = el3.text_input("LC i1e", label_visibility="collapsed", value=_p(_def.get('lenso_oi'),1), placeholder="Cyl")
                                        eli4 = el4.text_input("LJ i1e", label_visibility="collapsed", value=_p(_def.get('lenso_oi'),2), placeholder="Eje")
                                        eli5 = el5.text_input("LA i1e", label_visibility="collapsed", value=_p(_def.get('lenso_oi'),3), placeholder="Add")

                                        st.markdown("**(5) Refraccion (Rx actual)**")
                                        er1,er2,er3,er4,er5,er6,er7,er8,er9 = st.columns([1,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5])
                                        er1.write(" "); er2.write("**ESF**"); er3.write("**CYL**"); er4.write("**EJE**"); er5.write("**ADD**")
                                        er6.write("**DNP**"); er7.write("**ALT**"); er8.write("**DP**"); er9.write("**A/V**")
                                        er1.write("**OD**")
                                        ero2 = er2.text_input("RE o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),0), placeholder="Esf")
                                        ero3 = er3.text_input("RC o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),1), placeholder="Cyl")
                                        ero4 = er4.text_input("RJ o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),2), placeholder="Eje")
                                        ero5 = er5.text_input("RA o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),3), placeholder="Add")
                                        ero6 = er6.text_input("RDP o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),4), placeholder="DNP")
                                        ero7 = er7.text_input("RAL o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),5), placeholder="Alt")
                                        ero8 = er8.text_input("RDp1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),6), placeholder="DP")
                                        ero9 = er9.text_input("RAV o1e", label_visibility="collapsed", value=_p(_def.get('rx_od'),7), placeholder="A/V")
                                        er1.write("**OI**")
                                        eri2 = er2.text_input("RE i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),0), placeholder="Esf")
                                        eri3 = er3.text_input("RC i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),1), placeholder="Cyl")
                                        eri4 = er4.text_input("RJ i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),2), placeholder="Eje")
                                        eri5 = er5.text_input("RA i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),3), placeholder="Add")
                                        eri6 = er6.text_input("RDP i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),4), placeholder="DNP")
                                        eri7 = er7.text_input("RAL i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),5), placeholder="Alt")
                                        eri8 = er8.text_input("RDp2e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),6), placeholder="DP")
                                        eri9 = er9.text_input("RAV i1e", label_visibility="collapsed", value=_p(_def.get('rx_oi'),7), placeholder="A/V")

                                        st.markdown("**(6) Diagnostico**")
                                        CIE10_OPCIONES_E = [
                                            "H52.1 Miopia", "H52.0 Hipermetropia", "H52.2 Astigmatismo",
                                            "H52.3 Anisometropia", "H52.4 Presbicia", "H52.6 Otros defectos refractivos",
                                            "H40.0 Hipertension ocular", "H40.1 Glaucoma primario angulo abierto",
                                            "H40.2 Glaucoma primario angulo cerrado",
                                            "H26.9 Catarata", "H26.0 Catarata infantil", "H26.1 Catarata traumatica",
                                            "H35.3 Degeneracion macular", "H35.0 Retinopatia de fondo",
                                            "H50.0 Estrabismo convergente", "H50.1 Estrabismo divergente",
                                            "H50.4 Heteroforia", "H55.0 Nistagmo",
                                            "H04.1 Ojo seco (Sindrome de ojo seco)", "H04.0 Dacrioadenitis",
                                            "H10.9 Conjuntivitis", "H10.1 Conjuntivitis atopica",
                                            "H16.9 Queratitis", "H16.0 Ulcera corneal", "H18.0 Pigmentacion corneal",
                                            "H57.1 Dolor ocular", "H57.0 Anomalias pupilares",
                                            "H02.4 Ptosis palpebral", "H02.0 Entropion",
                                            "H25.0 Catarata senil incipiente", "H25.9 Catarata senil",
                                            "H33.0 Desprendimiento de retina", "H34.0 Oclusion arteria retiniana",
                                            "H30.9 Coriorretinitis", "H20.0 Iridociclitis",
                                            "Z01.0 Examen visual de rutina", "Z96.1 Lentes intraoculares",
                                        ]
                                        curr_diag = str(_def.get('diagnostico',''))
                                        _presel = [c for c in CIE10_OPCIONES_E if c in curr_diag]
                                        _curr_libre = curr_diag
                                        for _c in _presel:
                                            _curr_libre = _curr_libre.replace(_c, "").replace("|", "").strip()
                                        
                                        eh_diag_cie_multi = st.multiselect(
                                            "Buscador CIE-10 (Busca y selecciona para agregar)",
                                            options=CIE10_OPCIONES_E,
                                            default=_presel,
                                            key=f"cie_e_in_{h_id}"
                                        )
                                        eh_diag_libre = st.text_input("Detalle adicional", value=_curr_libre, key=f"dl_e_{h_id}")

                                        ed1, ed2, ed3 = st.columns(3)
                                        lentes_opts = ["SI","NO"]
                                        lentes_curr = str(_def.get('necesita_lentes','NO'))
                                        lentes_idx  = 0 if lentes_curr == "SI" else 1
                                        eh_necesita_lentes = ed1.radio("Necesita lentes", lentes_opts, index=lentes_idx, horizontal=True, key=f"nl_e_{h_id}")
                                        color_opts = ["Normal", "Se detecta daltonismo"]
                                        color_curr = str(_def.get('test_color','Normal'))
                                        color_idx = 1 if "dalton" in color_curr.lower() else 0
                                        eh_test_color = ed2.radio("Test de Color", color_opts, index=color_idx, horizontal=True, key=f"tc_e_{h_id}")
                                        def _safe_meses(v, default=12):
                                            try:
                                                return max(1, min(36, int(float(str(v)))))
                                            except Exception:
                                                return default
                                        # Proximo control como fecha
                                        from datetime import timedelta as _td2
                                        _curr_ctrl = str(_def.get('meses_proximo_control', ''))
                                        try:
                                            _ctrl_date = date.fromisoformat(_curr_ctrl[:10])
                                        except Exception:
                                            _meses_n = _safe_meses(_curr_ctrl)
                                            _ctrl_date = date.today() + _td2(days=_meses_n * 30)
                                        eh_proximo_control = ed3.date_input("Proximo control", value=_ctrl_date, key=f"pc_e_{h_id}")

                                        eh_obs = st.text_area("Observaciones / Recomendaciones", value=str(_def.get('observaciones','')), key=f"obs_e_{h_id}")
                                        eh_recom = st.text_area("Recomendaciones (Indicaciones al paciente)", value=str(_def.get('recomendaciones','')), key=f"rec_e_{h_id}")

                                        if st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True):
                                            eh_diag = " | ".join(eh_diag_cie_multi)
                                            if eh_diag_libre.strip():
                                                eh_diag = (eh_diag + " " + eh_diag_libre.strip()).strip()

                                            idx_h = st.session_state.df_historias[
                                                st.session_state.df_historias["id"].astype(str) == str(h_id)
                                            ].index
                                            if len(idx_h) > 0:
                                                i = idx_h[0]
                                                updates = {
                                                    "fecha": eh_fecha.strftime("%Y-%m-%d"),
                                                    "motivo": eh_motivo,
                                                    "ant_personales": eh_ant_per, "ant_familiares": eh_ant_fam,
                                                    "lenso_av_lej_od": eh_av_lej_sc_od, "lenso_av_cer_od": eh_av_cer_sc_od,
                                                    "lenso_av_lej_oi": eh_av_lej_sc_oi, "lenso_av_cer_oi": eh_av_cer_sc_oi,
                                                    "rx_av_lej_od": eh_rx_av_lej_od, "rx_av_cer_od": eh_rx_av_cer_od,
                                                    "rx_av_lej_oi": eh_rx_av_lej_oi, "rx_av_cer_oi": eh_rx_av_cer_oi,
                                                    "lenso_od": f"{elo2}|{elo3}|{elo4}|{elo5}",
                                                    "lenso_oi": f"{eli2}|{eli3}|{eli4}|{eli5}",
                                                    "rx_od": f"{ero2}|{ero3}|{ero4}|{ero5}|{ero6}|{ero7}|{ero8}|{ero9}",
                                                    "rx_oi": f"{eri2}|{eri3}|{eri4}|{eri5}|{eri6}|{eri7}|{eri8}|{eri9}",
                                                    "diagnostico": eh_diag,
                                                    "necesita_lentes": eh_necesita_lentes,
                                                    "test_color": eh_test_color,
                                                    "meses_proximo_control": eh_proximo_control.strftime("%Y-%m-%d"),
                                                    "observaciones": eh_obs,
                                                    "recomendaciones": eh_recom,
                                                }
                                                for campo, val in updates.items():
                                                    st.session_state.df_historias.at[i, campo] = val
                                                guardar_datos()
                                                st.session_state[f"editando_historia_{h_id}"] = False
                                                st.success("Historia actualizada.")
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
                                    # Opto info desde el usuario logueado
                                    import json as _json
                                    import base64 as _b64
                                    _ulogin = st.session_state.get("user_login", "")
                                    _usuarios_data = {}
                                    try:
                                        with open("usuarios.json", "r", encoding="utf-8") as _f:
                                            _usuarios_data = _json.load(_f)
                                    except Exception:
                                        pass
                                    # Fallback global desde optometrista.json
                                    _os = __import__("os")
                                    _global_opto = {}
                                    if _os.path.exists("optometrista.json"):
                                        try:
                                            with open("optometrista.json", "r", encoding="utf-8") as _f:
                                                _global_opto = _json.load(_f)
                                        except Exception: pass

                                    _ud = _usuarios_data.get(_ulogin, {})
                                    opto_info = {
                                        "username": _ulogin,
                                        "nombre":   _ud.get("nombre") or st.session_state.get("user_name") or _global_opto.get("opto_nombre", ""),
                                        "cargo":    _ud.get("cargo") or st.session_state.get("user_cargo") or _global_opto.get("opto_cargo", "Optometrista"),
                                        "registro": _ud.get("registro") or st.session_state.get("user_registro") or _global_opto.get("opto_registro", ""),
                                        "telefono": _ud.get("telefono") or st.session_state.get("user_telefono") or _global_opto.get("opto_telefono", ""),
                                    }
                                    try:
                                        pdf_bytes = generar_pdf_historia(hrow.to_dict(), pac.to_dict(), opto_info)
                                        # Vista Previa del certificado
                                        with st.expander("Vista Previa del Certificado", expanded=False):
                                            _b64str = _b64.b64encode(pdf_bytes).decode("utf-8")
                                            st.markdown(
                                                f'<iframe src="data:application/pdf;base64,{_b64str}" '
                                                f'width="100%" height="500px" style="border:none;"></iframe>',
                                                unsafe_allow_html=True
                                            )
                                            st.download_button(
                                                label="Descargar PDF",
                                                data=pdf_bytes,
                                                file_name=f"CertificadoVisual_{pac.get('nombre','').replace(' ','_')}_{hrow.get('fecha','')}.pdf",
                                                mime="application/pdf",
                                                use_container_width=True,
                                                key=f"pdf_dl_{hrow['id']}",
                                            )
                                        st.download_button(
                                            label="Descargar PDF",
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
            st.markdown("<div class='section-title'>Todos los Pacientes (orden alfabético)</div>", unsafe_allow_html=True)
            # Orden alfabético por apellidos; si no existe columna apellidos, usar nombre
            if "apellidos" in df_p_all.columns:
                df_ord = df_p_all.sort_values(
                    by=["apellidos", "nombres"], key=lambda c: c.str.upper().str.strip(), ascending=True
                )
            else:
                df_ord = df_p_all.sort_values(
                    by="nombre", key=lambda c: c.str.upper().str.strip(), ascending=True
                )
            for _, rp in df_ord.iterrows():
                # Contar historial del paciente
                n_hist = len(st.session_state.df_historias[
                    st.session_state.df_historias["paciente_id"].astype(str) == str(rp["id"])
                ])
                hc_badge = f"<span style='background:#1e40af;color:#bfdbfe;border-radius:4px;padding:2px 7px;font-size:11px;margin-right:6px;'>HC: {n_hist}</span>"
                rc1, rc2, rc3, rc4, rc5 = st.columns([3, 2, 1, 1, 1])
                rc1.markdown(
                    f"{hc_badge}**{rp.get('nombre','')}**  \n"
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
        st.markdown(f"<div class='section-title'>Nueva Consulta para: <b>{c_pac_sel}</b></div>", unsafe_allow_html=True)

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

            def _sugerir_cie10(esf_od, esf_oi, cyl_od, cyl_oi, add_od):
                sugs = []
                def _n(v):
                    try: return float(str(v).replace(",","."))
                    except: return 0.0
                if _n(esf_od) < -0.25 or _n(esf_oi) < -0.25: sugs.append("H52.1 Miopia")
                if _n(esf_od) > 0.25 or _n(esf_oi) > 0.25: sugs.append("H52.0 Hipermetropia")
                if abs(_n(cyl_od)) > 0.25 or abs(_n(cyl_oi)) > 0.25: sugs.append("H52.2 Astigmatismo")
                if _n(add_od) > 0.5: sugs.append("H52.4 Presbicia")
                if abs(_n(esf_od) - _n(esf_oi)) > 1.0: sugs.append("H52.3 Anisometropia")
                return sugs
            
            sugeridos = _sugerir_cie10(ro2, ri2, ro3, ri3, ro5)
            if sugeridos:
                st.caption(f"💡 Sugerencias por Rx: {', '.join(sugeridos)}")

            CIE10_OPCIONES = [
                "H52.1 Miopia", "H52.0 Hipermetropia", "H52.2 Astigmatismo",
                "H52.3 Anisometropia", "H52.4 Presbicia", "H52.6 Otros defectos refractivos",
                "H40.0 Hipertension ocular", "H40.1 Glaucoma primario angulo abierto",
                "H40.2 Glaucoma primario angulo cerrado",
                "H26.9 Catarata", "H26.0 Catarata infantil", "H26.1 Catarata traumatica",
                "H35.3 Degeneracion macular", "H35.0 Retinopatia de fondo",
                "H50.0 Estrabismo convergente", "H50.1 Estrabismo divergente",
                "H50.4 Heteroforia", "H55.0 Nistagmo",
                "H04.1 Ojo seco (Sindrome de ojo seco)", "H04.0 Dacrioadenitis",
                "H10.9 Conjuntivitis", "H10.1 Conjuntivitis atopica",
                "H16.9 Queratitis", "H16.0 Ulcera corneal", "H18.0 Pigmentacion corneal",
                "H57.1 Dolor ocular", "H57.0 Anomalias pupilares",
                "H02.4 Ptosis palpebral", "H02.0 Entropion",
                "H25.0 Catarata senil incipiente", "H25.9 Catarata senil",
                "H33.0 Desprendimiento de retina", "H34.0 Oclusion arteria retiniana",
                "H30.9 Coriorretinitis", "H20.0 Iridociclitis",
                "Z01.0 Examen visual de rutina", "Z96.1 Lentes intraoculares",
            ]
            c_diag_cie_multi = st.multiselect(
                "Buscador CIE-10 (Busca y selecciona los codigos a agregar)",
                options=CIE10_OPCIONES,
                placeholder="Escribe o selecciona..."
            )
            c_diag_libre = st.text_input("Detalle adicional / complemento", placeholder="Ej: OU, ambos ojos, bilateral")

            dcol1, dcol2, dcol3 = st.columns(3)
            c_necesita_lentes  = dcol1.radio("Paciente necesita lentes", ["SI", "NO"], horizontal=True)
            c_test_color       = dcol2.radio("Test de Color", ["Normal", "Se detecta daltonismo"], horizontal=True)
            from datetime import timedelta as _td
            c_proximo_control  = dcol3.date_input("Proximo control", value=date.today() + _td(days=365))

            c_obs = st.text_area("Observaciones / Recomendaciones (Opcional)", placeholder="Escribe observaciones adicionales...")
            c_ant_per, c_ant_fam, c_diab, c_hiper, c_otra = "", "", "NO", "NO", ""
            c_est_mus, c_seg_ext, c_test_col, c_est_ref, c_disp, c_recom = "", "", "", "", "", ""

            fcols = st.columns([2, 1])
            if fcols[0].form_submit_button("💾 Guardar Historia Clínica", type="primary", use_container_width=True):
                c_diag = " | ".join(c_diag_cie_multi)
                if c_diag_libre.strip():
                    c_diag = (c_diag + " " + c_diag_libre.strip()).strip()

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
                        "diagnostico": c_diag,
                        "recomendaciones": c_recom,
                        "necesita_lentes": c_necesita_lentes,
                        "test_color": c_test_color,
                        "meses_proximo_control": c_proximo_control.strftime("%Y-%m-%d"),
                    }
                    st.session_state.df_historias = pd.concat(
                        [st.session_state.df_historias, pd.DataFrame([nueva_h])], ignore_index=True
                    )
                    guardar_datos()
                    st.session_state["nueva_consulta_paciente"] = None
                    st.success(f"Consulta guardada para {c_pac_sel}")
                    st.rerun()
            if fcols[1].form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state["nueva_consulta_paciente"] = None
                st.rerun()
