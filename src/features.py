"""Hand-crafted lexical features extracted from a URL string."""
import ipaddress
import math
import re
from collections import Counter
from urllib.parse import urlsplit

SUSPICIOUS_WORDS = ["login", "signin", "verify", "secure", "account", "update",
                    "bank", "confirm", "password", "wallet", "support", "auth"]
SUSPICIOUS_TLDS = {"xyz", "top", "tk", "ml", "ga", "cf", "gq", "buzz", "live",
                   "click", "info", "online", "site", "app", "io", "ru", "cn"}


def entropy(s: str) -> float:
    if not s:
        return 0.0
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in Counter(s).values())


def is_ip(host: str) -> int:
    try:
        ipaddress.ip_address(host)
        return 1
    except ValueError:
        return 0


def hostname_of(url: str) -> str:
    """Lower-case hostname without scheme, port and leading 'www.'."""
    if "://" not in url:
        url = "http://" + url
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def host_features(host: str) -> dict:
    parts = host.split(".")
    tld = parts[-1] if len(parts) > 1 else ""
    tokens = re.split(r"[.\-]", host)
    letters = sum(ch.isalpha() for ch in host)
    vowels = sum(ch in "aeiou" for ch in host)
    return {
        "host_len": len(host),
        "num_dots": host.count("."),
        "num_hyphens": host.count("-"),
        "num_digits": sum(ch.isdigit() for ch in host),
        "digit_ratio": sum(ch.isdigit() for ch in host) / max(len(host), 1),
        "num_subdomains": max(len(parts) - 2, 0),
        "is_ip": is_ip(host),
        "suspicious_tld": int(tld in SUSPICIOUS_TLDS),
        "tld_len": len(tld),
        "entropy": entropy(host),
        "longest_token": max((len(t) for t in tokens), default=0),
        "vowel_ratio": vowels / max(letters, 1),
        "suspicious_words": sum(w in host for w in SUSPICIOUS_WORDS),
    }


def full_url_features(url: str) -> dict:
    """Host features plus features of the whole URL (scheme, path, query)."""
    f = host_features(hostname_of(url))
    rest = urlsplit(url if "://" in url else "http://" + url)
    f.update({
        "url_len": len(url),
        "is_https": int(url.lower().startswith("https")),
        "has_www": int("://www." in url.lower()),
        "path_len": len(rest.path),
        "num_slashes": rest.path.count("/"),
        "has_query": int(bool(rest.query)),
        "has_at": int("@" in url),
        "url_suspicious_words": sum(w in url.lower() for w in SUSPICIOUS_WORDS),
    })
    return f
