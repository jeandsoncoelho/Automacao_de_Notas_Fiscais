import logging
import os
import datetime
from src.config import LOG_FOLDER # Importa a pasta de logs definida em config.py

def setup_logger():
    """
    Configura e retorna um logger para o projeto.
    Cria um arquivo de log diário na pasta LOGS/ e também imprime no console.
    """
    # 1. Garante que a pasta de logs exista
    os.makedirs(LOG_FOLDER, exist_ok=True)

    # 2. Define o nome do arquivo de log com a data atual
    log_filename = f"processamento_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
    log_filepath = os.path.join(LOG_FOLDER, log_filename)

    # 3. Configura o logger raiz (root logger)
   
    # Remove handlers existentes para evitar duplicação em múltiplas chamadas
    # Isso é útil se a função for chamada mais de uma vez na mesma execução.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO, # Define o nível mínimo das mensagens a serem processadas (INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Formato das mensagens de log
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'), # Handler para salvar em arquivo
            logging.StreamHandler() # Handler para imprimir no console (stdout)
        ]
    )

    # Retorna o logger principal que será usado no main.py e em outros módulos
    return logging.getLogger(__name__) # '__name__' garante um logger com o nome do módulo