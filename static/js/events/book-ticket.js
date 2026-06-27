const form = document.getElementById("bookingForm");

      if (form) {
        form.onsubmit = function () {
          const btn = document.getElementById("confirmBtn");
          btn.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Processing...';
          btn.disabled = true;
        };
      }
