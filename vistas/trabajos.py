import streamlit as st
import pandas as pd
from datetime import date
from utils import wa_link, guardar_datos, generar_msg_factura


def render_trabajos():
    st.markdown("""
    <div class="page-header">
        <h1>📋 Ingreso de Trabajos</h1>
        <p>Registra ventas, servicios ópticos y realiza seguimiento de cobros</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Nuevo Registro", "📄 Historial y Filtros"])

    # ── FORMULARIO NUEVO TRABAJO ───────────────────────────────
    with tab1:
        with st.form("form_trabajo", clear_on_submit=True):
            st.markdown("<div class='section-title'>👤 Datos del Paciente y Servicio</div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                fecha = st.date_input("📅 Fecha del Trabajo", value=date.today())
            with col2:
                paciente = st.text_input("👤 Nombre Completo del Paciente", placeholder="Ej: María García López")
            with col3:
                tipo_lente = st.selectbox("🔬 Tipo de Lente", [
                    "Monofocal", "Progresivo", "Progresivo Premium", "Filtro Azul", "Contactología"
                ])

            col4, col5 = st.columns(2)
            with col4:
                laboratorio = st.selectbox("🏭 Laboratorio Proveedor", [
                    "Indulentes", "Pecsa/ImportVision", "Stock propio"
                ])
            with col5:
                observaciones = st.text_input("📝 Observaciones (opcional)", placeholder="Prescripción especial, urgente, etc.")

            st.markdown("<div class='section-title'>💰 Información de Pago</div>", unsafe_allow_html=True)
            col6, col7, col8 = st.columns(3)
            with col6:
                precio_total = st.number_input("💵 Precio Total al Paciente ($)", min_value=0.0, step=5.0, format="%.2f")
            with col7:
                abono = st.number_input("💳 Abono Inicial ($)", min_value=0.0, step=5.0, format="%.2f")
            with col8:
                metodo_pago = st.selectbox("🏦 Método de Pago", [
                    "Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia"
                ])

            saldo_calc  = max(0.0, precio_total - abono)
            estado_calc = "Pagado" if saldo_calc < 1 else ("Parcial" if abono > 0 else "Pendiente")

            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.info(f"**💵 Total:** ${precio_total:,.2f}")
            with col_res2:
                st.info(f"**✅ Abono:** ${abono:,.2f}")
            with col_res3:
                if saldo_calc < 1:
                    st.success(f"**✅ Saldo Pendiente:** $0.00 — Pagado")
                elif saldo_calc < precio_total * 0.5:
                    st.warning(f"**⚠️ Saldo Pendiente:** ${saldo_calc:,.2f}")
                else:
                    st.error(f"**🔴 Saldo Pendiente:** ${saldo_calc:,.2f}")

            submitted = st.form_submit_button("✅ Guardar Trabajo", use_container_width=True, type="primary")

            if submitted:
                if not paciente.strip():
                    st.error("⚠️ Ingresa el nombre del paciente.")
                elif precio_total <= 0:
                    st.error("⚠️ El precio total debe ser mayor a $0.")
                elif abono > precio_total:
                    st.error("⚠️ El abono no puede superar el precio total.")
                else:
                    # Calcular nuevo ID de trabajo de forma segura
                    df_t_current = st.session_state.df_trabajos
                    if not df_t_current.empty and "id" in df_t_current.columns:
                        max_t_id = pd.to_numeric(df_t_current["id"], errors="coerce").max()
                        nuevo_t_id = int(max_t_id + 1) if pd.notna(max_t_id) else 1
                    else:
                        nuevo_t_id = 1

                    new_row = {
                        "id":              nuevo_t_id,
                        "fecha":           fecha.strftime("%Y-%m-%d"),
                        "paciente":        paciente.strip(),
                        "tipo_lente":      tipo_lente,
                        "laboratorio":     laboratorio,
                        "precio_total":    precio_total,
                        "abono":           abono,
                        "metodo_pago":     metodo_pago,
                        "saldo_pendiente": saldo_calc,
                        "estado":          estado_calc,
                    }
                    st.session_state.df_trabajos = pd.concat([
                        st.session_state.df_trabajos, pd.DataFrame([new_row])
                    ], ignore_index=True)
                    st.success(f"✅ Trabajo registrado exitosamente para **{paciente}** — Estado: **{estado_calc}**")
                    st.balloons()

    # ── HISTORIAL ─────────────────────────────────────────────
    with tab2:
        df_hist = st.session_state.df_trabajos.copy()

        st.markdown("<div class='section-title'>🔍 Filtros</div>", unsafe_allow_html=True)
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            f_estado = st.multiselect("Estado", ["Pagado","Parcial","Pendiente"], default=["Pagado","Parcial","Pendiente"])
        with cf2:
            f_tipo = st.multiselect("Tipo de Lente", sorted(df_hist["tipo_lente"].unique()), default=sorted(df_hist["tipo_lente"].unique()))
        with cf3:
            f_lab = st.multiselect("Laboratorio", sorted(df_hist["laboratorio"].unique()), default=sorted(df_hist["laboratorio"].unique()))
        with cf4:
            f_metodo = st.multiselect("Método Pago", sorted(df_hist["metodo_pago"].unique()), default=sorted(df_hist["metodo_pago"].unique()))

        df_filtered = df_hist[
            df_hist["estado"].isin(f_estado) &
            df_hist["tipo_lente"].isin(f_tipo) &
            df_hist["laboratorio"].isin(f_lab) &
            df_hist["metodo_pago"].isin(f_metodo)
        ].sort_values("fecha", ascending=False)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Registros",    len(df_filtered))
        m2.metric("Ingreso Total", f"${df_filtered['precio_total'].sum():,.0f}")
        m3.metric("Cobrado",       f"${df_filtered['abono'].sum():,.0f}")
        m4.metric("Por Cobrar",    f"${df_filtered['saldo_pendiente'].sum():,.0f}")

        st.dataframe(
            df_filtered[["fecha","paciente","tipo_lente","laboratorio","precio_total","abono","saldo_pendiente","metodo_pago","estado"]].rename(columns={
                "fecha":"Fecha","paciente":"Paciente","tipo_lente":"Tipo Lente",
                "laboratorio":"Laboratorio","precio_total":"Total $","abono":"Abono $",
                "saldo_pendiente":"Saldo $","metodo_pago":"Método Pago","estado":"Estado",
            }),
            use_container_width=True, hide_index=True,
        )

        # ── BOTONES WHATSAPP POR REGISTRO ──
        st.markdown("<div class='section-title' style='margin-top:24px;'>💬 Enviar Factura por WhatsApp</div>", unsafe_allow_html=True)
        st.caption("Selecciona un trabajo para enviar el detalle al paciente.")

        for _, row_t in df_filtered.head(20).iterrows():
            p_info_match = st.session_state.df_pacientes[
                st.session_state.df_pacientes["nombre"].str.lower() == str(row_t.get("paciente", "")).lower()
            ]
            tiene_tel = len(p_info_match) > 0 and str(p_info_match.iloc[0].get("telefono", "")).strip() != ""
            col_r, col_wa = st.columns([5, 1])
            with col_r:
                est   = row_t.get('estado', '')
                color = '#22c55e' if est == 'Pagado' else ('#f59e0b' if est == 'Parcial' else '#ef4444')
                st.markdown(
                    f"<div style='padding:6px 12px; background:#1e293b; border-radius:8px; border-left:3px solid {color};'>"
                    f"<b>{row_t.get('fecha','')} — {row_t.get('paciente','')}</b> · {row_t.get('tipo_lente','')} · "
                    f"<span style='color:{color};'>{est}</span> · ${row_t.get('precio_total',0):.2f}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_wa:
                if tiene_tel:
                    num  = str(p_info_match.iloc[0]["telefono"])
                    link = wa_link(num, generar_msg_factura(row_t))
                    st.markdown(f"""<a href="{link}" target="_blank">
                        <button style='background:#25D366; color:white; border:none; border-radius:6px;
                        padding:6px 14px; cursor:pointer; font-size:14px; width:100%;'>
                        💬 WhatsApp</button></a>""", unsafe_allow_html=True)
                else:
                    st.caption("Sin número")
