import pytest
from theodolite_mcp.domain.logic import dms_to_decimal, decimal_to_dms

def test_dms_to_decimal_basic():
    assert dms_to_decimal(30, 30, 0) == pytest.approx(30.5)

def test_dms_to_decimal_seconds():
    # 30 + 30/60 + 30/3600 = 30 + 0.5 + 0.008333333333333333
    assert dms_to_decimal(30, 30, 30) == pytest.approx(30.5083333333)

def test_dms_to_decimal_negative():
    assert dms_to_decimal(-30, 30, 0) == pytest.approx(-30.5)

def test_dms_to_decimal_zero():
    assert dms_to_decimal(0, 0, 0) == 0.0

def test_dms_to_decimal_boundary():
    assert dms_to_decimal(0, 59, 59) == pytest.approx(59/60 + 59/3600)

def test_decimal_to_dms_basic():
    d, m, s = decimal_to_dms(30.5)
    assert d == 30
    assert m == 30
    assert s == pytest.approx(0)

def test_decimal_to_dms_seconds():
    d, m, s = decimal_to_dms(30.5083333333)
    assert d == 30
    assert m == 30
    assert s == pytest.approx(30, abs=1e-6)

def test_decimal_to_dms_negative():
    d, m, s = decimal_to_dms(-30.5)
    assert d == -30
    assert m == 30
    assert s == pytest.approx(0)
