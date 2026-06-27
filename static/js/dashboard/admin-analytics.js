document.addEventListener("DOMContentLoaded", () => {
  if (typeof Chart === "undefined") {
    return;
  }

  const ticketsChart = document.getElementById("ticketsChart");
  const statusChart = document.getElementById("statusChart");

  if (!ticketsChart || !statusChart) {
    return;
  }

  const parseChartData = (value) => {
    try {
      return JSON.parse(value || "[]");
    } catch (error) {
      return [];
    }
  };

  new Chart(ticketsChart, {
    type: "line",
    data: {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
      datasets: [{
        label: "Tickets",
        data: parseChartData(ticketsChart.dataset.chartData),
        tension: 0.4,
        fill: true,
      }],
    },
  });

  new Chart(statusChart, {
    type: "doughnut",
    data: {
      labels: ["Published", "Draft"],
      datasets: [{
        data: parseChartData(statusChart.dataset.chartData),
      }],
    },
  });
});
