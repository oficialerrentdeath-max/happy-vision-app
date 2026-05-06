import streamlit as st
import pandas as pd
from datetime import datetime
from database import supabase, registrar_auditoria, cargar_ordenes_trabajo

def render_nueva_orden():
    st.markdown("""
    <div class="page-header">
        <h1>📝 Gestión de Órdenes de Trabajo</h1>
        <p>Crea, busca y administra las recetas técnicas para el laboratorio</p>
    </div>
    """, unsafe_allow_html=True)

    tab_nueva, tab_historial = st.tabs(["➕ Nueva Orden", "🔍 Historial de Órdenes"])

    with tab_nueva:
        st.markdown("<div class='section-title'>👤 Datos del Paciente</div>", unsafe_allow_html=True)
        
        # Selección de Paciente (Buscador Inteligente)
        pacientes_dict = {}
        pacientes_nombres = {}
        
        try:
            res_p = supabase.table("historias_clinicas").select("id, paciente_nombre").execute()
            if res_p.data:
                pacientes_df = pd.DataFrame(res_p.data)
                
                filtro = st.text_input("🔍 Escribe el nombre del paciente:", placeholder="Buscar...")
                
                if filtro:
                    pacientes_df = pacientes_df[
                        pacientes_df["paciente_nombre"].str.contains(filtro, case=False, na=False)
                    ]
                
                if not pacientes_df.empty:
                    pacientes_dict = dict(zip(pacientes_df["id"], pacientes_df["paciente_nombre"]))
                    pacientes_nombres = dict(zip(pacientes_df["id"], pacientes_df["paciente_nombre"]))
                else:
                    st.warning("⚠️ No se encontraron pacientes con ese nombre.")
            else:
                st.info("No hay pacientes registrados en el sistema.")
        except Exception as e:
            st.error(f"Error al cargar pacientes: {e}")

        paciente_id = st.selectbox("Confirmar Selección del Paciente:", 
                                    options=list(pacientes_dict.keys()),
                                    format_func=lambda x: pacientes_dict.get(x, ""),
                                    key="sel_paciente_orden")
        
        # --- NUEVA LÓGICA: CARGAR ÚLTIMA RX ---
        ultima_rx_od = {"Esfera": "", "Cilindro": "", "Eje": "", "Adición": "", "A.V.": ""}
        ultima_rx_oi = {"Esfera": "", "Cilindro": "", "Eje": "", "Adición": "", "A.V.": ""}
        
        if paciente_id:
            try:
                # Buscar la historia más reciente de este paciente
                res_h = supabase.table("historias_clinicas")\
                    .select("*")\
                    .eq("id", paciente_id)\
                    .order("fecha", desc=True)\
                    .limit(1)\
                    .execute()
                
                if res_h.data:
                    h = res_h.data[0]
                    st.info(f"💡 Se cargaron automáticamente las medidas de la última historia ({h.get('fecha','')})")
                    
                    # Intentar extraer datos de Rx (asumiendo formato guardado anteriormente)
                    # En tu sistema, rx_od suele guardarse como string o dict.
                    # Si viene de la historia clinica pro, extraemos los valores:
                    ultima_rx_od = {
                        "Esfera": h.get("rx_od_esf", h.get("rx_od", "")), 
                        "Cilindro": h.get("rx_od_cil", ""), 
                        "Eje": h.get("rx_od_eje", ""), 
                        "Adición": h.get("rx_od_add", ""),
                        "A.V.": h.get("rx_av_lej_od", "")
                    }
                    ultima_rx_oi = {
                        "Esfera": h.get("rx_oi_esf", h.get("rx_oi", "")), 
                        "Cilindro": h.get("rx_oi_cil", ""), 
                        "Eje": h.get("rx_oi_eje", ""), 
                        "Adición": h.get("rx_oi_add", ""),
                        "A.V.": h.get("rx_av_lej_oi", "")
                    }
            except:
                pass

        st.divider()

        # FORMULARIO TIPO HISTORIA CLÍNICA (CON VALORES PRE-CARGADOS)
        st.markdown("<div class='section-title'>📋 Cuadro de Medidas (Receta)</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### 👁️ Ojo Derecho (OD)")
            od_esf = st.text_input("Esfera (OD)", value=str(ultima_rx_od["Esfera"]), placeholder="ej: -1.25", key="od_esf_n")
            od_cil = st.text_input("Cilindro (OD)", value=str(ultima_rx_od["Cilindro"]), placeholder="ej: -0.50", key="od_cil_n")
            od_eje = st.text_input("Eje (OD)", value=str(ultima_rx_od["Eje"]), placeholder="ej: 180", key="od_eje_n")
            od_add = st.text_input("Adición (OD)", value=str(ultima_rx_od["Adición"]), placeholder="ej: +2.00", key="od_add_n")
            od_av  = st.text_input("A.V. (OD)", value=str(ultima_rx_od["A.V."]), placeholder="ej: 20/20", key="od_av_n")

        with c2:
            st.markdown("### 👁️ Ojo Izquierdo (OI)")
            oi_esf = st.text_input("Esfera (OI)", value=str(ultima_rx_oi["Esfera"]), placeholder="ej: -1.00", key="oi_esf_n")
            oi_cil = st.text_input("Cilindro (OI)", value=str(ultima_rx_oi["Cilindro"]), placeholder="ej: -0.75", key="oi_cil_n")
            oi_eje = st.text_input("Eje (OI)", value=str(ultima_rx_oi["Eje"]), placeholder="ej: 170", key="oi_eje_n")
            oi_add = st.text_input("Adición (OI)", value=str(ultima_rx_oi["Adición"]), placeholder="ej: +2.00", key="oi_add_n")
            oi_av  = st.text_input("A.V. (OI)", value=str(ultima_rx_oi["A.V."]), placeholder="ej: 20/25", key="oi_av_n")

        st.divider()
        st.markdown("<div class='section-title'>🔬 Detalles Técnicos</div>", unsafe_allow_html=True)
        
        d1, d2, d3 = st.columns(3)
        dip = d1.text_input("D.I.P. (Distancia Interpupilar)", placeholder="62/60")
        altura = d2.text_input("Altura Focal", placeholder="18 mm")
        tipo_lente = d3.selectbox("Tipo de Lente", ["Monofocal", "Bifocal", "Progresivo", "Lente de Contacto"], key="tipo_lente_n")

        m1, m2 = st.columns(2)
        material = m1.multiselect("Material", ["CR-39", "Policarbonato", "Alto Índice", "Transitions", "Photogray"], key="mat_n")
        protecciones = m2.multiselect("Tratamientos", ["Antirreflejo", "Blue Defense", "Hidrofóbico", "Tinte"], key="prot_n")

        observaciones = st.text_area("Instrucciones para el Laboratorio", placeholder="Ej: Montar en armazón del paciente, biselado fino...")

        if st.button("💾 GUARDAR Y GENERAR ORDEN", type="primary", use_container_width=True):
            if not paciente_id:
                st.error("⚠️ Debes seleccionar un paciente.")
            else:
                nueva_orden = {
                    "paciente_id": paciente_id,
                    "paciente_nombre": pacientes_nombres[paciente_id],
                    "receta_od": {"Esf": od_esf, "Cil": od_cil, "Eje": od_eje, "Add": od_add, "AV": od_av},
                    "receta_oi": {"Esf": oi_esf, "Cil": oi_cil, "Eje": oi_eje, "Add": oi_add, "AV": oi_av},
                    "dip": dip,
                    "altura": altura,
                    "tipo_lente": tipo_lente,
                    "material": ", ".join(material),
                    "protecciones": ", ".join(protecciones),
                    "observaciones": observaciones,
                    "estado": "Pendiente",
                    "sucursal": st.session_state.get("sucursal_activa", "Matriz"),
                    "creado_por": st.session_state.get("user_login", "admin"),
                    "creado_el": datetime.now().isoformat()
                }
                
                try:
                    supabase.table("ordenes_trabajo").insert(nueva_orden).execute()
                    st.success(f"✅ Orden para {pacientes_nombres[paciente_id]} guardada exitosamente.")
                    registrar_auditoria("Nueva Orden", "Trabajos", f"Orden técnica para {pacientes_nombres[paciente_id]}", st.session_state.user_login)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    with tab_historial:
        st.markdown("<div class='section-title'>🔍 Buscador de Órdenes Técnicas</div>", unsafe_allow_html=True)
        
        busqueda = st.text_input("Buscar por nombre del paciente:", placeholder="Ej: Juan Pérez...")
        
        df_ord = cargar_ordenes_trabajo(st.session_state.get("sucursal_activa"))
        
        if not df_ord.empty:
            if busqueda:
                df_ord = df_ord[df_ord["paciente_nombre"].str.contains(busqueda, case=False, na=False)]
            
            for _, row in df_ord.iterrows():
                with st.expander(f"📄 Orden #{row['id']} - {row['paciente_nombre']} ({row['creado_el'][:10]})"):
                    col1, col2 = st.columns(2)
                    
                    # Mostrar receta guardada
                    rod = row.get("receta_od", {})
                    roi = row.get("receta_oi", {})
                    
                    col1.markdown(f"**OD:** Esf: {rod.get('Esf','')} | Cil: {rod.get('Cil','')} | Eje: {rod.get('Eje','')}")
                    col2.markdown(f"**OI:** Esf: {roi.get('Esf','')} | Cil: {roi.get('Cil','')} | Eje: {roi.get('Eje','')}")
                    
                    st.markdown(f"**Material:** {row.get('material','—')} | **Tratamientos:** {row.get('protecciones','—')}")
                    st.info(f"Estado: **{row['estado']}** | Sucursal: {row['sucursal']}")
        else:
            st.info("No hay órdenes registradas aún.")
