# PRD — mercadolivre-mcp

| Campo | Definição |
| --- | --- |
| Versão do documento | 1.0 |
| Data | 22/10/2026 |
| Produto | MCP local do Mercado Livre para o Hermes AI |
| Empresa | Dias Moto Peças — comércio eletrônico de peças e acessórios para motocicletas |
| Versão planejada | V1 / MVP, exclusivamente de leitura comercial |
| Fonte de requisitos | Arquivo fornecido `Texto colado(7).txt` |
| Situação | Planejamento pronto para orientar implementação; código e integração real ainda não validados |
| Ambiente alvo | Windows, VS Code, Python 3.13 e Hermes executado localmente |

## 1. Finalidade e regras de uso deste documento

Este PRD define o que desenvolver, como organizar a implementação, quais regras comerciais aplicar e como comprovar a entrega. Ele não é uma declaração de que o sistema já funciona. As decisões de produto aqui estabelecidas devem orientar o desenvolvimento sem transformar a V1 em uma plataforma maior.

Os termos **DEVE**, **NÃO DEVE** e **OBRIGATÓRIO** indicam requisitos. Valores apresentados como limites internos são decisões deste projeto, não limites atribuídos à API. Pontos identificados como **a confirmar** exigem consulta à documentação vigente e, quando necessário, validação com a aplicação real.

As sprints devem ser executadas em ordem de dependência. Use `- [ ]` para tarefas pendentes e `- [x]` para concluídas. Não marque como concluído algo bloqueado por credenciais, permissões ou validação real. Não implementar o sistema como consequência da geração deste documento.

## 2. Problema e resultado esperado

A empresa precisa investigar o desempenho de suas vendas e anúncios com dados verificáveis da própria conta. Informações dispersas, consultas limitadas à primeira página e cálculos sem critérios explícitos podem gerar recomendações comerciais incorretas.

O produto será uma fonte de dados para o Hermes. O MCP buscará informações na API oficial, validará as respostas e calculará métricas determinísticas em Python. O Hermes interpretará os resultados e formulará recomendações. Não haverá outro agente ou modelo de linguagem dentro do MCP.

### Objetivos da V1

1. Conectar uma conta de vendedor por OAuth oficial, sem compartilhar a senha com o agente.
2. Disponibilizar exatamente sete ferramentas comerciais e uma ferramenta OAuth.
3. Consultar pedidos, anúncios, visitas e perfil da conta autorizada.
4. Produzir resumos e comparações comerciais com regras reproduzíveis.
5. Informar lacunas, restrições de acesso, períodos parciais e falhas sem inventar números.
6. Executar localmente com poucos módulos e instalação reproduzível.

### Indicadores de sucesso

| Indicador | Critério de sucesso |
| --- | --- |
| Descoberta MCP | Hermes identifica exatamente as oito ferramentas previstas |
| Identidade | O perfil consultado corresponde à conta efetivamente autorizada |
| Integridade | Uma amostra manual de pedidos é reconciliada com a origem e com as fórmulas do PRD |
| Paginação | Cada listagem informa continuação; cada agregado demonstra cobertura ou assume incompletude |
| Segurança | Nenhum token, código OAuth, senha ou segredo aparece nas respostas MCP, logs ou arquivos versionáveis |
| Operação | Servidor inicia, encerra e reinicia pelo ambiente local documentado |
| Utilidade | Hermes consegue comparar dois períodos e identificar anúncios com maior queda com base nos retornos |

O aumento de vendas é uma hipótese de benefício, não um critério garantido de aceite do software.

## 3. Usuários, responsabilidades e jornadas

| Papel | Responsabilidade |
| --- | --- |
| Gestor da operação | Solicitar análises, autorizar a conta e avaliar as recomendações |
| Hermes AI | Selecionar ferramentas, solicitar páginas adicionais e interpretar dados e ressalvas |
| MCP | Autenticar, consultar, normalizar, calcular e retornar resultados estruturados |
| Desenvolvedor | Implementar o escopo, registrar decisões e executar verificações manuais |
| Responsável pela aplicação Mercado Livre | Criar/configurar a aplicação, permissões e Redirect URI |

**Conectar a conta:** configurar credenciais localmente → iniciar MCP → chamar `start_oauth` → autorizar no site oficial → callback validado → tokens protegidos → confirmar identidade por `get_seller_profile`.

**Investigar queda de vendas:** solicitar dois períodos → `get_sales_comparison` → identificar anúncios relevantes → consultar detalhes e visitas desses anúncios → Hermes apresenta evidências, hipóteses e ações propostas.

**Investigar visitas sem vendas:** listar anúncios próprios, incluindo os sem pedidos no período → consultar visitas em lotes limitados → combinar com vendas por ID. O MCP não deve escolher apenas os mais vendidos, pois isso ocultaria anúncios com tráfego e nenhuma venda.

## 4. Escopo e exclusões

### Incluído

- Uma operação comercial, uma aplicação e uma conta autorizada por instalação.
- Servidor FastMCP por `stdio`.
- OAuth Authorization Code, `state`, PKCE quando habilitado/exigido, callback e renovação segura.
- Perfil do vendedor, pedidos, anúncios próprios, detalhes e visitas.
- Agregação de vendas e comparação entre períodos.
- Validação Pydantic, cliente HTTP centralizado e tratamento de erros.
- Documentação de instalação, configuração, OAuth, Hermes e verificações manuais.

### Fora da V1

- Criar/editar anúncios, alterar preços ou estoque, cancelar pedidos e responder perguntas.
- Ads, campanhas e atribuição de tráfego como orgânico ou pago sem dados específicos.
- Integração NetOne, outros marketplaces e pesquisas de concorrentes.
- Dashboard, frontend, API REST de negócio, notificações e webhooks comerciais.
- Banco de dados, data warehouse, histórico próprio, Docker, Redis, Celery e hospedagem externa.
- Multiempresa, múltiplos vendedores simultâneos, sistema multiagente e processamento agendado.
- Cálculo de lucro líquido, conciliação financeira completa, custos e margens.
- Testes automatizados, `pytest`, arquivos `test_*.py` e infraestrutura de testes.
- Commits e pushes automáticos sem instrução expressa do usuário.

**Exceção necessária:** um receptor temporário de callback OAuth é permitido. Ele não é uma API comercial e deve ser encerrado após autorização ou expiração. A necessidade de HTTPS deve ser resolvida antes de declarar a autenticação viável no ambiente local.

## 5. Premissas, dependências e decisões pendentes

### Premissas de produto

- A empresa opera no Brasil, com fuso padrão `America/Sao_Paulo`; moeda é obtida nos dados e não presumida em cada registro.
- O Hermes será executado no mesmo Windows e usuário que possuem acesso ao cofre de credenciais.
- A V1 atende análises sob demanda, sem armazenamento histórico comercial.
- Haverá somente um processo utilizando o mesmo conjunto de tokens por vez.
- Permissões e disponibilidade dos recursos podem variar conforme aplicação, vendedor e políticas da plataforma.

### Dependências externas

- Acesso ao portal Developers e criação de aplicação habilitada para a integração.
- Client ID e Client Secret, inseridos localmente fora da conversa com o agente.
- Redirect URI HTTPS exata, registrada e utilizável no ambiente escolhido.
- Autorização humana no site oficial e conta com permissões para os recursos.
- Windows com backend seguro de credenciais acessível ao processo.
- Versão instalada do Hermes com suporte a MCP `stdio` e configuração confirmada.
- Acesso de rede aos domínios oficiais e Python com SSL funcional.

### Decisões de entrada obrigatórias

| ID | Decisão / confirmação | Responsável | Momento | Condição para avançar |
| --- | --- | --- | --- | --- |
| D01 | Aplicação criada e permissões mínimas disponíveis | Gestor + desenvolvedor | Sprint 0 | Checklist real da aplicação registrado, sem segredos |
| D02 | Viabilidade de callback HTTPS local, host e certificado | Desenvolvedor | Sprint 0 | URI aceita no portal, roteada ao receptor local e certificado confiável no navegador |
| D03 | Limites atuais de pedidos, visitas e bulk | Desenvolvedor | Sprint 0 | Fonte e limites registrados; pontos incertos permanecem explícitos |
| D04 | Sintaxe MCP da versão instalada do Hermes | Desenvolvedor | Sprint 0/6 | Comando, argumentos, diretório e variáveis confirmados |
| D05 | Versões compatíveis das dependências | Desenvolvedor | Sprint 1 | Instalação limpa em Python 3.13 e versões exatas registradas |

Ausência de credenciais não bloqueia fundação, contratos e documentação. Ausência de um callback HTTPS viável bloqueia a conclusão da autenticação real; não deve ser mascarada por token manual colado no chat, HTTP presumido ou serviço externo criado sem decisão de escopo.

## 6. Arquitetura e organização do código

Fluxo principal: **Hermes → FastMCP/stdio → ferramentas → cliente HTTP/autenticação → API oficial → validação e cálculo → resposta estruturada**.

### Stack

| Tecnologia | Uso obrigatório ou decisão |
| --- | --- |
| Python 3.13 | Versão inicial de referência; versões posteriores somente após confirmar compatibilidade |
| FastMCP | Servidor, registro, schemas e transporte `stdio` |
| requests | Comunicação HTTP com `requests.Session` |
| Pydantic | Modelos de entrada, saída e validação dos dados necessários |
| python-dotenv | Carregamento da configuração local |
| keyring | Dependência adicional justificada pelo armazenamento no cofre nativo do Windows |
| tzdata | Dependência adicional para disponibilizar base IANA ao `zoneinfo` no Windows |
| Biblioteca padrão | Decimal, datas, locks, OAuth aleatório, hash/PKCE, TLS e callback |
| Git/GitHub | Versionamento e documentação; não são necessários para executar consultas |
| LangChain 1.x | Somente se uma necessidade concreta surgir; não instalar na V1 por padrão |

Fixar em `requirements.txt` as versões efetivamente verificadas, incluindo dependências transitivas se necessário para reproduzir o ambiente. Não inventar versões compatíveis no planejamento. Evitar instalar ferramentas de desenvolvimento desnecessárias.

### Estrutura prevista

```text
mercadolivre-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py
│   ├── client.py
│   ├── auth.py
│   ├── tools.py
│   └── schemas.py
├── .env                 # local, nunca versionado
├── .env.example         # somente placeholders
├── .gitignore
├── requirements.txt
├── README.md
└── PRD.md
```

| Módulo | Responsabilidades e limites |
| --- | --- |
| `server.py` | Compor dependências, carregar configuração a partir da raiz, configurar logs, controlar ciclo de vida e iniciar `stdio`; não calcular métricas |
| `client.py` | Sessão HTTP, allowlist de destinos, timeouts, retries, paginação e integração com renovação; não formular recomendações |
| `auth.py` | Configuração OAuth, `state`, PKCE, callback, cofre, exclusão mútua e renovação; não expor segredos |
| `tools.py` | Oito ferramentas, coordenação das consultas, normalização e cálculos reutilizáveis |
| `schemas.py` | Entradas, saídas, erros, datas, dinheiro e metadados; não reproduzir toda a API |
| `__init__.py` | Identificar o pacote, sem executar chamadas de rede no import |

Usar uma função de registro que receba a instância FastMCP em `tools.py`, evitando import circular com `server.py`. Criar outro módulo apenas quando houver responsabilidade concreta que prejudique a clareza dos módulos atuais.

### Execução, estado e concorrência

- Ferramentas HTTP devem ser funções síncronas executadas fora do event loop conforme o FastMCP da versão fixada. Não chamar `requests` diretamente dentro de `async def` sem mecanismo documentado de execução em thread [S07].
- A V1 deve serializar o uso da sessão e as operações sensíveis de tokens com lock reentrante, evitando acesso concorrente inseguro a `Session` e renovação duplicada. Não criar pool paralelo de chamadas comerciais.
- Manter lock exclusivo de processo no Windows, por exemplo com `msvcrt.locking` em arquivo local sem segredos. O mesmo perfil de credenciais não pode ser usado por dois processos MCP ou por CLI e MCP simultaneamente.
- Manter em memória apenas sessão, identidade, autorização pendente, resultados em processamento e tokens necessários ao uso. Não persistir respostas comerciais em disco.
- Logs e diagnósticos exclusivamente em `stderr`; `stdout` reservado ao protocolo MCP. Não imprimir banners próprios ou mensagens de instalação em `stdout`.
- Encerrar sessão, listener OAuth e locks no desligamento. Iniciar sem autorização deve permitir descobrir ferramentas e chamar OAuth; não simular conta conectada.

## 7. Fontes oficiais e contrato de integração REST

Base comercial fixa: `https://api.mercadolibre.com`. A ferramenta não aceita uma URL fornecida pelo agente. Parâmetros devem ser passados pelo mecanismo de query/body da biblioteca, nunca concatenados como destinos arbitrários.

### Recursos previstos

| Uso | Método e rota | Parâmetros / observações | Referência |
| --- | --- | --- | --- |
| Autorizar no Brasil | Navegação para `https://auth.mercadolivre.com.br/authorization` | `response_type=code`, `client_id`, `redirect_uri`, `state`; parâmetros PKCE quando aplicáveis | S01 |
| Trocar código / renovar | `POST /oauth/token` | Form URL encoded no body; `grant_type` e campos oficiais por fluxo | S01 |
| Identidade | `GET /users/me` | Bearer da conta autorizada | S02 |
| Pedidos | `GET /orders/search` | `seller` derivado da identidade; filtros `order.date_created.from/to`, `order.status` quando solicitado e paginação oficial | S03 |
| Detalhe de pedido | `GET /orders/{order_id}` | Somente enriquecimento interno se a busca não fornecer campos essenciais; validar vendedor | S03 |
| IDs de anúncios próprios | `GET /users/{user_id}/items/search` | `status`, `limit`, `offset` ou `search_type=scan` com `scroll_id` conforme modo | S04 |
| Detalhe de anúncio | `GET /items/{item_id}` | Validar `seller_id` antes de expor o resultado | S04 |
| Enriquecimento de vários anúncios | `GET /items/bulk` | `ids`; seleção de atributos com prefixo `body.` e falhas por elemento | S04 |
| Visitas no período | `GET /items/visits` | `ids`, `date_from`, `date_to`; limites e semântica temporal próprios | S05 |

Este é o registro de rotas **planejadas**, não de chamadas já executadas. Ao implementar, atualizar esta tabela com os recursos realmente utilizados e retirar os desnecessários.

**Mudança já identificada:** a documentação de itens consultada orienta substituir `/items?ids=` por `/items/bulk?ids=`, com migração até 25/10/2026; o novo formato usa `status_code` e seleção `body.<campo>`. Desenvolver diretamente com a rota nova e validar seu formato real; não copiar o parser do multiget antigo [S04].

### Paginação e cobertura

- `list_orders` e `list_seller_items` retornam uma página por chamada, com continuação explícita; uma página válida não significa que toda a consulta foi coletada.
- `get_sales_summary` percorre internamente todas as páginas necessárias; `get_sales_comparison` reutiliza a mesma agregação para cada período.
- IDs devem ser deduplicados. Repetição de página/cursor sem progresso deve interromper a coleta com erro de incompletude.
- No scan de itens, não enviar `offset`. Usar o cursor conforme a regra vigente, vinculado à conta e aos filtros. Cursor expirado gera `CURSOR_EXPIRED` e orientação para reiniciar; não voltar silenciosamente à primeira página.
- Não aplicar scan de itens em pedidos. Se pedidos excederem a janela de paginação oficial, dividir o período em intervalos menores, sem sobreposição lógica, e deduplicar por `order_id`.
- Se nem a menor janela permitida pela granularidade oficial comportar todos os pedidos, retornar `PARTIAL_DATA`. Não inventar paginação ou prometer completude.
- Consultas são leituras sequenciais da API, sem snapshot transacional. Registrar início/fim da coleta e avisar quando a operação estiver mudando durante a consulta.

### Limites internos iniciais

| Limite | Padrão do projeto | Regra |
| --- | --- | --- |
| Página de listagem | 20; máximo interno 50 | O menor limite entre projeto e endpoint prevalece |
| Anúncios por chamada de visitas | 1 a 20 IDs únicos | Dividir em lotes menores se a API exigir |
| `top_n` | 10; entre 1 e 50 | Limita somente rankings, nunca a população usada no total |
| Período de vendas por agregação | Até 120 dias | Permite analisar aproximadamente três meses; respeitar retenção oficial |
| Consultas por agregação | Até 500 GETs ou 180 segundos | Incluir enriquecimentos e tentativas no orçamento; comparação compartilha esse orçamento |
| Janela OAuth pendente | Até 5 minutos | Limite interno, não afirmação de validade do código oficial |
| Tamanho serializado da resposta | Até 256 KiB | Paginar, limitar campos ou rejeitar; não cortar JSON nem omitir linhas silenciosamente |

Os limites acima são configuráveis localmente quando indicado na seção 14. A configuração não pode ultrapassar limites oficiais. Ao atingir orçamento, marcar incompletude e recomendar um período menor; a V1 não terá jobs, retomada persistente ou processamento em segundo plano de análises.

## 8. Contrato comum das ferramentas

### Validação de entradas

- IDs de anúncios do Brasil: formato `MLB` seguido de dígitos; validar também propriedade, pois formato não comprova autorização.
- IDs numéricos de conta/pedido são strings no contrato externo para evitar perda de precisão por clientes.
- Datas públicas usam `YYYY-MM-DD`. A data final é inclusiva na intenção do usuário; converter internamente para intervalo `[início às 00:00, dia seguinte ao fim às 00:00)` no fuso da empresa.
- Rejeitar início posterior ao fim, dias futuros e períodos maiores que o limite aplicável. Um período que inclua hoje é permitido com `period_is_open=true`.
- Não corrigir entradas inválidas silenciosamente. Se a API não representar exatamente o intervalo, devolver período efetivo e advertência; não afirmar precisão inexistente.
- `limit`, `offset`, `top_n` e listas de IDs têm validação de tipo, faixa e tamanho. Rejeitar `offset` negativo e combinação de cursor com offset.
- Filtrar estados somente pelos valores documentados e suportados. Estados novos recebidos da API devem ser preservados como desconhecidos, não convertidos em `paid`.

### Envelope de resposta

| Campo | Tipo / regra |
| --- | --- |
| `success` | Booleano; verdadeiro quando o objetivo da chamada foi atendido; pode haver ressalvas não impeditivas |
| `data` | Objeto validado específico da ferramenta; `null` quando nenhum resultado utilizável existe |
| `period` | Objeto com datas solicitadas, início/fim efetivos, fuso e convenção; `null` nas ferramentas sem período |
| `metadata` | Fonte, versão do contrato, identidade, horário de coleta, paginação e cobertura |
| `warnings` | Lista de objetos com `code` e `message`, sem segredos |
| `error` | `null` no sucesso; objeto com `code`, `message`, `retryable` e `retry_after_seconds` quando conhecido |

Metadados obrigatórios conforme aplicabilidade: `schema_version="1.0"`, `source="mercadolivre_api"`, `seller_id`, `retrieved_at` em UTC, `collection_started_at`, `collection_finished_at`, `endpoints_used` sem query sensível, `records_processed`, `api_total` quando fornecido, `has_more`, `next_offset` ou `next_cursor`, `collection_complete`, `period_is_open`, `coverage_reason`, `methodology_version` e `request_id` local.

**Semântica de completude:** `collection_complete` informa se todos os registros do escopo solicitado foram coletados. Em uma página, `success=true` e `has_more=true` são válidos; `collection_complete=false` informa que ainda restam páginas. Em agregados, coleta incompleta exige `success=false`, `error.code="PARTIAL_DATA"` e métricas definitivas `null`. Valores observados, se retornados, ficam em `data.partial_observed_metrics`, sem extrapolação. `period_is_open` é independente da cobertura: o período de hoje pode ter sido totalmente consultado e ainda mudar.

Dinheiro deve ser calculado com `Decimal` a partir da representação decimal dos números, preservando precisão ao decodificar JSON, e serializado como texto decimal acompanhado de `currency_id`. Não somar moedas distintas. Campos ausentes usam `null` e motivo; zero só é permitido quando há evidência de ausência na população completa.

Erros de validação gerados antes da execução pelo FastMCP podem usar o erro de protocolo documentado. Erros de domínio e da API devem usar o envelope padronizado; nunca retornar traceback ao Hermes. Se a versão do FastMCP permitir associar `isError` sem perder saída estruturada, fazê-lo e confirmar no cliente; o consumidor sempre deve verificar `success`.

### Modelos mínimos

`ToolResult`, `ToolError`, `Warning`, `Period`, `Metadata`, `Pagination`, `Money`, `SellerProfile`, `Order`, `OrderLine`, `SellerItem`, `ItemDetails`, `ItemVisits`, `SalesSummary`, `ItemSales` e `SalesComparison`. Modelar somente campos usados. Entradas devem rejeitar campos desconhecidos; respostas externas podem conter outros campos, mas a projeção de saída deve ser explícita.

## 9. Especificação das oito ferramentas

### RF01 — `get_seller_profile`

**Entrada:** nenhuma. A identidade nunca é escolhida pelo agente.

**Saída:** `seller_id`, `nickname`, `country_id`, `site_id`, situação da conta e projeção mínima de reputação disponível. Não incluir CPF/CNPJ, endereço, telefone ou e-mail.

**Processamento:** exigir autorização, consultar `/users/me`, validar resposta e registrar identidade para as demais chamadas. País/site ausentes ficam `null`; não inferir que o domínio consultado comprova o país da conta.

**Aceite:** identidade confirmada na conta real; sem autorização retorna `AUTH_REQUIRED`; dados pessoais excedentes não chegam ao Hermes.

### RF02 — `list_orders`

**Entrada:** `date_from`, `date_to`, `status=null`, `limit=20`, `offset=0`.

**Saída por pedido:** ID, `date_created`, `date_closed` quando disponível, estado atual, moeda, total declarado pela API, linhas com `item_id`, `variation_id` opcional, título, quantidade e preço unitário. Incluir somente os indicadores de pagamento/reembolso necessários às regras da seção 10; não retornar objeto bruto do comprador ou pagamento.

**Processamento:** derivar `seller`, traduzir filtros, buscar uma página e aplicar a convenção temporal do contrato. A documentação de pedidos informa limitações de granularidade dos filtros; a implementação deve ampliar a consulta quando necessário e filtrar os registros localmente para manter os limites corretos [S03]. Não alterar o offset oficial com base apenas na quantidade de registros que sobreviveram ao filtro local.

**Aceite:** página e continuação explícitas; pedidos não pagos permanecem distintos dos pagos; nenhum pedido de outro vendedor é exposto. Sem `status`, consultar a população suportada pela API e explicitar eventuais exclusões padrão.

### RF03 — `list_seller_items`

**Entrada:** `status=null`, `limit=20`, `offset=null`, `cursor=null`. Ausência de offset/cursor inicia scan; offset explícito seleciona paginação convencional quando permitida. Não aceitar ambos.

**Saída:** lista com ID, título, preço e moeda, status e disponibilidade quando obtida; `pagination_mode`, continuação e falhas de enriquecimento por ID.

**Processamento:** buscar IDs da conta, enriquecer por bulk atual e respeitar falhas individuais. Sem status, listar o universo de estados disponibilizado pela API, sem restringir automaticamente a ativos. No mínimo, oferecer filtro explícito para ativos e pausados.

**Aceite:** scan não usa offset; erro em um anúncio não apaga os demais; item sem detalhe continua identificado com limitação explícita; título e preço não são inventados.

### RF04 — `get_item_details`

**Entrada:** `item_id`.

**Saída:** ID, vendedor, título, preço/moeda, `available_quantity` quando permitido, `quantity_precision` (`exact`, `referential` ou `unknown`), status, categoria, atributos relevantes e permalink HTTPS fornecido pela API. Incluir variações somente com campos necessários e respeitar limite de resposta.

**Processamento:** consultar recurso oficial e verificar `seller_id`. Resultado de outro vendedor gera `PERMISSION_DENIED`, mesmo que seja publicamente consultável. Não seguir o permalink com credenciais.

**Aceite:** distinguir estoque referencial do exato; ausência de certeza gera `unknown`; não apresentar o estoque atual como evidência de estoque passado.

### RF05 — `get_item_visits`

**Entrada:** `date_from`, `date_to` e exatamente um de `item_id` ou `item_ids` (1 a 20 IDs únicos).

**Saída:** por ID, visitas totais, período solicitado e efetivamente coberto, situação de disponibilidade e eventuais erros individuais. Formatos de resposta de um ID e múltiplos IDs devem ser normalizados para a mesma lista.

**Processamento:** validar propriedade dos anúncios antes de consultar tráfego, reutilizando evidências obtidas na mesma execução. Respeitar janela máxima e antiguidade dos dados. A documentação consultada menciona limite de 150 dias; confirmar se corresponde à extensão do intervalo, à antiguidade ou a ambas antes de fixar a tradução dos filtros [S05]. Dividir janelas não deve ser usado para tentar contornar retenção indisponível.

**Aceite:** anúncio sem dado retorna `null` com motivo; zero real permanece zero; falha parcial não vira tráfego inexistente; visitas não são chamadas de compradores únicos ou tráfego orgânico.

### RF06 — `get_sales_summary`

**Entrada:** `date_from`, `date_to`, `top_n=10`.

**Saída:** faturamento bruto estimado, pedidos pagos, unidades, ticket médio, pedidos cancelados identificáveis, contagens por estado, indicadores disponíveis de reembolso e dois rankings: `top_items_by_units` e `top_items_by_revenue`. Cada ranking inclui ID, título observado, unidades e faturamento estimado.

**Processamento:** coletar a população de pedidos do período, deduplicar e calcular conforme seção 10. Não filtrar toda a coleta por `paid`, pois isso impediria contabilizar cancelamentos e outros estados. Utilizar uma função interna reutilizável para produzir agregados completos por anúncio antes de aplicar `top_n`.

**Aceite:** totais independem de `top_n`; totais por anúncio fecham com o total calculado; coleta incompleta invalida métricas definitivas. Ranking é uma seleção explícita, com `ranked_count` e `total_distinct_items`, não uma lista completa disfarçada.

### RF07 — `get_sales_comparison`

**Entrada:** `period_a_start`, `period_a_end`, `period_b_start`, `period_b_end`, `top_n=10`. A é a base e B é o período comparado.

**Saída:** resumo de A e B, diferença absoluta e percentual de faturamento, pedidos pagos, unidades e ticket; duração e média diária de cada período; anúncios com maiores quedas e crescimentos absolutos de faturamento. Cada anúncio mostra valores dos dois períodos e sua variação.

**Processamento:** reutilizar agregação de RF06, unindo todos os IDs observados nos dois períodos antes de ranquear. Não comparar apenas os respectivos top N. Anúncio presente em apenas um período recebe zero no outro somente se a coleta desse período estiver completa. Empates devem ser ordenados por ID para estabilidade.

**Aceite:** avisar durações diferentes e sobreposição; não substituir valores absolutos por médias silenciosamente; divisão por zero retorna percentual `null` com motivo. Se qualquer período estiver incompleto, não emitir rankings ou variações definitivas.

### RF08 — `start_oauth`

**Entrada:** `open_browser=true`. Não aceitar senha, código, token, URL de callback ou Client Secret como parâmetro MCP.

**Saída:** `status` (`pending`, `connected`, `denied`, `expired` ou `failed`), URL oficial de autorização quando pendente, horário de expiração interna e instrução segura. Sem segredos. `connected` exige tokens válidos e identidade confirmada.

**Processamento:** se já houver autorização válida, retornar conexão existente; se houver fluxo pendente, retornar o mesmo estado/URL sem abrir novos listeners; caso contrário iniciar callback e autorização. Retornar rapidamente com `pending`, sem bloquear a ferramenta aguardando a pessoa. O callback conclui a troca internamente. Nova chamada à mesma ferramenta consulta o estado; não criar nona ferramenta de status.

Abrir o navegador é uma tentativa local. Se falhar ou o ambiente não permitir, retornar URL para o usuário. Reautorizações após revogação ou expiração devem iniciar uma nova transação; uma substituição deliberada de conta exige encerrar a conexão e limpar o perfil local por procedimento administrativo documentado, sem ferramenta comercial extra.

**Aceite:** uma única transação pendente, `state` inválido rejeitado e conta não conectada antes de validar tokens e perfil. OAuth modifica o estado local; sua anotação MCP não deve alegar ausência total de efeitos colaterais.

## 10. Regras comerciais e fórmulas

### 10.1 População e eixo temporal

O eixo da V1 será a **data de criação do pedido**, aplicada igualmente a listagens, resumo e comparação. O período representa pedidos criados nele cujo estado é observado no instante da consulta. Não chamar esse resultado de fluxo de caixa recebido no período ou de vendas aprovadas pela data de pagamento.

Um pedido criado antes do período e pago durante ele fica fora; um criado no período e pago depois pode passar a compor o resultado em uma consulta posterior. Cancelamentos e reembolsos posteriores também podem alterar consultas históricas. Essa limitação deve constar em `methodology_version="created_paid_v1"` e na documentação do Hermes.

Deduplicar por `order_id`; `pack_id` não substitui o identificador do pedido e não deve consolidar pedidos distintos. Repetições conflitantes devem usar a versão mais atual quando houver timestamp confiável; sem critério confiável, sinalizar conflito e incompletude da métrica afetada.

### 10.2 Faturamento bruto estimado e elegibilidade

Para cada linha válida de pedido cujo estado atual seja exatamente `paid`:

```text
valor_linha = Decimal(preço_unitário_transacional) × quantidade
faturamento_bruto_estimado = soma dos valores_linha dos pedidos elegíveis
pedidos_pagos = quantidade de IDs únicos com estado paid
unidades_vendidas = soma das quantidades das linhas dos pedidos elegíveis
ticket_medio = faturamento_bruto_estimado / pedidos_pagos
```

- Usar preço transacional da linha, nunca preço atual do anúncio.
- `confirmed`, `payment_required`, `payment_in_process`, `partially_paid` e estados desconhecidos não compõem pedidos pagos.
- Pedidos `cancelled`, `pending_cancel`, `partially_refunded` ou com devolução integral identificada devem ser contados separadamente e excluídos do faturamento principal desta metodologia conservadora.
- Se um pedido `paid` contiver evidência contraditória de reembolso, classificá-lo como exceção de reembolso, excluí-lo do conjunto elegível e explicitar a quantidade e o critério. Nesse caso, `paid_orders_count` deve contar somente os pedidos elegíveis usados na fórmula, acompanhado de `api_paid_status_count` para distinguir o estado bruto recebido.
- Reembolso parcial não deve ser subtraído sem valores e vínculo confiáveis. A exclusão integral desses pedidos pode subestimar o bruto comercial original; tornar essa limitação explícita. `refund_adjusted_revenue` permanece `null` na V1.
- Frete, taxas, comissões, custo do produto, impostos e descontos/cuponagens não representados no preço de linha não são somados/subtraídos arbitrariamente.
- Total declarado do pedido e valores de pagamentos podem ser retornados separadamente para rastreabilidade; nunca somar pagamento e linhas como receitas independentes.
- Linha sem preço, quantidade, moeda ou ID necessário à agregação não recebe valor zero. Invalidar a métrica afetada e registrar quantidade de registros problemáticos.
- Calcular com precisão decimal e arredondar apenas na apresentação, para casas da moeda; BRL usa duas casas e `ROUND_HALF_UP`. Ticket e percentuais também devem ter regra estável documentada.

O rótulo obrigatório é **faturamento bruto estimado dos pedidos elegíveis**. Não é lucro, receita líquida, saldo de recebíveis ou conciliação com o painel do Mercado Livre. Comparações com o painel precisam usar a mesma data-base, status e composição monetária.

### 10.3 Cancelamentos, ausência de pedidos e moedas

- `cancelled_orders_count` conta IDs únicos com status de cancelamento documentado, dentro da mesma coorte de criação. Se a busca não disponibilizar essa população, retornar `null` e explicar.
- Ausência de pedidos em coleta completa permite contagens e faturamento iguais a zero. Ticket médio sem pedidos é `null` por denominador zero.
- Agrupar dinheiro e métricas por `currency_id`. A operação normalmente usa BRL, mas moedas diferentes não são convertidas nem somadas. Retornar por moeda; variações só entre a mesma moeda.
- Campos de cancelamento e reembolso representam o que a API tornou visível; não prometer reconstrução de todos os eventos financeiros.

### 10.4 Ranking e comparação

```text
delta_absoluto = valor_B − valor_A
delta_percentual = ((valor_B − valor_A) / valor_A) × 100, somente se valor_A ≠ 0
media_diaria = valor_do_periodo / quantidade_de_dias_calendario_inclusivos
```

Base zero e valor positivo em B: percentual `null`, motivo `ZERO_BASE`, descrição objetiva de surgimento de vendas. Ambos zero: percentual `null`, motivo `ZERO_BASE`, delta absoluto zero. Valor A positivo e B zero: variação de −100%.

O ranking principal de quedas/crescimentos é por diferença absoluta de faturamento por ID de anúncio, separado por moeda. Não unificar anúncios por títulos parecidos, SKU ou republicação sem vínculo comprovado. Renomeação usa o mesmo ID; título exibido deve informar a origem temporal disponível.

### 10.5 Visitas e interpretação

Visitas e pedidos só devem ser combinados para o mesmo ID e intervalos compatíveis. Não calcular uma taxa de conversão exata de compradores únicos com esses dados. Unidades/visitas, quando usadas pelo Hermes, são um indicador aproximado com metodologia explícita, e não uma nova métrica oficial do MCP.

Estado e estoque atuais não comprovam disponibilidade histórica. Queda simultânea de visitas e vendas não comprova que preço, concorrência ou estoque causaram o resultado. Dados de visitas também não comprovam separação entre orgânico e Ads.

## 11. OAuth e armazenamento seguro

### Fluxo de autorização

1. Verificar configuração, certificado, cofre e exclusão mútua do processo.
2. Gerar `state` criptograficamente aleatório e de uso único; manter vínculo com transação e expiração em memória.
3. Se PKCE estiver habilitado/exigido, gerar `code_verifier` e challenge `S256`, mantendo o verifier fora de logs e respostas [S01].
4. Iniciar receptor do callback antes de abrir a autorização. Listener apenas local, rota exata, limite de tamanho de requisição e sem listagem/servidor de arquivos.
5. Gerar URL oficial; retornar ao usuário e tentar abrir navegador quando permitido.
6. Receber callback, validar caminho, expiração, erro OAuth e `state` com comparação segura antes de trocar o código.
7. Trocar código por tokens com POST oficial; não repetir cegamente esse POST em timeout.
8. Consultar identidade com o token recebido e validar associação entre aplicação, vendedor e perfil configurado.
9. Persistir conjunto completo no cofre protegido e somente então declarar `connected`.
10. Invalidar transação, descartar código/verifier e encerrar listener após conclusão ou expiração. Callback repetido é rejeitado.

### Callback HTTPS local

A documentação oficial consultada exige Redirect URI HTTPS exata [S06]. **Não presumir que `http://localhost` será aceito**. A preferência é um receptor HTTPS ligado ao loopback no próprio Windows, com nome resolvido localmente e certificado confiável, desde que o portal aceite essa URI.

A Sprint 0 deve comprovar essa viabilidade. Certificado e chave são configuração local; não versionar chave privada nem desabilitar TLS do cliente HTTP. O README deverá documentar o host, porta, URI, configuração do certificado e remoção posterior, sem inventar um endereço já aprovado. Se a plataforma não aceitar a solução local, registrar o impedimento e a menor mudança de requisito necessária. Não adicionar túnel, servidor externo ou coleta do código via chat como solução automática.

### Cofre e rotação

- Usar `keyring` com backend seguro nativo do Windows validado. Backend nulo ou armazenamento em texto puro provoca `SECURE_STORAGE_UNAVAILABLE`; não fazer fallback para JSON em disco.
- Guardar uma única unidade lógica com access token, refresh token, expiração, vendedor, aplicação e versão do registro, identificada por aplicação/perfil. JSON dentro do cofre protegido é permitido; arquivo JSON aberto no disco não é.
- Usar `expires_in` recebido, não prazo fixo presumido. Renovar com margem interna inicial de 60 segundos.
- Antes da renovação, adquirir lock, reler a credencial vigente e verificar se ainda precisa renovar. Persistir o novo conjunto antes de liberar o acesso às próximas chamadas.
- Refresh token é rotativo e de uso único segundo a documentação consultada [S01]. Apenas uma renovação pode ocorrer por perfil de cada vez.
- Em timeout após envio da renovação, o consumo do refresh token é incerto. Não reapresentar automaticamente o mesmo refresh token. Interromper a sessão com `AUTH_REQUIRED` ou `OAUTH_RESULT_UNCERTAIN` e orientar reautorização.
- Falha ao persistir tokens novos interrompe a operação. Não declarar conexão recuperável com credencial antiga já consumida. Se o processo cair entre a troca e a gravação, nova autorização pode ser necessária; a V1 não promete transação distribuída com a plataforma.
- Em `invalid_grant`, revogação ou credencial inválida, invalidar a sessão local e permitir nova autorização.
- Procedimento local de desconexão deve encerrar o processo e remover o registro do cofre sem exibir seu conteúdo. Não adicionar ferramenta MCP além das oito previstas.

## 12. Cliente HTTP, erros e observabilidade

### Política de rede

- Sessão reutilizada com verificação TLS ativa e Bearer apenas nos recursos permitidos.
- Métodos comerciais restritos a GET na allowlist de rotas. POST permitido somente para `/oauth/token`; nenhum PUT, PATCH ou DELETE comercial.
- Desabilitar redirecionamento automático nas chamadas autenticadas; destino inesperado é erro, sem repasse de Authorization.
- Timeouts internos iniciais: conexão 5 segundos e leitura 30 segundos. O orçamento global considera todas as chamadas e esperas; não alegar que o timeout do requests garante sozinho um prazo total rígido.
- GETs: até três tentativas totais para erro de conexão transitório, timeout, HTTP 429 e 500/502/503/504. Backoff exponencial com jitter, base de 1 segundo e teto interno de 8 segundos.
- Respeitar `Retry-After` válido quando presente. Se a espera ultrapassar o orçamento restante, retornar `RATE_LIMITED` com orientação de nova tentativa, em vez de ignorar o servidor.
- 401: no máximo uma renovação segura e uma repetição do GET original. Segundo 401 encerra a tentativa.
- 403: `PERMISSION_DENIED`, sem renovar token repetidamente. Demais 4xx não têm retry automático salvo regra oficial específica.
- Decodificar/validar JSON e campos essenciais; HTML, payload inválido e divergência de schema geram erro explícito.
- Não atribuir um número universal de requisições por segundo ao Mercado Livre. Confirmar regras por recurso e reduzir chamadas, usar bulk e processar sequencialmente.

### Catálogo de erros

| Código | Situação e tratamento esperado |
| --- | --- |
| `AUTH_REQUIRED` | Sem credencial válida; chamar `start_oauth` |
| `TOKEN_EXPIRED` | Renovação segura não recuperou a sessão; reautorizar quando indicado |
| `CONFIGURATION_ERROR` | Variável, URI, certificado ou parâmetro local inválido |
| `SECURE_STORAGE_UNAVAILABLE` | Cofre protegido ausente/inacessível; corrigir ambiente |
| `OAUTH_RESULT_UNCERTAIN` | Troca/renovação com resultado remoto incerto; não repetir token de uso único |
| `OAUTH_STATE_INVALID` | Callback não corresponde à transação; rejeitar |
| `PERMISSION_DENIED` | Recurso sem permissão ou pertencente a outra conta |
| `INVALID_DATE_RANGE` | Intervalo inválido/futuro/acima dos limites aplicáveis |
| `INVALID_ARGUMENT` | ID, enum, paginação ou limite inválido |
| `CURSOR_EXPIRED` | Scan sem continuação válida; reiniciar de forma explícita |
| `ITEM_NOT_FOUND` | Anúncio inexistente ou não disponível conforme resposta oficial |
| `RATE_LIMITED` | Limite atingido após política limitada de espera |
| `API_UNAVAILABLE` | Falha transitória esgotou tentativas |
| `INVALID_API_RESPONSE` | Resposta não interpretável ou campo essencial inconsistente |
| `DATA_NOT_AVAILABLE` | Histórico ou métrica indisponível; não substituir por zero |
| `PARTIAL_DATA` | Falha/orçamento/paginação impediu concluir o objetivo |
| `PROCESS_ALREADY_RUNNING` | Outro processo possui o perfil de credenciais |

### Logs

Registrar somente horário, nível, ferramenta, `request_id`, template da rota, duração, status HTTP, tentativas e contagens. Não registrar headers completos, body de token, query de callback, corpo bruto da API, nome de comprador ou URL de autorização completa. Desativar access logs do receptor que revelem código/state.

`LOG_LEVEL=INFO` por padrão; modo DEBUG não relaxa a remoção de segredos. A V1 não precisa de serviço externo de telemetria ou arquivos de log persistentes por padrão.

## 13. Segurança e integridade

- `.env`, `.venv`, chaves privadas, certificados locais quando sensíveis, caches e arquivos runtime devem estar no `.gitignore`.
- `.env.example` contém apenas placeholders. Client Secret fica em variável de ambiente local; proteger a pasta com permissões do usuário e não fazer sync público.
- OAuth deve usar permissões mínimas efetivamente oferecidas pelo portal. Não inventar nomes de scopes. Mesmo que a plataforma conceda mais permissões, o código deve restringir métodos e rotas.
- Não expor access token, refresh token, código OAuth, verifier, senha ou Client Secret ao modelo.
- Não aceitar seller arbitrário, cabeçalhos de autenticação ou destinos HTTP nas ferramentas.
- Dados textuais de anúncios são conteúdo externo não confiável, nunca instruções para o servidor ou Hermes. Não executar comandos contidos em título/atributo.
- Retornar projeções mínimas de objetos externos. Nenhum dado pessoal de comprador é necessário aos relatórios da V1.
- Mensagens de erro devem ajudar a corrigir o problema sem expor payload sensível.
- Não compartilhar o mesmo registro de tokens entre Hermes pessoal e empresarial. Instalações/perfis independentes exigem autorização e cofre separados; simultaneidade multiambiente não faz parte da V1.

## 14. Configuração e operação local

### Variáveis propostas

| Nome | Obrigatoriedade / padrão | Observação |
| --- | --- | --- |
| `ML_CLIENT_ID` | Obrigatória para OAuth | Identificador da aplicação |
| `ML_CLIENT_SECRET` | Obrigatória para OAuth | Segredo local, nunca parâmetro MCP |
| `ML_REDIRECT_URI` | Obrigatória para OAuth | URI HTTPS exata aprovada no portal |
| `ML_PKCE_ENABLED` | Deve refletir configuração real | Se habilitado no portal, não permitir fluxo sem PKCE |
| `ML_CREDENTIAL_PROFILE` | `default` | Namespace local do cofre e lock; não é seletor livre de vendedor |
| `ML_CALLBACK_BIND_HOST` | Loopback | Não expor em interfaces públicas |
| `ML_CALLBACK_PORT` | Definida junto à Redirect URI | Não inventar porta já registrada |
| `ML_CALLBACK_CERT_FILE` | Obrigatória para HTTPS local | Caminho absoluto do certificado |
| `ML_CALLBACK_KEY_FILE` | Obrigatória para HTTPS local | Caminho absoluto protegido da chave privada |
| `BUSINESS_TIMEZONE` | `America/Sao_Paulo` | Validar com `zoneinfo` |
| `LOG_LEVEL` | `INFO` | Logs em stderr |
| `HTTP_CONNECT_TIMEOUT_SECONDS` | `5` | Número positivo com faixa segura |
| `HTTP_READ_TIMEOUT_SECONDS` | `30` | Número positivo com faixa segura |
| `MAX_ANALYSIS_REQUESTS` | `500` | Orçamento por agregação/comparação |
| `MAX_ANALYSIS_SECONDS` | `180` | Deve ser compatível com timeout do Hermes |

A configuração MCP deve apontar para o Python absoluto da `.venv` e executar `-m src.server` na raiz. O carregamento de `.env` deve ser relativo ao projeto, evitando depender acidentalmente do diretório do Hermes. Se o Hermes não suportar diretório de trabalho, usar o mecanismo documentado da versão instalada; não inventar chaves de configuração.

Comandos previstos para o README, a validar na implementação:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.server
```

Como alternativa à ativação bloqueada por política local do PowerShell, usar diretamente `.\.venv\Scripts\python.exe`; não recomendar relaxamento amplo de segurança do Windows. A execução manual do servidor stdio pode aguardar mensagens sem imprimir uma interface; isso é esperado.

O processo deve iniciar com ferramentas descobríveis mesmo sem credenciais. Chamadas comerciais retornam `AUTH_REQUIRED`; OAuth sem configuração retorna `CONFIGURATION_ERROR` com nomes de campos faltantes, sem seus valores. Fechar o Hermes deve encerrar o subprocesso e liberar recursos.

## 15. Requisitos não funcionais e critérios globais de aceite

| ID | Requisito | Evidência de aceite |
| --- | --- | --- |
| RNF01 | Simplicidade | Somente módulos/dependências necessários; nenhuma infraestrutura excluída |
| RNF02 | Reprodutibilidade | Ambiente limpo Windows/Python 3.13 instala requirements e inicia servidor |
| RNF03 | Protocolo íntegro | Descoberta e chamada no Hermes sem saída indevida em stdout |
| RNF04 | Segurança | Revisão manual de versionáveis, logs e respostas não encontra segredos |
| RNF05 | Robustez | Falhas HTTP/OAuth têm limite de tentativas e erro acionável |
| RNF06 | Precisão | Aritmética Decimal, moeda explícita e reconciliação manual da amostra |
| RNF07 | Cobertura | Nenhuma primeira página é apresentada como agregado completo |
| RNF08 | Transparência | Dados parciais/ausentes, período aberto e critérios da métrica são explícitos |
| RNF09 | Desempenho limitado | Orçamentos de chamadas/tempo respeitados; sem promessa de latência da API |
| RNF10 | Manutenção | Tipagem, docstrings úteis e responsabilidades sem imports circulares |
| RNF11 | Escopo | Exatamente oito ferramentas e nenhuma operação comercial de escrita |

Sem testes automatizados por decisão expressa de escopo. Verificações manuais são obrigatórias e devem registrar o que foi efetivamente observado. A ausência de automação reduz a proteção contra regressões; alterações posteriores precisam repetir as verificações manuais afetadas.

## 16. Plano de desenvolvimento por sprints

### 16.1 Organização do trabalho

As sprints são incrementos de escopo, sem duração fixa imposta. Para um desenvolvedor trabalhando com auxílio do Hermes, é preferível fechar cada entrega e registrar sua validação antes de iniciar funcionalidades dependentes. Estimar calendário somente após inspeção do repositório, confirmação das dependências externas e disponibilidade diária do desenvolvedor.

Cada tarefa deve ser pequena o suficiente para produzir uma alteração verificável. Se não couber em uma sessão de trabalho, dividi-la em subtarefas, mantendo o ID original como referência. Não criar tarefas de código sem necessidade apenas para preencher uma sprint.

| Sprint | Entrega | Dependência | Relação com as etapas do escopo original |
| --- | --- | --- | --- |
| 0 | Viabilidade, escopo e documentação técnica confirmados | Nenhuma | Etapa 1 — inspeção e planejamento |
| 1 | Ambiente, contratos e servidor mínimo | Sprint 0; fundação pode avançar com credenciais pendentes | Etapa 2 — fundação |
| 2 | Autenticação e persistência segura | Sprint 1 + viabilidade de callback | Etapa 3 — autenticação |
| 3 | Perfil e consulta de pedidos | Sprint 2 para validação real | Início da Etapa 4 — ferramentas |
| 4 | Anúncios, detalhes e visitas | Sprint 3 | Continuação da Etapa 4 |
| 5 | Resumo e comparação de vendas | Sprints 3 e 4 | Conclusão da Etapa 4 |
| 6 | Integração com Hermes e entrega da V1 | Sprints anteriores | Etapa 5 — integração e documentação |

### Sprint 0 — Inspeção, documentação e viabilidade

**Objetivo:** eliminar decisões bloqueantes antes da implementação. **Entregável:** PRD revisado, tabela de endpoints e registro de pendências no próprio PRD/README.

- [ ] S0.01 — Listar os arquivos existentes na raiz e identificar se há código, configuração ou repositório Git.
- [ ] S0.02 — Ler README e orientações locais existentes; registrar o que pode ser reaproveitado sem sobrescrever trabalho válido.
- [ ] S0.03 — Conferir o escopo com este PRD: oito ferramentas, leitura comercial e ausência de infraestrutura adicional.
- [ ] S0.04 — Consultar documentação oficial de OAuth e registrar campos, URI, PKCE, expiração e rotação aplicáveis.
- [ ] S0.05 — Confirmar criação/acesso à aplicação e listar permissões mínimas oferecidas pelo portal, sem copiar segredos.
- [ ] S0.06 — Confirmar requisitos atuais para Redirect URI HTTPS e validar se uma URI com receptor local é aceita pela aplicação.
- [ ] S0.07 — Definir host, porta, resolução local e certificado confiável para o callback; registrar o procedimento de configuração.
- [ ] S0.08 — Se a solução local não for aceita, registrar D02 como bloqueada e descrever a menor alteração necessária; não instalar infraestrutura externa automaticamente.
- [ ] S0.09 — Confirmar rotas de perfil e pedidos, formato das datas, estados retornados e eventuais exclusões padrão de cancelamentos.
- [ ] S0.10 — Confirmar limites de paginação de pedidos e granularidade mínima para particionar períodos completos.
- [ ] S0.11 — Confirmar busca de itens, scan, validade de cursor e formato atual de `/items/bulk`.
- [ ] S0.12 — Confirmar extensão, antiguidade e semântica dos intervalos de visitas; registrar os limites sem inferir retenção inexistente.
- [ ] S0.13 — Consultar documentação FastMCP para Python suportado, `stdio`, ferramentas síncronas e saídas estruturadas.
- [ ] S0.14 — Identificar a versão instalada do Hermes e sua configuração oficial para subprocesso MCP local.
- [ ] S0.15 — Registrar decisões D01–D05, fontes e pendências; revisar qualquer diferença entre documentação atual e este PRD.
- [ ] S0.ACEITE — Revisar a entrega: nenhuma rota foi inventada e cada bloqueio externo tem responsável e próximo passo registrado.
- [ ] S0.CONCLUSAO — Marcar a sprint concluída somente após cumprir o aceite; pendências de credenciais podem permanecer identificadas, mas viabilidade de callback deve estar decidida ou formalmente bloqueada.

### Sprint 1 — Fundação, contratos e servidor mínimo

**Objetivo:** estabelecer ambiente reproduzível e base utilizável sem a conta. **Entregável:** servidor mínimo, cliente HTTP básico, schemas e configuração.

- [ ] S1.01 — Confirmar instalação do Python 3.13 e funcionamento de SSL no Windows alvo.
- [ ] S1.02 — Criar `.venv` na raiz sem alterar ambientes de outros projetos.
- [ ] S1.03 — Instalar somente FastMCP, requests, Pydantic, python-dotenv, keyring e tzdata, com transitivas necessárias.
- [ ] S1.04 — Registrar versões verificadas em `requirements.txt`; confirmar instalação reproduzível em ambiente limpo.
- [ ] S1.05 — Criar a estrutura mínima `src` com os módulos que serão efetivamente implementados, sem arquivos arquiteturais adicionais vazios.
- [ ] S1.06 — Preparar `.gitignore` para `.env`, `.venv`, caches, runtime e material sensível do callback.
- [ ] S1.07 — Criar `.env.example` com nomes documentados e placeholders, sem dados de conta.
- [ ] S1.08 — Implementar carregamento de configuração pela raiz do projeto e validação de fuso, limites e campos locais.
- [ ] S1.09 — Definir `Money`, `Period`, `ToolError`, `Warning`, `Pagination`, `Metadata` e envelope de resposta.
- [ ] S1.10 — Implementar validação de datas inclusivas, limites, IDs e serialização de valores Decimal.
- [ ] S1.11 — Configurar logging em stderr com remoção de segredos e identificador local de requisição.
- [ ] S1.12 — Criar a composição do FastMCP em `server.py`, sem import circular e sem chamada de rede durante import.
- [ ] S1.13 — Implementar `requests.Session` central com TLS, host fixo e timeouts configuráveis.
- [ ] S1.14 — Implementar allowlist de métodos/rotas e bloqueio de redirects autenticados.
- [ ] S1.15 — Preparar o ciclo de vida para fechar sessão e liberar recursos no encerramento.
- [ ] S1.16 — Iniciar o servidor manualmente em stdio e confirmar que logs não contaminam stdout.
- [ ] S1.17 — Documentar comandos de ambiente e dependências no README; não registrar ferramentas comerciais fictícias para simular funcionamento.
- [ ] S1.ACEITE — Verificar instalação limpa, inicialização, configuração inválida e serialização monetária com exemplos locais claramente sintéticos.
- [ ] S1.CONCLUSAO — Marcar a sprint concluída quando a base estiver executável e os resultados das verificações estiverem registrados.

### Sprint 2 — OAuth, callback e ciclo de vida dos tokens

**Objetivo:** conectar com segurança e manter autorização. **Entregável:** `auth.py` funcional e ferramenta `start_oauth` registrada.

- [ ] S2.01 — Implementar identificação do perfil local por aplicação e namespace de credenciais.
- [ ] S2.02 — Implementar lock exclusivo entre processos para o perfil; retornar erro seguro se outro processo estiver ativo.
- [ ] S2.03 — Detectar o backend do keyring e rejeitar backends inseguros, nulos ou inacessíveis.
- [ ] S2.04 — Definir o registro único de tokens e metadados no cofre; não criar persistência plaintext.
- [ ] S2.05 — Implementar geração aleatória de `state`, expiração interna e controle de uma autorização pendente.
- [ ] S2.06 — Implementar `code_verifier` e challenge S256 quando PKCE estiver habilitado/exigido.
- [ ] S2.07 — Montar URL oficial do Brasil com a Redirect URI exatamente configurada.
- [ ] S2.08 — Implementar receptor HTTPS local restrito à rota OAuth e ao loopback, com certificado configurado.
- [ ] S2.09 — Desabilitar logs de URL do callback e rejeitar entradas grandes, caminhos inesperados e callbacks repetidos.
- [ ] S2.10 — Validar `state`, expiração e erros de consentimento antes de usar o código.
- [ ] S2.11 — Implementar troca do código com POST form encoded, sem retry automático de resultado incerto.
- [ ] S2.12 — Validar resposta de tokens e confirmar identidade autenticada antes de persistir/concluir conexão.
- [ ] S2.13 — Persistir o conjunto completo no cofre; tratar falha de gravação como falha de autenticação.
- [ ] S2.14 — Implementar checagem de expiração por `expires_in` com margem de 60 segundos.
- [ ] S2.15 — Implementar renovação sob lock, relendo a credencial e substituindo o refresh token retornado.
- [ ] S2.16 — Implementar tratamento de revogação, `invalid_grant` e timeout após envio sem reapresentar token de uso único.
- [ ] S2.17 — Registrar `start_oauth` com retorno rápido, abertura opcional de navegador e consulta do estado por nova chamada.
- [ ] S2.18 — Encerrar listener e limpar dados temporários após sucesso, recusa, erro ou expiração.
- [ ] S2.19 — Documentar desconexão local, remoção do cofre e nova autorização sem exibir valores secretos.
- [ ] S2.20 — Executar manualmente: callback com state incorreto, autorização recusada, expirada e chamada repetida enquanto pendente.
- [ ] S2.21 — Com credenciais disponíveis, executar autorização real, reiniciar o processo e comprovar recuperação da conexão pelo cofre.
- [ ] S2.22 — Com autorização válida, observar renovação controlada e confirmar que uma segunda execução é impedida pelo lock.
- [ ] S2.ACEITE — Comprovar fluxo completo e nenhum segredo em saída/log; se a conta não foi autorizada, registrar a implementação como pendente de validação real.
- [ ] S2.CONCLUSAO — Marcar a sprint concluída somente quando o aceite tiver evidência; sem autorização real, manter os itens correspondentes abertos.

### Sprint 3 — Perfil, pedidos e resiliência HTTP

**Objetivo:** estabelecer identidade e população comercial confiável. **Entregável:** RF01/RF02 e cliente HTTP com políticas de erro/paginação.

- [ ] S3.01 — Implementar GET autenticado usando credenciais internas, sem parâmetro de token nas ferramentas.
- [ ] S3.02 — Implementar política limitada de retries para GETs e contagem de tentativas.
- [ ] S3.03 — Implementar backoff com jitter e respeito a `Retry-After` dentro do orçamento.
- [ ] S3.04 — Implementar uma renovação por 401 e um replay do GET; impedir loop infinito.
- [ ] S3.05 — Mapear 403, 404, 429, 5xx, timeout e JSON inválido para erros seguros.
- [ ] S3.06 — Implementar `get_seller_profile` com projeção mínima de campos e guardar identidade validada.
- [ ] S3.07 — Implementar modelos `Order` e `OrderLine`, preservando dinheiro decimal e campos essenciais.
- [ ] S3.08 — Mapear datas públicas aos filtros de criação; implementar filtro local para fronteiras temporais.
- [ ] S3.09 — Implementar `list_orders` com seller interno, status validado, limit/offset e próxima página explícita.
- [ ] S3.10 — Projetar a saída de pedidos sem dados de comprador e sem pagamentos brutos completos.
- [ ] S3.11 — Implementar coletor interno de pedidos com deduplicação e detecção de páginas sem progresso.
- [ ] S3.12 — Implementar particionamento temporal quando o limite oficial impedir paginação integral.
- [ ] S3.13 — Tratar exclusões padrão da busca; consultar cancelados separadamente quando exigido e suportado, evitando dupla contagem.
- [ ] S3.14 — Se campos essenciais estiverem ausentes na busca, usar detalhe interno documentado apenas nos pedidos necessários.
- [ ] S3.15 — Aplicar orçamento de chamadas/tempo e retornar incompletude quando não puder concluir a população.
- [ ] S3.16 — Conferir manualmente uma página, sua continuação e as fronteiras de dias no fuso da empresa.
- [ ] S3.17 — Conferir amostra com pedidos pagos e outros estados reais disponíveis; registrar os casos não observáveis.
- [ ] S3.18 — Verificar sem credenciais que as chamadas comerciais devolvem `AUTH_REQUIRED` e sem acesso retornam erro seguro.
- [ ] S3.ACEITE — Demonstrar identidade correta, paginação explícita, proteção de compradores e distinção entre pedido criado e pago.
- [ ] S3.CONCLUSAO — Marcar a sprint concluída após registrar evidências reais e limites de cobertura de pedidos.

### Sprint 4 — Anúncios, detalhes e visitas

**Objetivo:** fornecer catálogo da conta e tráfego verificável. **Entregável:** RF03, RF04 e RF05.

- [ ] S4.01 — Implementar modelos mínimos de anúncio, detalhe, quantidade e visitas.
- [ ] S4.02 — Implementar busca de IDs pelo vendedor interno e filtro explícito de status.
- [ ] S4.03 — Implementar modo convencional de paginação somente dentro dos limites oficiais.
- [ ] S4.04 — Implementar scan sem offset, propagação correta de cursor e detecção de expiração.
- [ ] S4.05 — Implementar enriquecimento de IDs com `/items/bulk`, conforme novo formato e tamanho oficial do lote.
- [ ] S4.06 — Interpretar `status_code` por elemento e preservar IDs cujo detalhe falhou.
- [ ] S4.07 — Registrar `list_seller_items` com título/preço disponíveis, metadados e próxima página.
- [ ] S4.08 — Implementar consulta singular e registro de `get_item_details`.
- [ ] S4.09 — Validar propriedade por `seller_id` antes de expor detalhes ou usar o anúncio em visitas.
- [ ] S4.10 — Classificar precisão da quantidade como exata, referencial ou desconhecida conforme a origem.
- [ ] S4.11 — Projetar atributos e variações relevantes sem ultrapassar o limite de resposta.
- [ ] S4.12 — Implementar entrada exclusiva de `item_id`/`item_ids`, remoção controlada de duplicados e limites de lote.
- [ ] S4.13 — Implementar consulta de visitas com período efetivo, validação de janela e indisponibilidade explícita.
- [ ] S4.14 — Normalizar respostas de um e vários IDs e tratar falha individual sem atribuir zero.
- [ ] S4.15 — Registrar `get_item_visits` com saída estruturada e advertências temporais.
- [ ] S4.16 — Conferir manualmente anúncios ativos e pausados com a conta real e navegar para uma página/cursor seguinte.
- [ ] S4.17 — Conferir detalhe, preço e disponibilidade de uma amostra real; não atribuir precisão de estoque sem prova.
- [ ] S4.18 — Conferir visitas de um anúncio e de um lote; registrar limites reais e casos de dados ausentes.
- [ ] S4.19 — Verificar entrada inválida, cursor expirado quando reproduzível e bloqueio de anúncio de outra conta.
- [ ] S4.ACEITE — Demonstrar três ferramentas comerciais novas, propriedade validada e tratamento de erros parciais sem truncamento silencioso.
- [ ] S4.CONCLUSAO — Marcar a sprint concluída após registrar validações e atualizar a tabela de endpoints efetivamente usados.

### Sprint 5 — Resumo e comparação de vendas

**Objetivo:** produzir métricas consistentes e comparáveis. **Entregável:** RF06/RF07 com metodologia documentada.

- [ ] S5.01 — Implementar classificador de pedidos elegíveis, cancelados, parcialmente pagos e exceções de reembolso.
- [ ] S5.02 — Implementar agregação Decimal das linhas transacionais, sem usar preço atual do anúncio.
- [ ] S5.03 — Implementar contagem de IDs únicos e unidades, mantendo `pack_id` sem substituir `order_id`.
- [ ] S5.04 — Separar métricas por moeda e impedir soma entre moedas.
- [ ] S5.05 — Calcular ticket médio com os mesmos pedidos elegíveis e tratamento de denominador zero.
- [ ] S5.06 — Invalidar métricas afetadas por linhas essenciais ausentes, preservando contagens de diagnóstico.
- [ ] S5.07 — Agregar todo o universo por ID de anúncio antes de limitar rankings.
- [ ] S5.08 — Implementar rankings por unidades e por faturamento, com desempate determinístico.
- [ ] S5.09 — Registrar `get_sales_summary`, metodologia, cobertura e contagens de cancelamento/reembolso disponíveis.
- [ ] S5.10 — Aplicar regra de parcialidade: totais definitivos nulos e observados claramente separados.
- [ ] S5.11 — Implementar agregação reutilizável para dois períodos, sem chamar a função MCP decorada internamente.
- [ ] S5.12 — Unir todos os IDs dos períodos A/B, incluindo os ausentes em um deles somente com coleta completa.
- [ ] S5.13 — Calcular diferenças absolutas/percentuais de faturamento, pedidos, unidades e ticket.
- [ ] S5.14 — Tratar base zero, ausência de pedidos, moedas não coincidentes e métrica indisponível.
- [ ] S5.15 — Calcular dias inclusivos, médias diárias e alertas de duração diferente ou sobreposição.
- [ ] S5.16 — Ordenar maiores quedas/crescimentos por delta absoluto; aplicar `top_n` somente ao final.
- [ ] S5.17 — Registrar `get_sales_comparison` e impedir comparação definitiva se uma coleta estiver incompleta.
- [ ] S5.18 — Reconciliar manualmente uma amostra real: linhas, unidades, IDs, total calculado e ticket.
- [ ] S5.19 — Conferir manualmente, com cálculos sintéticos identificados como tal, os casos base zero, −100%, moedas distintas e períodos de durações diferentes.
- [ ] S5.20 — Conferir que mudar `top_n` não muda totais e que anúncio ausente do top N ainda pode aparecer entre maiores quedas.
- [ ] S5.21 — Verificar orçamento insuficiente com limite local reduzido, confirmando `PARTIAL_DATA` sem total definitivo.
- [ ] S5.22 — Documentar a diferença entre coorte de criação e fluxo de pagamentos no README e nas descrições relevantes.
- [ ] S5.ACEITE — Demonstrar totais rastreáveis, rankings sobre a população completa e comparação sem percentuais inválidos.
- [ ] S5.CONCLUSAO — Marcar a sprint concluída quando os cálculos e suas limitações estiverem comprovados e registrados.

### Sprint 6 — Integração com Hermes, revisão e entrega

**Objetivo:** tornar a V1 utilizável por outra pessoa no ambiente alvo. **Entregável:** projeto documentado, oito ferramentas descobertas e evidências de validação.

- [ ] S6.01 — Revisar nomes e confirmar exatamente sete ferramentas comerciais mais `start_oauth`.
- [ ] S6.02 — Revisar descrições, schemas, defaults e anotações MCP sem alegar ausência de efeitos locais no OAuth.
- [ ] S6.03 — Registrar a configuração real do Hermes com Python absoluto, argumentos e diretório comprovados.
- [ ] S6.04 — Configurar/iniciar pelo Hermes e confirmar descoberta das oito ferramentas.
- [ ] S6.05 — Executar jornada de conexão pelo Hermes sem senha ou token enviado ao modelo.
- [ ] S6.06 — Executar jornada de consulta de pedidos e navegação explícita para a próxima página.
- [ ] S6.07 — Executar comparação de dois períodos equivalentes, selecionar anúncios e consultar detalhes/visitas.
- [ ] S6.08 — Executar jornada de anúncios com visitas e nenhuma venda usando o catálogo, sem limitar a seleção aos mais vendidos.
- [ ] S6.09 — Ajustar timeouts do cliente Hermes conforme documentação, garantindo compatibilidade com o orçamento de análise.
- [ ] S6.10 — Confirmar que todas as chamadas comerciais são GET e que o único POST de negócio externo é o token OAuth.
- [ ] S6.11 — Revisar arquivos versionáveis, logs e respostas à procura de credenciais e dados pessoais desnecessários.
- [ ] S6.12 — Conferir ausência de testes automatizados, frameworks e componentes fora do escopo.
- [ ] S6.13 — Atualizar README com instalação Windows, configuração local, aplicação Developers, callback, OAuth e Hermes.
- [ ] S6.14 — Acrescentar solução de problemas para SSL, venv, falta de credenciais, cofre, 401/403/429 e callback HTTPS.
- [ ] S6.15 — Atualizar `requirements.txt`, tabela de endpoints e limitações com base na implementação final.
- [ ] S6.16 — Registrar cada verificação realizada e identificar o que permaneceu não verificado ou bloqueado.
- [ ] S6.17 — Reiniciar Hermes/processo e confirmar recuperação segura de conexão e liberação de locks ao encerrar.
- [ ] S6.18 — Preparar resumo da V1 e backlog de observação; não realizar commit/push sem instrução do usuário.
- [ ] S6.ACEITE — Demonstrar uso real das oito ferramentas e critérios globais, ou declarar claramente entrega técnica ainda pendente de validação da conta.
- [ ] S6.CONCLUSAO — Marcar a sprint concluída somente com aceite e documentação final coerentes.

### 16.2 Definição de pronto de cada tarefa

- [ ] Alteração restrita ao escopo e compatível com decisões/fonte oficial aplicáveis.
- [ ] Código legível e tipado, com tratamento de falhas relevantes e sem abstrações desnecessárias.
- [ ] Verificação manual pertinente executada, ou bloqueio externo registrado sem marcar a tarefa como validada.
- [ ] Mudança de comportamento e motivo técnico relevante explicados no registro da entrega.
- [ ] PRD/README/requirements atualizados quando afetados.
- [ ] Nenhum segredo, dado pessoal desnecessário ou afirmação de sucesso sem evidência.

## 17. Plano de verificação manual e evidências

Registrar os resultados no README, sem criar uma suíte automatizada. Usar uma tabela com: ID, data/hora, versão do código ou referência local, ambiente, procedimento, resultado esperado, resultado observado e situação. Evidências devem ser texto sanitizado e contagens; não salvar payload bruto contendo dados pessoais ou tokens.

| ID | Cenário | Resultado esperado |
| --- | --- | --- |
| VM01 | Iniciar sem credenciais | MCP descobrível; comerciais retornam `AUTH_REQUIRED`; OAuth explica configuração faltante |
| VM02 | Descobrir ferramentas pelo Hermes | Exatamente os oito nomes deste PRD, schemas e descrições válidos |
| VM03 | Autorizar conta real e reiniciar | Identidade correta; tokens recuperados do cofre sem vazamento |
| VM04 | Callback com state errado/expirado | Rejeição sem troca indevida do código |
| VM05 | Renovação e segundo processo | Renovação única e persistida; processo concorrente bloqueado |
| VM06 | Pedidos em mais de uma página | Continuação explícita e IDs sem duplicação no agregado |
| VM07 | Fronteira temporal e período atual | Dia final incluído corretamente; hoje sinalizado como período aberto |
| VM08 | Amostra paga/cancelada/reembolsada | Classificação coerente com metodologia; ausências não são tratadas como zero |
| VM09 | Anúncios ativos/pausados e bulk | Filtros coerentes, continuação e falhas por ID preservadas |
| VM10 | Detalhe de anúncio de outra conta | Recusa por propriedade antes de expor dados comerciais |
| VM11 | Visitas disponíveis e indisponíveis | Período efetivo explícito; visitas ausentes são `null` |
| VM12 | Reconciliação monetária | Soma das linhas elegíveis e dos anúncios coincide com total calculado |
| VM13 | Base zero e períodos diferentes | Percentual nulo quando necessário; durações/médias explícitas |
| VM14 | Coleta interrompida por limite interno | `PARTIAL_DATA`, metadados de cobertura e nenhum total definitivo |
| VM15 | HTTP 401/403/429/5xx quando reproduzível | Política limitada e erro seguro; não induzir carga ou indisponibilidade na API |
| VM16 | Revisão de segurança e stdio | Ausência de segredos/PII e logs somente em stderr |
| VM17 | Jornada comercial completa no Hermes | Recomendações apoiadas em dados consultados e ressalvas preservadas |

Não provocar 429 ou falhas de produção deliberadamente para obter evidência. Casos indisponíveis podem ser revisados manualmente no código ou exercitados localmente de forma controlada, sempre identificando o método utilizado. Revisão de código não deve ser registrada como observação real do comportamento da API. Cálculos sintéticos não são dados comerciais reais.

## 18. Riscos, limitações e respostas previstas

| Risco | Efeito | Tratamento mínimo |
| --- | --- | --- |
| Callback local incompatível com regras do portal | OAuth não conclui no desenho local | Resolver D02 na Sprint 0; registrar bloqueio e mudança mínima necessária |
| Aplicação sem permissão ou conta com restrição | Recursos retornam 403 ou faltam dados | Documentar permissão real; não tratar como falha transitória genérica |
| Mudança de endpoint/formato | Parser desatualizado | Usar bulk atual; revisar documentação antes de implementar e registrar data |
| Token rotativo consumido em timeout/crash | Sessão perdida | Exclusão mútua, persistência imediata e reautorização em resultado incerto |
| Histórico/visitas fora da disponibilidade | Análise de três meses fica incompleta | Explicitar cobertura; não extrapolar nem alegar retenção resolvida por lotes |
| Volume maior que orçamento local | Agregados não concluem | Particionar janelas quando permitido e recomendar consulta menor |
| Mudanças de estado durante leitura | Resultado histórico muda e paginação pode variar | Registrar instante, deduplicar, avisar falta de snapshot e repetir quando necessário |
| Estado atual do pedido e reembolsos | Diferença em relação ao painel financeiro | Metodologia conservadora explícita e sem promessa de receita líquida |
| Estado/estoque apenas atual | Hipóteses causais sobre passado ficam frágeis | Não afirmar causa de queda sem evidência temporal |
| Ausência de testes automatizados | Regressões podem passar despercebidas | Verificações manuais pertinentes a cada alteração |
| Hermes com configuração diferente | Integração não inicia | Confirmar versão e sintaxe; evitar exemplos de configuração presumidos |
| Cofre sob outro usuário Windows | Tokens inacessíveis | Executar Hermes e configuração no mesmo usuário; não copiar segredos em arquivos |

## 19. Aceite final e estados da entrega

### Entrega técnica implementada

- [ ] AF01 — Estrutura mínima e responsabilidades respeitadas.
- [ ] AF02 — Ambiente Windows/Python documentado e reproduzível.
- [ ] AF03 — Servidor inicia por stdio com stdout preservado.
- [ ] AF04 — Oito ferramentas corretas registradas, sem ferramentas comerciais adicionais.
- [ ] AF05 — OAuth completo com callback, state, PKCE aplicável e cofre protegido.
- [ ] AF06 — Renovação rotativa, concorrência e resultado incerto tratados.
- [ ] AF07 — Cliente HTTP central com TLS, timeout, paginação e erros limitados.
- [ ] AF08 — Somente rotas oficiais atuais, propriedade de anúncios e seller interno.
- [ ] AF09 — Cálculos Decimal e metodologia comercial implementados.
- [ ] AF10 — Cobertura, período aberto, ausência de dados e percentuais indefinidos tratados.
- [ ] AF11 — README, PRD e requirements coerentes com a implementação.
- [ ] AF12 — Nenhum componente proibido, teste automatizado ou segredo versionável.

### Validação real e liberação para uso

- [ ] AV01 — Aplicação configurada e conta real autorizada.
- [ ] AV02 — Perfil da conta conferido pelo responsável da operação.
- [ ] AV03 — Pedidos, anúncios e visitas consultados com cobertura registrada.
- [ ] AV04 — Resumo e comparação reconciliados em amostra de dados reais.
- [ ] AV05 — Descoberta e uso das oito ferramentas verificados no Hermes.
- [ ] AV06 — Instalação limpa, reinício e retomada segura de conexão comprovados.
- [ ] AV07 — Evidências manuais e limitações entregues sem segredos.
- [ ] AV08 — Gestor recebeu orientação para interpretar metodologia e resultados parciais.

Estados permitidos no relatório de entrega: **planejado**, **em implementação**, **implementado — pendente de configuração**, **implementado — pendente de validação real** e **V1 validada para uso local**. Não utilizar “V1 concluída” quando somente a estrutura ou o código sem conta real foram verificados.

## 20. Operação assistida e evolução para V2

Após liberar a V1, observar o uso durante um período definido pelo gestor, sem automação de coleta adicional. Registrar apenas problemas e oportunidades úteis: consultas solicitadas, limitações de período/volume, qualidade das métricas, falhas OAuth, tempo de análise e recomendações que precisaram de dados não disponíveis.

### Checklist de observação

- [ ] O01 — Definir responsável e duração do período de observação.
- [ ] O02 — Registrar exemplos reais de perguntas atendidas e lacunas, sem dados sensíveis desnecessários.
- [ ] O03 — Registrar divergências entre painel e MCP e verificar primeiro as metodologias.
- [ ] O04 — Registrar quantas consultas atingem limites ou retornam dados parciais.
- [ ] O05 — Priorizar correções da V1 antes de ampliar autonomia.
- [ ] O06 — Elaborar proposta de V2 a partir das evidências e decidir seu escopo separadamente.

Possibilidades futuras, **sem implementação nesta versão**: integração NetOne, histórico local para análises temporais, custos e margem, consultas adicionais e ações de criação/edição com autorização explícita, trilha de auditoria e limites por operação. A V2 não deve herdar permissão implícita para escrita apenas por usar a mesma credencial OAuth.

## 21. Referências e grau de verificação

Consulta documental realizada em **22/10/2026**. Este PRD combina requisitos do arquivo fornecido com decisões de projeto. Não houve acesso ao repositório do projeto, configuração do Hermes, aplicativo Developers ou conta de vendedor. Nenhuma chamada autenticada foi executada.

Parte das páginas oficiais do Mercado Livre retornou HTTP 403 na leitura direta. Foi possível consultar conteúdo indexado de páginas oficiais para autenticação, pedidos, itens/bulk e visitas. Portanto, endpoints e mudanças identificadas estão fundamentados nessas fontes, mas limites e permissões específicos devem ser reconfirmados durante a Sprint 0. Falha de acesso à documentação não deve ser confundida com falha da API comercial.

| Ref. | Fonte oficial | Uso no planejamento |
| --- | --- | --- |
| S01 | [Mercado Livre — Autenticação e Autorização](https://developers.mercadolivre.com.br/autenticacao-e-autorizacao) e [versão oficial em inglês](https://developers.mercadolivre.com.br/en_us/authentication-and-authorization) | Authorization Code, PKCE, token e rotação; conteúdo indexado consultado |
| S02 | [Mercado Livre — Configuração ou requisitos prévios](https://developers.mercadolivre.com.br/pt_br/lojas-oficiais/configuracao-ou-requisitos-previos) | Consulta `/users/me`; conteúdo indexado consultado |
| S03 | [Mercado Livre — Orders](https://developers.mercadolivre.com.br/pt_br/gerenciamento-de-vendas/gerenciamento-de-vendas) | Busca, filtros de criação, estados, granularidade e disponibilidade; conteúdo indexado consultado |
| S04 | [Mercado Livre — Busca de itens](https://developers.mercadolivre.com.br/pt_br/itens-e-buscas) | Busca própria, scan e migração bulk; conteúdo indexado com atualização de 31/08/2026 consultado |
| S05 | [Mercado Livre — Visitas](https://developers.mercadolivre.com.br/pt_br/como-comecar/recurso-visits) | Visitas por intervalo e limites temporais; conteúdo indexado com atualização de 02/01/2026 consultado |
| S06 | [Mercado Livre — Desenvolvimento in-house](https://developers.mercadolivre.com.br/pt_br/autenticacao-e-autorizacao/desenvolvimento-in-house) | Redirect URI HTTPS exata, mínimos de integração e segurança; conteúdo indexado consultado |
| S07 | [FastMCP — Tools](https://gofastmcp.com/servers/tools) e [Running your server](https://gofastmcp.com/deployment/running-server) | Ferramentas síncronas, estruturas de retorno e execução stdio |
| S08 | [Requests — Advanced Usage](https://requests.readthedocs.io/en/latest/user/advanced/) | Sessão reutilizável e uso de recursos HTTP |
| S09 | [Pydantic — Serialization](https://docs.pydantic.dev/latest/concepts/serialization/) | Serialização de contratos estruturados |
| S10 | [keyring — Documentação oficial](https://keyring.readthedocs.io/en/latest/) | Armazenamento em serviço de credenciais do sistema |
| S11 | [Python — zoneinfo](https://docs.python.org/3/library/zoneinfo.html) | Fuso IANA e dependência tzdata para ambientes sem base do sistema |

Os limites internos de 20/50 registros, 20 IDs, 120 dias, 500 GETs, 180 segundos, 5 minutos OAuth, timeouts e 256 KiB são decisões deste PRD. Não foram apresentados como limites oficiais da plataforma. A metodologia `created_paid_v1` também é uma decisão do produto, sujeita a revisão explícita antes de mudar o significado das métricas.

