"""Estoque do Recanto.

App Flask simples: produtos de higiene, entradas, retiradas e aviso Repor.
Regra principal: saldo = entradas - retiradas. Repor quando saldo <= minimo.
Os dados ficam no MySQL (tabelas produto e movimentacao).
"""
import os

import pymysql
from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ["ESTOQUE_SECRET"]
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Login unico da equipe. A senha fica so em hash (variavel de ambiente).
USUARIO = os.environ.get("ESTOQUE_USUARIO", "equipe")
SENHA_HASH = os.environ["ESTOQUE_SENHA_HASH"]


# ---------- Regras (sem banco, faceis de testar) ----------
def calcular_saldo(entradas, retiradas):
    return entradas - retiradas


def precisa_repor(saldo, minimo):
    return saldo <= minimo


# ---------- Acesso ao MySQL ----------
def conectar():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "estoque_recanto"),
        cursorclass=pymysql.cursors.DictCursor,
    )


SQL_PRODUTOS = """
    SELECT p.id, p.nome, p.estoque_minimo,
           COALESCE(SUM(CASE WHEN m.tipo = 'entrada' THEN m.quantidade END), 0) AS entradas,
           COALESCE(SUM(CASE WHEN m.tipo = 'retirada' THEN m.quantidade END), 0) AS retiradas
    FROM produto p LEFT JOIN movimentacao m ON m.produto_id = p.id
"""


def _montar(linha):
    saldo = calcular_saldo(int(linha["entradas"]), int(linha["retiradas"]))
    return {"id": linha["id"], "nome": linha["nome"], "estoque_minimo": linha["estoque_minimo"],
            "saldo": saldo, "repor": precisa_repor(saldo, linha["estoque_minimo"])}


def listar_produtos():
    with conectar() as con, con.cursor() as cur:
        cur.execute(SQL_PRODUTOS + " GROUP BY p.id ORDER BY p.nome")
        produtos = [_montar(linha) for linha in cur.fetchall()]
    # Itens que precisam repor aparecem primeiro.
    return sorted(produtos, key=lambda p: not p["repor"])


def buscar_produto(produto_id):
    with conectar() as con, con.cursor() as cur:
        cur.execute(SQL_PRODUTOS + " WHERE p.id = %s GROUP BY p.id", (produto_id,))
        linha = cur.fetchone()
        return _montar(linha) if linha else None


def inserir_produto(nome, minimo):
    with conectar() as con, con.cursor() as cur:
        try:
            cur.execute("INSERT INTO produto (nome, estoque_minimo) VALUES (%s, %s)", (nome, minimo))
        except pymysql.err.IntegrityError:
            raise ValueError("duplicado")
        con.commit()


def inserir_movimentacao(produto_id, tipo, quantidade):
    """Grava a movimentacao. Na retirada, trava o produto e confere o saldo
    na mesma transacao, para o saldo nunca ficar negativo."""
    with conectar() as con, con.cursor() as cur:
        cur.execute("SELECT id FROM produto WHERE id = %s FOR UPDATE", (produto_id,))
        if tipo == "retirada":
            cur.execute(SQL_PRODUTOS + " WHERE p.id = %s GROUP BY p.id", (produto_id,))
            saldo = _montar(cur.fetchone())["saldo"]
            if quantidade > saldo:
                con.rollback()
                raise ValueError(saldo)
        cur.execute("INSERT INTO movimentacao (produto_id, tipo, quantidade) VALUES (%s, %s, %s)",
                    (produto_id, tipo, quantidade))
        con.commit()


# ---------- Telas ----------
@app.before_request
def exigir_login():
    if request.endpoint not in ("login", "static") and not session.get("logado"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        if request.form.get("usuario") == USUARIO and check_password_hash(SENHA_HASH, request.form.get("senha", "")):
            session["logado"] = True
            return redirect(url_for("estoque"))
        erro = "Usuario ou senha incorretos."
    return render_template("login.html", erro=erro)


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def estoque():
    alterado = request.args.get("alterado", "")
    return render_template("estoque.html", produtos=listar_produtos(),
                           alterado=int(alterado) if alterado.isdigit() else None)


@app.route("/produto/novo", methods=["GET", "POST"])
def novo_produto():
    erro = None
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        minimo = request.form.get("estoque_minimo", "")
        if not nome or not minimo.isdigit():
            erro = "Informe o nome e um minimo (0 ou mais)."
        else:
            try:
                inserir_produto(nome[:80], int(minimo))
                return redirect(url_for("estoque"))
            except ValueError:
                erro = "Ja existe um produto com esse nome."
    return render_template("novo_produto.html", erro=erro)


@app.route("/movimentar", methods=["GET", "POST"])
def movimentar():
    erro = None
    escolhido = request.values.get("produto_id", "")
    tipo_escolhido = request.values.get("tipo", "retirada")
    if request.method == "POST":
        pid = request.form.get("produto_id", "")
        tipo = request.form.get("tipo")
        qtd = request.form.get("quantidade", "")
        produto = buscar_produto(int(pid)) if pid.isdigit() else None
        if not produto or tipo not in ("entrada", "retirada") or not qtd.isdigit() or int(qtd) <= 0:
            erro = "Escolha o produto, o tipo e uma quantidade maior que zero."
        else:
            try:
                inserir_movimentacao(produto["id"], tipo, int(qtd))
                return redirect(url_for("resultado", produto_id=produto["id"], tipo=tipo))
            except ValueError as e:
                erro = f"Quantidade maior que o saldo ({e.args[0]})."
    produtos = listar_produtos()
    fixo = next((p for p in produtos if str(p["id"]) == escolhido), None)
    return render_template("movimentar.html", produtos=produtos, fixo=fixo,
                           tipo=tipo_escolhido if tipo_escolhido in ("entrada", "retirada") else "retirada", erro=erro)


@app.route("/resultado")
def resultado():
    pid = request.args.get("produto_id", "")
    produto = buscar_produto(int(pid)) if pid.isdigit() else None
    tipo = request.args.get("tipo", "")
    repor = [p for p in listar_produtos() if p["repor"]]
    return render_template("resultado.html", produto=produto, tipo=tipo, repor=repor)


if __name__ == "__main__":
    app.run(debug=False)
