DISPOSABLE_DOMAINS = {
    "10minutemail.com",
    "10minutemail.net",
    "dispostable.com",
    "fakeinbox.com",
    "getnada.com",
    "grr.la",
    "guerrillamail.biz",
    "guerrillamail.com",
    "guerrillamail.de",
    "guerrillamail.net",
    "guerrillamail.org",
    "guerrillamailblock.com",
    "maildrop.cc",
    "mailinator.com",
    "sharklasers.com",
    "temp-mail.org",
    "tempmail.com",
    "tempmail.io",
    "tempmail.net",
    "throwawaymail.com",
    "trashmail.com",
    "yopmail.com",
}


def is_disposable_email(email: str) -> bool:
    if "@" not in email:
        return False

    domain = email.rsplit("@", 1)[-1].strip().lower().rstrip(".")
    if not domain:
        return False

    return any(
        domain == disposable_domain or domain.endswith(f".{disposable_domain}")
        for disposable_domain in DISPOSABLE_DOMAINS
    )
