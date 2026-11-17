# Estoque do Recanto

MVP para controle de itens de higiene: cadastro, entradas, retiradas e aviso de reposição.

## Validação local com dados simulados

O aplicativo está temporariamente sem banco de dados. Há três produtos fictícios, e os dados são mantidos apenas em memória: **as alterações são perdidas ao reiniciar**. A senha fixa é somente para testes locais.

1. Instale as dependências: `pip install -r requirements.txt`.
2. Execute `python app.py` e acesse http://127.0.0.1:5000.
3. Entre com usuário `equipe` e senha `123456`.

O código anterior conectado ao MySQL está preservado em `app_mysql.py`, junto com `banco.sql` e `.env.example`. Será necessário restaurar e configurar essa versão para usar o banco novamente.

## Testes

Instale as dependências com `pip install -r requirements-dev.txt` e execute `pytest -v --cov=app`. Os testes atuais usam dados em memória, sem conectar ao MySQL.

A tela inicial apresenta um dashboard com o resumo de reposição, gráfico ApexCharts e as últimas cinco movimentações feitas desde que o aplicativo foi iniciado. Na tela de estoque há busca por nome e filtro para produtos que precisam ser repostos. O gráfico usa CDN e precisa de internet; os números e listas continuam disponíveis se ele não carregar. Dados e histórico são simulados e se apagam ao reiniciar.

## Publicação no Render

A versão de demonstração usa a branch `Fase-04`, Python e Gunicorn, com dados em memória.

- Build Command — `pip install -r requirements.txt`
- Start Command — `gunicorn --workers 1 --threads 1 --bind 0.0.0.0:$PORT app:app`
- Variável de ambiente — `SECRET_KEY`, gerada no painel do Render.

O único processo mantém as movimentações da demonstração no mesmo espaço de memória. Os dados voltam ao estado inicial quando o serviço reinicia.
