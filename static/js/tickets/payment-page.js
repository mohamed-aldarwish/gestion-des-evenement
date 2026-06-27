document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("payment-form");

  if (!form || typeof Stripe === "undefined") {
    return;
  }

  const stripe = Stripe(form.dataset.stripePublicKey);
  const elements = stripe.elements();
  const card = elements.create("card");

  card.mount("#card-element");

  const submitBtn = document.getElementById("submit");
  const messageBox = document.getElementById("payment-message");

  const resetButton = () => {
    submitBtn.disabled = false;
    submitBtn.innerText = "Pay Now";
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    submitBtn.disabled = true;
    submitBtn.innerText = "Processing...";
    messageBox.textContent = "";

    try {
      const response = await fetch(form.dataset.createIntentUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": form.dataset.csrfToken,
        },
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        messageBox.textContent = data.error || "Payment initialization failed.";
        resetButton();
        return;
      }

      const result = await stripe.confirmCardPayment(data.clientSecret, {
        payment_method: {
          card,
        },
      });

      if (result.error) {
        messageBox.textContent = result.error.message;
        resetButton();
        return;
      }

      if (result.paymentIntent.status === "succeeded") {
        window.location.href = `${form.dataset.successUrl}?payment_intent=${result.paymentIntent.id}`;
      } else {
        window.location.href = form.dataset.cancelUrl;
      }
    } catch (error) {
      messageBox.textContent = "An error occurred. Please try again.";
      resetButton();
    }
  });
});
