import os


def load_local_env(project_root: str) -> None:
    """
    Load local development settings from .env without overriding real env vars.
    Supports simple KEY=VALUE lines, optional quotes, and comments.
    """
    path = os.path.join(project_root, ".env")
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key or key in os.environ:
                continue

            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value.startswith(("'", '"'))
            ):
                value = value[1:-1]

            os.environ[key] = value
