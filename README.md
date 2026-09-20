# iGEM dry-lab wiki framework

This branch contains a zero-dependency, responsive static HTML framework for the
project's dry-lab story. It intentionally uses editorial placeholders instead of
unreviewed scientific claims or results.

## Preview locally

From the repository root:

```bash
python -m http.server 8000
```

Open `http://localhost:8000/`.

The page also works when `index.html` is opened directly from the filesystem.

## Structure

```text
index.html              Semantic page structure and placeholder content
assets/css/site.css     Responsive visual system, print styles, accessibility
assets/js/site.js       Mobile navigation, scroll state, reveal, and tabs
.nojekyll               Keep static assets unchanged on GitHub Pages
```

## Content workflow

Replace placeholders in this order:

1. Final system overview and construct diagram.
2. Candidate-design figures and interactive explorer.
3. Structural-screening results and claim boundaries.
4. M3 recruitment and M4 pathway model contracts.
5. Engineering iterations and wet-lab feedback.
6. Claim–evidence table, software release, artifacts, and citations.

Every major figure should retain the four-part caption block: what it shows,
what it does not show, why it changed the design, and links to data/code.

## Deployment note

This branch is ready for static hosting. Publishing it through GitHub Pages may
still require enabling Pages in the repository settings; that setting is not
stored in this branch.
