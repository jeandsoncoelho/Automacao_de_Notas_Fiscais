import datetime
from src.logger_config import setup_logger
from src.pipeline.extract import get_all_filial_keys
from src.pipeline.transform import process_single_key
from src.pipeline.load import save_documents
from src.config import INPUT_FOLDER # Não está sendo usado diretamente aqui mas é bom ter

def run_data_pipeline():
    """
    Orquestra o pipeline de automação de notas fiscais.
    """
    logger = setup_logger()
    logger.info(f"Iniciando o pipeline de automação de notas em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Iniciando o pipeline de automação de notas em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        # Estágio 1: Extração
        logger.info(f"Estágio de Extração: Lendo chaves da pasta '{INPUT_FOLDER}'.")
        all_filial_keys_data = get_all_filial_keys(logger)

        if not all_filial_keys_data:
            logger.warning("Nenhum arquivo .txt com chaves válidas encontrado ou extraído.")
            return

        logger.info(f"Total de {len(all_filial_keys_data)} chaves encontradas para processamento.")

        for filial_code, key in all_filial_keys_data:
            logger.info(f"Processando chave: {key[:10]}... (Filial: {filial_code})")

            # Estágio 2: Transformação
            xml_content, pdf_content, note_number = process_single_key(key, logger)

            if xml_content and pdf_content and note_number:
                # Estágio 3: Carregamento
                current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                success = save_documents(
                    filial_code,
                    current_date_str,
                    note_number,
                    xml_content,
                    pdf_content,
                    logger
                )
                if success:
                    logger.info(f"Nota {note_number} (Filial: {filial_code}) processada e salva com sucesso.")
                else:
                    logger.error(f"Falha ao salvar documentos para nota {note_number} (Filial: {filial_code}).")
            else:
                logger.error(f"Falha ao obter XML/DANFE para a chave: {key[:10]}... Detalhes acima.")

    except Exception as e:
        logger.critical(f"Erro crítico no pipeline principal: {e}", exc_info=True)
    finally:
        logger.info(f"Pipeline de automação de notas finalizado em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_data_pipeline()