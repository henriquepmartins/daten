# Homebrew tap for `daten`

Esta pasta eh um template pronto para ser movido para um repositório separado chamado `homebrew-tap`.

## Estrutura esperada

```text
homebrew-tap/
  Formula/
    daten.rb
```

## Fluxo

1. Garanta que a tag `vX.Y.Z` ja exista no GitHub.
2. Rode:

```bash
uv run python scripts/render_homebrew_formula.py
```

3. Copie o conteudo desta pasta para o repositório do tap.
4. O install final sera:

```bash
brew install henriquepmartins/tap/daten
```
