// Admin view for The Thai Base.
// Public pages show floor ranges only. Exact floors, owners and room numbers live in
// /assets/admin-data.json, encrypted (AES-GCM, key from the passphrase via PBKDF2).
// After sign-in the derived key is kept on this device so listing pages show exact floors.
(function () {
  var KEY = "ttbAdminKey";
  var DATA_URL = "/assets/admin-data.json";

  function store(get, val) {
    try {
      if (get) return localStorage.getItem(KEY);
      if (val === null) localStorage.removeItem(KEY); else localStorage.setItem(KEY, val);
    } catch (e) { return null; }
  }
  function b64(s) { return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); }); }
  function toB64(buf) { return btoa(String.fromCharCode.apply(null, new Uint8Array(buf))); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  var blobPromise;
  function blob() {
    if (!blobPromise) blobPromise = fetch(DATA_URL, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("no admin data"); return r.json();
    });
    return blobPromise;
  }

  async function deriveRaw(pass, b) {
    var base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pass), "PBKDF2", false, ["deriveKey"]);
    var key = await crypto.subtle.deriveKey(
      { name: "PBKDF2", salt: b64(b.salt), iterations: b.iter, hash: "SHA-256" },
      base, { name: "AES-GCM", length: 256 }, true, ["decrypt"]);
    return crypto.subtle.exportKey("raw", key);
  }

  async function decrypt(rawB64, b) {
    var key = await crypto.subtle.importKey("raw", b64(rawB64), "AES-GCM", false, ["decrypt"]);
    var pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(b.iv) }, key, b64(b.data));
    return JSON.parse(new TextDecoder().decode(pt));
  }

  function fillFloors(rows) {
    var byId = {};
    rows.forEach(function (r) { byId[r.id] = r; });
    document.querySelectorAll("[data-floor-id]").forEach(function (el) {
      var r = byId[el.getAttribute("data-floor-id")];
      if (!r || !r.floor) return;
      var th = el.getAttribute("data-lang") === "th";
      var t = el.getAttribute("data-floor-tower");
      el.textContent = (th ? "ชั้น " : "Floor ") + r.floor + (t ? (th ? ", ตึก " : ", Tower ") + t : "");
      el.title = "Exact floor — visible to admins only";
      el.style.fontWeight = "600";
    });
  }

  function adminBar() {
    if (document.getElementById("ttb-admin-bar")) return;
    var bar = document.createElement("div");
    bar.id = "ttb-admin-bar";
    bar.setAttribute("style", "position:fixed;bottom:12px;right:12px;z-index:50;background:#1B2635;color:#fff;" +
      "padding:8px 12px;border-radius:6px;font-size:.85rem;box-shadow:0 2px 8px rgba(0,0,0,.25)");
    bar.innerHTML = 'Admin view · <a href="/admin/" style="color:#fff">Units</a> · ' +
      '<a href="#" id="ttb-admin-out" style="color:#fff">Sign out</a>';
    document.body.appendChild(bar);
    document.getElementById("ttb-admin-out").addEventListener("click", function (ev) {
      ev.preventDefault(); store(false, null); location.reload();
    });
  }

  function table(rows) {
    var host = document.getElementById("admin-table");
    if (!host) return;
    var head = ["Ref", "Deal", "Price", "Beds", "Size", "Tower", "Floor", "Owner", "Room", "Notes"];
    var body = rows.map(function (r) {
      var ref = r.url ? '<a href="' + esc(r.url) + '">' + esc(r.id) + "</a>" : esc(r.id);
      return "<tr><td>" + ref + "</td><td>" + esc(r.deal) + "</td><td>" + esc(r.price) + "</td><td>" +
        esc(r.beds) + "</td><td>" + esc(r.size) + "</td><td>" + esc(r.tower) + "</td><td><strong>" +
        esc(r.floor) + "</strong></td><td>" + esc(r.owner) + "</td><td>" + esc(r.room) + "</td><td>" +
        esc(r.notes) + "</td></tr>";
    }).join("");
    host.innerHTML = '<div class="table-scroll"><table class="rent-table"><thead><tr>' +
      head.map(function (h) { return '<th scope="col">' + h + "</th>"; }).join("") +
      "</tr></thead><tbody>" + body + "</tbody></table></div>";
    var form = document.getElementById("admin-login");
    if (form) form.style.display = "none";
  }

  // Price, size, bedrooms etc. come from the public unit list built on every
  // deploy, so they are current even when the encrypted file is older.
  async function merge(rows) {
    var pub;
    try {
      var r = await fetch("/assets/admin-units.json", { cache: "no-store" });
      if (!r.ok) return rows;
      pub = await r.json();
    } catch (e) { return rows; }
    var byId = {};
    rows.forEach(function (row) { byId[row.id] = row; });
    return pub.map(function (p) {
      var priv = byId[p.id] || {};
      return Object.assign({}, priv, p, { floor: priv.floor, owner: priv.owner, room: priv.room, notes: priv.notes });
    });
  }

  async function run(raw) {
    var rows = await merge(await decrypt(raw, await blob()));
    fillFloors(rows); adminBar(); table(rows);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var raw = store(true);
    if (raw) run(raw).catch(function () { store(false, null); });

    var form = document.getElementById("admin-login");
    if (!form) return;
    form.addEventListener("submit", async function (ev) {
      ev.preventDefault();
      var msg = document.getElementById("admin-msg");
      msg.textContent = "Checking…";
      try {
        var b = await blob();
        var rawKey = toB64(await deriveRaw(document.getElementById("admin-pass").value, b));
        await run(rawKey);
        store(false, rawKey);
        msg.textContent = "";
      } catch (e) {
        msg.textContent = "Wrong passphrase, or the admin data isn't published yet.";
      }
    });
  });
})();
