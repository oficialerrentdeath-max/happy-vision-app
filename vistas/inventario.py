import streamlit as st
import pandas as pd
from database import cargar_inventario, guardar_producto

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
    for col, default in [
        ("codigo_referencia",   ""),
        ("nombre",              ""),
        ("categoria",           ""),
        ("marca",               ""),
        ("proveedor",           ""),
        ("costo_compra",        0.0),
        ("precio_venta",        0.0),
        ("stock",               0),          # columna real en Supabase
        ("cantidad_disponible", 0),
    ]:
        if col not in df.columns:
            df[col] = default
    
    # Unificar stock: usar 'stock' si 'cantidad_disponible' no existe o está vacío
    if "stock" in df.columns:
        df["cantidad_disponible"] = df["stock"]

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

    # Preparar DataFrame para mostrar como tabla editable
    df_tabla = df_f[[
        "id", "codigo_referencia", "nombre", "categoria", "marca",
        "proveedor", "costo_compra", "precio_venta", "cantidad_disponible"
    ]].rename(columns={
        "codigo_referencia":   "Código",
        "nombre":              "Producto",
        "categoria":           "Categoría",
        "marca":               "Marca",
        "proveedor":           "Proveedor",
        "costo_compra":        "Costo Compra Unit",
        "precio_venta":        "Precio al Paciente",
        "cantidad_disponible": "Stock",
    }).reset_index(drop=True)

    # Tabla editable tipo Excel
    st.markdown("---")
    edited = st.data_editor(
        df_tabla,
        column_config={
            "id": None,  # Ocultar columna ID
            "Código":            st.column_config.TextColumn("Código", width="small"),
            "Producto":          st.column_config.TextColumn("Producto", width="medium"),
            "Categoría":         st.column_config.SelectboxColumn("Categoría", options=["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios", "Otros"], width="small"),
            "Marca":             st.column_config.TextColumn("Marca", width="small"),
            "Proveedor":         st.column_config.TextColumn("Proveedor", width="medium"),
            "Costo Compra Unit": st.column_config.NumberColumn("Costo Compra Unit", format="$%.2f", width="small"),
            "Precio al Paciente":st.column_config.NumberColumn("Precio al Paciente", format="$%.2f", width="small"),
            "Stock":             st.column_config.NumberColumn("Stock", min_value=0, step=1, width="small"),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="tabla_inventario"
    )

    # Botón para guardar cambios de la tabla
    if st.button("💾 Guardar Cambios de la Tabla", type="primary", use_container_width=True):
        cambios = 0
        for i, row_edit in edited.iterrows():
            id_orig = df_f.iloc[i]["id"] if i < len(df_f) else None
            if id_orig is None:
                continue
            guardar_producto({
                "id":                 id_orig,
                "codigo_referencia":  row_edit["Código"],
                "nombre":             row_edit["Producto"],
                "categoria":          row_edit["Categoría"],
                "marca":              row_edit["Marca"],
                "proveedor":          row_edit["Proveedor"],
                "precio_costo":       row_edit["Costo Compra Unit"],
                "precio_venta":       row_edit["Precio al Paciente"],
                "stock":              int(row_edit["Stock"]),
            })
            cambios += 1
        st.success(f"✅ {cambios} productos actualizados.")
        st.rerun()

    # Alerta de stock bajo
    bajo_stock = df[df["stock"] <= 3]
    if not bajo_stock.empty:
        st.warning(f"⚠️ **{len(bajo_stock)} producto(s) con stock ≤ 3:** " + ", ".join(bajo_stock["nombre"].astype(str).tolist()))
