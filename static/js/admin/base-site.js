document.addEventListener("DOMContentLoaded", function () {
    const header = document.querySelector("#header");

    if (header) {
      header.addEventListener("mouseenter", function () {
        header.style.filter = "brightness(1.15)";
      });

      header.addEventListener("mouseleave", function () {
        header.style.filter = "brightness(1)";
      });
    }

    console.log("Custom Django Admin loaded successfully.");
  });
