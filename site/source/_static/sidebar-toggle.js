// On wide screens, make the primary toggle collapse the sidebar
// instead of opening PyData's modal dialog.
const WIDE = window.matchMedia("(min-width: 992px)");
const KEY = "sbt-primary-collapsed";

if (sessionStorage.getItem(KEY) === "1") {
  document.documentElement.classList.add(KEY);
}

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".primary-toggle");
  if (!btn || !WIDE.matches) return;   // leave mobile behaviour alone
  event.preventDefault();
  event.stopImmediatePropagation();     // capture phase, so PyData never sees it
  const collapsed = document.documentElement.classList.toggle(KEY);
  try { sessionStorage.setItem(KEY, collapsed ? "1" : "0"); } catch (e) {}
}, true);
