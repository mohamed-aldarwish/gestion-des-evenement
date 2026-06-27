const dateInput = document.getElementById("event_date");
      const alertMsg = document.getElementById("date-alert");

      dateInput.addEventListener("change", function () {
        const selectedDate = new Date(this.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
          alertMsg.style.display = "block";
          this.style.borderColor = "#ef4444";
        } else {
          alertMsg.style.display = "none";
          this.style.borderColor = "var(--accent)";
        }
      });

      // تأثير زر الإرسال
      document.querySelector("form").addEventListener("submit", function () {
        const btn = this.querySelector('button[type="submit"]');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement...';
        btn.style.pointerEvents = "none";
      });
