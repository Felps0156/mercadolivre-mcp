# mercadolivre-mcp

MCP local de leitura comercial da conta Dias Moto Peças para o Hermes. O PRD é a fonte de requisitos. Estado em 22/10/2026: **Sprint 0 encerrada com ressalvas; Sprint 1 implementada e validada localmente sem conta**. O recorte OAuth administrativo continua pendente de grant/validação reais. O servidor FastMCP stdio existe, mas não registra ferramentas fictícias; as oito ferramentas reais pertencem às Sprints 2–5.

## Encerramento da Sprint 0

Felipe confirmou o diagnóstico no navegador sem aviso de certificado e autorizou o encerramento em 22/10/2026, registrado às 19:47 UTC−03. S0.07 concluído; S0.08 resolvido como **não aplicável**, pois o callback local foi aceito, sem caminho de rejeição ou infraestrutura externa. S0.CONCLUSAO marcado com a ressalva explícita registrada no PRD §24.

Permanecem abertos, sem alegação de confirmação: **S0.05** (permissões/PKCE no portal, antes do grant na Sprint 2), **S0.10** (limites de paginação, Sprint 3) e **S0.12** (retenção/fronteiras de visitas, Sprint 4). Responsáveis e condições constam no PRD §24; D03 também conserva a confirmação do lote do novo bulk. Isso não impede o encerramento administrativo aprovado, mas impede tratar esses contratos e a V1 como integralmente validados.

Não houve grant OAuth, renovação real ou consulta autenticada a `/users/me`. A Sprint 1 foi autorizada por pedido posterior de Felipe; essa autorização não inclui iniciar consentimento OAuth ou avançar à Sprint 2.

## Sprint 1 — fundação sem conta

Ambiente alvo: Windows 11, CPython 3.13.15; a `.venv` antiga 3.12 permanece intocada. A `.venv-oauth` existente foi ampliada para a fundação (FastMCP 4.1.3 e tzdata 2026.5); `requirements.txt` fixa as seis dependências diretas do PRD e suas transitivas exercitadas. Instalação reproduzível em PowerShell, na raiz, para quem ainda não possui o ambiente:

```powershell
uv venv .venv-oauth --python 3.13.15
uv pip install --python .venv-oauth\Scripts\python.exe -r requirements.txt
uv pip check --python .venv-oauth\Scripts\python.exe
.\.venv-oauth\Scripts\python.exe -m src.server
```

O servidor usa stdio e aguarda um cliente MCP; encerrar com Ctrl+C. Logs próprios em stderr, stdout somente protocolo. Não há banner próprio. `.env` é opcional para a fundação e carregado pela raiz do projeto independentemente do diretório de execução; nunca transmitir credenciais por chat. `.env.example` documenta os nomes sem valores privados. `BUSINESS_TIMEZONE=America/Sao_Paulo`, `LOG_LEVEL=INFO`, timeouts 5/30 segundos e orçamentos de 500 GETs/180 segundos são defaults locais validados na inicialização. Faixas internas: conexão até 30s, leitura até 60s, máximo 500 requisições/180s; valores não positivos são erro. Os orçamentos estão **configurados, ainda não aplicados a análises** que não existem. Configuração OAuth/PKCE/certificado continua na CLI administrativa e só é exigida ao iniciar fluxo OAuth, não ao descobrir o servidor vazio.

`src/server.py` compõe configuração, logs e lifespan de `MercadoLivreClient`, que fecha a `requests.Session` no encerramento. `src/client.py` usa origem HTTPS fixa, TLS ativo, timeouts 5/30 configuráveis, `trust_env=False`, lock da sessão, allowlist **atual** apenas GET `/users/me` e POST `/oauth/token`, sem redirects ou retry de POST. Política de retries, orçamento e rotas comerciais adicionais são Sprint 3; não inferir que estão prontos. `src/schemas.py` define `Money`, `Period`, `ToolError`, `Warning`, `Pagination`, `Metadata` e `ToolResult`, além de validação local de IDs, limites, offset e datas inclusivas convertidas a intervalo semiaberto no fuso local. `Money.amount` sai como texto decimal com moeda explícita. Nenhum `tools.py` vazio foi criado e nenhuma ferramenta provisória foi registrada: a descoberta stdio devolve **zero** ferramentas nesta sprint; isso não satisfaz VM01/VM02/aceite da V1.

### Registro de verificação manual da Sprint 1

Referência: `2cbc7f5` + working tree da Sprint 1 (sem commit). Horário local UTC−03 em 22/10/2026; exemplos monetários e de IDs abaixo são sintéticos, sem consulta comercial e sem suíte automatizada.

| ID | Data/hora | Código | Ambiente | Procedimento | Esperado | Observado | Situação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1-E01 | 20:03 | `src/server.py`, `src/auth.py` | Windows 11 / CPython 3.13.15 | `ssl.create_default_context()`, GET HTTPS público com confiança padrão, `src.auth check` | SSL funcional sem grant | TLS HTTPS 200; check validou WinVault, certificado e URI; nenhum token real | Verificado localmente |
| S1-E02 | 20:05 | `requirements.txt` | venv limpo no scratch / CPython 3.13.15 | `uv pip install -r requirements.txt`, `uv pip check`, imports e `ZoneInfo` | Reinstalação/compatibilidade | 73 pacotes fixados instalados, check compatível, FastMCP 4.1.3 e São Paulo disponíveis | Verificado localmente |
| S1-E03 | 20:03 | `src/schemas.py` | `.venv-oauth` | Exemplos sintéticos: 123.40 BRL, 20–22/10, IDs e argumentos inválidos | Decimal em texto, fim exclusivo dia 23, erros explícitos | `123.40` com `BRL`; fim `2026-10-23T00:00:00-03:00`; 4 intervalos/4 argumentos inválidos recusados; NaN recusado | Exercício sintético |
| S1-E04 | 20:04 | `src/client.py`, `src/server.py` | `.venv-oauth` | Examinar sessão e tentar rotas fora da allowlist sem enviar requisição | Destino/método proibidos | Base fixa HTTPS, `trust_env=False`, timeout configurado; 3 chamadas rejeitadas com `PERMISSION_DENIED` antes da rede | Exercício local, não API |
| S1-E05 | 20:04–20:05 | `src/server.py` | `.venv-oauth` e venv limpo, código copiado sem `.env` para scratch | Cliente FastMCP conecta via subprocesso `-m src.server` fora da raiz e lista ferramentas; encerramento | Handshake stdio, sem banners em stdout, teardown | Conectou em ambos ambientes; lista vazia intencional; log `server_started/server_stopped` em stderr; sem rede comercial | Verificado localmente, não Hermes |
| S1-E06 | 20:04 | `src/server.py` | cópia sem `.env` no scratch | Processo com stdin fechado e com fuso/orçamento/timeout inválidos, capturando canais | Saída stdout vazia; configuração inválida sanitizada | Normal: código 0, stdout 0 bytes; 3 configurações inválidas: código 1, stdout 0 bytes, apenas nomes de variáveis e erros em stderr | Verificado localmente |
| S1-E07 | 20:04–20:10 | `.gitignore`, `.env.example`, `src/server.py` | Windows / Git | `git check-ignore`; mensagem sintética Bearer/query/secret pelo formatter | Segredos não versionáveis/logáveis | `.env`, chaves TLS, backup TLS, runtime e venv ignorados; fonte não ignorada; texto sintético redigido, inclusive campo JSON | Revisão/exercício local; não auditoria real de respostas MCP |

Não foi executado grant OAuth, consulta autenticada, descoberta pelo Hermes ou reconciliação comercial. VM01 requer chamadas comerciais e `start_oauth` reais e continua pendente. S0.05/S0.10/S0.12 permanecem abertos nas sprints indicadas; não iniciar Sprint 2 sem autorização separada.

## Estado atual — recorte OAuth autorizado

Felipe confirmou a criação da aplicação e o cadastro de **https://127.0.0.1:8000/callback**. Essa é a única URI deste recorte; as candidatas de porta 8443 no histórico abaixo estão superadas. O cadastro é evidência informada pelo responsável, não leitura direta do portal; permissões reais e PKCE habilitado ainda precisam ser conferidos.

Foi autorizada inicialmente a antecipação dos pré-requisitos mínimos e do recorte OAuth; **a Sprint 1 integral foi autorizada posteriormente nesta solicitação**. Após a recusa inicial, Felipe autorizou instalar a CA local em 22/10/2026. Foi instalada uma CA exclusiva deste projeto em **CurrentUser\\Root**; nenhum aviso de segurança foi contornado e nenhum grant OAuth foi iniciado nesta etapa.

### Arquivos e limites da implementação

- `src/auth.py`: configuração pela raiz; compatibilidade explícita `ML_CLIENT_ID`/`CLIENT_ID` e `ML_CLIENT_SECRET`/`CLIENT_SECRET`, rejeitando conflitos; PKCE S256, state de uso único/5 minutos, listener HTTPS IPv4 loopback, WinVaultKeyring nativo, lock entre processos, rotação serializada e CLI administrativa. Não imprime tokens, state ou URL de autorização no terminal.
- `src/client.py`: Session exclusivamente para GET `/users/me` e POST `/oauth/token`, TLS ativo, redirects bloqueados, sem netrc/proxy ambiente, timeout 5/30s, payload limitado e erros sanitizados. Watchdog de socket de 45s interrompe headers/corpo lentos, inclusive HTTP/1.0; o resolvedor DNS do sistema não é cancelável aqui, portanto não há garantia absoluta de tempo total. POST OAuth nunca tem retry automático. Resiliência/paginação comercial completa continua fora deste recorte.
- `src/schemas.py`: envelope mínimo, erro seguro, projeção de identidade sem PII e registro de tokens com SecretStr; valores secretos só são desembrulhados na fronteira HTTP/cofre.
- `src/__init__.py`: sem I/O no import. `server.py` agora compõe o servidor mínimo; `tools.py` ainda não existe e `start_oauth` ainda não foi registrado como ferramenta MCP.
- `.gitignore`: preserva `.env`/venv e protege `.venv-oauth`, variantes de env, caches, runtime e chaves/certificados. `.env.example` contém somente nomes/defaults, não os valores do arquivo local. **O `.env` existente não foi editado ou impresso.**
- `requirements.txt`: versões diretas/transitivas do recorte OAuth preservadas e, na Sprint 1, acrescidas de FastMCP e tzdata com transitivas verificadas. Isso ainda não valida a V1 completa.

O ambiente original `.venv` Python 3.12 foi preservado. O recorte e a Sprint 1 usam **`.venv-oauth` com CPython 3.13.15**. A instalação de requirements foi repetida em ambiente limpo no scratch e os imports passaram; `uv pip check` também passou.

### TLS local — CA exclusiva instalada e confiança padrão verificada

O certificado autoassinado do diagnóstico inicial foi substituído por um certificado **de desenvolvimento** emitido pela CA mkcert exclusiva, com SAN IP `127.0.0.1`. Certificado/chave ativos continuam em `%LOCALAPPDATA%\DiasMoto\mercadolivre-mcp\tls\callback.pem` e `callback-key.pem`. O par anterior foi preservado no mesmo diretório com sufixo `.selfsigned-20261022-194131.bak`; não restaurá-lo inadvertidamente. A pasta tem ACL do usuário, SYSTEM e administradores, fora do repositório/OneDrive.

Instalação realizada com **mkcert v1.4.4**, binário Windows AMD64 do release oficial, sem instalar gerenciadores de pacotes ou alterar PATH. Executável em `%LOCALAPPDATA%\DiasMoto\mercadolivre-mcp\tools\mkcert-v1.4.4-windows-amd64.exe`; `CAROOT=%LOCALAPPDATA%\DiasMoto\mercadolivre-mcp\ca` e `TRUST_STORES=system` foram passados somente aos subprocessos desta operação. Isso não usa nem altera o CAROOT de outros projetos, Java ou perfis Firefox. A presença exata da CA em CurrentUser\\Root e a ACL herdada da pasta da CA foram lidas de volta. `rootCA-key.pem` é altamente sensível: nunca compartilhar, versionar ou sincronizar.

**Validação após instalação, 22/10/2026 às 19:41 UTC−03:** o callback real respondeu HTTP 200 usando `ssl.create_default_context()` **sem cafile especial ou verificação desligada**; a cadeia nativa do Windows também foi aceita. O certificado expira em 22/01/2029 às 19:41:31 UTC−03. O listener diagnóstico encerrou com código 0, stdout vazio e porta 8000 liberada. `authorize`/`reauthorize` mantêm a checagem de confiança antes de abrir OAuth. **Felipe confirmou posteriormente o diagnóstico no navegador sem aviso**, encerrando S0.07 com evidência informada pelo responsável, não captura de tela pelo agente.

Para essa confirmação, iniciar `tls-only --seconds 120` e abrir **https://127.0.0.1:8000/callback** no Edge/Chrome. Esperado: sem aviso de certificado e texto `HTTPS local pronto; nenhum OAuth executado.` Se o navegador já estava aberto durante a instalação, reiniciá-lo antes de repetir. Não executar `authorize` automaticamente; instalar CA não foi consentimento para iniciar grant.

Remoção futura da confiança desta CA, somente quando não mais necessária: em PowerShell, definir `CAROOT` para a pasta exclusiva acima e `TRUST_STORES=system`, executar o binário local com `-uninstall` e conferir a ausência da CA exata em CurrentUser\\Root. Esse comando remove confiança, não apaga a chave/CA; apagar material local exige decisão separada. Não usar o CAROOT padrão nem remover certificados de outros projetos.

### Comandos do recorte (PowerShell na raiz)

```powershell
.\.venv-oauth\Scripts\python.exe -m src.auth check
.\.venv-oauth\Scripts\python.exe -m src.auth tls-only --seconds 120
.\.venv-oauth\Scripts\python.exe -m src.auth authorize
.\.venv-oauth\Scripts\python.exe -m src.auth profile
```

`check` valida configuração, certificado carregável e escrita/leitura/remoção de um valor sintético no cofre, não autenticação da conta. Seu campo `browser_trust=not_checked` é fixo e não muda após instalar a CA. `tls-only` serve somente a rota diagnóstica e encerra; não dispara OAuth. `authorize` aguarda consentimento por até cinco minutos, sem expor códigos; `profile` só faz GET autenticado com credencial válida do cofre. Todos os diagnósticos da CLI vão a stderr, com stdout vazio. **Atualização de 22/10/2026:** `check` e confiança TLS padrão passaram; Felipe confirmou o navegador (§ Sprint 0 acima); ainda não houve grant real.

Renovação administrativa: `.\.venv-oauth\Scripts\python.exe -m src.auth refresh`, somente com tokens reais e em etapa acompanhada. Reautorização deliberada após falha: ação `reauthorize`; preserva vínculo ao vendedor anterior. Não trocar de conta silenciosamente: outro vendedor exige perfil local distinto definido pelo responsável, sem processos simultâneos por perfil.

Antes de renovar, persiste-se `refresh_in_flight` no mesmo registro do cofre, confirmado por readback. Assim, timeout/crash entre envio e persistência não permite reapresentar o refresh antigo no reinício. Apenas um novo conjunto completo substitui o marcador; falha/resultado incerto exige reautorização. O refresh é de uso único, e cada consulta de perfil faz no máximo uma renovação segura e uma repetição de GET.

### Evidências desta implementação e bloqueios reais

| Procedimento | Observado | Grau de evidência |
| --- | --- | --- |
| Configuração real via CLI `check` | Inicialmente erro de formato do ID; após correção local por Felipe, `success=true`, WinVaultKeyring, certificado carregado, PKCE S256 e URI exata | Diagnóstico real sanitizado repetido pelo agente; não valida Client Secret/PKCE no portal nem grant |
| TLS IPv4 real, cliente com confiança isolada | HTTP 200 na rota exata; rota alheia 404; no-store; encerramento | Rede local real, sem API comercial |
| Verificação TLS padrão / CLI authorize com configuração sintética | Certificado rejeitado; CLI não abre navegador nem executa grant | Bloqueio de segurança observado, sem CA instalada |
| WinVault nativo | Escrita/readback/remoção de valor sintético e round-trip do TokenRecord; segredo mascarado no repr | Cofre real, exclusivamente perfil/valores de diagnóstico, removidos ao final |
| Lock Windows | Segundo dono bloqueado; lock readquirido após encerrar | Exercício local real |
| PKCE/state/repetição | Challenge recalculado independentemente; state incorreto recebe 400 sem POST; start repetido mantém transação; replay rejeitado | Exercício controlado com estado sintético |
| Callback com troca/perfil | HTTP local 200 e estado conectado com cliente remoto sintético | **Não** é grant ou `/users/me` real |
| Rotação bem-sucedida/timeout/401 | Substituição persistida; marcador impede reapresentação; expiração + 401 não renova duas vezes | Exercício sintético do fluxo, não rotação de tokens reais |
| Compile/import/dependências | compileall, imports Python 3.13, pip check e reinstalação limpa passaram | Execução local; sem pytest/suíte de testes |

**Revisão independente e correções:** a revisão estática encontrou renovação duplicada no comando administrativo `refresh`, encerramento bloqueante se a thread do listener não chegasse a iniciar e ausência de orçamento de socket para respostas lentas. Os dois primeiros foram reproduzidos localmente antes da correção. Agora a CLI propaga a renovação já realizada e o listener fecha diretamente o socket quando a thread não iniciou. Exercício sintético confirmou uma única rotação mesmo com `expires_in=30` e HTTP 401, além de liberação/readquisição do lock após falha simulada de thread.

O transporte foi exercitado contra servidor **TLS local**, com confiança explícita isolada e orçamento reduzido só durante o diagnóstico para 0,2s: headers lentos foram interrompidos em 0,221s e corpo lento HTTP/1.0 em 0,259s; resposta normal passou em 0,004s. Nenhuma chamada comercial foi feita. O orçamento de produção permanece 45s por socket/requisição; resolução DNS/conexão anterior ao envio não é uma promessa de prazo rígido, e os 5 minutos são a janela de consentimento, não um prazo total garantido de todo o grant. Interrupção de POST preserva a política de resultado incerto, sem retry. A porta 8000 ficou sem listener após o encerramento das verificações.

**Consulta real a `/users/me` não executada.** Configuração local, confiança TLS padrão e diagnóstico no navegador passaram (este último confirmado por Felipe); faltam PKCE/permissões no portal e consentimento no site oficial. Não foi lido registro de produção de outro MCP, aproveitado token de outra integração nem emitido refresh real.

**Histórico do checkpoint TLS:** às 19:36 UTC−03 a confiança padrão rejeitava o certificado autoassinado. Após autorização e instalação da CA exclusiva, a repetição com o novo certificado passou com HTTP 200 e cadeia Windows válida; o servidor encerrou e liberou a porta. Felipe confirmou em seguida o navegador sem aviso, fechando S0.07. Aceites de autenticação/API reais continuam pendentes, separados dessa comprovação.

## Histórico da pesquisa e roteiro anterior

As seções seguintes preservam o planejamento e a pesquisa anteriores ao recorte. Menções a ausência de código, requirements, certificados e endereços candidatos são **baseline histórica**, não o estado atual. Para executar o recorte, prevalecem os comandos, URI e bloqueios acima. Nenhuma autorização para a Sprint 1 integral foi concedida.

## Estado observado e reaproveitamento

Inspeção local em 22/10/2026, a partir do commit `8d6f55e` (`first commit`), branch `main`:

- Raiz inicial: `PRD.md`, `AGENTS.md`, `.gitignore`, `.git/` e `.venv/`. README inexistente antes desta entrega.
- Não existem `src/`, requirements, lockfile, configuração de lint/build/CI ou código de aplicação a revisar. Não há padrões de implementação observados; a arquitetura é requisito futuro.
- `.gitignore` contém somente `.venv/`: reaproveitar essa regra; proteção de `.env`, certificados, chaves, caches e runtime será tarefa S1.06, **antes** de criar arquivos sensíveis.
- `.venv/pyvenv.cfg` registra Python **3.12.10**, não o alvo 3.13. S1.02 já estava marcado pelo usuário e foi preservado; isso não comprova S1.01 nem compatibilidade.
- Preservados Git, orientações válidas do AGENTS e a alteração preexistente de S1.02; AGENTS atualizado apenas para refletir o estado e as descobertas. Não houve instalação, OAuth, alteração do portal, configuração do Hermes, commit ou push.
- O arquivo de origem `Texto colado(7).txt`, citado pelo PRD, não está na raiz; não foi possível reconciliar seu conteúdo. O PRD disponível orienta esta entrega.

## Escopo confirmado

Exatamente sete ferramentas comerciais: `get_seller_profile`, `list_orders`, `list_seller_items`, `get_item_details`, `get_item_visits`, `get_sales_summary`, `get_sales_comparison`; mais `start_oauth`. Uma conta, FastMCP/stdio, requests, Pydantic, python-dotenv, keyring e tzdata; cálculos determinísticos, sem LLM dentro do MCP.

Sem escrita comercial, Ads, NetOne, frontend, banco, Docker, jobs, webhooks comerciais ou testes automatizados. O receptor OAuth temporário é a única exceção de servidor HTTP. As recomendações genéricas dos guias oficiais não ampliam esse escopo.

Contratos preservados: IDs externos como texto; dinheiro Decimal e moeda explícita; data final pública inclusiva em `America/Sao_Paulo`; metodologia `created_paid_v1` sobre criação e estado observado; reembolsos conforme PRD §10; agregado incompleto retorna `success=false`, `PARTIAL_DATA` e métricas definitivas nulas. `top_n` nunca limita a coleta.

## Fontes e método da pesquisa

Consulta em **22/10/2026**. As páginas Mercado Livre foram lidas integralmente pelo MCP documental oficial (`search_documentation` / `get_documentation_page`), não apenas por snippets. As datas abaixo são de atualização declarada pelo conteúdo, não prova de comportamento da API.

| Ref. | Fonte oficial | Atualização / evidência |
| --- | --- | --- |
| S01 | https://developers.mercadolivre.com.br/pt_br/autenticacao-e-autorizacao | 29/12/2025; página integral |
| S03 | https://developers.mercadolivre.com.br/pt_br/gerenciamento-de-vendas | 21/09/2026; página integral |
| S04 | https://developers.mercadolivre.com.br/pt_br/itens-e-buscas | 31/08/2026; página integral |
| S05 | https://developers.mercadolivre.com.br/pt_br/recurso-visits | 02/01/2026; página integral |
| S06 | https://developers.mercadolivre.com.br/pt_br/desenvolvimento-in-house | 06/10/2026; página integral |
| S12 | https://developers.mercadolivre.com.br/pt_br/crie-uma-aplicacao-no-mercado-livre | 29/12/2025; página integral |
| S13 | https://developers.mercadolivre.com.br/pt_br/permissoes-funcionais | 21/11/2025; página integral |
| S14 | https://developers.mercadolivre.com.br/pt_br/gerencie-seu-aplicativo | 15/10/2026; página integral |
| S07 | https://gofastmcp.com/servers/tools.md e https://gofastmcp.com/deployment/running-server.md | Leitura HTTPS 200; documentação corrente, não versão fixada |
| S15 | https://gofastmcp.com/getting-started/installation.md e https://pypi.org/pypi/fastmcp/json | Documentação e metadados HTTPS 200 |
| S16 | https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference | Documentação oficial HTTPS 200; confrontada com CLI/código instalado |

O extrator web configurado não extrai URLs; a alternativa foi o MCP documental e urllib com TLS ativo. Não se instalou pacote para contornar isso. Nenhuma chamada à API comercial ou ao endpoint de tokens foi executada; MCPs comerciais já disponíveis na sessão não provam grant desta futura aplicação e não foram usados como substitutos.

## OAuth: contrato documental confirmado (S0.04)

- Authorization Code: navegador em `https://auth.mercadolivre.com.br/authorization`, com `response_type=code`, `client_id`, `redirect_uri` exata e estática, e `state` aleatório por transação. O Mercado Livre não valida `state`; o receptor deve validá-lo.
- PKCE é opcional na configuração da aplicação, mas obrigatório no fluxo quando habilitado. Usar `code_challenge`, `code_challenge_method=S256` e `code_verifier` correspondente. Não usar `plain`.
- Troca: POST `https://api.mercadolibre.com/oauth/token`, body `application/x-www-form-urlencoded` com `grant_type=authorization_code`, `client_id`, `client_secret`, `code`, `redirect_uri` e `code_verifier` quando aplicável.
- Renovação: mesmo POST com `grant_type=refresh_token`, `client_id`, `client_secret`, `refresh_token`. Somente o último refresh token, de uso único; persistir o novo conjunto no cofre antes de liberar outras chamadas.
- A documentação informa access token de 6 horas e refresh token com expiração de 6 meses; a implementação deve respeitar `expires_in` e revogações, nunca presumir validade até esses prazos. Validade exata do authorization code não foi encontrada; 5 minutos é expiração interna da transação, não prazo oficial do código.
- Login deve ser do administrador/titular; operador/colaborador pode receber `invalid_operator_user_id`. Mudança de senha/segredo, revogação e inatividade podem invalidar credenciais antecipadamente.
- Não repetir troca/refresh após resultado incerto; locks de sessão/processo, cofre nativo e reautorização segura permanecem obrigatórios.
- A página S01 contém texto legado sobre Implicit Grant e descrição inconsistente de `client_secret`; os exemplos de POST e o guia S06 confirmam Authorization Code e segredo da aplicação. Não copiar o texto contraditório para implementação.

## Aplicação e permissões: D01 bloqueada (S0.05)

Responsável: **Felipe/gestor, com desenvolvedor**. Não foi disponibilizada identificação sanitizada da aplicação nem acesso ao seu painel. Não é possível afirmar criação, titularidade, permissões efetivas, PKCE ou grant.

Checklist a conferir no DevCenter, sem enviar segredos ao chat:

1. Aplicação sob a conta oficial da empresa e administrador autorizado; não criar outra aplicação automaticamente. Registrar apenas confirmação de titularidade e situação, sem Secret Key.
2. Unidade Mercado Livre separada de Mercado Pago: S06/S14 informam exigência desde 30/08/2026. Verificar ausência de scopes `urn:mp:...` no painel ou por procedimento administrativo autorizado; nenhuma rota administrativa será adicionada ao MCP V1.
3. Candidatos mínimos documentais: **Usuários** (default), **Publicação e sincronização** (itens), **Vendas e envios** (pedidos) e **Métricas do negócio** (visitas). Visitas aparecem em mais de uma área da documentação; confirmar mapeamento efetivo no portal sem habilitar permissões extras por suposição.
4. Nível leitura e acesso offline para renovação, se oferecidos: `read` e `offline_access` são nomes documentados. Não copiar `write` dos exemplos de tokens. Se leitura não bastar segundo a aplicação real, registrar a restrição para decisão explícita, sem habilitar escrita automaticamente.
5. Não selecionar Ads, mensagens, faturamento ou tópicos de notificações para suprir este escopo. Registrar nomes realmente oferecidos, escolhas e PKCE habilitado/desabilitado.

## Callback HTTPS: D02 formalmente bloqueada (S0.06–S0.08)

**Motivo:** S06/S12 exigem HTTPS e correspondência exata, mas não garantem aceitação de loopback nesta aplicação. Não há URI aprovada, host, porta, certificado ou prova de roteamento fornecidos. Não houve rejeição observada no portal; desconhecido não significa rejeitado. S0.08 é condicional e permanece aberto até essa decisão.

Responsável: **Felipe + desenvolvedor**. Próximo passo: acessar a aplicação e verificar aceitação de uma URI local acordada; depois executar o procedimento abaixo. A autenticação real da Sprint 2 não pode ser aceita antes disso; a fundação sem credenciais pode avançar.

Procedimento proposto, **não executado e sem valores aprovados**:

1. Escolher com o responsável um host/IP loopback, porta livre e caminho fixo; compor URI HTTPS sem parâmetros variáveis. A candidata concreta do roteiro guiado abaixo usa IP literal, sem nome/DNS. Não preencher `ML_REDIRECT_URI` com um endereço ficticiamente aprovado.
2. Confirmar que o portal salva a URI exata. Registrar aceitação ou mensagem sanitizada de rejeição; não copiar código OAuth, segredo ou tela com credenciais.
3. Com IP literal loopback não há alteração de resolução. Se for indispensável usar nome local, resolver exclusivamente para loopback no Windows; edição do arquivo hosts exige registro/backup e autorização administrativa. Não alterar DNS público ou abrir firewall automaticamente.
4. Emitir certificado com SAN correspondente ao nome ou IP literal e cadeia confiável no navegador do usuário. Proteger chave privada fora do versionamento e de sincronização compartilhada; obter consentimento antes de instalar uma CA. Não desabilitar TLS.
5. Conferir resolução, porta disponível e HTTPS no navegador com receptor diagnóstico temporário restrito ao loopback e à rota definida, sem logs de query. Registrar método/resultado sem tokens. Não implementar antecipadamente `auth.py` nesta sprint.
6. Anotar host, porta, URI, caminhos absolutos do certificado/chave e PKCE localmente; só então comprovar retorno do navegador ao receptor. Desligar receptor após a verificação.
7. Remoção: encerrar listener, desfazer somente a entrada hosts e confiança instaladas para esta finalidade e remover material local não usado, sem afetar outros projetos.

Se a URI local for efetivamente recusada, registrar evidência e solicitar primeiro orientação/suporte do Mercado Livre para uma URI local aceita. Se for indispensável uma URL pública, a menor alteração proposta é permitir **somente o callback HTTPS de autorização**, mediante revisão explícita do PRD e aprovação do responsável; túnel/hospedagem são alternativas a decidir, não adotadas. Não usar HTTP presumido, tokens manuais nem coleta do código pelo chat.

## Endpoints e limites revisados (D03)

São contratos **documentais**, ainda não observados com a conta. Base fixa `https://api.mercadolibre.com`; Bearer em header, TLS ativo, redirects autenticados desabilitados; nenhum destino arbitrário.

| Uso | Método / rota | Confirmação e pendência |
| --- | --- | --- |
| Identidade | GET `/users/me` | Confirmado em S01; validar identidade real em Sprint 3 |
| Pedidos | GET `/orders/search` | `seller`, `order.status`, `order.date_created.from/to`, `limit`, `offset`; `paging.total/offset/limit` no exemplo S03 |
| Enriquecimento interno de pedido | GET `/orders/{order_id}` | S03; validar seller; HTTP 206 e `X-Content-Missing` podem indicar campos ausentes |
| IDs próprios | GET `/users/{user_id}/items/search` | S04; `status`, `limit`, `offset` convencional; scan com `search_type=scan`, `scroll_id`, **sem offset** |
| Detalhe de anúncio | GET `/items/{item_id}` | S04; checar propriedade; quantidade pública referencial não prova estoque exato |
| Bulk atual | GET `/items/bulk` | S04: `ids`, `attributes=body.id,body.price,...`; elemento com `id` raiz, `status_code`, `body`; tamanho máximo do novo bulk não explicitado |
| Visitas por período | GET `/items/visits` | S05: `ids`, `date_from`, `date_to`; **um ID por requisição**, máximo de intervalo 150 dias |
| Token | POST `/oauth/token` | S01; único POST externo permitido ao projeto |

### Pedidos: S0.09 confirmado documentalmente; S0.10 parcialmente pendente

- Datas de filtro em ISO 8601 com offset; S03 informa que filtros usam até a **hora**, descartando minutos, segundos e milissegundos. Menor partição documental: uma hora, não segundos. Consultar envelope temporal que cubra a fronteira e filtrar localmente pelo intervalo interno semiaberto; preservar offset da API independentemente do filtro local.
- S03 informa disponibilidade de pedidos criados por até **12 meses** e exclusão de cancelados na busca como vendedor. Não há prova de que `order.status=cancelled` recupere essa população; não declarar zero nem totais de cancelamentos completos sem validação específica.
- Estados documentados: `confirmed`, `payment_required`, `payment_in_process`, `partially_paid`, `paid`, `partially_refunded`, `pending_cancel`, `cancelled`, `invalid`. Frontend pode chamar de cancelada uma venda que a API retorna `confirmed`. Preservar estado observado; não reclassificar por rótulo do painel.
- Ordenação default é `date_asc`, mas para sellers usa **date_closed**, não criação; não parar uma coleta com base em pressuposta ordenação por criação.
- O exemplo tem `paging.limit=50`; isso **não prova máximo oficial**. Teto de offset/resultados e limite oficial por página não foram encontrados em S03 nem na busca complementar. Responsável: desenvolvedor; consultar documentação/suporte antes de fixar teto e validar leitura autorizada na Sprint 3. Não herdar 1.000 do scan de itens nem inventar 10.000 para pedidos.
- Se uma hora ainda exceder a paginação disponível, declarar `PARTIAL_DATA`, sem subdivisão fictícia. `gross_price` novo representa total antes de descontos; **não substitui** `unit_price × quantity` da metodologia `created_paid_v1`.

**Pesquisa complementar de S0.10 — 22/10/2026:** releitura integral de Orders em português e espanhol, buscas por `orders paginacion offset`, `paginação orders limite` e `orders search maximum limit offset`. Ambas as páginas confirmam a precisão horária e mostram `paging.total`, `offset` e `limit=50` em exemplo; nenhuma delas estabelece o máximo de página ou teto de offset/resultados.[1][9] A FAQ oficial encontrada para limite próximo de 1.000 refere-se explicitamente à busca de **itens** e a scan/scroll, não a pedidos; não se aplica a `/orders/search`.[8] Não foi encontrada fonte oficial que justifique assumir 10.000 para pedidos. Resultado: pesquisa documental realizada, mas **S0.10 continua aberto** pela confirmação numérica externa.

Regra de implementação já prevista no PRD, sem implementar agora: página interna 20/máximo 50 não é limite oficial; percorrer paginação somente com cobertura verificável, deduplicar pedidos e filtrar fronteiras localmente. Particionar apenas em horas ou unidades maiores quando necessário e suportado; parar com `PARTIAL_DATA` se limite, erro, repetição ou orçamento impedir cobertura. Não usar scan de itens para pedidos nem inferir completude de uma página curta sem reconciliar a paginação. Uma eventual restrição de cancelados deve aparecer separadamente como limitação da população.

### Itens: S0.11 confirmado documentalmente, sem prova autenticada

- Busca convencional alcança a janela de 1.000 resultados; scan é a alternativa documentada para mais de 1.000. Padrão documentado 50 e máximo 100; projeto mantém máximo interno 50.
- `scroll_id` expira em **5 minutos**; S04 orienta reutilizá-lo na continuação. O texto tem redação ambígua sobre atualizar/reutilizar: preservar o cursor efetivamente fornecido e validar sequência real na Sprint 4, sem reiniciar silenciosamente.
- Busca própria oferece estados como `active`, `paused`, `closed`, `pending`, `not_yet_active`, `programmed`; não substituir por busca pública que só lista ativos.
- Migração até **25/10/2026**: substituir `/items?ids=` por `/items/bulk?ids=`; não usar parser de `code` antigo. Os **20 resultados** aparecem na seção legada Multiget, não como confirmação inequívoca do lote do novo bulk. Responsável: desenvolvedor; confirmar lote em documentação/suporte e validar na Sprint 4; usar limite interno conservador explicitamente não oficial até lá.

### Visitas: S0.12 parcialmente pendente

- S05 esclarece com erro explícito que a **extensão do intervalo não pode exceder 150 dias**; isso não comprova antiguidade/retenção da rota por período. O total dos últimos dois anos pertence a `/visits/items`, outra rota, não selecionada para RF05.
- Erro documentado `maximum amount of items to query is 1`: manter entrada MCP de 1–20 IDs únicos, mas dividir em **requisições sequenciais de um ID**, incluindo custo no orçamento; não enviar o lote inteiro.
- Exemplos de `date_from/to` são `YYYY-MM-DD`, com resposta em `00:00:00Z`. Exemplos de `time_window` excluem o dia `ending`, mas essa rota não prova inclusividade da rota por período. Aceitação de timestamp com offset, fronteira final e retenção histórica de `/items/visits` continuam não esclarecidas.
- Responsável: desenvolvedor; obter confirmação documental/suporte e observar fronteiras autorizadas na Sprint 4. Se não houver equivalência com o dia de São Paulo, retornar período efetivo UTC e advertência, nunca alinhamento fictício.
- S05 informa herança do histórico de visitas ao republicar a partir de `parent_item`; isso não permite unir vendas por títulos ou tratar visitas como compradores únicos, tráfego orgânico ou causalidade.

**Pesquisa complementar de S0.12 — 22/10/2026:** leitura integral PT, ES e duas páginas EN. As páginas locais concordam no erro para extensão superior a 150 dias e no máximo de um ID por requisição.[2][6][7] Os exemplos retornam `date_from/to` à meia-noite UTC; não definem em texto a inclusividade de `date_to` da rota `/items/visits` nem garantem timestamps com offset. O exemplo de `time_window` não foi promovido a contrato de outra rota.[2] A página EN voltada a integrações CBT informa até 48 horas para disponibilidade e contagem única por dia em itens locais; é evidência documental complementar, não garantia medida na conta MLB nem de compradores únicos em todo o período.[5] O dado recente pode ainda consolidar; não tratar diferença recente como perda definitiva.

Nenhuma dessas páginas esclarece a antiguidade recuperável por intervalo. Os dois anos são o total acumulado de `/visits/items`, **não** a retenção da rota por período.[2] Resultado: extensão e tamanho da requisição confirmados documentalmente; **S0.12 continua aberto** por retenção/fronteiras. RF05 deve devolver período efetivo e indisponibilidade, sem zero fictício, conversão exata presumida ou promessa de três meses de tráfego já validada.

## FastMCP e dependências (S0.13 / D05)

S07 confirma `mcp.run(transport="stdio")` (stdio também é default), `run()` em contexto síncrono e proteção `if __name__ == "__main__"`. Ferramentas `def` são executadas em threadpool na documentação corrente; requests deve ficar fora de `async def`, com lock reentrante compartilhado para serializar a sessão/renovação. Retornos dict/Pydantic geram `structuredContent`; anotação de retorno gera schema. Confirmar serialização Decimal e tratamento de erro na versão realmente fixada, sem depender apenas da documentação corrente.

S15/PyPI informa FastMCP **4.1.3**, publicado em 20/10/2026, `Requires-Python >=3.10` e classificador Python 3.13. É candidato documental, **não dependência instalada/verificada**, e não foi criado requirements. A documentação inclui APIs/versionamentos diferentes; Sprint 1 deve instalar somente a stack autorizada em Python 3.13, verificar import/stdio/schema/threadpool e fixar versões realmente exercitadas. D05 permanece pendente.

## Hermes instalado e configuração futura (S0.14 / D04)

`hermes --version` executado: **Hermes Agent v0.22.2 (2026.9.24), stable, local d923a5eb487a**, instalação Git em `C:\Users\fstiz\AppData\Local\hermes\hermes-agent`, runtime próprio Python 3.11.15. Esse Python não é o Python alvo do projeto. A metadata do `python` do terminal indicou outra distribuição `hermes-agent 0.20.0`: para a CLI executada, prevalece `hermes --version`. `hermes version` não existe nesta instalação.

`hermes mcp add --help` confirma `NAME`, `--command`, `--env KEY=VALUE`, `--connect-timeout` e `--args` **por último**. A fonte instalada `tools/mcp_tool_transport.py:125–136,371–374` resolve `config.get("cwd")` ou o contexto de sessão e repassa ao subprocesso; a CLI add não expõe uma flag `--cwd`. Não inventar uma flag nem depender do local em que Hermes foi iniciado.

Configuração proposta para a Sprint 6, **não executável hoje** porque não há módulo/ambiente alvo validado (PowerShell, comando completo em uma linha):

```powershell
hermes mcp add dias-moto-ml-local --command "C:\Users\fstiz\OneDrive\Documentos\Programação\mercadolivre-mcp\.venv\Scripts\python.exe" --env "PYTHONPATH=C:\Users\fstiz\OneDrive\Documentos\Programação\mercadolivre-mcp" --args -m src.server
```

O `PYTHONPATH` explícito permite localizar `src` mesmo se o cwd herdado variar; o futuro `server.py` deve localizar `.env` pela raiz do próprio projeto, não pelo cwd. Nenhum segredo vai em `--env`/argumentos. Não registrar o servidor agora nem sobrescrever MCPs existentes. Se o nome já existir, inspecionar e escolher nome distinto.

S16 documenta `timeout` e `connect_timeout`; a referência corrente informa default de chamada 300s, enquanto exemplos/skills antigos mostram 120s. Conferir valor efetivo na instalação e ajustá-lo por mecanismo oficial antes de validar orçamento de 180s. Registro, descoberta de oito ferramentas e chamadas reais permanecem S6.03–S6.09, não foram executados. Usar CLI oficial para registrar e ler de volta; não editar `mcp_servers` manualmente.

## Decisões, responsáveis e desbloqueio

| ID | Situação em 22/10/2026 | Responsável e próximo passo |
| --- | --- | --- |
| D01 | **Bloqueada por entrada humana**: aplicação/permissões reais desconhecidas | Felipe/gestor + desenvolvedor: confirmar titularidade, Mercado Livre sem scopes MP, permissões de leitura/offline e PKCE no portal; sem segredos no chat |
| D02 | **Formalmente bloqueada**: URI local aceita e certificado não comprovados | Felipe + desenvolvedor: executar procedimento de callback; em rejeição comprovada, decidir mudança mínima antes de qualquer serviço externo |
| D03 | **Parcial**: rotas/scan/bulk e extensão/1 ID de visitas documentados; faltam teto de pedidos, lote novo bulk, retenção/fronteiras de visitas | Desenvolvedor: documentação/suporte oficial; validação autenticada apenas após D01/D02, nas sprints 3–4 |
| D04 | **Sintaxe/versão identificadas**; integração real pendente | Desenvolvedor: usar Python absoluto e PYTHONPATH explícito, raiz por arquivo, confirmar timeout e descoberta na Sprint 6 |
| D05 | **Pendente da Sprint 1**: candidato FastMCP identificado, nada instalado | Desenvolvedor: validar Python 3.13 e stack permitida em ambiente limpo, depois fixar requirements |

## Evidências manuais desta entrega

Referência: base `8d6f55e` + alterações locais de documentação; Windows 11, Git Bash; timestamp coletado no início da pesquisa **22/10/2026 17:31:50 UTC−03**. Evidências exclusivamente documentais/locais, sem dados comerciais; esse horário não representa o encerramento da entrega.

| ID | Procedimento | Esperado | Observado | Situação |
| --- | --- | --- | --- | --- |
| S0-E01 | Inventário sem `.venv/.git` internos; git status/branch/log/ls-files | Identificar base e alterações existentes | Três arquivos versionados, main, commit 8d6f55e, somente PRD modificado por S1.02 no início | Verificado localmente |
| S0-E02 | Leitura integral PRD, AGENTS, ignore e pyvenv.cfg | Conhecer requisitos/padrões e preservar trabalho | Sem aplicação; Python 3.12.10; S1.02 preservado; nenhuma suíte automatizada | Revisão documental |
| S0-E03 | MCP documental oficial, oito páginas ML | Confirmar contrato e lacunas | OAuth, HTTPS, permissões, pedidos, scan/bulk e visitas registrados com diferenças acima | Verificado documentalmente, não API |
| S0-E04 | urllib HTTPS docs FastMCP e PyPI | Verificar stack candidata e comportamento documentado | Python >=3.10/classificador 3.13, stdio, def/threadpool e saída estruturada documentados | Não instalado/exercitado |
| S0-E05 | hermes --version; hermes mcp add --help; fonte de transporte e S16 | Identificar cliente/sintaxe sem mudar configuração | CLI 0.22.2, args por último, cwd na fonte e PYTHONPATH proposto | Inspeção local, integração não realizada |
| S0-E06 | Conferência de D01/D02 e lacunas D03 | Não inventar configurações reais | Nenhuma confirmação de portal/URI/certificado; tarefas dependentes abertas | Bloqueado/pendente, com responsáveis |

VM01–VM17 não executados: dependem da implementação/conta. Não há comandos de build, teste ou lint definidos. Os comandos `py -3.13 -m venv .venv`, ativação, instalação por requirements e `python -m src.server` do PRD §14 continuam **planejados**, não instruções operacionais já válidas.

## Acompanhamento da Sprint 0: autonomia e dependências externas

Atualização documental: **22/10/2026**, timestamp da pesquisa complementar coletado às **17:47:51 UTC−03**. Nenhum item novo foi marcado como concluído; as confirmações ainda não existem. O horário é da inspeção, não do início ou encerramento.

| Grupo | Itens / o que pode ser feito | Limite / evidência que falta |
| --- | --- | --- |
| Autônomo, documental | S0.10/S0.12: pesquisar fontes, comparar idiomas e registrar limites/contratos | Pesquisa feita; números e fronteiras não publicados nas fontes consultadas seguem pendentes, sem inventar resposta |
| Manual no DevCenter | S0.05: titularidade, permissões, offline e PKCE; S0.06: salvar URI HTTPS candidata | Felipe confirma os valores não secretos e o resultado do portal; nenhum login/segredo via chat |
| Local assistido, não é configuração do DevCenter | S0.07: porta, listener loopback, certificado e navegador confiável | Agente pode executar verificações e preparar diagnóstico após autorização; instalar ferramenta/CA exige acompanhamento e consentimento |
| Condicional, decisão humana | S0.08: se o portal recusar callback local | Registrar rejeição real e decidir mudança mínima; não assumir que houve recusa nem instalar túnel/deploy |
| Externo técnico | Lacunas S0.10/S0.12 e lote do novo bulk | Suporte oficial ou observação controlada autorizada nas sprints correspondentes; sem varreduras/carga para descobrir limites |
| Encerramento | S0.CONCLUSAO | Só revisar status após comprovação; fundação sem credenciais pode ser autorizada separadamente, não é encerramento automático |

Perguntas prontas para o suporte oficial (nenhum chamado foi aberto):

1. Para vendedor MLB em `GET /orders/search`, qual o máximo de `limit` e de `offset`/resultados por consulta? Como coletar integralmente uma coorte de criação quando uma janela de uma hora excede esse teto? O filtro explícito de cancelados recupera pedidos omitidos por padrão?
2. Em `GET /items/visits`, qual a data mais antiga consultável por intervalo? `date_to` é exclusivo ou inclusivo? São aceitos timestamps ISO 8601 com offset ou apenas datas normalizadas a UTC? A disponibilidade em até 48 horas informada na página EN se aplica à conta MLB local?

## Roteiro guiado: aplicação, HTTPS e OAuth

Executar **uma etapa de cada vez**, conferir o resultado e só então passar à seguinte. Não iniciar a Sprint 1 automaticamente. Nesta entrega só foram pesquisados e documentados os passos; nada abaixo foi instalado/configurado.

### Etapa A — Conferir a aplicação no DevCenter (agora)

1. No seu navegador, abra https://developers.mercadolivre.com.br/devcenter/ e entre pessoalmente com a conta titular/administradora da empresa. A recomendação oficial é criar a aplicação sob a conta proprietária da solução.[3]
2. Em **Minhas aplicações**, veja se já há aplicação adequada. Se existir, abra **Editar/Configurações**; não exclua, regenere segredo nem substitua URIs de integrações existentes. Se não existir, crie somente após conferir o limite da conta, com nome disponível e finalidade de leitura. Sugestão de descrição: `Consulta local de pedidos, anúncios e visitas da Dias Moto Peças para análise comercial, sem alterar dados.` A documentação limita descrição a 150 caracteres.[3]
3. Confirme unidade de negócio Mercado Livre e mantenha a separação de Mercado Pago já registrada em D01; não habilite pagamentos, Ads ou webhooks comerciais para cumprir este roteiro.
4. Nas permissões funcionais, procure **Usuários** (default), **Publicação e sincronização**, **Vendas e envios** e **Métricas do negócio**. São os grupos documentais relacionados a users, items, orders e visits; os rótulos efetivos devem ser conferidos na tela.[11]
5. Escolha **leitura**, não escrita. Confirme acesso offline para renovação quando oferecido. `read` e `offline_access` são nomes documentados; o exemplo com `write` não obriga a solicitá-lo.[4] Se a tela exigir escrita ou permissões adicionais, pare e descreva a exigência sanitizada; não habilite por tentativa.
6. Para aplicação nova/dedicada, a preferência do projeto é **habilitar PKCE**, usando S256 na implementação futura. PKCE é recomendado oficialmente e obrigatório no fluxo se habilitado no app.[3][4] Se aplicação existente atende outro sistema, não mude PKCE sem verificar impacto e autorização do responsável.
7. Não selecione tópicos de notificações. Se o formulário exigir URL pública de notificações mesmo sem tópicos, registre essa exigência; não invente URL nem abra infraestrutura externa.

**Ponto de parada A:** informar apenas se a aplicação existe, se pertence à empresa, os nomes/níveis das permissões disponíveis e o estado de PKCE. Não enviar Client Secret, código, token ou captura com esses valores. Não é necessário criar `.env` nesta sprint; seu ignore ainda não está pronto.

### Etapa B — Conferir uma URI local simples (depois de A)

**Candidata proposta, ainda não aprovada nem testada:** `https://127.0.0.1:8443/oauth/callback`. Escolha de projeto para reduzir configuração: IP loopback IPv4, porta candidata 8443, rota única `/oauth/callback`; sem domínio, DNS, hosts, proxy, túnel ou deploy. A porta ainda precisa ser conferida antes de iniciar listener. IP literal evita depender da escolha IPv4/IPv6 de `localhost`.

1. No campo **URLs de redirecionamento**, tente cadastrar a candidata exatamente como acima, sem `code`, `state`, query ou barra final adicional, preservando os cadastros existentes. HTTPS é exigido; a URI usada no fluxo deve coincidir exatamente com a cadastrada.[3][4]
2. Salve e reabra a aplicação para comprovar que o cadastro persistiu. Registre somente URI, data e resultado. A documentação consultada não garante aceitação de IP loopback; o cadastro é a primeira prova, não o fluxo OAuth completo.
3. Se recusada, **pare aqui** e informe a mensagem sanitizada. Não mude para HTTP, não use domínio de terceiro e não instale certificado/túnel para tentar contornar uma validação do portal. S0.08 só será resolvido com aceitação ou rejeição/decisão registradas.

**Ponto de parada B:** URI realmente persistida ou mensagem de rejeição. Nenhuma URL de autorização deve ser aberta ainda: o receptor seguro não existe.

### Etapa C — HTTPS confiável no Windows (somente após B e consentimento)

Proposta leve: **mkcert apenas como utilitário local de desenvolvimento**, não dependência de runtime do MCP. O projeto oficial suporta o repositório de certificados do Windows e certificados para `127.0.0.1`; ele não configura o listener.[10] Não foi encontrado executável `mkcert` no PATH desta sessão. Não instalar um gerenciador de pacotes inteiro só para isso: preferir o binário Windows adequado da página oficial de releases https://github.com/FiloSottile/mkcert/releases.

1. Antes de baixar/executar, revisar origem/arquitetura e eventual CA mkcert já usada por outros projetos. Usar Edge/Chrome para a verificação inicial: são lojas suportadas; suporte automático de Firefox no Windows não é prometido pelo README do utilitário.[10]
2. Reservar para este projeto a pasta local `%LOCALAPPDATA%\DiasMoto\mercadolivre-mcp\tls`, fora do OneDrive/repositório. Esse é caminho proposto, ainda não criado. Confirmar ACL restrita ao usuário e aos administradores autorizados antes de criar chaves; não compartilhar a pasta.
3. Só com autorização para alterar confiança do Windows, executar `mkcert -install`. Isso instala uma CA local: não é inofensivo nem equivale a uma CA pública. A chave `rootCA-key.pem` é altamente sensível e nunca deve ser compartilhada.[10]
4. Gerar certificado com SAN IP correto, depois de criar/proteger a pasta. Comando proposto para PowerShell, **não executado**:

```powershell
mkcert -cert-file "$env:LOCALAPPDATA\DiasMoto\mercadolivre-mcp\tls\callback.pem" -key-file "$env:LOCALAPPDATA\DiasMoto\mercadolivre-mcp\tls\callback-key.pem" 127.0.0.1
```

Os flags de caminho devem preceder os nomes/IPs.[10] Guardar somente os caminhos, nunca chave em texto no README. Verificação TLS da API permanece ativa; não configurar `verify=False`, ignorar avisos do navegador ou substituir globalmente as CAs do requests.

5. Após conferir que a porta está livre, preparar, em etapa acompanhada, um **diagnóstico temporário sem OAuth**: somente loopback `127.0.0.1`, TLS, rota acordada, sem servidor de arquivos, sem logs de URL/query. Abrir a candidata no navegador; exigir conexão confiável e resposta esperada, e encerrar. Não há código/comando de listener existente para executar hoje; não confundir `python -m http.server` (HTTP/arquivos) com esse receptor. O diagnóstico comprova TLS local, não uma autorização da conta.
6. Anotar URI salva, porta, certificado confiável, conexão no navegador e encerramento. Se falhar SAN/confiança/porta, corrigir localmente e repetir sem baixar a segurança. Não executar grant OAuth neste diagnóstico.

**Ponto de parada C:** S0.07 só fecha com esses resultados observados. Não instalar Nginx, Docker, serviços do Windows, servidor público ou domínio. Remoção posterior deve considerar se a CA é compartilhada: retirar confiança de uma CA usada por outros projetos os afeta; combinar antes de remover CA/arquivos.

### Etapa D — Entender OAuth agora; executar só na Sprint 2

Não precisamos gerar tokens para aprovar a fundação da Sprint 1. Autorizar agora sem receptor, validação de state e cofre implementados criaria um atalho inseguro. O fluxo abaixo é **futuro**, não executado e não requisito de código da Sprint 0:

1. Com fundação e autenticação implementadas/revisadas, preencher configuração local protegida, com ignore conferido; informar Client ID/Secret diretamente no computador, nunca nesta conversa.
2. Iniciar MCP e chamar `start_oauth`; o sistema deverá abrir listener HTTPS, gerar `state` e PKCE S256/verifier antes de abrir o navegador. O contrato oficial inclui esses parâmetros de autorização e o verifier na troca quando PKCE estiver ativo.[4]
3. Você confere domínio oficial `auth.mercadolivre.com.br`, conta e permissões, e consente pessoalmente. O navegador retorna à URI exata; não copiar a URL de retorno para chat, capturas ou logs.[4]
4. O receptor valida rota, expiração e `state`; troca o código pelo POST form encoded de `/oauth/token`, consulta `/users/me` e só declara conectado após validar identidade e persistir tokens no cofre nativo. POST e consulta de identidade são documentados; a ordem segura/cofre é decisão do PRD.[4]
5. Encerrar listener e descartar transação. Refresh token é de uso único e rotativo; nenhuma reapresentação automática após timeout de resultado incerto.[4] Reinício/renovação/ausência de vazamentos serão evidências da Sprint 2, não marcadas agora.

## Situação e entrada da Sprint 1

**Requisitos essenciais documentados:** escopo de oito ferramentas, arquitetura mínima, leitura comercial, TLS, state/PKCE, cofre, limites de orçamento e tratamento explícito de dados incompletos. **Viabilidade local ainda não comprovada:** cadastro da candidata e HTTPS confiável dependem das etapas A–C. Pesquisa não equivale a grant/autorização real.

Para encerrar integralmente a Sprint 0 faltam as comprovações A–C e a resolução/decisão explícita sobre as lacunas técnicas de S0.10/S0.12; S0.08 é condicional. Elas permanecem abertas, com responsáveis separados acima. Uma observação em poucas páginas da conta não comprova um teto universal nem a retenção máxima.

O PRD permite iniciar **somente a fundação** da Sprint 1 com credenciais pendentes e D02 formalmente bloqueada. Para isso não é necessário OAuth real, deploy ou resolver toda a API comercial: é necessário você aceitar os limites/pendências registrados e autorizar expressamente a Sprint 1. Isso não marca Sprint 0 como integralmente concluída. Para prosseguir sem essa ressalva, primeiro comprovar a solução local e esclarecer as lacunas externas. Nesta entrega não se alterou nenhum checkbox nem se executou tarefa da Sprint 1.

**Próximo passo acompanhado:** etapa A, conferir a aplicação e as opções reais. Depois validar o cadastro da URI candidata; só então decidir instalação de certificado. Aguardar retorno de Felipe antes de qualquer execução local sensível ou avanço de sprint.

## Sources

[1] https://developers.mercadolivre.com.br/pt_br/gerenciamento-de-vendas
[2] https://developers.mercadolivre.com.br/pt_br/recurso-visits
[3] https://developers.mercadolivre.com.br/pt_br/crie-uma-aplicacao-no-mercado-livre
[4] https://developers.mercadolivre.com.br/pt_br/autenticacao-e-autorizacao
[5] https://developers.mercadolibre.com/en_us/visits
[6] https://developers.mercadolibre.com/en_us/visits-resource
[7] https://developers.mercadolibre.com/es_ar/recurso-de-visitas
[8] https://developers.mercadolibre.com/en_us/limits-on-pagination-and-bulk-extraction-in-searches
[9] https://developers.mercadolibre.com.ar/es_ar/gestiona-ventas
[10] https://raw.githubusercontent.com/FiloSottile/mkcert/master/README.md
[11] https://developers.mercadolivre.com.br/pt_br/permissoes-funcionais
