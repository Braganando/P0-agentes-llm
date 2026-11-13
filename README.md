# 🚀 P0: Extrator de Despesas para Motoristas com LLM

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/docker-24%2B-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Aplicação desenvolvida como parte da **Residência em Inteligência Artificial**, focada em executar o primeiro ciclo completo de engenharia de software integrada a Modelos de Linguagem de Grande Porte (LLMs).

---

## 📌 1. Problema Escolhido e Público-Alvo

* **Quem possui a necessidade:** Motoristas de aplicativo (Uber, 99), taxistas e entregadores autônomos que realizam jornadas externas extensas.
* **Problema real:** A dificuldade e morosidade no registro e categorização manual de pequenos gastos diários (combustível, refeições, manutenção emergencial), comumente anotados de forma rápida, informal ou por mensagens fragmentadas durante o trabalho.
* **Resultado útil gerado:** Uma solução automatizada que recebe relatos informais em texto livre (ex.: *"coloquei 50 de etanol e almocei um prato feito de 25 reais"*) e consolida esses dados em um objeto estruturado em **JSON**, padronizando valores numéricos decimais, descrições claras e categorias financeiras pré-definidas (`Combustivel`, `Alimentacao` e `Manutencao`).

---

## 💡 2. Justificativa para o Uso de LLM

A linguagem natural utilizada no cotidiano por motoristas é altamente variável, permeada por gírias regionais (*"50 conto"*, *"marmitex"*, *"etanol"*, *"troca de óleo"*), omissão de pontuação e agregação de múltiplos eventos de compra em uma única frase.

* **Por que não regras fixas ou expressões regulares (Regex)?** Expressões regulares e algoritmos convencionais de busca por palavras-chave são excessivamente frágeis: falham ao tentar desmembrar múltiplos itens sem separadores formais, confundem contexto semântico e exigiriam manutenção contínua e complexa de dicionários de sinônimos.
* **Papel da IA:** O LLM atua na compreensão semântica e contextual da sentença, identificando entidades financeiras e delimitando a intenção de gasto mesmo com grafias informais, mapeando-as de forma determinística para uma estrutura padronizada em JSON.

---

## ⚙️ 3. Funcionamento da Solução e Arquitetura

A solução evoluiu de um script inicial CLI para uma aplicação Web conteinerizada robusta e resiliente (`v2.1`):

1. **Camada de Interface:** O usuário insere o relato informal através de um formulário Web servido na porta `8080`.
2. **Processamento do Servidor (WSGI / PID 1):** A aplicação Flask é servida via **Gunicorn** em formato *exec* no `Dockerfile` (assumindo o $\text{PID } 1$ para recebimento limpo de sinais `SIGTERM`), operando com worker multi-thread (`gthread`, 2 workers e 4 threads) e timeout estendido ($180\text{ s}$) para suportar o *cold start* de modelos locais.
3. **Integração Resiliente com LLM:**
   * **Provedor Principal:** Nuvem externa via API Gemini (`gemini-3.5-flash` com retentativa automática e *fallback* rápido para `gemini-2.5-flash`).
   * **Provedor Institucional (Contingência):** Servidor Ollama interno do laboratório (`qwen3.5:9b-q4_K_M`) via camada de compatibilidade OpenAI (`/v1`), com verificação de certificados TLS/SSL parametrizável via `LLM_CA_BUNDLE`.
4. **Higienização e Parsing:** Filtro pós-processamento (`limpar_json`) que elimina tags de raciocínio (`<think>...</think>`), crases Markdown e valida a integridade do JSON retornado via `json.loads()`.

---

## 🛑 4. Limites do Projeto

Respeitando estritamente o escopo do P0 (manter o projeto enxuto e demonstrar o ciclo fundamental):
* **No Escopo:** Entrada textual via formulário Web, orquestração e chamada a um LLM por requisição, extração estrita em três categorias (`Combustivel`, `Alimentacao`, `Manutencao`), tratamento de exceções previsíveis, testes automatizados e conteinerização em Docker.
* **Fora do Escopo:** Persistência em banco de dados SQL/NoSQL, autenticação de usuários e controle de login, agentes autônomos complexos com ferramentas externas (*tool use* / *function calling*), RAG (*Retrieval-Augmented Generation*) e integração com planilhas ou sistemas de gestão externos.

---

## 📦 5. Instalação e Preparação do Ambiente

### Pré-requisitos
* **Python:** Versão 3.12 ou superior
* **Docker:** Versão 24+ (para execução conteinerizada)
* **Git:** Para clonagem e versionamento

### Instalação Local (Ambiente Virtual)

1. Clone o repositório:
```bash
git clone https://github.com/Braganando/P0-agentes-llm.git
cd P0-agentes-llm
```

2. Crie e ative um ambiente virtual limpo:
```bash
python3 -m venv venv
# No Linux/macOS:
source venv/bin/activate
# No Windows:
venv\Scripts\activate
```

3. Instale as dependências declaradas:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 6. Configuração de Acesso ao LLM

O projeto segue as diretrizes de segurança, não armazenando nenhum token, chave ou credencial no código ou repositório.

1. Copie o arquivo de exemplo de variáveis de ambiente:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` configurando o provedor que deseja utilizar:
```ini
# --- Provedor Externo (Google Gemini) ---
GEMINI_API_KEY=sua_chave_de_api_aqui
LLM_MODEL=gemini-3.5-flash

# --- Provedor Institucional / Ollama Local (Devel Lab) ---
OLLAMA_HOST=https://llm-internal.softex:9001
# Controle de Validação SSL (true = validação padrão; false = diagnóstico; ou /caminho/ca.pem)
LLM_CA_BUNDLE=true

# --- Parâmetros de Execução ---
LLM_TIMEOUT=25
PORT=8080
```

---

## 💻 7. Comandos de Execução

### Opção A: Execução Direta (Desenvolvimento Local)
```bash
python app.py
```
Acesse a aplicação no navegador em: `http://localhost:8080`

### Opção B: Execução com Docker (Ambiente Limpo e Isolado)
1. Construa a imagem Docker enxuta (otimizada via `.dockerignore`):
```bash
docker build --no-cache -t nandobragacasgmailcom:latest .
```

2. Execute o container mapeando a porta 8080:
```bash
docker run -p 8080:8080 --env-file .env nandobragacasgmailcom:latest
```

### Opção C: Deploy no Portal Devel Lab (Ambiente Oficial na Nuvem)
1. Exporte a imagem para arquivo `.tar`:
```bash
docker save -o nandobragacasgmailcom.tar nandobragacasgmailcom:latest
```
2. No painel do Portal Devel Lab:
   * Envie o arquivo `nandobragacasgmailcom.tar`;
   * Defina a porta de exposição: `8080`;
   * Configure as variáveis de ambiente necessárias (`GEMINI_API_KEY`, `OLLAMA_HOST`, `LLM_CA_BUNDLE`);
   * Inicie o container e acesse pela porta pública mapeada pelo portal.

---

## 🧪 8. Execução dos Testes e Distinção entre Testes Reais e Simulados

O projeto contempla validação em dois níveis distintos:

* **Testes de Lógica Local (Simulados - Sem chamadas reais ao LLM):** Validam o comportamento interno da aplicação, limpeza e sanitização de JSON com tags `<think>`, tratamento de respostas com caracteres inválidos e validação de campos obrigatórios sem consumir créditos ou depender de conexão de rede.
* **Testes de Integração (Chamada Real ao LLM):** Validam a comunicação *end-to-end* com o provedor configurado (detalhados em [`RELATORIO_EXECUCAO.md`](RELATORIO_EXECUCAO.md)).

### Executando os Testes Automatizados
```bash
# Executa os testes unitários e de lógica local simulada
pytest tests/ -v
```

### Cenários de Validação Tratados
* **Entrada Válida:** Gera o JSON esperado com sucesso.
* **Entrada Vazia:** O envio é bloqueado tanto pelo front-end (`required`) quanto validado no back-end.
* **Credencial Ausente/Inválida:** A falha é interceptada de forma graciosa, acionando o *fallback* ou retornando mensagem clara ao usuário sem expor credenciais.
* **Falha de Comunicação/Timeout:** O sistema captura a indisponibilidade ou lentidão do servidor de IA e exibe mensagem amigável de recuperação em vez de gerar erro 500 (*crash*).

---

## 📋 9. Exemplos de Entrada e Saída

### Exemplo 1: Múltiplas Despesas em Sentença Informal
* **Entrada fornecida:**
  > *"gastei 25 reais num marmitex e 100 conto de etanol"*

* **Saída gerada pela aplicação:**
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

### Exemplo 2: Despesa de Manutenção Única
* **Entrada fornecida:**
  > *"Troquei as pastilhas de freio do carro, ficou 180 reais"*

* **Saída gerada pela aplicação:**
```json
{
    "categoria": "Manutencao",
    "valor": 180.0,
    "descricao": "pastilhas de freio"
}
```

---

## ⚠️ 10. Limitações Conhecidas

1. **Cold Start do Modelo Local:** No ambiente compartilhado do Devel Lab, se o modelo Ollama estiver em *standby*, a primeira requisição pode levar de $60\text{ a }120\text{ segundos}$ para responder, sendo necessário manter o timeout do Gunicorn em $180\text{ s}$.
2. **Moedas e Câmbio Estrangeiro:** O extrator assume valores em Reais (`R$`). Valores descritos em moedas estrangeiras (dólar, euro) sem indicação explícita de conversão não realizam conversão cambial.
3. **Escopo Fixo de Categorias:** Caso o usuário descreva um gasto fora de `Combustivel`, `Alimentacao` ou `Manutencao` (ex.: *"paguei a parcela do seguro"*), a IA buscará categorizar no item mais próximo ou descartará caso não haja aderência semântica.
4. **Instabilidade de Rede Externa/Interna:** Picos de demanda na API externa (`503 Service Unavailable`) ou timeouts no gateway interno (`504 Gateway Timeout`) são mitigados pelo *fallback* automático implementado na versão `v2.1`.

---

## 🏷️ 11. Tags e Histórico de Releases (Evolução Incremental)

O repositório reflete o desenvolvimento incremental exigido nas diretrizes através das seguintes tags:

* [`p0-basico`](https://github.com/Braganando/P0-agentes-llm/tree/p0-basico): Primeiro fluxo funcional de extração JSON com LLM e dependências isoladas.
* [`p0-intermediario`](https://github.com/Braganando/P0-agentes-llm/tree/p0-intermediario): Modularização do código, criação do `.gitignore`, tratamento de erros e containerização inicial.
* [`p0-avancado`](https://github.com/Braganando/P0-agentes-llm/tree/p0-avancado): Aplicação Web Flask/Gunicorn (`PID 1`, `gthread`) conteinerizada em Docker, resiliência multi-modelo (`v2.1`), validação em ambiente limpo no Devel Lab e [`RELATORIO_EXECUCAO.md`](RELATORIO_EXECUCAO.md) completo.

---

## 🎥 12. Vídeo de Demonstração

* **Link da Apresentação:** `[VÍDEO EM PRODUÇÃO - LINK SERÁ DISPONIBILIZADO AQUI]` *(Vídeo narrado com duração máxima de 5 minutos, publicado como Não Listado no YouTube com legendas revisadas)*.

---

## 👨‍💻 Autor

* **Desenvolvedor:** Fernando Braga
* **Contato:** `nandobraga.cas@gmail.com`
* **Programa:** Residência em Inteligência Artificial