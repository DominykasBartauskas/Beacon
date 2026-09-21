import pytest

from beacon_api.categories import (
    AI_ENGINEERING,
    AI_RESEARCH,
    MODELS_RELEASES,
    SAFETY_SECURITY,
    SOFTWARE_DEVELOPMENT,
    TOOLS_PLATFORMS,
    classify,
)


def test_unmatched_text_keeps_the_source_category() -> None:
    assert classify("A quiet Tuesday", default=AI_RESEARCH) == AI_RESEARCH
    assert classify("A quiet Tuesday", default=SOFTWARE_DEVELOPMENT) == SOFTWARE_DEVELOPMENT


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("A jailbreak attack on tool-using assistants", SAFETY_SECURITY),
        ("Introducing our open-weight model", MODELS_RELEASES),
        ("A lighter evaluation loop for prompting", AI_ENGINEERING),
        ("A new Rust compiler for the framework's runtime", TOOLS_PLATFORMS),
        ("We propose a scaling law for diffusion training", AI_RESEARCH),
    ],
)
def test_titles_land_in_the_right_category(title: str, expected: str) -> None:
    assert classify(title, default=AI_RESEARCH) == expected


def test_the_title_outweighs_the_summary() -> None:
    category = classify(
        "A jailbreak of the safety guardrail",
        "The framework is an open source library with an SDK and a CLI.",
        default=AI_RESEARCH,
    )

    assert category == SAFETY_SECURITY


def test_matching_is_word_bounded() -> None:
    # "token" must not fire on "tokenomics", nor "api" on "rapid"
    assert classify("Tokenomics of a rapid rollout", default=AI_RESEARCH) == AI_RESEARCH


def test_safety_wins_over_research_for_the_same_text() -> None:
    category = classify("Adversarial robustness study of neural networks", default=AI_RESEARCH)

    assert category == SAFETY_SECURITY
