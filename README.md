# ANVIL — Precision Brew Equipment Catalog

A vanilla-JS single-page e-commerce catalog built for the Full-Stack
Deployment & Project Architecture capstone. No framework, no build
tooling required to run it — just static files.

## Architecture

```
capstone/
├── index.html          shell: header, nav, #app mount point
├── css/styles.css       design tokens + all component styles
├── js/
│   ├── data.js          product data (mock API layer)
│   ├── state.js          cart state + localStorage + pub-sub
│   ├── router.js         hash-based client-side router
│   ├── utils.js          debounce, toast, formatting helpers
│   ├── main.js           entry point — wires routes to views
│   └── views/
│       ├── catalog.js    product grid, search, category filter
│       ├── product.js    product detail + add-to-cart
│       └── cart.js       cart line items + checkout summary
├── build.py              dependency-free minify/bundle script
└── dist/                 production build (generated)
```

Each module has one job and imports only what it needs — swapping
`data.js` for a real `fetch()` call to a backend wouldn't require
touching the router, views, or state module.

### Routing

`router.js` matches `location.hash` against registered patterns
(`/`, `/product/:id`, `/cart`) with no page reloads. Links use
`data-link` + a `#/...` href so normal `<a>` tags double as router
links — no click handlers needed on every link.

### State

`state.js` is the single source of truth for the cart. It persists
to `localStorage` on every change and uses a tiny pub-sub
(`onCartChange`) so the header cart badge and the cart view both
react to state changes without knowing about each other.

### Performance / asset optimization

- Product art is inline SVG (a few hundred bytes each) instead of
  raster photos — zero image requests, crisp at any size.
- Cards fade in via `IntersectionObserver` as they enter the
  viewport instead of animating a whole long grid at once.
- Search input is debounced (180ms) to avoid re-rendering the grid
  on every keystroke.
- `build.py` strips comments/whitespace from the CSS and concatenates
  all JS modules into a single minified bundle, cutting the
  combined JS+CSS payload by ~19% and dropping it to a single
  `<script>` request instead of 8 module fetches.

## Running locally

ES modules require a real HTTP origin (browsers block `import` over
`file://`), so serve the source folder rather than double-clicking
`index.html`:

```bash
cd capstone
python3 -m http.server 8000
# then open http://localhost:8000
```

Or run the production build the same way:

```bash
python3 build.py        # writes dist/
cd dist
python3 -m http.server 8000
```

## Deploying

The `dist/` folder is a plain static site — any static host works.
None of these steps run in this sandbox (no network access here),
but each takes under two minutes on your machine:

### Option A — Netlify (drag and drop, no CLI)
1. Go to app.netlify.com/drop
2. Drag the `dist/` folder onto the page
3. Netlify assigns a live `*.netlify.app` URL immediately

### Option B — Vercel (CLI)
```bash
npm i -g vercel
cd dist
vercel --prod
```

### Option C — GitHub Pages
1. Push the repo (or just `dist/`) to a GitHub repository
2. Repo Settings → Pages → set source to the branch/folder containing
   `dist/`
3. GitHub publishes it at `https://<user>.github.io/<repo>/`

### Option D — Render (static site)
1. New → Static Site → connect the repo
2. Build command: `python3 build.py`
3. Publish directory: `dist`

Any of these gives a public HTTPS URL with no server-side code to
maintain, since the whole app is static files plus client-side
JavaScript.
