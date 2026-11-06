import pytest

def soma(a, b):
    return a + b

def test_soma():
    resultado = soma (2,3)
    assert resultado == 5