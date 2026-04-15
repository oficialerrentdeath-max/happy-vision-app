import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def render_dashboard():
    st.markdown("""
    <div class="page-header">
        <h1>📊 Dashboard Financiero</h1>
        <p>Análisis de rentabilidad, utilidad neta y flujo de caja · Happy Vision</p>
    </div>
    """, unsafe_allow_html=True)

    df_t = st.session_state.df_trabajos.copy()
    df_g = st.session_state.df_gastos.copy()

    df_t["fecha_dt"] = pd.to_datetime(df_t["fecha"])
    df_t["mes"]      = df_t["fecha_dt"].dt.to_period("M").astype(str)

    meses_disp = sorted(df_t["mes"].unique().tolist(), reverse=True)

    col_f1, col_f2 = st.columns([2, 6])
    with col_f1:
        mes_sel = st.selectbox("📅 Período de análisis", ["Todos los períodos"] + meses_disp, key="dash_mes")

    if mes_sel != "Todos los períodos":
        df_m  = df_t[df_t["mes"] == mes_sel].copy()
        df_gm = df_g[df_g["fecha"] == mes_sel].copy()
    else:
        df_m  = df_t.copy()
        df_gm = df_g.copy()

    costo_pct = {"Indulentes": 0.35, "Pecsa/ImportVision": 0.40, "Stock propio": 0.20}
    df_m["costo_lab"] = df_m.apply(
        lambda r: r["precio_total"] * costo_pct.get(r["laboratorio"], 0.35), axis=1
    )

    ingreso_bruto   = df_m["precio_total"].sum()
    abonos_recibidos = df_m["abono"].sum()
    saldo_total     = df_m["saldo_pendiente"].sum()
    costo_labs      = df_m["costo_lab"].sum()
    gastos_op       = df_gm["monto"].sum()
    utilidad_neta   = ingreso_bruto - costo_labs - gastos_op
    margen          = (utilidad_neta / ingreso_bruto * 100) if ingreso_bruto > 0 else 0
    ticket_promedio = ingreso_bruto / len(df_m) if len(df_m) > 0 else 0

    # ── KPI CARDS ──────────────────────────────────────────────
    st.markdown("<div class='section-title'>💰 Indicadores Clave del Período</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-icon">💵</div><div class="kpi-value">${ingreso_bruto:,.0f}</div><div class="kpi-label">Ingreso Bruto</div></div>
        <div class="kpi-card"><div class="kpi-icon">✅</div><div class="kpi-value-green">${abonos_recibidos:,.0f}</div><div class="kpi-label">Total Cobrado</div></div>
        <div class="kpi-card"><div class="kpi-icon">⏳</div><div class="kpi-value-red">${saldo_total:,.0f}</div><div class="kpi-label">Por Cobrar</div></div>
        <div class="kpi-card"><div class="kpi-icon">🏭</div><div class="kpi-value-red">${costo_labs:,.0f}</div><div class="kpi-label">Costo Laboratorios</div></div>
        <div class="kpi-card"><div class="kpi-icon">🏢</div><div class="kpi-value-red">${gastos_op:,.0f}</div><div class="kpi-label">Gastos Operativos</div></div>
        <div class="kpi-card"><div class="kpi-icon">📈</div><div class="kpi-value-green">${utilidad_neta:,.0f}</div><div class="kpi-label">Utilidad Neta</div></div>
        <div class="kpi-card"><div class="kpi-icon">🎯</div><div class="kpi-value">{margen:.1f}%</div><div class="kpi-label">Margen Real</div></div>
        <div class="kpi-card"><div class="kpi-icon">🧾</div><div class="kpi-value">${ticket_promedio:,.0f}</div><div class="kpi-label">Ticket Promedio</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── GRÁFICOS ROW 1 ─────────────────────────────────────────
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("<div class='section-title'>📈 Evolución de Ingresos Mensuales</div>", unsafe_allow_html=True)
        df_monthly = df_t.groupby("mes").agg(
            ingreso=("precio_total","sum"), cobrado=("abono","sum"), trabajos=("id","count"),
        ).reset_index().sort_values("mes")
        df_monthly["costo"]    = df_monthly["ingreso"] * 0.37
        df_monthly["utilidad"] = df_monthly["ingreso"] - df_monthly["costo"]

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_monthly["mes"], y=df_monthly["ingreso"],
            mode="lines+markers", name="Ingreso Bruto", line=dict(color="#38bdf8", width=3),
            marker=dict(size=8), fill="tozeroy", fillcolor="rgba(56,189,248,0.07)"))
        fig_line.add_trace(go.Scatter(x=df_monthly["mes"], y=df_monthly["cobrado"],
            mode="lines+markers", name="Cobrado Real", line=dict(color="#22c55e", width=2, dash="dot"), marker=dict(size=7)))
        fig_line.add_trace(go.Scatter(x=df_monthly["mes"], y=df_monthly["utilidad"],
            mode="lines+markers", name="Utilidad Est.", line=dict(color="#a78bfa", width=2, dash="dash"), marker=dict(size=7)))
        fig_line.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.12, font=dict(size=11)), margin=dict(l=0,r=0,t=10,b=0), height=300,
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))
        st.plotly_chart(fig_line, use_container_width=True)

    with col_g2:
        st.markdown("<div class='section-title'>🍩 Distribución de Ingresos por Tipo de Lente</div>", unsafe_allow_html=True)
        df_tipo = df_m.groupby("tipo_lente")["precio_total"].sum().reset_index()
        fig_pie = px.pie(df_tipo, values="precio_total", names="tipo_lente", hole=0.55,
            color_discrete_sequence=["#3b82f6","#06b6d4","#8b5cf6","#ec4899","#f59e0b"])
        fig_pie.update_traces(textinfo="label+percent", textfont_size=12)
        fig_pie.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), showlegend=False, height=300,
            annotations=[dict(text=f"${ingreso_bruto:,.0f}", x=0.5, y=0.5, font_size=15, showarrow=False, font_color="#e2e8f0")])
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── GRÁFICOS ROW 2 ─────────────────────────────────────────
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.markdown("<div class='section-title'>🏭 Ingreso vs. Costo por Laboratorio</div>", unsafe_allow_html=True)
        df_lab = df_m.groupby("laboratorio").agg(ingreso=("precio_total","sum"), costo=("costo_lab","sum")).reset_index()
        df_lab["margen"] = df_lab["ingreso"] - df_lab["costo"]
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Ingreso", x=df_lab["laboratorio"], y=df_lab["ingreso"], marker_color="#3b82f6",
            text=df_lab["ingreso"].apply(lambda v: f"${v:,.0f}"), textposition="outside"))
        fig_bar.add_trace(go.Bar(name="Costo Lab", x=df_lab["laboratorio"], y=df_lab["costo"], marker_color="#ef4444",
            text=df_lab["costo"].apply(lambda v: f"${v:,.0f}"), textposition="outside"))
        fig_bar.add_trace(go.Bar(name="Margen", x=df_lab["laboratorio"], y=df_lab["margen"], marker_color="#22c55e",
            text=df_lab["margen"].apply(lambda v: f"${v:,.0f}"), textposition="outside"))
        fig_bar.update_layout(barmode="group", template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), height=300, legend=dict(orientation="h", y=1.12, font=dict(size=11)),
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g4:
        st.markdown("<div class='section-title'>💸 Desglose de la Utilidad Neta</div>", unsafe_allow_html=True)
        fig_w = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute","relative","relative","total"],
            x=["Ingreso Bruto", "− Costo Labs", "− Gastos Op.", "= Utilidad Neta"],
            y=[ingreso_bruto, -costo_labs, -gastos_op, None],
            connector=dict(line=dict(color="#334155", width=1)),
            decreasing=dict(marker_color="#ef4444"),
            increasing=dict(marker_color="#22c55e"),
            totals=dict(marker_color="#22c55e"),
            text=[f"${ingreso_bruto:,.0f}", f"-${costo_labs:,.0f}", f"-${gastos_op:,.0f}", f"${utilidad_neta:,.0f}"],
            textposition="outside",
        ))
        fig_w.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False,
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))
        st.plotly_chart(fig_w, use_container_width=True)

    # ── TABLAS INFERIORES ─────────────────────────────────────
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("<div class='section-title'>⏳ Saldos Pendientes por Cobrar</div>", unsafe_allow_html=True)
        df_pend = df_m[df_m["saldo_pendiente"] > 1].sort_values("saldo_pendiente", ascending=False).head(10)
        if len(df_pend) > 0:
            st.dataframe(df_pend[["fecha","paciente","tipo_lente","precio_total","abono","saldo_pendiente"]].rename(columns={
                "fecha":"Fecha","paciente":"Paciente","tipo_lente":"Tipo",
                "precio_total":"Total $","abono":"Abonado $","saldo_pendiente":"Saldo $",
            }), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Sin saldos pendientes en este período.")

    with col_t2:
        st.markdown("<div class='section-title'>📋 Gastos Operativos del Período</div>", unsafe_allow_html=True)
        if len(df_gm) > 0:
            df_gm_show = df_gm.groupby("concepto").agg(monto=("monto","sum")).reset_index().sort_values("monto", ascending=False)
            st.dataframe(df_gm_show.rename(columns={"concepto":"Concepto","monto":"Monto $"}),
                use_container_width=True, hide_index=True)
        else:
            st.info("Sin gastos registrados para este período.")
