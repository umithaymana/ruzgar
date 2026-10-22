/** Pilot B Vitrin — Rüzgar */
document.getElementById("btn-hello")?.addEventListener("click", () => {
  const out = document.getElementById("out");
  if (out) out.textContent = "Merhaba Ümit abi — Pilot B vitrin ayakta.";
});
document.getElementById("contact")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  alert(`Teşekkürler, ${fd.get("name") || "ziyaretçi"}!`);
});
