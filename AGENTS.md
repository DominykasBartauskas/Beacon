# Beacon project memory

- Use `uv` for Python/API work and dependency management.
- Use `pnpm` for frontend JavaScript work and dependency management.
- `api/` contains the FastAPI backend; `spa/` contains the React + TypeScript single-page app. Keep the API/SPA boundary explicit and synchronize frontend contracts from the API OpenAPI schema.
- Use Conventional Commits formatting for Git commit messages before pushing.
- ChatGPT/Codex should clean up temporary task sessions it creates once the related work is genuinely complete, unless the user asks to retain them.
