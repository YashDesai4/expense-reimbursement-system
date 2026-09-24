from __future__ import annotations

CATEGORY_KEYWORDS = {
    "Travel": {"airlines", "airways", "hotel", "uber", "lyft", "taxi", "rail", "rental"},
    "Meals": {"restaurant", "cafe", "coffee", "kitchen", "grill", "doordash", "pizza"},
    "Software": {"software", "cloud", "hosting", "github", "adobe", "microsoft"},
    "Office": {"office", "staples", "supplies", "printer", "paper", "desk"},
    "Training": {"course", "conference", "workshop", "udemy", "books"},
}


def suggest_category(vendor: str, description: str = "") -> str:
    text = f"{vendor} {description}".lower()
    scores = {
        category: sum(keyword in text for keyword in keywords)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "Other"
