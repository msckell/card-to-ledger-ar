from pipeline.ai.verifier import check

ALLOWED = {"TX-0042", "RC-0107", "TX-0041", "R-016"}


def _kinds(text: str) -> set[str]:
    return {v.split(":")[0] for v in check(text, ALLOWED)}


def test_raw_figure_fails():
    assert "raw_figure" in _kinds("The charge [TX-0042] is 8.00 higher than the receipt [RC-0107].")


def test_currency_symbol_fails():
    assert "raw_figure" in _kinds("The charge [TX-0042] is $ higher than the receipt [RC-0107].")


def test_number_word_fails():
    assert "raw_figure" in _kinds("The charge [TX-0042] was posted two days after [TX-0041].")


def test_invented_id_fails():
    assert "invented_id" in _kinds("The receipt [RC-0999] belongs to [TX-0042].")


def test_banned_claim_fails():
    assert "banned_claim" in _kinds("[TX-0042] is approved and can be posted.")
    assert "banned_claim" in _kinds("[TX-0042] looks fraudulent.")


def test_missing_citation_fails():
    assert "no_citation" in _kinds("The receipt amount is lower than the charge.")


def test_clean_explanation_passes():
    text = ("The receipt [RC-0107] matches [TX-0042] by merchant and date, but it was printed before "
            "the tip was added. Ask the cardholder for the final ticket.")
    assert check(text, ALLOWED) == []


def test_paraphrase_passes():
    text = ("[TX-0042] repeats the merchant and amount of [TX-0041] on the same card, and only "
            "one receipt exists, so it may be a double charge worth confirming with the cardholder.")
    assert check(text, ALLOWED) == []


def test_rule_id_is_allowed_when_listed():
    assert check("The broad rule [R-016] put [TX-0042] under travel.", ALLOWED) == []
