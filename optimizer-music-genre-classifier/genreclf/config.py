"""Names and budgets shared by every module."""

import dotenv

# Picks up a .env in this folder or any parent folder; real env vars win.
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))

PROJECT_NAME = "optimizer-music-genre-classifier"
MODEL = "gpt-4o-mini"
DATASET_NAME = "optimizer-music-genre-classifier-songs"
LIBRARY_PROMPT_NAME = "music-genre-classifier"
MAX_TRIALS = 5  # candidate prompts the optimizer may evaluate: the budget cap
