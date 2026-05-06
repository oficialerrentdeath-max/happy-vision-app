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

    # ── TABLA ESTILO EXCEL INTERACTIVA ────────────────────────
    st.markdown("---")
    st.markdown("👆 **Haz clic en cualquier producto de la tabla para ver sus opciones (editar, stock, eliminar).**")

    # Preparar DataFrame para visualización
    df_tabla = df_f[[
        "codigo_referencia", "nombre", "categoria", "marca",
        "proveedor", "costo_compra", "precio_venta", "cantidad_disponible"
    ]].copy()
    
    df_tabla.columns = ["Código", "Producto", "Categoría", "Marca", "Proveedor", "Costo", "PVP", "Stock"]

    # Mostrar la tabla interactiva
    event = st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key="tabla_interactiva_inventario"
    )

    # Si el usuario selecciona una fila, mostramos las acciones debajo
    if event.selection.rows:
        idx_seleccionado = event.selection.rows[0]
        row = df_f.iloc[idx_seleccionado]
        stock = row.get("cantidad_disponible", 0)
        
        st.markdown(f"""
            <div style='background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-top: 10px;'>
                <h3 style='margin:0; color:#1e293b;'>🛠️ Acciones para: {row.get('nombre', '')}</h3>
                <p style='margin:0; color:#64748b;'>Código: {row.get('codigo_referencia', '')} | Stock actual: {stock}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            if st.button("➕ Aumentar Stock", use_container_width=True, type="primary"):
                guardar_producto({"id": row['id'], "cantidad_disponible": stock + 1})
                st.rerun()
                
        with c2:
            if st.button("➖ Disminuir Stock", use_container_width=True):
                if stock > 0:
                    guardar_producto({"id": row['id'], "cantidad_disponible": stock - 1})
                    st.rerun()
                    
        with c3:
            with st.popover("✏️ Editar Producto", use_container_width=True):
                with st.form(f"edit_form_{row['id']}"):
                    e_cod = st.text_input("Código", value=row.get('codigo_referencia', ''))
                    e_nom = st.text_input("Producto", value=row.get('nombre', ''))
                    
                    cat_opciones = ["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"]
                    cat_actual = row.get('categoria', 'Monturas')
                    if cat_actual not in cat_opciones: cat_actual = "Monturas"
                    e_cat = st.selectbox("Categoría", cat_opciones, index=cat_opciones.index(cat_actual))
                    
                    e_marca = st.text_input("Marca", value=row.get('marca', ''))
                    e_prov = st.text_input("Proveedor", value=row.get('proveedor', ''))
                    e_costo = st.number_input("Costo", value=float(row.get('costo_compra', 0)))
                    e_pvp = st.number_input("PVP", value=float(row.get('precio_venta', 0)))
                    
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
                        st.rerun()
                        
        with c4:
            with st.popover("🗑️ Eliminar", use_container_width=True):
                st.error("⚠️ ¿Eliminar permanentemente?")
                if st.button("Sí, Eliminar", key=f"del_{row['id']}", type="primary", use_container_width=True):
                    eliminar_producto(row['id'])
                    st.rerun()


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
