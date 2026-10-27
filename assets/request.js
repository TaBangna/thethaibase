// "Tell us what you need" form. Nothing is sent to or stored by the website:
// the request is written out as a message and opened in a LINE (@thethaibase)
// or WhatsApp chat with us, where the renter presses send. It is also copied to the
// clipboard and shown on the page in case LINE isn't installed.
(function () {
  var LINE_ID = "@thethaibase";
  var T = {
    en: {
      head: "Condo request via thethaibase.com",
      budget: "Budget", beds: "Bedrooms", movein: "Move-in", lease: "Lease", people: "People",
      pets: "Pets", work: "Work/study", bld: "Buildings", notes: "Notes", name: "Name",
      missing: "Please fill in the fields marked *.",
      opening: "Opening the app… If nothing happens, copy the request below.",
      copied: "Copied. Paste it into a chat with us on LINE or WhatsApp."
    },
    th: {
      head: "แจ้งหาห้องเช่า ผ่าน thethaibase.com",
      budget: "งบ", beds: "ห้องนอน", movein: "ย้ายเข้า", lease: "สัญญา", people: "ผู้พักอาศัย",
      pets: "สัตว์เลี้ยง", work: "ที่ทำงาน/ที่เรียน", bld: "โครงการ", notes: "รายละเอียดเพิ่มเติม", name: "ชื่อ",
      missing: "กรุณากรอกช่องที่มีเครื่องหมาย *",
      opening: "กำลังเปิดแอป… ถ้าไม่เปิด คัดลอกข้อความด้านล่างได้เลย",
      copied: "คัดลอกแล้ว วางในแชท LINE หรือ WhatsApp ของเราได้เลย"
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("need-form");
    if (!form) return;
    var L = T[form.getAttribute("data-lang")] || T.en;
    var WA = (form.getAttribute("data-wa") || "").replace(/\D/g, "");
    if (!WA) form.querySelectorAll("[data-wa-only]").forEach(function (b) { b.remove(); });
    var msg = document.getElementById("need-msg");
    var box = document.getElementById("need-fallback");
    var text = document.getElementById("need-text");

    var date = form.elements.movein;
    try { date.min = new Date().toISOString().slice(0, 10); } catch (e) {}

    // "Any" and specific buildings are mutually exclusive.
    var blds = form.querySelectorAll('input[name="bld"]');
    blds.forEach(function (cb) {
      cb.addEventListener("change", function () {
        if (!cb.checked) return;
        blds.forEach(function (o) {
          if (o !== cb && (cb.value === "Any in Bang Na" || o.value === "Any in Bang Na")) o.checked = false;
        });
      });
    });

    form.addEventListener("input", function (ev) {
      var f = ev.target.closest && ev.target.closest(".field");
      if (f) f.classList.remove("field-bad");
    });

    function val(n) { var el = form.elements[n]; return el ? String(el.value || "").trim() : ""; }

    function compose() {
      var b = [];
      blds.forEach(function (cb) { if (cb.checked) b.push(cb.value); });
      var lines = [L.head, ""];
      [["name", val("name")], ["budget", val("budget")], ["beds", val("beds")], ["movein", val("movein")],
       ["lease", val("lease")], ["people", val("people")], ["pets", val("pets")], ["work", val("work")],
       ["bld", b.join(", ")], ["notes", val("notes")]].forEach(function (p) {
        if (p[1]) lines.push(L[p[0]] + ": " + p[1]);
      });
      return lines.join("\n");
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var via = (ev.submitter && ev.submitter.value) || "line";
      var bad = ["budget", "beds", "movein", "name"].filter(function (n) { return !val(n); });
      form.querySelectorAll(".field").forEach(function (f) { f.classList.remove("field-bad"); });
      if (bad.length) {
        bad.forEach(function (n) { var f = form.elements[n].closest(".field"); if (f) f.classList.add("field-bad"); });
        msg.textContent = L.missing;
        form.elements[bad[0]].focus();
        return;
      }
      var m = compose();
      text.value = m;
      box.hidden = false;
      msg.textContent = L.opening;
      try { if (navigator.clipboard) navigator.clipboard.writeText(m).catch(function () {}); } catch (e) {}
      if (typeof gtag === "function") {
        gtag("event", "generate_lead", { method: "request_form_" + via, link_location: "find_a_condo",
          budget: val("budget"), bedrooms: val("beds"), page_lang: document.documentElement.lang });
      }
      if (via === "whatsapp" && WA) window.location.href = "https://wa.me/" + WA + "?text=" + encodeURIComponent(m);
      else window.location.href = "https://line.me/R/oaMessage/" + encodeURIComponent(LINE_ID) + "/?" + encodeURIComponent(m);
    });

    document.getElementById("need-copy").addEventListener("click", function () {
      text.select();
      var done = function () { msg.textContent = L.copied; };
      try {
        if (navigator.clipboard) navigator.clipboard.writeText(text.value).then(done, function () { document.execCommand("copy"); done(); });
        else { document.execCommand("copy"); done(); }
      } catch (e) {}
    });
  });
})();
