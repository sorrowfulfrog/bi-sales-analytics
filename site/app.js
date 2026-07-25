async function loadPortfolioData() {
  try {
    const response = await fetch("data/metrics.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    Object.entries(data.metrics ?? {}).forEach(([name, value]) => {
      const element = document.querySelector(`[data-metric="${name}"]`);
      if (element) element.textContent = value;
    });

    Object.entries(data.integrations ?? {}).forEach(([name, value]) => {
      const element = document.querySelector(`[data-status="${name}"]`);
      if (!element) return;
      element.textContent = value;
      element.classList.toggle("ready", value.toLowerCase() === "ready");
    });
  } catch (error) {
    console.warn("Portfolio metrics are unavailable:", error);
  }
}

loadPortfolioData();

const lightbox = document.querySelector(".lightbox");
const lightboxImage = lightbox?.querySelector("img");
const closeLightbox = () => lightbox?.close();

document.querySelectorAll("[data-lightbox]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!lightbox || !lightboxImage) return;
    lightboxImage.src = button.dataset.lightbox;
    lightboxImage.alt = button.querySelector("img")?.alt ?? "Power BI dashboard";
    lightbox.showModal();
  });
});

lightbox?.querySelector(".lightbox-close")?.addEventListener("click", closeLightbox);
lightbox?.addEventListener("click", (event) => {
  if (event.target === lightbox) closeLightbox();
});
