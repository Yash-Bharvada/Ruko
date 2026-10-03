"""Shared text preprocessing. Used by BOTH training and prediction so they can never drift apart."""
import re

_URL = re.compile(r"https?://[^\s]+", re.I)
_PHONE = re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")
_LONGNUM = re.compile(r"\d{6,}")
_UPI = re.compile(r"[\w.\-]{2,}@[a-z]{2,}", re.I)

def _url_repl(m):
    url = m.group(0)
    host = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0].lower()
    tld = host.rsplit(".", 1)[-1] if "." in host else "none"
    # keep a coarse signal about the link without memorising random ids
    flags = ["urltoken", "tld_" + tld]
    if any(w in host for w in ("kyc", "verify", "secure", "update", "refund", "claim", "apk")):
        flags.append("urlword_suspicious")
    if "bit.ly" in host or "tinyurl" in host:
        flags.append("urlshortener")
    return " " + " ".join(flags) + " "

def preprocess(text) -> str:
    if text is None or (isinstance(text, float) and text != text):
        return ""
    t = str(text).strip().lower()
    t = _URL.sub(_url_repl, t)
    t = _UPI.sub(" upitoken ", t)
    t = _PHONE.sub(" phonetoken ", t)
    t = _LONGNUM.sub(" longnumtoken ", t)
    t = re.sub(r"\s+", " ", t)
    return t

# Gujarati / Hindi / Telugu use combining marks that Python's \w does NOT match,
# so the default tokenizer would cut words in half. Split on whitespace/punctuation instead.
TOKEN_PATTERN = r"[^\s.,!?:;()\[\]\"'|/\\<>{}\-]+"
