# src/config.py

import os

# Caminhos das pastas do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FOLDER = os.path.join(BASE_DIR, "CHAVES NOTAS")
OUTPUT_BASE_FOLDER = os.path.join(BASE_DIR, "NOTAS E XML")
LOG_FOLDER = os.path.join(BASE_DIR, "LOGS")

# --- URLs e APIs para meudanfe.com.br ---

# URL BASE da API para DOWNLOAD DE XML pela chave de acesso (CONFIRMADO: É POST, e chave vai na URL!)
MEUDANFE_API_XML_DOWNLOAD_BASE_URL = "https://ws.meudanfe.com/api/v1/get/nfe/xml/"

# URL da API para GERAR DANFE PDF enviando o XML no corpo (POST, text/plain)
MEUDANFE_API_DANFE_GENERATION_URL = "https://ws.meudanfe.com/api/v1/get/nfe/xmltodanfepdf/API"

# Sua chave de API (MUITO IMPORTANTE: OBTENHA ESTA CHAVE NO SITE MEUDANFE.COM.BR!)
# Se a API de download de XML ou a de geração de DANFE exigirem, preencha aqui.
MEUDANFE_API_KEY = "SUA_CHAVE_AQUI" # <-- COLOQUE SUA CHAVE AQUI!

# Outras configurações
REQUEST_TIMEOUT_SECONDS = 60