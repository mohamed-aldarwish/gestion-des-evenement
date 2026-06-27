const form = document.getElementById("deleteForm");
      const btn = document.getElementById("confirmDeleteBtn");

      form.addEventListener("submit", (e) => {
        // تأثير اهتزاز أخير قبل الحذف
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Suppression...';
        btn.style.opacity = "0.8";
        btn.style.pointerEvents = "none";
      });
