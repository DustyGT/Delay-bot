# Expanded begging & ETA keywords
BEGGING_PHRASES = [
    r"\bpls\b", r"\bplease\b", r"\bplz\b", r"\bgimme\b", r"\bgive me\b",
    r"\bneed\b", r"\bwant\b", r"\bcan i get\b", r"\bwhere is\b", r"\bwher is\b"
]

INSTANT_TRIGGERS = [
    r"\brelease date\b", r"\brelease-date\b", r"\blaunch date\b",
    r"\bwhen out\b", r"\bwen out\b", r"\bwhen release\b", r"\bwen release\b",
    r"\bwhen is it out\b", r"\bwhen is game out\b", r"\bwhen game out\b",
    r"\bapk link\b", r"\bdownload link\b", r"\bis it out yet\b", r"\bis it ready\b",
    r"\bapk drop\b", r"\bgame drop\b", r"\bwhen drop\b", r"\bwhen will it drop\b"
]

# Strict ETA Question components
ETA_QUESTIONS = ["when", "wen", "whens", "what time", "how long until", "how long till"]
RELEASE_TARGETS = ["game", "apk", "demo", "beta", "update", "build", "mod", "patch", "download"]
RELEASE_ACTIONS = ["come out", "coming out", "release", "released", "releasing", "launch", "drop", "dropping", "ready", "done", "available"]

def is_asking_about_release(text: str) -> bool:
    clean = re.sub(r"[^\w\s]", "", text.lower())

    # 1. Check instant exact trigger phrases
    for trigger in INSTANT_TRIGGERS:
        if re.search(trigger, clean):
            return True

    # 2. Check for explicit ETA begging pattern (Requires Question + Release Action or Target)
    has_eta_q = any(re.search(rf"\b{q}\b", clean) for q in ETA_QUESTIONS)
    has_target = any(re.search(rf"\b{t}\b", clean) for t in RELEASE_TARGETS)
    has_action = any(re.search(rf"\b{a}\b", clean) for a in RELEASE_ACTIONS)
    has_begging = any(re.search(rf"\b{b}\b", clean) for b in BEGGING_PHRASES)

    # Trigger if asking "when" + (target or action)
    if has_eta_q and (has_target or has_action):
        return True

    # Trigger if begging for a release target (e.g. "pls give game apk")
    if has_begging and has_target and has_action:
        return True

    return False
    
