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
        /* Ajuste solo para elementos en el área principal */
        [data-testid="stMain"] .cell-content {
            font-size: 14px;
            display: flex;
            align-items: center;
            height: 38px;
            color: #334155;
            margin: 0 !important;
        }
        
        /* Botones estilo CAJA (Código y Acciones) */
        [data-testid="stMain"] div[data-testid="stButton"] > button {
            border: 1px solid #e2e8f0 !important;
            background: white !important;
            padding: 4px 12px !important;
            color: #1e293b !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            height: 34px !important;
            transition: all 0.2s ease;
        }
        [data-testid="stMain"] div[data-testid="stButton"] > button:hover {
            border-color: #3b82f6 !important;
            color: #3b82f6 !important;
            background: #f8fafc !important;
        }

        /* Contenedor de edición */
        .edit-container {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        hr { 
            margin: 0 !important; 
            opacity: 0.1; 
            border: 0;
            border-top: 1px solid #1e293b;
        }
        </style>
    """, unsafe_allow_html=True)

    # ── TABLA PRINCIPAL ────────────────────────────────────────
    df = cargar_inventario(sucursal_activa)

    if df.empty:
        st.info("📭 No hay productos registrados.")
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

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── ENCABEZADOS ────────────────────────────────────────────
    cols_ratio = [1.2, 3.2, 1.2, 1.2, 1.8, 0.9, 0.9, 0.9]
    h = st.columns(cols_ratio)
    labels = ["CÓDIGO", "PRODUCTO", "CATEGORÍA", "MARCA", "PROVEEDOR", "COSTO", "PVP", "STOCK"]
    for i, label in enumerate(labels):
        h[i].markdown(f"<p style='font-size:15px; font-weight:800; color:#64748b; margin:0;'>{label}</p>", unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # ── FILAS DE DATOS ─────────────────────────────────────────
    for _, row in df_f.iterrows():
        cols = st.columns(cols_ratio)
        
        # 1. Código (Botón en Caja)
        with cols[0]:
            if st.button(row.get('codigo_referencia') or "---", key=f"c_{row['id']}"):
                st.session_state.inv_exp = row['id'] if st.session_state.get("inv_exp") != row['id'] else None
                st.rerun()

        def draw(val, idx, bold=False, color=None, is_money=False):
            style = f"font-weight:700;" if bold else ""
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
        draw(stock, 7, bold=True, color="#ef4444" if stock <= 3 else "#22c55e")

        # Acciones Expandidas (Limpieza de espacios)
        if st.session_state.get("inv_exp") == row['id']:
            st.markdown('<div style="margin-top: 10px;">', unsafe_allow_html=True)
            a1, a2, a3, a4 = st.columns([1.2, 1.2, 1.2, 1.2])
            
            if a1.button("➕ Stock", key=f"p_{row['id']}", use_container_width=True):
                guardar_producto({"id": row['id'], "cantidad_disponible": stock+1}); st.rerun()
            if a2.button("➖ Stock", key=f"m_{row['id']}", use_container_width=True):
                if stock > 0: guardar_producto({"id": row['id'], "cantidad_disponible": stock-1}); st.rerun()
            if a3.button("✏️ Editar", key=f"e_{row['id']}", use_container_width=True):
                st.session_state[f"ed_{row['id']}"] = not st.session_state.get(f"ed_{row['id']}", False)
                st.rerun()
            if a4.button("🗑️ Borrar", key=f"d_{row['id']}", use_container_width=True):
                eliminar_producto(row['id']); st.rerun()
            
            # Formulario de Edición Completo
            if st.session_state.get(f"ed_{row['id']}"):
                st.markdown('<div class="edit-container">', unsafe_allow_html=True)
                with st.form(f"f_{row['id']}", border=False):
                    # Fila 1: Datos de Identificación
                    c1, c2, c3 = st.columns([1, 1, 1])
                    n_cod = c1.text_input("Código", value=row.get('codigo_referencia', ''))
                    n_cat = c2.text_input("Categoría", value=row.get('categoria', ''))
                    n_mar = c3.text_input("Marca", value=row.get('marca', ''))
                    
                    # Fila 2: Detalles del Producto
                    c4, c5 = st.columns([2, 1])
                    n_nom = c4.text_input("Nombre / Producto", value=row.get('nombre', ''))
                    n_pro = c5.text_input("Proveedor", value=row.get('proveedor', ''))
                    
                    # Fila 3: Precios
                    c6, c7 = st.columns([1, 1])
                    n_cos = c6.number_input("Costo Compra ($)", value=float(row.get('costo_compra', 0)), step=0.01)
                    n_pvp = c7.number_input("PVP ($)", value=float(row.get('precio_venta', 0)), step=0.01)
                    
                    if st.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        guardar_producto({
                            "id": row['id'], 
                            "codigo_referencia": n_cod,
                            "categoria": n_cat,
                            "marca": n_mar,
                            "nombre": n_nom,
                            "proveedor": n_pro,
                            "costo_compra": n_cos, 
                            "precio_venta": n_pvp
                        })
                        st.session_state[f"ed_{row['id']}"] = False
                        st.success("Producto actualizado")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
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
