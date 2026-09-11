# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, send_file
import sqlite3
from pathlib import Path
from datetime import datetime, date

app = Flask(__name__)
DB = Path(__file__).with_name('estoque.db')

CATEGORIAS = ['Sorvete','Cobertura','Complemento','Açaí','Casquinha','Picolé']
FORMAS_PAGAMENTO = ['Dinheiro','Pix','Cartão de débito','Cartão de crédito']

PRECO_INGREDIENTES = {
    'leite': 4.50,
    'creme_de_leite': 6.00,
    'acucar': 3.00,
    'ovos': 10.00,
    'chocolate': 12.00,
    'morango': 8.00,
    'baunilha': 15.00,
    'corante': 5.00,
    'essencia': 7.00,
}

RECEITAS = {
    'Chocolate': {'leite': 0.5, 'creme_de_leite': 1, 'acucar': 0.2, 'chocolate': 0.3},
    'Morango': {'leite': 0.5, 'creme_de_leite': 1, 'acucar': 0.2, 'morango': 0.4},
    'Baunilha': {'leite': 0.5, 'creme_de_leite': 1, 'acucar': 0.2, 'baunilha': 0.1},
    'Creme': {'leite': 0.5, 'creme_de_leite': 2, 'acucar': 0.2, 'ovos': 2},
}

PRECO_VENDA = {
    'Chocolate': 25.00,
    'Morango': 28.00,
    'Baunilha': 22.00,
    'Creme': 24.00,
}

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    return c

def agora():
    return datetime.now().isoformat(timespec='seconds')

def init_db():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS produtos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        sabor TEXT,
        estoque_inicial INTEGER NOT NULL DEFAULT 0,
        estoque_minimo INTEGER NOT NULL DEFAULT 0,
        unidade TEXT NOT NULL,
        criado_em TEXT NOT NULL,
        atualizado_em TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS movimentacoes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        responsavel TEXT NOT NULL,
        criado_em TEXT NOT NULL,
        observacao TEXT,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendas(
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
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS caixa_movimentacoes(
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
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS dias(
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
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto ON movimentacoes(produto_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vendas_dia ON vendas(dia)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_caixa_dia ON caixa_movimentacoes(dia)')
    c.commit(); c.close()

def calcular_custo_producao(sabor):
    receita = RECEITAS.get(sabor)
    if not receita:
        return 0.0
    total = 0.0
    for ingrediente, quantidade in receita.items():
        preco = PRECO_INGREDIENTES.get(ingrediente, 0)
        total += preco * quantidade
    return round(total, 2)

def produto_completo(row, c):
    p = dict(row)
    entradas = c.execute("SELECT COALESCE(SUM(quantidade), 0) FROM movimentacoes WHERE produto_id = ? AND tipo = 'Entrada'", (p['id'],)).fetchone()[0]
    saidas = c.execute("SELECT COALESCE(SUM(quantidade), 0) FROM movimentacoes WHERE produto_id = ? AND tipo = 'Saída'", (p['id'],)).fetchone()[0]
    p['entradas'] = entradas
    p['saidas'] = saidas
    p['atual'] = p['estoque_inicial'] + entradas - saidas
    return p

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/style.css')
def style_css():
    return send_file('style.css')

@app.route('/script.js')
def script_js():
    return send_file('script.js')

@app.route('/index.html')
def index_html():
    return send_file('index.html')

@app.get('/api/config')
def config():
    return jsonify({'categorias': CATEGORIAS, 'formas_pagamento': FORMAS_PAGAMENTO, 'sabores': list(PRECO_VENDA.keys()), 'precos': PRECO_VENDA})

@app.get('/api/produtos')
def produtos():
    c = db()
    try:
        rows = c.execute('SELECT * FROM produtos ORDER BY atualizado_em DESC, id DESC').fetchall()
        return jsonify([produto_completo(row, c) for row in rows])
    finally:
        c.close()

@app.get('/api/receitas')
def receitas():
    resultado = {}
    for sabor, ingredientes in RECEITAS.items():
        custo = calcular_custo_producao(sabor)
        resultado[sabor] = {'ingredientes': ingredientes, 'custo': custo, 'preco_venda': PRECO_VENDA.get(sabor, 0), 'lucro': round(PRECO_VENDA.get(sabor, 0) - custo, 2)}
    return jsonify(resultado)

@app.get('/api/resumo')
def resumo():
    return jsonify({
        'produtos_cadastrados': 0,
        'itens_estoque': 0,
        'estoque_baixo': 0,
        'esgotados': 0,
        'itens_vendidos': 0,
        'alertas': [],
        'faturamento_dia': 0,
        'lucro_dia': 0,
        'custo_dia': 0,
        'despesas_dia': 0,
        'saldo_caixa': 0,
        'status_dia': 'não aberto',
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
