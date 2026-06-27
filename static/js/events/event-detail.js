document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-hero-image]").forEach((hero) => {
    hero.style.backgroundImage = `linear-gradient(rgba(15,23,42,.72), rgba(15,23,42,.72)), url('${hero.dataset.heroImage}')`;
    hero.style.backgroundSize = "cover";
    hero.style.backgroundPosition = "center";
  });

  const progressBar = document.getElementById("progress-bar");
  const seatsPercent = document.getElementById("seats-percent");

  if (!progressBar || !seatsPercent) {
    return;
  }

  const capacity = Number.parseInt(progressBar.dataset.capacity, 10) || 0;
  const remaining = Number.parseInt(progressBar.dataset.remaining, 10) || 0;
  const taken = Math.max(capacity - remaining, 0);
  const percentage = capacity > 0 ? Math.min((taken / capacity) * 100, 100) : 0;

  progressBar.style.width = `${percentage}%`;
  seatsPercent.innerText = `${Math.round(percentage)}% Full`;
});
