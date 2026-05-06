import streamlit as st
import pandas as pd
import re
from datetime import datetime
from database import supabase, registrar_auditoria, cargar_ordenes_trabajo

def parse_rx_string(rx_str):
    if not rx_str or not isinstance(rx_str, str) or rx_str.strip() == "":
        return {"Esfera": "", "Cilindro": "", "Eje": ""}
    rx_str = rx_str.replace(",", ".").replace("X", "x").strip()
    parts = re.findall(r'[+-]?\d*\.?\d+', rx_str)
    res = {"Esfera": "", "Cilindro": "", "Eje": ""}
    if len(parts) >= 1: res["Esfera"] = parts[0]
    if len(parts) >= 2: res["Cilindro"] = parts[1]
    if len(parts) >= 3: res["Eje"] = parts[2]
    return res

def render_nueva_orden():
    st.markdown("""<div class="page-header"><h1>📝 Gestión de Órdenes</h1><p>Administra las recetas técnicas</p></div>""", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Nueva Orden", "🔍 Historial"])

    with tab1:
        st.markdown("<div class='section-title'>👤 Datos del Paciente</div>", unsafe_allow_html=True)
        pacientes_dict = {}
        try:
            # BUSCAR EN LA TABLA DE PACIENTES REAL (No en historias)
            res_p = supabase.table("pacientes").select("id, nombres, apellidos, identificacion").execute()
            if res_p.data:
                df_p = pd.DataFrame(res_p.data)
                df_p["nombre_completo"] = df_p["nombres"] + " " + df_p["apellidos"]
                filtro = st.text_input("🔍 Buscar Paciente (Nombre o Cédula):", placeholder="Escriba aquí...")
                if filtro:
                    df_p = df_p[df_p["nombre_completo"].str.contains(filtro, case=False) | df_p["identificacion"].str.contains(filtro)]
                
                if not df_p.empty:
                    pacientes_dict = {row["id"]: f"{row['nombre_completo']} ({row['identificacion']})" for _, row in df_p.iterrows()}
                    pacientes_nombres = {row["id"]: row["nombre_completo"] for _, row in df_p.iterrows()}
        except Exception as e:
            st.error(f"Error cargando pacientes: {e}")

        paciente_id = st.selectbox("Confirmar Paciente:", options=list(pacientes_dict.keys()), format_func=lambda x: pacientes_dict.get(x, ""))
        
        p_key = f"p_{paciente_id}" if paciente_id else "p_none"
        rx_od_v = {"Esfera": "", "Cilindro": "", "Eje": "", "Adición": "", "A.V.": ""}
        rx_oi_v = {"Esfera": "", "Cilindro": "", "Eje": "", "Adición": "", "A.V.": ""}
        dip_v = ""

        if paciente_id:
            try:
                # BUSCAR LA ÚLTIMA HISTORIA USANDO EL ID DEL PACIENTE
                res_h = supabase.table("historias_clinicas").select("*").eq("paciente_id", paciente_id).order("fecha", desc=True).limit(1).execute()
                if res_h.data:
                    h = res_h.data[0]
                    parsed_od = parse_rx_string(h.get("rx_od", ""))
                    parsed_oi = parse_rx_string(h.get("rx_oi", ""))
                    rx_od_v.update(parsed_od); rx_oi_v.update(parsed_oi)
                    rx_od_v["A.V."] = h.get("rx_av_lej_od", ""); rx_oi_v["A.V."] = h.get("rx_av_lej_oi", "")
                    rx_od_v["Adición"] = h.get("rx_add", ""); rx_oi_v["Adición"] = h.get("rx_add", "")
                    dip_v = h.get("rx_dip", "")
                    st.success("✅ Datos de la última consulta cargados.")
            except: pass

        st.divider()
        st.markdown("<div class='section-title'>📋 Cuadro de Medidas</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### OD")
            od_esf = st.text_input("Esf (OD)", value=str(rx_od_v["Esfera"]), key=f"e_od_{p_key}")
            od_cil = st.text_input("Cil (OD)", value=str(rx_od_v["Cilindro"]), key=f"c_od_{p_key}")
            od_eje = st.text_input("Eje (OD)", value=str(rx_od_v["Eje"]), key=f"j_od_{p_key}")
            od_add = st.text_input("Add (OD)", value=str(rx_od_v["Adición"]), key=f"a_od_{p_key}")
            od_av  = st.text_input("AV (OD)", value=str(rx_od_v["A.V."]), key=f"v_od_{p_key}")
        with c2:
            st.markdown("### OI")
            oi_esf = st.text_input("Esf (OI)", value=str(rx_oi_v["Esfera"]), key=f"e_oi_{p_key}")
            oi_cil = st.text_input("Cil (OI)", value=str(rx_oi_v["Cilindro"]), key=f"c_oi_{p_key}")
            oi_eje = st.text_input("Eje (OI)", value=str(rx_oi_v["Eje"]), key=f"j_oi_{p_key}")
            oi_add = st.text_input("Add (OI)", value=str(rx_oi_v["Adición"]), key=f"a_oi_{p_key}")
            oi_av  = st.text_input("AV (OI)", value=str(rx_oi_v["A.V."]), key=f"v_oi_{p_key}")

        st.divider()
        d1, d2, d3 = st.columns(3)
        dip = d1.text_input("D.I.P.", value=str(dip_v), key=f"dip_{p_key}")
        altura = d2.text_input("Altura", key=f"alt_{p_key}")
        tipo = d3.selectbox("Lente", ["Monofocal", "Bifocal", "Progresivo"], key=f"t_{p_key}")
        
        obs = st.text_area("Observaciones", key=f"obs_{p_key}")

        if st.button("💾 GUARDAR ORDEN", type="primary", use_container_width=True):
            if not paciente_id: st.error("⚠️ Elija un paciente.")
            else:
                nueva = {
                    "paciente_id": paciente_id,
                    "paciente_nombre": pacientes_nombres[paciente_id],
                    "receta_od": {"Esf": od_esf, "Cil": od_cil, "Eje": od_eje, "Add": od_add, "AV": od_av},
                    "receta_oi": {"Esf": oi_esf, "Cil": oi_cil, "Eje": oi_eje, "Add": oi_add, "AV": oi_av},
                    "dip": dip, "altura": altura, "tipo_lente": tipo, "observaciones": obs,
                    "estado": "Pendiente", "sucursal": st.session_state.get("sucursal_activa"),
                    "creado_por": st.session_state.get("user_login"), "creado_el": datetime.now().isoformat()
                }
                try:
                    supabase.table("ordenes_trabajo").insert(nueva).execute()
                    st.success("✅ Orden guardada."); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    with tab2:
        df_ord = cargar_ordenes_trabajo(st.session_state.get("sucursal_activa"))
        if not df_ord.empty:
            for _, r in df_ord.iterrows():
                with st.expander(f"📄 #{r['id']} - {r['paciente_nombre']}"):
                    st.write(f"Estado: {r['estado']}")
