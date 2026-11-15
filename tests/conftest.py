import os
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.setdefault("ESTOQUE_SECRET", "chave-de-teste")
os.environ.setdefault("ESTOQUE_SENHA_HASH", generate_password_hash("senha-teste"))

import app as estoque  # noqa: E402


@pytest.fixture
def banco():
    """Recria as tabelas do banco.sql antes de cada teste."""
    con = estoque.conectar()
    with con.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS movimentacao")
        cur.execute("DROP TABLE IF EXISTS produto")
        sql = (RAIZ / "banco.sql").read_text(encoding="utf-8")
        for comando in sql.split(";"):
            comando = comando.strip()
            if comando.upper().startswith("CREATE TABLE"):
                cur.execute(comando)
    con.commit()
    con.close()


@pytest.fixture
def cliente(banco):
    estoque.app.config["TESTING"] = True
    with estoque.app.test_client() as c:
        c.post("/login", data={"usuario": "equipe", "senha": "senha-teste"})
        yield c
