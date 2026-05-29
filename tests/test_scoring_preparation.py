from gameplay.scoring import PreparedRunScore, ScoreParams, prepare_run_score


def test_prepare_run_score_builds_expected_elapsed_time() -> None:
    prepared = prepare_run_score(
        start_ms=1_000,
        now_ms=3_500,
        coins_value_sum=17,
        diamond_count=2,
        won=True,
    )

    assert prepared.elapsed_ms == 2_500


def test_prepare_run_score_preserves_score_inputs() -> None:
    prepared = prepare_run_score(
        start_ms=100,
        now_ms=900,
        coins_value_sum=9,
        diamond_count=1,
        won=False,
    )

    assert prepared.coins_value_sum == 9
    assert prepared.diamond_count == 1
    assert prepared.won is False


def test_prepare_run_score_uses_current_default_score_params() -> None:
    prepared = prepare_run_score(
        start_ms=0,
        now_ms=1_000,
        coins_value_sum=0,
        diamond_count=0,
        won=True,
    )

    assert prepared.params == ScoreParams(
        coin_k=30,
        time_penalty_per_sec=0.25,
        win_bonus=400,
        win_multiplier=1.25,
        loss_multiplier=0.35,
        diamond_bonus=400,
        apply_time_on_loss=False,
    )


def test_prepare_run_score_returns_prepared_run_score_dataclass() -> None:
    prepared = prepare_run_score(
        start_ms=0,
        now_ms=0,
        coins_value_sum=1,
        diamond_count=0,
        won=True,
    )

    assert isinstance(prepared, PreparedRunScore)
