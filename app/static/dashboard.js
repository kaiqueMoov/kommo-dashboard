let selectedSellerIds = new Set();
let selectedCampaignNames = new Set();
let selectedCarNames = new Set();
let currentLeadsData = []; 
let isLeadsExpanded = false; 
const LEADS_LIMIT = 5; // Quantidade de leads visíveis por padrão (mude se quiser)

const CURRENT_YEAR_START = "2026-01-01";

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
  return document.getElementById("searchInput").value.trim();
}

function setDefaultDates() {
  const startInput = document.getElementById("start");
  const endInput = document.getElementById("end");

  const now = new Date();
  const today = now.toISOString().slice(0, 10);

  if (!startInput.value) {
    startInput.value = CURRENT_YEAR_START;
  }

  if (!endInput.value) {
    endInput.value = today;
  }
}
{
  function renderCampaigns(rows) {
  const tbody = document.getElementById("campaignsTable");
  if (!tbody) return;

  tbody.innerHTML = "";

  rows.forEach((row) => {
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
}
}

function updateSelectionInfo(elementId, selectedCount, singular, plural, emptyText) {
  const info = document.getElementById(elementId);

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
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;

  const sellerIds = getSelectedSellerIds();
  const campaignNames = getSelectedCampaignNames();
  const carNames = getSelectedCarNames();
  const search = getSearchValue();

  const params = new URLSearchParams();

  if (start) {
    params.append("start", start);
  }

  if (end) {
    const endDate = new Date(end);
    endDate.setDate(endDate.getDate() + 1);
    const adjustedEnd = endDate.toISOString().slice(0, 10);
    params.append("end", adjustedEnd);
  }

  if (search) {
    params.append("search", search);
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

  if (search) {
    params.append("search", search);
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

function renderSummary(data) {
  document.getElementById("cardTotal").textContent = data.total_leads ?? 0;
  document.getElementById("cardReplied").textContent = data.replied_first_message ?? 0;
  document.getElementById("cardSql").textContent = data.sql_count ?? 0;
  document.getElementById("cardWon").textContent = data.won_count ?? 0;
  document.getElementById("cardLost").textContent = data.lost_count ?? 0;
}

function renderSellers(rows) {
  const tbody = document.getElementById("sellersTable");
  tbody.innerHTML = "";

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.seller_name ?? "Sem responsável"}</td>
      <td>${row.total_leads ?? 0}</td>
      <td>${row.sql_count ?? 0}</td>
      <td>${row.won_count ?? 0}</td>
      <td>${row.lost_count ?? 0}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSources(rows) {
  const tbody = document.getElementById("sourcesTable");
  tbody.innerHTML = "";

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.lead_source ?? "Sem origem"}</td>
      <td>${row.total_leads ?? 0}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderLeads(rows) {
  const tbody = document.getElementById("leadsTable");
  tbody.innerHTML = "";

  // Guarda os dados na variável global para usarmos no botão
  currentLeadsData = rows;

  // Se estiver expandido, mostra tudo. Se não, corta a array no limite.
  const leadsToShow = isLeadsExpanded ? rows : rows.slice(0, LEADS_LIMIT);

  leadsToShow.forEach((row) => {
    const createdAt = row.created_at_kommo
      ? new Date(row.created_at_kommo).toLocaleString("pt-BR")
      : "-";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.lead_name ?? "-"}</td>
      <td>${row.seller_name ?? "Sem responsável"}</td>
      <td>${row.pipeline_id ?? "-"}</td>
      <td>${row.status_id ?? "-"}</td>
      <td>${row.campaign_name ?? "Sem campanha"}</td>
      <td>${row.car_name ?? "Sem carro"}</td>
      <td>${row.lead_source ?? "Sem origem"}</td>
      <td>${createdAt}</td>
    `;
    tbody.appendChild(tr);
  });

  // Chama a função que cria o botão após renderizar a tabela
  renderShowMoreButton();
}



{
  function renderShowMoreButton() {
  let btnContainer = document.getElementById("toggleLeadsContainer");

  // Se o container do botão ainda não existir, cria e insere depois da tabela
  if (!btnContainer) {
    const table = document.getElementById("leadsTable").closest("table");
    btnContainer = document.createElement("div");
    btnContainer.id = "toggleLeadsContainer";
    btnContainer.style.textAlign = "center";
    btnContainer.style.marginTop = "15px"; // Espaço entre a tabela e o botão
    
    table.parentNode.insertBefore(btnContainer, table.nextSibling);
  }

  // Limpa o botão anterior
  btnContainer.innerHTML = "";

  // Só cria o botão se houver mais leads do que o limite permitido
  if (currentLeadsData.length > LEADS_LIMIT) {
    const btn = document.createElement("button");
    
    // Adicione as classes de CSS que você já usa no seu site (ex: "btn btn-primary")
    btn.className = "btn-ver-mais"; 
    btn.style.padding = "8px 16px";
    btn.style.cursor = "pointer";

    // Define o texto dinamicamente
    if (isLeadsExpanded) {
      btn.textContent = "Esconder Leads";
    } else {
      const hiddenCount = currentLeadsData.length - LEADS_LIMIT;
      btn.textContent = `Ver mais (${hiddenCount})`;
    }

    // Ação de clique: inverte o estado e renderiza novamente
    btn.addEventListener("click", () => {
      isLeadsExpanded = !isLeadsExpanded;
      renderLeads(currentLeadsData);
    });

    btnContainer.appendChild(btn);
  }
}
}

function renderOptionList(containerId, rows, optionClass, valueKey, labelKey, selectedSet, clickHandler, skipValues = []) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  rows.forEach((row) => {
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

async function loadDashboard() {
  const query = buildQuery();

  try {
    const [summary, sellers, sources, leads, campaigns] = await Promise.all([
      fetchJson(`/dashboard/summary${query}`),
      fetchJson(`/dashboard/sellers${query}`),
      fetchJson(`/dashboard/sources${query}`),
      fetchJson(`/dashboard/leads${query}`),
      fetchJson(`/dashboard/campaigns${query}`),
    ]);

    renderSummary(summary);
    renderSellers(sellers);
    renderSources(sources);
    
    // Volta a esconder a lista ao buscar novos dados
    isLeadsExpanded = false; 
    renderLeads(leads);
    
    renderCampaigns(campaigns);
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

document.getElementById("applyFilters").addEventListener("click", async () => {
  await refreshFilterLists();
  await loadDashboard();
});

document.getElementById("searchInput").addEventListener("keydown", async (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    await refreshFilterLists();
    await loadDashboard();
  }
});

document.getElementById("clearSellers").addEventListener("click", () => {
  selectedSellerIds.clear();
  updateSellerListUI();
  updateAllSelectionInfos();
});

document.getElementById("clearCampaigns").addEventListener("click", () => {
  selectedCampaignNames.clear();
  updateCampaignListUI();
  updateAllSelectionInfos();
});

document.getElementById("clearCars").addEventListener("click", () => {
  selectedCarNames.clear();
  updateCarListUI();
  updateAllSelectionInfos();
});

async function initDashboard() {
  setDefaultDates();
  await refreshFilterLists();
  await loadDashboard();
}

initDashboard();