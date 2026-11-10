# 🚀 P0: Agente LLM de Classificação Financeira

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_Framework-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Conteinerização-2496ED.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Finalizado-success.svg)]()

## 📖 Visão Geral

O **Projeto P0** é o desafio inicial da Residência em Inteligência Artificial. O objetivo principal é construir uma aplicação capaz de receber entradas em linguagem natural sobre despesas diárias (ex: "gastei 25 reais num marmitex e 100 conto de etanol") e utilizar uma LLM para extrair, categorizar e formatar esses dados em uma estrutura JSON rígida.

O projeto evoluiu de um script CLI básico consumindo a API do Google Gemini para uma **aplicação Web conteinerizada (Flask + Gunicorn)**, projetada para se comunicar com um modelo fundacional local (`qwen3.5:9b`) através de um ambiente em nuvem restrito (Devel Lab Portal).

## 🏗️ Arquitetura e Tecnologias

A arquitetura final foi desenhada para garantir resiliência de rede e otimização de infraestrutura.

*   **Backend:** Python 3.12 + Flask
*   **Servidor WSGI:** Gunicorn (configurado com timeout de 120s para processamento assíncrono de LLMs)
*   **Integração LLM:** Requisições REST via biblioteca `requests` (com bypass de SSL para ambientes internos `verify=False`).
*   **Infraestrutura:** Docker (Imagem base `python:3.12-slim` com `.dockerignore` estrito para garantir pacotes < 250MB).

## ✨ Funcionalidades

*   **Processamento Múltiplo:** Capacidade de identificar e separar múltiplas despesas descritas numa única frase.
*   **Formatação Restrita:** Retorno exclusivo de objetos JSON padronizados, sem conversas paralelas da IA.
*   **Tratamento de Erros:** Captura elegante de falhas de conexão, timeouts de infraestrutura (504 Gateway Timeout) e entradas inválidas, retornando feedback visual ao utilizador em vez de "crashar" a aplicação.
*   **Interface Web:** Formulário HTML simples e direto servido na porta 8080.

## 🚀 Como Executar Localmente

### Pré-requisitos
*   [Docker](https://www.docker.com/get-started) instalado na máquina.
*   (Opcional) Acesso ao ambiente interno do laboratório ou uma instância local do Ollama rodando o modelo `qwen3.5:9b`.

### Passos para Deploy

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/SeuUsuario/P0-agentes-llm.git
    cd P0-agentes-llm
    ```

2.  **Construa a imagem Docker:**
    ```bash
    docker build -t app-gastos:latest .
    ```

3.  **Execute o container:**
    ```bash
    docker run -p 8080:8080 -e OLLAMA_HOST="http://host.docker.internal:11434" app-gastos:latest
    ```
    *(Acesse `http://localhost:8080` no seu navegador).*

## ☁️ Deploy no Devel Lab Portal

Para publicar a aplicação na infraestrutura de avaliação:

1.  Gere o arquivo Tarball da imagem:
    ```bash
    docker save -o seuexemplo.tar app-gastos:latest
    ```
2.  No painel do portal, preencha os campos obrigatórios:
    *   **Porta do container:** `8080`
    *   **Variáveis de ambiente:** `OLLAMA_HOST=https://llm-internal.softex:9001`
3.  Faça o upload do `.tar` e inicie o container.

---
*Projeto desenvolvido por Fernando Silveira como parte dos requisitos de avaliação da Residência em IA (TrendsIA).*