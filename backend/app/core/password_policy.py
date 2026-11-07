"""New-password policy; existing credentials are never rewritten or trimmed.

NIST SP 800-63B-4 informs the length/passphrase policy. The zxcvbn threshold is
JOMO's additional guessability check, not a claim of NIST certification or a
complete breached-password lookup. Supabase remains the password verifier.
"""
import json
from pathlib import Path
import re

from fastapi import HTTPException
from zxcvbn import zxcvbn

POLICY = json.loads((Path(__file__).resolve().parents[1] / "data/password_policy.json").read_text())
MIN_LENGTH = POLICY["minimum_length"]
MAX_BYTES = POLICY["maximum_utf8_bytes"]


def validate_new_password(password: str, email: str = "") -> None:
    message = None
    byte_length = 0
    if len(password) < MIN_LENGTH:
        message = f"Use at least {MIN_LENGTH} characters. Several unrelated words work well."
    else:
        try:
            byte_length = len(password.encode("utf-8"))
        except UnicodeEncodeError:
            raise HTTPException(400, detail={"code": "WEAK_PASSWORD", "message": "Use valid Unicode characters in your password."}) from None
    if not message and byte_length > MAX_BYTES:
        message = f"Use a shorter password: the sign-in service accepts up to {MAX_BYTES} UTF-8 bytes. Unicode characters can use more than one byte."
    elif not message and password.lower().strip() in POLICY["blocked_passwords"]:
        message = "This is a commonly guessed or well-known password. Choose your own unrelated words or use a password manager."
    elif not message:
        local = email.lower().split("@")[0]
        context = [*POLICY["context_words"], email.lower(), local,
                   *(part for part in re.split(r"[^a-z0-9]+", local) if len(part) >= 3)]
        result = zxcvbn(password, user_inputs=[word for word in context if word])
        if result["score"] < POLICY["minimum_score"]:
            message = "This password is too predictable. Try several unrelated words or a password manager, and avoid your email or the app name."
    if message:
        raise HTTPException(400, detail={"code": "WEAK_PASSWORD", "message": message})
