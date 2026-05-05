import streamlit as st
import pandas as pd
from datetime import date
from database import obtener_estado_caja, abrir_caja, registrar_gasto, obtener_resumen_dia, cerrar_caja, cargar_sucursales

def render_contabilidad():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>💰 Contabilidad y Caja</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Control de flujo de caja, gastos y cierres diarios</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal = st.session_state.get("sucursal_activa", "Matriz")
    hoy = date.today().strftime("%Y-%m-%d")
    
    tabs = st.tabs(["💵 Caja Diaria", "🌍 Reporte Global (Admin)"])
    
    with tabs[0]:
        # 1. Verificar Estado de Caja
        caja = obtener_estado_caja(sucursal, hoy)
    
        if not caja:
            # PANTALLA DE APERTURA
            st.warning(f"🚨 La caja de hoy ({hoy}) en **{sucursal}** aún no ha sido abierta.")
            with st.form("apertura_caja"):
                st.subheader("Apertura de Caja")
                monto_ini = st.number_input("Monto Inicial en Efectivo (Base para cambio)", min_value=0.0, value=0.0, format="%.2f")
                if st.form_submit_button("🔓 Abrir Caja Ahora", use_container_width=True):
                    abrir_caja({
                        "fecha": hoy,
                        "sucursal": sucursal,
                        "monto_apertura": monto_ini,
                        "estado": "Abierta",
                        "abierta_por": st.session_state.user_login
                    })
                    st.success("Caja abierta correctamente.")
                    st.rerun()
        
        elif caja["estado"] == "Cerrada":
            st.success(f"✅ La caja de hoy ya fue cerrada por **{caja.get('cerrada_por')}**.")
            st.metric("Balance Final", f"${float(caja['monto_cierre']):.2f}")
            if st.button("🔄 Ver Detalles del Cierre"):
                 st.json(caja)
                 
        else:
            # PANTALLA DE CAJA ABIERTA (DURANTE EL DÍA)
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### 💸 Registrar Gasto")
                with st.form("form_gasto", clear_on_submit=True):
                    cat = st.selectbox("Categoría", ["Alquiler", "Luz/Servicios", "Insumos Óptica", "Publicidad", "Sueldos", "Varios"])
                    desc = st.text_input("Descripción", placeholder="Ej: Pago de luz local centro")
                    monto_g = st.number_input("Monto ($)", min_value=0.0, format="%.2f")
                    if st.form_submit_button("Registrar Salida", use_container_width=True):
                        if monto_g > 0:
                            registrar_gasto({
                                "fecha": hoy,
                                "sucursal": sucursal,
                                "categoria": cat,
                                "descripcion": desc,
                                "monto": monto_g,
                                "usuario": st.session_state.user_login
                            })
                            st.success("Gasto registrado.")
                            st.rerun()

            with col2:
                st.markdown("### 📊 Resumen en Tiempo Real")
                resumen = obtener_resumen_dia(sucursal, hoy)
                
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Efectivo (Ventas)", f"${resumen['Efectivo']:.2f}")
                mc2.metric("Tarjetas / Transf.", f"${resumen['Tarjeta'] + resumen['Transferencia']:.2f}")
                mc3.metric("Gastos Hoy", f"-${resumen['Gastos']:.2f}", delta_color="inverse")
                
                # Cálculo de Balance
                base = float(caja["monto_apertura"])
                total_esperado = base + resumen["Efectivo"] - resumen["Gastos"]
                
                st.markdown(f"""
                    <div style='background:#f8fafc; border:2px dashed #cbd5e1; border-radius:15px; padding:20px; text-align:center; margin-top:20px;'>
                        <p style='margin:0; color:#64748b; font-size:14px;'>TOTAL EFECTIVO ESPERADO EN CAJA</p>
                        <h2 style='margin:5px 0; color:#0f172a;'>${total_esperado:.2f}</h2>
                        <p style='margin:0; color:#94a3b8; font-size:11px;'>(Base: ${base:.2f} + Ventas: ${resumen['Efectivo']:.2f} - Gastos: ${resumen['Gastos']:.2f})</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                if st.button("🔒 Realizar CIERRE DE CAJA", type="primary", use_container_width=True):
                    with st.form("cierre_final"):
                        st.subheader("Confirmar Cierre")
                        m_final = st.number_input("Monto Físico en Efectivo (Conteo real)", value=total_esperado)
                        st.info("Al cerrar, ya no se podrán registrar más ventas o gastos por hoy.")
                        if st.form_submit_button("Confirmar y Cerrar Día"):
                            cerrar_caja(caja["id"], {
                                "monto_cierre": m_final,
                                "ventas_efectivo": resumen["Efectivo"],
                                "ventas_tarjeta": resumen["Tarjeta"],
                                "ventas_transf": resumen["Transferencia"],
                                "gastos_totales": resumen["Gastos"],
                                "estado": "Cerrada",
                                "cerrada_por": st.session_state.user_login,
                                "sucursal": sucursal
                            })
                            st.success("Caja cerrada. ¡Buen trabajo!")
                            st.rerun()

    with tabs[1]:
        if st.session_state.user_role != "Administrador":
            st.error("Acceso restringido al Administrador General.")
        else:
            st.markdown("### 📈 Rendimiento de todas las Sucursales")
            df_s = cargar_sucursales()
            sedes = df_s["nombre"].tolist() if not df_s.empty else ["Matriz"]
            
            resumen_global = []
            for s in sedes:
                r = obtener_resumen_dia(s, hoy)
                est = obtener_estado_caja(s, hoy)
                resumen_global.append({
                    "Sucursal": s,
                    "Estado": est["estado"] if est else "Sin Abrir",
                    "Ventas Totales": r["Efectivo"] + r["Tarjeta"] + r["Transferencia"],
                    "Gastos": r["Gastos"],
                    "Neto": (r["Efectivo"] + r["Tarjeta"] + r["Transferencia"]) - r["Gastos"]
                })
            
            df_res = pd.DataFrame(resumen_global)
            st.dataframe(df_res, use_container_width=True, hide_index=True)
            
            # Gráfico simple de barras
            st.bar_chart(df_res.set_index("Sucursal")[["Ventas Totales", "Gastos"]])
