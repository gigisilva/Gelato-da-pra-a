# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, render_template
import sqlite3
from pathlib import Path
from datetime import datetime, date

app = Flask(**name**, template_folder="templates", static_folder="static")

DB = Path(**file**).with_name("estoque.db")

CATEGORIAS = [
"Sorvete",
"Cobertura",
"Complemento",
"Açaí",
"Casquinha",
"Picolé"
]

FORMAS_PAGAMENTO = [
"Dinheiro",
"Pix",
"Cartão de débito",
"Cartão de crédito"
]

PRECO_INGREDIENTES = {
"leite": 4.50,
"creme_de_leite": 6.00,
"acucar": 3.00,
"ovos": 10.00,
"chocolate": 12.00,
"morango": 8.00,
"baunilha": 15.00,
"corante": 5.00,
"essencia": 7.00
}

RECEITAS = {
"Chocolate": {
"leite": 0.5,
"creme_de_leite": 1,
"acucar": 0.2,
"chocolate": 0.3
},
"Morango": {
"leite": 0.5,
"creme_de_leite": 1,
"acucar": 0.2,
"morango": 0.4
},
"Baunilha": {
"leite": 0.5,
"creme_de_leite": 1,
"acucar": 0.2,
"baunilha": 0.1
},
"Creme": {
"leite": 0.5,
"creme_de_leite": 2,
"acucar": 0.2,
"ovos": 2
}
}

PRECO_VENDA = {
"Chocolate": 25.00,
"Morango": 28.00,
"Baunilha": 22.00,
"Creme": 24.00
}

def db():
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
c.execute("PRAGMA foreign_keys = ON")
return c

def agora():
return datetime.now().isoformat(timespec="seconds")

def hoje():
return date.today().isoformat()

def calcular_custo_receita(sabor):
receita = RECEITAS.get(sabor, {})

```
return round(
    sum(
        PRECO_INGREDIENTES.get(ingrediente, 0) * quantidade
        for ingrediente, quantidade in receita.items()
    ),
    2
)
```

def custo_sabor(c, sabor):
row = c.execute("""
SELECT custo
FROM sabores
WHERE LOWER(nome) = LOWER(?)
""", (sabor,)).fetchone()

```
if row:
    return float(row["custo"])

return calcular_custo_receita(sabor)
```

def preco_sabor(c, sabor):
row = c.execute("""
SELECT preco
FROM sabores
WHERE LOWER(nome) = LOWER(?)
""", (sabor,)).fetchone()

```
if row:
    return float(row["preco"])

return float(PRECO_VENDA.get(sabor, 0))
```

def init_db():
c = db()

```
try:
    c.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            sabor TEXT,
            estoque_inicial REAL NOT NULL DEFAULT 0,
            estoque_minimo REAL NOT NULL DEFAULT 0,
            unidade TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantidade REAL NOT NULL,
            responsavel TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            observacao TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            sabor TEXT NOT NULL,
            quantidade REAL NOT NULL,
            preco_unitario REAL NOT NULL,
            faturamento REAL NOT NULL,
            custo REAL NOT NULL,
            lucro REAL NOT NULL,
            forma_pagamento TEXT NOT NULL,
            responsavel TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            dia TEXT NOT NULL,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS caixa_movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            forma_pagamento TEXT,
            venda_id INTEGER,
            responsavel TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            dia TEXT NOT NULL,
            FOREIGN KEY(venda_id) REFERENCES vendas(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS dias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL UNIQUE,
            abertura_em TEXT,
            fechamento_em TEXT,
            saldo_inicial REAL NOT NULL DEFAULT 0,
            saldo_final REAL,
            saldo_esperado REAL,
            diferenca REAL,
            faturamento REAL NOT NULL DEFAULT 0,
            custo_vendas REAL NOT NULL DEFAULT 0,
            lucro REAL NOT NULL DEFAULT 0,
            despesas REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'fechado'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sabores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            preco REAL NOT NULL DEFAULT 0,
            custo REAL NOT NULL DEFAULT 0,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto
        ON movimentacoes(produto_id)
    """)

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_vendas_dia
        ON vendas(dia)
    """)

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_caixa_dia
        ON caixa_movimentacoes(dia)
    """)

    criado = agora()

    for nome, preco in PRECO_VENDA.items():
        c.execute("""
            INSERT OR IGNORE INTO sabores (
                nome,
                preco,
                custo,
                criado_em,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            nome,
            preco,
            calcular_custo_receita(nome),
            criado,
            criado
        ))

    c.commit()
finally:
    c.close()
```

def produto_completo(row, c):
p = dict(row)

```
entradas = c.execute("""
    SELECT COALESCE(SUM(quantidade), 0)
    FROM movimentacoes
    WHERE produto_id = ?
    AND tipo = 'Entrada'
""", (p["id"],)).fetchone()[0]

saidas = c.execute("""
    SELECT COALESCE(SUM(quantidade), 0)
    FROM movimentacoes
    WHERE produto_id = ?
    AND tipo = 'Saída'
""", (p["id"],)).fetchone()[0]

p["entradas"] = entradas
p["saidas"] = saidas
p["estoque_atual"] = p["estoque_inicial"] + entradas - saidas
p["atual"] = p["estoque_atual"]

return p
```

def garantir_dia(c, dia=None):
dia = dia or hoje()

```
row = c.execute("""
    SELECT *
    FROM dias
    WHERE dia = ?
""", (dia,)).fetchone()

if not row:
    c.execute("""
        INSERT INTO dias (
            dia,
            abertura_em,
            saldo_inicial,
            status
        )
        VALUES (?, ?, 0, 'aberto')
    """, (dia, agora()))

    c.commit()

    row = c.execute("""
        SELECT *
        FROM dias
        WHERE dia = ?
    """, (dia,)).fetchone()

return row
```

def resumo_dia(c, dia):
dia_row = c.execute("""
SELECT *
FROM dias
WHERE dia = ?
""", (dia,)).fetchone()

```
faturamento = c.execute("""
    SELECT COALESCE(SUM(faturamento), 0)
    FROM vendas
    WHERE dia = ?
""", (dia,)).fetchone()[0]

custo = c.execute("""
    SELECT COALESCE(SUM(custo), 0)
    FROM vendas
    WHERE dia = ?
""", (dia,)).fetchone()[0]

despesas = c.execute("""
    SELECT COALESCE(SUM(valor), 0)
    FROM caixa_movimentacoes
    WHERE dia = ?
    AND tipo = 'Saída'
""", (dia,)).fetchone()[0]

entradas_caixa = c.execute("""
    SELECT COALESCE(SUM(valor), 0)
    FROM caixa_movimentacoes
    WHERE dia = ?
    AND tipo = 'Entrada'
""", (dia,)).fetchone()[0]

saldo_inicial = (
    float(dia_row["saldo_inicial"])
    if dia_row
    else 0
)

saldo_caixa = saldo_inicial + entradas_caixa - despesas
lucro = faturamento - custo

return {
    "faturamento": round(faturamento, 2),
    "custo": round(custo, 2),
    "lucro": round(lucro, 2),
    "despesas": round(despesas, 2),
    "saldo_caixa": round(saldo_caixa, 2),
    "status": dia_row["status"] if dia_row else "não aberto",
    "saldo_inicial": round(saldo_inicial, 2)
}
```

@app.route("/")
def index():
return render_template("index.html")

@app.get("/api/config")
def config():
c = db()

```
try:
    rows = c.execute("""
        SELECT nome, preco
        FROM sabores
        ORDER BY nome
    """).fetchall()

    sabores = [row["nome"] for row in rows]
    precos = {
        row["nome"]: row["preco"]
        for row in rows
    }

    return jsonify({
        "categorias": CATEGORIAS,
        "formas_pagamento": FORMAS_PAGAMENTO,
        "sabores": sabores,
        "precos": precos
    })
finally:
    c.close()
```

@app.get("/api/sabores")
def listar_sabores():
c = db()

```
try:
    rows = c.execute("""
        SELECT *
        FROM sabores
        ORDER BY nome
    """).fetchall()

    return jsonify([dict(row) for row in rows])
finally:
    c.close()
```

@app.post("/api/sabores")
def criar_sabor():
data = request.get_json(silent=True) or {}

```
nome = str(data.get("nome", "")).strip()

try:
    preco = float(data.get("preco", 0))
    custo = float(data.get("custo", 0))
except (TypeError, ValueError):
    return jsonify({"erro": "Preço ou custo inválido"}), 400

if not nome:
    return jsonify({"erro": "Informe o nome do sabor"}), 400

if preco <= 0:
    return jsonify({"erro": "Informe um preço maior que zero"}), 400

if custo < 0:
    return jsonify({"erro": "O custo não pode ser negativo"}), 400

c = db()

try:
    existente = c.execute("""
        SELECT id
        FROM sabores
        WHERE LOWER(nome) = LOWER(?)
    """, (nome,)).fetchone()

    if existente:
        return jsonify({
            "erro": "Esse sabor já está cadastrado"
        }), 400

    criado = agora()

    cur = c.execute("""
        INSERT INTO sabores (
            nome,
            preco,
            custo,
            criado_em,
            atualizado_em
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        nome,
        preco,
        custo,
        criado,
        criado
    ))

    c.commit()

    return jsonify({
        "ok": True,
        "id": cur.lastrowid,
        "nome": nome,
        "preco": preco,
        "custo": custo
    }), 201
finally:
    c.close()
```

@app.put("/api/sabores/[int:sabor_id](int:sabor_id)")
def atualizar_sabor(sabor_id):
data = request.get_json(silent=True) or {}

```
nome = str(data.get("nome", "")).strip()

try:
    preco = float(data.get("preco", 0))
    custo = float(data.get("custo", 0))
except (TypeError, ValueError):
    return jsonify({"erro": "Preço ou custo inválido"}), 400

if not nome:
    return jsonify({"erro": "Informe o nome do sabor"}), 400

if preco <= 0:
    return jsonify({"erro": "Informe um preço maior que zero"}), 400

if custo < 0:
    return jsonify({"erro": "O custo não pode ser negativo"}), 400

c = db()

try:
    sabor = c.execute("""
        SELECT id
        FROM sabores
        WHERE id = ?
    """, (sabor_id,)).fetchone()

    if not sabor:
        return jsonify({"erro": "Sabor não encontrado"}), 404

    duplicado = c.execute("""
        SELECT id
        FROM sabores
        WHERE LOWER(nome) = LOWER(?)
        AND id != ?
    """, (nome, sabor_id)).fetchone()

    if duplicado:
        return jsonify({
            "erro": "Esse sabor já está cadastrado"
        }), 400

    c.execute("""
        UPDATE sabores
        SET nome = ?,
            preco = ?,
            custo = ?,
            atualizado_em = ?
        WHERE id = ?
    """, (
        nome,
        preco,
        custo,
        agora(),
        sabor_id
    ))

    c.commit()

    return jsonify({
        "ok": True,
        "id": sabor_id,
        "nome": nome,
        "preco": preco,
        "custo": custo
    })
finally:
    c.close()
```

@app.get("/api/produtos")
def listar_produtos():
c = db()

```
try:
    rows = c.execute("""
        SELECT *
        FROM produtos
        ORDER BY atualizado_em DESC, id DESC
    """).fetchall()

    return jsonify([
        produto_completo(row, c)
        for row in rows
    ])
finally:
    c.close()
```

@app.post("/api/produtos")
def criar_produto():
data = request.get_json(silent=True) or {}

```
nome = str(data.get("nome", "")).strip()
categoria = str(data.get("categoria", "")).strip()
sabor = str(data.get("sabor", "")).strip()
unidade = str(data.get("unidade", "unidade")).strip()

try:
    estoque_inicial = float(
        data.get("estoque_inicial", 0)
    )
    estoque_minimo = float(
        data.get("estoque_minimo", 0)
    )
except (TypeError, ValueError):
    return jsonify({
        "erro": "Quantidade de estoque inválida"
    }), 400

if not nome:
    return jsonify({
        "erro": "Informe o nome do produto"
    }), 400

if not categoria:
    return jsonify({
        "erro": "Informe a categoria"
    }), 400

if estoque_inicial < 0 or estoque_minimo < 0:
    return jsonify({
        "erro": "O estoque não pode ser negativo"
    }), 400

c = db()

try:
    criado = agora()

    cur = c.execute("""
        INSERT INTO produtos (
            nome,
            categoria,
            sabor,
            estoque_inicial,
            estoque_minimo,
            unidade,
            criado_em,
            atualizado_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome,
        categoria,
        sabor,
        estoque_inicial,
        estoque_minimo,
        unidade,
        criado,
        criado
    ))

    produto_id = cur.lastrowid

    c.commit()

    row = c.execute("""
        SELECT *
        FROM produtos
        WHERE id = ?
    """, (produto_id,)).fetchone()

    return jsonify(
        produto_completo(row, c)
    ), 201
finally:
    c.close()
```

@app.post("/api/movimentacoes")
def criar_movimentacao():
data = request.get_json(silent=True) or {}

```
try:
    produto_id = int(data.get("produto_id"))
    quantidade = float(data.get("quantidade", 0))
except (TypeError, ValueError):
    return jsonify({
        "erro": "Produto ou quantidade inválida"
    }), 400

tipo = str(data.get("tipo", "")).strip()

if tipo.lower() == "entrada":
    tipo = "Entrada"

if tipo.lower() in ("saida", "saída"):
    tipo = "Saída"

responsavel = str(
    data.get("responsavel", "Sistema")
).strip()

observacao = str(
    data.get("observacao", "")
).strip()

if tipo not in ("Entrada", "Saída"):
    return jsonify({
        "erro": "Tipo de movimentação inválido"
    }), 400

if quantidade <= 0:
    return jsonify({
        "erro": "A quantidade deve ser maior que zero"
    }), 400

c = db()

try:
    produto = c.execute("""
        SELECT *
        FROM produtos
        WHERE id = ?
    """, (produto_id,)).fetchone()

    if not produto:
        return jsonify({
            "erro": "Produto não encontrado"
        }), 404

    atual = produto_completo(
        produto,
        c
    )["atual"]

    if tipo == "Saída" and quantidade > atual:
        return jsonify({
            "erro": (
                f"Estoque insuficiente. "
                f"Disponível: {atual:g}"
            )
        }), 400

    criado = agora()

    c.execute("""
        INSERT INTO movimentacoes (
            produto_id,
            tipo,
            quantidade,
            responsavel,
            criado_em,
            observacao
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        produto_id,
        tipo,
        quantidade,
        responsavel,
        criado,
        observacao
    ))

    c.execute("""
        UPDATE produtos
        SET atualizado_em = ?
        WHERE id = ?
    """, (criado, produto_id))

    c.commit()

    return jsonify({
        "ok": True,
        "produto": produto_completo(
            c.execute("""
                SELECT *
                FROM produtos
                WHERE id = ?
            """, (produto_id,)).fetchone(),
            c
        )
    }), 201
finally:
    c.close()
```

@app.get("/api/movimentacoes")
def listar_movimentacoes():
c = db()

```
try:
    rows = c.execute("""
        SELECT
            m.*,
            p.nome AS produto,
            p.nome AS produto_nome,
            p.unidade
        FROM movimentacoes m
        JOIN produtos p
            ON p.id = m.produto_id
        ORDER BY m.id DESC
    """).fetchall()

    resultado = []

    for row in rows:
        item = dict(row)
        item["data"] = item["criado_em"]
        resultado.append(item)

    return jsonify(resultado)
finally:
    c.close()
```

@app.get("/api/receitas")
def listar_receitas():
c = db()

```
try:
    rows = c.execute("""
        SELECT *
        FROM sabores
        ORDER BY nome
    """).fetchall()

    resultado = []

    for row in rows:
        nome = row["nome"]

        resultado.append({
            "sabor": nome,
            "ingredientes": RECEITAS.get(nome, {}),
            "custo": row["custo"],
            "preco_venda": row["preco"],
            "lucro": round(
                row["preco"] - row["custo"],
                2
            )
        })

    return jsonify(resultado)
finally:
    c.close()
```

@app.post("/api/producao")
def registrar_producao():
data = request.get_json(silent=True) or {}

```
sabor = str(data.get("sabor", "")).strip()
responsavel = str(
    data.get("responsavel", "Sistema")
).strip()

try:
    quantidade = float(
        data.get("quantidade", 0)
    )
except (TypeError, ValueError):
    return jsonify({
        "erro": "Quantidade inválida"
    }), 400

if not sabor:
    return jsonify({
        "erro": "Selecione um sabor"
    }), 400

if quantidade <= 0:
    return jsonify({
        "erro": "A quantidade deve ser maior que zero"
    }), 400

c = db()

try:
    produto = c.execute("""
        SELECT *
        FROM produtos
        WHERE sabor = ?
        ORDER BY id
        LIMIT 1
    """, (sabor,)).fetchone()

    if not produto:
        return jsonify({
            "erro": (
                "Cadastre um produto com esse "
                "sabor antes de registrar a produção"
            )
        }), 400

    criado = agora()

    c.execute("""
        INSERT INTO movimentacoes (
            produto_id,
            tipo,
            quantidade,
            responsavel,
            criado_em,
            observacao
        )
        VALUES (?, 'Entrada', ?, ?, ?, ?)
    """, (
        produto["id"],
        quantidade,
        responsavel,
        criado,
        f"Produção de {sabor}"
    ))

    c.execute("""
        UPDATE produtos
        SET atualizado_em = ?
        WHERE id = ?
    """, (criado, produto["id"]))

    c.commit()

    return jsonify({"ok": True})
finally:
    c.close()
```

@app.get("/api/vendas")
def listar_vendas():
c = db()

```
try:
    rows = c.execute("""
        SELECT *
        FROM vendas
        ORDER BY id DESC
    """).fetchall()

    resultado = []

    for row in rows:
        item = dict(row)
        item["total"] = item["faturamento"]
        item["valor"] = item["faturamento"]
        item["data"] = item["criado_em"]
        resultado.append(item)

    return jsonify(resultado)
finally:
    c.close()
```

@app.post("/api/vendas")
def criar_venda():
data = request.get_json(silent=True) or {}

```
sabor = str(data.get("sabor", "")).strip()
forma = str(
    data.get("forma_pagamento", "")
).strip()

responsavel = str(
    data.get("responsavel", "Sistema")
).strip()

try:
    quantidade = float(
        data.get("quantidade", 0)
    )
except (TypeError, ValueError):
    return jsonify({
        "erro": "Quantidade inválida"
    }), 400

if not sabor:
    return jsonify({
        "erro": "Selecione um sabor"
    }), 400

if quantidade <= 0:
    return jsonify({
        "erro": "A quantidade deve ser maior que zero"
    }), 400

if forma not in FORMAS_PAGAMENTO:
    return jsonify({
        "erro": "Forma de pagamento inválida"
    }), 400

c = db()

try:
    dia = hoje()
    dia_row = garantir_dia(c, dia)

    if dia_row["status"] != "aberto":
        return jsonify({
            "erro": (
                "O dia precisa estar aberto "
                "para registrar vendas"
            )
        }), 400

    produto = c.execute("""
        SELECT *
        FROM produtos
        WHERE sabor = ?
        ORDER BY id
        LIMIT 1
    """, (sabor,)).fetchone()

    if not produto:
        return jsonify({
            "erro": (
                "Cadastre um produto com esse "
                "sabor antes de registrar a venda"
            )
        }), 400

    produto_atual = produto_completo(
        produto,
        c
    )["atual"]

    if quantidade > produto_atual:
        return jsonify({
            "erro": (
                f"Estoque insuficiente. "
                f"Disponível: {produto_atual:g}"
            )
        }), 400

    preco = preco_sabor(c, sabor)
    custo_unitario = custo_sabor(c, sabor)

    if preco <= 0:
        return jsonify({
            "erro": "Preço de venda inválido"
        }), 400

    faturamento = round(
        preco * quantidade,
        2
    )

    custo = round(
        custo_unitario * quantidade,
        2
    )

    lucro = round(
        faturamento - custo,
        2
    )

    criado = agora()

    cur = c.execute("""
        INSERT INTO vendas (
            produto_id,
            sabor,
            quantidade,
            preco_unitario,
            faturamento,
            custo,
            lucro,
            forma_pagamento,
            responsavel,
            criado_em,
            dia
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        produto["id"],
        sabor,
        quantidade,
        preco,
        faturamento,
        custo,
        lucro,
        forma,
        responsavel,
        criado,
        dia
    ))

    venda_id = cur.lastrowid

    c.execute("""
        INSERT INTO movimentacoes (
            produto_id,
            tipo,
            quantidade,
            responsavel,
            criado_em,
            observacao
        )
        VALUES (?, 'Saída', ?, ?, ?, ?)
    """, (
        produto["id"],
        quantidade,
        responsavel,
        criado,
        f"Venda de {sabor}"
    ))

    c.execute("""
        INSERT INTO caixa_movimentacoes (
            tipo,
            descricao,
            valor,
            forma_pagamento,
            venda_id,
            responsavel,
            criado_em,
            dia
        )
        VALUES (
            'Entrada',
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
    """, (
        f"Venda de {sabor}",
        faturamento,
        forma,
        venda_id,
        responsavel,
        criado,
        dia
    ))

    c.execute("""
        UPDATE produtos
        SET atualizado_em = ?
        WHERE id = ?
    """, (criado, produto["id"]))

    c.commit()

    return jsonify({
        "ok": True,
        "faturamento": faturamento,
        "custo": custo,
        "lucro": lucro
    }), 201
finally:
    c.close()
```

@app.get("/api/caixa")
def listar_caixa():
c = db()

```
try:
    rows = c.execute("""
        SELECT *
        FROM caixa_movimentacoes
        ORDER BY id DESC
    """).fetchall()

    resultado = []

    for row in rows:
        item = dict(row)
        item["data"] = item["criado_em"]
        resultado.append(item)

    return jsonify(resultado)
finally:
    c.close()
```

@app.post("/api/caixa")
def criar_caixa():
data = request.get_json(silent=True) or {}

```
tipo = str(data.get("tipo", "")).strip()
descricao = str(
    data.get("descricao", "")
).strip()

responsavel = str(
    data.get("responsavel", "Sistema")
).strip()

forma = str(
    data.get("forma_pagamento", "")
).strip() or None

try:
    valor = float(data.get("valor", 0))
except (TypeError, ValueError):
    return jsonify({
        "erro": "Valor inválido"
    }), 400

if tipo.lower() == "entrada":
    tipo = "Entrada"

if tipo.lower() in ("saida", "saída"):
    tipo = "Saída"

if tipo not in ("Entrada", "Saída"):
    return jsonify({
        "erro": "Tipo inválido"
    }), 400

if valor <= 0:
    return jsonify({
        "erro": "O valor deve ser maior que zero"
    }), 400

if not descricao:
    return jsonify({
        "erro": "Informe uma descrição"
    }), 400

c = db()

try:
    dia = hoje()
    dia_row = garantir_dia(c, dia)

    if dia_row["status"] != "aberto":
        return jsonify({
            "erro": "O dia precisa estar aberto"
        }), 400

    c.execute("""
        INSERT INTO caixa_movimentacoes (
            tipo,
            descricao,
            valor,
            forma_pagamento,
            venda_id,
            responsavel,
            criado_em,
            dia
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            NULL,
            ?,
            ?,
            ?
        )
    """, (
        tipo,
        descricao,
        valor,
        forma,
        responsavel,
        agora(),
        dia
    ))

    c.commit()

    return jsonify({"ok": True}), 201
finally:
    c.close()
```

@app.get("/api/resumo")
def resumo():
c = db()

```
try:
    produtos = c.execute("""
        SELECT *
        FROM produtos
    """).fetchall()

    completos = [
        produto_completo(row, c)
        for row in produtos
    ]

    baixo = [
        p for p in completos
        if p["atual"] <= p["estoque_minimo"]
        and p["atual"] > 0
    ]

    esgotados = [
        p for p in completos
        if p["atual"] <= 0
    ]

    vendas = c.execute("""
        SELECT COALESCE(SUM(quantidade), 0)
        FROM vendas
        WHERE dia = ?
    """, (hoje(),)).fetchone()[0]

    financeiro = resumo_dia(c, hoje())

    return jsonify({
        "produtos": len(completos),
        "produtos_cadastrados": len(completos),
        "estoque_total": sum(
            max(0, p["atual"])
            for p in completos
        ),
        "itens_estoque": sum(
            max(0, p["atual"])
            for p in completos
        ),
        "estoque_baixo": len(baixo),
        "esgotados": len(esgotados),
        "itens_vendidos": vendas,
        "alertas": [
            {
                "id": p["id"],
                "nome": p["nome"],
                "atual": p["atual"],
                "minimo": p["estoque_minimo"],
                "categoria": p["categoria"]
            }
            for p in baixo + esgotados
        ],
        "receita": financeiro["faturamento"],
        "faturamento_dia": financeiro["faturamento"],
        "custo": financeiro["custo"],
        "custo_dia": financeiro["custo"],
        "lucro": financeiro["lucro"],
        "lucro_dia": financeiro["lucro"],
        "despesas": financeiro["despesas"],
        "despesas_dia": financeiro["despesas"],
        "saldo_esperado": financeiro["saldo_caixa"],
        "saldo_caixa": financeiro["saldo_caixa"],
        "status_dia": financeiro["status"]
    })
finally:
    c.close()
```

@app.get("/api/dia")
def status_dia():
c = db()

```
try:
    row = c.execute("""
        SELECT *
        FROM dias
        WHERE dia = ?
    """, (hoje(),)).fetchone()

    if row:
        return jsonify(dict(row))

    return jsonify({
        "dia": hoje(),
        "status": "fechado",
        "saldo_inicial": 0
    })
finally:
    c.close()
```

@app.get("/api/dia/abrir")
def status_dia_abrir():
return status_dia()

@app.post("/api/dia/abrir")
def abrir_dia():
data = request.get_json(silent=True) or {}

```
dia = str(
    data.get("data") or hoje()
)

try:
    saldo_inicial = float(
        data.get("saldo_inicial", 0)
    )
except (TypeError, ValueError):
    return jsonify({
        "erro": "Saldo inicial inválido"
    }), 400

if saldo_inicial < 0:
    return jsonify({
        "erro": "O saldo inicial não pode ser negativo"
    }), 400

c = db()

try:
    existente = c.execute("""
        SELECT *
        FROM dias
        WHERE dia = ?
    """, (dia,)).fetchone()

    if existente:
        if existente["status"] == "aberto":
            return jsonify({
                "erro": "O dia já está aberto"
            }), 400

        c.execute("""
            UPDATE dias
            SET abertura_em = ?,
                fechamento_em = NULL,
                saldo_inicial = ?,
                saldo_final = NULL,
                saldo_esperado = NULL,
                diferenca = NULL,
                status = 'aberto'
            WHERE dia = ?
        """, (
            agora(),
            saldo_inicial,
            dia
        ))
    else:
        c.execute("""
            INSERT INTO dias (
                dia,
                abertura_em,
                saldo_inicial,
                status
            )
            VALUES (?, ?, ?, 'aberto')
        """, (
            dia,
            agora(),
            saldo_inicial
        ))

    c.commit()

    return jsonify({"ok": True})
finally:
    c.close()
```

@app.post("/api/dia/fechar")
def fechar_dia():
data = request.get_json(silent=True) or {}

```
dia = str(
    data.get("data") or hoje()
)

try:
    saldo_contado = float(
        data.get("saldo_contado", 0)
    )
except (TypeError, ValueError):
    return jsonify({
        "erro": "Saldo contado inválido"
    }), 400

c = db()

try:
    row = c.execute("""
        SELECT *
        FROM dias
        WHERE dia = ?
    """, (dia,)).fetchone()

    if not row:
        return jsonify({
            "erro": "O dia ainda não foi aberto"
        }), 400

    if row["status"] != "aberto":
        return jsonify({
            "erro": "O dia já está fechado"
        }), 400

    financeiro = resumo_dia(c, dia)

    esperado = financeiro["saldo_caixa"]
    diferenca = saldo_contado - esperado

    c.execute("""
        UPDATE dias
        SET fechamento_em = ?,
            saldo_final = ?,
            saldo_esperado = ?,
            diferenca = ?,
            faturamento = ?,
            custo_vendas = ?,
            lucro = ?,
            despesas = ?,
            status = 'fechado'
        WHERE dia = ?
    """, (
        agora(),
        saldo_contado,
        esperado,
        diferenca,
        financeiro["faturamento"],
        financeiro["custo"],
        financeiro["lucro"],
        financeiro["despesas"],
        dia
    ))

    c.commit()

    return jsonify({
        "ok": True,
        "saldo_esperado": round(
            esperado,
            2
        ),
        "diferenca": round(
            diferenca,
            2
        )
    })
finally:
    c.close()
```

@app.get("/api/fechamentos")
def fechamentos():
c = db()

```
try:
    rows = c.execute("""
        SELECT *
        FROM dias
        WHERE status = 'fechado'
        ORDER BY dia DESC
    """).fetchall()

    resultado = []

    for row in rows:
        item = dict(row)
        item["saldo_contado"] = item["saldo_final"]
        resultado.append(item)

    return jsonify(resultado)
finally:
    c.close()
```

@app.get("/api/fechamentos/<dia>")
def fechamento_dia(dia):
c = db()

```
try:
    row = c.execute("""
        SELECT *
        FROM dias
        WHERE dia = ?
    """, (dia,)).fetchone()

    if not row:
        return jsonify({
            "erro": "Fechamento não encontrado"
        }), 404

    return jsonify(dict(row))
finally:
    c.close()
```

@app.get("/api/financeiro")
def financeiro():
c = db()

```
try:
    data = resumo_dia(c, hoje())

    return jsonify({
        "data": hoje(),
        **data
    })
finally:
    c.close()
```

@app.post("/api/calcular")
def calcular():
data = request.get_json(silent=True) or {}

```
sabor = str(
    data.get("sabor", "")
).strip()

quantidade = float(
    data.get("quantidade", 1) or 1
)

c = db()

try:
    preco = preco_sabor(c, sabor)
    custo = custo_sabor(c, sabor)

    faturamento = preco * quantidade
    custo_total = custo * quantidade

    return jsonify({
        "sabor": sabor,
        "quantidade": quantidade,
        "preco_unitario": round(preco, 2),
        "custo_unitario": round(custo, 2),
        "faturamento": round(faturamento, 2),
        "custo": round(custo_total, 2),
        "lucro": round(
            faturamento - custo_total,
            2
        )
    })
finally:
    c.close()
```

init_db()

if **name** == "**main**":
app.run(
host="0.0.0.0",
port=5000,
debug=True
)
