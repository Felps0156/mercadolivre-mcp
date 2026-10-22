# mercadolivre-mcp

MCP local planejado para o Hermes consultar e analisar a conta do Mercado Livre da Dias Moto Peças. A fonte de requisitos é `PRD.md`. No momento desta inspeção, existem apenas esse PRD e uma `.venv/`: não há código de aplicação, README, manifesto de dependências, lockfile, configuração de lint, CI ou repositório `.git` local. A arquitetura abaixo é especificação, não implementação observada.

## Escopo e execução do trabalho

- Consultar `PRD.md` antes de implementar; seguir as sprints 0–6 e suas dependências (seção 16).
- V1: uma conta, leitura comercial, FastMCP via `stdio`, cálculos determinísticos em Python; nenhum LLM dentro do MCP.
- Exatamente oito ferramentas previstas: `get_seller_profile`, `list_orders`, `list_seller_items`, `get_item_details`, `get_item_visits`, `get_sales_summary`, `get_sales_comparison`, `start_oauth`.
- Não adicionar escrita comercial, Ads, NetOne, banco de dados, frontend, Docker, jobs ou ferramentas MCP extras.
- Testes automatizados, `pytest` e arquivos `test_*.py` estão expressamente fora da V1. A validação é manual.
- Não executar commits/pushes sem instrução expressa. Não marcar tarefas ou sprints como concluídas sem evidências; registrar bloqueios e validação real pendente.

## Ambiente e comandos

- Alvo especificado: Windows, Python 3.13. A `.venv/pyvenv.cfg` existente registra Python 3.12.10; ela não comprova compatibilidade com o alvo.
- Dependências previstas, ainda sem versões verificadas: FastMCP, requests, Pydantic, python-dotenv, keyring e tzdata. Não instalar LangChain por padrão.
- Os comandos abaixo são transcritos do PRD, seção 14, para PowerShell na raiz. São planejados, não comandos já validados; `requirements.txt` e `src.server` ainda não existem.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.server
```

- O PRD permite usar diretamente `.\.venv\Scripts\python.exe` quando a ativação for bloqueada, sem relaxar amplamente a política do Windows.
- Não há comando de build, teste ou lint definido no estado atual. Não inventar invocações nem apresentar os comandos planejados como executáveis hoje.
- Na implementação, fixar em `requirements.txt` somente versões verificadas e documentar a instalação real no README.

## Organização e contratos previstos

- `src/server.py`: composição, configuração pela raiz, logs e ciclo de vida; sem métricas.
- `src/client.py`: `requests.Session`, allowlist, timeouts, retries e paginação.
- `src/auth.py`: OAuth, callback, cofre, locks e renovação.
- `src/tools.py`: registro das oito ferramentas e cálculos compartilhados; receber a instância FastMCP por função de registro para evitar import circular.
- `src/schemas.py`: entradas/saídas Pydantic, erros, dinheiro e metadados. `src/__init__.py` não deve chamar a rede.
- Não há convenções de código ou commits observáveis ainda; os limites desta seção são requisitos do PRD.
- Envelope: `success`, `data`, `period`, `metadata`, `warnings`, `error`. Erros de domínio/API usam esse contrato, sem traceback ao Hermes.
- IDs numéricos externos são strings; IDs de anúncio brasileiro seguem `MLB` + dígitos, com propriedade validada separadamente.
- Datas públicas `YYYY-MM-DD`, fim inclusivo convertido para intervalo interno semiaberto em `America/Sao_Paulo`.
- Dinheiro com `Decimal`, serializado como texto e moeda explícita; não somar moedas diferentes nem substituir dado ausente por zero.
- Metodologia `created_paid_v1`: coorte pela criação do pedido, elegibilidade pelo estado observado; preço transacional das linhas, nunca preço atual do anúncio. Aplicar as exceções de reembolso da seção 10.
- Agregados percorrem a população completa e deduplicam por `order_id`; `top_n` limita apenas rankings. Coleta incompleta exige `PARTIAL_DATA`, `success=false` e métricas definitivas nulas.

## Configuração e armadilhas

- As variáveis são propostas, não implementadas: consultar a tabela completa na seção 14. OAuth depende de `ML_CLIENT_ID`, `ML_CLIENT_SECRET`, `ML_REDIRECT_URI` e configuração local de callback/certificado; PKCE deve refletir a aplicação real.
- Callback exige viabilidade de HTTPS e URI exata aprovada no portal; host, porta e certificado ainda não estão definidos. Não presumir `http://localhost`, adicionar túnel automaticamente ou pedir código/token no chat.
- Tokens ficam no cofre nativo do Windows via keyring, nunca JSON plaintext. Hermes e cofre devem usar o mesmo usuário; apenas um processo por perfil de credenciais.
- Refresh token rotativo não pode ser reapresentado automaticamente após timeout de resultado incerto. Proteger sessão/renovação com locks; não paralelizar chamadas comerciais.
- `stdout` é exclusivo do MCP; logs em `stderr`. Servidor stdio pode aguardar mensagens sem interface visível.
- Carregar `.env` pela raiz do projeto; a futura configuração Hermes deve usar Python absoluto da venv e `-m src.server`, sem presumir suporte a chaves de diretório de trabalho.
- API comercial fixa em `https://api.mercadolibre.com`, GETs permitidos por allowlist; POST somente para `/oauth/token`. TLS ativo e redirects autenticados desabilitados.
- O PRD prevê `/items/bulk` com `status_code` por elemento e seleção `body.<campo>`; reconfirmar documentação vigente antes de implementar, sem copiar parser do multiget antigo.
- Scan de itens não usa offset e não se aplica a pedidos. Limites internos do PRD não são limites oficiais da API; reconfirmar retenção, permissões e paginação.
- Ao criar `.gitignore`, excluir `.env`, `.venv`, caches, runtime e material sensível do callback; `.env.example` contém somente placeholders. Não persistir respostas comerciais brutas.

## Verificação manual

- Usar os cenários VM01–VM17 da seção 17 e os aceites da sprint correspondente; não criar suíte automatizada.
- Registrar no futuro README: ID, data/hora, referência do código, ambiente, procedimento, esperado, observado e situação; somente evidências sanitizadas.
- Distinguir revisão de código, exercício sintético e consulta real da API. Não provocar 429/falhas de produção para obter evidência.
- Sem conta autorizada, callback comprovado e jornadas reais no Hermes, não declarar “V1 validada para uso local”.
