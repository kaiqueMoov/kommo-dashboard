let selectedSellerIds = new Set();
let selectedCampaignNames = new Set();
let selectedCarNames = new Set();

const CURRENT_YEAR_START = "2026-01-01";
const DEFAULT_VISIBLE_ROWS = 5;

let dashboardMetadata = {
  pipelines: {},
  statuses: {},
};

let expandedTables = {
  campaigns: false,
  cars: false,
  sellers: false,
  leads: false,
};

let currentCampaignsData = [];
let currentCarsData = [];
let currentSellersData = [];
let currentLeadsData = [];

const FUNNEL_RULES = {
  CPA: {
    aliases: ["cpa", "trafego pago", "lead novo trafego pago"],
    stages: [
      "Etapa de leads de entrada",
      "Solicitações",
      "Lead Novo Tráfego Pago",
      "Liguei",
      "Mensagem Enviada",
      "Respondeu a Primeira Mensagem",
      "SQL",
      "Orçamento Enviado",
      "Em Negociação",
      "Aguardando Documentos",
      "Subir Ficha",
      "Em Análise",
      "Aprovado Para Contratação",
      "Venda ganha",
    ],
  },
  FS: {
    aliases: ["fs", "seguro auto", "funil seguros"],
    stages: [
      "Etapa de leads de entrada",
      "Novo Lead",
      "Mensagem Enviada",
      "Respondeu a Primeira Mensagem",
      "Cálculo Enviado",
      "Cálculo Respondido",
      "Proposta Gerada",
      "Aguardando Vistoria",
      "Em Processo de Emissão",
      "Indicação Vida",
      "Venda ganha",
    ],
  },
  SEGURO_SAUDE: {
    aliases: ["funil seguro saude", "seguro saude", "saude", "saúde"],
    stages: [
      "Etapa de leads de entrada",
      "Novo Lead Cadastrado",
      "Renovações",
      "Responderam Sim",
      "Sair da Lista",
      "Outras Respostas do Disparo",
      "Mensagem Enviada",
      "Respondeu com Dados",
      "Cotação Enviada",
      "Respondeu Cotação",
      "Aguardando Documentação",
      "Análise Operadora",
      "Aguardando Pagamento",
      "Renovação Concluída",
      "Venda ganha",
    ],
  },
  SEGURO_VIDA: {
    aliases: ["funil seguro de vida", "seguro de vida", "vida"],
    stages: [
      "Etapa de leads de entrada",
      "Prospecção",
      "Mensagem Enviada",
      "Respondeu a Primeira Mensagem",
      "Cálculo Enviado",
      "Em Andamento",
      "Proposta Gerada",
      "Em Análise Seguradora",
      "Proposta Recusada",
      "Venda ganha",
    ],
  },
};

function getSelectedSellerIds() {
  return Array.from(selectedSellerIds);
}

function getSelectedCampaignNames() {
  return Array.from(selectedCampaignNames);
}

function getSelectedCarNames() {
  return Array.from(selectedCarNames);
}

function getSearchValue() {
  const input = document.getElementById("searchInput");
  return input ? input.value.trim() : "";
}

function getFinalizedFilterValue() {
  const select = document.getElementById("finalizedFilter");
  return select ? select.value : "";
}

function setDefaultDates() {
  const startInput = document.getElementById("start");
  const endInput = document.getElementById("end");

  if (!startInput || !endInput) return;

  const now = new Date();
  const today = now.toISOString().slice(0, 10);

  if (!startInput.value) {
    startInput.value = CURRENT_YEAR_START;
  }

  if (!endInput.value) {
    endInput.value = today;
  }
}

function updateSelectionInfo(elementId, selectedCount, singular, plural, emptyText) {
  const info = document.getElementById(elementId);
  if (!info) return;

  if (selectedCount === 0) {
    info.textContent = emptyText;
    return;
  }

  if (selectedCount === 1) {
    info.textContent = `1 ${singular} selecionado`;
    return;
  }

  info.textContent = `${selectedCount} ${plural} selecionados`;
}

function toggleSelection(setRef, value) {
  const normalizedValue = String(value);

  if (setRef.has(normalizedValue)) {
    setRef.delete(normalizedValue);
  } else {
    setRef.add(normalizedValue);
  }
}

function toggleSellerSelection(sellerId) {
  toggleSelection(selectedSellerIds, sellerId);
  updateSellerListUI();
  updateAllSelectionInfos();
}

function toggleCampaignSelection(campaignName) {
  toggleSelection(selectedCampaignNames, campaignName);
  updateCampaignListUI();
  updateAllSelectionInfos();
}

function toggleCarSelection(carName) {
  toggleSelection(selectedCarNames, carName);
  updateCarListUI();
  updateAllSelectionInfos();
}

function updateAllSelectionInfos() {
  updateSelectionInfo(
    "sellerSelectionInfo",
    getSelectedSellerIds().length,
    "vendedor",
    "vendedores",
    "Nenhum vendedor selecionado"
  );

  updateSelectionInfo(
    "campaignSelectionInfo",
    getSelectedCampaignNames().length,
    "campanha",
    "campanhas",
    "Nenhuma campanha selecionada"
  );

  updateSelectionInfo(
    "carSelectionInfo",
    getSelectedCarNames().length,
    "carro",
    "carros",
    "Nenhum carro selecionado"
  );
}

function updateOptionUI(selectorClass, setRef) {
  document.querySelectorAll(selectorClass).forEach((item) => {
    const optionValue = item.dataset.optionValue;
    const isSelected = setRef.has(String(optionValue));

    item.classList.toggle("is-selected", isSelected);

    const dot = item.querySelector(".seller-dot");
    if (dot) {
      dot.classList.toggle("is-selected", isSelected);
    }
  });
}

function updateSellerListUI() {
  updateOptionUI(".seller-option", selectedSellerIds);
}

function updateCampaignListUI() {
  updateOptionUI(".campaign-option", selectedCampaignNames);
}

function updateCarListUI() {
  updateOptionUI(".car-option", selectedCarNames);
}

function buildQuery() {
  const startInput = document.getElementById("start");
  const endInput = document.getElementById("end");

  const start = startInput ? startInput.value : "";
  const end = endInput ? endInput.value : "";

  const sellerIds = getSelectedSellerIds();
  const campaignNames = getSelectedCampaignNames();
  const carNames = getSelectedCarNames();
  const search = getSearchValue();
  const finalizedFilter = getFinalizedFilterValue();

  const params = new URLSearchParams();

  if (start) {
    params.append("start", start);
  }

  if (end) {
    const endDate = new Date(end);
    endDate.setDate(endDate.getDate() + 1);
    params.append("end", endDate.toISOString().slice(0, 10));
  }

  if (search) {
    params.append("search", search);
  }

  if (finalizedFilter) {
    params.append("lead_finalizado", finalizedFilter);
  }

  sellerIds.forEach((sellerId) => {
    params.append("seller_ids", sellerId);
  });

  campaignNames.forEach((campaignName) => {
    params.append("campaign_names", campaignName);
  });

  carNames.forEach((carName) => {
    params.append("car_names", carName);
  });

  const query = params.toString();
  return query ? `?${query}` : "";
}

function buildCurrentYearQuery() {
  const params = new URLSearchParams();
  params.append("start", CURRENT_YEAR_START);

  const search = getSearchValue();
  const sellerIds = getSelectedSellerIds();
  const finalizedFilter = getFinalizedFilterValue();

  if (search) {
    params.append("search", search);
  }

  if (finalizedFilter) {
    params.append("lead_finalizado", finalizedFilter);
  }

  sellerIds.forEach((sellerId) => {
    params.append("seller_ids", sellerId);
  });

  return `?${params.toString()}`;
}

async function fetchJson(url) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Erro ao carregar ${url}`);
  }

  return response.json();
}

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function normalizeStatusName(value) {
  return normalizeText(value);
}

function getPipelineName(pipelineId) {
  if (!pipelineId) return "Sem pipeline";
  return dashboardMetadata.pipelines[String(pipelineId)] || `Pipeline ${pipelineId}`;
}

function getStatusName(pipelineId, statusId) {
  if (!statusId) return "Sem status";
  const compositeKey = `${pipelineId}:${statusId}`;
  return dashboardMetadata.statuses[compositeKey] || `Status ${statusId}`;
}

function detectFunnelTypeFromPipeline(pipelineName) {
  const normalizedPipeline = normalizeText(pipelineName);

  for (const [funnelKey, config] of Object.entries(FUNNEL_RULES)) {
    for (const alias of config.aliases) {
      if (normalizedPipeline.includes(normalizeText(alias))) {
        return funnelKey;
      }
    }
  }

  return "OUTROS";
}

function getStageOrderFromFunnel(funnelType, statusName) {
  const config = FUNNEL_RULES[funnelType];
  if (!config) return 999;

  const normalizedStatus = normalizeText(statusName);

  for (let i = 0; i < config.stages.length; i += 1) {
    if (normalizeText(config.stages[i]) === normalizedStatus) {
      return i + 1;
    }
  }

  return 999;
}

function getFunnelDisplayName(funnelType) {
  switch (funnelType) {
    case "CPA":
      return "CPA";
    case "FS":
      return "FS";
    case "SEGURO_SAUDE":
      return "Seguro Saúde";
    case "SEGURO_VIDA":
      return "Seguro de Vida";
    default:
      return "Outros";
  }
}

function getFunnelBadgeClass(funnelType) {
  switch (funnelType) {
    case "CPA":
      return "table-badge table-badge--funnel table-badge--funnel-cpa";
    case "FS":
      return "table-badge table-badge--funnel table-badge--funnel-fs";
    case "SEGURO_SAUDE":
      return "table-badge table-badge--funnel table-badge--funnel-saude";
    case "SEGURO_VIDA":
      return "table-badge table-badge--funnel table-badge--funnel-vida";
    default:
      return "table-badge table-badge--funnel table-badge--funnel-default";
  }
}

function getStatusBadgeClass(statusName) {
  const normalized = normalizeStatusName(statusName);

  if (
    normalized.includes("ganho") ||
    normalized.includes("fechado ganho") ||
    normalized.includes("closed won")
  ) {
    return "table-badge table-badge--status table-badge--won";
  }

  if (
    normalized.includes("perdido") ||
    normalized.includes("fechado perdido") ||
    normalized.includes("lost") ||
    normalized.includes("desqualificado") ||
    normalized.includes("recusada")
  ) {
    return "table-badge table-badge--status table-badge--lost";
  }

  if (
    normalized.includes("sql") ||
    normalized.includes("qualificado") ||
    normalized.includes("qualificacao")
  ) {
    return "table-badge table-badge--status table-badge--sql";
  }

  if (
    normalized.includes("novo") ||
    normalized.includes("lead") ||
    normalized.includes("inicial") ||
    normalized.includes("primeiro contato") ||
    normalized.includes("prospeccao")
  ) {
    return "table-badge table-badge--status table-badge--new";
  }

  return "table-badge table-badge--status table-badge--default";
}

function getFinalizedBadge(isFinalized) {
  return isFinalized
    ? `<span class="table-badge table-badge--finalized-yes">Finalizado</span>`
    : `<span class="table-badge table-badge--finalized-no">Aberto</span>`;
}

function getVisibleRows(rows, tableKey) {
  return expandedTables[tableKey] ? rows : rows.slice(0, DEFAULT_VISIBLE_ROWS);
}

function updateToggleButton(buttonId, rows, tableKey) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;

  if (!rows || rows.length <= DEFAULT_VISIBLE_ROWS) {
    btn.style.display = "none";
    return;
  }

  btn.style.display = "inline-flex";
  btn.textContent = expandedTables[tableKey] ? "Ver menos" : "Ver mais";
}

function renderSummary(data) {
  const cardTotal = document.getElementById("cardTotal");
  const cardReplied = document.getElementById("cardReplied");
  const cardSql = document.getElementById("cardSql");
  const cardWon = document.getElementById("cardWon");
  const cardLost = document.getElementById("cardLost");

  if (cardTotal) cardTotal.textContent = data.total_leads ?? 0;
  if (cardReplied) cardReplied.textContent = data.replied_first_message ?? 0;
  if (cardSql) cardSql.textContent = data.sql_count ?? 0;
  if (cardWon) cardWon.textContent = data.won_count ?? 0;
  if (cardLost) cardLost.textContent = data.lost_count ?? 0;
}

function renderSellerHighlights(rows) {
  const container = document.getElementById("sellerHighlights");
  if (!container) return;

  container.innerHTML = "";

  const topThree = [...rows]
    .sort((a, b) => {
      if ((b.won_count ?? 0) !== (a.won_count ?? 0)) {
        return (b.won_count ?? 0) - (a.won_count ?? 0);
      }
      return (b.won_rate ?? 0) - (a.won_rate ?? 0);
    })
    .slice(0, 3);

  topThree.forEach((row, index) => {
    const div = document.createElement("div");
    div.className = "seller-highlight-card";

    const medal = index === 0 ? "🥇" : index === 1 ? "🥈" : "🥉";

    div.innerHTML = `
      <div class="seller-highlight-top">
        <span class="seller-medal">${medal}</span>
        <span class="seller-rank-label">Top ${index + 1}</span>
      </div>
      <strong>${row.seller_name ?? "Sem responsável"}</strong>
      <div class="seller-highlight-metrics">
        <span><b>${row.total_leads ?? 0}</b> leads</span>
        <span><b>${row.sql_count ?? 0}</b> SQL</span>
        <span><b>${row.won_count ?? 0}</b> ganhos</span>
        <span><b>${row.won_rate ?? 0}%</b> conversão</span>
      </div>
    `;

    container.appendChild(div);
  });
}

function renderCarHighlights(rows) {
  const container = document.getElementById("carHighlights");
  if (!container) return;

  container.innerHTML = "";

  const topThree = [...rows]
    .sort((a, b) => {
      if ((b.total_leads ?? 0) !== (a.total_leads ?? 0)) {
        return (b.total_leads ?? 0) - (a.total_leads ?? 0);
      }
      return (b.won_rate ?? 0) - (a.won_rate ?? 0);
    })
    .slice(0, 3);

  topThree.forEach((row, index) => {
    const div = document.createElement("div");
    div.className = "car-highlight-card";

    const badge =
      index === 0 ? "🚘 Destaque" :
      index === 1 ? "🚗 Alta procura" :
      "📈 Potencial";

    div.innerHTML = `
      <div class="car-highlight-top">
        <span class="car-rank-label">${badge}</span>
      </div>
      <strong>${row.car_name ?? "Sem carro"}</strong>
      <div class="car-highlight-metrics">
        <span><b>${row.total_leads ?? 0}</b> leads</span>
        <span><b>${row.sql_count ?? 0}</b> SQL</span>
        <span><b>${row.won_count ?? 0}</b> ganhos</span>
        <span><b>${row.won_rate ?? 0}%</b> conversão</span>
      </div>
    `;

    container.appendChild(div);
  });
}

function renderSellers(rows) {
  const tbody = document.getElementById("sellersTable");
  if (!tbody) return;

  tbody.innerHTML = "";
  currentSellersData = rows || [];

  const visibleRows = getVisibleRows(currentSellersData, "sellers");

  visibleRows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.seller_name ?? "Sem responsável"}</td>
      <td>${row.total_leads ?? 0}</td>
      <td>${row.replied_first_message ?? 0}</td>
      <td>${row.reply_rate ?? 0}%</td>
      <td>${row.sql_count ?? 0}</td>
      <td>${row.sql_rate ?? 0}%</td>
      <td>${row.won_count ?? 0}</td>
      <td>${row.won_rate ?? 0}%</td>
      <td>${row.lost_count ?? 0}</td>
    `;
    tbody.appendChild(tr);
  });

  renderSellerHighlights(currentSellersData);
  updateToggleButton("toggleSellersTable", currentSellersData, "sellers");
}

function renderSources(rows) {
  const tbody = document.getElementById("sourcesTable");
  if (!tbody) return;

  tbody.innerHTML = "";

  (rows || []).forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.lead_source ?? "Sem origem"}</td>
      <td>${row.total_leads ?? 0}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderCampaigns(rows) {
  const tbody = document.getElementById("campaignsTable");
  if (!tbody) return;

  tbody.innerHTML = "";
  currentCampaignsData = rows || [];

  const visibleRows = getVisibleRows(currentCampaignsData, "campaigns");

  visibleRows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.campaign_name ?? "Sem campanha"}</td>
      <td>${row.total_leads ?? 0}</td>
      <td>${row.replied_first_message ?? 0}</td>
      <td>${row.sql_count ?? 0}</td>
      <td>${row.won_count ?? 0}</td>
      <td>${row.lost_count ?? 0}</td>
      <td>${row.reply_rate ?? 0}%</td>
      <td>${row.sql_rate ?? 0}%</td>
      <td>${row.won_rate ?? 0}%</td>
    `;
    tbody.appendChild(tr);
  });

  updateToggleButton("toggleCampaignsTable", currentCampaignsData, "campaigns");
}

function renderCars(rows) {
  const tbody = document.getElementById("carsTable");
  if (!tbody) return;

  tbody.innerHTML = "";
  currentCarsData = rows || [];

  const visibleRows = getVisibleRows(currentCarsData, "cars");

  visibleRows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.car_name ?? "Sem carro"}</td>
      <td>${row.total_leads ?? 0}</td>
      <td>${row.sql_count ?? 0}</td>
      <td>${row.sql_rate ?? 0}%</td>
      <td>${row.won_count ?? 0}</td>
      <td>${row.won_rate ?? 0}%</td>
      <td>${row.lost_count ?? 0}</td>
    `;
    tbody.appendChild(tr);
  });

  renderCarHighlights(currentCarsData);
  updateToggleButton("toggleCarsTable", currentCarsData, "cars");
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("pt-BR");
}

function openLeadDrawer() {
  const drawer = document.getElementById("leadDrawer");
  const overlay = document.getElementById("leadDrawerOverlay");

  if (drawer) drawer.classList.add("is-open");
  if (overlay) overlay.classList.add("is-open");
}

function closeLeadDrawer() {
  const drawer = document.getElementById("leadDrawer");
  const overlay = document.getElementById("leadDrawerOverlay");

  if (drawer) drawer.classList.remove("is-open");
  if (overlay) overlay.classList.remove("is-open");
}

function renderLeadDetail(detail) {
  const title = document.getElementById("leadDrawerTitle");
  const subtitle = document.getElementById("leadDrawerSubtitle");
  const grid = document.getElementById("leadDetailGrid");
  const timeline = document.getElementById("leadTimeline");

  if (title) title.textContent = detail.lead_name || "Detalhes do lead";
  if (subtitle) subtitle.textContent = `${detail.seller_name || "Sem responsável"} • ${detail.status_name || "Sem status"}`;

  if (grid) {
    const finalizedBlock =
      detail.is_finalized !== undefined
        ? `<div class="lead-detail-card"><span>Finalização</span><strong>${detail.is_finalized ? "Finalizado" : "Aberto"}</strong></div>`
        : "";

    grid.innerHTML = `
      <div class="lead-detail-card"><span>Funil</span><strong>${getFunnelDisplayName(detail.funnel_type)}</strong></div>
      <div class="lead-detail-card"><span>Pipeline</span><strong>${detail.pipeline_name || "-"}</strong></div>
      <div class="lead-detail-card"><span>Status atual</span><strong>${detail.status_name || "-"}</strong></div>
      <div class="lead-detail-card"><span>Campanha</span><strong>${detail.campaign_name || "-"}</strong></div>
      <div class="lead-detail-card"><span>Carro</span><strong>${detail.car_name || "-"}</strong></div>
      <div class="lead-detail-card"><span>Origem</span><strong>${detail.lead_source || "-"}</strong></div>
      ${finalizedBlock}
    `;
  }

  if (timeline) {
    const items = detail.timeline || [];

    timeline.innerHTML = items.length
      ? items
          .map(
            (item) => `
              <div class="lead-timeline-item">
                <div class="lead-timeline-dot lead-timeline-dot--${item.type}"></div>
                <div class="lead-timeline-content">
                  <strong>${item.label}</strong>
                  <span>${formatDateTime(item.date)}</span>
                </div>
              </div>
            `
          )
          .join("")
      : `<div class="lead-timeline-empty">Sem histórico disponível.</div>`;
  }
}

async function openLeadDetail(leadId) {
  try {
    const detail = await fetchJson(`/dashboard/lead/${leadId}`);
    renderLeadDetail(detail);
    openLeadDrawer();
  } catch (error) {
    console.error(error);
    alert("Erro ao carregar detalhe do lead.");
  }
}

function renderLeads(rows) {
  const tbody = document.getElementById("leadsTable");
  if (!tbody) return;

  tbody.innerHTML = "";
  currentLeadsData = rows || [];

  const visibleRows = getVisibleRows(currentLeadsData, "leads");

  visibleRows.forEach((row) => {
    const createdAt = row.created_at_kommo
      ? new Date(row.created_at_kommo).toLocaleString("pt-BR")
      : "-";

    const pipelineName = row.pipeline_name || getPipelineName(row.pipeline_id);
    const statusName = row.status_name || getStatusName(row.pipeline_id, row.status_id);
    const statusClass = getStatusBadgeClass(statusName);

    const funnelType = row.funnel_type || detectFunnelTypeFromPipeline(pipelineName);
    const funnelLabel = getFunnelDisplayName(funnelType);
    const funnelClass = getFunnelBadgeClass(funnelType);

    const finalizedBadge = getFinalizedBadge(row.is_finalized);

    const tr = document.createElement("tr");
    tr.className = "lead-row-clickable";
    tr.innerHTML = `
      <td>${row.lead_name ?? "-"}</td>
      <td>${row.seller_name ?? "Sem responsável"}</td>
      <td><span class="${funnelClass}">${funnelLabel}</span></td>
      <td><span class="table-badge table-badge--pipeline">${pipelineName}</span></td>
      <td><span class="${statusClass}">${statusName}</span></td>
      <td>${finalizedBadge}</td>
      <td>${row.campaign_name ?? "Sem campanha"}</td>
      <td>${row.car_name ?? "Sem carro"}</td>
      <td>${row.lead_source ?? "Sem origem"}</td>
      <td>${createdAt}</td>
    `;

    tr.addEventListener("click", () => openLeadDetail(row.id));
    tbody.appendChild(tr);
  });

  updateToggleButton("toggleLeadsTable", currentLeadsData, "leads");
}

function renderFunnelStageBoards(rows) {
  const container = document.getElementById("funnelStageBoards");
  if (!container) return;

  container.innerHTML = "";

  const grouped = {
    CPA: {},
    FS: {},
    SEGURO_SAUDE: {},
    SEGURO_VIDA: {},
  };

  (rows || []).forEach((row) => {
    const pipelineName = row.pipeline_name || getPipelineName(row.pipeline_id);
    const statusName = row.status_name || getStatusName(row.pipeline_id, row.status_id);

    const funnelType = row.funnel_type || detectFunnelTypeFromPipeline(pipelineName);
    if (!grouped[funnelType]) return;

    const stageOrder = row.stage_order || getStageOrderFromFunnel(funnelType, statusName);
    const stageKey = `${stageOrder}__${statusName}`;

    if (!grouped[funnelType][stageKey]) {
      grouped[funnelType][stageKey] = {
        stage_name: statusName,
        count: 0,
        stage_order: stageOrder,
      };
    }

    grouped[funnelType][stageKey].count += 1;
  });

  Object.keys(grouped).forEach((funnelType) => {
    const board = document.createElement("div");
    board.className = "funnel-stage-board";

    const rowsForFunnel = Object.values(grouped[funnelType]).sort(
      (a, b) => a.stage_order - b.stage_order
    );

    const itemsHtml = rowsForFunnel.length
      ? rowsForFunnel
          .map(
            (item) => `
              <div class="funnel-stage-item">
                <span class="funnel-stage-name">${item.stage_name}</span>
                <span class="funnel-stage-count">${item.count}</span>
              </div>
            `
          )
          .join("")
      : `<div class="funnel-stage-empty">Sem leads neste funil.</div>`;

    board.innerHTML = `
      <div class="funnel-stage-board-header">
        <h3>${getFunnelDisplayName(funnelType)}</h3>
      </div>
      <div class="funnel-stage-list">
        ${itemsHtml}
      </div>
    `;

    container.appendChild(board);
  });
}

function renderOptionList(containerId, rows, optionClass, valueKey, labelKey, selectedSet, clickHandler, skipValues = []) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = "";

  (rows || []).forEach((row) => {
    const rawValue = row[valueKey];
    const label = row[labelKey];

    if (!rawValue) return;
    if (skipValues.includes(label)) return;

    const option = document.createElement("button");
    option.type = "button";
    option.className = optionClass;
    option.dataset.optionValue = String(rawValue);

    option.innerHTML = `
      <span class="seller-dot"></span>
      <span class="seller-name">${label}</span>
    `;

    option.addEventListener("click", () => clickHandler(rawValue));
    container.appendChild(option);
  });

  updateOptionUI(`.${optionClass}`, selectedSet);
}

async function loadSellerOptions() {
  const query = buildCurrentYearQuery();
  const sellers = await fetchJson(`/dashboard/sellers${query}`);
  renderOptionList(
    "sellerList",
    sellers,
    "seller-option",
    "seller_id",
    "seller_name",
    selectedSellerIds,
    toggleSellerSelection
  );
}

async function loadCampaignOptions() {
  const query = buildCurrentYearQuery();
  const campaigns = await fetchJson(`/dashboard/campaigns${query}`);
  renderOptionList(
    "campaignList",
    campaigns,
    "campaign-option",
    "campaign_name",
    "campaign_name",
    selectedCampaignNames,
    toggleCampaignSelection,
    ["Sem campanha"]
  );
}

async function loadCarOptions() {
  const query = buildCurrentYearQuery();
  const cars = await fetchJson(`/dashboard/cars${query}`);
  renderOptionList(
    "carList",
    cars,
    "car-option",
    "car_name",
    "car_name",
    selectedCarNames,
    toggleCarSelection,
    ["Sem carro"]
  );
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function getRate(part, total) {
  if (!total) return 0;
  return (part / total) * 100;
}

function pickBestPerformer(rows, labelKey) {
  const safeRows = (rows || []).filter((row) => (row.total_leads ?? 0) > 0);

  if (!safeRows.length) {
    return {
      name: "Sem dados",
      rate: 0,
      total: 0,
      won: 0,
    };
  }

  const qualifiedRows = safeRows.filter((row) => (row.total_leads ?? 0) >= 3);
  const baseRows = qualifiedRows.length ? qualifiedRows : safeRows;

  const best = [...baseRows].sort((a, b) => {
    if ((b.won_rate ?? 0) !== (a.won_rate ?? 0)) {
      return (b.won_rate ?? 0) - (a.won_rate ?? 0);
    }

    if ((b.won_count ?? 0) !== (a.won_count ?? 0)) {
      return (b.won_count ?? 0) - (a.won_count ?? 0);
    }

    return (b.total_leads ?? 0) - (a.total_leads ?? 0);
  })[0];

  return {
    name: best[labelKey] ?? "Sem nome",
    rate: best.won_rate ?? 0,
    total: best.total_leads ?? 0,
    won: best.won_count ?? 0,
  };
}

function renderConversionCards(summary, sellers, campaigns, cars) {
  const container = document.getElementById("conversionCards");
  if (!container) return;

  const totalLeads = summary?.total_leads ?? 0;
  const replied = summary?.replied_first_message ?? 0;
  const sqlCount = summary?.sql_count ?? 0;
  const wonCount = summary?.won_count ?? 0;
  const lostCount = summary?.lost_count ?? 0;

  const replyRate = getRate(replied, totalLeads);
  const sqlRate = getRate(sqlCount, totalLeads);
  const wonRate = getRate(wonCount, totalLeads);
  const lostRate = getRate(lostCount, totalLeads);

  const bestSeller = pickBestPerformer(sellers, "seller_name");
  const bestCampaign = pickBestPerformer(campaigns, "campaign_name");
  const bestCar = pickBestPerformer(cars, "car_name");

  container.innerHTML = `
    <div class="conversion-card conversion-card--metric">
      <span class="conversion-label">% Resposta</span>
      <strong>${formatPercent(replyRate)}</strong>
      <small>${replied} de ${totalLeads} leads responderam a 1ª mensagem</small>
    </div>

    <div class="conversion-card conversion-card--metric">
      <span class="conversion-label">% SQL</span>
      <strong>${formatPercent(sqlRate)}</strong>
      <small>${sqlCount} de ${totalLeads} leads chegaram em SQL</small>
    </div>

    <div class="conversion-card conversion-card--metric">
      <span class="conversion-label">% Ganho</span>
      <strong>${formatPercent(wonRate)}</strong>
      <small>${wonCount} de ${totalLeads} leads viraram venda</small>
    </div>

    <div class="conversion-card conversion-card--metric">
      <span class="conversion-label">% Perdido</span>
      <strong>${formatPercent(lostRate)}</strong>
      <small>${lostCount} de ${totalLeads} leads foram perdidos</small>
    </div>

    <div class="conversion-card conversion-card--highlight">
      <span class="conversion-label">Melhor vendedor</span>
      <strong>${bestSeller.name}</strong>
      <small>${formatPercent(bestSeller.rate)} de conversão • ${bestSeller.won} ganhos em ${bestSeller.total} leads</small>
    </div>

    <div class="conversion-card conversion-card--highlight">
      <span class="conversion-label">Melhor campanha</span>
      <strong>${bestCampaign.name}</strong>
      <small>${formatPercent(bestCampaign.rate)} de conversão • ${bestCampaign.won} ganhos em ${bestCampaign.total} leads</small>
    </div>

    <div class="conversion-card conversion-card--highlight">
      <span class="conversion-label">Carro destaque</span>
      <strong>${bestCar.name}</strong>
      <small>${formatPercent(bestCar.rate)} de conversão • ${bestCar.won} ganhos em ${bestCar.total} leads</small>
    </div>
  `;
}

async function loadDashboard() {
  const query = buildQuery();

  try {
    const [summary, sellers, sources, leads, campaigns, cars] = await Promise.all([
      fetchJson(`/dashboard/summary${query}`),
      fetchJson(`/dashboard/sellers${query}`),
      fetchJson(`/dashboard/sources${query}`),
      fetchJson(`/dashboard/leads${query}`),
      fetchJson(`/dashboard/campaigns${query}`),
      fetchJson(`/dashboard/cars${query}`),
    ]);

    try {
      const metadata = await fetchJson(`/dashboard/metadata`);
      dashboardMetadata = metadata || { pipelines: {}, statuses: {} };
    } catch (metadataError) {
      console.warn("Metadata não carregada:", metadataError);
      dashboardMetadata = { pipelines: {}, statuses: {} };
    }

    expandedTables.campaigns = false;
    expandedTables.sellers = false;
    expandedTables.cars = false;
    expandedTables.leads = false;

    renderSummary(summary);
    renderSellers(sellers);
    renderSources(sources);
    renderLeads(leads);
    renderCampaigns(campaigns);
    renderCars(cars);
    renderFunnelStageBoards(leads);
    renderConversionCards(summary, sellers, campaigns, cars);
  } catch (error) {
    console.error(error);
    alert("Erro ao carregar o dashboard.");
  }
}

async function refreshFilterLists() {
  await Promise.all([
    loadSellerOptions(),
    loadCampaignOptions(),
    loadCarOptions(),
  ]);
  updateAllSelectionInfos();
}

function bindClickIfExists(id, handler) {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener("click", handler);
  }
}

function bindInputIfExists(id, eventName, handler) {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener(eventName, handler);
  }
}

bindClickIfExists("applyFilters", async () => {
  await refreshFilterLists();
  await loadDashboard();
});

bindInputIfExists("searchInput", "keydown", async (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    await refreshFilterLists();
    await loadDashboard();
  }
});

bindInputIfExists("finalizedFilter", "change", async () => {
  await refreshFilterLists();
  await loadDashboard();
});

bindClickIfExists("clearSellers", () => {
  selectedSellerIds.clear();
  updateSellerListUI();
  updateAllSelectionInfos();
});

bindClickIfExists("clearCampaigns", () => {
  selectedCampaignNames.clear();
  updateCampaignListUI();
  updateAllSelectionInfos();
});

bindClickIfExists("clearCars", () => {
  selectedCarNames.clear();
  updateCarListUI();
  updateAllSelectionInfos();
});

bindClickIfExists("toggleCampaignsTable", () => {
  expandedTables.campaigns = !expandedTables.campaigns;
  renderCampaigns(currentCampaignsData);
});

bindClickIfExists("toggleCarsTable", () => {
  expandedTables.cars = !expandedTables.cars;
  renderCars(currentCarsData);
});

bindClickIfExists("toggleSellersTable", () => {
  expandedTables.sellers = !expandedTables.sellers;
  renderSellers(currentSellersData);
});

bindClickIfExists("toggleLeadsTable", () => {
  expandedTables.leads = !expandedTables.leads;
  renderLeads(currentLeadsData);
});

bindClickIfExists("closeLeadDrawer", closeLeadDrawer);
bindClickIfExists("leadDrawerOverlay", closeLeadDrawer);

async function initDashboard() {
  setDefaultDates();
  await refreshFilterLists();
  await loadDashboard();
}

initDashboard();