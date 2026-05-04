#!/usr/bin/env python3
"""
=======================================================================
LATAM Airlines Group | OSINT 
Departamento: CTI 
Módulos: RSS de aviación/negocios + Dorks avanzados sobre Bing
=======================================================================
"""
import re, os, csv, time, random, logging
from datetime import datetime

import requests, feedparser
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator

# --------------------- CONFIGURACIÓN ---------------------
OUTPUT_CSV = "CTI_LATAM_informe.csv"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('latam_osint.log'), logging.StreamHandler()])
logger = logging.getLogger("LATAM_CTI")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) Version/17.1 Mobile/15E148 Safari/604.1",
]

RSS_FEEDS = [
    "https://www.flightglobal.com/rss",
    "https://simpleflying.com/feed/",
    "https://www.aviacionline.com/rss",
    "https://www.aerotime.aero/feed/",
    "https://www.latercera.com/arcio/rss/",
    "https://rpp.pe/feed",
    "https://www.lanacion.com.ar/arcio/rss/",
    "https://www.clarin.com/rss/",
    "https://www.larepublica.co/rss/economia",
    "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "https://www.forbes.com/business/feed/",
    "https://www.bbc.com/news/business/rss.xml",
    "https://www.aviation24.be/feed/",
    "https://www.airlive.net/feed/",
    "https://aviationweek.com/rss.xml",
    "https://simpleflying.com/feed/",
    "https://airinsight.com/feed/",
    "https://atwonline.com/rss.xml",
    "https://aerolatinnews.com/feed/",
    "https://www.aeroflap.com.br/feed/",
    "https://actualidadaeroespacial.com/feed/",
    "https://aviaciondigital.com/feed/",
    "https://www.preferente.com/feed/",
    "https://www.aerotime.aero/feed/",
    "https://www.flightradar24.com/blog/feed/",
    "https://runwaygirlnetwork.com/feed/",
    "https://aviationsourcenews.com/feed/",
    "https://www.aviacionline.com/rss",
    "https://noticiasaereas.com/feed/",
    "https://www.breakingtravelnews.com/rss",
    "https://www.aviationtoday.com/feed/",
    "https://thepointsguy.com/feed/",
    "https://www.travelmole.com/feed/"
]

DORKS_BING = [
    '"LATAM Airlines" accidente OR incidente OR emergencia',
    '"LATAM" cancelación OR retraso OR "mal tiempo"',
    'site:latercera.com "LATAM"',
    'site:emol.com "LATAM"',
    '"LATAM" hack OR ciberataque OR ransomware OR filtración',
    '"LATAM" vulnerabilidad OR brecha OR "fuga de datos"',
    '"LATAM Airlines" deuda OR bancarrota OR reestructuración',
    '"LATAM" despido OR huelga OR sindicato',
    '"LATAM Airlines" demanda OR juicio OR multa',
    'filetype:pdf "LATAM Airlines" informe OR reporte',
]

CONTEXTO_LATAM = [
    'airline', 'aerolinea', 'aerolínea', 'vuelo', 'avión', 'airport', 'aeropuerto',
    'pasajero', 'passenger', 'tripulación', 'crew', 'ruta', 'a320', 'a350', 'b787',
    'cargo', 'mro', 'airbus', 'boeing', 'acción', 'stock', 'share', 'bancarrota',
    'bankruptcy', 'deuda', 'debt', 'quiebre', 'reestructura', 'despido', 'layoff',
    'ganancia', 'profit', 'pérdida', 'loss', 'ingreso', 'revenue', 'demanda',
    'lawsuit', 'sindicato', 'union', 'huelga', 'strike', 'accidente', 'accident',
    'incidente', 'emergencia', 'hack', 'hackeo', 'ciber', 'cyber', 'ransomware',
    'filtración', 'leak', 'breach', 'vulnerabilidad', 'chile', 'perú', 'brasil',
    'argentina', 'colombia',
]

analyzer = SentimentIntensityAnalyzer()
translator = GoogleTranslator(source='auto', target='en')

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.bing.com/",
    }

def clean_html(raw):
    return re.sub(r'<[^>]+>', '', raw).strip()

def es_relevante(texto):
    t = texto.lower()
    if not any(x in t for x in ['latam', 'latam airlines', 'latam cargo', 'latam pass']):
        return False
    return any(p in t for p in CONTEXTO_LATAM)

def calcular_sentimiento(texto):
    try:
        traducido = translator.translate(texto[:500])
        return analyzer.polarity_scores(traducido)['compound']
    except Exception as e:
        logger.warning(f"Error sentimiento: {e}")
        return analyzer.polarity_scores(texto[:500])['compound']

# --------------------- CSV ---------------------
def load_existing_links():
    links = set()
    if os.path.isfile(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                links.add(row.get('link', ''))
    return links

def save_csv(items):
    if not items:
        return []
    unicos = {it['link']: it for it in items if it.get('link')}
    existing = load_existing_links()
    nuevos = [it for link, it in unicos.items() if link not in existing]
    if not nuevos:
        logger.info("Sin novedades para guardar.")
        return []
    file_exists = os.path.isfile(OUTPUT_CSV)
    campos = ['fuente', 'canal', 'titulo', 'link', 'resumen', 'fecha', 'sentimiento']
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if not file_exists:
            w.writeheader()
        w.writerows(nuevos)
    logger.info(f"CSV actualizado (+{len(nuevos)} registros)")
    return nuevos

# --------------------- RSS (con estadísticas) ---------------------
def recolectar_rss():
    resultados = []
    total_feeds = len(RSS_FEEDS)
    feeds_ok = 0
    total_entradas = 0
    total_relevantes = 0

    print(f"\n🔍 Consultando {total_feeds} fuentes RSS...")
    for url in RSS_FEEDS:
        try:
            resp = requests.get(url, headers=get_headers(), timeout=15)
            feed = feedparser.parse(resp.content)
            entradas_feed = len(feed.entries)
            total_entradas += entradas_feed
            relevantes_feed = 0
            for e in feed.entries:
                titulo = e.get('title', '')
                link = e.get('link', '')
                desc = clean_html(e.get('description', '') or e.get('summary', ''))
                texto = f"{titulo}. {desc}"
                if not es_relevante(texto):
                    continue
                relevantes_feed += 1
                total_relevantes += 1
                sent = calcular_sentimiento(texto)
                resultados.append({
                    'fuente': 'RSS',
                    'canal': url.split('/')[2],
                    'titulo': titulo,
                    'link': link,
                    'resumen': desc[:300],
                    'fecha': e.get('published', datetime.now().isoformat()),
                    'sentimiento': sent
                })
            feeds_ok += 1
            logger.info(f"   {url.split('/')[2]}: {entradas_feed} arts, {relevantes_feed} relevantes")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as ex:
            logger.warning(f"   {url} -> error: {ex}")

    print(f"\n📊 ESTADÍSTICAS RSS:")
    print(f"   Feeds activos: {feeds_ok}/{total_feeds}")
    print(f"   Total artículos descargados: {total_entradas}")
    print(f"   Relevantes para LATAM: {total_relevantes}")
    print(f"   → {len(resultados)} noticias pasan al almacenamiento")
    return resultados

# --------------------- BING DORKS ---------------------
def buscar_en_bing(query, num=5):
    session = requests.Session()
    session.headers.update(get_headers())
    try:
        session.get("https://www.bing.com", timeout=10)
        time.sleep(random.uniform(1, 3))
    except:
        pass

    for intento in range(2):
        resultados = []
        for start in range(1, num + 1, 10):
            params = {'q': query, 'first': start, 'FORM': 'PERE' if start == 1 else f'PERE{start//10}'}
            try:
                resp = session.get("https://www.bing.com/search", params=params, timeout=15)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.select('li.b_algo'):
                    h2 = item.select_one('h2 a')
                    if not h2:
                        continue
                    link = h2.get('href', '')
                    titulo = h2.get_text(strip=True)
                    snippet_tag = item.select_one('.b_caption p') or item.select_one('.b_lineclamp2')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    if link and titulo:
                        resultados.append({'titulo': titulo, 'link': link, 'snippet': snippet})
                    if len(resultados) >= num:
                        break
                if len(resultados) >= num:
                    break
                time.sleep(random.uniform(3.5, 7.0))
            except Exception as e:
                logger.error(f"Error Bing: {e}")
                break
        if resultados:
            logger.info(f"   -> {len(resultados)} resultados")
            return resultados
        if intento < 1:
            time.sleep(15)
    return []

def recolectar_dorks():
    todos = []
    seen = set()
    total_dorks = len(DORKS_BING)
    print(f"\n🔍 Ejecutando {total_dorks} dorks en Bing...")
    for i, dork in enumerate(DORKS_BING, 1):
        print(f"   Dork {i}/{total_dorks}: {dork}")
        logger.info(f"Bing Dork: {dork}")
        resultados = buscar_en_bing(dork, num=5)
        for r in resultados:
            if r['link'] not in seen:
                seen.add(r['link'])
                texto = f"{r['titulo']}. {r['snippet']}"
                sent = calcular_sentimiento(texto)
                todos.append({
                    'fuente': 'Dork',
                    'canal': 'bing',
                    'titulo': r['titulo'],
                    'link': r['link'],
                    'resumen': r['snippet'][:300],
                    'fecha': datetime.now().isoformat(),
                    'sentimiento': sent
                })
        time.sleep(random.uniform(10, 18))
    print(f"\n📊 ESTADÍSTICAS DORKS:")
    print(f"   Dorks ejecutados: {total_dorks}")
    print(f"   Resultados únicos obtenidos: {len(todos)}")
    return todos

# --------------------- MENÚ ---------------------
def menu():
    print("""
    ╔══════════════════════════════════════════╗
    ║        CTI LATAM | Estadísticas          ║
    ╠══════════════════════════════════════════╣
    ║  1. Solo RSS                             ║
    ║  2. Solo Dorks (Bing)                    ║
    ║  3. Ciclo completo (RSS + Dorks)         ║
    ║  0. Salir                                ║
    ╚══════════════════════════════════════════╝
    """)

def main():
    while True:
        menu()
        op = input("Opción: ").strip()
        if op == '0':
            break
        elif op == '1':
            rss = recolectar_rss()
            new = save_csv(rss)
            print(f"\n💾 Guardados en CSV: {len(new)} nuevos registros (de {len(rss)} candidatos)")
        elif op == '2':
            dorks = recolectar_dorks()
            new = save_csv(dorks)
            print(f"\n💾 Guardados en CSV: {len(new)} nuevos registros (de {len(dorks)} candidatos)")
        elif op == '3':
            print("\n=== CICLO COMPLETO ===")
            rss = recolectar_rss()
            dorks = recolectar_dorks()
            all_items = rss + dorks
            new = save_csv(all_items)
            print(f"\n📦 RESUMEN FINAL:")
            print(f"   RSS → {len(rss)} candidatos")
            print(f"   Dorks → {len(dorks)} candidatos")
            print(f"   Total nuevos en CSV → {len(new)}")
            criticas = [n for n in all_items if n.get('sentimiento') is not None and n['sentimiento'] <= -0.6]
            if criticas:
                print(f"\n🚨 {len(criticas)} AMENAZAS CRÍTICAS:")
                for c in criticas[:5]:
                    print(f"   • [{c['canal']}] {c['titulo']} (sent: {c['sentimiento']:.2f})")
            else:
                print("\n✅ Sin amenazas críticas en este ciclo.")
        else:
            print("Opción inválida.")
        print("="*50)

if __name__ == "__main__":
    print("""
     ██████╗ ████████╗██╗    ██╗      █████╗ ████████╗ █████╗ ███╗   ███╗
    ██╔════╝ ╚══██╔══╝██║    ██║     ██╔══██╗╚══██╔══╝██╔══██╗████╗ ████║
    ██║         ██║   ██║    ██║     ███████║   ██║   ███████║██╔████╔██║
    ██║         ██║   ██║    ██║     ██╔══██║   ██║   ██╔══██║██║╚██╔╝██║
    ╚██████╗    ██║   ██║    ███████╗██║  ██║   ██║   ██║  ██║██║ ╚═╝ ██║
     ╚═════╝    ╚═╝   ╚═╝    ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝
                            
                        [ Cyber Threat Intelligence ]
    """)
    main()
