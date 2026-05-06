import streamlit as st
import pandas as pd
from datetime import datetime
from database import supabase, registrar_auditoria

def render_nueva_orden():
    st.markdown("""
    <div class="page-header">
        <h1>📝 Generar Orden de Trabajo</h1>
        <p>Completa los detalles técnicos de la receta para el laboratorio</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Búsqueda de Paciente (Obligatorio para la orden)
    from vistas.clinica import _cargar_historias # Reusar lógica de carga si existe
    
    with st.container():
        st.markdown("<div class='section-title'>👤 Selección de Paciente</div>", unsafe_allow_html=True)
        # Por ahora un selector simple de pacientes existentes
        try:
            res_p = supabase.table("historias_clinicas").select("id, paciente_nombre").execute()
            pacientes_op = {p["id"]: p["paciente_nombre"] for p in res_p.data} if res_p.data else {}
        except:
            pacientes_op = {}
        
        paciente_sel = st.selectbox("Seleccione el paciente para esta orden:", 
                                    options=list(pacientes_op.keys()),
                                    format_func=lambda x: pacientes_op[x])

    st.markdown("---")
    
    # 2. CUADRO DE MEDIDAS TÉCNICO
    st.markdown("<div class='section-title'>📋 Cuadro de Medidas (Receta)</div>", unsafe_allow_html=True)
    
    cols_receta = ["Esfera", "Cilindro", "Eje", "Adición", "A.V."]
    data_od = {c: [""] for c in cols_receta}
    data_oi = {c: [""] for c in cols_receta}
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ojo Derecho (OD)")
        df_od = st.data_editor(pd.DataFrame(data_od), key="receta_od_nueva", hide_index=True, use_container_width=True)
    with c2:
        st.subheader("Ojo Izquierdo (OI)")
        df_oi = st.data_editor(pd.DataFrame(data_oi), key="receta_oi_nueva", hide_index=True, use_container_width=True)

    # Otros detalles técnicos
    t1, t2, t3 = st.columns(3)
    dip = t1.text_input("D.I.P. (Distancia Interpupilar)", placeholder="62/60")
    altura = t2.text_input("Altura Focal", placeholder="18 mm")
    tipo_lente = t3.selectbox("Tipo de Lente", ["Monofocal", "Bifocal (FT/Kriptok)", "Progresivo", "Ocupacional"])

    # 3. DETALLES DE MATERIAL Y TRATAMIENTOS
    st.markdown("<div class='section-title'>🔬 Especificaciones de Laboratorio</div>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    material = m1.multiselect("Material de la Luna", 
                             ["CR-39", "Policarbonato", "Alto Índice (1.61/1.67)", "Cristal", "Transitions", "Photogray"])
    protecciones = m2.multiselect("Tratamientos / Protecciones", 
                                 ["Antirreflejo Básico", "Blue Defense (Filtro Azul)", "Super Hidrofóbico", "Espejado", "Tinte"])

    observaciones = st.text_area("Observaciones Técnicas para el Laboratorio", 
                                 placeholder="Ej: Montaje en armazón ranurado, biselado especial...")

    # 4. GUARDAR ORDEN
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 GENERAR Y ENVIAR A LABORATORIO", type="primary", use_container_width=True):
        if not paciente_sel:
            st.error("⚠️ Debes seleccionar un paciente para generar la orden.")
        else:
            nueva_orden = {
                "paciente_id": paciente_sel,
                "paciente_nombre": pacientes_op[paciente_sel],
                "receta_od": df_od.to_dict('records')[0],
                "receta_oi": df_oi.to_dict('records')[0],
                "dip": dip,
                "altura": altura,
                "tipo_lente": tipo_lente,
                "material": ", ".join(material),
                "protecciones": ", ".join(protecciones),
                "observaciones": observaciones,
                "estado": "Pendiente",
                "sucursal": st.session_state.get("sucursal_activa", "Matriz"),
                "creado_por": st.session_state.get("user_login", "admin")
            }
            
            try:
                supabase.table("ordenes_trabajo").insert(nueva_orden).execute()
                registrar_auditoria("Generar Orden", "Orden de Trabajo", 
                                   f"Nueva orden creada para {pacientes_op[paciente_sel]}", 
                                   st.session_state.get("user_login", ""),
                                   st.session_state.get("user_name", ""),
                                   st.session_state.get("sucursal_activa", ""))
                st.success("✅ ¡Orden de trabajo generada y enviada al laboratorio exitosamente!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error al guardar la orden: {e}")
