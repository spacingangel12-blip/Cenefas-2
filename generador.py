from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, HexColor
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))
FD   = os.path.join(BASE, 'static', 'fonts')

pdfmetrics.registerFont(TTFont('Archivo', os.path.join(FD, 'ArchivoBlack-Regular.ttf')))
pdfmetrics.registerFont(TTFont('MontB',   os.path.join(FD, 'Montserrat-Bold.ttf')))
pdfmetrics.registerFont(TTFont('MontR',   os.path.join(FD, 'Montserrat-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Passion', os.path.join(FD, 'PassionOne-Bold.ttf')))

PW   = 139.7 * mm
PH   = 215.9 * mm
HALF = PH / 2
MAR  = 12 * mm
USEW = PW - 2 * MAR

# ── Calibración para hoja preimpresa ────────────────────────────────────────
# La hoja física YA trae impresa una franja superior (naranja/roja con el
# texto "¡Siempre ahorrando, siempre contigo!") y un logo inferior derecho.
# Este PDF solo dibuja el contenido variable (tipo/marca/detalle/precio)
# encima de esa hoja, así que hay que "empujar" todo el bloque de texto
# hacia abajo lo suficiente para que no choque con la franja, y "encoger"
# la altura útil para que no choque con el logo de abajo.
#
# Ajusta estos dos valores según lo que midas en la hoja física real:
#   TOP_OFFSET    -> cuánto bajar todo el contenido (mm) para librar la franja
#   BOTTOM_OFFSET -> cuánto subir la línea de "Cód/Vigencia" (mm) para librar el logo
TOP_OFFSET    = 10 * mm   # valor de arranque, ajustar con la hoja física
BOTTOM_OFFSET = 0  * mm   # valor de arranque, ajustar con la hoja física

def sw(c, t, f, s): return c.stringWidth(t, f, s)

def fit_s(c, t, f, start, min_s, max_w):
    s = start
    while s > min_s and sw(c, t, f, s) > max_w: s -= 1
    return s

def wrap(c, txt, font, size, max_w):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if sw(c, test, font, size) <= max_w: cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def cxs(c, txt, font, size):
    return MAR + (USEW - sw(c, txt, font, size)) / 2

def hollow(c, txt, font, size, cy, max_w=None, min_s=20, offset=0.9):
    if max_w is None: max_w = USEW
    size = fit_s(c, txt, font, size, min_s, max_w)
    tx = cxs(c, txt, font, size)
    c.setFont(font, size)
    c.setFillColor(black)
    for dx in (-offset, 0, offset):
        for dy in (-offset, 0, offset):
            if dx == 0 and dy == 0: continue
            c.drawString(tx+dx, cy+dy, txt)
    c.setFillColor(white)
    c.drawString(tx, cy, txt)
    c.setFillColor(black)

def fmt_precio(val):
    try:
        f = round(float(str(val).replace(',', '')), 2)
        return f"{f:.2f}".rstrip('0').rstrip('.')
    except: return str(val).strip()

def normaliza_oferta(po):
    s = str(po).strip().upper()
    s = re.sub(r'POR\s*\$\s*', 'POR $', s)
    s = re.sub(r'%\s*AHORRO', '% DE AHORRO', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def draw_cenefa(c, base_y, row, vigencia, sin_precio=False):
    top = base_y + HALF - TOP_OFFSET

    tipo   = str(row.get('TIPO',   '') or '').strip()
    marca  = str(row.get('MARCA',  '') or '').strip()
    det    = str(row.get('DETALLE','') or '').strip()
    cod    = str(row.get('CODIGO', '') or '').strip()
    pn_raw = str(row.get('PRECIO NORMAL', '') or '').strip()
    po_raw = '' if sin_precio else normaliza_oferta(row.get('PRECIO OFERTA', ''))

    tiene_marca = marca and marca not in ('', 'nan')
    tiene_tipo  = tipo  and tipo  not in ('', 'nan')
    tiene_det   = det   and det   not in ('', 'nan')

    det_main = re.sub(r'\s*\*[^*]+$', '', det).strip()
    det_exc  = re.sub(r'^.*?(\*[^*]+)$', r'\1', det).strip() if '*' in det else ''
    if det_exc and not det_exc.startswith('*'): det_exc = ''

    c.setStrokeColor(HexColor('#AAAAAA'))
    c.setLineWidth(0.3 * mm)
    c.line(0, base_y + HALF, PW, base_y + HALF)

    if tiene_marca:
        if tiene_tipo:
            tz_top = top - 6 * mm
            tz_h   = 8 * mm
            ts = fit_s(c, tipo.upper(), 'MontB', 12, 6, USEW)
            ty = (tz_top - tz_h) + (tz_h - ts * 0.72) / 2
            c.setFont('MontB', ts)
            c.setFillColor(HexColor('#555555'))
            c.drawString(cxs(c, tipo.upper(), 'MontB', ts), ty, tipo.upper())

        mz_top = top - 14 * mm
        mz_h   = 20 * mm
        mu = marca.upper()
        ms  = fit_s(c, mu, 'Archivo', 52, 14, USEW)
        cap = ms * 1.18
        my  = (mz_top - mz_h) + (mz_h - cap) / 2
        c.setFont('Archivo', ms)
        c.setFillColor(black)
        c.drawString(cxs(c, mu, 'Archivo', ms), my, mu)

        if tiene_det:
            dz_top = top - 34 * mm
            dz_h   = 9 * mm
            du = det_main.upper()
            for ds in range(9, 5, -1):
                lns = wrap(c, du, 'MontR', ds, USEW)
                if len(lns) <= 2 and len(lns) * ds * 1.3 <= dz_h: break
            lns = wrap(c, du, 'MontR', ds, USEW)
            lh  = ds * 1.3
            fy  = dz_top - (dz_h - len(lns)*lh) / 2 - lh
            c.setFillColor(HexColor('#333333'))
            for i, ln in enumerate(lns):
                c.setFont('MontR', ds)
                c.drawString(cxs(c, ln, 'MontR', ds), fy - i*lh, ln)
            if det_exc:
                exc_y = fy - len(lns)*lh - 1
                c.setFont('MontR', 6)
                c.setFillColor(HexColor('#666666'))
                c.drawString(cxs(c, det_exc.upper(), 'MontR', 6), exc_y, det_exc.upper())

        oz_top = top - 43 * mm
        oz_bot = top - 88 * mm

    else:
        if tiene_tipo:
            tz_top = top - 6 * mm
            tz_h   = 16 * mm
            tu = tipo.upper()
            ts = fit_s(c, tu, 'Archivo', 26, 9, USEW)
            lns = wrap(c, tu, 'Archivo', ts, USEW)
            lh  = ts * 1.22
            while len(lns) > 2 and ts > 9:
                ts -= 1; lns = wrap(c, tu, 'Archivo', ts, USEW); lh = ts * 1.22
            blk = len(lns) * lh
            fy  = tz_top - (tz_h - blk) / 2 - lh
            c.setFillColor(black)
            for i, ln in enumerate(lns):
                c.setFont('Archivo', ts)
                c.drawString(cxs(c, ln, 'Archivo', ts), fy - i*lh, ln)

        if tiene_det:
            dz_top = top - 22 * mm
            dz_h   = 16 * mm
            du = det_main.upper()
            for ds in range(11, 6, -1):
                lns = wrap(c, du, 'MontB', ds, USEW)
                if len(lns) <= 3 and len(lns) * ds * 1.25 <= dz_h: break
            lns = wrap(c, du, 'MontB', ds, USEW)
            lh  = ds * 1.25
            fy  = dz_top - (dz_h - len(lns)*lh) / 2 - lh
            c.setFillColor(black)
            for i, ln in enumerate(lns):
                c.setFont('MontB', ds)
                c.drawString(cxs(c, ln, 'MontB', ds), fy - i*lh, ln)
            if det_exc:
                exc_y = fy - len(lns)*lh - 1
                c.setFont('MontR', 6)
                c.setFillColor(HexColor('#666666'))
                c.drawString(cxs(c, det_exc.upper(), 'MontR', 6), exc_y, det_exc.upper())

        oz_top = top - 38 * mm
        oz_bot = top - 88 * mm

    # ── Zona de oferta (solo si hay precio) ──────────────────────────────────
    if not sin_precio and po_raw:
        offer_raw = po_raw
        no_d  = ['%', 'AHORRO', 'DESCUENTO', 'LLEVA', 'POR', '$']
        add_d = not any(k in offer_raw for k in no_d)
        if add_d and not re.match(r'^[\d,.]+$', offer_raw): add_d = False
        offer = ('$' + offer_raw) if add_d else offer_raw

        oz_h  = oz_top - oz_bot
        max_s = int(oz_h / 1.28)

        if 'LLEVA' in offer and 'POR' in offer:
            t1, t2 = offer.split('POR', 1)
            t1, t2 = t1.strip(), 'POR ' + t2.strip()
            s = min(54, max_s)
            s = fit_s(c, t1, 'Passion', s, 14, USEW)
            s = fit_s(c, t2, 'Passion', s, 14, USEW)
            cap = s * 1.18; blk = 2 * cap; gap = (oz_h - blk) / 3
            y1 = oz_top - gap - cap
            y2 = y1 - gap * 0.6 - cap
            hollow(c, t1, 'Passion', s, y1, min_s=14)
            hollow(c, t2, 'Passion', s, y2, min_s=14)
        elif 'LLEVA' in offer:
            s  = fit_s(c, offer, 'Passion', min(54, max_s), 14, USEW)
            cy = oz_bot + (oz_h - s * 1.18) / 2
            hollow(c, offer, 'Passion', s, cy, min_s=14)
        elif '%' in offer and 'AHORRO' in offer:
            m = re.search(r'(\d+%)', offer)
            if m:
                pct  = m.group(1)
                rest = offer.replace(pct, '').strip()
                sp = fit_s(c, pct,  'Passion', min(int(oz_h*0.62/1.28), max_s), 18, USEW)
                sr = fit_s(c, rest, 'Passion', min(int(oz_h*0.38/1.28), max_s), 14, USEW)
                cp, cr = sp*1.15, sr*1.15
                gap = (oz_h - cp - cr) / 3
                yp = oz_top - gap - cp
                yr = yp - gap * 0.5 - cr
                hollow(c, pct,  'Passion', sp, yp, min_s=18)
                hollow(c, rest, 'Passion', sr, yr, min_s=14)
        elif '%' in offer:
            s  = fit_s(c, offer, 'Passion', min(max_s, 100), 18, USEW)
            cy = oz_bot + (oz_h - s * 1.15) / 2
            hollow(c, offer, 'Passion', s, cy, min_s=18)
        else:
            s  = fit_s(c, offer, 'Passion', max_s, 18, USEW)
            cy = oz_bot + (oz_h - s * 1.15) / 2
            hollow(c, offer, 'Passion', s, cy, min_s=18)

        # Precio anterior (tachado)
        show_prev = False
        if pn_raw and pn_raw not in ('nan', '', 'NaN'):
            pn_fmt   = fmt_precio(pn_raw)
            clean_po = re.sub(r'[^\d,.]', '', po_raw)
            show_prev = (pn_fmt != fmt_precio(clean_po)) if clean_po else True

        prev_rl = top - 91 * mm
        if show_prev:
            txt = f"Precio Anterior: ${fmt_precio(pn_raw)}"
            fs  = 7.5
            c.setFont('MontB', fs)
            c.setFillColor(HexColor('#555555'))
            tw = sw(c, txt, 'MontB', fs)
            tx = MAR + (USEW - tw) / 2
            c.drawString(tx, prev_rl, txt)
            c.setStrokeColor(HexColor('#333333'))
            c.setLineWidth(0.5)
            c.line(tx, prev_rl + fs*0.38, tx+tw, prev_rl + fs*0.38)

    # ── Código y vigencia ─────────────────────────────────────────────────────
    info_rl = top - 99 * mm + TOP_OFFSET + BOTTOM_OFFSET
    if cod and cod != 'nan':
        c.setFont('MontR', 7)
        c.setFillColor(HexColor('#444444'))
        c.drawString(MAR, info_rl, f"Cód: {cod}")

    c.setFont('MontB', 7)
    c.setFillColor(black)
    vtw = sw(c, vigencia, 'MontB', 7)
    c.drawString(MAR + (USEW - vtw) / 2, info_rl, vigencia)


def generar_pdf(filas, vigencia, output_path, sin_precio=False):
    cv = canvas.Canvas(output_path, pagesize=(PW, PH))
    total = len(filas)
    for i in range(0, total, 2):
        draw_cenefa(cv, HALF, filas[i], vigencia, sin_precio=sin_precio)
        if i + 1 < total:
            draw_cenefa(cv, 0, filas[i+1], vigencia, sin_precio=sin_precio)
        cv.showPage()
    cv.save()
