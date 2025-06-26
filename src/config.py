import os

# Caminhos das pastas do projeto
# Usa os.path.join para garantir compatibilidade entre sistemas operacionais (Windows/Linux/macOS)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Pega o diretório raiz do projeto

INPUT_FOLDER = os.path.join(BASE_DIR, "CHAVES NOTAS")
OUTPUT_BASE_FOLDER = os.path.join(BASE_DIR, "NOTAS E XML")
LOG_FOLDER = os.path.join(BASE_DIR, "LOGS")

# --- URLs e APIs para meudanfe.com.br (AJUSTADO CONFORME AS INFORMAÇÕES QUE VOCÊ FORNECEU) ---

# URL da API para gerar DANFE a partir de XML/Chave
# Este é o endpoint POST que você encontrou:
MEUDANFE_API_DANFE_GENERATION_URL = "https://ws.meudanfe.com/api/v1/get/nfe/xmltodanfepdf/API"

# ATENÇÃO: Você precisará encontrar a URL e o método (GET/POST) corretos
# para BAIXAR O XML da NF-e a partir da chave de acesso.
# Por enquanto, vou deixar um placeholder. Você precisa verificar na documentação da API.
# Exemplo (pode não ser o correto!):
MEUDANFE_API_XML_DOWNLOAD_URL = "https://ws.meudanfe.com/api/v1/get/nfe/xmltodanfepdf/API" # << VERIFIQUE ISTO NA DOCUMENTAÇÃO!

# Sua chave de API (MUITO IMPORTANTE: OBTENHA ESTA CHAVE NO SITE MEUDANFE.COM.BR!)
# Para fins de teste, você pode colar a chave aqui, mas para produção, use variáveis de ambiente.
MEUDANFE_API_KEY = "SUA_CHAVE_DE_API_AQUI" # <-- COLOQUE SUA CHAVE AQUI!

# Outras configurações (ex: timeout para requisições HTTP)
REQUEST_TIMEOUT_SECONDS = 60 # Tempo limite para as requisições (em segundos)