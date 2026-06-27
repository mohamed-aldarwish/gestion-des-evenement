// تحسين تجربة المستخدم عند الضغط على الزر
      const form = document.querySelector("form");
      const submitBtn = document.querySelector('button[type="submit"]');

      form.addEventListener("submit", () => {
        submitBtn.innerHTML = "Processing...";
        submitBtn.style.opacity = "0.7";
        submitBtn.style.pointerEvents = "none";
      });
