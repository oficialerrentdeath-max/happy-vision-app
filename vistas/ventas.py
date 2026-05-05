import streamlit as st
import pandas as pd
from datetime import datetime
from database import registrar_venta_directa, registrar_pago_saldo, cargar_inventario, cargar_ordenes_trabajo

def render_ventas():
    st.markdown("""
        <div class="page-header">
            <h1 style='margin:0; color:#1e293b;'>🛒 Punto de Venta (Ventas)</h1>
            <p style='margin:5px 0 0 0; color:#64748b;'>Venta directa de accesorios, líquidos y cobro de saldos pendientes</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🛍️ Venta Directa", "💰 Cobro de Saldos"])
    sucursal_activa = st.session_state.get("sucursal_activa", "Matriz")

    # ── VENTA DIRECTA ──────────────────────────────────────────
    with tab1:
        col_inv, col_cart = st.columns([2, 1])
        
        # Carrito en session_state
        if "cart" not in st.session_state: st.session_state.cart = []
        
        with col_inv:
            st.subheader("📦 Productos en Stock")
            df_inv = cargar_inventario(sucursal_activa)
            if df_inv.empty:
                st.warning("No hay productos en el inventario para esta sucursal.")
            else:
                # Buscador de productos
                busc_prod = st.text_input("🔍 Buscar producto...", placeholder="Nombre del armazón, líquido, etc.")
                df_f = df_inv[df_inv["nombre"].str.contains(busc_prod, case=False)] if busc_prod else df_inv
                
                for _, prod in df_f.head(10).iterrows():
                    with st.container():
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{prod['nombre']}**\n<small>{prod['categoria']} | Stock: {prod['stock']}</small>", unsafe_allow_html=True)
                        c2.markdown(f"**${float(prod['precio_venta']):.2f}**")
                        if c3.button("➕", key=f"add_{prod['id']}"):
                            if prod['stock'] > 0:
                                st.session_state.cart.append({"id": prod['id'], "nombre": prod['nombre'], "precio": float(prod['precio_venta'])})
                                st.toast(f"Añadido: {prod['nombre']}")
                            else:
                                st.error("Sin stock")

        with col_cart:
            st.subheader("🛒 Carrito")
            if not st.session_state.cart:
                st.info("El carrito está vacío.")
            else:
                total = 0
                for i, item in enumerate(st.session_state.cart):
                    cc1, cc2 = st.columns([4, 1])
                    cc1.write(f"{item['nombre']} - ${item['precio']:.2f}")
                    if cc2.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                    total += item['precio']
                
                st.markdown("---")
                st.markdown(f"### Total: ${total:.2f}")
                
                with st.form("checkout_form"):
                    cliente = st.text_input("Nombre del Cliente", value="Consumidor Final")
                    metodo = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia"])
                    if st.form_submit_button("✅ Finalizar Venta", use_container_width=True, type="primary"):
                        if total > 0:
                            venta_data = {
                                "fecha": datetime.now().isoformat(),
                                "cliente": cliente,
                                "total": total,
                                "metodo_pago": metodo,
                                "sucursal": sucursal_activa,
                                "vendedor": st.session_state.user_login,
                                "productos": st.session_state.cart
                            }
                            res = registrar_venta_directa(venta_data)
                            if res:
                                st.success("¡Venta realizada con éxito!")
                                st.session_state.cart = []
                                st.rerun()
                        else:
                            st.error("El carrito está vacío.")

    # ── COBRO DE SALDOS ────────────────────────────────────────
    with tab2:
        st.subheader("💵 Órdenes con Saldo Pendiente")
        df_ord = cargar_ordenes_trabajo(sucursal_activa)
        if df_ord.empty:
            st.info("No hay órdenes pendientes en esta sucursal.")
        else:
            df_pend = df_ord[df_ord["saldo"] > 0]
            if df_pend.empty:
                st.success("🎉 ¡Todas las órdenes están pagadas!")
            else:
                for _, ord in df_pend.iterrows():
                    with st.expander(f"Orden #{ord['id']} - {ord['paciente_nombre']} (Saldo: ${float(ord['saldo']):.2f})"):
                        c1, c2 = st.columns(2)
                        monto_pago = c1.number_input("Monto a cobrar ($)", min_value=0.1, max_value=float(ord['saldo']), value=float(ord['saldo']), key=f"monto_{ord['id']}")
                        metodo_pago = c2.selectbox("Método", ["Efectivo", "Tarjeta", "Transferencia"], key=f"met_{ord['id']}")
                        
                        if st.button(f"Confirmar Cobro de ${monto_pago:.2f}", key=f"btn_pago_{ord['id']}", type="primary"):
                            exito = registrar_pago_saldo(ord['id'], monto_pago, metodo_pago, st.session_state.user_login, sucursal_activa)
                            if exito:
                                st.success(f"Pago registrado para la orden #{ord['id']}")
                                st.rerun()
