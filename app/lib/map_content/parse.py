import re
from typing import List, Dict, Optional


def extract_rating_from_text(text: str) -> Optional[str]:
    match = re.search(r"(\d\.\d)\s*\(", text)
    return match.group(1) if match else None


def extract_price_from_text(text: str) -> Optional[str]:
    match = re.search(r"(\${1,4}|[£€]\s?\d+[\w–\-\d]*)", text)
    return match.group(1) if match else None


def extract_description_from_lines(lines: List[str]) -> Optional[str]:
    for line in lines:
        if "·" in line:
            return line
    for line in lines[1:5]:
        if 1 <= len(line.split()) <= 3 and line[:1].isupper():
            return line
    return None


def looks_like_name(line: str) -> bool:
    if not line:
        return False
    if line.startswith("http"):
        return False
    if line in {"Save", "Share", "", "", ""}:
        return False
    if any(tok in line for tok in ["places", "Shared list", "Permanently closed"]):
        return False
    if "·" in line or "$" in line or "£" in line or "€" in line:
        return False
    if re.search(r"\d\.\d\s*\(", line):
        return False
    return len(line) <= 60


def parse_places_from_lines(lines: List[str]) -> List[Dict[str, Optional[str]]]:
    start_indices: List[int] = []
    for i in range(len(lines) - 1):
        if looks_like_name(lines[i]) and re.search(r"\d\.\d\s*\(", lines[i + 1]):
            start_indices.append(i)

    items: List[Dict[str, Optional[str]]] = []
    for si, i in enumerate(start_indices):
        j = start_indices[si + 1] if si + 1 < len(start_indices) else len(lines)
        window = lines[i:j]
        name = window[0]
        block_text = "\n".join(window)
        rating = extract_rating_from_text(block_text)
        price = None
        description = None
        for w in window[1:6]:
            if price is None:
                price = extract_price_from_text(w)
            if description is None:
                if "·" in w:
                    description = w
                else:
                    if 1 <= len(w.split()) <= 3 and w[:1].isupper() and not re.search(r"\d", w):
                        description = w
            if price and description:
                break
        items.append({
            "name": name,
            "rating": rating,
            "description": description,
            "price": price,
        })
    return items


