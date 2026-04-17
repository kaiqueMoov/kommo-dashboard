function buildQuery() {
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;

  const params = new URLSearchParams();

  if (start) params.append("start", start);
  if (end) {
    const endDate = new Date(end);
    endDate.setDate(endDate.getDate() + 1);
    const adjustedEnd = endDate.toISOString().slice(0, 10);
    params.append("end", adjustedEnd);
  }

  const query = params.toString();
  return query ? `?${query}` : "";
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

  rows.forEach((row) => {
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
}

async function loadDashboard() {
  const query = buildQuery();

  try {
    const [summary, sellers, sources, leads] = await Promise.all([
      fetchJson(`/dashboard/summary${query}`),
      fetchJson(`/dashboard/sellers${query}`),
      fetchJson(`/dashboard/sources${query}`),
      fetchJson(`/dashboard/leads${query}`),
    ]);

    renderSummary(summary);
    renderSellers(sellers);
    renderSources(sources);
    renderLeads(leads);
  } catch (error) {
    console.error(error);
    alert("Erro ao carregar o dashboard.");
  }
}

document.getElementById("applyFilters").addEventListener("click", loadDashboard);

loadDashboard();