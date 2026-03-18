# daten

CLI em Python para inicializar projetos de ciencia de dados e ML usando `uv`.

## Instalacao

```bash
uv tool install daten
```

No macOS com Homebrew, a distribuicao recomendada fica em um tap proprio:

```bash
brew install seu-user/tap/daten
```

## Comandos

Se estiver desenvolvendo localmente:

```bash
uv run daten doctor
uv run daten init meu-projeto
```

## Templates

- `notebook`: ambiente para EDA, estudos e treinos simples.
- `production`: API de inferencia tabular com estrutura enxuta para uso real.

## Desenvolvimento

```bash
uv sync --extra dev
uv run pytest
uv build --no-sources
```

## Publicacao

- PyPI: veja [docs/RELEASING.md](docs/RELEASING.md)
- Homebrew tap: veja [homebrew-tap/README.md](homebrew-tap/README.md)
