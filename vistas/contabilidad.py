import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import obtener_estado_caja, abrir_caja, registrar_gasto, obtener_resumen_dia, cerrar_caja, cargar_sucursales, cargar_ventas_historial

def render_contabilidad():
    st.markdown("""
        <style>
        .metric-card {
            background-color: white;
            border: 1px solid #e2e8f0;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .profit-text { color: #16a34a; font-weight: bold; font-size: 24px; }
        .revenue-text { color: #00458e; font-weight: bold; font-size: 24px; }
        .cost-text { color: #dc2626; font-weight: bold; font-size: 24px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>💰 Gestión Financiera y Rentabilidad</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Control de caja diaria y análisis de ganancias netas</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal = st.session_state.get("sucursal_activa", "Matriz")
    es_admin = st.session_state.get("user_role") == "Administrador"
    hoy = date.today().strftime("%Y-%m-%d")
    
    tabs = st.tabs(["💵 Caja Diaria", "📈 Rentabilidad y Reportes"])
    
    with tabs[0]:
        # --- Lógica de Caja Diaria (Existente pero estilizada) ---
        caja = obtener_estado_caja(sucursal, hoy)
        if not caja:
            st.warning(f"🚨 Caja Cerrada para **{sucursal}**. Ábrela para empezar a registrar.")
            if st.button("🔓 Abrir Caja Hoy"):
                abrir_caja({"fecha": hoy, "sucursal": sucursal, "monto_apertura": 0, "estado": "Abierta", "abierta_por": st.session_state.user_login})
                st.rerun()
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("💸 Gastos")
                with st.form("gasto_r"):
                    cat = st.selectbox("Categoría", ["Lunas/Lab", "Armazones", "Sueldos", "Servicios", "Otros"])
                    monto = st.number_input("Monto ($)", min_value=0.0)
                    if st.form_submit_button("Registrar Gasto"):
                        registrar_gasto({"fecha": hoy, "sucursal": sucursal, "categoria": cat, "monto": monto, "usuario": st.session_state.user_login})
                        st.rerun()
            with col2:
                res = obtener_resumen_dia(sucursal, hoy)
                st.metric("Ventas Hoy (Efectivo)", f"${res['Efectivo']:.2f}")
                st.metric("Total Gastos Hoy", f"-${res['Gastos']:.2f}")

    with tabs[1]:
        if not es_admin:
            st.error("🔒 El reporte de rentabilidad solo es visible para el Administrador.")
        else:
            st.subheader("📊 Análisis de Ganancias Reales")
            
            # Filtros de tiempo
            c_f1, c_f2, c_f3 = st.columns(3)
            suc_sel = c_f1.selectbox("Sucursal:", ["Todas"] + cargar_sucursales()["nombre"].tolist())
            mes_sel = c_f2.selectbox("Mes:", ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month)
            anio_sel = c_f3.selectbox("Año:", [2024, 2025, 2026], index=0)

            # Cargar datos
            df_v = cargar_ventas_historial(suc_sel)
            
            if df_v.empty:
                st.info("No hay datos de ventas para este periodo.")
            else:
                # Procesar fechas para filtros
                df_v['fecha_dt'] = pd.to_datetime(df_v['fecha'])
                df_v['mes_nombre'] = df_v['fecha_dt'].dt.month_name()
                
                # Traducir meses si es necesario o filtrar por número
                meses_map = {"Enero":1, "Febrero":2, "Marzo":3, "Abril":4, "Mayo":5, "Junio":6, "Julio":7, "Agosto":8, "Septiembre":9, "Octubre":10, "Noviembre":11, "Diciembre":12}
                
                df_f = df_v[df_v['fecha_dt'].dt.year == anio_sel]
                if mes_sel != "Todos":
                    df_f = df_f[df_f['fecha_dt'].dt.month == meses_map[mes_sel]]

                # KPIs de Rentabilidad
                ingresos = df_f['total'].astype(float).sum()
                costos = df_f['costo_total'].astype(float).sum()
                ganancia = ingresos - costos
                
                kpi1, kpi2, kpi3 = st.columns(3)
                with kpi1:
                    st.markdown(f'<div class="metric-card">Ingresos Brutos<br><span class="revenue-text">${ingresos:,.2f}</span></div>', unsafe_allow_html=True)
                with kpi2:
                    st.markdown(f'<div class="metric-card">Costos (Lab/Material)<br><span class="cost-text">${costos:,.2f}</span></div>', unsafe_allow_html=True)
                with kpi3:
                    st.markdown(f'<div class="metric-card">GANANCIA NETA<br><span class="profit-text">${ganancia:,.2f}</span></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráfico de Ganancia por Día
                st.write("### 📈 Tendencia de Ganancia Diaria")
                df_f['fecha_dia'] = df_f['fecha_dt'].dt.date
                df_daily = df_f.groupby('fecha_dia').agg({'total': 'sum', 'costo_total': 'sum'}).reset_index()
                df_daily['Ganancia'] = df_daily['total'] - df_daily['costo_total']
                st.area_chart(df_daily.set_index('fecha_dia')[['total', 'Ganancia']])

                # Detalle de Ventas
                with st.expander("📝 Ver desglose de transacciones"):
                    st.dataframe(df_f[['fecha', 'cliente', 'total', 'costo_total', 'metodo_pago', 'sucursal']], use_container_width=True)
