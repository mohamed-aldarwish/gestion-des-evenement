document.addEventListener("DOMContentLoaded", () => {
        const card = document.getElementById("loginCard");
        const togglePass = document.getElementById("togglePass");
        const passwordField = document.getElementById("passwordField");
        const form = document.getElementById("loginForm");
        const btn = document.getElementById("submitBtn");
        const btnText = btn.querySelector("span");
        const loader = document.getElementById("btnLoader");

        // ظهور البطاقة بسلاسة
        setTimeout(() => {
          card.classList.add("active");
        }, 150);

        // إظهار/إخفاء كلمة المرور
        togglePass.addEventListener("click", () => {
          const type =
            passwordField.getAttribute("type") === "password"
              ? "text"
              : "password";
          passwordField.setAttribute("type", type);
          togglePass.classList.toggle("fa-eye");
          togglePass.classList.toggle("fa-eye-slash");
        });

        // حركة الزر عند الإرسال
        form.addEventListener("submit", (e) => {
          btnText.innerText = "Authenticating...";
          loader.style.display = "inline-block";
          btn.style.pointerEvents = "none";
          btn.style.opacity = "0.8";
        });
      });
