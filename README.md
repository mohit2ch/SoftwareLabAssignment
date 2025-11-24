# SoftwareLabAssignment

## Automatic collection and filtering of Proxy server addresses 

This project automates the collection and filtering of proxy server addresses using Python. It performs web scraping to gather proxy addresses from multiple online sources, then tests each proxy to verify its functionality and measures key metrics such as response time. The project filters out non-working or slow proxies to ensure reliability. Finally, it presents the validated proxy list along with detailed statistics like location and response time through a user friendly Flask web interface.

## Project Architecture

![project-architecture-image](./project_architecture.png)

## File-wise description

### Backend

**main.py**: This file initializes a Flask web application with CORS that exposes API endpoints to control and retrieve status from a ProxyScheduler and its list of validated proxy items.

**models.py**: This file defines a data model class ProxyItem to structure proxy server information (IP, port, protocol, validation status, etc.) and provides methods for string representation and uniqueness checks.

**proxy_scheduler.py**: This file defines the ProxyScheduler class, which uses background threading to periodically fetch, validate, and store a collection of ProxyItem objects.

**proxy_validator.py**: This file contains functions to parallelly validate a list of proxy servers using a ThreadPoolExecutor, checking their connectivity, response time, location, against specified URLs using the requests library.

**providers directory**: This directory contains web scraping files that scrape various free proxy address websites using beautiful-soup.

### Frontend
#### `config` and `global` files

**index.html :** The root HTML file that loads your React app and mounts it into the `#root` div. 

**package.json :** Defines project metadata, dependencies, scripts, and tooling configuration. 

**package-lock.json :** Auto-generated lockfile that records the exact versions of installed npm dependencies. 

**tsconfig.app.json :** TypeScript configuration for the frontend application source code under `src/`. 

**tsconfig.json :** Root TypeScript config that references the app config and node config. 

**tsconfig.node.json :** TypeScript config specifically for Node/Vite config files. 

**vite.config.ts :** Vite's configuration file that sets up plugins and bundler behavior for the project.

---


#### `/src` folder
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
