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
                    # Selección de Paciente (Opcional para venta directa, obligatorio para orden lab)
                    from database import cargar_pacientes
                    df_pacs = cargar_pacientes()
                    pac_nombres = ["Consumidor Final"] + df_pacs["nombre"].tolist() if not df_pacs.empty else ["Consumidor Final"]
                    paciente_sel = st.selectbox("Paciente / Cliente", pac_nombres)
                    
                    st.markdown("---")
                    st.markdown("🩺 **Datos Clínicos (Si aplica)**")
                    c_rx1, c_rx2 = st.columns(2)
                    rx_od = c_rx1.text_input("Receta OD", placeholder="Esf, Cyl, Eje")
                    rx_oi = c_rx2.text_input("Receta OI", placeholder="Esf, Cyl, Eje")
                    
                    c_rx3, c_rx4 = st.columns(2)
                    dist_pupilar = c_rx3.number_input("Distancia Pupilar (mm)", min_value=0.0, format="%.1f")
                    tipo_lente = c_rx4.text_input("Tipo de Lente (Laboratorio)", placeholder="Ej: Policarbonato AR")
                    
                    st.markdown("---")
                    st.markdown("💰 **Finanzas**")
                    metodo = st.selectbox("Forma de Pago", ["Efectivo", "Tarjeta", "Transferencia"])
                    abono = st.number_input("Abono Inicial ($)", min_value=0.0, max_value=total_venta, value=total_venta)
                    saldo = total_venta - abono
                    st.warning(f"Saldo Pendiente: ${saldo:.2f}")
                    
                    if st.form_submit_button("🛒 Finalizar y Guardar", use_container_width=True, type="primary"):
                        if total_venta > 0:
                            # 1. Preparar Datos de la Orden
                            p_id = None
                            if paciente_sel != "Consumidor Final":
                                p_id = df_pacs[df_pacs["nombre"] == paciente_sel].iloc[0]["id"]
                            
                            # Buscar ID de la montura si hay una en el carrito
                            montura_id = None
                            for it in st.session_state.items_venta:
                                if it["tipo"] == "Montura":
                                    montura_id = it["id_ref"]
                                    break
                            
                            orden_data = {
                                "paciente_id": p_id,
                                "paciente_nombre": paciente_sel,
                                "montura_id": montura_id,
                                "receta_od": rx_od,
                                "receta_oi": rx_oi,
                                "distancia_pupilar": dist_pupilar,
                                "tipo_lente_laboratorio": tipo_lente,
                                "estado_trabajo": "Pendiente",
                                "sucursal": sucursal_activa,
                                "detalles_json": st.session_state.items_venta # Guardamos todo el carrito por si acaso
                            }
                            
                            # 2. Preparar Datos del Pago
                            pago_data = {
                                "monto_total": total_venta,
                                "abono_inicial": abono,
                                "saldo_pendiente": saldo,
                                "metodo_pago": metodo
                            }
                            
                            # 3. Guardar en Base de Datos (Función vinculada)
                            from database import guardar_orden_trabajo
                            res_id = guardar_orden_trabajo(orden_data, pago_data)
                            
                            if res_id:
                                # 4. Descontar stock si hubo montura
                                if montura_id:
                                    from database import supabase
                                    curr = supabase.table("inventario_monturas").select("cantidad_disponible").eq("id", montura_id).execute()
                                    if curr.data:
                                        nuevo_stock = max(0, int(curr.data[0]["cantidad_disponible"]) - 1)
                                        supabase.table("inventario_monturas").update({"cantidad_disponible": nuevo_stock}).eq("id", montura_id).execute()

                                st.success(f"Orden #{res_id} y Pago registrados exitosamente.")
                                
                                # Generar PDF de la Venta
                                from utils import generar_pdf_venta
                                data_pdf = {
                                    "fecha": datetime.now().isoformat(),
                                    "cliente": paciente_sel,
                                    "total": total_venta,
                                    "sucursal": sucursal_activa,
                                    "detalles": st.session_state.items_venta
                                }
                                pdf_b = generar_pdf_venta(data_pdf)
                                st.download_button("📥 Descargar Comprobante/Orden", data=pdf_b, file_name=f"Orden_{res_id}_{paciente_sel}.pdf", mime="application/pdf", use_container_width=True)
                                
                                st.session_state.items_venta = []
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
