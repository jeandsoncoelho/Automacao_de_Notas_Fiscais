import requests
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import shutil # Para limpar a pasta de downloads entre os testes

SELENIUM_HEADLESS = True # Mude para False para VER o navegador abrindo e agindo.
# Caminho para downloads temporários do Selenium
TEMP_DOWNLOAD_DIR = os.path.abspath("temp_downloads_selenium")
if not os.path.exists(TEMP_DOWNLOAD_DIR):
    os.makedirs(TEMP_DOWNLOAD_DIR)

from src.config import (
    MEUDANFE_API_XML_DOWNLOAD_BASE_URL,  # URL base para download de XML
    MEUDANFE_API_DANFE_GENERATION_URL,  # URL para gerar DANFE PDF
    MEUDANFE_API_KEY,  # Chave de API
    REQUEST_TIMEOUT_SECONDS,
    MEUDANFE_WEB_URL
)

def initialize_webdriver(headless_mode, timeout_seconds, download_dir, logger_func):
    """
    Inicializa e configura um WebDriver Chrome para automação,
    com foco em downloads automáticos e modo headless.

    Args:
        headless_mode (bool): Se True, o navegador não será exibido.
        timeout_seconds (int): Tempo limite para carregamento de páginas e elementos.
        download_dir (str): Caminho para o diretório de downloads temporário.
        logger_func (function): Função de log a ser usada (ex: logger.info, log_message).

    Returns:
        webdriver.Chrome or None: Uma instância configurada do WebDriver, ou None em caso de erro.
    """
    # 1. Garante que o diretório de downloads esteja limpo e pronto
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir) # Remove a pasta e todo o seu conteúdo
        time.sleep(0.5) # Pequena pausa para garantir que a pasta foi deletada
    os.makedirs(download_dir, exist_ok=True) # Recria a pasta vazia
    logger_func("info", f"Pasta de downloads temporária limpa e recriada: {download_dir}")

    driver = None
    try:
        chrome_options = Options()
        if headless_mode:
            chrome_options.add_argument("--headless")
        
        # Argumentos para otimização e estabilidade
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        # --- OPÇÕES CRÍTICAS PARA DOWNLOADS AUTOMÁTICOS ---
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            
            # Preferências de Segurança para Download (ajustadas para 'safeBrowse.enabled' corretamente)
            "safeBrowse.enabled": False, # Desabilita a Navegação Segura por completo
            "safeBrowse.disable_download_protection": True, # Desabilita proteção de download
            "safeBrowse.disable_extension_blacklist": True,
            "profile.default_content_setting_values.automatic_downloads": 1, # Permite downloads automáticos
            "profile.default_content_setting_values.notifications": 2, # Bloqueia notificações
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Argumentos adicionais para burlar verificações de download e segurança
        chrome_options.add_argument("--disable-features=SafeBrowse") # Outra forma de desabilitar SafeBrowse
        chrome_options.add_argument("--allow-untrusted-downloads")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--no-default-browser-check")
        
        # Argumentos que podem ser necessários para evitar detecção de automação
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        logger_func("info", f"Inicializando o WebDriver Chrome com opções de download no diretório: {download_dir}")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout_seconds)
        logger_func("info", "WebDriver inicializado com sucesso.")
        return driver

    except WebDriverException as e:
        logger_func("error", f"WebDriverException ao inicializar o WebDriver. Verifique se o Chrome está instalado e o ChromeDriver é compatível. Erro: {e}")
        logger_func("error", "Tente atualizar o Chrome ou a biblioteca webdriver-manager.")
        return None
    except Exception as e:
        logger_func("error", f"Erro inesperado ao inicializar o WebDriver: {e}", exc_info=True)
        return None

def perform_meudanfe_search(driver, key, web_url, timeout_seconds, logger_func):
    """
    Navega para a página do meudanfe.com.br, insere a chave de acesso e clica no botão de busca.

    Args:
        driver (webdriver.Chrome): A instância do WebDriver.
        key (str): A chave de acesso da nota fiscal.
        web_url (str): A URL base do site (MEUDANFE_WEB_URL).
        timeout_seconds (int): Tempo limite para espera de elementos.
        logger_func (function): Função de log a ser usada (ex: log_message).

    Returns:
        bool: True se a busca foi realizada com sucesso, False caso contrário.
    """
    if not driver:
        logger_func("error", "WebDriver não está inicializado para realizar a busca.")
        return False

    try:
        logger_func("info", f"Navegando para: {web_url}")
        driver.get(web_url)

        # --- LOCALIZADORES COM BASE NO HTML FORNECIDO ---
        # Campo de input da chave de acesso (pelo placeholder)
        input_field_locator = (By.XPATH, "//input[@placeholder='Digite a CHAVE DE ACESSO']")
        
        # Botão "Buscar DANFE/XML" (pelo texto)
        consult_button_locator = (By.XPATH, "//button[contains(text(), 'Buscar DANFE/XML')]")

        logger_func("info", f"Procurando campo de input da chave com {input_field_locator}")
        WebDriverWait(driver, timeout_seconds).until(
            EC.presence_of_element_located(input_field_locator)
        )
        input_element = driver.find_element(*input_field_locator)
        input_element.send_keys(key)
        logger_func("info", f"Chave {key[:10]}... inserida no campo.")

        logger_func("info", f"Procurando botão de consulta com {consult_button_locator}")
        WebDriverWait(driver, timeout_seconds).until(
            EC.element_to_be_clickable(consult_button_locator)
        )
        driver.find_element(*consult_button_locator).click()
        logger_func("info", "Botão 'Buscar DANFE/XML' clicado. Aguardando resultados...")

        # Aguardar que a URL mude para /ver-danfe
        logger_func("info", "Aguardando carregamento da página de resultados (/ver-danfe)...")
        WebDriverWait(driver, timeout_seconds).until(
            EC.url_contains("/ver-danfe")
        )
        logger_func("info", f"Página de resultados carregada: {driver.current_url}")
        
    
        return True

    except TimeoutException:
        logger_func("error", "Tempo limite excedido ao esperar por elemento ou carregamento da página.")
        return False
    except NoSuchElementException as e:
        logger_func("error", f"Elemento não encontrado na página durante a busca: {e}")
        return False
    except WebDriverException as e:
        logger_func("error", f"Erro no WebDriver durante a busca: {e}", exc_info=True)
        return False
    except Exception as e:
        logger_func("error", f"Erro inesperado na navegação/inserção da chave: {e}", exc_info=True)
        return False


def extract_xml_results_page(driver, key, timeout_seconds, download_dir, logger_func, extract_nfe_func):
    """
    Extrai o conteúdo XML e PDF da página de resultados (/ver-danfe).

    Args:
        driver (webdriver.Chrome): A instância do WebDriver.
        key (str): A chave de acesso da nota fiscal (para logs e simulação de número).
        timeout_seconds (int): Tempo limite para espera de elementos.
        download_dir (str): Caminho para o diretório de downloads temporário.
        logger_func (function): Função de log a ser usada.
        extract_nfe_func (function): Função para extrair o número da nota do XML.

    Returns:
        tuple: (xml_content_bytes, pdf_content_bytes, note_number_str) ou (None, None, None) em caso de falha.
    """
    xml_content = None
    
    if not driver:
        logger_func("error", "WebDriver não está inicializado para extrair documentos.")
        return None, None, None

    try:
        # Espera adicional para garantir que a página de resultados está totalmente pronta
        # Isso pode ser ajustado com base na sua observação da página /ver-danfe.
        logger_func("info", "Aguardando elementos específicos na página de resultados...")
        # Ex: esperar por um botão de download, ou um elemento que indica sucesso na busca.
        # WebDriverWait(driver, timeout_seconds).until(EC.presence_of_element_located((By.ID, "algum_id_do_resultado")))
        
        # --- Lógica de clique no pop-up de segurança de download (se ainda ocorrer) ---
        # Adicione aqui o bloco de try-except para clicar no pop-up "Baixar arquivo não verificado"
        # que desenvolvemos anteriormente.
        try:
            unverified_download_button_locator = (By.XPATH, "//button[contains(text(), 'Baixar arquivo não verificado')]")
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(unverified_download_button_locator))
            driver.find_element(*unverified_download_button_locator).click()
            logger_func("info", "Botão 'Baixar arquivo não verificado' clicado.")
            time.sleep(1) # Pequena pausa após o clique
        except (TimeoutException, NoSuchElementException):
            logger_func("debug", "Pop-up 'Baixar arquivo não verificado' não encontrado ou não apareceu.")
        except Exception as e:
            logger_func("error", f"Erro ao tentar clicar no pop-up de segurança: {e}")

        # --- ETAPA DE DOWNLOAD DO XML ---
        xml_download_locator = (By.XPATH, "//button[contains(text(), 'Baixar XML')]")

        logger_func("info", f"Procurando botão/link de download de XML: {xml_download_locator}")
        WebDriverWait(driver, timeout_seconds).until(
            EC.element_to_be_clickable(xml_download_locator)
        )
        xml_download_element = driver.find_element(*xml_download_locator)
        
        logger_func("info", "Botão/link de Baixar XML encontrado. Clicando...")
        xml_download_element.click() 

        # Aguardar o arquivo ser baixado para a pasta de downloads
        time.sleep(3) # Dê um tempo para o download iniciar 

        downloaded_xml_files = [f for f in os.listdir(download_dir) if f.endswith('.xml')]
        
        if downloaded_xml_files:
            latest_xml_file_path = max([os.path.join(download_dir, f) for f in downloaded_xml_files], key=os.path.getctime)
            logger_func("info", f"Arquivo XML baixado encontrado: {latest_xml_file_path}")
            with open(latest_xml_file_path, 'rb') as f:
                xml_content = f.read()
            logger_func("info", "Conteúdo XML lido do arquivo baixado.")
        else:
            logger_func("error", "Nenhum arquivo XML encontrado na pasta de downloads após o clique. Simuando XML.")
            
        return xml_content    

    except TimeoutException:
        logger_func("error", f"Tempo limite excedido ao esperar por elemento na página de resultados para a chave: {key}.")
    except NoSuchElementException as e:
        logger_func("error", f"Elemento esperado não encontrado na página de resultados para a chave: {key}: {e}")
    except WebDriverException as e:
        logger_func("error", f"Erro no WebDriver (navegador) durante a extração de documentos: {e}", exc_info=True)
    except Exception as e:
        logger_func("critical", f"Erro crítico e inesperado durante a extração de documentos: {e}", exc_info=True)
    
    return None, None, None


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

        # Headers para a requisição de download do XML 
        xml_headers = {
            "authority": "ws.meudanfe.com",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "text/plain;charset=UTF-8",  
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
        
        if xml_response.status_code != 200:
            initializeWeb =  initialize_webdriver(headless_mode=SELENIUM_HEADLESS,timeout_seconds=REQUEST_TIMEOUT_SECONDS, download_dir=TEMP_DOWNLOAD_DIR, logger_func=logger.error)
            if initializeWeb:
                serachWeb = perform_meudanfe_search(driver=initializeWeb, key=key, web_url=MEUDANFE_WEB_URL, timeout_seconds=REQUEST_TIMEOUT_SECONDS, logger_func=logger.error)
                if serachWeb:
                    xml_content = extract_xml_results_page(
                        driver=initializeWeb,
                        key=key,
                        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
                        download_dir=TEMP_DOWNLOAD_DIR,
                        logger_func=logger.error,
                        extract_nfe_func=extract_note_number_from_xml
                    )
            initializeWeb.quit()
            logger.info(f"XML Content: {xml_content}")        
            if xml_content is None:
                logger.error(
                    f"Erro ao baixar XML para a chave {key}: Status {xml_response.status_code} - Resposta: {xml_response.text}"
                )
                return None, None, None

        if xml_content is None:
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
            "Content-Type": "text/plain",  
        }
       
        danfe_payload = xml_content  # Envie o conteúdo BINÁRIO do XML diretamente

        logger.debug(
            f"Tentando gerar DANFE de: {MEUDANFE_API_DANFE_GENERATION_URL} para nota: {note_number}"
        )
        danfe_response = requests.post(
            MEUDANFE_API_DANFE_GENERATION_URL,
            data=danfe_payload,  
            headers=danfe_headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

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
