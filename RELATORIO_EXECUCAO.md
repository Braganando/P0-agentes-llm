# Relatório de Execução e Engenharia — Projeto P0 (Extrator de Despesas com LLM)

## 1. Visão Geral e Objetivo
O **Extrator de Despesas para Motoristas** é uma aplicação web containerizada desenvolvida em Python (Flask) que utiliza Modelos de Linguagem de Grande Porte (LLMs) para converter descrições financeiras em linguagem natural (ex.: *"gastei 25 reais num marmitex e 100 conto de etanol"*) em estruturas JSON padronizadas e prontas para persistência contábil.

---

## 2. Arquitetura e Decisões de Engenharia

Para atender aos requisitos de produção do ambiente **Devel Lab**, a arquitetura evoluiu de um script simples para um serviço web resiliente:

1. **Gerenciamento de Processos (PID 1) e Concorrência no Gunicorn:**
   * **Problema diagnosticado:** O uso do comando `CMD` em formato *shell* no `Dockerfile` alocava o processo principal (`PID 1`) ao interpretador `/bin/sh -c`, impedindo o repasse adequado de sinais POSIX (`SIGTERM`) ao Gunicorn durante o desligamento do container. Além disso, o uso de um único *worker* síncrono (`sync`) causava bloqueio e *timeout* (`Error handling request - no URI read`) quando navegadores abriam conexões TCP de *preconnect* vazias.
   * **Solução implementada:** Adoção estrita da forma *exec* (`CMD ["gunicorn", ...]`) combinada ao worker `gthread` (`--workers 2 --threads 4 --timeout 180`), garantindo que o Gunicorn assuma diretamente o **PID 1** para *graceful shutdown* e processe múltiplas conexões simultâneas sem bloqueio.

2. **Validação de Segurança SSL/TLS Parametrizada:**
   * **Problema diagnosticado:** O certificado do servidor interno (`llm-internal.softex:9001`) é assinado por uma Autoridade Certificadora (CA) privada ausente no pacote padrão `ca-certificates` da imagem base `python:3.12-slim`.
   * **Solução implementada:** Eliminação do `verify=False` fixo em código. A validação TLS foi parametrizada via variável de ambiente `LLM_CA_BUNDLE`: por padrão, mantém a verificação criptográfica ativa (`True`), aceita o caminho de um certificado raiz interno (`/caminho/ca.pem`) em produção e permite o isolamento temporário de falhas em homologação (`false`) sem alterar o código-fonte.

3. **Resiliência a *Cold Start* (Standby) e Alta Demanda (Arquitetura Multi-Modelo):**
   * **Problema diagnosticado:** O servidor Ollama interno permanece em *standby* e leva de 1 a 2 minutos para inicializar na primeira requisição (causando `504 Gateway Timeout` ou `WORKER TIMEOUT` no Gunicorn padrão de 30s). Já chamadas externas estão sujeitas a picos momentâneos de demanda (`503 Service Unavailable`).
   * **Solução implementada:** Implementação da camada `consultar_llm()` com política de *retry* automático e *fallback* em cascata utilizando o SDK `google-genai` (`gemini-3.5-flash` -> `gemini-2.5-flash`) e o SDK `openai` apontado para a URL Base `/v1` do Ollama interno (`qwen3.5:9b-q4_K_M`), mantendo os limites de *timeout* do cliente HTTP abaixo do limite do Gunicorn (180s).

4. **Higienização e Validação de Saída JSON:**
   * Implementação da função `limpar_json()` via expressões regulares para remover blocos de raciocínio intermediário (`<think>...</think>`) e marcações Markdown (` ```json `) antes da validação com `json.loads()`, garantindo a renderização de um JSON estrito e indentado na interface.

---

## 3. Registro de Testes e Validação em Ambiente Limpo (Devel Lab)

* **Ambiente de Execução:** Portal Devel Lab (`devel-llm.eastus.cloudapp.azure.com`)
* **Container:** `31-nandobraga.cas` | **Porta exposta:** `8080/tcp`
* **Entrada de Teste:** `"gastei 25 reais num marmitex e 100 conto de etanol"`
* **Resultado Obtido (HTTP 200 OK):**
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