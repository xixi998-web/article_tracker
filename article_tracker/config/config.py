from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .config_schema import UnifiedConfig


def _resolve_env(config: UnifiedConfig) -> None:
    config.llm.api_key = config.llm.api_key or os.getenv(config.llm.api_key_env, "")
    config.output.email.smtp_pass = config.output.email.smtp_pass or os.getenv(config.output.email.smtp_pass_env, "")
    config.s2.api_key = config.s2.api_key or os.getenv(config.s2.api_key_env, "")
    config.openalex.email = config.openalex.email or os.getenv(config.openalex.email_env, "")


class Config:
    @staticmethod
    def load(path: str | Path, *, resolve_env: bool = True) -> UnifiedConfig:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = UnifiedConfig.model_validate(data)
        if resolve_env:
            env_file = p.parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            _resolve_env(config)
        return config

    @staticmethod
    def validate(path: str | Path) -> list[str]:
        try:
            Config.load(path)
            return []
        except Exception as e:
            return [str(e)]
