import { defineConfig, globalIgnores } from "eslint/config"
import nextCoreWebVitals from "eslint-config-next/core-web-vitals"
import nextTypeScript from "eslint-config-next/typescript"

export default defineConfig([
  ...nextCoreWebVitals,
  ...nextTypeScript,
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Ignore non-source / heavy directories so `eslint .` does not traverse them
  // (traversing backend/.venv, .pnpm-store, datasets, and ML artifacts caused
  // an out-of-memory crash). These contain no lintable frontend source.
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "node_modules/**",
    ".pnpm-store/**",
    "backend/**",
    "dataset for training/**",
    "docs/**",
    "public/**",
    "playwright-report/**",
    "test-results/**",
    "coverage/**",
  ]),
])
