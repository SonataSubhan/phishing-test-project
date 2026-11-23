// Runs the exported model (web/model.json) in the browser.
// Same steps as scikit-learn: char n-grams -> TF-IDF -> L2 norm -> logistic regression.

const SUSPICIOUS_WORDS = ["login", "signin", "verify", "secure", "account", "update",
  "bank", "confirm", "password", "wallet", "support", "auth"];
const SUSPICIOUS_TLDS = new Set(["xyz", "top", "tk", "ml", "ga", "cf", "gq", "buzz", "live",
  "click", "info", "online", "site", "app", "io", "ru", "cn"]);

function hostnameOf(url) {
  url = url.trim();
  if (!url.includes("://")) url = "http://" + url;
  let host;
  try {
    host = new URL(url).hostname.toLowerCase();
  } catch (e) {
    return "";
  }
  if (host.startsWith("[") && host.endsWith("]")) host = host.slice(1, -1);
  return host.startsWith("www.") ? host.slice(4) : host;
}

function entropy(s) {
  if (!s) return 0;
  const counts = {};
  for (const ch of s) counts[ch] = (counts[ch] || 0) + 1;
  let e = 0;
  for (const c of Object.values(counts)) {
    const p = c / s.length;
    e -= p * Math.log2(p);
  }
  return e;
}

function isIp(host) {
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return host.split(".").every(n => Number(n) <= 255);
  return host.includes(":");  // IPv6
}

function hostFeatures(host) {
  const parts = host.split(".");
  const tld = parts.length > 1 ? parts[parts.length - 1] : "";
  const tokens = host.split(/[.\-]/);
  const digits = [...host].filter(ch => ch >= "0" && ch <= "9").length;
  const letters = [...host].filter(ch => /\p{L}/u.test(ch)).length;
  const vowels = [...host].filter(ch => "aeiou".includes(ch)).length;
  return {
    host_len: host.length,
    num_dots: parts.length - 1,
    num_hyphens: (host.match(/-/g) || []).length,
    num_digits: digits,
    digit_ratio: digits / Math.max(host.length, 1),
    num_subdomains: Math.max(parts.length - 2, 0),
    is_ip: isIp(host) ? 1 : 0,
    suspicious_tld: SUSPICIOUS_TLDS.has(tld) ? 1 : 0,
    tld_len: tld.length,
    entropy: entropy(host),
    longest_token: Math.max(0, ...tokens.map(t => t.length)),
    vowel_ratio: vowels / Math.max(letters, 1),
    suspicious_words: SUSPICIOUS_WORDS.filter(w => host.includes(w)).length,
  };
}

function charNgrams(text, minN, maxN) {
  const counts = new Map();
  const chars = [...text];
  for (let n = minN; n <= Math.min(maxN, chars.length); n++) {
    for (let i = 0; i + n <= chars.length; i++) {
      const g = chars.slice(i, i + n).join("");
      counts.set(g, (counts.get(g) || 0) + 1);
    }
  }
  return counts;
}

function predict(model, host) {
  const [minN, maxN] = model.ngram_range;
  const terms = [];
  let norm = 0;
  for (const [g, count] of charNgrams(host.replace(/\s+/g, " "), minN, maxN)) {
    const entry = model.vocab[g];
    if (!entry) continue;
    const [idf, weight] = entry;
    const value = (1 + Math.log(count)) * idf;
    terms.push({ ngram: g, value, weight });
    norm += value * value;
  }
  norm = Math.sqrt(norm) || 1;

  let score = model.intercept;
  for (const t of terms) {
    t.contribution = (t.value / norm) * t.weight;
    score += t.contribution;
  }
  terms.sort((a, b) => b.contribution - a.contribution);
  return {
    probability: 1 / (1 + Math.exp(-score)),
    phishingParts: terms.filter(t => t.contribution > 0).slice(0, 6),
    legitParts: terms.filter(t => t.contribution < 0).reverse().slice(0, 6),
  };
}

if (typeof module !== "undefined") module.exports = { hostnameOf, hostFeatures, predict };
