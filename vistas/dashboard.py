import streamlit as st
import pandas as pd
import plotly.express as px
from database import cargar_ordenes_trabajo, cargar_inventario, obtener_resumen_dia, cargar_citas_hoy

def render_dashboard():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🏠 Dashboard de Control</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Resumen ejecutivo de Happy Vision</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal = st.session_state.get("sucursal_activa", "Matriz")
    
    # 0. ALERTAS DE CITAS PARA HOY
    df_citas = cargar_citas_hoy(sucursal)
    citas_pendientes = df_citas[df_citas["estado"] == "Pendiente"] if not df_citas.empty else pd.DataFrame()
    
    if not citas_pendientes.empty:
        st.warning(f"🔔 **¡Atención!** Tienes {len(citas_pendientes)} citas agendadas para hoy.")
        for _, cita in citas_pendientes.iterrows():
            st.markdown(f"- **{cita['hora']}**: {cita['paciente_nombre']} ({cita.get('motivo', 'Sin motivo')})")
        st.divider()
    
    # 1. MÉTRICAS PRINCIPALES
    resumen = obtener_resumen_dia(sucursal, st.session_state.get("fecha_hoy", pd.Timestamp.now().strftime("%Y-%m-%d")))
    df_ordenes = cargar_ordenes_trabajo(sucursal)
    df_inv = cargar_inventario(sucursal)
    
    m1, m2, m3, m4 = st.columns(4)
    
    # Ventas de hoy (Efectivo + Otros)
    ventas_hoy = resumen["Efectivo"] + resumen["Tarjeta"] + resumen["Transferencia"]
    m1.metric("Ventas de Hoy", f"${ventas_hoy:.2f}", delta=f"-${resumen['Gastos']:.2f} gastos")
    
    # Órdenes en Laboratorio
    en_lab = 0
    listos = 0
    if not df_ordenes.empty and "estado" in df_ordenes.columns:
        en_lab = len(df_ordenes[df_ordenes["estado"] == "En Laboratorio"])
        listos = len(df_ordenes[df_ordenes["estado"] == "Listo para Entrega"])
    
    m2.metric("En Laboratorio", en_lab, help="Trabajos que están actualmente en proceso")
    m3.metric("Listos p/ Entrega", listos, delta=f"{listos} clientes esperando" if listos > 0 else None)
    
    # Alertas de Inventario (Robustez ante nombres de columnas)
    bajo_stock = 0
    if not df_inv.empty:
        col_s = "cantidad_disponible" if "cantidad_disponible" in df_inv.columns else "stock"
        col_m = "stock_minimo" if "stock_minimo" in df_inv.columns else None
        
        if col_m:
            bajo_stock = len(df_inv[df_inv[col_s] <= df_inv[col_m]])
        else:
            # Fallback: Consideramos bajo stock si es <= 3
            bajo_stock = len(df_inv[df_inv[col_s] <= 3])
            
    m4.metric("Bajo Stock", bajo_stock, delta="Revisar" if bajo_stock > 0 else "OK", delta_color="inverse" if bajo_stock > 0 else "normal")

    st.divider()

    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown("### 📈 Flujo de Órdenes Recientes")
        if not df_ordenes.empty:
            # Gráfico de órdenes por estado
            df_counts = df_ordenes["estado"].value_counts().reset_index()
            df_counts.columns = ["Estado", "Cantidad"]
            fig = px.bar(df_counts, x="Estado", y="Cantidad", color="Estado", 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de órdenes aún.")

    with col_r:
        # Mostrar productos con bajo stock
        if bajo_stock > 0:
            col_s = "cantidad_disponible" if "cantidad_disponible" in df_inv.columns else "stock"
            col_m = "stock_minimo" if "stock_minimo" in df_inv.columns else None
            
            if col_m:
                df_alertas = df_inv[df_inv[col_s] <= df_inv[col_m]].head(5)
            else:
                df_alertas = df_inv[df_inv[col_s] <= 3].head(5)
                
            for _, row in df_alertas.iterrows():
                st.error(f"**{row.get('nombre', 'Producto')}**\n\nQuedan solo **{row.get(col_s, 0)}** unidades.")
        else:
            st.success("✅ Inventario saludable.")
            
        st.markdown("---")
        # Mostrar órdenes más antiguas sin entregar
        st.markdown("**⏳ Trabajos Pendientes**")
        if not df_ordenes.empty and "estado" in df_ordenes.columns:
            df_viejas = df_ordenes[df_ordenes["estado"] == "Pendiente"].head(3)
            for _, row in df_viejas.iterrows():
                st.warning(f"ID #{row['id']} - {row['paciente_nombre']}")
        else:
            st.caption("No hay trabajos pendientes.")

    # Acceso Rápido
    st.markdown("### ⚡ Acciones Rápidas")
    cq1, cq2, cq3 = st.columns(3)
    if cq1.button("👥 Ver Pacientes", use_container_width=True):
        st.session_state.page = "Pacientes"
        st.rerun()
    if cq2.button("🧪 Gestionar Laboratorio", use_container_width=True):
        st.session_state.page = "Laboratorio"
        st.rerun()
    if cq3.button("💰 Abrir/Cerrar Caja", use_container_width=True):
        st.session_state.page = "Contabilidad"
        st.rerun()

    st.divider()
    st.markdown("## 📊 Business Intelligence & Reportes Gerenciales")
    
    tab1, tab2, tab3 = st.tabs(["💰 Rentabilidad Financiera", "📦 Rotación ABC", "📈 Tendencias"])
    
    with tab1:
        st.subheader("Reporte Financiero y de Rentabilidad")
        from database import cargar_ventas_historial
        df_ventas = cargar_ventas_historial(sucursal)
        
        if not df_ventas.empty:
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'])
            df_ventas['mes'] = df_ventas['fecha'].dt.to_period('M').astype(str)
            df_ventas['total'] = pd.to_numeric(df_ventas['total'], errors='coerce').fillna(0)
            df_ventas['costo_total'] = pd.to_numeric(df_ventas.get('costo_total', 0), errors='coerce').fillna(0)
            df_ventas['utilidad'] = df_ventas['total'] - df_ventas['costo_total']
            
            resumen_mes = df_ventas.groupby('mes').agg(
                Ingresos=('total', 'sum'),
                Costos=('costo_total', 'sum'),
                Utilidad=('utilidad', 'sum')
            ).reset_index()
            
            fig_fin = px.bar(resumen_mes, x='mes', y=['Ingresos', 'Costos', 'Utilidad'],
                             barmode='group', title="Evolución Financiera por Mes")
            st.plotly_chart(fig_fin, use_container_width=True)
            
            # Margen de Ganancia
            total_ingresos = resumen_mes['Ingresos'].sum()
            total_utilidad = resumen_mes['Utilidad'].sum()
            margen_promedio = (total_utilidad / total_ingresos * 100) if total_ingresos > 0 else 0
            
            st.metric("Margen de Ganancia Promedio Global", f"{margen_promedio:.1f}%")
        else:
            st.info("No hay suficientes datos de ventas para el reporte financiero.")
            
    with tab2:
        st.subheader("Análisis de Rotación de Inventario (ABC)")
        if not df_inv.empty:
            df_inv['precio_venta'] = pd.to_numeric(df_inv.get('precio_venta', 0), errors='coerce').fillna(0)
            df_inv['cantidad'] = pd.to_numeric(df_inv.get('cantidad_disponible', df_inv.get('stock', 0)), errors='coerce').fillna(0)
            df_inv['valor_potencial'] = df_inv['precio_venta'] * df_inv['cantidad']
            
            fig_abc = px.pie(df_inv.sort_values('valor_potencial', ascending=False).head(10), 
                             names='nombre', values='valor_potencial', 
                             title="Top 10 Productos por Valor Estancado en Stock")
            st.plotly_chart(fig_abc, use_container_width=True)
        else:
            st.info("No hay datos de inventario.")
            
    with tab3:
        st.subheader("Tendencias de Venta por Categoría")
        if not df_ventas.empty:
            fig_tendencia = px.pie(df_ventas, names='metodo_pago', title="Distribución por Método de Pago")
            st.plotly_chart(fig_tendencia, use_container_width=True)
