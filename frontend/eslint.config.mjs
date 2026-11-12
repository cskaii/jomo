import { defineConfig, globalIgnores } from "eslint/config";
import js from "@eslint/js";
import nextPlugin from "@next/eslint-plugin-next";
import react from "@eslint-react/eslint-plugin";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y-x";
import tseslint from "typescript-eslint";
import globals from "globals";

// Keep React Hooks responsible for compiler checks instead of reporting them twice.
const hooksOwnedRules = Object.fromEntries(
  Object.keys(reactHooks.configs.flat.recommended.rules)
    .filter(name => Object.hasOwn(react.rules, name.replace("react-hooks/", "")))
    .map(name => [name.replace("react-hooks/", "@eslint-react/"), "off"]),
);

const eslintConfig = defineConfig([
  globalIgnores([
    ".next*/**", ".cache/**", "out/**", "build/**", ".pnpm-store/**", "next-env.d.ts",
  ]),
  {
    files: ["**/*.{js,mjs,cjs,jsx,ts,tsx}"],
    extends: [js.configs.recommended, tseslint.configs.recommended],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
  {
    files: ["src/**/*.{jsx,tsx}"],
    extends: [react.configs["recommended-typescript"], reactHooks.configs.flat.recommended, jsxA11y.configs.recommended],
    plugins: { "@next/next": nextPlugin },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
      ...hooksOwnedRules,
      // Preserve the project's existing ref names; this is a naming preference.
      "@eslint-react/naming-convention-ref-name": "off",
    },
    settings: { "react-x": { version: "19.3.0" } },
  },
  {
    files: ["src/features/prototype/GardenCarousel.tsx"],
    rules: {
      // This named carousel group is focusable specifically for arrow-key scrolling.
      "jsx-a11y-x/no-noninteractive-tabindex": ["error", { roles: ["group"] }],
      "jsx-a11y-x/no-noninteractive-element-interactions": ["error", { div: ["onKeyDown"] }],
    },
  },
  {
    files: ["src/features/prototype/GardenNavigation.tsx"],
    rules: {
      // The native dialog supports Escape and uses clicks only to dismiss its backdrop.
      "jsx-a11y-x/no-noninteractive-element-interactions": ["error", { dialog: ["onClick", "onKeyDown"] }],
    },
  },
  {
    files: ["tests/**/*.cjs"],
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
]);

export default eslintConfig;
