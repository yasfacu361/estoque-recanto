# Estoque do Recanto

Projeto de Software (T02). Controle simples dos produtos de higiene do Recanto da Vovó: cadastro de produto com quantidade mínima, entradas, retiradas e aviso **⚠ Repor**.


**Regra principal:** saldo = entradas − retiradas. O aviso Repor aparece quando o saldo fica igual ou menor que o mínimo. Uma retirada não pode deixar o saldo negativo.

Tecnologia: Python 3.12+, Flask, PyMySQL e MySQL 8. O saldo não fica gravado; ele é calculado a partir da tabela `movimentacao`.


## Como rodar

1. Crie o banco: `mysql -u root -p < banco.sql`
2. Instale as dependências: `pip install -r requirements.txt`
3. Gere o hash da senha da equipe:
   `python -c "from werkzeug.security import generate_password_hash as g; print(g('sua-senha'))"`
4. Defina as variáveis de ambiente listadas em `.env.example` (no Windows, `set NOME=valor`; no Linux, `export NOME=valor`).
5. `python app.py` e abra http://127.0.0.1:5000

O sistema começa vazio. Cadastre os produtos em **Novo produto** e registre as entradas.
