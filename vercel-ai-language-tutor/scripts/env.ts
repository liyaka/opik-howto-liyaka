import { config } from "dotenv";
import path from "node:path";

// Loads this folder's .env, then the repo-root .env; neither overrides variables already set.
export function loadEnv() {
  config({ path: path.resolve(process.cwd(), ".env"), quiet: true });
  config({ path: path.resolve(process.cwd(), "../.env"), quiet: true });
}
