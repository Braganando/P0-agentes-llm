# Relatório de Execução - Projeto P0

## 1. Evolução por Nível

O projeto evoluiu de um script simples de terminal para uma aplicação conteinerizada resiliente, lidando com mudanças de requisitos no ambiente de IA durante o desenvolvimento.

* **Nível Básico (`p0-basico`):**
  * **O que foi construído:** O sistema iniciou como um script de linha de comando (CLI) em Python, utilizando inicialmente a API do Google Gemini para receber textos sobre gastos, processar a solicitação e estruturar a saída no terminal.
  * **Segurança e Dependências:** A configuração isolou parâmetros sensíveis em arquivo `.env` (API Keys) e declarou os pacotes no `requirements.txt`.

* **Nível Intermediário (`p0-intermediario`):**
  * **O que foi acrescentado:** O código foi modularizado. Ocorreu a primeira grande pivotagem: a substituição da API do Gemini pela LLM local do Devel Lab (`qwen3.5:9b-q4_K_M`). Foram inseridos blocos lógicos `try/except` robustos para lidar com indisponibilidade de rede.
  * **Tratamento de Erros e Git:** Adoção do fluxo de versionamento no GitHub e blindagem contra entradas vazias. O sistema provou sucesso ao categorizar múltiplas entradas simultâneas via CLI.

* **Nível Avançado (`p0-avancado`):**
  * **O que foi acrescentado:** Migração completa da interface CLI para uma interface Web (Flask + Gunicorn) na porta 8080. A aplicação foi empacotada em Docker com otimização extrema de tamanho de imagem (`.dockerignore`).
  * **Reproduzibilidade:** Validação local garantida no ambiente Docker e adaptação das variáveis de ambiente (`OLLAMA_HOST`) para leitura direta na nuvem. A configuração final exigiu ajustes no `timeout` do servidor e a exposição explícita de portas (`EXPOSE 8080`) no manifesto da imagem.

---

## 2. Decisões Principais

### Decisão 1: Pivotagem de Provedor de LLM (Gemini para Devel Lab)
* **Decisão Tomada:** Substituição da integração inicial via Google Gemini pela LLM interna hospedada na infraestrutura do curso (`llm-internal.softex:9001`).
* **Alternativa Considerada:** Manter a aplicação consumindo a API externa do Gemini Cloud.
* **Justificativa:** Adequação estrita às diretrizes recebidas no meio do projeto para conformidade com o ambiente de avaliação na nuvem, que restringe o acesso externo e fornece um modelo fundacional próprio.

### Decisão 2: Otimização Extrema de Conteinerização (Docker)
* **Decisão Tomada:** Utilização da imagem base `python:3.12-slim` e um `.dockerignore` estrito (bloqueando a pasta virtual `venv`).
* **Alternativa Considerada:** Usar a imagem Python padrão.
* **Justificativa:** Limite de 250MB do Devel Lab para o envio do arquivo `.tar`, exigindo um ambiente leve e de rápida compilação.

### Decisão 3: Tuning de Timeout e Exposição Explícita de Porta
* **Decisão Tomada:** Ampliação do tempo limite do Gunicorn e da biblioteca `requests` para 120 segundos (`--timeout 120`), uso de sintaxe JSON rigorosa no `CMD` do Dockerfile e a declaração de `EXPOSE 8080`.
* **Alternativa Considerada:** Manter o Gunicorn com as configurações e limites padrão (30 segundos).
* **Justificativa:** A LLM local do curso (`qwen3.5:9b`) exige alto tempo de processamento. O limite padrão de 30s causava a interrupção abrupta do *worker* do Gunicorn (Erro 500). O `EXPOSE 8080` foi necessário pois a interface do portal falhava em mapear a porta sem a instrução no manifesto da imagem.

---

## 3. Testes e Resultados

| Teste | Entrada ou Situação | Resultado Esperado | Resultado Obtido |
| :--- | :--- | :--- | :--- |
| **01. Entrada Válida Múltipla (CLI/Sucesso)** | Texto no terminal: `"gastei 25 reais num marmitex e 100 conto de etanol"`. | O código identifica dois gastos distintos e categoriza corretamente. | **Aprovado** / O parsing funcionou perfeitamente, processando duas entradas simultâneas no terminal local. |
| **02. Isolamento de Rede (Docker Local)** | Submissão do mesmo texto via interface Web executada em `localhost:8080`. | Interceptação de falha de conexão com a rede restrita, sem crash do sistema. | **Aprovado** / Gunicorn manteve-se estável e o frontend exibiu o erro amigável de falha de rede. |
| **03. Validação de Variável (Portal Devel Lab)** | Submissão no portal após leitura da variável `OLLAMA_HOST`. | Ocorrer requisição HTTP com o endereço configurado. | **Aprovado** / A aplicação logou a formatação da URL de destino sem a presença de caracteres inválidos. |
| **04. Teste de Stress/Timeout (Portal Devel Lab)** | Execução de requisição com tempo limite de 120s configurado no Gunicorn. | A aplicação aguarda o processamento lento da LLM sem o *worker* morrer. | **Parcialmente Aprovado** / O Gunicorn suportou a espera, mas o servidor LLM da infraestrutura retornou um Erro 504 (Gateway Timeout), indicando sobrecarga na nuvem. |

---

## 4. Falhas e Limitações

* **O que aconteceu:** A aplicação Web, ao ser executada no portal do Devel Lab, apresentou uma série de erros sucessivos: inicialmente um "Internal Server Error" (HTTP 500), seguido por um erro de build `/bin/sh: 1: [gunicorn,: not found`, e finalmente um "504 Gateway Timeout".
* **Como foi identificado:** Através da análise sistemática dos *logs* de execução do container via dashboard do portal. 
* **Como foi tratado:** 
  1. O **Erro 500** foi diagnosticado como o Gunicorn matando o processo (*WORKER TIMEOUT*) após 30 segundos, pois a LLM demorava a responder. Resolvido aumentando o `--timeout` para 120 no Dockerfile e no `requests.post`.
  2. O erro **`/bin/sh: 1: [gunicorn,: not found`** ocorreu devido a falhas na sintaxe JSON do `CMD` no Dockerfile (uso de aspas indevidas), corrigido adotando a matriz JSON estrita com aspas duplas `"`.
  3. O erro **504 Gateway Timeout** ocorreu em seguida, validando que a nossa aplicação estava funcionando e aguardando pacientemente, mas o *proxy* da LLM interna (`llm-internal.softex:9001`) falhou em entregar a resposta no tempo estabelecido pela sua própria infraestrutura.
* **Por que permanece:** O erro 504 final é uma limitação de infraestrutura e sobrecarga do servidor hospedeiro da LLM, que excede a janela viável de resposta, estando fora do escopo de correção da aplicação cliente.

---

## 5. Uso de IA no Desenvolvimento

| Ferramenta Utilizada | Tarefa Delegada | Resultado Aproveitado | Correções / Alterações Realizadas | Forma de Verificação |
| :--- | :--- | :--- | :--- | :--- |
| **Gemini** | Implementação do fluxo inicial e integração com API. | Lógica central de chamadas à API e formatação inicial do prompt. | Refatoração completa quando os requisitos mudaram para a LLM local do Devel Lab. | Execução de testes no terminal local com sucesso. |
| **Gemini** | Transição de CLI para arquitetura Flask + Docker. | Estrutura do `Dockerfile` e arquivos base (`app.py`). | Adição do `.dockerignore` para reduzir o pacote para menos de 250MB. | Build local validado sem erros de tamanho. |
| **Gemini** | Diagnóstico avançado de *logs* no portal da nuvem. | Identificação das raízes do Erro 500 (Gunicorn timeout) e erros de sintaxe no Dockerfile. | Ajuste da declaração `CMD`, aumento de timeout (`120s`) e declaração explícita de `EXPOSE 8080`. | Monitoramento dos *logs* de saída no painel do aluno evidenciando a evolução dos erros (até o 504 final). |

---

## 6. Reflexão Final

* **Principal Aprendizado:** A resiliência vai além do código; envolve o ajuste fino da infraestrutura. A necessidade de alinhar tempos de *timeout* entre servidor web (Gunicorn), biblioteca HTTP (requests) e servidor remoto (Ollama) foi a grande lição de arquitetura.
* **Competência Mais Desenvolvida:** Análise de *logs* de servidores e diagnóstico de operações Docker (troubleshooting). Identificar que um erro 500 era problema de limite de tempo, e um erro de comando era puramente sintaxe de aspas, consolidou o domínio sobre o ecossistema.
* **Aspecto a ser Aprimorado:** Expandir os conhecimentos sobre os limites de *proxies* reversos (Nginx/Gateway), aprendendo a desenhar aplicações assíncronas (com filas) para evitar que requisições longas dependam do ciclo de vida de uma conexão HTTP síncrona.