# 🚀 Automação de Notas Fiscais - Pipeline E.T.L.

Este projeto em Python implementa uma pipeline de automação para leitura, processamento e organização de notas fiscais. O objetivo principal é automatizar a extração de chaves de acesso de arquivos de texto, baixar os documentos XML e DANFE (PDF) correspondentes de um serviço web externo, e organizá-los em uma estrutura de pastas segmentada por filial e data.

## 🎯 Objetivo do Projeto

Desenvolver um script robusto em Python que:
- Acesse arquivos `.txt` contendo chaves de acesso de notas fiscais.
- Extraia as chaves de acesso e o código da filial do nome do arquivo.
- Utilize uma API externa (`ws.meudanfe.com`) para baixar o XML e gerar o PDF da DANFE para cada chave.
- Organize os arquivos XML e PDF em uma estrutura de pastas clara e segmentada (`./NOTAS E XML/<filial>/<AAAA-MM-DD>/XML/` e `./DANFE/`).
- Renomeie os arquivos com o número da nota fiscal.
- Implemente tratamento de erros e gere logs detalhados do processamento.

## 💡 Arquitetura da Solução (Pipeline E.T.L.)

O projeto foi estruturado como uma pipeline de dados utilizando o padrão **E.T.L.** (Extract, Transform, Load), promovendo modularidade, testabilidade e escalabilidade:

-   **Extract (src/pipeline/extract.py):**
    -   Responsável pela `Ingestão` dos dados.
    -   Lê os arquivos `.txt` da pasta `CHAVES NOTAS/`.
    -   Extrai as chaves de acesso (44 dígitos) e identifica o código da filial a partir do nome do arquivo.

-   **Transform (src/pipeline/transform.py):**
    - Na descrição do case , foi falado para fazer webScraping , mas encontrei uma forma melhor , como a propria API para as requisições, deixando o processo mais rápido.
    -   Responsável pelo `Processamento` dos dados.
    -   Para cada chave de acesso:
        -   Faz uma requisição `POST` para a API de download de XML (`ws.meudanfe.com`) para obter o conteúdo XML da nota.
        -   Extrai o número da nota fiscal do XML.
        -   Faz uma requisição `POST` para a API de geração de DANFE (`ws.meudanfe.com`) para obter o PDF correspondente, enviando o XML como payload.
    -   Inclui tratamento robusto para falhas de conexão, requisições mal sucedidas e chaves inválidas.

-   **Load (src/pipeline/load.py):**
    -   Responsável pelo `Carregamento` dos dados.
    -   Salva os arquivos XML e PDF na estrutura de pastas definida (`./NOTAS E XML/<filial>/<AAAA-MM-DD>/`).
    -   Renomeia os arquivos usando o número da nota fiscal.

-   **Orquestrador (src/main.py):**
    -   Coordena o fluxo de execução entre os estágios da pipeline.
    -   Gerencia o logging e o tratamento de erros em nível de sistema.

-   **Configurações (src/config.py):**
    -   Centraliza parâmetros como caminhos de pastas, URLs de API e chaves de API.

-   **Logging (src/logger_config.py):**
    -   Configura um sistema de log para registrar todas as operações, warnings e erros em arquivos de log diários na pasta `LOGS/`.

## 📂 Estrutura de Pastas
├── CHAVES NOTAS/
│   ├── CHAVES FILIAL 04.txt
│   └── CHAVES FILIAL 05.txt
├── NOTAS E XML/
│   ├── FILIAL 04/
│   │   ├── AAAA-MM-DD/
│   │   │   ├── XML/
│   │   │   │   └── 007725447.xml
│   │   │   └── DANFE/
│   │   │       └── 007725447.pdf
│   └── FILIAL 05/
│       └── AAAA-MM-DD/
│           ├── XML/
│           │   └── 007725447.xml
│           └── DANFE/
│               └── 007725447.pdf
├── LOGS/
│   ├── processamento_YYYY-MM-DD.txt
├── src/
│   ├── pipeline/
│   │   ├── extract.py      # Estágio de Extração
│   │   ├── transform.py    # Estágio de Transformação
│   │   ├── load.py         # Estágio de Carregamento
│   │   └── init.py     # Indica que 'pipeline' é um pacote
│   ├── main.py             # Orquestrador principal da pipeline
│   ├── config.py           # Configurações do ambiente
│   ├── logger_config.py    # Configuração de logs
│   └── init.py         # Indica que 'src' é um pacote
├── requirements.txt        # Dependências do projeto Python
├── .gitignore              # Arquivos e pastas a serem ignorados pelo Git
└── README.md               # Este arquivo de documentação

## 🛠️ Pré-requisitos

Para executar este projeto, você precisará ter instalado:

* **Python 3.11+** (Recomendado baixar do [python.org/downloads](https://www.python.org/downloads/)). **Certifique-se de marcar "Add Python.exe to PATH" durante a instalação.**
* **Git** (Recomendado baixar do [git-scm.com/downloads](https://git-scm.com/downloads/)).
* Um editor de código (como **VS Code**, recomendado).

Executar o arquivo requerements "pip install -r requirements.txt"

## 🚀 Como Configurar e Rodar o Projeto

Siga estes passos para configurar e executar a pipeline em sua máquina local.

### 1. Clonar o Repositório

Abra seu terminal (Prompt de Comando no Windows, Terminal no macOS/Linux) e clone este repositório:

```bash
git clone [https://github.com/jeandsoncoelho/Automacao_de_Notas_Fiscais.git](https://github.com/jeandsoncoelho/Automacao_de_Notas_Fiscais.git) 
cd automacao-notas-fiscais

# Criar o ambiente virtual (venv é o nome da pasta)
python -m venv venv

# Ativar o ambiente virtual
# No Windows PowerShell:
.\venv\Scripts\activate
# No macOS/Linux ou Git Bash:
# source venv/bin/activate
```

Executar a Pipeline
python -m src.main