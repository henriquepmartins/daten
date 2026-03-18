# Releasing `daten`

## PyPI

1. Crie o projeto `daten` no PyPI.
2. Configure Trusted Publishing para este repositório no PyPI.
3. Rode localmente:

```bash
uv sync --extra dev
uv run pytest
uv build --no-sources
```

4. Faça uma tag semantica:

```bash
git tag v0.1.0
git push origin v0.1.0
```

5. O workflow `publish.yml` vai buildar e publicar o pacote.

Se quiser publicar manualmente, rode:

```bash
uv publish --token "$PYPI_API_TOKEN"
```

## Homebrew tap

1. Garanta que a tag `vX.Y.Z` ja exista no GitHub.
2. Gere ou atualize a formula:

```bash
uv run python scripts/render_homebrew_formula.py
```

3. Copie a pasta `homebrew-tap/` para um repositório separado chamado `homebrew-tap`.
4. O install final fica:

```bash
brew install henriquepmartins/tap/daten
```
