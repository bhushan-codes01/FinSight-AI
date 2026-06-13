const expenseCtx = document.getElementById("expenseChart").getContext("2d");
const trendCtx = document.getElementById("trendChart").getContext("2d");

const expenseChart = new Chart(expenseCtx, {
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
    plugins: {
      legend: { position: "bottom", labels: { color: "#cbd5e1" } },
    },
  },
});

const trendChart = new Chart(trendCtx, {
  type: "line",
  data: {
    labels: window.trendLabels || [],
    datasets: [
      {
        label: "Net Cash Flow",
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
    scales: {
      x: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(148, 163, 184, 0.1)" } },
      y: { ticks: { color: "#cbd5e1" }, grid: { color: "rgba(148, 163, 184, 0.1)" } },
    },
    plugins: {
      legend: { labels: { color: "#cbd5e1" } },
    },
  },
});
