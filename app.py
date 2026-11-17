"""Estoque do Recanto.

App Flask simples: produtos de higiene, entradas, retiradas e aviso Repor.
Regra principal: saldo = entradas - retiradas. Repor quando saldo <= minimo.
Modo temporario de validacao: dados ficticios em memoria, sem conexao ao MySQL.
"""
from datetime import datetime
import os

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-local-de-validacao")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Credenciais fixas apenas para validacao local.
USUARIO = "equipe"
SENHA = "123456"

# Dados ficticios: alteracoes sao perdidas ao reiniciar.
produtos_mock = [
    {"id": 1, "nome": "Sabonete", "estoque_minimo": 10, "saldo": 8},
    {"id": 2, "nome": "Fralda geriatrica", "estoque_minimo": 20, "saldo": 35},
    {"id": 3, "nome": "Creme dental", "estoque_minimo": 5, "saldo": 12},
]

movimentacoes_mock = []

# ---------- Regras (sem banco, faceis de testar) ----------
def calcular_saldo(entradas, retiradas):
    return entradas - retiradas


def precisa_repor(saldo, minimo):
    return saldo <= minimo


# ---------- Dados simulados em memoria ----------
def listar_produtos():
    produtos = [{**p, "repor": precisa_repor(p["saldo"], p["estoque_minimo"])}
                for p in produtos_mock]
    return sorted(produtos, key=lambda p: (not p["repor"], p["nome"].casefold()))


def buscar_produto(produto_id):
    return next((p for p in listar_produtos() if p["id"] == produto_id), None)


def inserir_produto(nome, minimo):
    if any(p["nome"].casefold() == nome.casefold() for p in produtos_mock):
        raise ValueError("duplicado")
    proximo_id = max((p["id"] for p in produtos_mock), default=0) + 1
    produtos_mock.append({"id": proximo_id, "nome": nome, "estoque_minimo": minimo, "saldo": 0})


def inserir_movimentacao(produto_id, tipo, quantidade):
    produto = next(p for p in produtos_mock if p["id"] == produto_id)
    if tipo == "retirada" and quantidade > produto["saldo"]:
        raise ValueError(produto["saldo"])
    produto["saldo"] += quantidade if tipo == "entrada" else -quantidade
    movimentacoes_mock.insert(0, {"produto": produto["nome"], "tipo": tipo, "quantidade": quantidade, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})

# ---------- Telas ----------
@app.before_request
def exigir_login():
    if request.endpoint not in ("login", "static") and not session.get("logado"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        if request.form.get("usuario") == USUARIO and request.form.get("senha", "") == SENHA:
            session["logado"] = True
            return redirect(url_for("inicio"))
        erro = "Usuario ou senha incorretos."
    return render_template("login.html", erro=erro)


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def inicio():
    produtos = listar_produtos()
    repor = [p for p in produtos if p["repor"]]
    return render_template("dashboard.html", produtos=produtos, repor=repor,
                           movimentacoes=movimentacoes_mock[:5])


@app.route("/estoque")
def estoque():
    alterado = request.args.get("alterado", "")
    busca = request.args.get("busca", "").strip()
    filtro = request.args.get("filtro", "todos")
    produtos = [p for p in listar_produtos() if busca.casefold() in p["nome"].casefold()
                and (filtro != "repor" or p["repor"])]
    return render_template("estoque.html", produtos=produtos, busca=busca, filtro=filtro,
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
