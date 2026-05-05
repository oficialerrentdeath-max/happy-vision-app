import streamlit as st
import pandas as pd
from datetime import datetime
from database import registrar_venta_directa, registrar_pago_saldo, cargar_inventario, cargar_ordenes_trabajo

def render_ventas():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🧾 Generador de Ventas / Factura</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Arma el presupuesto o venta detallada para el paciente</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🛒 Nueva Venta Detallada", "💰 Cobro de Saldos"])
    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")

    # ── VENTA DETALLADA ────────────────────────────────────────
    with tab1:
        if "items_venta" not in st.session_state: st.session_state.items_venta = []
        
        c_izq, c_der = st.columns([1.5, 1])
        
        with c_izq:
            st.subheader("🛠️ Armar Pedido")
            
            # 1. MONTURA (Desde Inventario)
            with st.expander("👓 Seleccionar Montura", expanded=True):
                df_inv = cargar_inventario(sucursal_activa)
                df_monturas = df_inv[df_inv["categoria"] == "Monturas"] if not df_inv.empty else pd.DataFrame()
                
                if df_monturas.empty:
                    st.warning("No hay monturas registradas en el inventario.")
                else:
                    busc_m = st.text_input("🔍 Buscar Montura (Nombre/Código)", placeholder="Ej: Vision 5021")
                    df_m_f = df_monturas[df_monturas["nombre"].str.contains(busc_m, case=False)] if busc_m else df_monturas
                    
                    for _, m in df_m_f.head(5).iterrows():
                        col_m1, col_m2 = st.columns([3, 1])
                        col_m1.write(f"**{m['nombre']}** - ${m['precio_venta']:.2f}")
                        if col_m2.button("Añadir", key=f"add_m_{m['id']}"):
                            st.session_state.items_venta.append({
                                "tipo": "Montura",
                                "detalle": f"MONTURA {m['nombre']}",
                                "id_ref": m['id'],
                                "precio": float(m['precio_venta'])
                            })
                            st.toast("Montura añadida")

            # 2. LUNAS (Configuración Manual por ahora)
            with st.expander("🔬 Configurar Lunas", expanded=True):
                col_l1, col_l2 = st.columns(2)
                material = col_l1.selectbox("Material", ["Resina CR39", "Policarbonato", "Alto Índice 1.61", "Alto Índice 1.67", "Cristal"])
                proteccion = col_l2.multiselect("Protecciones", ["Antireflejo", "Blue Defense", "Fotocromático", "UV400", "Filtro IR"])
                
                precio_lunas = st.number_input("Precio de las Lunas ($)", min_value=0.0, step=5.0)
                
                if st.button("➕ Añadir Lunas al Pedido", use_container_width=True):
                    desc_lunas = f"LUNAS {material} " + (" ".join(proteccion) if proteccion else "")
                    st.session_state.items_venta.append({
                        "tipo": "Lunas",
                        "detalle": desc_lunas.strip(),
                        "precio": precio_lunas
                    })
                    st.toast("Lunas añadidas")

            # 3. OTROS PRODUCTOS
            with st.expander("🛍️ Otros Productos"):
                df_otros = df_inv[df_inv["categoria"] != "Monturas"] if not df_inv.empty else pd.DataFrame()
                if not df_otros.empty:
                    p_otro = st.selectbox("Seleccionar producto", df_otros["nombre"].tolist())
                    if st.button("Añadir Producto"):
                        row = df_otros[df_otros["nombre"] == p_otro].iloc[0]
                        st.session_state.items_venta.append({
                            "tipo": "Accesorio",
                            "detalle": row["nombre"],
                            "id_ref": row["id"],
                            "precio": float(row["precio_venta"])
                        })

        with c_der:
            st.subheader("📄 Resumen de Venta")
            if not st.session_state.items_venta:
                st.info("No hay ítems en la venta.")
            else:
                total_venta = 0
                for i, it in enumerate(st.session_state.items_venta):
                    with st.container():
                        st.markdown(f"""
                        <div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-bottom:5px; display:flex; justify-content:space-between;'>
                            <div style='font-size:13px;'><b>{it['tipo']}:</b> {it['detalle']}</div>
                            <div style='font-weight:bold;'>${it['precio']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Quitar", key=f"del_it_{i}"):
                            st.session_state.items_venta.pop(i)
                            st.rerun()
                        total_venta += it['precio']
                
                st.markdown(f"## Total: ${total_venta:.2f}")
                
                with st.form("form_finalizar_venta"):
                    cliente = st.text_input("Nombre del Cliente", value="Consumidor Final")
                    metodo = st.selectbox("Forma de Pago", ["Efectivo", "Tarjeta", "Transferencia"])
                    abono = st.number_input("Abono ($)", min_value=0.0, max_value=total_venta, value=total_venta)
                    
                    if st.form_submit_button("🛒 Finalizar y Guardar", use_container_width=True, type="primary"):
                        if total_venta > 0:
                            data_v = {
                                "fecha": datetime.now().isoformat(),
                                "cliente": cliente,
                                "total": total_venta,
                                "abono": abono,
                                "saldo": total_venta - abono,
                                "metodo_pago": metodo,
                                "sucursal": sucursal_activa,
                                "vendedor": st.session_state.user_login,
                                "detalles": st.session_state.items_venta
                            }
                            # Reutilizamos registrar_venta_directa o creamos una específica
                            res = registrar_venta_directa(data_v)
                            if res:
                                st.success("Venta guardada exitosamente.")
                                st.session_state.items_venta = []
                                st.rerun()
                        else:
                            st.error("Añade productos antes de finalizar.")

    # ── COBRO DE SALDOS ────────────────────────────────────────
    with tab2:
        st.subheader("💵 Órdenes con Saldo Pendiente")
        df_ord = cargar_ordenes_trabajo(sucursal_activa)
        if df_ord.empty:
            st.info("No hay órdenes pendientes en esta sucursal.")
        else:
            df_pend = df_ord[df_ord["saldo"] > 0]
            if df_pend.empty:
                st.success("🎉 ¡Todas las órdenes están pagadas!")
            else:
                for _, ord in df_pend.iterrows():
                    with st.expander(f"Orden #{ord['id']} - {ord['paciente_nombre']} (Saldo: ${float(ord['saldo']):.2f})"):
                        c1, c2 = st.columns(2)
                        monto_pago = c1.number_input("Monto a cobrar ($)", min_value=0.1, max_value=float(ord['saldo']), value=float(ord['saldo']), key=f"monto_{ord['id']}")
                        metodo_pago = c2.selectbox("Método", ["Efectivo", "Tarjeta", "Transferencia"], key=f"met_{ord['id']}")
                        
                        if st.button(f"Confirmar Cobro de ${monto_pago:.2f}", key=f"btn_pago_{ord['id']}", type="primary"):
                            exito = registrar_pago_saldo(ord['id'], monto_pago, metodo_pago, st.session_state.user_login, sucursal_activa)
                            if exito:
                                st.success(f"Pago registrado para la orden #{ord['id']}")
                                st.rerun()
