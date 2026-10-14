import { Opik } from "opik";

export const PROJECT_NAME = "openai-ts-museum-visitor-desk";

// One Opik client for the app. Every trace it creates lands in this project;
// without an explicit name traces would go to "Default Project".
export const opik = new Opik({ projectName: process.env.OPIK_PROJECT_NAME ?? PROJECT_NAME });
