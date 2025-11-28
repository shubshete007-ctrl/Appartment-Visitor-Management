
document.addEventListener("click", (e) => {
  const openTarget = e.target.closest("[data-open-modal]");
  const closeTarget = e.target.closest("[data-close-modal]");

  if (openTarget) {
    const id = openTarget.getAttribute("data-open-modal");
    const modal = document.getElementById(id);
    if (modal) modal.classList.add("show");
  }

  if (closeTarget) {
    const modal = closeTarget.closest(".modal");
    if (modal) modal.classList.remove("show");
  }
});

document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
  backdrop.addEventListener("click", () => {
    const modal = backdrop.closest(".modal");
    if (modal) modal.classList.remove("show");
  });
});

const toggleBtn = document.getElementById("mobileMenuToggle");
const sidebar = document.querySelector(".sidebar");

if (toggleBtn && sidebar) {
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
}

// Auto-hide flash messages (login/logout/success/error) after 2 seconds
window.addEventListener("load", () => {
  const flashMessages = document.querySelectorAll(".flash");
  if (flashMessages.length) {
    setTimeout(() => {
      flashMessages.forEach(f => {
        f.style.transition = "opacity 0.5s ease";
        f.style.opacity = "0";
        setTimeout(() => f.remove(), 500); // Remove after fade
      });
    }, 2000);
  }
});