import requests
import xml.etree.ElementTree as ET
from src.config import MEUDANFE_API_XML_URL, MEUDANFE_API_DANFE_URL, REQUEST_TIMEOUT_SECONDS

def extract_note_number_from_xml(xml_content, logger):
    """
    Extrai o número da nota fiscal (nNF) do conteúdo XML.
    Assume que o XML é uma NF-e padrão.
    """
    try:
        # Parseia o XML. Remove namespaces se o find() estiver com problemas,
        root = ET.fromstring(xml_content)
        
        #Loop para verificar se tem uma tag chamada nNF , se tiver retorna o texto dessa tag
        for elem in root.iter():
            if 'nNF' in elem.tag:
                return elem.text.strip()

        # Fallback para um padrão mais específico de NF-e
        # <NFe><infNFe><ide><nNF>
        nfe_node = root.find('.//{http://www.portalfiscal.inf.br/nfe}NFe')
        if nfe_node:
            inf_nfe_node = nfe_node.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            if inf_nfe_node:
                ide_node = inf_nfe_node.find('.//{http://www.portalfiscal.inf.br/nfe}ide')
                if ide_node:
                    n_nf_element = ide_node.find('.//{http://www.portalfiscal.inf.br/nfe}nNF')
                    if n_nf_element is not None:
                        return n_nf_element.text.strip()

        logger.warning("Não foi possível encontrar a tag 'nNF' no XML.")
        return None
    except ET.ParseError as e:
        logger.error(f"Erro ao parsear XML: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao extrair número da nota do XML: {e}", exc_info=True)
        return None

def process_single_key(key, logger):
    """
    Consulta e baixa o XML, e gera o PDF da DANFE para uma dada chave de acesso.
    Retorna (xml_content, pdf_content, note_number) ou (None, None, None) em caso de falha.
    """
    xml_content = None
    pdf_content = None
    note_number = None

    logger.info(f"Iniciando download do XML e geração do DANFE para a chave: {key}")

    try:
        # 1. Download do XML
        logger.debug(f"Tentando baixar XML de: {MEUDANFE_API_XML_URL}{key}") # Use debug para ver URLs completas
        xml_response = requests.get(
            f"{MEUDANFE_API_XML_URL}{key}",
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        xml_response.raise_for_status() # Lança HTTPError para status 4xx/5xx
        xml_content = xml_response.content

        # 2. Extrair número da nota do XML
        note_number = extract_note_number_from_xml(xml_content, logger)
        if not note_number:
            logger.error(f"Não foi possível extrair o número da nota do XML para a chave: {key}. Pulando DANFE.")
            return None, None, None

        # 3. Gerar DANFE PDF via API
        logger.debug(f"Tentando gerar DANFE de: {MEUDANFE_API_DANFE_URL} para nota: {note_number}")
        danfe_payload = {"chave": key} # A API pode exigir outros parâmetros
        danfe_response = requests.post(
            MEUDANFE_API_DANFE_URL,
            json=danfe_payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        danfe_response.raise_for_status()
        pdf_content = danfe_response.content

        logger.info(f"Sucesso ao obter XML e DANFE para a nota: {note_number} (chave: {key[:10]}...).")
        return xml_content, pdf_content, note_number

    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao processar chave {key}: Status {e.response.status_code} - {e.response.text}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão para a chave {key}: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Tempo esgotado para a chave {key}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição inesperado para a chave {key}: {e}")
    except Exception as e:
        logger.critical(f"Erro crítico e inesperado no estágio de transformação para a chave {key}: {e}", exc_info=True)

    return None, None, None # Retorna None em caso de falha