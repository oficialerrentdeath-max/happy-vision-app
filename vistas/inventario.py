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
    
    # CSS para que los botones de las celdas parezcan texto normal y la fila sea "cliqueable"
    st.markdown("""
        <style>
        .grid-cell button {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
            color: inherit !important;
            text-align: left !important;
            font-size: 13px !important;
            box-shadow: none !important;
            width: 100% !important;
            display: block !important;
            height: auto !important;
            min-height: 0 !important;
        }
        .grid-cell button:hover {
            color: #2563eb !important;
            background: #f1f5f9 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ── FORMULARIO AGREGAR ─────────────────────────────────────
    with st.expander("➕ Agregar Nueva Montura / Producto", expanded=False):
        with st.form("nuevo_producto_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n_cod      = c1.text_input("Código", placeholder="Ej: RX-5154")
            n_producto = c2.text_input("Producto", placeholder="Ej: Aviator Clásico")
            n_cat      = c3.selectbox("Categoría", ["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"])

            c4, c5, c6 = st.columns(3)
            n_marca    = c4.text_input("Marca", placeholder="Ej: Ray-Ban")
            n_color    = c5.text_input("Color / Modelo", placeholder="Ej: Negro Mate")
            n_prov     = c6.text_input("Proveedor", placeholder="Ej: Distribuidora XYZ")

            c7, c8, c9 = st.columns(3)
            n_costo    = c7.number_input("Costo Compra Unit ($)", min_value=0.0, format="%.2f")
            n_venta    = c8.number_input("Precio al Paciente ($)", min_value=0.0, format="%.2f")
            n_stock    = c9.number_input("Stock", min_value=0, value=0)

            if st.form_submit_button("💾 Guardar", use_container_width=True, type="primary"):
                if n_cod and n_marca:
                    guardar_producto({
                        "codigo_referencia": n_cod,
                        "nombre":            n_producto,
                        "categoria":         n_cat,
                        "marca":             n_marca,
                        "modelo_color":      n_color,
                        "proveedor":         n_prov,
                        "costo_compra":      n_costo,
                        "precio_venta":      n_venta,
                        "cantidad_disponible": n_stock,
                        "sucursal":          sucursal_activa
                    })
                    st.success("✅ Producto agregado exitosamente.")
                    st.rerun()
                else:
                    st.error("⚠️ Código y Marca son obligatorios.")

    # ── TABLA PRINCIPAL ────────────────────────────────────────
    df = cargar_inventario(sucursal_activa)

    if df.empty:
        st.info("📭 No hay productos registrados. Agrega el primero con el formulario de arriba.")
        return

    # Normalizar columnas al nuevo esquema
    col_map = {
        "codigo_referencia":  "codigo_referencia",
        "nombre":             "nombre",
        "categoria":          "categoria",
        "marca":              "marca",
        "proveedor":          "proveedor",
        "costo_compra":       "costo_compra",
        "precio_venta":       "precio_venta",
        "cantidad_disponible":"cantidad_disponible",
    }
    for col, default in [("nombre", ""), ("categoria", ""), ("proveedor", ""),
                         ("costo_compra", 0.0), ("precio_venta", 0.0),
                         ("cantidad_disponible", 0), ("codigo_referencia", "")]:
        if col not in df.columns:
            df[col] = default

    # Filtros rápidos
    fil1, fil2, fil3 = st.columns([2, 1, 1])
    busq = fil1.text_input("🔍 Buscar", placeholder="Código, marca, producto...")
    cats = ["Todos"] + sorted(df["categoria"].dropna().unique().tolist())
    filtro_cat = fil2.selectbox("Categoría", cats)
    st.markdown(f"**{len(df)} productos** en {sucursal_activa}")

    df_f = df.copy()
    if busq:
        mask = (
            df_f["codigo_referencia"].astype(str).str.contains(busq, case=False, na=False) |
            df_f["nombre"].astype(str).str.contains(busq, case=False, na=False) |
            df_f["marca"].astype(str).str.contains(busq, case=False, na=False)
        )
        df_f = df_f[mask]
    if filtro_cat != "Todos":
        df_f = df_f[df_f["categoria"] == filtro_cat]

    # ── TABLA ESTILO EXCEL CON ACCIONES ────────────────────────
    st.markdown("---")
    
    # Definir proporciones de columnas (ajustadas sin la columna Acciones)
    cols_ratio = [1.5, 3.5, 1.5, 1.5, 2, 1, 1, 1]
    
    # Encabezado de la tabla
    header_cols = st.columns(cols_ratio)
    header_cols[0].markdown("**Código**")
    header_cols[1].markdown("**Producto**")
    header_cols[2].markdown("**Categoría**")
    header_cols[3].markdown("**Marca**")
    header_cols[4].markdown("**Proveedor**")
    header_cols[5].markdown("**Costo**")
    header_cols[6].markdown("**PVP**")
    header_cols[7].markdown("**Stock**")
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)
    
    # Filas de datos
    for _, row in df_f.iterrows():
        cols = st.columns(cols_ratio)
        
        # Color de stock
        stock = row.get('cantidad_disponible', 0)
        color_stock = "red" if stock <= 3 else "green"
        
        # Cada celda es ahora un botón invisible que activa la expansión de la fila
        def grid_button(label, key, column_idx):
            with cols[column_idx]:
                st.markdown('<div class="grid-cell">', unsafe_allow_html=True)
                if st.button(label, key=key):
                    if st.session_state.get("inventario_expanded") == row['id']:
                        st.session_state.inventario_expanded = None
                    else:
                        st.session_state.inventario_expanded = row['id']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        grid_button(str(row.get('codigo_referencia', '')), f"btn_cod_{row['id']}", 0)
        grid_button(str(row.get('nombre', '')), f"btn_nom_{row['id']}", 1)
        grid_button(str(row.get('categoria', '')), f"btn_cat_{row['id']}", 2)
        grid_button(str(row.get('marca', '')), f"btn_mar_{row['id']}", 3)
        grid_button(str(row.get('proveedor', '')), f"btn_pro_{row['id']}", 4)
        grid_button(f"${float(row.get('costo_compra', 0)):.2f}", f"btn_cos_{row['id']}", 5)
        grid_button(f"${float(row.get('precio_venta', 0)):.2f}", f"btn_pvp_{row['id']}", 6)
        grid_button(str(stock), f"btn_stk_{row['id']}", 7)
                
        # Opciones expandidas
        if st.session_state.get("inventario_expanded") == row['id']:
            with st.container():
                st.markdown(f"""
                    <div style='background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 10px; margin-top: 5px;'>
                        <h4 style='margin:0; color:#1e293b;'>🛠️ Acciones para: {row.get('nombre', '')}</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button("➕ Aumentar Stock", key=f"add_{row['id']}", use_container_width=True, type="primary"):
                        guardar_producto({"id": row['id'], "cantidad_disponible": stock + 1})
                        st.rerun()
                with c2:
                    if st.button("➖ Disminuir Stock", key=f"sub_{row['id']}", use_container_width=True):
                        if stock > 0:
                            guardar_producto({"id": row['id'], "cantidad_disponible": stock - 1})
                            st.rerun()
                with c3:
                    if st.button("✏️ Editar Detalles", use_container_width=True):
                        st.session_state[f"edit_mode_{row['id']}"] = not st.session_state.get(f"edit_mode_{row['id']}", False)
                
                with c4:
                    with st.popover("🗑️ Eliminar", use_container_width=True):
                        st.error("⚠️ ¿Eliminar permanentemente?")
                        if st.button("Sí, Eliminar", key=f"del_{row['id']}", type="primary", use_container_width=True):
                            eliminar_producto(row['id'])
                            st.session_state.inventario_expanded = None
                            st.rerun()

                # Formulario de edición que se despliega HACIA ABAJO (sin popover)
                if st.session_state.get(f"edit_mode_{row['id']}"):
                    st.markdown("---")
                    with st.form(f"edit_form_{row['id']}"):
                        st.write("**📝 Editar Información del Producto**")
                        e1, e2, e3 = st.columns(3)
                        e_cod = e1.text_input("Código", value=row.get('codigo_referencia', ''))
                        e_nom = e2.text_input("Producto", value=row.get('nombre', ''))
                        
                        cat_opciones = ["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"]
                        cat_actual = row.get('categoria', 'Monturas')
                        if cat_actual not in cat_opciones: cat_actual = "Monturas"
                        e_cat = e3.selectbox("Categoría", cat_opciones, index=cat_opciones.index(cat_actual))
                        
                        e4, e5, e6 = st.columns(3)
                        e_marca = e4.text_input("Marca", value=row.get('marca', ''))
                        e_prov = e5.text_input("Proveedor", value=row.get('proveedor', ''))
                        e_costo = e6.number_input("Costo", value=float(row.get('costo_compra', 0)))
                        
                        e7, e8 = st.columns(2)
                        e_pvp = e7.number_input("PVP", value=float(row.get('precio_venta', 0)))
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            guardar_producto({
                                "id": row['id'],
                                "codigo_referencia": e_cod,
                                "nombre": e_nom,
                                "categoria": e_cat,
                                "marca": e_marca,
                                "proveedor": e_prov,
                                "costo_compra": e_costo,
                                "precio_venta": e_pvp
                            })
                            st.session_state[f"edit_mode_{row['id']}"] = False
                            st.rerun()
                            
        st.markdown("<hr style='margin: 0; padding: 0; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)


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
