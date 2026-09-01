"""Shared command metadata and result limits."""

MAX_SEARCH_RESULTS = 10
API_MAX_SEARCH_RESULTS = 50

RANK_COMMANDS = {
    ("b50", "best50"): "best50",
    ("b40", "best40"): "best40",
    ("b35", "best35"): "best35",
    ("b15", "best15"): "best15",
    ("ab35", "allb35"): "allb35",
    ("ab50", "allb50"): "allb50",
    ("apb50", "ap50"): "apb50",
    ("fdxb50", "fdx50"): "fdxb50",
    ("rct50", "r50"): "rct50",
    ("idealb50", "idlb50"): "idlb50",
    ("s50", "sun50", "寸止め", "寸50"): "sun50",
    ("unknown",): "unknown",
}


def rank_command_words(*, hidden=()):
    """Return every rank-command alias except explicitly hidden words."""
    hidden = set(hidden)
    return tuple(sorted(alias for aliases in RANK_COMMANDS for alias in aliases if alias not in hidden))
