import re

class LocatorScorer:
    BASE_SCORES = {
        "get_by_role": 0.9,
        "get_by_label": 0.85,
        "get_by_text": 0.75,
        "id": 0.7,
        "css": 0.6,
        "xpath": 0.4,
    }

    @staticmethod
    def score_locator(locator_type, locator_string, element_attrs, element_text):
        score = LocatorScorer.BASE_SCORES.get(locator_type, 0.0)

        if "aria-label" in element_attrs:
            score += 0.1

        if locator_type in ["get_by_label", "get_by_text"]:
            text_to_check = element_attrs.get("aria-label", "") if locator_type == "get_by_label" else element_text

            if text_to_check:
                word_count = len(text_to_check.split())
                if word_count <= 5:
                    score += 0.05
                if word_count > 10:
                    score -= 0.1

                if text_to_check.isupper() or not any(c.isalpha() for c in text_to_check):
                    score -= 0.05

        if "id" in element_attrs:
            if re.search(r'(abc[0-9]{3}|[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', element_attrs["id"]):
                score -= 0.2

        if "class" in element_attrs:
            generic_classes = ["btn", "main", "container", "row", "col", "card", "modal"]
            if any(cls in element_attrs["class"] for cls in generic_classes):
                score -= 0.15

        if not element_text:
            score -= 0.3

        return round(max(0, score), 2)