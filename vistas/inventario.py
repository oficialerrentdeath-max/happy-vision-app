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
        with st.expander("➕ Agregar Nueva Montura", expanded=False):
            with st.form("nuevo_producto_form", clear_on_submit=True):
                n_cod = st.text_input("Código de Referencia", placeholder="Ej: RX-5154")
                n_marca = st.text_input("Marca", placeholder="Ej: Ray-Ban")
                n_modelo = st.text_input("Modelo / Color", placeholder="Ej: Aviator - Negro")
                
                c3, c4 = st.columns(2)
                n_stock = c3.number_input("Cantidad Disponible", min_value=0, value=0)
                n_min = c4.number_input("Stock Mínimo (Alerta)", min_value=0, value=5)
                
                c5, c6 = st.columns(2)
                n_costo = c5.number_input("Costo Compra ($)", min_value=0.0, format="%.2f")
                n_venta = c6.number_input("Precio Venta ($)", min_value=0.0, format="%.2f")
                
                if st.form_submit_button("💾 Guardar en Inventario", use_container_width=True):
                    if n_cod and n_marca:
                        guardar_producto({
                            "codigo_referencia": n_cod,
                            "marca": n_marca,
                            "modelo_color": n_modelo,
                            "cantidad_disponible": n_stock,
                            "stock_minimo": n_min,
                            "costo_compra": n_costo,
                            "precio_venta": n_venta,
                            "sucursal": sucursal_activa
                        })
                        st.success("Montura agregada.")
                        st.rerun()
                    else:
                        st.error("Código y Marca son obligatorios.")

    with col_acc1:
        st.markdown(f"### Monturas en {sucursal_activa}")
        if df.empty:
            st.info("No hay monturas registradas en esta sucursal.")
        else:
            # Tabla de inventario
            for _, row in df.iterrows():
                with st.container():
                    low_stock = row.get('cantidad_disponible', 0) <= row.get('stock_minimo', 5)
                    color_stock = "#ef4444" if low_stock else "#22c55e"
                    
                    st.markdown(f"""
                        <div style='background:white; border:1px solid #e2e8f0; border-radius:12px; padding:15px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <h4 style='margin:0; color:#1e293b;'>{row.get('codigo_referencia', 'S/C')} - {row.get('marca', 'Sin Marca')}</h4>
                                <p style='margin:2px 0; font-size:12px; color:#64748b;'>🎨 {row.get('modelo_color', 'N/A')}</p>
                                <p style='margin:0; font-weight:700; color:#3b82f6;'>💰 PVP: ${row.get('precio_venta', 0):.2f}</p>
                            </div>
                            <div style='text-align:right;'>
                                <p style='margin:0; font-size:10px; color:#94a3b8;'>DISPONIBLE</p>
                                <h2 style='margin:0; color:{color_stock};'>{row.get('cantidad_disponible', 0)}</h2>
                                {'<span style="color:#ef4444; font-size:10px; font-weight:bold;">⚠️ BAJO STOCK</span>' if low_stock else ''}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    with c2:
                        if st.button("➕", key=f"add_{row['id']}"):
                            guardar_producto({"id": row['id'], "cantidad_disponible": row['cantidad_disponible'] + 1})
                            st.rerun()
                    with c3:
                        if st.button("➖", key=f"rem_{row['id']}"):
                            if row['cantidad_disponible'] > 0:
                                guardar_producto({"id": row['id'], "cantidad_disponible": row['cantidad_disponible'] - 1})
                                st.rerun()
                    with c4:
                        with st.popover("✏️"):
                            with st.form(f"edit_inv_{row['id']}"):
                                e_cod = st.text_input("Código", value=row.get('codigo_referencia', ''))
                                e_marca = st.text_input("Marca", value=row.get('marca', ''))
                                e_mod = st.text_input("Modelo/Color", value=row.get('modelo_color', ''))
                                e_costo = st.number_input("Costo", value=float(row.get('costo_compra', 0)))
                                e_venta = st.number_input("Venta", value=float(row.get('precio_venta', 0)))
                                if st.form_submit_button("Actualizar"):
                                    guardar_producto({
                                        "id": row['id'],
                                        "codigo_referencia": e_cod,
                                        "marca": e_marca,
                                        "modelo_color": e_mod,
                                        "costo_compra": e_costo,
                                        "precio_venta": e_venta
                                    })
                                    st.success("Actualizado")
                                    st.rerun()
                    st.divider()
