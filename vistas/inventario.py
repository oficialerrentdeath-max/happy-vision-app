import streamlit as st
import plotly.graph_objects as go


def render_inventario():
    st.markdown("""
    <div class="page-header">
        <h1>📦 Control de Inventario</h1>
        <p>Gestión de armazones, plaquetas y líquidos · Alertas de reabastecimiento en tiempo real</p>
    </div>
    """, unsafe_allow_html=True)

    df_inv       = st.session_state.df_inventario.copy()
    bajo_stock_df = df_inv[df_inv["stock"] < df_inv["stock_min"]]
    limite_df     = df_inv[(df_inv["stock"] >= df_inv["stock_min"]) & (df_inv["stock"] <= df_inv["stock_min"] * 1.25)]

    if len(bajo_stock_df) > 0:
        st.error(f"⚠️ **ALERTA:** {len(bajo_stock_df)} producto(s) por debajo del stock mínimo.")
    if len(limite_df) > 0:
        st.warning(f"⚡ {len(limite_df)} producto(s) próximos a alcanzar el stock mínimo.")
    if len(bajo_stock_df) == 0 and len(limite_df) == 0:
        st.success("✅ Todo el inventario está en niveles óptimos.")

    tab_i1, tab_i2, tab_i3 = st.tabs(["📊 Vista General", "🔄 Registrar Movimiento", "🚨 Panel de Alertas"])

    def stock_status(row):
        if row["stock"] < row["stock_min"]:
            return "🔴 Bajo Mínimo"
        elif row["stock"] <= row["stock_min"] * 1.25:
            return "🟡 Límite"
        else:
            return "🟢 OK"

    # ── VISTA GENERAL ───────────────────────────────────────────
    with tab_i1:
        ci1, ci2 = st.columns([2, 6])
        with ci1:
            cat_sel = st.selectbox("Filtrar categoría", ["Todas"] + sorted(df_inv["categoria"].unique().tolist()))

        df_show = df_inv if cat_sel == "Todas" else df_inv[df_inv["categoria"] == cat_sel]
        df_show = df_show.copy()
        df_show["Estado"]        = df_show.apply(stock_status, axis=1)
        df_show["Disponibilidad"] = (df_show["stock"] / df_show["stock_min"] * 100).round(0).astype(int).astype(str) + "%"

        ki1, ki2, ki3, ki4 = st.columns(4)
        ki1.metric("Total Productos",    len(df_inv))
        ki2.metric("🔴 Bajo Mínimo",     len(bajo_stock_df))
        ki3.metric("🟡 En Límite",       len(limite_df))
        ki4.metric("Valor Inventario",   f"${(df_inv['stock'] * df_inv['costo']).sum():,.0f}")

        st.dataframe(
            df_show[["categoria","subcategoria","producto","stock","stock_min","Disponibilidad","unidad","costo","precio","Estado"]].rename(columns={
                "categoria":"Categoría","subcategoria":"Subcategoría","producto":"Producto",
                "stock":"Stock Actual","stock_min":"Mínimo","unidad":"Unidad","costo":"Costo $","precio":"Precio $",
            }),
            use_container_width=True, hide_index=True,
        )

        st.markdown("<div class='section-title'>📊 Niveles de Stock vs. Mínimo</div>", unsafe_allow_html=True)
        df_chart = df_show.sort_values("stock")
        colors   = df_chart["Estado"].map({"🔴 Bajo Mínimo":"#ef4444","🟡 Límite":"#f59e0b","🟢 OK":"#22c55e"})

        fig_stock = go.Figure()
        fig_stock.add_trace(go.Bar(
            y=df_chart["producto"], x=df_chart["stock"], name="Stock Actual", orientation="h",
            marker_color=list(colors),
            text=df_chart["stock"].astype(str) + " " + df_chart["unidad"], textposition="inside",
        ))
        fig_stock.add_trace(go.Scatter(
            y=df_chart["producto"], x=df_chart["stock_min"], mode="markers", name="Stock Mínimo",
            marker=dict(symbol="line-ew", size=18, color="#f8fafc", line=dict(color="#f8fafc",width=2)),
        ))
        fig_stock.update_layout(
            template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=10,b=0), height=max(350, len(df_chart)*26),
            legend=dict(orientation="h", y=1.05),
            xaxis=dict(gridcolor="#1e293b", title="Unidades"), yaxis=dict(gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_stock, use_container_width=True)

    # ── MOVIMIENTO DE STOCK ────────────────────────────────────
    with tab_i2:
        st.markdown("<div class='section-title'>🔄 Registrar Entrada o Salida</div>", unsafe_allow_html=True)

        with st.form("form_movimiento", clear_on_submit=False):
            cm1, cm2 = st.columns(2)
            with cm1:
                cat_mov = st.selectbox("Categoría", sorted(df_inv["categoria"].unique()))
            with cm2:
                prods_cat = df_inv[df_inv["categoria"] == cat_mov]["producto"].tolist()
                prod_sel  = st.selectbox("Producto", prods_cat)

            prod_row = df_inv[df_inv["producto"] == prod_sel].iloc[0]
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("Stock Actual",  f"{prod_row['stock']} {prod_row['unidad']}")
            pm2.metric("Stock Mínimo",  f"{prod_row['stock_min']} {prod_row['unidad']}")
            pm3.metric("Estado",        stock_status(prod_row))

            cm3, cm4 = st.columns(2)
            with cm3:
                tipo_mov = st.radio("Tipo de Movimiento", ["📥 Entrada (Compra/Reposición)", "📤 Salida (Venta/Uso)"], horizontal=True)
            with cm4:
                cantidad_mov = st.number_input("Cantidad", min_value=1, step=1, value=1)

            nota_mov    = st.text_input("Nota del movimiento (opcional)", placeholder="Proveedor, motivo, etc.")
            nueva_cant  = prod_row["stock"] + cantidad_mov if "Entrada" in tipo_mov else prod_row["stock"] - cantidad_mov

            if "Salida" in tipo_mov and cantidad_mov > prod_row["stock"]:
                st.error(f"❌ Stock insuficiente. Solo hay {prod_row['stock']} {prod_row['unidad']} disponibles.")
            else:
                st.info(f"**Vista previa:** Stock actual **{prod_row['stock']}** → **{max(0, nueva_cant)}** {prod_row['unidad']}")

            mov_ok = st.form_submit_button("📝 Confirmar Movimiento", use_container_width=True, type="primary")
            if mov_ok:
                idx  = st.session_state.df_inventario[st.session_state.df_inventario["producto"] == prod_sel].index[0]
                curr = st.session_state.df_inventario.at[idx, "stock"]
                if "Entrada" in tipo_mov:
                    st.session_state.df_inventario.at[idx, "stock"] = curr + cantidad_mov
                    st.success(f"✅ Entrada de **{cantidad_mov} {prod_row['unidad']}** para **{prod_sel}**. Nuevo stock: {curr + cantidad_mov}")
                else:
                    if cantidad_mov > curr:
                        st.error(f"❌ Stock insuficiente: {curr} {prod_row['unidad']} disponibles.")
                    else:
                        st.session_state.df_inventario.at[idx, "stock"] = curr - cantidad_mov
                        st.success(f"✅ Salida de **{cantidad_mov} {prod_row['unidad']}** para **{prod_sel}**. Nuevo stock: {curr - cantidad_mov}")
                st.rerun()

    # ── PANEL DE ALERTAS ──────────────────────────────────────
    with tab_i3:
        st.markdown("<div class='section-title'>🔴 Productos Bajo Stock Mínimo — Reabastecimiento Urgente</div>", unsafe_allow_html=True)

        df_inv_live = st.session_state.df_inventario.copy()
        bajo_live   = df_inv_live[df_inv_live["stock"] < df_inv_live["stock_min"]]
        limite_live = df_inv_live[(df_inv_live["stock"] >= df_inv_live["stock_min"]) & (df_inv_live["stock"] <= df_inv_live["stock_min"] * 1.25)]

        if len(bajo_live) == 0:
            st.markdown("<div class='alert-ok'><span class='alert-text'>✅ Sin productos bajo el mínimo.</span></div>", unsafe_allow_html=True)
        else:
            for _, row in bajo_live.iterrows():
                deficit    = row["stock_min"] - row["stock"]
                costo_repo = deficit * row["costo"]
                st.markdown(f"""
                <div class='alert-critical'>
                    <span class='alert-text'>🔴 <strong>{row['producto']}</strong> &nbsp;·&nbsp; {row['categoria']} / {row['subcategoria']}</span>
                    <div class='alert-sub'>
                        Stock actual: <strong>{row['stock']}</strong> {row['unidad']} &nbsp;|&nbsp;
                        Mínimo: <strong>{row['stock_min']}</strong> {row['unidad']} &nbsp;|&nbsp;
                        Déficit: <strong style='color:#fca5a5'>{deficit} {row['unidad']}</strong> &nbsp;|&nbsp;
                        Costo reposición: <strong style='color:#fca5a5'>${costo_repo:.2f}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if len(limite_live) > 0:
            st.markdown("<div class='section-title' style='margin-top:24px;'>🟡 Productos en Nivel de Alerta</div>", unsafe_allow_html=True)
            for _, row in limite_live.iterrows():
                st.markdown(f"""
                <div class='alert-warning'>
                    <span class='alert-text'>🟡 <strong>{row['producto']}</strong> &nbsp;·&nbsp; {row['categoria']} / {row['subcategoria']}</span>
                    <div class='alert-sub'>Stock actual: <strong>{row['stock']}</strong> {row['unidad']} &nbsp;|&nbsp; Mínimo: <strong>{row['stock_min']}</strong> {row['unidad']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div class='section-title' style='margin-top:28px;'>🟢 Estado Completo del Inventario</div>", unsafe_allow_html=True)
        for _, row in df_inv_live.iterrows():
            pct = (row["stock"] / row["stock_min"] * 100) if row["stock_min"] > 0 else 100
            if row["stock"] < row["stock_min"]:
                cls, icon = "alert-critical", "🔴"
            elif row["stock"] <= row["stock_min"] * 1.25:
                cls, icon = "alert-warning", "🟡"
            else:
                cls, icon = "alert-ok", "🟢"
            st.markdown(f"""
            <div class='{cls}' style='display:flex; justify-content:space-between; align-items:center;'>
                <span class='alert-text'>{icon} <strong>{row['producto']}</strong> <span style='color:#64748b; font-size:11px;'>({row['categoria']})</span></span>
                <span class='alert-text' style='font-size:0.85rem;'>{row['stock']} / {row['stock_min']} {row['unidad']} &nbsp; ({min(pct,999):.0f}%)</span>
            </div>
            """, unsafe_allow_html=True)
