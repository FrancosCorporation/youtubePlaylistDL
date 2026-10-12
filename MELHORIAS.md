# MELHORIAS — youtubePlaylistDL

> **Análise inicial:** 2026-10-05 · **Atualizado:** 2026-10-11 · Python 3.11+ · branch `master`
> O programa continua pequeno: um CLI para playlist, MP4 progressivo e MP3.

## 0. Como usar este documento

1. Resolva P0 antes de P1 e P2.
2. Marque cada item ao implementar e rode as verificações estáticas indicadas.
3. Não baixe conteúdo sem autorização; consulte os Termos do YouTube.
4. TEST-01 permanece pendente; não foram criados nem executados testes nesta rodada.

## 1. Diagnóstico executivo

O script antigo dependia de `time.clock`, raspava HTML da playlist com regex, criava caminhos a partir do título e chamava FFmpeg/LAME via shell. Também não fixava a dependência nem explicava a instalação dos conversores.

As correções desta rodada substituem o scraper pelo `Playlist` de `pytubefix`, fixam a dependência, validam os hosts/IDs, limitam o tempo de rede, usam nomes numéricos e executam os conversores sem shell.

## 2. Tabela de prioridades

| ID | Item | Severidade | Estado |
|---|---|---|---|
| BUG-01 | `time.clock` removido em Python moderno | P0 | Implementado |
| BUG-02 | Nome de arquivo baseado em título externo | P0 | Implementado |
| BUG-03 | Scraper frágil e sem limite de rede | P1 | Implementado |
| SEC-01 | Dependência não fixada e sem manutenção recente | P1 | Implementado com `pytubefix` |
| SEC-02 | Execução de conversores via shell | P2 | Implementado |
| SEC-03 | URL final usando HTTP | P2 | Implementado |
| TEST-01 | Sem testes unitários | P2 | Pendente |
| DEVOPS-01 | Sem lint/CI | P2 | Implementado; CI não executa testes |
| DEVOPS-02 | Python 3.10 sem suporte de segurança e CI em uma versão | P1 | Implementado: Python 3.11+ e matriz 3.11/3.14 |
| DOC-01 | Requisitos e limitações legais desatualizados | P2 | Implementado |

## 3. Segurança

### SEC-01 · Dependência instável e sem pin · [P1]

- **Arquivo:** `requirements.txt`
- **Evidência:** `pytube` no PyPI continua na versão 15.0.0, publicada em 2023; mudanças do YouTube causam falhas na extração.
- **Mudança:** usar `pytubefix==11.2.0`, publicada em 2026, mantendo uma versão exata.
- **Aceite:** ambiente reproduzível com parser de playlist e download progressivo.
- **Verificação:** `python -m pip install -r requirements.txt --dry-run`

### SEC-02 · Conversores chamados pelo shell · [P2]

- **Arquivo:** `ytPlaylistDL.py`
- **Evidência:** o código antigo concatenava nomes e chamava `os.system`.
- **Mudança:** usar `subprocess.run` com argumentos separados, sem shell; checar `ffmpeg` e `lame` antes da rede.
- **Aceite:** ausência dos executáveis gera uma mensagem clara; nomes de saída não são interpretados pelo shell.
- **Verificação:** `rg -n 'os\.system|subprocess\.run|shutil\.which' ytPlaylistDL.py`

### SEC-03 · URLs de vídeo em HTTP · [P2]

- **Arquivo:** `ytPlaylistDL.py`
- **Evidência:** o código antigo prefixava URLs com `http://www.youtube.com/`.
- **Mudança:** validar host e ID e gerar links canônicos `https://www.youtube.com/watch?v=...`.
- **Aceite:** links da playlist usam HTTPS e hosts externos são recusados.
- **Verificação:** `rg -n 'http://www\.youtube|https://www\.youtube' ytPlaylistDL.py`

## 4. Bugs e defeitos funcionais

### BUG-01 · `time.clock` foi removido · [P0]

- **Arquivo:** `ytPlaylistDL.py`, `ProgressBar`
- **Evidência:** `time.clock()` não existe em Python 3.8+ e a barra também podia dividir por zero no primeiro bloco.
- **Mudança:** medir com `time.perf_counter()` e limitar taxa/tempo restante a valores seguros.
- **Aceite:** barra de progresso funciona em Python moderno.
- **Verificação:** `rg -n 'time\.clock|perf_counter' ytPlaylistDL.py`

### BUG-02 · Título do vídeo era usado como caminho · [P0]

- **Arquivo:** `ytPlaylistDL.py`, `download_Video_Audio`
- **Evidência:** `yt.title` vinha do uploader e entrava em `rename` e argumentos de shell.
- **Mudança:** usar nomes `0000-VIDEO_ID.mp4`/`.mp3` e enviar caminhos como argumentos separados.
- **Aceite:** `/`, `:`, `?` ou Unicode no título não altera os caminhos locais.
- **Verificação:** `rg -n 'yt\.title.*(rename|system)|os\.rename' ytPlaylistDL.py`

### BUG-03 · Extração de playlist sem timeout · [P1]

- **Arquivo:** `ytPlaylistDL.py`, `getPlaylistVideoUrls`
- **Evidência:** o scraper com regex era frágil e `urlopen` não tinha limite de espera.
- **Mudança:** usar `pytubefix.Playlist`, normalizar entrada HTTPS e definir timeout de rede de 30 segundos; downloads têm até três tentativas.
- **Aceite:** lista de vídeos vem da biblioteca fixada e falha de rede termina com mensagem útil.
- **Verificação:** `rg -n 'Playlist\(|setdefaulttimeout|NETWORK_TIMEOUT_SECONDS|max_retries' ytPlaylistDL.py`

## 5. Qualidade: testes

### TEST-01 · Funções sem cobertura · [P2]

- **Arquivo:** *(ausente)* `tests/`
- **Evidência:** funções de formatação e validação não têm testes offline.
- **Mudança:** futuramente testar IDs, normalização de URLs, formatação e erros de configuração sem rede.
- **Aceite:** suíte unitária passa sem chamar YouTube.
- **Estado:** pendente; não adicionada nem executada nesta rodada.
- **Verificação futura:** `python -m pytest -q`

## 6. DevOps / Infra

### DEVOPS-01 · Sem lint ou CI · [P2]

- **Arquivo:** `.github/workflows/ci.yml`, `requirements-dev.txt`, `pyproject.toml`
- **Evidência:** não havia verificações automáticas.
- **Mudança:** CI instala dependências fixadas e executa `py_compile` e Ruff em Python 3.11 e 3.14.
- **Aceite:** erro de sintaxe ou lint bloqueia push/pull request.
- **Verificação local:** `python -m py_compile ytPlaylistDL.py && ruff check ytPlaylistDL.py`

### DEVOPS-02 · Versão mínima Python sem suporte e CI estreita · [P1]

- **Arquivos:** `README.md`, `pyproject.toml`, `.github/workflows/ci.yml`
- **Evidência:** o projeto dizia aceitar Python 3.10, cujo ciclo de suporte terminou em 2026-10-01. O workflow só verificava Python 3.14 e usava `ubuntu-latest`, sem fixar o runner.
- **Mudança:** exigir Python 3.11+, alinhar o alvo do Ruff e verificar sintaxe/lint em Python 3.11 e 3.14 sobre Ubuntu 24.04.
- **Referência:** [Python 3.10.22 chegou ao fim de vida em 2026-10-01](https://www.python.org/downloads/release/python-31022/).
- **Validação:** sintaxe em Python 3.14 e Ruff local passaram; a CI confirmará Python 3.11 e 3.14 após o push. Não adicionei nem executei testes.

## 7. Documentação

### DOC-01 · Requisitos e uso desatualizados · [P2]

- **Arquivo:** `README.md`
- **Evidência:** pedia Python 3.4.1 e não documentava conversores nem restrições de uso.
- **Mudança:** documentar Python 3.11+, venv, dependência fixada, FFmpeg/LAME, comandos e Termos do YouTube.
- **Aceite:** a instalação e a autorização de download estão explícitas.
- **Verificação:** `rg -n 'Python 3\.11|requirements\.txt|FFmpeg|LAME|Terms of Service' README.md`

## 8. Ordem de execução

1. **Wave 1 — P0:** BUG-01 e BUG-02.
2. **Wave 2 — P1:** BUG-03 e SEC-01.
3. **Wave 3 — P2:** SEC-02, SEC-03, DEVOPS-01 e DOC-01.
4. TEST-01 segue pendente.

## 9. Fora de escopo e riscos

- Não contornar proteções nem baixar conteúdo sem autorização; os Termos restringem downloads salvo autorização do serviço, permissão aplicável ou base legal pertinente.
- Não adicionar download paralelo, GUI ou formatos além de MP4, WAV temporário e MP3.
- O YouTube pode alterar seus endpoints; uma versão fixada melhora reprodução, mas não impede futuras quebras.
- O modo de rede é um timeout global do processo, adequado ao CLI sequencial.

## 10. Definição de pronto

- [x] BUG-01 — `perf_counter` e taxa segura.
- [x] BUG-02 — nomes por índice e ID; nenhum rename/shell com título.
- [x] BUG-03 — `pytubefix.Playlist` com timeout e tentativas limitadas.
- [x] SEC-01 — `pytubefix` fixado.
- [x] SEC-02 — subprocesso sem shell e verificação de executáveis.
- [x] SEC-03 — URL canônica HTTPS e host validado.
- [ ] TEST-01 — testes offline pendentes.
- [x] DEVOPS-01 — CI estática com sintaxe e Ruff.
- [x] DEVOPS-02 — mínimo Python 3.11 e matriz de versões suportadas.
- [x] DOC-01 — README atualizado.

**Validação estática:**

```bash
python -m py_compile ytPlaylistDL.py
ruff check ytPlaylistDL.py
python -m pip install -r requirements-dev.txt --dry-run
git diff --check
```

*Plano atualizado em 2026-10-11. TEST-01 permanece pendente; OAuth/playlist e downloads reais não foram exercitados.*
