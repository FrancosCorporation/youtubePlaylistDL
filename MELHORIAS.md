# MELHORIAS — youtubePlaylistDL

> **Gerado por análise de código em 2026-10-05** · Stack: Python + pytube + urllib + ffmpeg/lame · Branch: main

Plano de melhoria do projeto `youtubePlaylistDL` (script único `ytPlaylistDL.py`, ~175 linhas), gerado exclusivamente a partir de leitura direta do código, do `README.md` e do `.gitignore` em 2026-10-05. Nenhum arquivo:linha foi inventado — todos os itens usam somente os fatos da análise recebida.

## 0. Como usar este documento

- Cada item tem um ID estável (`BUG-*`, `SEC-*`, `TEST-*`, `DEVOPS-*`, `DOC-*`) e uma severidade: **[P0]** (bloqueia execução / corrige primeiro), **[P1]** (importante, funcional ou de reprodutibilidade), **[P2]** (higiene, hardening e dívida técnica).
- Cada item traz 6 campos obrigatórios: **Arquivo:** (onde mexer), **Evidência:** (fato observado no código), **Impacto:** (por que importa), **Mudança:** (o que fazer), **Aceite:** (critério de pronto do item), **Verificação:** (comando em bloco `bash` para conferir).
- Ordem recomendada: Wave 1 (P0) → Wave 2 (P1) → Wave 3 (P2). Ver detalhes em `## 8. Ordem de execução (waves)`.
- Escopo: somente `ytPlaylistDL.py`, `README.md`, `requirements.txt` (a criar), testes e CI. Fora de escopo em `## 9. Fora de escopo / riscos`.
- Convenção de verificação: comandos `grep` vazios significam "problema eliminado"; comandos `cat`/`ls`/`pytest` significam "artefato existe e passa".

## 1. Diagnóstico executivo

Projeto mínimo e legível: um único script `ytPlaylistDL.py` (~175 linhas) que baixa vídeos/áudios de uma playlist do YouTube. É um fork de repositório externo (há merge de PR do autor original no histórico). Não há `requirements.txt`, testes ou CI; o `.gitignore` só tem `*.iml`/`.idea`.

### O que está bem

| Aspecto | Evidência |
|---|---|
| Escopo pequeno e auditável | Único código: `ytPlaylistDL.py` (~175 linhas) |
| Funções puras isoláveis para teste | `getHumanTime`, `bytestostr`, `getFinalVideoUrl`, `getPlaylistUrlID` não precisam de rede |
| Fluxo principal simples | `getPageHtml` → `getPlaylistVideoUrls` → `download_Video_Audio` em `ytPlaylistDL.py` |
| Criação de diretório tolerante | `os.makedirs(directory, exist_ok=True)` em `ytPlaylistDL.py` |

### O que está quebrado

| Problema | ID | Severidade |
|---|---|---|
| `time.clock` removido no Python 3.8+, script não executa | BUG-01 | [P0] |
| `os.rename` com `yt.title` cru quebra em títulos com caracteres inválidos | BUG-02 | [P0] |
| Scraping de HTML com regex sem timeout/User-Agent | BUG-03 | [P1] |
| Dependência `pytube` sem pin (`pip3 install pytube` solto) | SEC-01 | [P1] |
| `os.system` com interpolação + binários externos `ffmpeg`/`lame` sem checagem | SEC-02 | [P2] |
| URL final construída com `http://` | SEC-03 | [P2] |
| Zero testes | TEST-01 | [P2] |
| Sem CI/lint | DEVOPS-01 | [P2] |
| `README.md` pede Python 3.4.1+ (2014, EOL) | DOC-01 | [P2] |

## 2. Tabela de prioridades

| ID | Título | Sev. | Arquivo |
|---|---|---|---|
| BUG-01 | time.clock removido no Python 3.8+, script não executa | [P0] | ytPlaylistDL.py:21 |
| BUG-02 | os.rename com yt.title cru quebra em títulos com caracteres inválidos | [P0] | ytPlaylistDL.py:129-136 |
| BUG-03 | scraping de HTML com regex sem timeout/User-Agent | [P1] | ytPlaylistDL.py:getPageHtml/getPlaylistVideoUrls |
| SEC-01 | dependência pytube sem pin | [P1] | (ausente) requirements.txt |
| SEC-02 | os.system com interpolação + binários externos sem checagem | [P2] | ytPlaylistDL.py:131-135 |
| SEC-03 | URL final construída com http:// | [P2] | ytPlaylistDL.py:getFinalVideoUrl |
| TEST-01 | zero testes | [P2] | (ausente) tests/ |
| DEVOPS-01 | sem CI/lint | [P2] | (ausente) .github/workflows/ |
| DOC-01 | README pede Python 3.4.1+ (2014, EOL) | [P2] | README.md |

## 3. Segurança

### SEC-01 · dependência pytube sem pin · [P1]

- **Arquivo:** (ausente) requirements.txt
- **Evidência:** `ytPlaylistDL.py` faz `from pytube import YouTube` sem pin de versão; o `README.md` manda `pip3 install pytube` solto. O `pytube` quebra com frequência por mudanças do YouTube.
- **Impacto:** Instalação não reproduzível: cada máquina pode pegar uma versão diferente do `pytube`, e quebras por mudanças do YouTube não são rastreáveis nem reversíveis.
- **Mudança:** Criar `requirements.txt` com `pytube==<versão testada>` (a versão que for validada manualmente) e atualizar o `README.md` para mandar `pip install -r requirements.txt`.
- **Aceite:** `pip install -r requirements.txt` reproduz o ambiente; a versão do `pytube` está pinada.
- **Verificação:**
```bash
cat requirements.txt
```

### SEC-02 · os.system com interpolação + binários externos sem checagem · [P2]

- **Arquivo:** ytPlaylistDL.py:131-135
- **Evidência:** `download_Video_Audio` monta `aud = 'ffmpeg -i '+str(file_no)+'.mp4'+' '+str(file_no)+'.wav'` e chama `os.system(aud)`, depois `os.system(final_audio)` com `lame`. `file_no` é índice (seguro), mas há shell via `os.system` sem `shlex` e dependência de binários externos `ffmpeg`/`lame` não declarados nem checados.
- **Impacto:** Uso de shell sem necessidade (risco de injeção se o padrão for copiado para entradas não seguras) e falha opaca quando `ffmpeg`/`lame` não estão instalados.
- **Mudança:** Trocar `os.system` com concatenação por `subprocess.run` com lista de args (sem shell) e checar `shutil.which('ffmpeg')` / `shutil.which('lame')` no início com erro claro; documentar a dependência no `README.md`.
- **Aceite:** Sem `os.system` com concatenação no arquivo; ausência de `ffmpeg`/`lame` gera mensagem de erro clara em vez de falha silenciosa.
- **Verificação:**
```bash
grep -n 'os.system' ytPlaylistDL.py
```

### SEC-03 · URL final construída com http:// · [P2]

- **Arquivo:** ytPlaylistDL.py:getFinalVideoUrl
- **Evidência:** `getFinalVideoUrl` constrói `'http://www.youtube.com/'` (http, não https).
- **Impacto:** URLs geradas usam transporte sem TLS; tráfego pode ser interceptado/modificado em vez de usar `https`.
- **Mudança:** Trocar o prefixo para `https://` em `getFinalVideoUrl`.
- **Aceite:** URLs de saída saem com `https`.
- **Verificação:**
```bash
grep -n 'http://www.youtube' ytPlaylistDL.py
```

## 4. Bugs e defeitos funcionais

### BUG-01 · time.clock removido no Python 3.8+, script não executa · [P0]

- **Arquivo:** ytPlaylistDL.py:21
- **Evidência:** `print_progress` contém `elapsed = int(time.clock() - start) + 1`. `time.clock` foi removido no Python 3.8, logo qualquer Python moderno levanta `AttributeError`.
- **Impacto:** O script não executa em qualquer Python moderno: a barra de progresso quebra com `AttributeError` ([P0], bloqueante total).
- **Mudança:** Trocar `time.clock()` por `time.perf_counter()` (ou `time.monotonic()`), mantendo o restante do cálculo de `elapsed`.
- **Aceite:** `print_progress` executa sem `AttributeError` em Python moderno.
- **Verificação:**
```bash
python3 -c "import time; print(hasattr(time,'clock'))"
grep -n time.clock ytPlaylistDL.py
```

### BUG-02 · os.rename com yt.title cru quebra em títulos com caracteres inválidos · [P0]

- **Arquivo:** ytPlaylistDL.py:129-136
- **Evidência:** `download_Video_Audio` faz `os.rename(yt.title+'.mp4', ...)` usando `yt.title` (título do vídeo, controlado pelo uploader) para construir nome de arquivo. Títulos com travessia/encoding estranho ou caracteres inválidos quebram o rename; o `except OSError` genérico engole o erro. `file_no` é índice (seguro).
- **Impacto:** Vídeos com títulos contendo `/`, `:`, `?` (ou outros caracteres inválidos no SO) baixam mas não renomeiam/convertam — falha silenciosa com `OSError` genérico engolido ([P0]).
- **Mudança:** Sanitizar o título (regex `[^\w\-. ]` ou `slugify`) antes de usar como nome de arquivo, e/ou usar o nome de arquivo retornado pelo download em vez de reconstruir a partir de `yt.title`.
- **Aceite:** Vídeo com título contendo `/ : ?` baixa e renomeia sem `OSError` engolido.
- **Verificação:**
```bash
grep -n 'yt.title' ytPlaylistDL.py
```

### BUG-03 · scraping de HTML com regex sem timeout/User-Agent · [P1]

- **Arquivo:** ytPlaylistDL.py:getPageHtml/getPlaylistVideoUrls
- **Evidência:** `getPlaylistVideoUrls` faz scraping de HTML com regex (frágil a mudanças do YouTube); `getPageHtml` usa `urllib` (`urlopen`) sem timeout e sem `User-Agent`.
- **Impacto:** Extração quebra a qualquer mudança no HTML do YouTube; sem timeout a falha de rede trava o script em vez de falhar rápido com mensagem clara ([P1]).
- **Mudança:** Adicionar timeout explícito no `urlopen` + `User-Agent`; considerar migrar a extração para `pytube.Playlist`.
- **Aceite:** Falha de rede falha rápido com mensagem clara em vez de travar.
- **Verificação:**
```bash
grep -n 'timeout\|User-Agent' ytPlaylistDL.py
```

## 5. Qualidade: testes

### TEST-01 · zero testes · [P2]

- **Arquivo:** (ausente) tests/
- **Evidência:** Sem testes, sem CI, sem tratamento de erro específico (bare `except` em download). Não há diretório de testes nem `pytest`/`unittest` no repositório.
- **Impacto:** Regressões (ex.: BUG-01, BUG-03, SEC-03) não são detectadas automaticamente; cada mudança no scraping ou no `pytube` exige teste manual.
- **Mudança:** Criar testes unitários puros (sem rede) para `getHumanTime`, `bytestostr`, `getFinalVideoUrl` e `getPlaylistUrlID` (não precisam de rede). Mínimo de 4 testes com `pytest`.
- **Aceite:** `pytest` com ≥4 testes passando, sem dependência de rede.
- **Verificação:**
```bash
python -m pytest -q
```

## 6. DevOps / Infra

### DEVOPS-01 · sem CI/lint · [P2]

- **Arquivo:** (ausente) .github/workflows/
- **Evidência:** Sem testes, sem CI. O `.gitignore` só tem `*.iml`/`.idea`; não há workflow, lint ou compilação automatizada.
- **Impacto:** Código quebrado (ex.: BUG-01) entra na branch sem barreira; estilo e erros de sintaxe não são checados automaticamente.
- **Mudança:** Criar workflow com `py_compile` + `ruff` + `pytest` para bloquear push quebrado.
- **Aceite:** Push quebrado é bloqueado pelo CI; `py_compile`, `ruff` e `pytest` executam a cada push/PR.
- **Verificação:**
```bash
ls .github/workflows/
```

## 7. Documentação

### DOC-01 · README pede Python 3.4.1+ (2014, EOL) · [P2]

- **Arquivo:** README.md
- **Evidência:** O `README.md` diz "needs Python 3.4.1+" (versão de 2014, EOL há anos) e manda `pip3 install pytube` solto, sem mencionar `ffmpeg`/`lame`.
- **Impacto:** Instrução desatualizada e não reproduzível do zero: usuário instala Python EOL e `pytube` flutuante, sem saber dos binários externos.
- **Mudança:** Atualizar para Python 3.10+, documentar `ffmpeg`/`lame`, `requirements.txt`, e limitações (ToS do YouTube).
- **Aceite:** Instrução funciona do zero em máquina limpa seguindo só o `README.md`.
- **Verificação:**
```bash
grep -ni 'python 3' README.md
```

## 8. Ordem de execução (waves)

- **Wave 1 — Desbloquear execução [P0]:** BUG-01 (`time.clock` → `time.perf_counter()`), BUG-02 (sanitizar `yt.title` antes do `os.rename`). Motivo: sem isso o script nem roda nem renomeia em Python moderno.
- **Wave 2 — Reprodutibilidade e rede [P1]:** SEC-01 (criar `requirements.txt` com `pytube` pinado), BUG-03 (timeout + `User-Agent` no `urlopen`; avaliar `pytube.Playlist`). Motivo: torna a instalação repetível e a falha de rede rápida e clara.
- **Wave 3 — Hardening e higiene [P2]:** SEC-02 (`subprocess.run` sem shell + `shutil.which('ffmpeg'/'lame')`), SEC-03 (`https`), TEST-01 (≥4 testes puros com `pytest`), DEVOPS-01 (workflow `py_compile` + `ruff` + `pytest`), DOC-01 (`README.md` para Python 3.10+ com `ffmpeg`/`lame`, `requirements.txt` e ToS). Motivo: fecha segurança, qualidade e documentação após o script voltar a funcionar.
- Dependências entre waves: Wave 2 depende da Wave 1 (só faz sentido pinar/testar rede com o script executando); Wave 3 depende das anteriores (testes e CI cobrem o código já corrigido).

## 9. Fora de escopo / riscos

- Não escalar para burlar proteções do YouTube; respeitar os Termos de Serviço (ToS) do YouTube — o plano cobre apenas download legítimo de conteúdo permitido, documentando as limitações no `README.md`.
- Não reescrever o extrator de playlist para APIs não oficiais ou técnicas anti-bloqueio; a migração sugerida é apenas para `pytube.Playlist` (uso suportado).
- Não adicionar download paralelo, GUI ou novos formatos além do fluxo atual `mp4` → `wav` → `mp3` (`ffmpeg`/`lame`).
- Risco: mudanças no HTML do YouTube ou no `pytube` podem requebrar BUG-03/SEC-01 mesmo após o fix — mitigado por `requirements.txt` pinado e testes puros.
- Risco: títulos com Unicode/controles ainda podem variar por SO mesmo após sanitização — mitigado por teste manual com títulos problemáticos.
- Risco: `ffmpeg`/`lame` ausentes ou com versões incompatíveis — mitigado por checagem com `shutil.which` e documentação.

## 10. Definição de pronto (DoD)

- [ ] `grep -n time.clock ytPlaylistDL.py` vazio e `print_progress` sem `AttributeError` (BUG-01).
- [ ] Título com `/ : ?` baixa e renomeia sem `OSError` (BUG-02).
- [ ] `grep -n 'timeout\|User-Agent' ytPlaylistDL.py` com ocorrências (BUG-03).
- [ ] `cat requirements.txt` mostra `pytube==<versão testada>` e `pip install -r requirements.txt` reproduz (SEC-01).
- [ ] `grep -n 'os.system' ytPlaylistDL.py` vazio; binários checados com erro claro (SEC-02).
- [ ] `grep -n 'http://www.youtube' ytPlaylistDL.py` vazio (SEC-03).
- [ ] `python -m pytest -q` com ≥4 testes passando sem rede (TEST-01).
- [ ] `ls .github/workflows/` existe e CI com `py_compile` + `ruff` + `pytest` verde (DEVOPS-01).
- [ ] `grep -ni 'python 3' README.md` indica Python 3.10+ com `ffmpeg`/`lame`, `requirements.txt` e ToS (DOC-01).
- [ ] `python3 /tmp/validate.py youtubePlaylistDL` retorna OK (11 seções, sem IDs duplicados, todos os 6 campos).

*Fim do plano. Gerado por leitura direta do código em 2026-10-05. Valide com `python3 /tmp/validate.py youtubePlaylistDL`.*
