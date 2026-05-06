import streamlit as st
import pandas as pd
from database import cargar_inventario, guardar_producto, eliminar_producto


def render_inventario():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>📦 Control de Inventario</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Gestión de monturas y productos</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")
    
    # CSS Refinado: Compacto y Profesional (Estilo Excel)
    st.markdown("""
        <style>
        .cell-content {
            font-size: 13px;
            padding: 8px 0;
            display: flex;
            align-items: center;
            min-height: 38px;
            color: #334155;
        }
        .code-btn {
            padding: 8px 0;
            display: flex;
            align-items: center;
            min-height: 38px;
        }
        .code-btn div[data-testid="stButton"] > button {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
            color: #2563eb !important;
            font-size: 13px !important;
            font-weight: bold !important;
            text-decoration: underline !important;
            box-shadow: none !important;
            min-height: 0 !important;
        }
        hr { margin: 5px 0 !important; opacity: 0.1; }
        </style>
    """, unsafe_allow_html=True)

    # ── TABLA PRINCIPAL ────────────────────────────────────────
    df = cargar_inventario(sucursal_activa)

    if df.empty:
        st.info("📭 No hay productos registrados.")
        # Formulario para agregar el primero
        with st.expander("➕ Agregar Primer Producto", expanded=True):
            with st.form("new_first"):
                c1, c2 = st.columns(2); n_cod = c1.text_input("Código"); n_mar = c2.text_input("Marca")
                if st.form_submit_button("Guardar"):
                    guardar_producto({"codigo_referencia": n_cod, "marca": n_mar, "sucursal": sucursal_activa}); st.rerun()
        return

    # Normalización de columnas
    for col, default in [("nombre", ""), ("categoria", ""), ("proveedor", ""),
                         ("costo_compra", 0.0), ("precio_venta", 0.0),
                         ("cantidad_disponible", 0), ("codigo_referencia", "")]:
        if col not in df.columns:
            df[col] = default

    # Buscador y Filtros
    f1, f2 = st.columns([3, 1])
    busq = f1.text_input("🔍 Buscar por código, marca o producto...", label_visibility="collapsed")
    f_cat = f2.selectbox("Categoría", ["Todas"] + sorted(df["categoria"].unique().tolist()), label_visibility="collapsed")

    df_f = df.copy()
    if busq:
        df_f = df_f[df_f.apply(lambda r: busq.lower() in str(r).lower(), axis=1)]
    if f_cat != "Todas":
        df_f = df_f[df_f["categoria"] == f_cat]

    st.markdown("---")
    
    # ── ENCABEZADOS ────────────────────────────────────────────
    # Ratios: Código(1.2), Producto(3.2), Cat(1.2), Marca(1.2), Prov(1.8), Costo(0.9), PVP(0.9), Stock(0.9)
    cols_ratio = [1.2, 3.2, 1.2, 1.2, 1.8, 0.9, 0.9, 0.9]
    h = st.columns(cols_ratio)
    labels = ["CÓDIGO", "PRODUCTO", "CATEGORÍA", "MARCA", "PROVEEDOR", "COSTO", "PVP", "STOCK"]
    for i, label in enumerate(labels):
        h[i].markdown(f"<p style='font-size:14px; font-weight:bold; color:#1e293b; margin:0;'>{label}</p>", unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # ── FILAS DE DATOS ─────────────────────────────────────────
    for _, row in df_f.iterrows():
        cols = st.columns(cols_ratio)
        
        # Código Interactuable
        with cols[0]:
            st.markdown('<div class="code-btn">', unsafe_allow_html=True)
            if st.button(row.get('codigo_referencia') or "---", key=f"c_{row['id']}"):
                st.session_state.inv_exp = row['id'] if st.session_state.get("inv_exp") != row['id'] else None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        def draw(val, idx, bold=False, color=None, is_money=False):
            style = f"font-weight:bold;" if bold else ""
            if color: style += f"color:{color};"
            display = f"${float(val):.2f}" if is_money else str(val)
            with cols[idx]:
                st.markdown(f'<div class="cell-content" style="{style}">{display}</div>', unsafe_allow_html=True)

        draw(row.get('nombre', ''), 1, bold=True)
        draw(row.get('categoria', ''), 2)
        draw(row.get('marca', ''), 3)
        draw(row.get('proveedor', ''), 4)
        draw(row.get('costo_compra', 0), 5, is_money=True)
        draw(row.get('precio_venta', 0), 6, is_money=True, color="#2563eb", bold=True)
        
        stock = int(row.get('cantidad_disponible', 0))
        draw(stock, 7, bold=True, color="red" if stock <= 3 else "green")

        # Acciones Expandidas
        if st.session_state.get("inv_exp") == row['id']:
            with st.container():
                st.markdown(f"<div style='background:#f1f5f9; border-radius:4px; padding:10px; margin:5px 0;'>", unsafe_allow_html=True)
                a1, a2, a3, a4 = st.columns(4)
                if a1.button("➕ Stock", key=f"p_{row['id']}", use_container_width=True):
                    guardar_producto({"id": row['id'], "cantidad_disponible": stock+1}); st.rerun()
                if a2.button("➖ Stock", key=f"m_{row['id']}", use_container_width=True):
                    if stock > 0: guardar_producto({"id": row['id'], "cantidad_disponible": stock-1}); st.rerun()
                if a3.button("✏️ Editar", key=f"e_{row['id']}", use_container_width=True):
                    st.session_state[f"ed_{row['id']}"] = not st.session_state.get(f"ed_{row['id']}", False)
                if a4.button("🗑️ Borrar", key=f"d_{row['id']}", use_container_width=True):
                    eliminar_producto(row['id']); st.rerun()
                
                if st.session_state.get(f"ed_{row['id']}"):
                    with st.form(f"f_{row['id']}"):
                        e1, e2, e3 = st.columns(3)
                        n_c = e1.number_input("Costo", value=float(row.get('cost_compra', row.get('costo_compra', 0))))
                        n_p = e2.number_input("PVP", value=float(row.get('precio_venta', 0)))
                        n_n = e3.text_input("Nombre", value=row.get('nombre', ''))
                        if st.form_submit_button("Guardar"):
                            guardar_producto({"id": row['id'], "costo_compra": n_c, "precio_venta": n_p, "nombre": n_n})
                            st.session_state[f"ed_{row['id']}"] = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)


    # Alerta de stock bajo
    try:
        if not df.empty:
            stock_num = pd.to_numeric(df["cantidad_disponible"], errors='coerce').fillna(0)
            bajo_stock = df[stock_num <= 3]
            if not bajo_stock.empty:
                codigos = [str(x) for x in bajo_stock["codigo_referencia"].tolist() if pd.notna(x) and str(x).strip()]
                codigos_str = ", ".join(codigos) if codigos else "Varios productos sin código"
                st.warning(f"⚠️ **{len(bajo_stock)} producto(s) con stock ≤ 3:** {codigos_str}")
    except Exception as e:
        import traceback
        st.error(f"Error calculando stock bajo: {str(e)}")
        st.error(traceback.format_exc())
