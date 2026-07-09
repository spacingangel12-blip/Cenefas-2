import re

MARCAS = [
    "DELI BELL", "BLUE BAY", "ALETA DE ORO", "BABY CONFI", "NEUTRO BALANCE",
    "NEUTRO BALAN",
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
    # --- Ampliación: marcas detectadas en catálogos reales ---
    "FUZE TEA", "NESCAFÉ", "NESCAFE", "MOLIÈRE", "MOLIERE", "NESTLÉ", "NESTLE",
    "CANDY MANDY", "FUD", "CRACKIS", "ACT II", "LA BOTANERA", "YOPLAIT",
    "ORAL-B", "ORAL B", "CREST", "RASER", "HANDS&BODY", "HANDS & BODY",
    "NEUTROGENA", "OLD SPICE", "SECRET", "PALMIRA", "TERSSO", "SENSAZEN",
    "CITREX", "PÉTALO", "PETALO", "LINNETTE", "ZOTE", "FLASH", "MAGNOCLOR",
    "LOPRESOR", "ROBOTEK", "EVEREADY", "EVENFLO", "FRISO GOLD", "FRISO",
    "MININO", "MAC'MA", "MAC´MA", "DODYS", "KLEENEX COTTONELLE", "KLEENEX",
    "SUAVEL", "CURAN", "BLUE TREE", "MURANO", "AFTER BITE",
]

TIPOS = [
    "PASTA DENTAL", "PASTAS", "PASTA",
    "SHAMPOO", "SHAMP",
    "CREMA CORP", "CREMA PARA PEINAR", "CREMAS", "CREMA",
    "DESODORANTES", "DESODORANTE", "DESOD",
    "JABÓN LAVANDERÍA", "JABÓN MANOS", "JAB MANOS", "JABÓN", "JAB",
    "DETERGENTES", "DETERGENTE",
    "LAVATRASTES", "SUAVIZANTES", "SUAVIZANTE", "SUAV",
    "LIMPIADOR", "LIMP",
    "PAPEL HIGIÉNICO", "PAPEL HIGIENICO", "PAPEL HIG", "PAÑALES", "PANAL",
    "TOALLAS FEMENINAS", "TOALLAS ANTIBACTERIALES", "TOALLAS",
    "TOALLITAS HÚMEDAS", "TOALLITAS",
    "TINTES", "MOUSSES",
    "AGUA NATURAL",
    "BEBIDA ENERGÉTICA", "BEBIDA SUEROX", "BEBIDA",
    "PILAS", "PROT LAB", "ALIMENTO",
    "ACCESORIOS", "ARTÍCULOS PARA BEBÉ", "REPELENTES",
    "BOLÍGRAFO", "MARCATEXTOS", "LÁPIZ",
    "CEREALES", "CEREAL", "CHOCOLATES", "CHOC",
    "GALLETA", "SOPA", "ACEITE", "HUEVO",
    "BOTANAS", "PAN DE CAJA",
    "ENDULZANTES", "SOLUCIÓN SANITIZANTE", "SOLUCION", "SOLUCIÓN",
    "LLAVEROS", "LLAVERO", "PELUCHES", "IMANES",
    "ROSUVASTATINA", "DULCES", "DULCE", "ACOND", "ATÚN", "ATUN",
    # --- Ampliación: tipos detectados en catálogos reales ---
    "CAFÉ", "CAFE", "JAMÓN", "JAMON", "PALOMITAS", "SALSA", "YOGHURT",
    "YOGURT", "HILOS DENTALES", "ESPONJA", "SERVILLETAS", "SERV",
]

def parse_descripcion(desc):
    raw = str(desc).strip().upper()
    raw = re.sub(r'\s+', ' ', raw)  # colapsar espacios dobles/múltiples (frecuentes en catálogos reales)

    exc_m   = re.search(r'(\*[^\*]+)$', raw)
    excepto = exc_m.group(1).strip() if exc_m else ''
    base    = raw[:exc_m.start()].strip() if excepto else raw

    tipo  = ''
    resto = base
    for t in sorted(TIPOS, key=len, reverse=True):
        pat = re.compile(r'^' + re.escape(t) + r'(?:\s|,|$)')
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
