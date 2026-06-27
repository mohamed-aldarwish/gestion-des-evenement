// Apply uniform styling to auto-generated Django password fields
  document.querySelectorAll('input[type="password"]').forEach(input => {
    input.classList.add('password-input-style');
    // Clear placeholder if any to keep it clean
    input.placeholder = "••••••••";
  });
