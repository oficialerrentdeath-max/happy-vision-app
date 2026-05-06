import streamlit as st
import pandas as pd
import plotly.express as px
from database import cargar_ordenes_trabajo, cargar_inventario, obtener_resumen_dia

def render_dashboard():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🏠 Dashboard de Control</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Resumen ejecutivo de Happy Vision</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal = st.session_state.get("sucursal_activa", "Matriz")
    
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
