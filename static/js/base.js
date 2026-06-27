setTimeout(function () {
        const messages = document.querySelectorAll(".alert");
        messages.forEach((msg) => {
          msg.style.transition = "0.5s";
          msg.style.opacity = "0";
          setTimeout(() => msg.remove(), 500);
        });
      }, 4000);
