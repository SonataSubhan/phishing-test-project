const slides = [...document.querySelectorAll(".slide")];
const counter = document.getElementById("counter");
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const bar = document.getElementById("progress");
let current = 0;

function show(i) {
  current = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((s, k) => s.classList.toggle("current", k === current));
  slides[current].scrollTop = 0;
  counter.textContent = `${current + 1} / ${slides.length}`;
  prev.disabled = current === 0;
  next.disabled = current === slides.length - 1;
  bar.style.width = `${((current + 1) / slides.length) * 100}%`;
  history.replaceState(null, "", `#${current + 1}`);
}

prev.addEventListener("click", () => show(current - 1));
next.addEventListener("click", () => show(current + 1));

document.addEventListener("keydown", e => {
  if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") { e.preventDefault(); show(current + 1); }
  if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); show(current - 1); }
  if (e.key === "Home") show(0);
  if (e.key === "End") show(slides.length - 1);
  if (e.key === "f") document.documentElement.requestFullscreen?.().catch(() => {});
});

const start = parseInt(location.hash.slice(1), 10);
show(Number.isNaN(start) ? 0 : start - 1);
