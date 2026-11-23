const LABELS = {
  host_len: "Domain length",
  num_dots: "Dots",
  num_hyphens: "Hyphens",
  num_digits: "Digits",
  digit_ratio: "Digit ratio",
  num_subdomains: "Subdomains",
  is_ip: "Is an IP address",
  suspicious_tld: "Suspicious TLD (.xyz, .top …)",
  tld_len: "TLD length",
  entropy: "Entropy",
  longest_token: "Longest part",
  vowel_ratio: "Vowel ratio",
  suspicious_words: "Suspicious words (login, verify …)",
};

const form = document.getElementById("form");
const input = document.getElementById("url");
const button = document.getElementById("check");
const output = document.getElementById("output");
const historyList = document.getElementById("history");
let model = null;

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function formatNumber(v) {
  return Number.isInteger(v) ? v : v.toFixed(2);
}

function chips(parts, cls) {
  if (parts.length === 0) return '<span class="muted small">none</span>';
  return parts.map(p => `<span class="chip ${cls}">${escapeHtml(p.ngram)}</span>`).join("");
}

function showResult(url) {
  const host = hostnameOf(url);
  if (!host) {
    output.innerHTML = '<p class="error">Could not read a domain from this link. Example: https://example.com</p>';
    return;
  }
  const r = predict(model, host);
  const features = hostFeatures(host);
  const percent = (r.probability * 100).toFixed(1);
  const isPhishing = r.probability >= 0.5;

  output.innerHTML = `
    <div class="box result">
      <div class="verdict ${isPhishing ? "phishing" : "legit"}">
        <strong>${isPhishing ? "Likely phishing" : "Looks legitimate"}</strong>
        <span>Phishing probability: <b>${percent}%</b></span>
      </div>
      <div class="host">Checked domain: ${escapeHtml(host)}</div>
      <div>
        <div class="bar"><span style="width:${percent}%"></span></div>
        <div class="bar-scale"><span>0%</span><span>50% threshold</span><span>100%</span></div>
      </div>
      <div class="two-cols">
        <div><h3>Pushed towards phishing</h3><div class="chips">${chips(r.phishingParts, "red")}</div></div>
        <div><h3>Pushed towards legitimate</h3><div class="chips">${chips(r.legitParts, "green")}</div></div>
      </div>
      <div>
        <h3>Domain features</h3>
        <div class="table-wrap"><table>
          ${Object.entries(features).map(([k, v]) => `<tr><td>${LABELS[k]}</td><td class="num">${formatNumber(v)}</td></tr>`).join("")}
        </table></div>
        <p class="muted small" style="margin-top:8px">These are the hand-made features from the Random Forest experiment, shown for reference. The verdict above comes from the n-gram model.</p>
      </div>
    </div>`;

  const li = document.createElement("li");
  li.innerHTML = `<span>${escapeHtml(host)}</span><span class="${isPhishing ? "red" : "green"}">${percent}%</span>`;
  historyList.prepend(li);
  document.getElementById("history-box").hidden = false;
}

form.addEventListener("submit", e => {
  e.preventDefault();
  if (model && input.value.trim()) showResult(input.value);
});

document.querySelectorAll(".examples button").forEach(b => {
  b.addEventListener("click", () => {
    input.value = b.textContent;
    if (model) showResult(b.textContent);
  });
});

fetch("model.json")
  .then(res => res.json())
  .then(data => {
    model = data;
    input.disabled = false;
    button.disabled = false;
    button.textContent = "Check";
    input.focus();
  })
  .catch(() => {
    button.textContent = "Error";
    output.innerHTML = '<p class="error">The model could not be loaded. Try refreshing the page.</p>';
  });
