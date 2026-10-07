// EduPulse Main JavaScript Helpers

document.addEventListener("DOMContentLoaded", () => {
  // 1. User Dropdown Toggle
  const dropdownTriggers = document.querySelectorAll("[data-dropdown-toggle]");
  dropdownTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const targetId = trigger.getAttribute("data-dropdown-toggle");
      const targetMenu = document.getElementById(targetId);
      if (targetMenu) {
        targetMenu.classList.toggle("show");
      }
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown-menu.show").forEach((menu) => {
      menu.classList.remove("show");
    });
  });

  // 2. Modals
  const modalTriggers = document.querySelectorAll("[data-modal-target]");
  modalTriggers.forEach((btn) => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-modal-target");
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.style.display = "flex";
      }
    });
  });

  const modalCloses = document.querySelectorAll("[data-modal-close]");
  modalCloses.forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal-backdrop");
      if (modal) {
        modal.style.display = "none";
      }
    });
  });

  // 3. Radio Card selection highlighting
  document.querySelectorAll(".option-label input[type='radio']").forEach((radio) => {
    radio.addEventListener("change", function () {
      const name = this.name;
      document.querySelectorAll(`input[name='${name}']`).forEach((r) => {
        r.closest(".option-label").classList.remove("selected");
      });
      if (this.checked) {
        this.closest(".option-label").classList.add("selected");
      }
    });
  });
});

// Toast Notifications Helper
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.style.position = "fixed";
    container.style.bottom = "24px";
    container.style.right = "24px";
    container.style.zIndex = "9999";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "8px";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `alert alert-${type === "error" ? "danger" : type === "success" ? "success" : "info"}`;
  toast.style.boxShadow = "0 10px 15px -3px rgba(0,0,0,0.1)";
  toast.style.animation = "fadeIn 0.25s ease";
  toast.innerHTML = `<i class="fa-solid fa-circle-info"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
