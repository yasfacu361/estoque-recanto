"""Testes unitarios das regras, sem banco."""
from app import calcular_saldo, precisa_repor


def test_saldo_e_entradas_menos_retiradas():
    assert calcular_saldo(10, 4) == 6


def test_saldo_sem_movimentacao_e_zero():
    assert calcular_saldo(0, 0) == 0


def test_repor_quando_saldo_igual_ao_minimo():
    assert precisa_repor(10, 10) is True


def test_repor_quando_saldo_abaixo_do_minimo():
    assert precisa_repor(4, 10) is True


def test_nao_repor_quando_saldo_acima_do_minimo():
    assert precisa_repor(30, 20) is False
