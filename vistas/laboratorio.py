import streamlit as st
import pandas as pd
from database import cargar_ordenes_trabajo, actualizar_estado_orden

def render_laboratorio():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🧪 Gestión de Laboratorio</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Órdenes de trabajo, estados y entregas</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")
    
    # Estados permitidos
    ESTADOS = ["Pendiente", "En Laboratorio", "Recibido", "Listo para Entrega", "Entregado"]
    
    df_ordenes = cargar_ordenes_trabajo(sucursal_activa)
    
    if df_ordenes.empty:
        st.info("No hay órdenes de trabajo registradas. Crea una desde la ficha del paciente.")
    else:
        # Resumen rápido en métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pendientes", len(df_ordenes[df_ordenes["estado"] == "Pendiente"]))
        c2.metric("En Lab", len(df_ordenes[df_ordenes["estado"] == "En Laboratorio"]))
        c3.metric("Listos", len(df_ordenes[df_ordenes["estado"] == "Listo para Entrega"]))
        
        # Filtro por estado
        filtro_est = st.segmented_control("Filtrar por Estado", ["Todas"] + ESTADOS, default="Todas")
        
        df_show = df_ordenes.copy()
        if filtro_est != "Todas":
            df_show = df_show[df_show["estado"] == filtro_est]

        for _, row in df_show.iterrows():
            with st.container():
                # Color basado en estado
                bg_color = "#fefce8" if row['estado'] == "Pendiente" else "#f0f9ff"
                border_color = "#fef08a" if row['estado'] == "Pendiente" else "#bae6fd"
                if row['estado'] == "Listo para Entrega": bg_color, border_color = "#f0fdf4", "#bbf7d0"
                if row['estado'] == "Entregado": bg_color, border_color = "#f8fafc", "#e2e8f0"

                st.markdown(f"""
                    <div style='background:{bg_color}; border:1px solid {border_color}; border-radius:15px; padding:20px; margin-bottom:15px;'>
                        <div style='display:flex; justify-content:space-between; align-items:start;'>
                            <div>
                                <span style='background:#2563eb; color:white; padding:4px 10px; border-radius:20px; font-size:10px; font-weight:bold;'>ORDEN #{row['id']}</span>
                                <h3 style='margin:10px 0 5px 0; color:#1e293b;'>👤 {row['paciente_nombre']}</h3>
                                <p style='margin:0; font-size:13px; color:#64748b;'>🗓️ Creada el: {pd.to_datetime(row['creado_el']).strftime('%Y-%m-%d %H:%M')}</p>
                            </div>
                            <div style='text-align:right;'>
                                <p style='margin:0; font-size:11px; color:#64748b;'>ESTADO ACTUAL</p>
                                <p style='margin:0; font-weight:bold; color:#2563eb; font-size:18px;'>{row['estado']}</p>
                            </div>
                        </div>
                        <div style='margin-top:15px; display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,0.5); padding:10px; border-radius:10px;'>
                             <div>
                                <p style='margin:0; font-size:10px; color:#94a3b8;'>VALOR TOTAL</p>
                                <p style='margin:0; font-weight:bold;'>${float(row['total_venta']):.2f}</p>
                             </div>
                             <div>
                                <p style='margin:0; font-size:10px; color:#94a3b8;'>ABONO</p>
                                <p style='margin:0; font-weight:bold; color:#16a34a;'>${float(row['abono']):.2f}</p>
                             </div>
                             <div>
                                <p style='margin:0; font-size:10px; color:#94a3b8;'>SALDO PENDIENTE</p>
                                <p style='margin:0; font-weight:bold; color:#ef4444;'>${float(row['saldo']):.2f}</p>
                             </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Acciones
                ca1, ca2, ca3 = st.columns([2, 2, 1])
                with ca1:
                    nuevo_e = st.selectbox("Cambiar Estado", ESTADOS, index=ESTADOS.index(row['estado']), key=f"est_{row['id']}")
                    if nuevo_e != row['estado']:
                        actualizar_estado_orden(row['id'], nuevo_e, st.session_state.user_login, sucursal_activa)
                        st.success(f"Estado actualizado a {nuevo_e}")
                        st.rerun()
                with ca2:
                    if st.button("📄 Ver Detalles / Receta", key=f"receta_{row['id']}", use_container_width=True):
                        st.json(row['detalles_receta'])
                with ca3:
                    st.button("📥 Ticket", key=f"ticket_{row['id']}", use_container_width=True)
                
                st.divider()
