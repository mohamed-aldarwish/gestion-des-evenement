document.addEventListener("DOMContentLoaded", () => {
        const card = document.getElementById("registerCard");

        // تأثير الدخول
        setTimeout(() => {
          card.classList.add("active");
        }, 150);

        const form = document.getElementById("registerForm");
        const btn = document.getElementById("regBtn");
        const btnText = btn.querySelector("span");
        const loader = document.getElementById("regLoader");

        form.addEventListener("submit", () => {
          btnText.innerText = "Registering...";
          loader.style.display = "inline-block";
          btn.style.pointerEvents = "none";
          btn.style.opacity = "0.9";
        });
      });
