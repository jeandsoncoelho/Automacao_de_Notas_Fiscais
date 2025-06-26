# src/pipeline/transform.py

import requests
import xml.etree.ElementTree as ET

# Remover importações de selenium e webdriver_manager!
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
# from webdriver_manager.chrome import ChromeDriverManager


from src.config import (
    MEUDANFE_API_XML_DOWNLOAD_BASE_URL,  # URL base para download de XML
    MEUDANFE_API_DANFE_GENERATION_URL,  # URL para gerar DANFE PDF
    MEUDANFE_API_KEY,  # Chave de API
    REQUEST_TIMEOUT_SECONDS,
)


# A função extract_note_number_from_xml permanece a mesma
def extract_note_number_from_xml(xml_content, logger):
    """
    Extrai o número da nota fiscal (nNF) do conteúdo XML.
    Assume que o XML é uma NF-e padrão.
    """
    try:
        logger.info(f"xml{xml_content}")
        root = ET.fromstring(xml_content)

        logger.info(f"nfe number{root}")
        n_nf_element = None
        for elem in root.iter():
            if elem.tag.endswith("nNF"):
                n_nf_element = elem
                break

        if n_nf_element is not None and n_nf_element.text:
            return n_nf_element.text.strip()

        nfe_namespace = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
        nfe_node = root.find(".//nfe:NFe", nfe_namespace)
        if nfe_node:
            inf_nfe_node = nfe_node.find("nfe:infNFe", nfe_namespace)
            if inf_nfe_node:
                ide_node = inf_nfe_node.find("nfe:ide", nfe_namespace)
                if ide_node:
                    n_nf_element = ide_node.find("nfe:nNF", nfe_namespace)
                    if n_nf_element is not None and n_nf_element.text:
                        return n_nf_element.text.strip()

        logger.warning("Não foi possível encontrar a tag 'nNF' no XML.")
        return None
    except ET.ParseError as e:
        logger.error(f"Erro ao parsear XML: {e}")
        return None
    except Exception as e:
        logger.error(
            f"Erro inesperado ao extrair número da nota do XML: {e}", exc_info=True
        )
        return None


# %%
def process_single_key(key, logger):
    """
    Processa uma única chave de acesso:
    1. Baixa o XML da nota fiscal usando a API direta (POST, chave na URL, payload texto puro).
    2. Gera o PDF da DANFE enviando o XML baixado para a API de conversão (POST, XML no corpo, text/plain).
    Retorna (xml_content, pdf_content, note_number) ou (None, None, None) em caso de falha.
    """
    xml_content = None
    pdf_content = None
    note_number = None

    logger.info(f"Iniciando download do XML e geração do DANFE para a chave: {key}")

    try:
        # --- PASSO 1: BAIXAR O XML DA NOTA USANDO A API DIRETA (POST) ---
        xml_download_url = f"https://ws.meudanfe.com/api/v1/get/nfe/xml/{key}"

        # Headers para a requisição de download do XML (baseados nos que você forneceu)
        xml_headers = {
            "authority": "ws.meudanfe.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "text/plain;charset=UTF-8",  # MANTÉM ESTE!
            "origin": "https://www.meudanfe.com.br",
            "referer": "https://www.meudanfe.com.br/",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        # Payload para a requisição de download do XML (a própria chave codificada em bytes)
        xml_payload = key.encode("utf-8")

        logger.debug(
            f"Tentando baixar XML de: {xml_download_url} com payload de {len(xml_payload)} bytes."
        )

        xml_response = requests.post(
            xml_download_url,
            headers=xml_headers,
            data=xml_payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        # xml_response.raise_for_status()  # Lança exceção para erros HTTP (4xx, 5xx)

        xml_content = xml_response.content


        if not xml_content:
            logger.error(
                f"Não foi recebido conteúdo XML válido ao tentar baixar para a chave: {key}"
            )
            return None, None, None

        logger.info(f"XML baixado com sucesso para a chave: {key[:10]}...")

        # Extrair número da nota do XML
        note_number = extract_note_number_from_xml(xml_content, logger)
        logger.info(f"XML note number: {note_number}...")

        if not note_number:
            logger.error(
                f"Não foi possível extrair o número da nota do XML baixado para a chave: {key}. Pulando geração de DANFE."
            )
            return None, None, None

        # --- PASSO 2: GERAR DANFE PDF ENVIANDO O XML PARA A API DE CONVERSÃO ---
        danfe_headers = {
            "Content-Type": "text/plain",  # Conforme seu comando curl anterior para DANFE
        }
        # Adicionar a API Key para a API de DANFE, SE for necessária e você a tiver.
        # if MEUDANFE_API_KEY and MEUDANFE_API_KEY != "SUA_CHAVE_AQUI":
        #     danfe_headers["X-Api-Key"] = (
        #         MEUDANFE_API_KEY  # OU 'Authorization': f'Bearer {MEUDANFE_API_KEY}',
        #     )

        danfe_payload = xml_content  # Envie o conteúdo BINÁRIO do XML diretamente

        logger.debug(
            f"Tentando gerar DANFE de: {MEUDANFE_API_DANFE_GENERATION_URL} para nota: {note_number}"
        )
        danfe_response = requests.post(
            MEUDANFE_API_DANFE_GENERATION_URL,
            data=danfe_payload,  # Use 'data' para enviar o conteúdo bruto (text/plain)
            headers=danfe_headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        # danfe_response.raise_for_status()  # Lança exceção para erros HTTP
        pdf_content = (
            danfe_response.content
        )  # O PDF geralmente vem como conteúdo binário direto

        logger.info(
            f"Sucesso ao obter XML e DANFE para a nota: {note_number} (chave: {key[:10]}...)."
        )
        return xml_content, pdf_content, note_number

    except requests.exceptions.HTTPError as e:
        logger.error(
            f"Erro HTTP ao processar chave {key}: Status {e.response.status_code} - Resposta: {e.response.text}"
        )
        if e.response.status_code == 403:
            logger.error(
                "POSSÍVEL PROBLEMA: Acesso negado. Verifique sua API Key ou permissões."
            )
        elif e.response.status_code == 404:
            logger.error(
                "POSSÍVEL PROBLEMA: Chave de acesso não encontrada ou URL incorreta."
            )
        elif e.response.status_code == 400:
            logger.error(
                "POSSÍVEL PROBLEMA: Requisição inválida. O formato do payload ou headers pode estar incorreto para a API de XML ou DANFE."
            )
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão para a chave {key}: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Tempo esgotado para a chave {key}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição inesperado para a chave {key}: {e}")
    except Exception as e:
        logger.critical(
            f"Erro crítico e inesperado no estágio de transformação para a chave {key}: {e}",
            exc_info=True,
        )

    return None, None, None  # Retorna None em caso de qualquer falha
