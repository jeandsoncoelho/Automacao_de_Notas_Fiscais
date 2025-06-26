import os
import re
from src.config import INPUT_FOLDER

def parse_filial_from_filename(filename):
    """
    Extrai o código da filial do nome do arquivo (Ex: 'CHAVES FILIAL 04.txt' -> 'FILIAL 04').
    Retorna None se o padrão não for encontrado.
    """
    # Padrão regex para encontrar "FILIAL XX"
    match = re.search(r'FILIAL (\d+)', filename, re.IGNORECASE)
    if match:
        # Retorna o código da filial formatado como "FILIAL 04"
        return f"FILIAL {match.group(1).zfill(2)}"
    return None

def read_keys_from_file(filepath, logger):
    """
    Lê um arquivo .txt e extrai as chaves de acesso.
    Espera 44 dígitos numéricos por linha.
    """
    keys = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Remove espaços em branco, quebras de linha
                clean_line = line.strip()
                # Padrão regex para 44 dígitos numéricos
                if re.fullmatch(r'\d{44}', clean_line):
                    keys.append(clean_line)
                else:
                    logger.warning(f"Linha {line_num} no arquivo '{os.path.basename(filepath)}' ignorada: '{clean_line}' (Formato inválido).")
        return keys
    except FileNotFoundError:
        logger.error(f"Arquivo '{filepath}' não encontrado.")
        return []
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo '{filepath}': {e}", exc_info=True)
        return []

def get_all_filial_keys(logger):
    """
    Percorre a pasta de entrada, lê todos os arquivos .txt e
    retorna uma lista de tuplas (filial_code, key).
    """
    all_data = []
    # Usa glob para encontrar todos os arquivos .txt na pasta de entrada
    # from glob import glob # Adicione no topo do arquivo se usar glob
    # files = glob(os.path.join(INPUT_FOLDER, "*.txt"))

    try:
        for filename in os.listdir(INPUT_FOLDER):
            if filename.endswith(".txt"):
                filepath = os.path.join(INPUT_FOLDER, filename)
                filial_code = parse_filial_from_filename(filename)

                if not filial_code:
                    logger.warning(f"Nome de arquivo inválido para filial: '{filename}'. Pulando.")
                    continue

                logger.info(f"Processando arquivo de chaves: '{filename}' para filial: '{filial_code}'.")
                keys = read_keys_from_file(filepath, logger)

                for key in keys:
                    all_data.append((filial_code, key))
        return all_data
    except FileNotFoundError:
        logger.error(f"Pasta de entrada '{INPUT_FOLDER}' não encontrada. Certifique-se de que ela existe.")
        return []
    except Exception as e:
        logger.critical(f"Erro crítico ao listar arquivos na pasta de entrada: {e}", exc_info=True)
        return []