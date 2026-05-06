import streamlit as st
import pandas as pd
from datetime import datetime
from database import registrar_venta_directa, registrar_pago_saldo, cargar_inventario, cargar_ordenes_trabajo

def render_ventas():
    # ── ESTILOS CSS PARA ESTILO FACTURA ──
    st.markdown("""
        <style>
        .invoice-box {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .invoice-header {
            background-color: #00458e; /* Azul SRI */
            color: white;
            padding: 8px 15px;
            font-weight: 600;
            font-size: 16px;
        }
        .invoice-body {
            padding: 15px;
        }
        .stButton button {
            border-radius: 4px !important;
        }
        .total-box {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            padding: 10px;
        }
        .total-row {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .total-row:last-child {
            border-bottom: none;
            font-weight: bold;
            font-size: 1.1em;
            color: #00458e;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🧾 Facturación y Ventas</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Emisión de comprobantes y registro de ventas</p>
        </div>
    """, unsafe_allow_html=True)

    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")
    
    # Inicializar carrito si no existe
    if "carrito_ventas" not in st.session_state:
        st.session_state.carrito_ventas = []

    tab1, tab2 = st.tabs(["🛒 Nueva Venta / Factura", "💰 Cobro de Saldos"])

    with tab1:
        # 1. SECCIÓN ADQUIRENTE
        st.markdown('<div class="invoice-box"><div class="invoice-header">Adquirente</div></div>', unsafe_allow_html=True)
        with st.container():
            c1, c2, c3 = st.columns([1, 1, 2])
            identificacion = c1.text_input("Identificación:*", placeholder="RUC / Cédula")
            tipo_id = c2.selectbox("Tipo identificación:*", ["Cédula", "RUC", "Pasaporte", "Consumidor Final"])
            razon_social = c3.text_input("Razón social / Nombres:*", placeholder="Nombre completo del cliente")
            
            c4, c5, c6 = st.columns([2, 1, 1])
            direccion = c4.text_input("Dirección:", placeholder="Av. Principal y Calle Secundaria")
            telefono = c5.text_input("Teléfono:", placeholder="09XXXXXXXX")
            email = c6.text_input("Correo electrónico:*", placeholder="ejemplo@correo.com")

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. SECCIÓN PRODUCTOS
        st.markdown('<div class="invoice-box"><div class="invoice-header">Detalle de Productos</div></div>', unsafe_allow_html=True)
        
        # Buscador de productos
        df_inv = cargar_inventario(sucursal_activa)
        if not df_inv.empty:
            # Crear lista de opciones para el buscador
            opciones_inv = [f"{row['codigo']} | {row['nombre']} (${row['precio_venta']})" for _, row in df_inv.iterrows()]
            prod_sel = st.selectbox("🔍 Buscar producto en inventario (Código o Nombre):", [""] + opciones_inv)
            
            if prod_sel:
                cod_sel = prod_sel.split(" | ")[0]
                producto = df_inv[df_inv["codigo"] == cod_sel].iloc[0]
                
                # Botón para añadir al carrito
                if st.button(f"➕ Añadir {producto['nombre']} al detalle", use_container_width=True):
                    # Verificar si ya está en el carrito para aumentar cantidad
                    existe = False
                    for item in st.session_state.carrito_ventas:
                        if item["id_ref"] == producto["id"]:
                            item["cantidad"] += 1
                            item["total"] = item["cantidad"] * item["precio"]
                            existe = True
                            break
                    
                    if not existe:
                        st.session_state.carrito_ventas.append({
                            "id_ref": producto["id"],
                            "codigo": producto["codigo"],
                            "descripcion": producto["nombre"],
                            "cantidad": 1,
                            "precio": float(producto["precio_venta"]),
                            "descuento": 0.0,
                            "total": float(producto["precio_venta"]),
                            "iva_tipo": "15%" # Por defecto 15% en Ecuador actualmente
                        })
                    st.toast(f"Añadido: {producto['nombre']}")
                    st.rerun()

        # Tabla de Detalles (Simulada con columnas)
        if st.session_state.carrito_ventas:
            st.markdown("<hr>", unsafe_allow_html=True)
            # Encabezados de tabla
            th1, th2, th3, th4, th5, th6 = st.columns([1, 4, 1.5, 1, 1.5, 0.5])
            th1.markdown("**Cant.**")
            th2.markdown("**Descripción**")
            th3.markdown("**P. Unitario**")
            th4.markdown("**Desc.**")
            th5.markdown("**V. Total**")
            th6.markdown("")

            for idx, item in enumerate(st.session_state.carrito_ventas):
                r1, r2, r3, r4, r5, r6 = st.columns([1, 4, 1.5, 1, 1.5, 0.5])
                
                # Cantidad editable
                new_cant = r1.number_input("", min_value=1, value=item["cantidad"], key=f"cant_{idx}", label_visibility="collapsed")
                if new_cant != item["cantidad"]:
                    item["cantidad"] = new_cant
                    item["total"] = (item["cantidad"] * item["precio"]) - item["descuento"]
                    st.rerun()
                
                r2.write(f"{item['codigo']} - {item['descripcion']}")
                r3.write(f"${item['precio']:.2f}")
                
                # Descuento editable
                new_desc = r4.number_input("", min_value=0.0, value=item["descuento"], key=f"desc_{idx}", label_visibility="collapsed")
                if new_desc != item["descuento"]:
                    item["descuento"] = new_desc
                    item["total"] = (item["cantidad"] * item["precio"]) - item["descuento"]
                    st.rerun()
                
                r5.write(f"**${item['total']:.2f}**")
                
                if r6.button("🗑️", key=f"del_{idx}"):
                    st.session_state.carrito_ventas.pop(idx)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. SECCIÓN PAGOS Y TOTALES
        if st.session_state.carrito_ventas:
            col_pago, col_totales = st.columns([1.5, 1])
            
            with col_pago:
                st.markdown('<div class="invoice-box"><div class="invoice-header">Formas de Pago</div></div>', unsafe_allow_html=True)
                metodo_pago = st.radio("Seleccione el método:", ["Efectivo", "Transferencia", "Tarjeta de Débito", "Tarjeta de Crédito"], horizontal=True)
                abono = st.number_input("Monto Recibido / Abono ($):", min_value=0.0, value=sum(i["total"] for i in st.session_state.carrito_ventas))
            
            with col_totales:
                st.markdown('<div class="invoice-box"><div class="invoice-header">Totales</div></div>', unsafe_allow_html=True)
                
                subtotal = sum(i["cantidad"] * i["precio"] for i in st.session_state.carrito_ventas)
                total_descuento = sum(i["descuento"] for i in st.session_state.carrito_ventas)
                # Cálculo de IVA (Simplificado: 15% sobre el subtotal con descuento)
                # Nota: En una factura real, esto se calcula por item (IVA 0% o 15%)
                iva_valor = (subtotal - total_descuento) * 0.15
                total_final = (subtotal - total_descuento) + iva_valor
                
                st.markdown(f"""
                    <div class="total-box">
                        <div class="total-row"><span>Subtotal sin impuestos:</span><span>${subtotal:.2f}</span></div>
                        <div class="total-row"><span>Descuento total:</span><span>${total_descuento:.2f}</span></div>
                        <div class="total-row"><span>IVA 15%:</span><span>${iva_valor:.2f}</span></div>
                        <div class="total-row"><span>VALOR A PAGAR:</span><span>${total_final:.2f}</span></div>
                    </div>
                """, unsafe_allow_html=True)
                
                saldo_pendiente = max(0.0, total_final - abono)
                if saldo_pendiente > 0:
                    st.warning(f"Saldo pendiente: ${saldo_pendiente:.2f}")

                if st.button("✅ FINALIZAR Y REGISTRAR VENTA", type="primary", use_container_width=True):
                    if not razon_social or not identificacion:
                        st.error("Por favor complete los datos del cliente.")
                    else:
                        # Preparar datos para DB
                        venta_data = {
                            "cliente": razon_social,
                            "identificacion": identificacion,
                            "direccion": direccion,
                            "telefono": telefono,
                            "email": email,
                            "total": total_final,
                            "abono": abono,
                            "saldo": saldo_pendiente,
                            "metodo_pago": metodo_pago,
                            "sucursal": sucursal_activa,
                            "detalles": st.session_state.carrito_ventas,
                            "fecha": datetime.now().isoformat()
                        }
                        
                        # Guardar y Descontar Stock
                        from database import registrar_venta_directa
                        res = registrar_venta_directa(venta_data)
                        
                        if res:
                            st.success("¡Venta registrada con éxito!")
                            # Limpiar carrito
                            st.session_state.carrito_ventas = []
                            st.balloons()
                            st.rerun()

        else:
            st.info("Añada productos para comenzar la factura.")

    # ── TAB 2: COBRO DE SALDOS (MANTENER LÓGICA EXISTENTE PERO MÁS LIMPIA) ──
    with tab2:
        st.subheader("💵 Órdenes con Saldo Pendiente")
        df_ord = cargar_ordenes_trabajo(sucursal_activa)
        if df_ord.empty:
            st.info("No hay órdenes pendientes en esta sucursal.")
        else:
            # Filtrar solo las que tienen saldo > 0
            # Nota: El dataframe de cargar_ordenes_trabajo puede variar su estructura según database.py
            # Asumimos que tiene columna 'saldo'
            if "saldo" in df_ord.columns:
                df_pend = df_ord[df_ord["saldo"] > 0]
                if df_pend.empty:
                    st.success("🎉 ¡Todas las órdenes están pagadas!")
                else:
                    for _, ord in df_pend.iterrows():
                        with st.expander(f"Orden #{ord['id']} - {ord['paciente_nombre']} (Saldo: ${float(ord['saldo']):.2f})"):
                            c1, c2 = st.columns(2)
                            monto_pago = c1.number_input("Monto a cobrar ($)", min_value=0.1, max_value=float(ord['saldo']), value=float(ord['saldo']), key=f"monto_{ord['id']}")
                            met_pago = c2.selectbox("Método", ["Efectivo", "Tarjeta", "Transferencia"], key=f"met_{ord['id']}")
                            
                            if st.button(f"Confirmar Pago", key=f"btn_pago_{ord['id']}", type="primary"):
                                from database import registrar_pago_saldo
                                exito = registrar_pago_saldo(ord['id'], monto_pago, met_pago, st.session_state.user_login, sucursal_activa)
                                if exito:
                                    st.success(f"Cobro registrado para la orden #{ord['id']}")
                                    st.rerun()
            else:
                st.error("Error al cargar saldos. Verifique la estructura de la tabla.")
