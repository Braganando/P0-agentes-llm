# 🚀 P0: Extrator de Despesas para Motoristas com LLM

Aplicação desenvolvida como parte da **Residência em Inteligência Artificial**, focada em executar o primeiro ciclo completo de engenharia de software integrada a Modelos de Linguagem de Grande Porte (LLMs).

## 📌 1. Problema Escolhido e Público-Alvo

* **Quem possui a necessidade:** Motoristas de aplicativo (Uber, 99), taxistas e entregadores autônomos que realizam jornadas externas extensas.

* **Problema real:** A dificuldade e morosidade no registro e categorização manual de pequenos gastos diários (combustível, refeições, manutenção emergencial), comumente anotados de forma rápida, informal ou por mensagens fragmentadas durante o trabalho.

* **Resultado útil gerado:** Uma solução automatizada que recebe relatos informais em texto livre (ex.: *"coloquei 50 de etanol e almocei um prato feito de 25 reais"*) e consolida esses dados em um objeto estruturado em **JSON**, padronizando valores numéricos decimais, descrições claras e categorias financeiras pré-definidas (`Combustivel`, `Alimentacao` e `Manutencao`).

## 💡 2. Justificativa para o Uso de LLM

A linguagem natural utilizada no cotidiano por motoristas é altamente variável, permeada por gírias regionais (*"50 conto"*, *"marmitex"*, *"etanol"*, *"troca de óleo"*), omissão de pontuação e agregação de múltiplos eventos de compra em uma única frase.

* **Por que não regras fixas ou expressões regulares (Regex)?** Expressões regulares e algoritmos convencionais de busca por palavras-chave são excessivamente frágeis: falham ao tentar desmembrar múltiplos itens sem separadores formais, confundem contexto semântico e exigiriam manutenção contínua e complexa de dicionários de sinônimos.

* **Papel da IA:** O LLM atua na compreensão semântica e contextual da sentença, identificando entidades financeiras e delimitando a intenção de gasto mesmo com grafias informais, mapeando-as de forma determinística para uma estrutura padronizada em JSON.

## ⚙️ 3. Funcionamento da Solução e Arquitetura

A solução evoluiu de um script inicial CLI para uma aplicação Web conteinerizada robusta e resiliente (`v2.1.1`):

1. **Camada de Interface e Sanitização de Entrada:** O usuário insere o relato informal através de um formulário Web servido na porta `8080`. Além da trava HTML (`required`), o back-end aplica higienização via `.strip()` antes de acionar a IA, bloqueando strings vazias ou compostas exclusivamente por espaços em branco.

2. **Processamento do Servidor (WSGI / PID 1):** A aplicação Flask é servida via **Gunicorn** em formato *exec* no `Dockerfile` (assumindo o `PID 1` para recebimento limpo de sinais `SIGTERM`), operando com worker multi-thread (`gthread`, 2 workers e 4 threads) e timeout estendido (`180 s`) para suportar o *cold start* de modelos locais.

3. **Integração Resiliente com LLM:**

   * **Provedor Principal:** Nuvem externa via API Gemini (`gemini-3.5-flash` com retentativa automática e *fallback* rápido para `gemini-3.8-flash`).

   * **Provedor Institucional (Contingência):** Servidor Ollama interno do laboratório (`qwen3.5:9b-q4_K_M`) via camada de compatibilidade OpenAI (`/v1`), com verificação de certificados TLS/SSL parametrizável via `LLM_CA_BUNDLE`.

4. **Higienização, Parsing e Tratamento Seguro de Exceções:** Filtro pós-processamento (`limpar_json`) que elimina tags de raciocínio (`<think>...</think>`), crases Markdown e extrai com segurança o último objeto JSON válido via `json.JSONDecoder().raw_decode()`, validando a integridade da saída com `json.loads()`. Falhas inesperadas têm seu *traceback* registrado exclusivamente nos logs internos do servidor (`exc_info=True`), exibindo ao usuário apenas orientações amigáveis sem expor *stack traces* ou credenciais.

## 🛑 4. Limites do Projeto

Respeitando estritamente o escopo do P0 (manter o projeto enxuto e demonstrar o ciclo fundamental):

* **No Escopo:** Entrada textual via formulário Web, validação e orquestração de chamada a um LLM por requisição, extração estrita em três categorias (`Combustivel`, `Alimentacao`, `Manutencao`), tratamento seguro de exceções previsíveis, validação funcional e conteinerização em Docker.

* **Fora do Escopo:** Persistência em banco de dados SQL/NoSQL, autenticação de usuários e controle de login, agentes autônomos complexos com ferramentas externas (*tool use* / *function calling*), RAG (*Retrieval-Augmented Generation*) e integração com planilhas ou sistemas de gestão externos.

## 📦 5. Instalação e Preparação do Ambiente

### Pré-requisitos

* **Python:** Versão 3.12 ou superior

* **Docker:** Versão 24+ (para execução conteinerizada)

* **Git:** Para clonagem e versionamento

### Instalação Local (Ambiente Virtual)

1. Clone o repositório:

```bash
git clone [https://github.com/Braganando/P0-agentes-llm.git](https://github.com/Braganando/P0-agentes-llm.git)
cd P0-agentes-llm
```

2. Crie e ative um ambiente virtual limpo:

```bash
python3 -m venv venv
# No Linux/macOS:
source venv/bin/activate
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

3. Instale as dependências declaradas:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 🔑 6. Configuração de Acesso ao LLM

O projeto segue as diretrizes de segurança, não armazenando nenhum token, chave ou credencial no código ou repositório.

1. Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env.example .env
```

2. Edite o arquivo `.env` configurando o provedor que deseja utilizar:

```env
# --- Provedor Externo (Google Gemini) ---
GEMINI_API_KEY=sua_chave_de_api_aqui
LLM_MODEL=gemini-3.5-flash

# --- Provedor Institucional / Ollama Local (Devel Lab) ---
OLLAMA_HOST=[https://llm-internal.softex:9001](https://llm-internal.softex:9001)
# Controle de Validação SSL (true = validação padrão; false = diagnóstico; ou /caminho/ca.pem)
LLM_CA_BUNDLE=true

# --- Parâmetros de Execução ---
# Timeout (em segundos) aplicado às requisições da API Gemini; o fallback Ollama usa 120s
LLM_TIMEOUT=25
PORT=8080
```

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

## 🧪 8. Validação Funcional e Cenários de Teste

A aplicação foi validada em dois ambientes complementares — **ambiente local (`localhost:8080`)** para verificação de regras de entrada e tratamento de exceções sem consumo de API, e **ambiente homologado na nuvem (Devel Lab)** para testes de integração *end-to-end* com os provedores de IA (detalhados em [`RELATORIO_EXECUCAO.md`](RELATORIO_EXECUCAO.md)).

### Cenários de Validação Tratados

* **Entrada Válida (Múltiplos ou Únicos Itens):** Gera o objeto JSON estruturado com valores decimais e categorias padronizadas.

* **Entrada Vazia ou Apenas Espaços em Branco:** O envio vazio é bloqueado no navegador (`required`) e entradas compostas apenas por espaços (`"   "`) são interceptadas no back-end via `.strip()`, exibindo orientação clara ao usuário sem acionar a API do LLM.

* **Entrada Fora do Escopo (Sem Valor Financeiro):** Frases conversacionais sem despesas (ex.: *"Olá bom dia tudo bem?"*) são higienizadas e retornam estrutura controlada (`{"despesas": []}`) sem quebrar a interface.

* **Falha de Comunicação, Timeout ou Exceção Genérica:** Indisponibilidades na API externa acionam o *fallback* automático; falhas de rede, timeouts ou exceções inesperadas exibem mensagem controlada na tela e registram o detalhe técnico exclusivamente nos logs do servidor sem gerar erro 500 (*crash*) ou expor *stack traces* ao usuário.

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

## ⚠️ 10. Limitações Conhecidas

1. **Cold Start do Modelo Local:** No ambiente compartilhado do Devel Lab, se o modelo Ollama estiver em *standby*, a primeira requisição pode levar de 60 a 120 segundos para responder, sendo necessário manter o timeout do Gunicorn em `180 s`.

2. **Moedas e Câmbio Estrangeiro:** O extrator assume valores em Reais (`R$`). Valores descritos em moedas estrangeiras (dólar, euro) sem indicação explícita de conversão não realizam conversão cambial.

3. **Escopo Fixo de Categorias:** Caso o usuário descreva um gasto fora de `Combustivel`, `Alimentacao` ou `Manutencao` (ex.: *"paguei a parcela do seguro"*), a IA buscará categorizar no item mais próximo ou descartará caso não haja aderência semântica.

4. **Instabilidade de Rede Externa/Interna:** Picos de demanda, limite de cota ou timeouts na API externa (`429 Too Many Requests`, `503 Service Unavailable`, `504 Deadline Exceeded`) são mitigados por retentativas e *fallback* automático (`gemini-3.8-flash` e servidor Ollama interno). Já lentidões ou timeouts no gateway interno (`504 Gateway Timeout`) são mitigados pelos timeouts estendidos (`120 s` no cliente HTTP e `180 s` no Gunicorn) e pelo tratamento amigável de erros (`APITimeoutError` / `APIStatusError`).

5. **Sanitização Downstream para Persistência SQL (OWASP LLM02):** Embora a aplicação bloqueie *Prompt Injection* direto e force o retorno em schema JSON estrito, payloads SQL inseridos deliberadamente como descrição semântica de uma peça ou item são preservados como texto dentro do atributo `"descricao"`. Portanto, integrações futuras que persistam esse JSON em bancos relacionais devem obrigatoriamente utilizar *Prepared Statements* (queries parametrizadas).

## 🏷️ 11. Tags e Histórico de Releases (Evolução Incremental)

O repositório reflete o desenvolvimento incremental exigido nas diretrizes através das seguintes tags:

* [`p0-basico`](https://github.com/Braganando/P0-agentes-llm/tree/p0-basico): Primeiro fluxo funcional de extração JSON com LLM e dependências isoladas.

* [`p0-intermediario`](https://github.com/Braganando/P0-agentes-llm/tree/p0-intermediario): Modularização do código, criação do `.gitignore`, tratamento de erros e containerização inicial.

* [`p0-avancado`](https://github.com/Braganando/P0-agentes-llm/tree/p0-avancado): Aplicação Web Flask/Gunicorn (`PID 1`, `gthread`) conteinerizada em Docker, resiliência multi-modelo (`v2.1`), blindagem de sanitização, extração segura de JSON, atualização do fallback para `gemini-3.8-flash` e mascaramento de exceções (`v2.1.1`), validação em ambiente limpo no Devel Lab e [`RELATORIO_EXECUCAO.md`](RELATORIO_EXECUCAO.md) completo.

## 🎥 12. Vídeo de Demonstração

* **Link da Apresentação:** [https://youtu.be/oNYYo4qTydE](https://youtu.be/oNYYo4qTydE) *(Vídeo narrado com duração de 5 minutos, publicado como Não Listado no YouTube com legendas revisadas em Português. Nota: após a gravação, foi aplicado o refinamento `v2.1.1` no back-end para bloqueio de entradas compostas apenas por espaços, mascaramento de exceções genéricas, atualização do modelo reserva para `gemini-3.8-flash`, regra explícita de zero despesas no prompt e extração segura via `limpar_json()`, conforme documentado na Seção 2.4 do `RELATORIO_EXECUCAO.md`).*

## 📚 13. Referências Técnicas

* **Devel LLM Portal (Instituto Hardware BR / Softex):** Guia de utilização da plataforma, diretrizes de empacotamento de imagens Docker (`.tar`) e integração com o endpoint institucional `llm-internal.softex:9001`.

* **Google GenAI SDK (`google-genai`):** Documentação oficial para chamadas estruturadas (`response_mime_type="application/json"`) e controle de *timeouts* HTTP.

* **OpenAI Python SDK & Ollama OpenAI Compatibility:** Documentação da camada de compatibilidade `/v1/chat/completions` utilizada para contingência com o modelo `qwen3.5:9b-q4_K_M`.

* **Gunicorn WSGI HTTP Server:** Boas práticas de execução em containers Docker (*exec form* para `PID 1`, tratamento de sinais POSIX `SIGTERM` e dimensionamento de workers `gthread`).

* **OWASP Top 10 for Large Language Model Applications:** Diretrizes de mitigação para *LLM01 (Prompt Injection)* e *LLM02 (Insecure Output Handling)*.

## 🤖 14. Declaração de Uso de Ferramentas de IA

Este projeto foi desenvolvido por **Fernando Braga** com o apoio do **Google Gemini** como assistente de engenharia de software e *pair programming*. A ferramenta de IA auxiliou na refatoração arquitetural para resiliência multi-modelo, na análise diagnóstica de logs de infraestrutura (tratamento de *cold start*, ajuste de *workers* no Gunicorn, parametrização de validação SSL/TLS e higienização de entradas/exceções) e na revisão e formatação da documentação técnica (`README.md` e `RELATORIO_EXECUCAO.md`).

A concepção do problema, as decisões arquiteturais, os testes de segurança (*Prompt Injection* e *SQL Injection* de segunda ordem), a construção das imagens Docker e a validação completa em produção no ambiente Devel Lab foram conduzidos, executados e verificados integralmente pelo autor.

## 👨‍💻 Autor

* **Desenvolvedor:** Fernando Braga

* **Contato:** `nandobraga.cas@gmail.com`

* **Programa:** Residência em Inteligência Artificial (TrendsIA)