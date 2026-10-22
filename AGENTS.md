# mercadolivre-mcp

MCP local para o Hermes analisar a conta Mercado Livre da Dias Moto Peças. `PRD.md` é a fonte de requisitos; §§23–25 registram o recorte OAuth, Sprint 0 com ressalvas e Sprint 1 validada localmente sem conta. Há `src/auth.py`, `client.py`, `schemas.py`, `server.py`, `__init__.py` e requirements completos. Servidor FastMCP stdio mínimo inicia, mas ainda registra zero ferramentas reais; `tools.py` não existe. Check/TLS padrão passaram; Felipe confirmou navegador sem aviso. Grant/API reais pendentes. Não iniciar Sprint 2 sem autorização separada.

## Escopo e execução do trabalho

- Consultar `PRD.md` antes de implementar; seguir as sprints 0–6 e suas dependências (seção 16).
- V1: uma conta, leitura comercial, FastMCP via `stdio`, cálculos determinísticos em Python; nenhum LLM dentro do MCP.
- Exatamente oito ferramentas previstas: `get_seller_profile`, `list_orders`, `list_seller_items`, `get_item_details`, `get_item_visits`, `get_sales_summary`, `get_sales_comparison`, `start_oauth`.
- Não adicionar escrita comercial, Ads, NetOne, banco de dados, frontend, Docker, jobs ou ferramentas MCP extras.
- Testes automatizados, `pytest` e arquivos `test_*.py` estão expressamente fora da V1. A validação é manual.
- Não executar commits/pushes sem instrução expressa. Não marcar tarefas ou sprints como concluídas sem evidências; registrar bloqueios e validação real pendente.
- Encerramento aprovado da Sprint 0 não apagou S0.05/S0.10/S0.12: permissões/PKCE antes do grant na Sprint 2, teto de pedidos na Sprint 3 e retenção/fronteiras de visitas na Sprint 4. S0.08 foi resolvido como não aplicável; não inventar rejeição do callback.

## Ambiente e comandos

- Ambiente OAuth validado: `.venv-oauth`/CPython 3.13.15 no Windows. A `.venv` original 3.12.10 foi preservada; não usá-la inadvertidamente.
- `requirements.txt` fixa requests/Pydantic/python-dotenv/keyring/FastMCP/tzdata e transitivas exercitadas, com reinstalação limpa em Python 3.13.15. Não instalar LangChain.
- Comandos da CLI administrativa OAuth (PowerShell na raiz), com diagnósticos em stderr e sem tokens. `authorize` ainda bloqueia com configuração inválida ou TLS não confiável:

```powershell
.\.venv-oauth\Scripts\python.exe -m src.auth check
.\.venv-oauth\Scripts\python.exe -m src.auth tls-only --seconds 120
.\.venv-oauth\Scripts\python.exe -m src.auth authorize
.\.venv-oauth\Scripts\python.exe -m src.auth profile
```

- Sintaxe/imports exercitados: `.venv-oauth/Scripts/python.exe -m compileall -q src`; dependências: `uv pip check --python .venv-oauth/Scripts/python.exe`. Sem build/lint/suíte automatizada configurados.
- O recorte OAuth é CLI administrativa, não uma nona ferramenta. `python -m src.server` inicia stdio sem credenciais e sem ferramentas; handshake local foi exercitado, mas descoberta das oito no Hermes ainda não. Não simular ferramentas comerciais.

## Organização e contratos previstos

- `src/server.py`: composição, configuração pela raiz, logs e ciclo de vida; sem métricas.
- `src/client.py`: `requests.Session`, allowlist, timeouts, retries e paginação.
- `src/auth.py`: OAuth, callback, cofre, locks e renovação.
- `src/tools.py`: registro das oito ferramentas e cálculos compartilhados; receber a instância FastMCP por função de registro para evitar import circular.
- `src/schemas.py`: entradas/saídas Pydantic, erros, dinheiro e metadados. `src/__init__.py` não deve chamar a rede.
- Código observado: classes AuthConfig/AuthManager/WindowsVault/ProfileLock, erros DomainError com envelope seguro, SecretStr nos tokens, Session de origem fixa e locks; módulos futuros continuam especificação.
- Envelope: `success`, `data`, `period`, `metadata`, `warnings`, `error`. Erros de domínio/API usam esse contrato, sem traceback ao Hermes.
- IDs numéricos externos são strings; IDs de anúncio brasileiro seguem `MLB` + dígitos, com propriedade validada separadamente.
- Datas públicas `YYYY-MM-DD`, fim inclusivo convertido para intervalo interno semiaberto em `America/Sao_Paulo`.
- Dinheiro com `Decimal`, serializado como texto e moeda explícita; não somar moedas diferentes nem substituir dado ausente por zero.
- Metodologia `created_paid_v1`: coorte pela criação do pedido, elegibilidade pelo estado observado; preço transacional das linhas, nunca preço atual do anúncio. Aplicar as exceções de reembolso da seção 10.
- Agregados percorrem a população completa e deduplicam por `order_id`; `top_n` limita apenas rankings. Coleta incompleta exige `PARTIAL_DATA`, `success=false` e métricas definitivas nulas.

## Configuração e armadilhas

- Configuração OAuth pela raiz: ML_CLIENT_ID/ML_CLIENT_SECRET, com aliases explícitos CLIENT_ID/CLIENT_SECRET preexistentes; conflitos são erro. Não imprimir/editar `.env` nem normalizar IDs. O erro inicial de formato foi corrigido por Felipe; check real passou, sem comprovar grant ou credenciais aceitas pela API.
- URI cadastrada segundo Felipe e implementada: `https://127.0.0.1:8000/callback`. CA mkcert exclusiva autorizada/instalada em CurrentUser Root; CAROOT em `%LOCALAPPDATA%\DiasMoto\mercadolivre-mcp\ca`, certificado SAN IP ativo na subpasta `tls`, fora do OneDrive. Check/TLS/cadeia Windows passaram e Felipe confirmou diagnóstico no navegador; grant real não executado. Não compartilhar rootCA-key.pem nem instalar/remover outra CA. Nenhum grant automático após instalar certificado.
- Tokens ficam no cofre nativo do Windows via keyring, nunca JSON plaintext. Hermes e cofre devem usar o mesmo usuário; apenas um processo por perfil de credenciais.
- Refresh token rotativo não pode ser reapresentado automaticamente após timeout de resultado incerto. Proteger sessão/renovação com locks; não paralelizar chamadas comerciais.
- O marcador `refresh_in_flight` é persistido/readback antes da renovação; interrupção deixa perfil bloqueado para reautorização. Não removê-lo para tentar reutilizar refresh antigo.
- `stdout` é exclusivo do MCP; logs em `stderr`. Servidor stdio pode aguardar mensagens sem interface visível.
- Carregar `.env` pela raiz do projeto; a futura configuração Hermes deve usar Python absoluto da venv e `-m src.server`, sem presumir suporte a chaves de diretório de trabalho.
- API comercial fixa em `https://api.mercadolibre.com`, GETs permitidos por allowlist; POST somente para `/oauth/token`. TLS ativo e redirects autenticados desabilitados.
- O PRD prevê `/items/bulk` com `status_code` por elemento e seleção `body.<campo>`; reconfirmar documentação vigente antes de implementar, sem copiar parser do multiget antigo.
- A pesquisa da Sprint 0 confirmou `id` raiz no bulk e cursor de scan de 5 minutos; lote máximo do novo bulk permanece incerto. Os 20 resultados do Multiget legado não o comprovam.
- Visitas aceitam um ID por GET e intervalo de até 150 dias: a entrada MCP de até 20 IDs exige chamadas sequenciais. Retenção e fronteiras UTC/São Paulo ainda não estão resolvidas.
- Pedidos: filtros com precisão horária, histórico documentado até 12 meses e exclusão de cancelados na busca como seller; não presumir recuperação por filtro de status, ordenação por criação ou teto de offset não documentado.
- Scan de itens não usa offset e não se aplica a pedidos. Limites internos do PRD não são limites oficiais da API; reconfirmar retenção, permissões e paginação.
- Ao criar `.gitignore`, excluir `.env`, `.venv`, caches, runtime e material sensível do callback; `.env.example` contém somente placeholders. Não persistir respostas comerciais brutas.

## Verificação manual

- Usar os cenários VM01–VM17 da seção 17 e os aceites da sprint correspondente; não criar suíte automatizada.
- Registrar no README: ID, data/hora, referência do código, ambiente, procedimento, esperado, observado e situação; somente evidências sanitizadas.
- Distinguir revisão de código, exercício sintético e consulta real da API. Não provocar 429/falhas de produção para obter evidência.
- Sem conta autorizada, callback comprovado e jornadas reais no Hermes, não declarar “V1 validada para uso local”.
