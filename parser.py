import re

MARCAS = [
    "DELI BELL", "BLUE BAY", "ALETA DE ORO", "BABY CONFI", "NEUTRO BALANCE",
    "MANZANITA SOL", "SEVEN UP", "BONY BLUE", "BIO CLASSIC", "DULZI KIDS",
    "BI SWEET", "NATURE´S HEART", "NATURE'S HEART", "MR CAT", "DOG STAR",
    "FORTY DOG", "FORTY CAT", "GOOD CARE", "CAT CHOW", "HERBAL ESSENCES",
    "HEAD & SHOULDERS", "DOS:PUNTOS", "NATU KIDS", "STA. MARIA", "NEUTRO B",
    "KELLOGG´S", "KELLOGG'S", "KERNEL", "GUADALUPE", "SABROSANO",
    "CARLOS V", "EPURA", "PEPSI", "RED BULL", "SUEROX", "PEÑAFIEL", "CLAMATO",
    "MIRINDA", "NUTRIOLI", "ALPURA", "CREMINO", "NUCITA", "MUIBON", "CURAPACK",
    "COLGATE", "SENSAVAL", "BRISAGE", "CAPRICE", "TAMPAX", "AFFECTIVE",
    "COLORSILK", "CONFIHÁBILE", "COREGA", "SENSODYNE",
    "PANTENE", "ELVIVE", "FRUCTIS", "OBAO", "SABA", "TERSSURA", "KDELLE",
    "AXE", "REXONA", "DOVE", "LACTOVIT", "VASELINE",
    "FUERZAMAX", "GIRASOL", "ENSUEÑO", "POETT", "FABULOSO", "DOWNY",
    "AXION", "SALVO", "ACE", "ARIEL", "SULTAN", "AJAX", "PALMOLIVE", "CLOROX",
    "GERBER", "COMODISEC", "SMUDY´S", "SMUDY'S", "BBTIPS", "KLEENBEBÉ",
    "NIDO", "ENFAGROW", "HUGGIES", "NAN",
    "FACILAND", "ELITE", "PHARMALIFE", "ENERGIZER", "KROMICELL",
    "PLESCENT", "SELENA", "BENEFUL", "SUAVITEL", "MENNEN", "STEFANO",
    "OPTIMS", "LADY S", "SPEED S",
]

TIPOS = [
    "PASTA DENTAL", "PASTA",
    "SHAMPOO", "SHAMP",
    "CREMA CORP", "CREMA PARA PEINAR", "CREMA",
    "DESODORANTE", "DESOD",
    "JABÓN LAVANDERÍA", "JABÓN MANOS", "JABÓN NEUTRO", "JABÓN", "JAB",
    "DETERGENTES", "DETERGENTE",
    "LAVATRASTES", "SUAVIZANTE", "SUAV",
    "LIMPIADOR", "LIMP",
    "PAPEL HIGIÉNICO", "PAÑALES",
    "TOALLAS FEMENINAS", "TOALLAS ANTIBACTERIALES", "TOALLAS",
    "TOALLITAS HÚMEDAS", "TOALLITAS",
    "TINTES", "MOUSSES",
    "AGUA NATURAL",
    "BEBIDA ENERGÉTICA", "BEBIDA SUEROX", "BEBIDA ALPURA", "BEBIDA",
    "PILAS", "PROT LAB", "ALIMENTO",
    "ACCESORIOS", "ARTÍCULOS PARA BEBÉ", "REPELENTES",
    "BOLÍGRAFO", "MARCATEXTOS", "LÁPIZ",
    "CEREAL", "CHOCOLATES", "CHOC",
    "GALLETA", "SOPA", "ACEITE", "HUEVO",
    "BOTANAS", "PAN DE CAJA",
    "ENDULZANTES", "SOLUCIÓN SANITIZANTE",
    "LLAVEROS", "LLAVERO", "PELUCHES", "IMANES",
    "ROSUVASTATINA", "DULCE", "ACOND", "ATÚN",
]

def parse_descripcion(desc):
    raw = str(desc).strip().upper()

    exc_m   = re.search(r'(\*[^\*]+)$', raw)
    excepto = exc_m.group(1).strip() if exc_m else ''
    base    = raw[:exc_m.start()].strip() if excepto else raw

    tipo  = ''
    resto = base
    for t in sorted(TIPOS, key=len, reverse=True):
        pat = re.compile(r'^' + re.escape(t) + r'(?:\s|$)')
        if pat.match(resto):
            tipo  = t
            resto = resto[len(t):].strip().lstrip(',').strip()
            break

    if not tipo and resto.startswith('LÍNEA'):
        tipo  = 'LÍNEA'
        resto = resto[5:].strip()

    marca   = ''
    detalle = resto
    for m in sorted(MARCAS, key=len, reverse=True):
        pat = re.compile(r'^' + re.escape(m) + r'(?:\s|,|$)')
        if pat.match(resto):
            marca   = m
            detalle = resto[len(m):].strip().lstrip(',').strip()
            break

    if not tipo and not marca and resto:
        words   = resto.split()
        tipo    = words[0]
        detalle = ' '.join(words[1:])

    if excepto:
        detalle = (detalle + ' ' + excepto).strip() if detalle else excepto

    return {
        'TIPO':    tipo.strip(),
        'MARCA':   marca.strip(),
        'DETALLE': detalle.strip(),
    }
