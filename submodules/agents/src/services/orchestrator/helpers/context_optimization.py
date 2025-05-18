"""Context optimization utilities for handling large context windows efficiently."""

from typing import List, Dict, Optional
from collections import Counter
import json
import re


def detect_repeated_structures(text: str) -> Dict[str, float]:
    """
    Analyze text for repeated structural patterns like JSON, XML, or key-value pairs.
    Returns a dict of pattern types and their density scores (0-1).
    """
    patterns = {
        "json_like": r"[{[].*?[\]}]",
        "key_value": r'["\']\w+["\']\s*:\s*.*?(?=[,}]|$)',
        "xml_like": r"<[^>]+>.*?</[^>]+>",
        "list_items": r"^\s*[-*•]\s+.*$",
        "numbered_items": r"^\s*\d+\.\s+.*$",
    }

    total_length = len(text)
    if total_length == 0:
        return {}

    scores = {}
    for pattern_name, regex in patterns.items():
        matches = re.finditer(regex, text, re.MULTILINE)
        matched_text = "".join(match.group(0) for match in matches)
        scores[pattern_name] = len(matched_text) / total_length

    return scores


def analyze_information_density(text: str) -> float:
    """
    Calculate information density based on character/token repetition.
    Returns a score between 0-1 where higher means more unique information.
    """
    if not text:
        return 0.0

    # Count character frequencies
    char_counts = Counter(text)
    total_chars = len(text)

    # Calculate entropy-based density
    char_frequencies = [count / total_chars for count in char_counts.values()]
    entropy = sum(-freq * (freq**0.5) for freq in char_frequencies)  # Modified entropy calculation

    # Normalize to 0-1 range
    return min(1.0, entropy * 2)  # Scale factor of 2 empirically determined


def optimize_context_block(text: str, max_length: int, preserve_start: int = 100, preserve_end: int = 100) -> str:
    """
    Intelligently optimize a block of text to fit within max_length while preserving
    important information based on structural analysis and information density.
    """
    if len(text) <= max_length:
        return text

    # Analyze text structure
    structure_scores = detect_repeated_structures(text)

    # If we detect high structural repetition, try to preserve one complete instance
    if any(score > 0.3 for score in structure_scores.values()):
        # Find complete structural units (e.g. complete JSON objects, list items)
        units = extract_complete_units(text)
        if units:
            # Keep representative units that fit in max_length
            return compress_structural_units(units, max_length)

    # Otherwise use information density-based approach
    return optimize_by_density(text, max_length, preserve_start, preserve_end)


def extract_complete_units(text: str) -> List[str]:
    """Extract complete structural units from text (JSON objects, list items etc)."""
    units = []

    # Try parsing as JSON first
    try:
        json_data = json.loads(text)
        if isinstance(json_data, (list, dict)):
            return [json.dumps(item) for item in (json_data if isinstance(json_data, list) else [json_data])]
    except json.JSONDecodeError:
        pass

    # Extract other patterns
    patterns = [
        (r"^\s*[-*•]\s+.*$", True),  # List items, multiline
        (r"^\s*\d+\.\s+.*$", True),  # Numbered items, multiline
        (r"<[^>]+>.*?</[^>]+>", False),  # XML-like tags
        (r'["\']\w+["\']\s*:\s*.*?(?=[,}]|$)', False),  # Key-value pairs
    ]

    for pattern, is_multiline in patterns:
        flags = re.MULTILINE if is_multiline else 0
        matches = re.finditer(pattern, text, flags)
        units.extend(match.group(0) for match in matches)

    return units


def compress_structural_units(units: List[str], max_length: int) -> str:
    """Compress structural units to fit max_length while preserving representation."""
    if not units:
        return ""

    # Always keep first and last unit
    if len(units) > 2:
        total_length = len(units[0]) + len(units[-1])
        remaining_length = max_length - total_length

        # If we can't fit any middle units, just return first and last
        if remaining_length <= 0:
            return f"{units[0]}\n...[{len(units)-2} similar items omitted]...\n{units[-1]}"

        # Try to fit representative middle units
        middle_units = []
        for unit in units[1:-1]:
            if len(unit) + 1 <= remaining_length:  # +1 for newline
                middle_units.append(unit)
                remaining_length -= len(unit) + 1
            else:
                break

        if middle_units:
            return "\n".join(
                [units[0]]
                + middle_units
                + [f"...[{len(units)-len(middle_units)-2} similar items omitted]...", units[-1]]
            )

    return "\n".join(units)


def optimize_by_density(text: str, max_length: int, preserve_start: int, preserve_end: int) -> str:
    """Optimize text based on information density analysis."""
    if len(text) <= max_length:
        return text

    # Always preserve start and end sections
    start_text = text[:preserve_start]
    end_text = text[-preserve_end:]

    # Analyze middle section
    middle_text = text[preserve_start:-preserve_end]

    # Split into chunks and analyze density
    chunk_size = 100
    chunks = [middle_text[i : i + chunk_size] for i in range(0, len(middle_text), chunk_size)]

    # Calculate density scores for chunks
    chunk_scores = [(chunk, analyze_information_density(chunk)) for chunk in chunks]

    # Sort chunks by density score
    sorted_chunks = sorted(chunk_scores, key=lambda x: x[1], reverse=True)

    # Build optimized middle section
    remaining_length = max_length - (len(start_text) + len(end_text))
    optimized_middle = ""

    for chunk, score in sorted_chunks:
        if len(chunk) + 1 <= remaining_length:  # +1 for newline
            optimized_middle += chunk + "\n"
            remaining_length -= len(chunk) + 1
        else:
            break

    return f"{start_text}{optimized_middle}[...content optimized...]\n{end_text}"
