import pytest

from presidio_anonymizer.operators import GenZ


@pytest.mark.parametrize(
    # fmt: off
    "params",
    [
        {"entity_type": "PERSON"},
    ],
    # fmt: on
)
def test_given_value_for_redact_then_we_return_empty_value(params):
    operator = GenZ()
    allowed = operator.GENZ_MAP["PERSON"]
    text = operator.operate("bla", params)
    assert text in allowed


def test_when_validate_anonymizer_then_correct_name():
    assert GenZ().operator_name() == "genz"
