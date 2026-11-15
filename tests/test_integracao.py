"""Testes de integracao: rotas do Flask gravando e lendo no MySQL."""
import app as estoque


def produto(nome):
    return next(p for p in estoque.listar_produtos() if p["nome"] == nome)


def test_sem_login_vai_para_tela_de_login(banco):
    with estoque.app.test_client() as c:
        resp = c.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


def test_login_com_senha_errada(banco):
    with estoque.app.test_client() as c:
        resp = c.post("/login", data={"usuario": "equipe", "senha": "errada"})
        assert "Usuario ou senha incorretos" in resp.get_data(as_text=True)


def test_cadastra_produto_e_mostra_repor(cliente):
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    p = produto("Sabonete")
    assert p["saldo"] == 0 and p["repor"] is True
    assert "⚠ Repor" in cliente.get("/").get_data(as_text=True)


def test_nao_aceita_produto_repetido(cliente):
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    resp = cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "5"})
    assert "Ja existe um produto" in resp.get_data(as_text=True)


def test_nao_aceita_minimo_invalido(cliente):
    resp = cliente.post("/produto/novo", data={"nome": "Shampoo", "estoque_minimo": "-1"})
    assert "Informe o nome" in resp.get_data(as_text=True)


def test_entrada_aumenta_saldo_e_tira_aviso(cliente):
    cliente.post("/produto/novo", data={"nome": "Creme dental", "estoque_minimo": "6"})
    pid = produto("Creme dental")["id"]
    resp = cliente.post("/movimentar", data={"produto_id": pid, "tipo": "entrada", "quantidade": "12"},
                        follow_redirects=True)
    assert "Entrada registrada" in resp.get_data(as_text=True)
    p = produto("Creme dental")
    assert p["saldo"] == 12 and p["repor"] is False


def test_retirada_maior_que_saldo_e_bloqueada(cliente):
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    pid = produto("Sabonete")["id"]
    cliente.post("/movimentar", data={"produto_id": pid, "tipo": "entrada", "quantidade": "4"})
    resp = cliente.post("/movimentar", data={"produto_id": pid, "tipo": "retirada", "quantidade": "5"})
    assert "Quantidade maior que o saldo (4)" in resp.get_data(as_text=True)
    assert produto("Sabonete")["saldo"] == 4


def test_retirada_grava_e_aparece_em_precisa_repor(cliente):
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    pid = produto("Sabonete")["id"]
    cliente.post("/movimentar", data={"produto_id": pid, "tipo": "entrada", "quantidade": "4"})
    resp = cliente.post("/movimentar", data={"produto_id": pid, "tipo": "retirada", "quantidade": "2"},
                        follow_redirects=True)
    texto = resp.get_data(as_text=True)
    assert "Retirada registrada" in texto and "saldo 2" in texto and "⚠ Repor" in texto


def test_movimentacao_com_dados_invalidos(cliente):
    resp = cliente.post("/movimentar", data={"produto_id": "", "tipo": "entrada", "quantidade": "0"})
    assert "Escolha o produto" in resp.get_data(as_text=True)


def test_sair_encerra_sessao(cliente):
    cliente.get("/sair")
    assert cliente.get("/").status_code == 302


def test_itens_para_repor_aparecem_primeiro(cliente):
    cliente.post("/produto/novo", data={"nome": "Creme dental", "estoque_minimo": "6"})
    cliente.post("/movimentar", data={"produto_id": produto("Creme dental")["id"], "tipo": "entrada", "quantidade": "12"})
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    nomes = [p["nome"] for p in estoque.listar_produtos()]
    assert nomes == ["Sabonete", "Creme dental"]


def test_botao_da_linha_ja_escolhe_o_produto(cliente):
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    pid = produto("Sabonete")["id"]
    texto = cliente.get(f"/movimentar?produto_id={pid}&tipo=retirada").get_data(as_text=True)
    assert "Retirada de Sabonete" in texto
    assert f'name="produto_id" value="{pid}"' in texto


def test_linha_alterada_fica_destacada(cliente):
    cliente.post("/produto/novo", data={"nome": "Sabonete", "estoque_minimo": "10"})
    pid = produto("Sabonete")["id"]
    assert "alterado" in cliente.get(f"/?alterado={pid}").get_data(as_text=True)
