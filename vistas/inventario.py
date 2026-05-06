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

    # ── TABLA ESTILO EXCEL CON ACCIONES ────────────────────────
    st.markdown("---")
    
    # Definir proporciones de columnas
    cols_ratio = [1.2, 2.5, 1.5, 1.5, 1.5, 1, 1, 1, 2]
    
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
    header_cols[8].markdown("**Acciones**")
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)
    
    # Filas de datos
    for _, row in df_f.iterrows():
        cols = st.columns(cols_ratio)
        
        # Color de stock
        stock = row.get('cantidad_disponible', 0)
        color_stock = "red" if stock <= 3 else "green"
        
        cols[0].markdown(f"<span style='font-size:13px;'>{row.get('codigo_referencia', '')}</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span style='font-size:13px; font-weight:bold; color:#1e293b;'>{row.get('nombre', '')}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span style='font-size:13px;'>{row.get('categoria', '')}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"<span style='font-size:13px;'>{row.get('marca', '')}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span style='font-size:13px;'>{row.get('proveedor', '')}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span style='font-size:13px;'>${float(row.get('costo_compra', 0)):.2f}</span>", unsafe_allow_html=True)
        cols[6].markdown(f"<span style='font-size:13px; color:#2563eb; font-weight:bold;'>${float(row.get('precio_venta', 0)):.2f}</span>", unsafe_allow_html=True)
        cols[7].markdown(f"<span style='font-size:14px; font-weight:bold; color:{color_stock};'>{stock}</span>", unsafe_allow_html=True)
        
        # Acciones
        with cols[8]:
            btn1, btn2, btn3, btn4 = st.columns(4)
            with btn1:
                if st.button("➕", key=f"add_{row['id']}", help="Aumentar Stock"):
                    guardar_producto({"id": row['id'], "cantidad_disponible": stock + 1})
                    st.rerun()
            with btn2:
                if st.button("➖", key=f"sub_{row['id']}", help="Disminuir Stock"):
                    if stock > 0:
                        guardar_producto({"id": row['id'], "cantidad_disponible": stock - 1})
                        st.rerun()
            with btn3:
                with st.popover("✏️"):
                    with st.form(f"edit_form_{row['id']}"):
                        st.write("**Editar Producto**")
                        e_cod = st.text_input("Código", value=row.get('codigo_referencia', ''))
                        e_nom = st.text_input("Producto", value=row.get('nombre', ''))
                        e_cat = st.selectbox("Categoría", ["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"], index=["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"].index(row.get('categoria', 'Monturas')) if row.get('categoria', 'Monturas') in ["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"] else 0)
                        e_marca = st.text_input("Marca", value=row.get('marca', ''))
                        e_prov = st.text_input("Proveedor", value=row.get('proveedor', ''))
                        e_costo = st.number_input("Costo", value=float(row.get('costo_compra', 0)))
                        e_pvp = st.number_input("PVP", value=float(row.get('precio_venta', 0)))
                        
                        if st.form_submit_button("Actualizar"):
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
                            st.success("Actualizado")
                            st.rerun()
            with btn4:
                with st.popover("🗑️"):
                    st.error("¿Estás seguro?")
                    if st.button("Sí, Eliminar", key=f"del_{row['id']}", type="primary"):
                        eliminar_producto(row['id'])
                        st.rerun()
        
        st.markdown("<hr style='margin: 0; padding: 0; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)


    # Alerta de stock bajo
    bajo_stock = df[df["cantidad_disponible"] <= 3]
    if not bajo_stock.empty:
        st.warning(f"⚠️ **{len(bajo_stock)} producto(s) con stock ≤ 3:** " + ", ".join(bajo_stock["codigo_referencia"].astype(str).tolist()))
