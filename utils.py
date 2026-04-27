"""
╔══════════════════════════════════════════════════════════════╗
║  HAPPY VISION · UTILIDADES Y BACKEND                         ║
║  Funciones de datos, persistencia, PDF y WhatsApp            ║
╚══════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import random
import io
import json
import os
import urllib.parse
from datetime import datetime, date, timedelta
from fpdf import FPDF
import streamlit as st


# ══════════════════════════════════════════════════════════════
# GENERACIÓN DE DATOS DE PRUEBA
# ══════════════════════════════════════════════════════════════
def generate_sample_data():
    """Genera datos de prueba realistas para Happy Vision."""
    pacientes = [
        "María García", "Carlos López", "Ana Martínez", "José Rodríguez",
        "Laura Pérez", "Luis Hernández", "Carmen Torres", "Miguel Flores",
        "Sandra Ramírez", "Diego Morales", "Patricia Jiménez", "Roberto Castro",
        "Daniela Vega", "Andrés Reyes", "Valentina Cruz", "Felipe Núñez",
        "Camila Herrera", "Sebastián Ruiz", "Natalia Mendoza", "Alejandro Díaz",
    ]
    tipos_lente  = ["Monofocal", "Progresivo", "Progresivo Premium", "Filtro Azul", "Contactología"]
    laboratorios = ["Indulentes", "Pecsa/ImportVision", "Stock propio"]
    metodos_pago = ["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia"]

    precios = {
        "Monofocal":          (80,  160),
        "Progresivo":         (180, 290),
        "Progresivo Premium": (290, 520),
        "Filtro Azul":        (120, 210),
        "Contactología":      (55,  130),
    }

    random.seed(42)
    trabajos = []
    today = datetime.today()

    for i in range(60):
        days_ago  = random.randint(0, 89)
        fecha     = today - timedelta(days=days_ago)
        paciente  = random.choice(pacientes)
        tipo      = random.choice(tipos_lente)
        lab       = random.choice(laboratorios)
        metodo    = random.choice(metodos_pago)
        p_min, p_max = precios[tipo]
        precio    = round(random.uniform(p_min, p_max), 2)
        pct_abono = random.choice([0.3, 0.5, 0.7, 1.0, 1.0])
        abono     = round(min(precio * pct_abono, precio), 2)
        saldo     = round(precio - abono, 2)

        trabajos.append({
            "id":             i + 1,
            "fecha":          fecha.strftime("%Y-%m-%d"),
            "paciente":       paciente,
            "tipo_lente":     tipo,
            "laboratorio":    lab,
            "precio_total":   precio,
            "abono":          abono,
            "metodo_pago":    metodo,
            "saldo_pendiente": saldo,
            "estado":         "Pagado" if saldo < 1 else ("Parcial" if abono > 0 else "Pendiente"),
        })

    # ─── Inventario ───────────────────────────────────────────
    inventario = [
        {"id":1,  "categoria":"Armazones",  "subcategoria":"TR90",     "producto":"Armazón TR90 Negro",                      "stock":8,  "stock_min":5,  "unidad":"unid", "costo":15.0, "precio":35.0},
        {"id":2,  "categoria":"Armazones",  "subcategoria":"TR90",     "producto":"Armazón TR90 Azul",                       "stock":3,  "stock_min":5,  "unidad":"unid", "costo":15.0, "precio":35.0},
        {"id":3,  "categoria":"Armazones",  "subcategoria":"TR90",     "producto":"Armazón TR90 Rojo",                       "stock":6,  "stock_min":4,  "unidad":"unid", "costo":14.0, "precio":32.0},
        {"id":4,  "categoria":"Armazones",  "subcategoria":"TR90",     "producto":"Armazón TR90 Gris",                       "stock":2,  "stock_min":5,  "unidad":"unid", "costo":15.0, "precio":35.0},
        {"id":5,  "categoria":"Armazones",  "subcategoria":"Acetato",  "producto":"Armazón Acetato Havana",                  "stock":10, "stock_min":4,  "unidad":"unid", "costo":20.0, "precio":55.0},
        {"id":6,  "categoria":"Armazones",  "subcategoria":"Acetato",  "producto":"Armazón Acetato Negro Mate",              "stock":7,  "stock_min":4,  "unidad":"unid", "costo":18.0, "precio":48.0},
        {"id":7,  "categoria":"Armazones",  "subcategoria":"Acetato",  "producto":"Armazón Acetato Carey",                   "stock":1,  "stock_min":3,  "unidad":"unid", "costo":22.0, "precio":60.0},
        {"id":8,  "categoria":"Armazones",  "subcategoria":"Acetato",  "producto":"Armazón Acetato Transparente",            "stock":5,  "stock_min":3,  "unidad":"unid", "costo":21.0, "precio":55.0},
        {"id":9,  "categoria":"Plaquetas",  "subcategoria":"Suaves",   "producto":"Plaqueta suave transparente (par)",       "stock":25, "stock_min":10, "unidad":"par",  "costo":0.50, "precio":2.0},
        {"id":10, "categoria":"Plaquetas",  "subcategoria":"Suaves",   "producto":"Plaqueta suave blanca (par)",             "stock":8,  "stock_min":10, "unidad":"par",  "costo":0.50, "precio":2.0},
        {"id":11, "categoria":"Plaquetas",  "subcategoria":"Suaves",   "producto":"Plaqueta suave nose pad (par)",           "stock":14, "stock_min":8,  "unidad":"par",  "costo":0.60, "precio":2.5},
        {"id":12, "categoria":"Plaquetas",  "subcategoria":"Silicona", "producto":"Plaqueta silicona anti-alérgica (par)",   "stock":30, "stock_min":10, "unidad":"par",  "costo":0.80, "precio":3.5},
        {"id":13, "categoria":"Plaquetas",  "subcategoria":"Silicona", "producto":"Plaqueta silicona con tornillo (par)",    "stock":4,  "stock_min":8,  "unidad":"par",  "costo":1.00, "precio":4.0},
        {"id":14, "categoria":"Plaquetas",  "subcategoria":"Silicona", "producto":"Plaqueta silicona oval larga (par)",      "stock":6,  "stock_min":8,  "unidad":"par",  "costo":0.90, "precio":3.5},
        {"id":15, "categoria":"Líquidos",   "subcategoria":"Limpieza", "producto":"Spray limpiador lentes 120ml",            "stock":12, "stock_min":6,  "unidad":"frasco","costo":3.50,"precio":8.0},
        {"id":16, "categoria":"Líquidos",   "subcategoria":"Limpieza", "producto":"Spray limpiador lentes 250ml",            "stock":2,  "stock_min":4,  "unidad":"frasco","costo":5.50,"precio":12.0},
        {"id":17, "categoria":"Líquidos",   "subcategoria":"Limpieza", "producto":"Solución limpiadora ultrasónica 500ml",   "stock":5,  "stock_min":3,  "unidad":"frasco","costo":8.00,"precio":18.0},
        {"id":18, "categoria":"Líquidos",   "subcategoria":"Limpieza", "producto":"Paño microfibra premium",                 "stock":3,  "stock_min":15, "unidad":"unid", "costo":0.80, "precio":3.0},
        {"id":19, "categoria":"Líquidos",   "subcategoria":"Limpieza", "producto":"Toallitas húmedas lentes (caja 100)",     "stock":4,  "stock_min":3,  "unidad":"caja", "costo":4.00, "precio":9.0},
    ]

    # ─── Gastos Operativos ────────────────────────────────────
    random.seed(7)
    gastos = []
    conceptos = [
        ("Arriendo local",        "Fijo",     800),
        ("Servicios básicos",     "Fijo",     120),
        ("Internet y teléfono",   "Fijo",      45),
        ("Salario asistente",     "Fijo",     600),
        ("Publicidad redes",      "Variable",  80),
        ("Materiales de oficina", "Variable",  30),
        ("Transporte y envíos",   "Variable",  40),
        ("Mantenimiento equipos", "Variable",   0),
    ]
    for month_offset in range(3):
        month_date = today - timedelta(days=30 * month_offset)
        mes_str = month_date.strftime("%Y-%m")
        for concepto, tipo, monto_base in conceptos:
            if monto_base > 0:
                variacion = random.uniform(0.93, 1.07)
                gastos.append({
                    "fecha":    mes_str,
                    "concepto": concepto,
                    "tipo":     tipo,
                    "monto":    round(monto_base * variacion, 2),
                })
        if random.random() > 0.4:
            gastos.append({
                "fecha":    mes_str,
                "concepto": "Mantenimiento equipos",
                "tipo":     "Variable",
                "monto":    round(random.uniform(50, 220), 2),
            })

    # ─── Pacientes y Clínicas ─────────────────────────────────
    df_p = pd.DataFrame(columns=["id", "identificacion", "nombre", "genero", "direccion", "edad", "telefono", "correo", "ocupacion"])
    df_h = pd.DataFrame(columns=[
        "id", "paciente_id", "paciente_nombre", "fecha",
        "ant_personales", "ant_familiares", "motivo", "diabetes", "hipertension", "patologia_otra", "observaciones",
        "lenso_od", "lenso_av_lej_od", "lenso_av_cer_od",
        "lenso_oi", "lenso_av_lej_oi", "lenso_av_cer_oi",
        "rx_od", "rx_av_lej_od", "rx_av_cer_od",
        "rx_oi", "rx_av_lej_oi", "rx_av_cer_oi",
        "estado_muscular", "seg_externo", "test_colores",
        "estado_refractivo", "diagnostico", "disposicion", "recomendaciones",
        "meses_proximo_control",
    ])

    return (
        pd.DataFrame(trabajos),
        pd.DataFrame(inventario),
        pd.DataFrame(gastos),
        df_p,
        df_h,
    )


# ══════════════════════════════════════════════════════════════
# PERSISTENCIA
# ══════════════════════════════════════════════════════════════
def guardar_datos():
    """Guarda los DataFrames actuales a CSV y sincroniza con Supabase."""
    from database import guardar_todos_pacientes, guardar_todas_historias
    
    if "df_pacientes" in st.session_state:
        st.session_state.df_pacientes.to_csv("pacientes.csv", index=False)
        # Sincronizar con Supabase
        guardar_todos_pacientes(st.session_state.df_pacientes)

    if "df_historias" in st.session_state:
        st.session_state.df_historias.to_csv("historias.csv", index=False)
        # Sincronizar historias con Supabase
        guardar_todas_historias(st.session_state.df_historias)

    # Nota: optometrista.json ya no es la fuente primaria si usamos Supabase para usuarios,
    # pero por compatibilidad con código antiguo lo guardamos.
    try:
        with open("optometrista.json", "w", encoding="utf-8") as f:
            json.dump({
                "opto_nombre":    st.session_state.get("opto_nombre", ""),
                "opto_registro":  st.session_state.get("opto_registro", ""),
                "opto_cargo":     st.session_state.get("opto_cargo", ""),
                "opto_direccion": st.session_state.get("opto_direccion", ""),
                "opto_telefono":  st.session_state.get("opto_telefono", ""),
            }, f)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# WHATSAPP
# ══════════════════════════════════════════════════════════════
def wa_link(numero: str, mensaje: str) -> str:
    """Genera link para abrir WhatsApp Web con un mensaje."""
    num = numero.replace(" ", "").replace("+", "").replace("-", "")
    if num.startswith("0"):
        num = "593" + num[1:]
    return f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"


def generar_msg_factura(row) -> str:
    """Genera el mensaje WhatsApp para una factura/trabajo."""
    estado = row.get('estado', '')
    return (
        f"*👁️ Happy Vision - Detalle de su Servicio*\n\n"
        f"📌 Paciente: {row.get('paciente', '')}\n"
        f"📅 Fecha: {row.get('fecha', '')}\n"
        f"🔬 Tipo de Lente: {row.get('tipo_lente', '')}\n"
        f"🏢 Laboratorio: {row.get('laboratorio', '')}\n\n"
        f"💰 Total: ${row.get('precio_total', 0):.2f}\n"
        f"✅ Abonado: ${row.get('abono', 0):.2f}\n"
        f"⏳ Saldo Pendiente: ${row.get('saldo_pendiente', 0):.2f}\n"
        f"🏷️ Estado: {estado}\n\n"
        f"Para consultas: +593 96 324 1158 | Happy Vision"
    )


def generar_msg_hc(row, paciente_info) -> str:
    """Genera el mensaje WhatsApp para una historia clínica."""
    return (
        f"*👁️ Happy Vision - Resumen de Consulta Optométrica*\n\n"
        f"👤 Paciente: {paciente_info.get('nombre', '')}\n"
        f"📅 Fecha: {row.get('fecha', '')}\n"
        f"📝 Motivo: {row.get('motivo', '')}\n\n"
        f"*Rx Final:*\n"
        f"👁️ OD: {row.get('rx_od', '')}\n"
        f"👁️ OI: {row.get('rx_oi', '')}\n\n"
        f"💡 Recomendaciones:\n{row.get('recomendaciones', '')}\n\n"
        f"Para consultas: +593 96 324 1158 | Happy Vision"
    )


def generar_msg_indicaciones(row, paciente_info) -> str:
    """Genera el mensaje WhatsApp con indicaciones médicas y tratamiento (colirios, etc.)."""
    recom = row.get('recomendaciones', '') or row.get('observaciones', '')
    if not str(recom).strip() or str(recom).strip().lower() in ('nan', 'none', ''):
        recom = 'Ver indicaciones de su optometrista.'
    control = row.get('meses_proximo_control', '')
    control_txt = f"\n📅 *Próximo control:* en {control} mes(es)." if control else ""
    return (
        f"*💊 Happy Vision - Indicaciones Médicas*\n\n"
        f"👤 Paciente: {paciente_info.get('nombre', '')}\n"
        f"📅 Consulta: {row.get('fecha', '')}\n\n"
        f"*Indicaciones / Tratamiento:*\n{recom}"
        f"{control_txt}\n\n"
        f"Consultas: +593 96 324 1158 | Happy Vision"
    )


# ══════════════════════════════════════════════════════════════
# PDF
# ══════════════════════════════════════════════════════════════
def _s(texto) -> str:
    """Convierte texto a Latin-1 seguro para fpdf (Helvetica), eliminando emojis."""
    if texto is None:
        return ""
    t = str(texto)
    # Forzar Latin-1 ignorando lo que no se pueda convertir (emojis, etc.)
    # Latin-1 soporta ñ, tildes y caracteres especiales del español
    return t.encode("latin-1", errors="ignore").decode("latin-1")


def generar_pdf_historia(row: dict, paciente_info: dict, opto: dict) -> bytes:
    """Genera el Certificado Visual PDF usando fpdf estándar."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(18, 10, 18)

    # ─ LOGO ────────────────────────────────────────────
    logo_path = None
    for cand in ["logo.png", "logo.jpg", "logo.jpeg"]:
        if os.path.exists(cand):
            logo_path = cand
            break
    if logo_path:
        try:
            watermark_path = logo_path
            try:
                from PIL import Image
                img = Image.open(logo_path).convert("RGBA")
                r, g, b, a = img.split()
                a_faded = a.point(lambda p: p * 0.10)
                img.putalpha(a_faded)
                bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                bg.paste(img, (0, 0), img)
                watermark_path = "logo_watermark_temp.png"
                bg.convert("RGB").save(watermark_path, format="PNG")
            except Exception:
                pass

            pdf.image(watermark_path, x=5, y=40, w=200)

            header_path = logo_path
            try:
                from PIL import Image, ImageChops
                img_head = Image.open(logo_path).convert("RGBA")
                bbox = img_head.split()[-1].getbbox()
                if bbox:
                    img_head = img_head.crop(bbox)
                bg_white = Image.new("RGBA", img_head.size, (255,255,255,255))
                diff = ImageChops.difference(img_head, bg_white)
                bbox2 = diff.getbbox()
                if bbox2:
                    img_head = img_head.crop(bbox2)
                final_bg = Image.new("RGBA", img_head.size, (255,255,255,255))
                final_bg.paste(img_head, (0, 0), img_head)
                header_path = "logo_header_temp.png"
                final_bg.convert("RGB").save(header_path, format="PNG")
            except Exception:
                pass

            pdf.image(header_path, x=82.5, y=3, w=45)
            pdf.set_y(30)
        except Exception:
            pdf.set_y(20)
    else:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 160, 180)
        pdf.cell(0, 10, "HAPPY VISION", ln=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "Tu optica amiga", ln=True, align="C")

    # ─ LINEA + TITULO ─────────────────
    pdf.set_draw_color(0, 160, 180)
    pdf.set_line_width(1)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "CERTIFICADO VISUAL", ln=True, align="C")
    pdf.ln(3)

    # ─ DATOS PACIENTE ──────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(22, 6, "NOMBRE:", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(81, 6, _s(str(paciente_info.get("nombre", "")).upper()), ln=False)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(18, 6, "CÉDULA:", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _s(paciente_info.get("identificacion", "")), ln=True)

    edad_display = str(paciente_info.get('edad', ''))
    fnac_raw = paciente_info.get('fecha_nacimiento', '')
    if fnac_raw:
        try:
            _fnac = date.fromisoformat(str(fnac_raw))
            _hoy = date.today()
            edad_display = str(_hoy.year - _fnac.year - ((_hoy.month, _hoy.day) < (_fnac.month, _fnac.day)))
        except Exception:
            pass

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(14, 6, "EDAD:", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(28, 6, f"{_s(edad_display)} años", ln=False)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(17, 6, "FECHA:", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(44, 6, _s(row.get("fecha", "")), ln=False)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(24, 6, "TELÉFONO:", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _s(paciente_info.get("telefono", "")), ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 6, "MOTIVO DE LA CONSULTA:", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _s(row.get("motivo", "")), ln=True)
    pdf.ln(3)

    # ─ AGUDEZA VISUAL Y TABLAS RX ──────────────────────────────────
    def _av(v):
        v = _s(v).strip()
        if not v: return " "
        if "20/" in v: return v
        return f"20/{v}"

    def print_av_double_column(sc_lej_od, sc_lej_oi, sc_cer_od, sc_cer_oi, cc_lej_od, cc_lej_oi, cc_cer_od, cc_cer_oi):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(90, 5, "AGUDEZA VISUAL S/C", ln=False)
        pdf.cell(90, 5, "AGUDEZA VISUAL C/C", ln=True)
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(90, 5, "LEJOS:", ln=False)
        pdf.cell(90, 5, "LEJOS:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(90, 5, f"O.D.: {_av(sc_lej_od)}", ln=False)
        pdf.cell(90, 5, f"O.D.: {_av(cc_lej_od)}", ln=True)
        pdf.cell(90, 5, f"O.I.: {_av(sc_lej_oi)}", ln=False)
        pdf.cell(90, 5, f"O.I.: {_av(cc_lej_oi)}", ln=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(90, 5, "CERCA:", ln=False)
        pdf.cell(90, 5, "CERCA:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(90, 5, f"O.D. {_s(sc_cer_od)}", ln=False)
        pdf.cell(90, 5, f"O.D. {_s(cc_cer_od)}", ln=True)
        pdf.cell(90, 5, f"O.I. {_s(sc_cer_oi)}", ln=False)
        pdf.cell(90, 5, f"O.I. {_s(cc_cer_oi)}", ln=True)
        pdf.ln(3)

    def draw_rx_table(titulo, od_str, oi_str, is_refraccion=False):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, _s(titulo), ln=True)
        pdf.ln(1)

        def parse_str(s):
            s_val = str(s)
            pts = s_val.split("|") if "|" in s_val else s_val.split()
            while len(pts) < 10: pts.append("")
            return [x.strip() if x.strip() != "-" else "" for x in pts]

        pod = parse_str(od_str)
        poi = parse_str(oi_str)

        pdf.set_font("Helvetica", "B", 8)
        if is_refraccion:
            hdrs = ["RX", "ESF", "CYL", "EJE", "ADD", "DNP", "ALT", "D.P.", "A/V"]
            wcol = [22, 19, 19, 19, 19, 19, 19, 19, 19]
        else:
            hdrs = ["RX", "ESF", "CYL", "EJE", "ADD"]
            wcol = [34, 35, 35, 35, 35]

        pdf.set_fill_color(240, 245, 248)
        pdf.set_draw_color(180, 190, 200)
        pdf.set_line_width(0.2)
        for i, h in enumerate(hdrs):
            pdf.cell(wcol[i], 8, h, border=1, align="C", fill=True, ln=(i==len(hdrs)-1))

        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(wcol[0], 8, "OD", border=1, align="C")
        pdf.set_font("Helvetica", "", 8)
        for i in range(1, len(hdrs)):
            pdf.cell(wcol[i], 8, pod[i-1] if (i-1) < len(pod) else "", border=1, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(wcol[0], 8, "OI", border=1, align="C")
        pdf.set_font("Helvetica", "", 8)
        for i in range(1, len(hdrs)):
            pdf.cell(wcol[i], 8, poi[i-1] if (i-1) < len(poi) else "", border=1, align="C")
        pdf.ln()
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.2)

    print_av_double_column(
        row.get("lenso_av_lej_od"), row.get("lenso_av_lej_oi"),
        row.get("lenso_av_cer_od"), row.get("lenso_av_cer_oi"),
        row.get("rx_av_lej_od"),   row.get("rx_av_lej_oi"),
        row.get("rx_av_cer_od"),   row.get("rx_av_cer_oi"),
    )
    draw_rx_table("LENSOMETRIA (RX EN USO)", row.get("lenso_od"), row.get("lenso_oi"), is_refraccion=False)
    draw_rx_table("REFRACCION (RX ACTUAL)",  row.get("rx_od"),    row.get("rx_oi"),    is_refraccion=True)
    pdf.ln(5)

    # ─ EXAMEN CLINICO ─────────────────────────────────
    def _clean(val):
        v = str(val).strip()
        if v.lower() in ("", "nan", "none", "null"): return ""
        return v

    def clinico(lbl, val):
        v = _clean(val)
        if v:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(55, 7, _s(lbl) + ":", ln=False)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, _s(v), ln=True)

    clinico("ESTADO MUSCULAR",  row.get("estado_muscular"))
    clinico("SEGMENTO EXTERNO", row.get("seg_externo"))
    clinico("TEST DE COLORES",  row.get("test_colores"))
    clinico("DIAGNOSTICO",      row.get("diagnostico"))

    lentes_val = _clean(str(row.get("necesita_lentes", "")))
    if lentes_val:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(65, 7, "PACIENTE NECESITA LENTES:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, lentes_val.upper(), ln=True)

    color_val = _clean(str(row.get("test_color", "")))
    if color_val:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(55, 7, "TEST DE COLOR:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        display_color = "SE DETECTA DALTONISMO" if "dalton" in color_val.lower() else "NORMAL"
        pdf.cell(0, 7, display_color, ln=True)

    pdf.ln(2)

    # ─ DISPOSICION / OBSERVACIONES ───────────────────────────────────
    disp_raw = row.get("disposicion", "") or row.get("recomendaciones", "")
    disp = _s(_clean(disp_raw))
    if disp:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "DISPOSICION:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, disp)
        pdf.ln(2)

    obs_raw = row.get("observaciones", "")
    obs = _s(_clean(obs_raw))
    if obs:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(42, 7, "RECOMENDACIONES:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, obs)
        pdf.ln(2)

    # ─ FIRMA Y PIE DE PÁGINA (posición dinámica) ──────────────────────
    firma_path = f"firma_{opto.get('username','')}.png"
    if opto.get("firma_base64"):
        import base64
        firma_path = "firma_temp.png"
        try:
            with open(firma_path, "wb") as f_tmp:
                f_tmp.write(base64.b64decode(opto["firma_base64"]))
        except Exception:
            pass
    elif not os.path.exists(firma_path):
        firma_path = "firma.png"

    # Espacio mínimo para firma + datos = ~35mm
    espacio_firma = 35
    y_firma_min = 257 - espacio_firma  # ~222mm
    y_actual = pdf.get_y()

    # Si el contenido es muy largo, la firma se coloca justo debajo
    y_firma = max(y_actual + 6, y_firma_min)
    # Asegurar que no se salga de la página
    if y_firma + espacio_firma > 277:
        y_firma = 277 - espacio_firma

    if os.path.exists(firma_path):
        try:
            pdf.image(firma_path, x=77, y=y_firma, w=55, h=16)
        except Exception:
            pass

    y_linea = y_firma + 17
    pdf.set_y(y_linea)
    pdf.set_draw_color(80, 80, 80)
    pdf.set_line_width(0.4)
    pdf.line(65, pdf.get_y(), 145, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 5, _s(opto.get("nombre", "")), ln=True, align="C")
    pdf.cell(0, 5, _s(opto.get("cargo", "OPTOMETRA")).upper(), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f"Reg.: {_s(opto.get('registro', ''))}  |  Tel.: {_s(opto.get('telefono', ''))}", ln=True, align="C")

    buf = io.BytesIO()
    raw = pdf.output(dest='S')
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    buf.write(raw.encode("latin-1") if isinstance(raw, str) else bytes(raw))
    return buf.getvalue()
