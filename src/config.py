from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AppSettings:
    oracle_dsn: str = ""
    oracle_wallet_dir: str = ""
    oracle_user: str = ""
    oracle_password: str = ""
    wallet_password: str = ""
    oracle_schema: str = ""
    oracle_ai_profile: str = ""
    row_limit: int = 200

    @classmethod
    def load(cls):
        return cls(**{field: os.getenv(env, "") for field, env in {
            "oracle_dsn": "DB_DSN", "oracle_wallet_dir": "WALLET_DIR",
            "oracle_user": "DB_USER", "oracle_password": "DB_PASSWORD",
            "wallet_password": "WALLET_PASSWORD", "oracle_schema": "DB_SCHEMA",
        }.items()})
