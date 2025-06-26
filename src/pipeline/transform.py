import requests
import xml.etree.ElementTree as ET
from src.config import (
    MEUDANFE_API_XML_DOWNLOAD_URL,        # Importa a URL para baixar o XML (você precisa confirmar esta URL)
    MEUDANFE_API_DANFE_GENERATION_URL,    # Importa a URL para gerar a DANFE PDF
    MEUDANFE_API_KEY,                     # Importa a chave de API (se necessário, verifique a doc)
    REQUEST_TIMEOUT_SECONDS
)

def extract_note_number_from_xml(xml_content, logger):
    """
    Extrai o número da nota fiscal (nNF) do conteúdo XML.
    Assume que o XML é uma NF-e padrão.
    """
    try:
        root = ET.fromstring(xml_content)
        
        # Abordagem mais robusta para encontrar a tag nNF, ignorando namespaces
        # Procura por qualquer elemento cuja tag termine com 'nNF'.
        # Isso é flexível, mas pode pegar tags não intencionais se 'nNF' aparecer em outro contexto.
        # Para NF-e, geralmente está sob <ide>
        n_nf_element = None
        for elem in root.iter():
            if elem.tag.endswith('nNF'):
                n_nf_element = elem
                break # Encontrou o primeiro, pode parar
        
        if n_nf_element is not None and n_nf_element.text:
            return n_nf_element.text.strip()

        # Fallback para o padrão específico de NF-e com namespace (mais preciso se o namespace for consistente)
        # O namespace é crucial aqui. Use o namespace correto da NFe.
        # Geralmente é "http://www.portalfiscal.inf.br/nfe"
        nfe_namespace = {'nfe': 'http://www.portalfiscal.inf.br/nfe'} # Defina o namespace
        
        nfe_node = root.find('.//nfe:NFe', nfe_namespace) # Busca o nó NFe
        if nfe_node:
            inf_nfe_node = nfe_node.find('nfe:infNFe', nfe_namespace) # Busca infNFe dentro de NFe
            if inf_nfe_node:
                ide_node = inf_nfe_node.find('nfe:ide', nfe_namespace) # Busca ide dentro de infNFe
                if ide_node:
                    n_nf_element = ide_node.find('nfe:nNF', nfe_namespace) # Busca nNF dentro de ide
                    if n_nf_element is not None and n_nf_element.text:
                        return n_nf_element.text.strip()

        logger.warning("Não foi possível encontrar a tag 'nNF' no XML. Verifique o formato do XML.")
        return None
    except ET.ParseError as e:
        logger.error(f"Erro ao parsear XML: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao extrair número da nota do XML: {e}", exc_info=True)
        return None


def process_single_key(key, logger):
    """
    Processa uma única chave de acesso:
    1. Baixa o XML da nota fiscal a partir da chave (MUITO IMPORTANTE: AINDA PRECISA DA API PARA ISSO).
    2. Gera o PDF da DANFE enviando o XML baixado para a API de conversão.
    Retorna (xml_content, pdf_content, note_number) ou (None, None, None) em caso de falha.
    """
    xml_content = None
    pdf_content = None
    note_number = None

    logger.info(f"Iniciando download do XML e geração do DANFE para a chave: {key}")

    try:
        # --- PASSO 1: BAIXAR O XML DA NOTA USANDO A CHAVE DE ACESSO ---
        # ATENÇÃO: Esta é a parte mais incerta e DEPENDE DA DOCUMENTAÇÃO REAL da API do meudanfe.com.br
        # para download de XML por chave. O endpoint MEUDANFE_API_XML_DOWNLOAD_URL no config.py
        # É UM PLACEHOLDER! Você precisa confirmar URL, método (GET/POST), payload e headers.

        download_xml_headers = {
            # Adicione 'Authorization' ou 'X-Api-Key' se a API de DOWNLOAD DE XML exigir
            # Exemplo: 'Authorization': f'Bearer {MEUDANFE_API_KEY}',
            # Exemplo: 'X-Api-Key': MEUDANFE_API_KEY,
            'Content-Type': 'application/json' # Ajuste conforme a API de download de XML exigir
        }
        download_xml_payload = {"chave": key} # Exemplo de payload. Verifique a documentação da API.

        logger.debug(f"Tentando baixar XML da URL: {MEUDANFE_API_XML_DOWNLOAD_URL} com chave: {key}")
        
        # É provável que seja um POST se a chave for enviada no corpo, ou GET se for na URL.
        # Por enquanto, vou manter POST como no exemplo anterior, mas ajuste conforme a API real.
        xml_download_response = requests.post(
            MEUDANFE_API_XML_DOWNLOAD_URL,
            json=download_xml_payload, # Use json= para enviar um dicionário como JSON
            headers=download_xml_headers,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        xml_download_response.raise_for_status() # Lança exceção para erros HTTP (4xx, 5xx)

        # O XML pode vir direto no response.content, ou dentro de um JSON (ex: response.json()['xml_data'])
        # Você PRECISA verificar o formato da resposta da API de download de XML.
        # Exemplo se for XML puro no content:
        xml_content = xml_download_response.content 
        
        # Exemplo se for JSON com o XML como string base64:
        # import base64
        # response_data = xml_download_response.json()
        # xml_base64_string = response_data.get('xmlBase64', '')
        # xml_content = base64.b64decode(xml_base64_string)

        # Exemplo se for JSON com o XML como string pura:
        # response_data = xml_download_response.json()
        # xml_content = response_data.get('xml_string', '').encode('utf-8')


        if not xml_content:
            logger.error(f"Não foi recebido conteúdo XML válido ao tentar baixar para a chave: {key}")
            return None, None, None

        logger.info(f"XML baixado com sucesso para a chave: {key[:10]}...")

        # Extrair número da nota do XML
        note_number = extract_note_number_from_xml(xml_content, logger)
        if not note_number:
            logger.error(f"Não foi possível extrair o número da nota do XML baixado para a chave: {key}. Pulando geração de DANFE.")
            return None, None, None

        # --- PASSO 2: GERAR DANFE PDF ENVIANDO O XML PARA A API DE CONVERSÃO ---
        danfe_headers = {
            'Content-Type': 'text/plain', # Conforme seu comando curl
            # Adicione 'Authorization' ou 'X-Api-Key' se a API de GERAÇÃO DE DANFE exigir
            # 'Authorization': f'Bearer {MEUDANFE_API_KEY}',
            # 'X-Api-Key': MEUDANFE_API_KEY,
        }
        
        # O corpo da requisição POST para a API de DANFE é o próprio conteúdo XML
        danfe_payload = xml_content # Envie o conteúdo binário do XML diretamente

        logger.debug(f"Tentando gerar DANFE de: {MEUDANFE_API_DANFE_GENERATION_URL} para nota: {note_number}")
        danfe_response = requests.post(
            MEUDANFE_API_DANFE_GENERATION_URL,
            data=danfe_payload, # Use 'data' para enviar o conteúdo bruto (text/plain)
            headers=danfe_headers,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        danfe_response.raise_for_status() # Lança exceção para erros HTTP
        pdf_content = danfe_response.content # O PDF geralmente vem como conteúdo binário direto

        logger.info(f"Sucesso ao obter XML e DANFE para a nota: {note_number} (chave: {key[:10]}...).")
        return xml_content, pdf_content, note_number

    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao processar chave {key}: Status {e.response.status_code} - Resposta: {e.response.text}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão para a chave {key}: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Tempo esgotado para a chave {key}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição inesperado para a chave {key}: {e}")
    except Exception as e:
        logger.critical(f"Erro crítico e inesperado no estágio de transformação para a chave {key}: {e}", exc_info=True)

    return None, None, None # Retorna None em caso de qualquer falha

