const expenseEl = document.getElementById("expenseChart");
const trendEl = document.getElementById("trendChart");

if (expenseEl) {
  const expenseCtx = expenseEl.getContext("2d");
  window.expenseChartInst = new Chart(expenseCtx, {
    type: "pie",
    data: {
      labels: window.expenseCategories || [],
      datasets: [
        {
          data: window.expenseValues || [],
          backgroundColor: ["#4f9dff", "#7c3aed", "#14b8a6", "#f97316", "#e11d48", "#facc15"],
          borderColor: "rgba(255,255,255,0.08)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { color: "#cbd5e1" } },
      },
    },
  });
}

if (trendEl) {
  const trendCtx = trendEl.getContext("2d");
  window.trendChartInst = new Chart(trendCtx, {
    type: "line",
    data: {
      labels: window.trendLabels || [],
      datasets: [
        {
          label: "Monthly Expenses",
          data: window.trendValues || [],
          borderColor: "#4f9dff",
          backgroundColor: "rgba(79, 157, 255, 0.2)",
          tension: 0.35,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: "#93c5fd",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(148, 163, 184, 0.1)" } },
        y: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(148, 163, 184, 0.1)" } },
      },
      plugins: {
        legend: { labels: { color: "#cbd5e1" } },
      },
    },
  });
}

window.updateChartsTheme = function() {
  const isLight = document.body.classList.contains('theme-light');
  const style = getComputedStyle(document.body);
  const textColor = style.getPropertyValue('--text-secondary').trim() || (isLight ? '#475569' : '#cbd5e1');
  const gridColor = style.getPropertyValue('--border').trim() || (isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.08)');
  const borderColor = style.getPropertyValue('--border').trim() || (isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.08)');

  if (window.expenseChartInst) {
    window.expenseChartInst.options.plugins.legend.labels.color = textColor;
    window.expenseChartInst.data.datasets[0].borderColor = borderColor;
    window.expenseChartInst.update();
  }
  if (window.trendChartInst) {
    window.trendChartInst.options.plugins.legend.labels.color = textColor;
    window.trendChartInst.options.scales.x.ticks.color = textColor;
    window.trendChartInst.options.scales.x.grid.color = gridColor;
    window.trendChartInst.options.scales.y.ticks.color = textColor;
    window.trendChartInst.options.scales.y.grid.color = gridColor;
    window.trendChartInst.update();
  }
};

// Initial theme update for charts
if (typeof window.updateChartsTheme === 'function') {
  window.updateChartsTheme();
}
