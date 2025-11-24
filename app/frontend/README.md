### `config` and `global` files

**index.html :** The root HTML file that loads your React app and mounts it into the `#root` div. 

**package.json :** Defines project metadata, dependencies, scripts, and tooling configuration. 

**package-lock.json :** Auto-generated lockfile that records the exact versions of installed npm dependencies. 

**tsconfig.app.json :** TypeScript configuration for the frontend application source code under `src/`. 

**tsconfig.json :** Root TypeScript config that references the app config and node config. 

**tsconfig.node.json :** TypeScript config specifically for Node/Vite config files. 

**vite.config.ts :** Vite's configuration file that sets up plugins and bundler behavior for the project.

---


### `/src` folder
Inside here lie the actual frontend React components and their css styling

**index.css :** Global styling file that defines theme colors, layout basics, and shared app-wide styles. 

**main.tsx :** Entry point of the React app that mounts the root `<App />` component into the DOM.

**types.tsx :** Contains TypeScript type definitions/interfaces used across components.

**vite-env.d.ts :** Vite-generated TypeScript declarations enabling support for Vite-specific features.

**App.css :** Styling specific to the main App layout and its UI elements. 

**App.tsx :** The main application component that renders controls, scheduler info, table area, and blocklist.

**components/ProxyTable.css :** Styling for the proxy table UI, including sorting/filtering controls and row formatting. 

**components/ProxyTable.tsx :** Component responsible for displaying proxy data in a responsive, sortable, filterable table.

---
