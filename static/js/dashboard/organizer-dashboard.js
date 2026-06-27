document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-progress]").forEach((bar) => {
    const progress = Number.parseFloat(bar.dataset.progress) || 0;
    bar.style.width = `${Math.min(Math.max(progress, 0), 100)}%`;
  });

  const revenueChart = document.getElementById("revenueChart");

  if (!revenueChart || typeof Chart === "undefined") {
    return;
  }

  let revenueData = [];

  try {
    revenueData = JSON.parse(revenueChart.dataset.chartData || "[]");
  } catch (error) {
    revenueData = [];
  }

  new Chart(revenueChart, {
    type: "line",
    data: {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
      datasets: [{
        label: "Revenue",
        data: revenueData,
        borderColor: "#d4af37",
        backgroundColor: "rgba(212,175,55,0.15)",
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
    },
  });
});
