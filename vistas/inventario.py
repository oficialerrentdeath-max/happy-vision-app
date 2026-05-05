import streamlit as st
import pandas as pd
from database import cargar_inventario, guardar_producto

def render_inventario():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>📦 Control de Inventario</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Gestión de stock, monturas y accesorios</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")
    
    # Cargar datos
    df = cargar_inventario(sucursal_activa)
    
    col_acc1, col_acc2 = st.columns([2, 1])
    
    with col_acc2:
        with st.expander("➕ Agregar Nuevo Producto", expanded=False):
            with st.form("nuevo_producto_form", clear_on_submit=True):
                n_nombre = st.text_input("Nombre del Producto", placeholder="Ej: Ray-Ban Aviator RB3025")
                c1, c2 = st.columns(2)
                n_cat = c1.selectbox("Categoría", ["Monturas", "Lentes de Contacto", "Líquidos", "Accesorios"])
                n_marca = c2.text_input("Marca")
                
                c3, c4 = st.columns(2)
                n_stock = c3.number_input("Stock Inicial", min_value=0, value=0)
                n_min = c4.number_input("Stock Mínimo (Alerta)", min_value=0, value=5)
                
                c5, c6 = st.columns(2)
                n_costo = c5.number_input("Precio Costo ($)", min_value=0.0, format="%.2f")
                n_venta = c6.number_input("Precio Venta ($)", min_value=0.0, format="%.2f")
                
                if st.form_submit_button("💾 Guardar en Inventario", use_container_width=True):
                    if n_nombre:
                        guardar_producto({
                            "nombre": n_nombre,
                            "categoria": n_cat,
                            "marca": n_marca,
                            "stock": n_stock,
                            "stock_minimo": n_min,
                            "precio_costo": n_costo,
                            "precio_venta": n_venta,
                            "sucursal": sucursal_activa
                        })
                        st.success("Producto agregado.")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio.")

    with col_acc1:
        st.markdown(f"### Productos en {sucursal_activa}")
        if df.empty:
            st.info("No hay productos registrados en esta sucursal.")
        else:
            # Filtros rápidos
            cats = ["Todos"] + df["categoria"].unique().tolist()
            filtro_cat = st.segmented_control("Filtrar Categoría", cats, default="Todos")
            
            df_filtered = df.copy()
            if filtro_cat != "Todos":
                df_filtered = df_filtered[df_filtered["categoria"] == filtro_cat]
            
            # Tabla de inventario
            for _, row in df_filtered.iterrows():
                with st.container():
                    low_stock = row['stock'] <= row['stock_minimo']
                    color_stock = "#ef4444" if low_stock else "#22c55e"
                    
                    st.markdown(f"""
                        <div style='background:white; border:1px solid #e2e8f0; border-radius:12px; padding:15px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <h4 style='margin:0; color:#1e293b;'>{row['nombre']}</h4>
                                <p style='margin:2px 0; font-size:12px; color:#64748b;'>🏷️ {row['categoria']} | Marca: {row.get('marca','N/A')}</p>
                                <p style='margin:0; font-weight:700; color:#3b82f6;'>💰 PVP: ${row['precio_venta']:.2f}</p>
                            </div>
                            <div style='text-align:right;'>
                                <p style='margin:0; font-size:10px; color:#94a3b8;'>STOCK</p>
                                <h2 style='margin:0; color:{color_stock};'>{row['stock']}</h2>
                                {'<span style="color:#ef4444; font-size:10px; font-weight:bold;">⚠️ BAJO STOCK</span>' if low_stock else ''}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    with c2:
                        if st.button("➕ Stock", key=f"add_{row['id']}"):
                            guardar_producto({"id": row['id'], "stock": row['stock'] + 1})
                            st.rerun()
                    with c3:
                        if st.button("➖ Stock", key=f"rem_{row['id']}"):
                            if row['stock'] > 0:
                                guardar_producto({"id": row['id'], "stock": row['stock'] - 1})
                                st.rerun()
                    with c4:
                        with st.popover("✏️"):
                            with st.form(f"edit_inv_{row['id']}"):
                                e_nom = st.text_input("Nombre", value=row['nombre'])
                                e_costo = st.number_input("Costo", value=float(row['precio_costo']))
                                e_venta = st.number_input("Venta", value=float(row['precio_venta']))
                                e_min = st.number_input("Mínimo", value=int(row['stock_minimo']))
                                if st.form_submit_button("Actualizar"):
                                    guardar_producto({
                                        "id": row['id'],
                                        "nombre": e_nom,
                                        "precio_costo": e_costo,
                                        "precio_venta": e_venta,
                                        "stock_minimo": e_min
                                    })
                                    st.success("Actualizado")
                                    st.rerun()
                    st.divider()
