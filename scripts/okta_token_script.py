"""
OktaTokenValidator (dotenv-friendly)
- Prefers .env (via python-dotenv), falls back to config.ini, then env vars.
- Creates client-credentials access tokens, caches them with expiry metadata,
  and validates tokens (using okta_jwt_verifier if installed).
"""

from __future__ import annotations
import json
import base64
import logging
import os
import time
import requests
import configparser
from typing import Optional, Tuple

# Try to import dotenv (optional) to load .env automatically
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except Exception:
    DOTENV_AVAILABLE = False

# Try to import okta_jwt_verifier; fall back gracefully if not installed.
try:
    from okta_jwt_verifier import AccessTokenVerifier
    HAS_OKTA_VERIFIER = True
except Exception:
    HAS_OKTA_VERIFIER = False

# ----- Logging -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ----- Defaults -----
DEFAULT_CONFIG_PATH = "config.ini"
DEFAULT_SECTION = "okta"


class OktaTokenValidator:
    def __init__(self,
                 config_path: str = DEFAULT_CONFIG_PATH,
                 section: str = DEFAULT_SECTION,
                 prefer_dotenv: bool = True):
        # 1) Optionally load .env first
        if prefer_dotenv and DOTENV_AVAILABLE:
            # load_dotenv does nothing if there is no .env file
            load_dotenv()
            logger.debug("python-dotenv loaded (if .env exists).")

        # 2) Read config.ini if present
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        cfg = self.config[section] if section in self.config else {}

        # 3) Read values: priority .env/env vars > config.ini
        def get_conf(key: str, cfg_section=cfg, env_key: Optional[str] = None, default: str = "") -> str:
            env_key = env_key or key.upper()
            return os.getenv(env_key) or cfg_section.get(key, default)

        self.okta_domain = get_conf('okta_domain', env_key='OKTA_DOMAIN')
        self.client_id = get_conf('client_id', env_key='OKTA_CLIENT_ID')
        self.client_secret = get_conf('client_secret', env_key='OKTA_CLIENT_SECRET')
        scopes = get_conf('scopes', env_key='OKTA_SCOPES')
        self.scopes = scopes.split() if scopes else []
        self.token_file_path = get_conf('token_file', env_key='OKTA_TOKEN_FILE') or 'okta_token.json'

        if not self.okta_domain:
            logger.error("Okta domain is not configured. Set OKTA_DOMAIN in .env or config.ini.")
        if not (self.client_id and self.client_secret):
            logger.warning("Client ID / Secret missing. Set OKTA_CLIENT_ID and OKTA_CLIENT_SECRET in .env or config.ini.")

    # --- Internal helpers ---
    def _save_token_file(self, token: str, expires_at: int) -> None:
        data = {"access_token": token, "expires_at": expires_at}
        try:
            with open(self.token_file_path, "w") as f:
                json.dump(data, f)
            logger.debug("Token written to %s (expires_at=%d)", self.token_file_path, expires_at)
        except Exception as e:
            logger.exception("Failed to write token file: %s", e)

    def _load_token_file(self) -> Optional[dict]:
        if not os.path.exists(self.token_file_path):
            logger.debug("Token file '%s' does not exist.", self.token_file_path)
            return None
        try:
            with open(self.token_file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.exception("Failed to read token file: %s", e)
            return None

    def create_token(self) -> Optional[Tuple[str, int]]:
        """Request a new token from Okta using client_credentials and save it with expiry."""
        if not (self.okta_domain and self.client_id and self.client_secret):
            logger.error("Missing Okta configuration: cannot request token.")
            return None

        token_url = f"{self.okta_domain.rstrip('/')}/oauth2/default/v1/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": " ".join(self.scopes)
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            resp = requests.post(token_url, data=payload, headers=headers, timeout=10)
        except requests.RequestException as e:
            logger.exception("HTTP request to token endpoint failed: %s", e)
            return None

        if resp.status_code != 200:
            logger.error("Failed to obtain token: status=%s body=%s", resp.status_code, resp.text)
            return None

        try:
            token_data = resp.json()
            access_token = token_data.get("access_token")
            expires_in = int(token_data.get("expires_in", 0))
            if not access_token:
                logger.error("Token response missing access_token: %s", token_data)
                return None

            expires_at = int(time.time()) + expires_in if expires_in > 0 else 0
            self._save_token_file(access_token, expires_at)
            logger.info("New access token obtained, expires in %s seconds.", expires_in)
            return access_token, expires_at
        except Exception as e:
            logger.exception("Failed to parse token response: %s", e)
            return None

    @staticmethod
    def _decode_jwt_payload(token: str) -> Optional[dict]:
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return None
            payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode("utf-8")
            return json.loads(payload_json)
        except Exception:
            return None

    def is_token_expired(self, token: Optional[str] = None, expires_at: Optional[int] = None) -> bool:
        now = int(time.time())
        if expires_at:
            return now >= expires_at

        if not token:
            return True

        payload = self._decode_jwt_payload(token)
        if not payload:
            logger.debug("Unable to decode JWT payload; assuming expired.")
            return True

        exp = payload.get("exp")
        if not isinstance(exp, int):
            logger.debug("No numeric 'exp' claim found; assuming expired.")
            return True

        return now >= exp

    def refresh_token_if_needed(self) -> Optional[str]:
        saved = self._load_token_file()
        if saved:
            token = saved.get("access_token")
            expires_at = saved.get("expires_at", 0)
            if token and not self.is_token_expired(token=token, expires_at=expires_at):
                logger.info("Using cached token (expires_at=%s).", expires_at)
                return token
            else:
                logger.info("Cached token missing or expired; creating a new token.")
        else:
            logger.info("No cached token; creating a new token.")

        created = self.create_token()
        if created:
            access_token, _ = created
            return access_token
        return None

    def validate_okta_token(self, token: str) -> Tuple[bool, str]:
        """Validate token using okta_jwt_verifier if present, else do minimal checks."""
        if not token:
            return False, "No token provided."

        payload = self._decode_jwt_payload(token)
        if not payload:
            return False, "Failed to decode token payload."

        if HAS_OKTA_VERIFIER:
            try:
                issuer = payload.get("iss")
                audience = payload.get("aud")
                if not issuer or not audience:
                    return False, "Token payload missing 'iss' or 'aud'."

                verifier = AccessTokenVerifier(issuer=issuer, audience=audience)
                verifier.verify(token)
                return True, json.dumps(payload)
            except Exception as e:
                logger.exception("Token verification failed using okta_jwt_verifier: %s", e)
                return False, f"Verification failed: {e}"

        # fallback checks
        if self.is_token_expired(token=token):
            return False, "Token is expired."
        missing = [c for c in ("iss", "aud", "exp") if c not in payload]
        if missing:
            return False, f"Token payload missing claims: {missing}"
        return True, json.dumps(payload)


# ----- Usage Example -----
if __name__ == "__main__":
    # prefer .env (default). Set prefer_dotenv=False to skip .env even if python-dotenv installed.
    validator = OktaTokenValidator(prefer_dotenv=True)

    token = validator.refresh_token_if_needed()
    if not token:
        logger.error("Failed to obtain token.")
        raise SystemExit(1)

    valid, info = validator.validate_okta_token(token)
    logger.info("Is token valid? %s", valid)
    if valid:
        logger.debug("Token payload: %s", info)
    else:
        logger.error("Token validation failed: %s", info)
