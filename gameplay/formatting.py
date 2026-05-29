"""Formatting helpers for gameplay-related values."""

from __future__ import annotations


def format_time(ms: int) -> str:
    """
    Convert milliseconds to a ``M:SS.mmm`` string.

    The formatting matches the historical Maze Game behavior and is used
    by gameplay HUD and leaderboard rendering.

    :param ms: Duration in milliseconds.
    :return: Formatted time string, for example ``"1:23.456"``.
    """
    seconds, milliseconds = divmod(ms, 1000)
    minutes, sec = divmod(seconds, 60)
    return f"{minutes}:{sec:02d}.{milliseconds:03d}"
