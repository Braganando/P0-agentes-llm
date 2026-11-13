# Relatório de Execução, Engenharia e Troubleshooting — Projeto P0

**Projeto:** Extrator de Despesas para Motoristas com Agentes LLM

**Autor:** Fernando Braga (`nandobraga.cas@gmail.com`)

**Repositório:** `https://github.com/Braganando/P0-agentes-llm`

**Versão Final:** `v2.1` (Release `p0-avancado`)

## 1. Visão Geral e Objetivo do Projeto

O **Extrator de Despesas para Motoristas** é uma solução baseada em Modelos de Linguagem de Grande Porte (LLMs) projetada para automatizar o registro contábil de profissionais do volante. A aplicação recebe relatos informais em linguagem natural (ex.: *"gastei 25 reais num marmitex e 100 conto de etanol"*) e realiza a extração estruturada das entidades financeiras, retornando estritamente um objeto JSON padronizado nas categorias `Combustivel`, `Alimentacao` ou `Manutencao`, contendo valores numéricos decimais e descrições concisas.

O desenvolvimento foi estruturado de forma incremental, evoluindo de um script local até uma aplicação web containerizada em Docker de alta resiliência, homologada no ambiente isolado do **Portal Devel Lab**.

## 2. Evolução Cronológica e Fases de Desenvolvimento

A linha do tempo de engenharia do projeto foi registrada no controle de versão Git através de três marcos principais (*tags*):

### 2.1. Fase 1 — Concepção e Nível Básico (`tag: p0-basico`)

* **Escopo Inicial:** Construção do fluxo base de integração com LLM para leitura de entradas textuais e extração estruturada em JSON via engenharia de prompt (*Zero-Shot Prompting* com restrição de esquema).
* **Configuração de Ambiente:** Estruturação inicial do repositório com isolamento de variáveis sensíveis (`.env` com `python-dotenv`) e definição das dependências no `requirements.txt`.
* **Seleção e Ajuste de Modelo:** Realização de testes comparativos entre versões da família Gemini (`gemini-1.5-flash` e `gemini-3.8-flash`), estabilizando a escolha no modelo **`gemini-3.5-flash`** em conjunto com o SDK `google-genai` e configuração `response_mime_type="application/json"`.

### 2.2. Fase 2 — Modularização, Logs e Containerização (`tag: p0-intermediario`)

* **Refatoração e Tratamento de Erros:** O código monolítico inicial foi desacoplado em funções modulares com blocos `try/except` específicos para falhas de comunicação de API e validação sintática do retorno via `json.loads()`.
* **Observabilidade e Interface:** Adição de rastreamento de execução com a biblioteca `logging` (`INFO`, `WARNING`, `ERROR`) e migração da interface de linha de comando (CLI) para uma aplicação web em **Flask** escutando em `0.0.0.0:8080`, conforme especificação técnica do manual do Devel Lab.
* **Empacotamento Docker e Higiene de Repositório:**
  * Criação do `Dockerfile` baseado na imagem oficial enxuta `python:3.12-slim` com servidor WSGI **Gunicorn**.
  * **Incidente de Limite de Arquivo no GitHub (`GH001: Large files detected`):** Durante o empacotamento da imagem Docker (`nandobragacasgmailcom.tar`), o comando `git push` foi rejeitado pelo limite de arquivos grandes do GitHub.
  * **Correção Aplicada:** Remoção de pacotes binários `.tar` da árvore de rastreamento (`git rm --cached`), criação do arquivo `.gitignore` (bloqueando `*.tar`, `*.zip`, `.env` e `__pycache__/`) e criação do `.dockerignore` (evitando que artefatos locais e a pasta `.git` inflamem o *build* da imagem).

### 2.3. Fase 3 — Resiliência Multi-Modelo e Adequação Arquitetural (`tag: p0-avancado`)

* Evolução para a versão **`v2.1`**, incorporando gerenciamento correto de sinais de sistema operacional ($\text{PID } 1$), concorrência multi-thread no Gunicorn, parametrização de certificados SSL/TLS, suporte à camada de compatibilidade OpenAI (`/v1`) do servidor Ollama interno e *fallback* automático entre provedores.

## 3. Diagnóstico de Infraestrutura e Troubleshooting no Devel Lab

Durante a implantação e os testes de estresse no **Portal Devel Lab**, a aplicação enfrentou desafios reais de infraestrutura, rede e concorrência. Abaixo estão documentados os seis problemas diagnosticados nos logs do container e as soluções definitivas implementadas:

### 3.1. Falha de Handshake SSL/TLS (`SSLCertVerificationError`) e Segurança em Produção

* **Sintoma:** Ao tentar conectar ao servidor interno de IA (`https://llm-internal.softex:9001`), o cliente HTTP abortava a conexão por falha na verificação do certificado digital.
* **Causa Raiz:** O certificado TLS do endpoint interno da instituição é assinado por uma Autoridade Certificadora (CA) privada/interna que não faz parte do pacote padrão `ca-certificates` da imagem `python:3.12-slim`.
* **Discussão Arquitetural e Solução:** Inicialmente, utilizou-se `verify=False` para isolar a falha de rede e comprovar a conectividade. Contudo, conforme alinhado nas discussões técnicas do fórum da residência, manter `verify=False` fixo em produção desativa a validação de identidade do host e expõe a aplicação a ataques *Man-in-the-Middle (MitM)*.
  * **Implementação (`obter_config_ssl`):** O código foi refatorado para eliminar o `verify=False` hardcoded, parametrizando a validação através da variável de ambiente `LLM_CA_BUNDLE`:
    1. Por padrão (`LLM_CA_BUNDLE=true`), mantém a validação criptográfica estrita ativa.
    2. Aceita o caminho de um certificado raiz interno (`LLM_CA_BUNDLE=/caminho/ca.pem`) para validação completa da cadeia privada.
    3. Permite o modo de diagnóstico (`LLM_CA_BUNDLE=false`) via variável de ambiente no painel apenas para isolamento de falhas em homologação, sem alterar o código-fonte.

### 3.2. Formato do `CMD` no Dockerfile e Gerenciamento de Sinais ($\text{PID } 1$)

* **Sintoma:** Na primeira tentativa de *build*, o container falhou ao iniciar com o erro `/bin/sh: 1: [gunicorn,: not found`.
* **Causa Raiz:** O uso de aspas simples dentro dos colchetes (`CMD ['gunicorn', ...]`) invalidou o parse JSON do Docker, fazendo com que a instrução fosse interpretada literalmente pelo shell `/bin/sh -c`. Uma tentativa intermediária usando a forma *shell* sem colchetes (`CMD gunicorn ...`) funcionou, mas gerou um problema estrutural apontado pela mentoria: na forma *shell*, o processo de $\text{PID } 1$ passa a ser o `/bin/sh`, deixando o Gunicorn como processo filho. Como o `/bin/sh` não repassa sinais POSIX (como `SIGTERM`) aos filhos, clicar em "Parar" no portal fazia o container ignorar o aviso de parada e terminar abruptamente via `SIGKILL`.
* **Solução Definitiva:** Adoção estrita da forma *exec* com sintaxe JSON válida (aspas duplas):
  ```dockerfile
  CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "180", "app:app"]
  ```
  Isso comprovou nos logs (`[1] [INFO] Starting gunicorn 27.0.0`) que o Gunicorn assumiu diretamente o $\text{PID } 1$ em primeiro plano, garantindo o *graceful shutdown*.

### 3.3. Descompasso de Timeout (`WORKER TIMEOUT`) e *Cold Start* (*Standby*) da LLM

* **Sintoma:** A interface web exibia `500 Internal Server Error` após exatos $30\text{ segundos}$ na primeira requisição enviada ao container.
* **Causa Raiz:** Análise dos logs do container revelou `[CRITICAL] WORKER TIMEOUT` no Gunicorn seguido de `504 Gateway Timeout` na resposta do servidor interno. Conforme confirmado pela equipe de mentoria, a LLM do laboratório permanece em modo ***standby*** quando ociosa e leva de $1\text{ a }2\text{ minutos}$ para concluir sua inicialização (*cold start*) após a primeira chamada de um container. O limite padrão do Gunicorn ($30\text{ s}$) matava o *worker* antes de a IA acordar.
* **Solução Definitiva:** Ampliação do `--timeout` do Gunicorn para $180\text{ segundos}$ e configuração de timeouts escalonados no cliente HTTP, garantindo que o Python capture eventuais atrasos de rede antes que o gerenciador de processos derrube o *worker*.

### 3.4. Bloqueio de Worker Síncrono por Preconnect (`Error handling request - no URI read`)

* **Sintoma:** Mesmo com timeout ampliado, observou-se nos logs o erro `Error handling request (no URI read)` no `sync.py` do Gunicorn, causando queda temporária do worker único (`pid:8`).
* **Causa Raiz:** Navegadores modernos abrem conexões TCP preventivas (*preconnect*) sem enviar dados HTTP imediatos. Com apenas $1\text{ worker}$ síncrono (`sync`), a conexão vazia bloqueava a fila de atendimento da aplicação.
* **Solução Definitiva:** Adição dos parâmetros `--workers 2 --threads 4` no `Dockerfile`, migrando automaticamente o Gunicorn para o worker **`gthread`**. Isso permitiu absorver conexões ociosas e pacotes malformados da rede (`bare LF as line terminator`) sem interromper o processamento das despesas.

### 3.5. Picos de Demanda Externa (`HTTP 503`) e Modo *Thinking* do Qwen 3.5 (`Resposta vazia ''`)

* **Sintoma:** Em testes reais registrados nos logs:
  1. A chamada rápida ao `gemini-3.5-flash` conectou rapidamente, mas recebeu `503 Service Unavailable ("This model is currently experiencing high demand")` devido a um pico momentâneo nos servidores externos.
  2. O sistema acionou automaticamente o *fallback* para o servidor Ollama interno via SDK compatível da OpenAI (`/v1/chat/completions`), que retornou `HTTP 200 OK` após a janela de processamento, porém com `content` vazio (`''`).
* **Causa Raiz:** O modelo interno `qwen3.5:9b-q4_K_M` possui geração de raciocínio (*reasoning* / `<think>`) ativa por padrão. Quando chamado pela rota `/v1` com a restrição `response_format={"type": "json_object"}`, o parser interno do Ollama pode esvaziar o campo `content` ou alocar a resposta nos campos extras de *reasoning*.
* **Solução Definitiva (`v2.1`):**
  * Adição de política de *retry* imediato no Gemini ($2\text{ tentativas}$ no `gemini-3.5-flash` seguidas de *fallback* para `gemini-2.5-flash`), contornando oscilações `503` em poucos segundos.
  * Ajuste da chamada OpenAI SDK (`/v1`) para o Ollama interno removendo o bloqueio de `response_format`, inspecionando tanto `message.content` quanto `message.model_extra["reasoning"]` e aplicando a função `limpar_json()` (que remove tags `<think>...</think>`, blocos Markdown e isola o objeto `{...}` via expressão regular).

### 3.6. Conflito de Instância no Portal Devel Lab (`409 Client Error: Conflict`)

* **Sintoma:** Ao excluir um container e subir uma nova imagem imediatamente no painel Devel Lab, o sistema exibia `409 Conflict: The container name "/31-nandobraga.cas-0" is already in use`.
* **Solução Operacional:** Identificou-se que o motor Docker subjacente ao portal exige a atualização de estado da sessão (recarregamento da página via `F5` após a exclusão) para liberar o descritor do container anterior antes de um novo *upload*.

## 4. Arquitetura Final da Solução (`v2.1`)

```text
[Navegador do Usuário]
         │  POST / ( Formulário HTML )
         ▼
[Container Docker: python:3.12-slim | Porta 8080]
  └── PID 1: Gunicorn 27.0 (worker: gthread | 2 workers | 4 threads | timeout: 180s)
        └── Aplicação Flask (app.py v2.1)
              ├── 1. Camada Primária (google-genai SDK):
              │      ├── Tentativa 1 e 2: gemini-3.5-flash
              │      └── Tentativa 3 (Fallback rápido): gemini-2.5-flash
              │
              ├── 2. Camada de Contingência Local (openai SDK -> /v1):
              │      └── Endpoint: https://llm-internal.softex:9001/v1 (qwen3.5:9b-q4_K_M)
              │          └── Validação TLS controlada via LLM_CA_BUNDLE
              │
              └── 3. Higienizador e Validador JSON (limpar_json + json.loads):
                     └── Remove <think>, crases Markdown e indenta JSON final
```

## 5. Registro de Testes e Validação em Produção (Devel Lab)

A versão final (`v2.1`) foi implantada e validada em um container limpo no ambiente oficial do laboratório:

* **URL de Acesso Público (Devel Lab):** `http://devel-llm.eastus.cloudapp.azure.com:32915`
* **Container ID / Nome:** `31-nandobraga.cas-0` (`8080/tcp`)
* **Caso de Teste Executado (Múltiplas Despesas em Linguagem Coloquial):**
  * **Input:** `"gastei 25 reais num marmitex e 100 conto de etanol"`

### 5.1. Evidência de Logs de Produção (`v2.1` no Container Devel Lab)

Os registros coletados diretamente do painel do container comprovam a execução do Gunicorn como $\text{PID } 1$ (`[1] [INFO]`), o funcionamento do *worker* `gthread` (`pid: 7` e `pid: 8`), o descarte seguro de conexões ociosas de *preconnect* e a extração concluída com sucesso (`HTTP/1.1 200 OK`) em aproximadamente $3\text{ segundos}$:

```text
2026-11-12T03:06:23.365148468Z [2026-11-12 03:06:23 +0000] [1] [INFO] Starting gunicorn 27.0.0
2026-11-12T03:06:23.365268150Z [2026-11-12 03:06:23 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
2026-11-12T03:06:23.365271825Z [2026-11-12 03:06:23 +0000] [1] [INFO] Using worker: gthread
2026-11-12T03:06:23.367001573Z [2026-11-12 03:06:23 +0000] [7] [INFO] Booting worker with pid: 7
2026-11-12T03:06:23.402316898Z [2026-11-12 03:06:23 +0000] [8] [INFO] Booting worker with pid: 8
2026-11-12T03:06:23.511896359Z [2026-11-12 03:06:23 +0000] [1] [INFO] Control socket listening at /root/.gunicorn/gunicorn.ctl
2026-11-12T03:06:23.918975259Z INFO:root:=== EXTRATOR v2.1 INICIADO | Modelo: gemini-3.5-flash | Gemini Key ativa: True ===
2026-11-12T13:36:44.408827728Z INFO:root:[v2.1] Texto recebido: gastei 25 reais num marmitex e 100 conto de etanol
2026-11-12T13:36:44.434924783Z INFO:root:[v2.1] Consultando Gemini (gemini-3.5-flash) - Tentativa 1/3...
2026-11-12T13:36:47.471926559Z INFO:httpx2:HTTP Request: POST https://generativelanguage.googleapis.com/v1/models/gemini-3.5-flash:generateContent "HTTP/1.1 200 OK"
2026-11-12T13:36:47.479130217Z INFO:root:[v2.1] Resposta bruta recebida: '{\n  "despesas": [\n    {\n      "categoria": "Alimentacao",\n      "valor": 25.0,\n      "descricao": "marmitex"\n    },\n    {\n      "categoria": "Combustivel",\n      "valor": 100.0,\n      "descricao": "etanol"\n    }\n  ]\n}'
2026-11-12T13:36:47.479812378Z INFO:root:[v2.1] Extração realizada com sucesso.
```

### 5.2. Saída Obtida na Interface Web (Validada com Sucesso)

```json
{
    "despesas": [
        {
            "categoria": "Alimentacao",
            "valor": 25.0,
            "descricao": "marmitex"
        },
        {
            "categoria": "Combustivel",
            "valor": 100.0,
            "descricao": "etanol"
        }
    ]
}
```

## 6. Conclusão

O ciclo completo de desenvolvimento do Projeto P0 permitiu validar na prática não apenas a engenharia de prompt e a extração estruturada de dados com LLMs, mas principalmente os requisitos críticos de engenharia de software para produção: gerenciamento adequado de processos Linux em containers ($\text{PID } 1$), segurança em transporte TLS/SSL com CAs privadas, dimensionamento de *workers* e *timeouts* diante de LLMs com *cold start* elevado e implementação de *fallbacks* resilientes utilizando SDKs padronizados de mercado (`google-genai` e `openai`).