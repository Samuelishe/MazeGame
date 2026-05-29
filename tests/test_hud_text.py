from gameplay.hud_text import build_hud_text, build_player_prefix


def test_build_player_prefix_without_active_player() -> None:
    assert build_player_prefix(None) == ""


def test_build_player_prefix_with_active_player() -> None:
    assert build_player_prefix("Irwyn") == "Игрок: Irwyn   "


def test_build_hud_text_without_active_player() -> None:
    assert build_hud_text(
        active_player_name=None,
        coins_collected=17,
        bronze_count=1,
        silver_count=2,
        gold_count=3,
        diamond_count=4,
        elapsed_ms_live=83456,
    ) == "💰 17 (🥉1/🥈2/🥇3/💎4)   ⏱ 1:23.456"


def test_build_hud_text_with_active_player() -> None:
    assert build_hud_text(
        active_player_name="Irwyn",
        coins_collected=17,
        bronze_count=1,
        silver_count=2,
        gold_count=3,
        diamond_count=4,
        elapsed_ms_live=83456,
    ) == "Игрок: Irwyn   💰 17 (🥉1/🥈2/🥇3/💎4)   ⏱ 1:23.456"


def test_build_hud_text_preserves_spacing_and_time_formatting() -> None:
    assert build_hud_text(
        active_player_name="A",
        coins_collected=0,
        bronze_count=0,
        silver_count=0,
        gold_count=0,
        diamond_count=0,
        elapsed_ms_live=999,
    ) == "Игрок: A   💰 0 (🥉0/🥈0/🥇0/💎0)   ⏱ 0:00.999"
