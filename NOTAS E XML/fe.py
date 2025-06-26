import os
from src.config import OUTPUT_BASE_FOLDER

def create_output_directories(base_path, filial_code, date_str, logger):
    """
    Cria a estrutura de diretórios:
    <base_path>/<filial_code>/<date_str>/XML/
    <base_path>/<filial_code>/<date_str>/DANFE/
    """
    output_filial_folder = os.path.join(base_path, filial_code)
    output_date_folder = os.path.join(output_filial_folder, date_str)
    output_xml_folder = os.path.join(output_date_folder, "XML")
    output_danfe_folder = os.path.join(output_date_folder, "DANFE")

    os.makedirs(output_xml_folder, exist_ok=True)
    os.makedirs(output_danfe_folder, exist_ok=True)

    logger.debug(f"Diretórios criados/verificados: {output_xml_folder}, {output_danfe_folder}")

    return output_xml_folder, output_danfe_folder

def save_documents(filial_code, date_str, note_number, xml_content, pdf_content, logger):
    """
    Salva o XML e o PDF na estrutura de pastas correta.
    """
    if not xml_content or not pdf_content or not note_number:
        logger.error(f"Conteúdo ou número da nota inválido para salvar. Nota: {note_number}")
        return False

    try:
        xml_folder, danfe_folder = create_output_directories(
            OUTPUT_BASE_FOLDER, filial_code, date_str, logger
        )

        xml_filename = f"{note_number}.xml"
        pdf_filename = f"{note_number}.pdf"

        xml_filepath = os.path.join(xml_folder, xml_filename)
        pdf_filepath = os.path.join(danfe_folder, pdf_filename)

        # Salvar XML
        with open(xml_filepath, 'wb') as f: # 'wb' para escrever em modo binário
            f.write(xml_content)
        logger.info(f"XML salvo: {xml_filepath}")

        # Salvar PDF
        with open(pdf_filepath, 'wb') as f: # 'wb' para escrever em modo binário
            f.write(pdf_content)
        logger.info(f"DANFE PDF salvo: {pdf_filepath}")

        return True

    except Exception as e:
        logger.error(f"Erro ao salvar documentos para nota {note_number} (Filial: {filial_code}): {e}", exc_info=True)
        return False