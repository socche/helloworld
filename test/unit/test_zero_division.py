from app.calc import Calculator
import pytest

def test_divide_by_zero():
    calc = Calculator()
    with pytest.raises(TypeError, match="Division by zero is not possible"):
        calc.divide(10, 0)
