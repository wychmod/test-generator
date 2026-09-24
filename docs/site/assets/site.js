/* Testcase Generator 官网交互 */
(function () {
  "use strict";

  /* ---------- 移动端导航 ---------- */
  var navToggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("open");
    });
  }

  /* ---------- 滚动渐入 ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- 通用复制 ---------- */
  function copyText(text, btn, okLabel) {
    function done() {
      var old = btn.textContent;
      btn.textContent = okLabel || "已复制";
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = old;
        btn.classList.remove("copied");
      }, 1600);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(); });
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { /* 忽略 */ }
      document.body.removeChild(ta);
    }
  }
  document.querySelectorAll("[data-copy-text]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      copyText(btn.getAttribute("data-copy-text"), btn, "已复制");
    });
  });

  /* ---------- 流水线 Tabs（index.html） ---------- */
  var pipeTabs = document.querySelectorAll(".pipe-tab");
  var pipePanel = document.getElementById("pipe-panel");
  if (pipeTabs.length && pipePanel && window.PIPELINE_DATA) {
    function renderPhase(key) {
      var d = window.PIPELINE_DATA[key];
      if (!d) { return; }
      pipePanel.innerHTML =
        '<h3>' + d.title + '</h3>' +
        '<p class="pipe-sub">' + d.sub + '</p>' +
        '<div class="pipe-grid">' +
        '<div class="pipe-block"><h4>核心产出</h4><ul>' + d.outputs.map(function (o) { return '<li>' + o + '</li>'; }).join('') + '</ul></div>' +
        '<div class="pipe-block"><h4>关键能力</h4><ul>' + d.skills.map(function (s) { return '<li>' + s + '</li>'; }).join('') + '</ul></div>' +
        '</div>' +
        '<div class="gate-meter"><div class="gm-label"><span>质量门禁阈值</span><span>' + d.gate + ' / 100</span></div>' +
        '<div class="gate-bar"><span style="width:' + d.gate + '%"></span></div></div>' +
        (d.note ? '<div class="pipe-note">' + d.note + '</div>' : '');
    }
    pipeTabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        pipeTabs.forEach(function (t) { t.classList.remove("active"); });
        tab.classList.add("active");
        renderPhase(tab.getAttribute("data-phase"));
      });
    });
    renderPhase("p0");
  }

  /* ---------- agents.html 文档浏览 ---------- */
  var docLinks = document.querySelectorAll(".doc-link");
  if (docLinks.length) {
    var panels = document.querySelectorAll(".doc-panel");
    var sidebar = document.querySelector(".agents-sidebar");
    var sidebarToggle = document.querySelector(".sidebar-toggle");

    function showDoc(id, push) {
      panels.forEach(function (p) { p.hidden = p.id !== "doc-" + id; });
      docLinks.forEach(function (l) {
        l.classList.toggle("active", l.getAttribute("data-doc") === id);
      });
      if (push !== false) {
        history.replaceState(null, "", "#" + id);
      }
      if (sidebar) { sidebar.classList.remove("open"); }
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    docLinks.forEach(function (link) {
      link.addEventListener("click", function () {
        showDoc(link.getAttribute("data-doc"));
      });
    });
    var initial = location.hash.replace("#", "");
    var firstDoc = docLinks[0].getAttribute("data-doc");
    showDoc(document.getElementById("doc-" + initial) ? initial : firstDoc, false);

    /* 分组折叠 */
    document.querySelectorAll(".nav-group-head").forEach(function (head) {
      head.addEventListener("click", function () {
        head.closest(".nav-group").classList.toggle("collapsed");
      });
    });

    /* 搜索过滤 */
    var search = document.querySelector(".sidebar-search");
    if (search) {
      search.addEventListener("input", function () {
        var q = search.value.trim().toLowerCase();
        docLinks.forEach(function (l) {
          var hit = !q || l.getAttribute("data-title").indexOf(q) !== -1 ||
            l.textContent.toLowerCase().indexOf(q) !== -1;
          l.classList.toggle("hidden-by-search", !hit);
        });
        if (q) {
          document.querySelectorAll(".nav-group").forEach(function (g) { g.classList.remove("collapsed"); });
        }
      });
    }

    /* 移动端抽屉 */
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener("click", function () { sidebar.classList.add("open"); });
      var closeBtn = sidebar.querySelector(".sidebar-close");
      if (closeBtn) {
        closeBtn.addEventListener("click", function () { sidebar.classList.remove("open"); });
      }
    }

    /* 复制提示词原文（base64 → UTF-8） */
    document.querySelectorAll("[data-copy-raw]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-copy-raw");
        var b64 = window.PROMPT_RAW && window.PROMPT_RAW[id];
        if (!b64) { return; }
        var bin = atob(b64);
        var bytes = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) { bytes[i] = bin.charCodeAt(i); }
        var text = new TextDecoder("utf-8").decode(bytes);
        copyText(text, btn, "已复制原文");
      });
    });
  }
})();
