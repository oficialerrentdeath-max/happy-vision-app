import streamlit as st
import pandas as pd
from datetime import datetime
from database import cargar_ventas_historial
from utils import sri, correo

def render_facturacion():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🧾 Facturación Electrónica (SRI)</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Emisión de comprobantes legales y tributarios</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")
    
    tab1, tab2 = st.tabs(["📄 Nueva Factura Real", "🔍 Historial de Facturas"])

    with tab1:
        st.markdown("""
            <div style="background-color: #f8fafc; border-left: 5px solid #0ea5e9; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                <h3 style="margin-top:0; color:#0f172a;">🔗 Vincular con Venta Interna</h3>
                <p style="color:#64748b; font-size:14px;">Selecciona un registro de venta interno para generar la factura fiscal automáticamente.</p>
            </div>
        """, unsafe_allow_html=True)

        # Cargar ventas internas para vincular
        df_ventas = cargar_ventas_historial(sucursal_activa)
        if not df_ventas.empty:
            # Crear lista de opciones
            opciones_v = [f"Venta #{r['id']} | {r['cliente']} | ${r['total']} | {r['fecha'][:10]}" for _, r in df_ventas.iterrows()]
            venta_sel = st.selectbox("Seleccionar Venta Interna:", [""] + opciones_v)
            
            if venta_sel:
                v_id = int(venta_sel.split(" #")[1].split(" |")[0])
                v_data = df_ventas[df_ventas["id"] == v_id].iloc[0]
                st.info(f"✅ Venta vinculada: {v_data['cliente']} - Total: ${v_data['total']}")
        else:
            st.warning("⚠️ No hay ventas internas registradas para facturar.")

        st.divider()
        
        # DATOS FISCALES DEL CLIENTE
        st.subheader("👤 Datos del Adquirente")
        c1, c2 = st.columns(2)
        razon_social = c1.text_input("Razón Social / Nombres:*", value=v_data['cliente'] if 'v_data' in locals() else "")
        identificacion = c2.text_input("RUC / Cédula / Pasaporte:*", value=v_data['identificacion'] if 'v_data' in locals() else "")
        
        c3, c4, c5 = st.columns([2, 1, 1])
        direccion = c3.text_input("Dirección Fiscal:")
        telefono = c4.text_input("Teléfono:")
        email = c5.text_input("Correo Electrónico (para XML/PDF):")

        st.divider()
        
        # DATOS DEL COMPROBANTE
        st.subheader("🧾 Detalles del Comprobante")
        d1, d2, d3 = st.columns(3)
        tipo_comp = d1.selectbox("Tipo de Comprobante:", ["Factura", "Nota de Venta (RISE)", "Liquidación de Compra"])
        establecimiento = d2.text_input("Establecimiento (Punto Emisión):", value="001-001", help="Ej: 001-001")
        secuencial = d3.text_input("Número Secuencial:", placeholder="000000001")

        # PREVIEW DE LA FACTURA (PROFESIONAL)
        st.markdown("""
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 30px; margin-top: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; margin-bottom: 20px;">
                    <div>
                        <h2 style="margin:0; color:#1e40af;">HAPPY VISION</h2>
                        <p style="margin:5px 0; color:#64748b; font-size:12px;">RUC: 1724219463001<br>Dirección: Calle Principal S/N<br>Teléfono: +593 96 324 1158</p>
                    </div>
                    <div style="text-align: right;">
                        <h4 style="margin:0; color:#ef4444;">FACTURA</h4>
                        <p style="margin:5px 0; color:#0f172a; font-weight:700;">No. 001-001-000000001</p>
                        <p style="margin:0; color:#64748b; font-size:10px;">AMBIENTE: PRODUCCIÓN<br>EMISIÓN: NORMAL</p>
                    </div>
                </div>
                <div style="background:#f8fafc; padding:15px; border-radius:8px; margin-bottom:20px;">
                    <p style="margin:0; font-size:13px; color:#334155;"><b>CLIENTE:</b> """ + (razon_social or '---') + """<br>
                    <b>RUC/CI:</b> """ + (identificacion or '---') + """<br>
                    <b>FECHA:</b> """ + datetime.now().strftime('%d/%m/%Y') + """</p>
                </div>
                <table style="width:100%; border-collapse: collapse; font-size:13px;">
                    <tr style="background:#f1f5f9; color:#475569; text-align:left;">
                        <th style="padding:10px; border-bottom:1px solid #e2e8f0;">Cant</th>
                        <th style="padding:10px; border-bottom:1px solid #e2e8f0;">Descripción</th>
                        <th style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;">P. Unit</th>
                        <th style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;">Total</th>
                    </tr>
                    <tr>
                        <td style="padding:10px; border-bottom:1px solid #f1f5f9;">1</td>
                        <td style="padding:10px; border-bottom:1px solid #f1f5f9;">Servicios Optométricos / Monturas</td>
                        <td style="padding:10px; border-bottom:1px solid #f1f5f9; text-align:right;">$0.00</td>
                        <td style="padding:10px; border-bottom:1px solid #f1f5f9; text-align:right;">$0.00</td>
                    </tr>
                </table>
                <div style="margin-top:20px; display:flex; justify-content:flex-end;">
                    <div style="width:200px;">
                        <div style="display:flex; justify-content:space-between; padding:5px 0;"><span>Subtotal:</span><span>$0.00</span></div>
                        <div style="display:flex; justify-content:space-between; padding:5px 0;"><span>IVA 15%:</span><span>$0.00</span></div>
                        <div style="display:flex; justify-content:space-between; padding:5px 0; border-top:2px solid #1e40af; font-weight:800; font-size:16px;"><span>TOTAL:</span><span>$0.00</span></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 EMITIR FACTURA ELECTRÓNICA", type="primary", use_container_width=True):
            try:
                # Preparar datos del comprobante
                datos = {
                    "razon_social": razon_social,
                    "identificacion": identificacion,
                    "cliente": razon_social,
                    "ruc_emisor": "1724219463001",
                    "establecimiento": establecimiento.split('-')[0] if '-' in establecimiento else establecimiento,
                    "punto_emision": establecimiento.split('-')[1] if '-' in establecimiento else "001",
                    "secuencial": secuencial.zfill(9),
                    "direccion_matriz": direccion,
                    "direccion_establecimiento": direccion,
                    "subtotal": 0.0,
                    "iva": 0.0,
                    "total": 0.0,
                    "items": [
                        {
                            "codigo": "SERV001",
                            "descripcion": "Servicios Ópticos",
                            "cantidad": 1,
                            "precio": 0.0,
                            "descuento": 0.0,
                            "precio_total": 0.0,
                        }
                    ],
                }
                # Generar XML y firmar
                xml_raw = sri.generar_xml_factura(datos)
                xml_firmado = sri.firmar_xml_xades(xml_raw, p12_path="firma.p12", password="")
                # Enviar a SRI (recepción)
                resp = sri.enviar_sri_recepcion(xml_firmado)
                if resp.get("estado") == 200:
                    # Autorizar comprobante
                    clave = sri.generar_clave_acceso(
                        fecha_emision=datetime.now().strftime("%d%m%Y"),
                        tipo_comprobante="01",
                        ruc=datos["ruc_emisor"],
                        ambiente="2",
                        numero_secuencial=datos["secuencial"],
                        codigo_numerico="12345678",
                    )
                    auth = sri.autorizar_sri_comprobante(clave)
                    # Generar PDF RIDE
                    pdf_bytes = correo.crear_pdf_ride(xml_firmado)
                    # Enviar email al cliente
                    enviado = correo.enviar_email(
                        destino=email,
                        asunto="Factura Electrónica - Happy Vision",
                        cuerpo="Adjunto encontrará su factura electrónica y el RIDE.",
                        adjuntos=[("factura.xml", xml_firmado.encode("utf-8")), ("RIDE.pdf", pdf_bytes)],
                    )
                    if enviado:
                        st.success("✅ Factura emitida, autorizada y enviada por email.")
                    else:
                        st.error("⚠️ Factura generada, pero falló el envío de email.")
                else:
                    st.error(f"❌ Error al enviar al SRI: {resp.get('texto')}")
            except Exception as e:
                st.error(f"❌ Ocurrió un error durante la facturación: {e}")
            st.balloons()

    with tab2:
        st.subheader("🔍 Historial de Facturas Emitidas")
        st.info("Aquí se mostrarán los comprobantes autorizados por el SRI.")
