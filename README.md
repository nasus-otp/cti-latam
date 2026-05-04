🛰️ LATAM Airlines OSINT Pipeline 🛰️ 

Pipeline automatizado de ciberinteligencia (CTI) para monitorizar la reputación de **LATAM Airlines Group** usando fuentes abiertas (OSINT).  
Recolecta noticias desde **feeds RSS** especializados y realiza **búsquedas avanzadas (dorks)** en Bing, filtra contenido relevante, analiza el sentimiento con VADER y almacena los resultados en CSV sin duplicados.

****Instalación****

Debian:

1. Clona el repositorio:
    ~~~
    git clone https://github.com/nasus-otp/cti-latam.git
    cd latam-osint-pipeline

2. Crea un entorno virtual (opcional pero recomendado):
    ~~~
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows

3. Instala las dependencias:
    ~~~
    pip install requests feedparser beautifulsoup4 vaderSentiment deep-translator

Aparecerá un menú interactivo:

    Opción 1 – Solo RSS (12 fuentes de aviación, negocios y prensa regional)
    Opción 2 – Solo Dorks (10 búsquedas avanzadas en Bing)
    Opción 3 – Ciclo completo (RSS + Dorks + alertas de sentimiento crítico)

Los resultados se guardan en CTI_LATAM_informe.csv y el registro de actividad en latam_osint.log.

📋 Requisitos:

    Python 3.9 o superior
    Conexión a internet para acceder a los feeds y a Bing

📄 Licencia:

    Este proyecto es de uso académico. Consulta los términos de uso de los sitios web consultados antes de utilizarlo en producción.
