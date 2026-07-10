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
    # --- Ampliación: Farmacia / OTC / Autoservicio (Farmacia Guadalajara) ---
    # Laboratorios / marca propia de farmacia
    "PHARMALIFE NATURA", "GENOMMA LAB", "GENOMMA", "SILANES", "LIOMONT",
    "SENOSIAIN", "PISA", "SANFER", "CHINOIN", "COLLINS", "ARMSTRONG",
    "BEST", "RIMSA", "LANDSTEINER", "MAVER", "PROBIOMED", "NEOLPHARMA",
    "SANOFI", "BAYER", "PFIZER", "NOVARTIS", "GSK", "MERCK", "ROCHE",
    "TEVA", "ABBOTT", "JOHNSON", "J&J",
    # Dolor / fiebre / resfriado / analgésicos
    "TAFIROL", "TEMPRA", "DOLO NEUROBION", "NEUROBION", "BEDOYECTA",
    "SUPRADYN", "REDOXON", "CENTRUM", "ADVIL", "BUSCAPINA", "MELOX",
    "SAL DE UVAS PICOT", "ALKA-SELTZER", "ALKA SELTZER", "MEJORAL",
    "VICK VAPORUB", "VICKS", "ANTIFLU-DES", "ANTIFLU DES", "SANSFLU",
    "AFRIN", "SUDAFED", "BENADRYL", "CLARITIN", "ALERGIOL", "ACTRON",
    "ASPIRINA", "ASPIRINA PROTECT", "MK", "GELVER", "NAPROXENO",
    "IBUPROFENO", "PARACETAMOL", "TIORFAN", "PEPTO-BISMOL", "PEPTO BISMOL",
    "MELOXICAM", "DICLOFENACO", "OMEPRAZOL", "RANITIDINA", "LOSARTAN",
    "METFORMINA", "SILDENAFIL", "TELMISARTAN", "ETORICOXIB",
    # Marca propia línea salud / dispositivos
    "PHARMALIFE VITALS", "ACCU-CHEK", "ACCU CHEK", "ONE TOUCH",
    "OMRON", "BRAUN", "MICROLIFE",
    # Cuidado bucal / garganta
    "LISTERINE", "STREPSILS", "RICOLA", "BUCOFRESH", "MENTHOLATUM",
    "ORAL AID", "DENTOL",
    # Vitaminas / suplementos / nutrición
    "GNC", "ENSURE", "BOOST", "PEDIASURE", "GLUCERNA", "CHOCOMILK",
    "NESQUIK", "MILO", "ABBOTT NUTRITION", "MEGARED", "OMEGA 3",
    # Bebé / infantil (adicional a lo ya existente)
    "SIMILAC", "S-26", "PROMIL", "MUCOSOLVAN", "PAIDOTERIN",
    "BABYSEC", "PAÑALES BABYSEC",
    # Cuidado femenino / higiene
    "ALWAYS", "NOSOTRAS", "STAYFREE", "OB", "SABA PROTECT",
    "SUAVE", "JOHNSON'S", "JOHNSON´S", "JOHNSON BABY", "CETAPHIL",
    "EUCERIN", "NIVEA", "AVEENO", "LA ROCHE POSAY", "CERAVE", "CERAVÉ",
    "BEPANTHEN", "GERBER PURITAS",
    # Belleza / cuidado personal (farmacia)
    "MAYBELLINE", "L'ORÉAL", "LOREAL", "REVLON", "NYX", "COVER GIRL",
    "GILLETTE", "BIC", "SCHICK", "NAIR",
    # Sueros / hidratación / electrolitos
    "ELECTROLIT", "SUERO ORAL", "HYDRA SHOT", "GATORADE", "POWERADE",
    "VIDA SUERO ORAL",
    # Repelentes / cuidado exterior
    "OFF!", "OFF", "STAYAWAY", "NOPICOS",
    # Cigarros / dulcería de farmacia (frecuentes en autoservicio)
    "HALLS", "TROLLI", "BUBBALOO", "DE LA ROSA", "MAZAPAN",
    # Papelería / conveniencia (adicional)
    "BIC CRISTAL", "PILOT",
    # --- Ampliación 2: más laboratorios / marcas propias mexicanas ---
    "SCHWEPPES", "GELCAPS", "SOLFRA", "GRISI", "DERMOCLIN", "AVENE",
    "AVÈNE", "ISDIN", "VICHY", "BIODERMA", "PROBELLE", "ASEPXIA",
    "TOKS", "MK LAB", "RANBAXY", "APOTEX", "STENDHAL",
    "AMSA", "ATLANTIS", "ZUOZ", "COFARMEN", "COLLINS PHARMA",
    "LAKESIDE", "SYNTHON", "DEGORTS", "LEGRAND", "BRULUART",
    # Gastrointestinal
    "GASTRIOL", "DIGESIL", "SAL DE FRUTA LUA", "LUA", "ESOMEPRAZOL",
    "PANTOPRAZOL", "SIMETICONA", "LOPERAMIDA", "MYLICON", "GASTRIUM",
    "MOTILIUM", "PRIMPERAN",
    # Respiratorio / tos / gripe
    "TUSSIONEX", "BISOLVON", "AMBROXOL", "DEXTROMETORFANO",
    "LORATADINA", "AMBROPAX", "VAPORUB", "TABCIN", "DRIXORAL",
    "MUCOSIL", "FLUIMUCIL",
    # Cardiovascular / metabólico (genéricos comunes de farmacia)
    "ATORVASTATINA", "ENALAPRIL", "AMLODIPINO", "CAPTOPRIL",
    "GLIBENCLAMIDA", "INSULINA", "LANTUS", "NOVORAPID", "GLUCOFAGE",
    "JARDIANCE", "OZEMPIC", "MOUNJARO", "WEGOVY",
    # Dermatológico específico
    "DERMOVATE", "CELESTODERM", "BETAMETASONA", "HIDROCORTISONA",
    "CLOTRIMAZOL", "KETOCONAZOL", "PANALOG", "FUCIDIN", "ELIDEL",
    # Oftálmico / óptica
    "OPTIVAR", "SISTANE", "REFRESH", "VISINE", "OCUBALM", "PATANOL",
    # Cuidado del cabello (adicional)
    "SCHWARZKOPF", "SYOSS", "TRESEMMÉ", "TRESEMME", "SEDAL",
    "SALON LINE", "NIELY", "IMPULSE", "PROCLINIC", "WELLA",
    # Higiene bucal (adicional)
    "CLOSE UP", "AQUAFRESH", "PARODONTAX", "DENTIPRO",
    # Snacks / abarrotes de autoservicio (frecuentes en farmacia)
    "SABRITAS", "BARCEL", "RUFFLES", "CHEETOS", "DORITOS",
    "COCA COLA", "COCA-COLA", "FANTA", "SPRITE", "BOING", "JUMEX",
    "DEL VALLE", "V8", "GANSITO", "MARINELA", "BIMBO", "TIA ROSA",
    "PRINGLES", "OREO", "EMPERADOR", "CHOKIS", "PRINCESA",
    # Papelería / regalos / temporada
    "SHARPIE", "BINER", "SCRIBE", "STAEDTLER", "FABER-CASTELL",
    "FABER CASTELL", "CROSS", "HELLO KITTY", "MINIONS",
    # Higiene / limpieza del hogar (adicional)
    "LYSOL", "GLADE", "AIR WICK", "PINOL", "MAXILIMP", "SANYTOL",
    "CLORALEX", "SUPER K",
    # --- Ampliación 3: veterinaria ---
    "PEDIGREE", "WHISKAS", "DOG CHOW", "FRISKIES", "PURINA",
    "NUPEC", "ROYAL CANIN", "HILLS", "PRO PLAN", "EXCELLENT",
    "MIMASCOTA", "VITALCAN", "CACHORRO FIEL", "FRONTLINE",
    "BRAVECTO", "NEXGARD", "DRONTAL", "SIMPARICA",
    # Lácteos / refrigerados
    "LALA", "SANTA CLARA", "YAKULT", "DANONE", "ACTIVIA", "CHOBANI",
    "PHILADELPHIA", "CHIPILO", "ILC", "GLORIA",
    "COUNTRY FRESH", "SVELTY",
    # Condimentos / abarrotes básicos
    "MCCORMICK", "HERDEZ", "LA COSTEÑA", "LA COSTENA", "VALENTINA",
    "TAJIN", "TAJÍN", "MAGGI", "KNORR", "LYNCOTT", "CLEMENTE JACQUES",
    "BÚFALO", "BUFALO", "DOÑA MARÍA", "DONA MARIA", "LA MODERNA",
    "BARILLA", "VERONA", "1-2-3", "LIGHT & FIT", "HEINZ",
    # Panadería / galletas (adicional)
    "SPONCH", "GAMESA", "RICOLINO", "TRIS", "MAMUT", "ARCOIRIS",
    "SUAVICREMA", "MEDIA NOCHE", "DONITAS", "TWINKIES",
    # Electrónica / pilas / accesorios
    "DURACELL", "PANASONIC", "SONY", "PHILIPS", "RAYOVAC",
    "STEREN", "PERFECT CHOICE", "VORAGO", "GHIA",
    # Café / té adicional
    "LYONS", "DOLCA", "COMBATE", "LIPTON", "TÉ MORELIA", "TE MORELIA",
    "STARBUCKS", "LEGAL",
    # Cuidado infantil adicional
    "CHICCO", "PRINSEL", "MAM", "NUK", "AVENT", "MEDELA", "GRACO",
    "FISHER PRICE", "EVENFLO ADVANCED", "SUAVINEX", "PLAYTEX",
    # Snacks dulces / chocolates adicionales
    "HERSHEY'S", "HERSHEYS", "MILKY WAY", "SNICKERS", "M&M'S",
    "TWIX", "BUBBALOO POP", "CARLOS V CHOCOLATE",
    "TURIN", "LUCAS", "PULPARINDO", "VERO", "RICOLINO PALETAS",
    "MAZAPÁN DE LA ROSA",
    # Cuidado del hogar / desinfección adicional
    "MICROLAX", "FRESKA", "PATO PURIFICANTE", "PATO WC", "VANISH",
    "MR MUSCULO", "MR. MÚSCULO", "1000 EN 1",
    # Cigarros y encendedores (autoservicio farmacia)
    "BIC ENCENDEDOR", "CRICKET",
    # Marcas de belleza / cuidado personal adicionales
    "DOVE MEN", "NIVEA MEN", "ADIDAS FRAGANCIAS", "AXE FRAGANCIAS",
    "TIMOTEI", "SVENSON", "KONZIL", "POND'S", "PONDS", "PONDS AGE MIRACLE",
    "OLAY", "SOFT & BEAUTIFUL",
    # Farmacia adicional: dermatológico y cuidado de heridas
    "CICATRICURE", "MEDERMA", "HANSAPLAST", "CURITAS 3M", "3M NEXCARE",
    "MICROPORE",
    # --- Ampliación 4: catálogo real farmaciasguadalajara.com (jul 2026) ---
    # Medicamentos / marca propia farmacia y genéricos adicionales
    "LUNARIUM", "KIRRUZ", "ENTEROGERMINA", "VESSEL DUE F", "LIBERTRIM",
    "LIBERTRIM ALFA", "JARDIANZ", "JARDIANZ DPP", "ABINTRA", "MUGASIN",
    "ACARBOSA", "DEPEND", "PRUDENCE", "ATEMPERATOR", "P. BEE LEVY",
    "PBEE LEVY", "COLGATE PERIOGARD", "PERIOGARD",
    # Belleza / cuidado facial y capilar adicional
    "BIO-OIL", "BIO OIL", "HAWAIIAN TROPIC", "BIOMETIK", "BELSKIN",
    "SAN LUIS", "CHIVIX", "ST. IVES", "ST IVES", "MUSTELA", "ECLIPSOL",
    "OLEODERM", "ENDOCARE", "HELIOCARE", "DR. AKERMAN'S", "DR AKERMAN'S",
    "DR. HEALTH", "DR HEALTH", "BIOSCENTS", "BODY & BEAUTY",
    "GOT2B", "PROSA", "OKRA", "TOP FASHION", "SANBORNS", "THE BOTANIST",
    "SPEED STICK", "TETRALISAL", "EFFEZEL", "DEXERYL", "DUCRAY",
    "A-DERMA", "ADERMA", "POP LIFE", "HELLO DAISE",
    "PEACHY DAISE", "SUNNY DAISE", "SECRET SCENTS",
    # Hogar / limpieza / temporada
    "MIKADO AURA", "MIKADO", "ARM & HAMMER", "OXICLEAN",
    "ARM & HAMMER + OXICLEAN", "ALCOSOL", "BRIDGECO", "OKKO", "PANINI",
    # Electrónicos
    "LIME", "GOWIN", "FREEKICK-L", "FREEKICK",
    # Alimentos / despensa adicional
    "MRS. CUBBISON'S", "MRS CUBBISONS", "CANOIL", "CAPULLO", "CRISTAL",
    "GRANA", "KÁRTAMUS", "KARTAMUS",
    # --- Ampliación 5: catálogo real farmaciasguadalajara.com (jul 2026) ---
    # Vitaminas / suplementos / multivitamínicos adicionales
    "SOLANUM", "VIDANAT", "SUKROL", "CBD LIFE", "HABITS", "NUTRIBIO",
    "ENTEREX", "BELACAPS", "MULTIBLUE", "FALCON", "BIRDMAN", "YAOCA",
    "VITAL PROTEINS", "CAHUENGA", "D-LACTASE", "ELEMENTAL", "GUINART",
    "XOTZIL", "MEGA UVA", "NARTEX", "SCHMIDT SCHULER & HERRICK",
    "SCHULER & HERRICK", "PRIME BOOST", "PHARMATON", "ANAHUAC",
    "CALTRATE", "WU NUTRITION", "CARDISPAN", "COMPLEMENT BALANCE PRO",
    "GOMIX", "NATURAL HEALTH", "SIENNA", "UKN", "NEPRO", "AVIVIA",
    "C-REVITAL", "SHOT-B", "CASEC", "VIPLENA", "ARCALION", "ARISTOCAPS",
    "BEBISTAN", "BEDOYECTA TRI", "DECA-DURABOLIN", "REGENESIS MAX",
    "G-NOSITOL", "INOFOLIC", "ELEVIT", "OPTI-MYO", "OPTI-LAC",
    "PROBIOLOG", "BIOGAIA", "LACTOKEY", "BENEI-G", "ADEROGYL",
    "AUTRIN", "FICONAX", "APROVASC",
    # Mascotas adicional
    "FELIX", "GRAND PET", "PRIME CARE", "CANPRO", "GANADOR",
    "PPT", "CLAUDIO'S", "KITTEN",
    # Bebé / fórmulas infantiles adicionales
    "ENFAMIL", "FRISOLAC", "NOVAMIL", "ALULA", "NUTRIBABY", "KABRITA",
    "ALTHÉRA", "ALTHERA", "GOOD START", "NEOCATE", "NUTRAMIGEN",
    "NUTRILON", "PURAMINO", "SMA", "NIDAL", "ENFALAC", "EXCELLA",
    "BABY SKY", "KLEENBEBÉ COMODISEC", "BBTIPS SENSITIVE", "KIDDIES",
    "DODY'S", "DODYS PREMIUM", "FIXODENT", "GARNIER",
    # Papelería / juguetería adicionales
    "UPAK", "KOLA LOKA", "ARTKIDS", "DIPAK",
    "GLOBOS PAYASO", "KOLOR", "ESCRIMEX", "PAPER MATE", "PENTEL",
    "CRAYITOONS", "MATTEL", "HASBRO", "PLAY-DOH", "PLAY DOH",
    "EDUCACTIVITY", "TOY JAM", "BF TOYS", "LEV SPORTS", "BATH TOYS",
    "NOVELTY", "FISHER-PRICE", "GLÜCK", "GLUCK",
    # --- Ampliación 6: investigación exhaustiva farmaciasguadalajara.com (jul 2026) ---
    # Café / té / cremas para café
    "LOS PORTALES", "TASTER'S CHOICE", "JACOBS", "GARAT", "CORINA",
    "BLASÓN", "CAFÉ MEXICANO", "EL MARINO", "VUELA", "ORO CAFÉ",
    "PUNTA DEL CIELO", "COFFEE MATE", "THERBAL", "LA PASTORA",
    "GN+VIDA", "HERBACIL", "KOYA HEALTHFOODS", "DOBLETT", "SAROSO",
    "TITEA", "MUMBAI", "REMEDY 24", "XOTZIL CLOROFILA",
    # Panadería / galletas / pastelitos
    "CUÉTARA", "CUETARA", "PAN BUENO", "GRANVITA", "LA INTEGRAL",
    "MARIBEL", "TAIFELD'S", "MARIÁN", "TROYANAS", "CAYRO", "WONDER",
    "CRACKETS", "SUANDY", "DELY BELY", "QUAKER", "JULITAS",
    "EL PANQUÉ",
    # Dulcería / chocolates / chicles
    "TRIDENT", "FERRERO ROCHER", "SKWINKLES", "BONDY FIESTA",
    "MENTOS", "SKITTLES", "CHUPA CHUPS", "PELÓN", "TIC TAC", "EFRUTTI",
    "ICEE", "ZUMBA", "AKIPIKA", "COME VERDE", "REESE'S", "TUTSI",
    "WINKY", "LARÍN", "INDY", "RANITA", "KINDER", "MILCH",
    # Cuidado bucal adicional
    "GUM", "GELCLAIR", "LACER", "NOVACARE", "BEXIDENT", "DENTOBAC",
    "KIN", "KIN B5", "BUCAROL", "GINGILACER",
    # Oftálmico / lentes de contacto
    "OFTENO", "EYESTIL", "SPLASH TEARS", "SOPHIA", "PROLUB", "ZEBESTEN",
    "ALERCROM", "ALESIRAM", "ALIN", "ALLEANCE", "ALPHAGAN", "ANHIGOT",
    "AQUADRAN", "ARTELAC", "ACUTEARS", "AGGLAD", "AILICEC",
    "OPTI-FREE", "RENU", "RENU PLUS", "RENU FRESH", "BIOTRUE",
    "SYSTANE", "HYABAK", "THEALOZ", "LAGRICEL", "HUMYLUB", "GAAP",
    "KRYTANTEK", "TRAZIDEX", "NAZIL", "SOPHIPREN", "MONOLATAN",
    # Bebidas
    "BLUEBAY", "BONAFONT", "CIEL", "DR. PEPPER", "STA. MARÍA BEBIDA",
    "CANADA DRY", "MIRÍNDA", "ZUBBA", "FRESCA", "MUNDET", "JARRITOS",
    "SQUIRT", "7UP", "CASERA", "AGA", "CABALLITOS", "ADES",
    "OLÉ", "SPRING FRESH", "JAZTEA", "CALAHUA", "NATURA JUGO",
    "OCEAN SPRAY", "TREE TOP", "V8 SPLASH", "ARIZONA",
    "TORRES 5", "TORRES 10", "JIMADOR", "CABRITO", "DON ROBERTO",
    "EL MEZCALITO", "GRAND DOUGLAS", "JACK DANIEL'S", "RANCHO ESCONDIDO",
    # Limpieza / lavandería
    "MAS COLOR", "BOLD", "PERSIL", "FOCA", "BLANCA NIEVES", "ROMA",
    "UTIL", "CARISMA", "LEÓN", "MARIPOSA", "LIRIO", "BLANCATEL",
    "MAGNOCLOR JABON", "EASY SHINE", "SCOTCH-BRITE", "SCOTCH BRITE",
    "FAMILYGUARD", "WOW CLEAN", "SC JOHNSON", "HARPIC", "LAVABRILLO",
    "DRANO", "INMUNO CLEAN",
    # --- Ampliación 7: investigación exhaustiva farmaciasguadalajara.com (jul 2026) ---
    # Dermo / marcas destacadas (home + sección "Marcas" de Dermo)
    "CANTABRIA LABS", "FARMAPIEL", "LETI AT4", "MOM TO MOM", "SERENITY",
    "SESDERMA", "PILEXIL", "UMBRELLA", "LUBRIDERM", "FLARICEL", "CHOLAL",
    # Salud sexual / preservativos (filtro de marcas real, categoría Preservativos)
    "SICO", "TROJAN", "PLAYBOY", "TRUST", "DUREX", "MAX SENS",
    # Oftalmología / lentes de contacto adicional (filtro de marcas real)
    "ALLERGAN", "LUMIGAN", "TRAVATAN", "XALATAN", "XALACOM",
    "RESTASIS", "ZADITEN", "NEVANAC", "LATISSE", "COMBIGAN", "AZOPT",
    "AZARGA", "LASTACAFT", "COSOPT", "DUOTRAV", "SIMBRINZA", "GANFORTI",
    "MAXITROL", "ZYPRED", "SOPHIXIN", "REFRESH FUSION", "REFRESH TEARS",
    "RENU ADVANCED",
    # --- Ampliación 8: catálogo real farmaciasguadalajara.com (jul 2026) ---
    # Bebés: fórmulas infantiles, higiene y cuidado adicional (filtro de marcas real)
    "ACICRAN KIDS", "ADEKON", "BACAOMAX", "BLUMEN", "C-BOOST", "CALCIGENOL",
    "CHICOLASTIC", "DUNOXSOL", "FER-IN-SOL", "FERRANINA", "ITALVIRÓN", "LACTIPAN",
    "POLY-VI-SOL", "SCOTT", "TEDDY HONEY BEAR", "TRI-VI-SOL", "VALMETROL",
    # Vitaminas y Suplementos: multivitamínicos y suplementos alimenticios
    # (filtro de marcas real, categorías Multivitaminas y Suplementos Alimenticios)
    "A-D-KAN", "ABLAZOR", "ACICRAN", "ALOE VERA", "AMINOTER", "ARISTO", "ASCENDA",
    "BACK2 PARTY", "BEDOYECTA +G", "BELABEAR", "BELLAFEM", "BELLUNO", "BENE-G",
    "BEROCCA", "BILANCA", "BIOMETRIX", "BIONELLA", "BIOPROTECT", "BIOTINA",
    "BIOTREFON", "BLOOM", "C-TECH", "CALCIPLUS", "CALCIUM-SANDOZ", "CALTRUM",
    "CARNOTVID", "CBOOST", "CIPROLISINA", "CISTEXEL", "CITRACAL", "CITRUS C",
    "COGNEXEL", "COMBESTERAL", "COMPLIDERMOL", "CORPOTASIN", "CORPOTASIN GK",
    "CORPOTASIN LP", "CRUDOX", "CUTERAL", "DABEON", "DEMUS", "DETRESGEL VIT",
    "DEXABION DC", "DIASPORAL", "DICLOF", "DINAFORT", "DITREI AMD", "DOLO BEDOYECTA",
    "DOLO TIAMINAL", "DOLO-NEUROBIÓN", "DOSHA LIFE", "DOTAVIT", "DRUSEN", "E-400",
    "EFE-CARN", "EMERGEN-C", "ENLYS", "ESCLEROVITAN", "ETERNAL", "EVERVITAL",
    "FEMEDUAL", "FEMINIS", "FEROCINE", "FERREXEL", "FIBIOMET", "FISIOFER", "FORTAC",
    "FOTORAL", "FREMALT", "G-BALANCE", "GESTOMEG", "GINKGO BILOBA", "GIRANDA",
    "GLUTAPAK", "GLUTAPAK R", "GOLI", "GRANAGARD", "HEMAMINA", "HEMAMINA-JET",
    "HIALOFLEX", "HIALOVIS", "HIDROFEROL", "HIGH POWER", "HISTOFIL", "HISTOGRAIN",
    "HYDRASHOT", "I-OMEGA3", "IBEROFLORA", "IDYLLA", "INOVOCARE", "INVERSION", "K-50",
    "KINISI", "KRILL ANTARTA", "L-CARNITINA", "LA SALUD ES PRIMERO", "LISEFEX",
    "LUCEBIOT", "LUXTER", "LYSI", "MACUHEALT", "MAGFOR", "MAKZIM", "MATER", "MATERNA",
    "MAXELLA", "MAXIBILOBA", "MDMIL", "MERICART", "MI FIBRA DIARIA", "MIDENAR",
    # --- Ampliación 9: catálogo real farmaciasguadalajara.com (jul 2026) — Circulatorio ---
    # Anticoagulantes / antiagregantes (filtro de marcas real, categoría Anticoagulantes)
    "XARELTO", "PRADAXAR", "ELICUIS", "AVIVIA", "BOLENTAX", "CLEXANE", "EXBUTEN",
    "LOVENTRAX", "OXCER", "PRASUCOR", "TIREVN", "AXOVAR", "GANGOTRI", "VENASTAT",
    "XARABAN", "LIXIANA", "VESSEL DUE", "XAVI", "EMIPRIL", "INHEPAR", "LEGALON",
    # Cardiovasculares (filtro de marcas real, categoría Cardiovasculares)
    "MICARDIS", "EXFORGE", "ALMETEC", "ILTUX", "TELARTEQ", "ANGIOTROFIN",
    "ARAHKOR", "BICARTIAL", "BLOPRESS", "ROLET", "ATACAND", "CO-DIOVAN",
    "CONCOR", "CORIATROS", "DAFLON", "AVIRENA", "COR-DULAS", "COZAAR",
    "DILACORAN", "DIOVAN", "EDARBI", "ELATEC", "ENTRESTO", "INSPRA",
    "LODESTAR", "MAXOPRESS", "OPENVAS", "TEMERIT", "TRITACE", "ZESTRIL",
    "CADUET", "COVERSAM", "ENALADIL", "EVIPRESS", "GLIOTEN", "IDAPTAN",
    "ILTUXAM-HCT", "ISORBID", "LOBIVON", "NEVARPIS", "NEXUS", "VASCULFLOW",
    "VERQUVO", "VIALIBRAM", "ZANIDIP", "AGRELESS", "ALDOMET", "APROVEL",
    "AVALIDE", "AVAPRO", "BATENSIAR", "BICONCOR", "BRILINTA", "CARDINIT",
    "CAUDALINE", "CLAUTER", "DEGREGAN", "DILATREND", "DINEXA", "DUBILA",
    "DUOALMETEC", "ELANTAN", "ESPIDORM", "FLUCOGREL", "HIGROTON", "HYZAAR",
    "INDERALICI", "LEYALTIS", "LOBI", "LODARTA", "MEDIFLOW", "MINIPRES",
    "MITZORATTA", "NORFENON", "NORVAS", "PHLEBODIA", "PLAVIX", "PLENACOR",
    "PRESONE", "PRETERAX", "PROCORALAN", "RULLE", "SERMION", "TARKA",
    "TEMITEV", "TENORETIC", "TENORMIN", "TEVETENZ", "TRIPLIXAM", "TRITAZIDE",
    "TRIVAS", "VALVULAN", "VILOPRE", "ZESTORETIC", "AXIRAS", "BLOQADRE",
    "BRAXAN", "CAPTRAL", "COAPROVEL", "CO-APROVEL", "CO-DEGREGAN", "COMBI-SIG",
    "COPLAVIX", "CORDARONE", "COVERSYL", "DILA-TEC", "DIMODAN", "DISGREN",
    "DOMBREL", "FLEXAR", "ISOKET", "JADAVAN", "KALIOLITE", "LANOXIN",
    "LOGIMAX", "MINITRAN", "NATRILIX", "NATRIXAM", "PLENDIL", "REGIVAS",
    "REMANSIL", "ROFUCAL", "RUTERAL", "SAFEBUL HID", "SELOKEN", "SELOPRES",
    "STUGERON", "TAMBOCOR", "TEBOVEN", "TEMIVAR", "TEVARDIS", "TRENTAL",
    "VANALOT", "VARCOR", "VARITON", "ZANIDUAL",
    # Tiroides (filtro de marcas real, categoría Tiroides)
    "EUTIROX", "SYNTHROID", "GLANROTIR", "KARET", "TAPAZOL", "GANGLIOSIDE",
    "MENSIFEM", "AMET", "CYNOMEL", "CYNOPLUS", "MICCIL", "NORALCODEX",
    "NOVOTIRAL", "THEVIER",
    # --- Ampliación 10: catálogo real farmaciasguadalajara.com (jul 2026) ---
    # Incontinencia (filtro de marcas real)
    "TENA",
    # Sistema Nervioso: Anticonvulsivos (filtro de marcas real)
    "LYRICA", "EPIVAL", "KEPPRA", "PRIKUL", "CARBAZINA", "CRIAM", "DISMEDOX",
    "KRIADEX", "LAMICTAL", "NEURONTIN", "PISARPEK", "RIMASTINE", "TEGRETOL",
    "VIMPAT", "ANZANERA", "GABANTIN", "OXETOL", "DEPAKENE",
    # Sistema Nervioso: Psicotrópicos (filtro de marcas real)
    "TRADEA", "FIRSITO", "SEROQUEL", "ANTREDAMIN", "CONCERTA", "DEXTION",
    "LEXOTAN", "MOTRUXIA", "ARATAEUS", "BRINTELLIX", "LUVOX", "NOKU",
    "Q-MIND", "RISPERDAL", "ZOQUALO", "APEGO", "VALDOXA", "SIDERIL",
    "TAFIL", "LEXAPRO", "RYBELSUS",
    # Sistema Nervioso: Neuroléptico (filtro de marcas real)
    "ARQUERA", "REXULTI", "ABRETIA", "CLOPIXOL", "FLUOXAC", "DEVIXDOL",
    "DULPICAP", "FARMAXETINA", "KASTANDI", "NUCLEO C.M.P", "PISAURIT",
    "DHARMA", "FLUANXOL",
    # Óseo / Antiartríticos (filtro de marcas real)
    "NOVOVARTALON", "VARTALON", "FOSAMAX", "ARCOXIA", "DOLAREN", "GELICART",
    "VOLTAREN", "EUFLEXXA", "ARDOSONS", "PIASCLEDINE", "NURO-B", "CUYULID",
    "INDAFLEX",
    # Hormonal: Anticonceptivos y Hormonales (filtro de marcas real)
    "MILEVA", "GYNOVIN", "LUMINANCE", "CECILET", "YASMIN", "YASMÍN",
    "GINORELLE", "ILIMIT", "MICROGYNON", "PATECTOR", "PROVERA", "RADIANCE",
    "CERAZETTE", "CYCLOFEMINA", "CYCLOFÉMINA", "EVRA", "LIBERFEM",
    "MARVELON", "MERCILON", "MESIGYNA", "ALIN", "UTROGESTAN", "GESLUTIN",
    "ANUAR", "BETNOVATE", "ANGELIQ", "BELARA", "BIOLAIF", "CALCORT",
    "CAVERJECT", "CELESTONE", "QLAIRA", "SLINDA", "NORDET", "PAULA",
    # Obesidad / Antiobesidad (filtro de marcas real)
    "IFA", "ACXION", "REDUSTAT", "DEMOGRASS", "ITRAVIL", "LINDEZA",
    "TRIYOTEX", "CONAGRAD", "CONFORIAR", "HESVEN", "PROCTO-GLYVENOL",
    "STETIKAL", "TERFAMEX", "VEDIPAL", "ANDANZA", "ASENLIX",
    # Óptica (filtro de marcas real, lentes de lectura)
    "SPL",
    "MILDA", "MINERGIUM", "MOREBON", "MULTI BLUE", "MULTILYTE", "MUNEKIDS", "MUVARETA",
    "MUVMENT", "MYO INOSITOL", "NATURE'S BOUNTY", "NATURE'S LIFE", "NEPRO HP",
    "NEURALIN", "NEURALIN RELIEF", "NEUROBION DC", "NEUROFLAX", "NIGHT-Z", "NOCELE",
    "NUTRIOSO", "OCUDRIVE", "OGESTAN", "OMACOR", "ONVIX", "OPTIMIN", "ORANGELART",
    "ORREI", "PILEFHI D", "PISAVIT", "PLENAFEM", "PLENIREN", "POLIQ", "POWERMAN",
    "PRESENZA", "PREVITA", "PROESSE", "PROSURE", "PROT-AGE", "PROTEINEX", "PULMOCARE",
    "PURA KID", "PURE LIFE", "REACTIMOL", "REGENESIS", "ROCA VIT", "ROCAVIT", "ROMINA",
    "SANSAGE", "SHILAJIT", "SIENNA SPM´S", "SK-INVITA", "SMART VIT", "SNELVIT",
    "SOFLAVIN", "STOP&GO", "STRESSTABS", "SUCROSOM", "SUCROSOM F", "SULVERION",
    "SUMA-B", "TALARIC", "TIAMINAL", "TRANSVITAL", "TRIBEDOCE", "VALAIT", "VALDECASAS",
    "VALMETROL-3", "VIDAMIL", "VIRLOMA", "VITAFUSIN", "VIVIOPTAL", "VOTRIPAX",
    # --- Ampliación 11: categorías faltantes detectadas vs. farmaciasguadalajara.com (jul 2026) ---
    # Diuréticos / Vasoconstrictores / Circulatorio adicional
    "LASIX", "ALDACTONE", "ESIDREX", "HIDROCLOROTIAZIDA", "FUROSEMIDA",
    "ESPIRONOLACTONA", "PRIVIGEN",
    # Curaciones: botiquín / vendas
    "3M", "CUROX", "HARTMANN", "VENOSAN",
    # Cuidado del pie
    "DR. SCHOLL'S", "DR SCHOLLS", "PIÉ SANO", "PIE SANO", "PROFOOT",
    # Cuidado del calzado
    "KIWI", "VIRGINIA", "MEDIA SUELA",
    # Carnes frías / abarrotes adicionales
    "FUD PREMIUM", "SAN RAFAEL", "VIRGINIA PENINSULAR", "ZWAN", "CAMPOFRÍO",
    "CAMPOFRIO", "THOMY",
    # Cerveza / vinos / licores (autoservicio farmacia)
    "CORONA", "MODELO", "VICTORIA", "TECATE", "INDIO", "PACIFICO", "PACÍFICO",
    "XX LAGER", "BOHEMIA", "HEINEKEN", "BUD LIGHT",
    "SAN MARCOS", "CETO", "TORRES", "SANTO TOMÁS", "SANTO TOMAS", "FREIXENET",
    "BACARDI", "JOSE CUERVO", "JOSÉ CUERVO", "DON JULIO", "TORADA",
    # --- Ampliación 12: verificación adicional vs. farmaciasguadalajara.com (jul 2026) ---
    # Juguetería adicional (filtro de marcas real)
    "FIFA", "WANNA BUBBLES", "NECNON", "NERF", "FLEXOR",
    # Electrónicos / Cómputo adicional (filtro de marcas real)
    "KINGSTON", "STYLOS", "SANDISK", "ADATA", "MOSI", "TAG PASE",
    # Papelería adicional (filtro de marcas real)
    "POST-IT", "SCOTCH", "KOLE",
    # Juguetería / colores (marca real, sección Básicos de Papelería)
    "CRAYOLA",
    # Piojos / kits especializados
    "HERKLIN",
    # Papel higiénico adicional
    "REGIO",
    # Respiratorio / tos adicional
    "TESALON",
    # Congelados: helados y paletas
    "HOLANDA", "MAGNUM",
    # Alimentos: untables / conservas adicional
    "NUTELLA", "TUNY",
    # Farmacia: genéricos y OTC adicional
    "GO-ON", "BACFIL", "TUMS", "LIPITOR",
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
    "GALLETA", "GALLETAS", "SOPA", "ACEITE", "HUEVO",
    "BOTANAS", "PAN DE CAJA",
    "ENDULZANTES", "SOLUCIÓN SANITIZANTE", "SOLUCION", "SOLUCIÓN",
    "LLAVEROS", "LLAVERO", "PELUCHES", "IMANES",
    "ROSUVASTATINA", "DULCES", "DULCE", "ACOND", "ATÚN", "ATUN",
    # --- Ampliación: tipos detectados en catálogos reales ---
    "CAFÉ", "CAFE", "TÉ", "TE", "JAMÓN", "JAMON", "PALOMITAS", "SALSA", "YOGHURT",
    "YOGURT", "HILOS DENTALES", "ESPONJA", "SERVILLETAS", "SERV",
    # --- Ampliación: Farmacia / OTC / Autoservicio (Farmacia Guadalajara) ---
    "MEDICAMENTO GENÉRICO", "MEDICAMENTO GENERICO", "MEDICAMENTO",
    "ANALGÉSICO", "ANALGESICO", "ANTIGRIPAL", "ANTIÁCIDO", "ANTIACIDO",
    "ANTIALÉRGICO", "ANTIALERGICO", "ANTIINFLAMATORIO", "ANTIBIÓTICO",
    "ANTIBIOTICO", "VITAMINAS", "VITAMINA", "MULTIVITAMÍNICO",
    "MULTIVITAMINICO", "SUPLEMENTO", "SUERO ORAL", "ELECTROLITOS",
    "TABLETAS", "CÁPSULAS", "CAPSULAS", "JARABE", "GOTAS", "SOBRES",
    "CREMA MEDICADA", "UNGÜENTO", "UNGUENTO", "PROTECTOR SOLAR",
    "BLOQUEADOR SOLAR", "REPELENTE", "CURITAS", "GASAS", "ALCOHOL",
    "ANTISÉPTICO", "ANTISEPTICO", "TERMÓMETRO", "TERMOMETRO",
    "GLUCÓMETRO", "GLUCOMETRO", "TIRAS REACTIVAS", "CUBREBOCAS",
    "ENJUAGUE BUCAL", "PASTILLAS PARA LA GARGANTA", "ANTIPIRÉTICO",
    "ANTIPIRETICO", "LAXANTE", "ANTIDIARREICO", "ANTIÁCIDOS",
    "FÓRMULA INFANTIL", "FORMULA INFANTIL", "LECHE EN POLVO",
    "TOALLAS HÚMEDAS", "TOALLAS HUMEDAS", "CREMA PARA BEBÉ",
    "CREMA PARA BEBE", "CONDONES", "PRUEBA DE EMBARAZO",
    "CUIDADO PERSONAL", "COLONIA", "PERFUME", "MAQUILLAJE",
    "RASTRILLO", "RASTRILLOS", "ENERGIZANTE", "HIDRATANTE",
    # --- Ampliación 2: más categorías de farmacia / autoservicio ---
    "ANTIVIRAL", "ANTIMICÓTICO", "ANTIMICOTICO", "ANTIESPASMÓDICO",
    "ANTIESPASMODICO", "DESCONGESTIONANTE", "EXPECTORANTE",
    "ANTITUSIVO", "PROBIÓTICO", "PROBIOTICO", "PREBIÓTICO",
    "COLÁGENO", "COLAGENO", "OMEGA", "CALCIO", "HIERRO",
    "ÁCIDO FÓLICO", "ACIDO FOLICO", "MELATONINA", "MAGNESIO",
    "INSULINA", "LANCETAS", "JERINGAS", "TIRAS DE GLUCOSA",
    "OXÍMETRO", "OXIMETRO", "BAUMANÓMETRO", "BAUMANOMETRO",
    "CUBREBOCA", "GUANTES", "FAJA", "RODILLERA", "TOBILLERA",
    "MUÑEQUERA", "BASTÓN", "BASTON", "SILLA DE RUEDAS", "MULETAS",
    "GOTAS OFTÁLMICAS", "GOTAS OFTALMICAS", "LENTES DE CONTACTO",
    "SOLUCIÓN PARA LENTES", "SOLUCION PARA LENTES",
    "PRUEBA COVID", "PRUEBA DE GLUCOSA", "PRUEBA RÁPIDA",
    "PRUEBA RAPIDA", "ANTICONCEPTIVO", "PARCHE ANTICONCEPTIVO",
    "LUBRICANTE ÍNTIMO", "LUBRICANTE INTIMO", "GEL ÍNTIMO",
    "TOALLA SANITARIA", "TAMPÓN", "TAMPON", "COPA MENSTRUAL",
    "REFRESCO", "AGUA MINERAL", "JUGO", "NÉCTAR", "NECTAR",
    "BOTANA", "PAPAS FRITAS", "GALLETAS SALADAS", "GALLETAS DULCES",
    "PASTELITO", "CHICLE", "CHICLES", "PALETA", "PALETAS",
    "BOLÍGRAFOS", "PLUMÓN", "PLUMONES", "CUADERNO", "MOCHILA",
    "JUGUETE", "PELUCHE", "REGALO", "TARJETA DE REGALO",
    "AMBIENTADOR", "INSECTICIDA", "TRAMPA PARA INSECTOS",
    "CLORO", "PASTILLAS SANITIZANTES", "GEL ANTIBACTERIAL",
    "GEL ANTISÉPTICO", "GEL ANTISEPTICO",
    # --- Ampliación 3: más categorías de autoservicio ---
    "ALIMENTO PARA PERRO", "ALIMENTO PARA GATO", "CROQUETAS",
    "ARENA PARA GATO", "COLLAR ANTIPULGAS", "SHAMPOO PARA MASCOTA",
    "LECHE", "LECHE DESLACTOSADA", "YOGHURT BEBIBLE", "CREMA ÁCIDA",
    "CREMA ACIDA", "QUESO", "QUESO CREMA", "MANTEQUILLA", "MARGARINA",
    "GELATINA", "FLAN", "HELADO", "PALETA HELADA",
    "SALSA CATSUP", "MOSTAZA", "MAYONESA", "VINAGRE", "CONSOMÉ",
    "CONSOME", "SAZONADOR", "ESPECIAS", "CHILE EN POLVO",
    "PASTA PARA SOPA", "FIDEO", "ARROZ", "FRIJOL", "LENTEJA",
    "HARINA", "AZÚCAR", "AZUCAR", "SAL", "MIEL",
    "PAN BLANCO", "PAN INTEGRAL", "PAN DULCE", "TORTILLA",
    "CEREAL DE CAJA", "BARRA DE CEREAL", "BARRITA",
    "PILA ALCALINA", "PILA RECARGABLE", "CARGADOR", "AUDÍFONOS",
    "AUDIFONOS", "CABLE USB", "FOCO", "FOCO LED", "EXTENSIÓN",
    "EXTENSION",
    "LIMPIADOR PARA AUTO", "AMBIENTADOR PARA AUTO", "ACEITE PARA MOTOR",
    "LIMPIA PARABRISAS",
    "BIBERÓN", "BIBERON", "CHUPÓN", "CHUPON", "PORTABEBÉ", "PORTABEBE",
    "COCHE PARA BEBÉ", "COCHE PARA BEBE", "ANDADERA", "MOISÉS",
    "MOISES",
    "CHOCOLATE EN BARRA", "CHOCOLATE EN POLVO", "CAJETA", "CAJETA DE LECHE",
    "GOMITAS", "MALVAVISCO",
    "DESINFECTANTE", "LIMPIA PISOS", "LIMPIADOR MULTIUSOS",
    "QUITAMANCHAS", "BLANQUEADOR",
    "ENCENDEDOR", "CERILLOS",
    # --- Ampliación: categorías faltantes detectadas vs. farmaciasguadalajara.com (jul 2026) ---
    # Cuidado del Pie (SUPER/Higiene)
    "PEDICURE", "PANTIMEDIAS", "TOBIMEDIAS", "TALCO PARA PIES", "SPRAY PARA PIES",
    # Hogar: Desechables
    "BOLSA HERMÉTICA", "BOLSA HERMETICA", "BOLSA DE BASURA", "BOLSA PARA BASURA",
    "CUBIERTOS DESECHABLES", "PALILLOS", "POPOTES", "PAPEL ALUMINIO",
    "PLATOS DESECHABLES", "VASOS DESECHABLES",
    # Hogar: Cuidado del Calzado
    "LUSTRADOR", "CERA PARA CALZADO", "BETÚN", "BETUN",
    # Hogar: Velas y Veladoras
    "VELA", "VELADORA",
    # Farmacia: Dermatología especializada
    "ANTIHERPÉTICO", "ANTIHERPETICO", "ESCABICIDA", "TRATAMIENTO ANTI VPH",
    # Farmacia: Diabetes y Endocrinas
    "DIURÉTICO", "DIURETICO",
    # Farmacia: Accesorios Médicos
    "NEBULIZADOR",
    # Farmacia: Circulatorio adicional
    "ANTIANÉMICO", "ANTIANEMICO", "ANTICOLESTEROL", "HEMOSTÁTICO", "HEMOSTATICO",
    "LIPOTRÓPICO", "LIPOTROPICO", "TÓNICO RECONSTITUYENTE", "TONICO RECONSTITUYENTE",
    "VASOCONSTRICTOR",
    # Farmacia: Curaciones adicional
    "BOTIQUÍN", "BOTIQUIN", "VENDA", "VENDITA", "PARCHE ADHESIVO",
    # Alimentos: Carnes Frías
    "CHORIZO", "TOCINO", "PEPPERONI", "CARNE SECA",
    # Alimentos: Enlatados
    "SARDINA", "FRUTA EN ALMÍBAR", "FRUTA EN ALMIBAR",
    # Alimentos: Congelados
    "HIELO",
    # Alimentos: Panadería adicional
    "BOLLO", "PAN PARA HOT DOG", "PAN MOLIDO", "CRUTÓN", "CRUTON", "PAN TOSTADO",
    # Bebidas: Cerveza / Vinos / Licores
    "CERVEZA", "VINO", "VINO TINTO", "VINO BLANCO", "LICOR", "TEQUILA", "RON",
    "WHISKY", "BRANDY",
    # Belleza: Cosméticos adicional
    "MÁSCARA DE PESTAÑAS", "MASCARA DE PESTAÑAS", "BASE DE MAQUILLAJE",
    # Electrónicos: Cómputo
    "MEMORIA SD", "MEMORIA USB", "LECTOR DE MEMORIAS",
    # Hogar: Jardín y Ferretería adicional
    "HERRAMIENTA",
    # Juguetería adicional
    "JUEGO DE MESA", "JUEGO DE CREATIVIDAD",
    # --- Ampliación: categorías confirmadas en footer/menú de farmaciasguadalajara.com ---
    # Salud: Parto (subcategoría propia junto a Sistema Nervioso, Óseo, etc.)
    "PARTO",
    # Servicio propio de sucursal (aparece como categoría junto a Papelería en el footer)
    "RECARGA DE TIEMPO AIRE",
]

# ── Precompilación de patrones (una sola vez al importar el módulo) ────────
# parse_descripcion() se llama una vez por cada fila del Excel; antes, cada
# llamada recompilaba cientos/miles de regex (uno por cada TIPO y MARCA).
# Con listas de ~400 TIPOS y ~1500 MARCAS, eso son miles de compilaciones
# de regex repetidas en cada fila, lo cual es muy costoso en CPU
# (crítico en hosting con CPU limitada, como el plan gratuito de Render).
# Aquí se compilan una sola vez y se reutilizan en todas las llamadas.
_TIPOS_PATRONES = [
    (t, re.compile(r'^' + re.escape(t) + r'(?:\s|,|$)'))
    for t in sorted(TIPOS, key=len, reverse=True)
]
_MARCAS_ORDENADAS = sorted(MARCAS, key=len, reverse=True)
_MARCAS_PATRONES_INICIO = [
    (m, re.compile(r'^' + re.escape(m) + r'(?:\s|,|$)'))
    for m in _MARCAS_ORDENADAS
]
_MARCAS_PATRONES_ANYWHERE = [
    (m, re.compile(r'(?:^|\s)' + re.escape(m) + r'(?=\s|,|$)'))
    for m in _MARCAS_ORDENADAS
]

def parse_descripcion(desc):
    raw = str(desc).strip().upper()
    raw = re.sub(r'\s+', ' ', raw)  # colapsar espacios dobles/múltiples (frecuentes en catálogos reales)

    exc_m   = re.search(r'(\*[^\*]+)$', raw)
    excepto = exc_m.group(1).strip() if exc_m else ''
    base    = raw[:exc_m.start()].strip() if excepto else raw

    tipo  = ''
    resto = base
    for t, pat in _TIPOS_PATRONES:
        if pat.match(resto):
            tipo  = t
            resto = resto[len(t):].strip().lstrip(',').strip()
            break

    if not tipo and resto.startswith('LÍNEA'):
        tipo  = 'LÍNEA'
        resto = resto[5:].strip()

    marca   = ''
    detalle = resto
    for m, pat in _MARCAS_PATRONES_INICIO:
        if pat.match(resto):
            marca   = m
            detalle = resto[len(m):].strip().lstrip(',').strip()
            break

    # Si la marca no está pegada al inicio (p.ej. "CREMA HIDRATANTE CERAVE"),
    # buscarla en cualquier posición dentro de 'resto' con límites de palabra.
    if not marca and resto:
        for m, pat in _MARCAS_PATRONES_ANYWHERE:
            match = pat.search(resto)
            if match:
                marca = m
                antes  = resto[:match.start()].strip().rstrip(',').strip()
                despues = resto[match.end():].strip().lstrip(',').strip()
                detalle = (antes + ' ' + despues).strip() if antes and despues else (antes or despues)
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
