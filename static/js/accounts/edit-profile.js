// Dynamic Avatar Preview
  const avatarInput = document.querySelector('input[type="file"]');
  const avatarPreview = document.getElementById("avatarPreview");

  if (avatarInput && avatarPreview) {
    // Add the styling class to the input dynamically
    avatarInput.classList.add('form-input-style');
    
    avatarInput.addEventListener("change", function () {
      const file = this.files && this.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = function(e) {
        avatarPreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
      }
      reader.readAsDataURL(file);
    });
  }

  // Inject styles into the auto-generated Django inputs
  document.querySelectorAll('input:not([type="checkbox"]):not([type="file"]), select, textarea').forEach(input => {
    input.classList.add('form-input-style');
  });
  const fileInput = document.querySelector('input[type="file"]');
const fileNameDisplay = document.getElementById("file-name-display");
const fileLabel = document.querySelector(".file-label");

if (fileInput) {
    fileInput.addEventListener("change", function() {
        if (this.files && this.files.length > 0) {
            const name = this.files[0].name;
            // Affiche le nom du fichier au lieu du texte par défaut
            fileNameDisplay.textContent = name;
            fileLabel.classList.add("active");
        } else {
            fileNameDisplay.textContent = "Choisir une image...";
            fileLabel.classList.remove("active");
        }
    });
}
