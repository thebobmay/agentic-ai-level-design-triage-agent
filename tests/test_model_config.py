"""Unit tests for src/model_config.py."""

from src.model_config import EXPERIMENT_MODELS, GPT_4O_MINI, GPT_5_1, estimate_cost


def test_experiment_has_the_three_chosen_models():
    assert len(EXPERIMENT_MODELS) == 3
    assert {m.label for m in EXPERIMENT_MODELS} == {"gpt-4o-mini", "gpt-4.1", "gpt-5.1"}


def test_reasoning_model_leaves_settings_unset_chat_pins_temperature():
    assert GPT_5_1.settings is None  # reasoning model: no forced temperature
    assert GPT_4O_MINI.settings == {"temperature": 0.0}


def test_estimate_cost_uses_per_million_pricing():
    # gpt-4o-mini: $0.15 in, $0.60 out per 1M
    assert estimate_cost(1_000_000, 1_000_000, GPT_4O_MINI) == 0.15 + 0.60
    assert estimate_cost(500_000, 0, GPT_4O_MINI) == 0.075
    assert estimate_cost(0, 0, GPT_5_1) == 0.0
