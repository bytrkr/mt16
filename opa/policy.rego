package mt16

default allow = false

# =========================
# ALLOW RULE
# =========================
allow {
    input.intent != ""
    not blocked_keyword
}

# =========================
# BLOCKED KEYWORDS
# =========================
blocked_keyword {
    keyword := blocked[_]
    contains(lower(input.intent), keyword)
}

blocked := [
    "hack",
    "exploit",
    "bypass",
    "illegal"
]
