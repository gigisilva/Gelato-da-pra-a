const API = "/api";

let produtos = [];
let receitas = [];

const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

const money = v => Number(v || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
});

const num = v => Number(v || 0).toLocaleString("pt-BR", {
    maximumFractionDigits: 2
});

const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
}[c]));

const dateTime = v => {
    if (!v) return "--";
    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? v : d.toLocaleString("pt-BR");
};

async function api(url, options = {}) {
    const res = await fetch(API + url, options);
    let data = {};
    try {
        data = await res.json();
    } catch {}
    if (!res.ok) throw new Error(data.erro || data.error || "Erro na operação.");
    return data;
}

function toast(message, type = "") {
    let el = $("#toast");
    if (!el) {
        el = document.createElement("div");
        el.id = "toast";
        el.className = "toast";
        document.body.appendChild(el);
    }
    el.textContent = message;
    el.className = `toast show ${type}`;
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => el.classList.remove("show"), 3000);
}

function openModal(id) {
    const modal = $(`#${id}`);
    if (!modal) return;
    modal.classList.add("show");
    modal.querySelector("input:not([type='hidden']),select,textarea")?.focus();
}

function closeModal(id) {
    $(`#${id}`)?.classList.remove("show");
}

function closeAllModals() {
    $$(".backdrop").forEach(el => el.classList.remove("show"));
}

function mostrarPagina(id) {
    const dashboard = $("#dashboard");

    if (dashboard) dashboard.style.display = id === "dashboard" ? "block" : "none";

    $$(".secondary").forEach(el => {
        el.style.display = el.id === id ? "block" : "none";
    });

    $$(".nav").forEach(el => {
        el.classList.toggle("active", el.dataset.go === id);
    });
}

async function carregarProdutos() {
    try {
        const data = await api("/produtos");
        produtos = Array.isArray(data) ? data : data.produtos || [];
        renderizarProdutos();
        preencherProdutosMovimentacao();
        atualizarResumoProdutos();
        atualizarAlertas();
    } catch (e) {
        console.error(e);
    }
}

function renderizarProdutos() {
    const tbody = $("#tbody");
    if (!tbody) return;

    const busca = ($("#search")?.value || "").toLowerCase().trim();
    const filtro = $(".filter.active")?.dataset.filter || "Todos";

    let lista = produtos.filter(p =>
        `${p.nome || ""} ${p.categoria || ""} ${p.sabor || ""}`
            .toLowerCase()
            .includes(busca)
    );

    lista = lista.filter(p => {
        const estoque = Number(p.estoque_atual || 0);
        const minimo = Number(p.estoque_minimo || 0);

        if (filtro === "baixo") return estoque > 0 && estoque <= minimo;
        if (filtro === "esgotado") return estoque <= 0;
        if (filtro !== "Todos") return p.categoria === filtro;
        return true;
    });

    tbody.innerHTML = lista.map(p => {
        const estoque = Number(p.estoque_atual || 0);
        const minimo = Number(p.estoque_minimo || 0);
        const classe = estoque <= minimo ? "neg" : "pos";

        return `
            <tr>
                <td>${esc(p.nome)}</td>
                <td>${esc(p.categoria || "-")}</td>
                <td>${esc(p.sabor || "-")}</td>
                <td>${num(p.estoque_inicial)}</td>
                <td class="pos">${num(p.entradas)}</td>
                <td class="neg">${num(p.saidas)}</td>
                <td class="current ${classe}">${num(estoque)}</td>
                <td>${num(minimo)}</td>
            </tr>
        `;
    }).join("");

    if ($("#empty")) $("#empty").style.display = lista.length ? "none" : "block";
}

function preencherProdutosMovimentacao() {
    const select = $("#moveProduct");
    if (!select) return;

    select.innerHTML = `<option value="">Selecione o produto</option>` +
        produtos.map(p => `<option value="${p.id}">${esc(p.nome)}</option>`).join("");
}

function atualizarResumoProdutos() {
    if ($("#productSummary")) {
        $("#productSummary").innerHTML = `
            <div class="moveRow">
                <span>Produtos cadastrados</span>
                <b>${num(produtos.length)}</b>
            </div>
        `;
    }
}

function atualizarAlertas() {
    const baixos = produtos.filter(p =>
        Number(p.estoque_atual || 0) <= Number(p.estoque_minimo || 0)
    );

    if ($("#alerts")) {
        $("#alerts").textContent =
            `${baixos.length} ${baixos.length === 1 ? "alerta" : "alertas"}`;
    }

    const list = $("#alertList");
    if (!list) return;

    list.innerHTML = baixos.length
        ? baixos.map(p => `
            <div class="alert">
                <strong>${esc(p.nome)}</strong>
                <small>Atual: <b>${num(p.estoque_atual)}</b> · Mínimo: <b>${num(p.estoque_minimo)}</b></small>
                <button type="button" data-action="movimentacao">Registrar reposição</button>
            </div>
        `).join("")
        : `
            <div class="alert emptyAlert">
                <strong>Estoque em ordem</strong>
                <small>Nenhum produto precisa de reposição.</small>
            </div>
        `;
}

async function salvarProduto(event) {
    event.preventDefault();

    try {
        const form = event.target;
        const data = new FormData(form);

        if (!String(data.get("nome") || "").trim()) {
            toast("Digite o nome do produto.", "error");
            return;
        }

        await api("/produtos", { method: "POST", body: data });
        form.reset();
        closeModal("productModal");
        toast("Produto cadastrado com sucesso!", "success");
        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function carregarMovimentacoes() {
    const container = $("#moves");
    if (!container) return;

    try {
        const data = await api("/movimentacoes");
        const lista = Array.isArray(data) ? data : data.movimentacoes || [];

        container.innerHTML = lista.length
            ? lista.map(m => {
                const entrada = String(m.tipo || "").toLowerCase() === "entrada";
                return `
                    <div class="moveRow">
                        <div>
                            <strong>${esc(m.produto_nome || m.produto || "-")}</strong>
                            <small>${dateTime(m.data)}</small>
                        </div>
                        <div class="${entrada ? "entry" : "exit"}">
                            ${entrada ? "+" : "-"}${num(m.quantidade)}
                        </div>
                    </div>
                `;
            }).join("")
            : `<div class="empty" style="display:block"><b>Nenhuma movimentação registrada.</b></div>`;
    } catch (e) {
        console.error(e);
    }
}

async function salvarMovimentacao(event) {
    event.preventDefault();

    try {
        const form = event.target;
        const data = new FormData(form);
        const produtoId = data.get("produto_id");
        const tipo = String(data.get("tipo") || "").toLowerCase();
        const quantidade = Number(data.get("quantidade") || 0);

        if (!produtoId) {
            toast("Selecione um produto.", "error");
            return;
        }

        if (!["entrada", "saída", "saida"].includes(tipo)) {
            toast("Selecione entrada ou saída.", "error");
            return;
        }

        if (quantidade <= 0) {
            toast("Digite uma quantidade válida.", "error");
            return;
        }

        if (tipo === "saída" || tipo === "saida") {
            const produto = produtos.find(p => String(p.id) === String(produtoId));

            if (produto && quantidade > Number(produto.estoque_atual || 0)) {
                toast(`Estoque insuficiente. Disponível: ${num(produto.estoque_atual)}.`, "error");
                return;
            }
        }

        await api("/movimentacoes", { method: "POST", body: data });

        form.reset();
        closeModal("moveModal");
        toast(
            tipo === "entrada"
                ? "Entrada registrada com sucesso!"
                : "Saída registrada com sucesso!",
            "success"
        );

        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function carregarResumo() {
    try {
        const data = await api("/resumo");

        if ($("#s1")) $("#s1").textContent = num(data.produtos);
        if ($("#s2")) $("#s2").textContent = num(data.estoque_total);
        if ($("#s3")) $("#s3").textContent = num(data.estoque_baixo);
        if ($("#s4")) $("#s4").textContent = num(data.esgotados);
        if ($("#s5")) $("#s5").textContent = num(data.itens_vendidos);

        if ($("#dailyRevenue")) $("#dailyRevenue").textContent = money(data.receita);
        if ($("#dailyCost")) $("#dailyCost").textContent = money(data.custo);
        if ($("#dailyProfit")) $("#dailyProfit").textContent = money(data.lucro);
        if ($("#dailyCash")) $("#dailyCash").textContent = money(data.saldo_esperado);

        if ($("#updated")) {
            $("#updated").textContent = new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit"
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function carregarReceitas() {
    try {
        const data = await api("/receitas");
        receitas = Array.isArray(data) ? data : data.receitas || [];

        const options = receitas.map(r => {
            const sabor = r.sabor || r.nome || r.flavor;
            return `<option value="${esc(sabor)}">${esc(sabor)}</option>`;
        }).join("");

        if ($("#productionFlavor")) {
            $("#productionFlavor").innerHTML =
                `<option value="">Selecione o sabor</option>${options}`;
        }

        if ($("#saleFlavor")) {
            $("#saleFlavor").innerHTML =
                `<option value="">Selecione o sabor</option>${options}`;
        }

        if ($("#recipeList")) {
            $("#recipeList").innerHTML = receitas.map(r => {
                const sabor = r.sabor || r.nome || r.flavor;
                return `
                    <div class="moveRow">
                        <span>${esc(sabor)}</span>
                        <b>${money(r.custo || 0)}</b>
                    </div>
                `;
            }).join("");
        }
    } catch (e) {
        console.error(e);
    }
}

async function salvarProducao(event) {
    event.preventDefault();

    try {
        await api("/producao", {
            method: "POST",
            body: new FormData(event.target)
        });

        event.target.reset();
        closeModal("productionModal");
        toast("Produção registrada com sucesso!", "success");
        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function carregarVendas() {
    const container = $("#salesList");
    if (!container) return;

    try {
        const data = await api("/vendas");
        const lista = Array.isArray(data) ? data : data.vendas || [];

        container.innerHTML = lista.length
            ? lista.map(v => `
                <div class="moveRow">
                    <div>
                        <strong>${esc(v.sabor || v.produto || "-")}</strong>
                        <small>${num(v.quantidade)} unidade(s) · ${dateTime(v.data)}</small>
                    </div>
                    <b class="pos">${money(v.total || v.valor)}</b>
                </div>
            `).join("")
            : `<div class="empty" style="display:block"><b>Nenhuma venda registrada.</b></div>`;
    } catch (e) {
        console.error(e);
    }
}

async function salvarVenda(event) {
    event.preventDefault();

    try {
        await api("/vendas", {
            method: "POST",
            body: new FormData(event.target)
        });

        event.target.reset();
        closeModal("saleModal");
        toast("Venda registrada com sucesso!", "success");
        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function carregarCaixa() {
    const container = $("#cashList");
    if (!container) return;

    try {
        const data = await api("/caixa");
        const lista = Array.isArray(data) ? data : data.movimentacoes || [];

        container.innerHTML = lista.length
            ? lista.map(c => {
                const entrada = String(c.tipo || "").toLowerCase() === "entrada";
                return `
                    <div class="moveRow">
                        <div>
                            <strong>${esc(c.descricao || "Movimentação")}</strong>
                            <small>${dateTime(c.data)}</small>
                        </div>
                        <b class="${entrada ? "entry" : "exit"}">
                            ${entrada ? "+" : "-"}${money(c.valor)}
                        </b>
                    </div>
                `;
            }).join("")
            : `<div class="empty" style="display:block"><b>Nenhuma movimentação de caixa.</b></div>`;
    } catch (e) {
        console.error(e);
    }
}

async function salvarCaixa(event) {
    event.preventDefault();

    try {
        await api("/caixa", {
            method: "POST",
            body: new FormData(event.target)
        });

        event.target.reset();
        closeModal("cashModal");
        toast("Movimentação de caixa registrada!", "success");
        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function carregarDia() {
    try {
        const data = await api("/dia");

        if ($("#dayStatus")) {
            $("#dayStatus").textContent =
                data.status === "aberto" ? "Dia aberto" : "Dia fechado";
            $("#dayStatus").className =
                data.status === "aberto" ? "dayStatus open" : "dayStatus";
        }
    } catch (e) {
        console.error(e);
    }
}

async function abrirDia(event) {
    event.preventDefault();

    try {
        await api("/dia/abrir", {
            method: "POST",
            body: new FormData(event.target)
        });

        event.target.reset();
        closeModal("openDayModal");
        toast("Dia aberto com sucesso!", "success");
        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function prepararFechamento() {
    try {
        const data = await api("/resumo");
        const esperado = Number(data.saldo_esperado || 0);

        if ($("#closeExpected")) {
            $("#closeExpected").textContent = money(esperado);
            $("#closeExpected").dataset.value = esperado;
        }

        atualizarDiferenca();
    } catch (e) {
        toast(e.message, "error");
    }
}

function atualizarDiferenca() {
    const contado = Number($("#closeCounted")?.value || 0);
    const esperado = Number($("#closeExpected")?.dataset.value || 0);
    const diferenca = contado - esperado;

    if ($("#differencePreview")) {
        $("#differencePreview").textContent = money(diferenca);
        $("#differencePreview").className = diferenca >= 0 ? "pos" : "neg";
    }
}

async function fecharDia(event) {
    event.preventDefault();

    try {
        await api("/dia/fechar", {
            method: "POST",
            body: new FormData(event.target)
        });

        event.target.reset();
        closeModal("closeDayModal");
        toast("Dia encerrado com sucesso!", "success");
        await atualizarTudo();
    } catch (e) {
        toast(e.message, "error");
    }
}

async function carregarFechamentos() {
    const container = $("#closingHistory");
    if (!container) return;

    try {
        const data = await api("/fechamentos");
        const lista = Array.isArray(data) ? data : data.fechamentos || [];

        container.innerHTML = lista.length
            ? lista.map(f => `
                <div class="moveRow">
                    <div>
                        <strong>${esc(f.data)}</strong>
                        <small>Saldo contado: ${money(f.saldo_contado)}</small>
                    </div>
                    <b class="${Number(f.lucro || 0) >= 0 ? "pos" : "neg"}">
                        ${money(f.lucro)}
                    </b>
                </div>
            `).join("")
            : `<div class="empty" style="display:block"><b>Nenhum fechamento registrado.</b></div>`;
    } catch (e) {
        console.error(e);
    }
}

document.addEventListener("click", async event => {
    if (event.target.closest(".backdrop") &&
        event.target === event.target.closest(".backdrop")) {
        closeAllModals();
        return;
    }

    const close = event.target.closest("[data-close]");
    if (close) {
        closeModal(close.dataset.close);
        return;
    }

    const nav = event.target.closest("[data-go]");
    if (nav) {
        mostrarPagina(nav.dataset.go);
        return;
    }

    const filter = event.target.closest(".filter");
    if (filter) {
        $$(".filter").forEach(b => b.classList.remove("active"));
        filter.classList.add("active");
        renderizarProdutos();
        return;
    }

    const action = event.target.closest("[data-action]")?.dataset.action;

    if (action === "produto") {
        openModal("productModal");
    } else if (action === "movimentacao") {
        await carregarProdutos();
        openModal("moveModal");
    } else if (action === "producao") {
        await carregarReceitas();
        openModal("productionModal");
    } else if (action === "venda") {
        await carregarReceitas();
        openModal("saleModal");
    } else if (action === "caixa") {
        openModal("cashModal");
    } else if (action === "abrir-dia") {
        openModal("openDayModal");
    } else if (action === "fechar-dia") {
        await prepararFechamento();
        openModal("closeDayModal");
    }

    if (event.target.closest("#addTop,#addProducts,#emptyAdd")) {
        openModal("productModal");
    }

    if (event.target.closest("#addMove")) {
        await carregarProdutos();
        openModal("moveModal");
    }

    if (event.target.closest("#addProduction")) {
        await carregarReceitas();
        openModal("productionModal");
    }

    if (event.target.closest("#addSale")) {
        await carregarReceitas();
        openModal("saleModal");
    }

    if (event.target.closest("#addCash")) {
        openModal("cashModal");
    }

    if (event.target.closest("#openDay")) {
        openModal("openDayModal");
    }

    if (event.target.closest("#closeDay")) {
        await prepararFechamento();
        openModal("closeDayModal");
    }
});

document.addEventListener("input", event => {
    if (event.target.id === "search") renderizarProdutos();
    if (event.target.id === "closeCounted") atualizarDiferenca();
});

document.addEventListener("submit", event => {
    const forms = {
        productForm: salvarProduto,
        moveForm: salvarMovimentacao,
        productionForm: salvarProducao,
        saleForm: salvarVenda,
        cashForm: salvarCaixa,
        openDayForm: abrirDia,
        closeDayForm: fecharDia
    };

    const fn = forms[event.target.id];
    if (fn) fn(event);
});

document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeAllModals();
});

async function atualizarTudo() {
    await carregarProdutos();
    await carregarResumo();
    await carregarDia();
    await carregarMovimentacoes();
    await carregarReceitas();
    await carregarVendas();
    await carregarCaixa();
    await carregarFechamentos();
}

document.addEventListener("DOMContentLoaded", async () => {
    mostrarPagina("dashboard");

    if ($("#openDayDate") && !$("#openDayDate").value) {
        $("#openDayDate").value = new Date().toISOString().slice(0, 10);
    }

    await atualizarTudo();
});