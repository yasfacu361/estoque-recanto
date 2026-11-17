import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import app as estoque  # noqa: E402


@pytest.fixture
def banco():
    """Isola os dados em memoria para cada teste."""
    anteriores = estoque.produtos_mock[:]
    movimentos_anteriores = estoque.movimentacoes_mock[:]
    estoque.movimentacoes_mock.clear()
    estoque.produtos_mock.clear()
    yield
    estoque.produtos_mock[:] = anteriores
    estoque.movimentacoes_mock[:] = movimentos_anteriores


@pytest.fixture
def cliente(banco):
    estoque.app.config["TESTING"] = True
    with estoque.app.test_client() as c:
        c.post("/login", data={"usuario": "equipe", "senha": "123456"})
        yield c
