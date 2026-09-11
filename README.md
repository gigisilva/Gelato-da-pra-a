# Controle de Estoque — Python + Live Server

Este projeto implementa o fluxograma da imagem usando:

- **HTML/CSS/JavaScript** para a interface;
- **Live Server do VS Code** para abrir o frontend;
- **Python + Flask** como servidor/API local;
- **estoque.json** para guardar os produtos mesmo depois de fechar o programa.

## 1. Estrutura

```text
controle_estoque_live_server/
├── app.py
├── estoque.json
├── requirements.txt
├── index.html
├── style.css
├── script.js
└── README.md
```

## 2. Instalar o Flask

Abra o terminal do VS Code dentro desta pasta:

```bash
python -m pip install -r requirements.txt
```

Se `python` não funcionar no Windows, tente:

```bash
py -m pip install -r requirements.txt
```

## 3. Iniciar o servidor Python

No terminal:

```bash
python app.py
```

ou:

```bash
py app.py
```

A API ficará em:

```text
http://127.0.0.1:5000
```

**Não abra `index.html` diretamente pelo navegador.**

## 4. Abrir pelo Live Server

No VS Code:

1. Instale a extensão **Live Server**.
2. Abra a pasta deste projeto.
3. Clique com o botão direito em `index.html`.
4. Selecione **Open with Live Server**.
5. O navegador normalmente abrirá algo como:

```text
http://127.0.0.1:5500/index.html
```

O frontend usa o Live Server na porta 5500 e conversa com o Python na porta 5000.

## 5. Como o programa segue o fluxograma

### Entrada (E)

1. Digite o código.
2. Digite a descrição.
3. Digite a quantidade.
4. Clique em **Entrada**.
5. Se o produto já existir, a quantidade é somada.
6. Se não existir, o produto é criado.

Exemplo:

```text
P001
Motor DC
10
Entrada
```

Depois:

```text
P001
Motor DC
5
Entrada
```

Resultado:

```text
P001 → 15 unidades
```

### Saída (S)

1. Digite o código.
2. Digite a quantidade.
3. Clique em **Saída**.
4. O Python verifica se existe estoque suficiente.
5. Se houver, subtrai a quantidade.
6. Se não houver, o sistema mostra **"Está em falta"** e não altera o estoque.

Exemplo:

```text
Estoque: 10
Saída: 4
Resultado: 6
```

Se tentar:

```text
Estoque: 6
Saída: 10
```

O sistema responde:

```text
Está em falta.
Estoque disponível: 6 unidade(s).
```

## 6. Onde os dados ficam?

Os produtos são armazenados no arquivo:

```text
estoque.json
```

Assim, se você fechar o navegador e abrir novamente, os produtos continuam cadastrados.

## 7. Observação importante

O **Live Server não executa Python**. Ele serve os arquivos HTML/CSS/JS.

Por isso o projeto possui dois servidores:

```text
Navegador
   │
   ▼
Live Server :5500
   │
   │ HTTP / API
   ▼
Flask Python :5000
   │
   ▼
estoque.json
```

Isso permite usar exatamente o Live Server no VS Code, enquanto o Python fica responsável pela lógica do estoque.
