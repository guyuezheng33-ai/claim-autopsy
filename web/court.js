/* Citation court UI. The judge lives in core/court.py; this file only renders
 * its dossier and, when a local server is present, asks for a live AI run. */
(function () {
  "use strict";

  var EXAMPLES = [
    { key: "eiffel", label: "Eiffel Tower · supported" },
    { key: "flu", label: "Flu vaccine · refuted" },
    { key: "population", label: "Population guard · AI struck" },
    { key: "coffee", label: "Coffee & growth · not in source" },
    { key: "struck", label: "Fabricated quote · struck" }
  ];
  var activeKey = "eiffel";
  var currentDossier = null;
  var currentMulti = null;
  var batchMode = false;
  var maxSources = 8;
  var isLocalServer = (location.protocol === "http:" || location.protocol === "https:") &&
    (location.hostname === "127.0.0.1" || location.hostname === "localhost" ||
     location.hostname === "[::1]" || location.port === "8765");
  var liveProgress = null;
  var liveTimer = null;
  var liveToken = 0;
  var PROOF_CASES = {
    fake: { key: "struck", label: "Fabricated quote · adversarial fixture" },
    real: { key: "eiffel", label: "Real model mistake · wrong side" }
  };
  var JUDGE_STEPS = [
    { label: "Trap", run: function () { showProof("fake"); } },
    { label: "Real model mistake", run: function () { showProof("real"); } },
    { label: "Accepted quote", run: function () { fill(EXAMPLES[1]); scrollToResult(); } },
    { label: "Four-source conflict", run: function () { loadBatchExample(); scrollToResult(); } },
    { label: "Receipt", run: function () {
      showProof("fake");
      scrollToReceipt();
    } }
  ];
  var judgeStepIndex = -1;
  var DEMO_ALIASES = {
    fake: "struck", struck: "struck",
    real: "eiffel", eiffel: "eiffel",
    flu: "flu", coffee: "coffee", population: "population"
  };
  var queryDemo = null;
  var queryJudge = false;
  try {
    var params = new URLSearchParams(location.search);
    queryDemo = params.get("demo");
    queryJudge = params.get("judge") === "1";
  } catch (e) {
    queryDemo = null;
    queryJudge = false;
  }

  function isRecording(d) {
    return d && d.replay_mode === "live-run-recording";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function receiptMarkdown(d) {
    var lines = ["# Claim Autopsy — citation receipt", ""];
    lines.push("- Run: `" + ((d.receipt || {}).run_id || "") + "`");
    lines.push("- Generated: " + ((d.receipt || {}).generated_at || ""));
    lines.push("- Engine: " + ((d.receipt || {}).engine || ""));
    lines.push("- Model: " + ((d.receipt || {}).model || "none"));
    lines.push("- Claim: " + ((d.input || {}).claim || ""));
    lines.push("- Source hash: `" + ((d.input || {}).source_sha256 || "") + "`");
    lines.push("");
    (d.atoms || []).forEach(function (a) {
      lines.push("## " + a.atom_id + " — " + a.verdict.toUpperCase());
      lines.push(a.claim);
      lines.push("");
      lines.push("Judge: " + a.reason);
      (d.arguments || []).filter(function (x) { return x.atom_id === a.atom_id; }).forEach(function (x) {
        lines.push("- " + x.status.toUpperCase() + " · " + (x.origin === "ai" ? "AI" : "RULE") + " · " +
          x.side + " · " + x.evidence_id + " · chars " + x.char_start + "–" + x.char_end);
        lines.push("  > " + x.quote);
        if (x.strike_reason) lines.push("  Strike: " + x.strike_reason);
      });
      lines.push("");
    });
    lines.push("---");
    lines.push(d.disclaimer || "");
    return lines.join("\n");
  }

  function receiptMarkdownMulti(p) {
    var lines = ["# Claim Autopsy — multi-source receipt", ""];
    lines.push("- Claim: " + ((p.input || {}).claim || ""));
    lines.push("- Run: `" + ((p.receipt || {}).run_id || "") + "`");
    lines.push("- Model: " + ((p.receipt || {}).model || "none"));
    lines.push("- Sources: " + ((p.summary || {}).sources || 0));
    lines.push("");
    (p.rows || []).forEach(function (r) {
      lines.push("## " + r.name + " — " + String(r.verdict || "").toUpperCase());
      lines.push("- Source id: `" + r.source_id + "` · SHA-256 `" + r.sha256 + "`");
      if (r.quote) {
        lines.push("- Accepted quote: `" + r.quote.quote + "` · chars " +
          r.quote.char_start + "–" + r.quote.char_end + " · " + String(r.quote.origin || "").toUpperCase());
        if (r.quote.bridge) {
          var pairs = (r.quote.bridge.anchors || []).map(function (x) { return x[0] + " → " + x[1]; }).join(", ");
          lines.push("- AI bridge: " + pairs);
        }
      } else {
        lines.push("- No accepted quotation.");
      }
      lines.push("");
    });
    if ((p.summary || {}).cross_source_conflict) {
      lines.push("**Cross-source conflict:** at least one source supports and one refutes the claim. "
        + "This receipt does not pick a winner.");
      lines.push("");
    }
    lines.push("---");
    lines.push(p.disclaimer || "");
    return lines.join("\n");
  }

  function download(name, text, type) {
    var blob = new Blob([text], { type: type });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function bindExports(root, d, multi) {
    var jsonBtn = root.querySelector("#courtCopyJson");
    var mdBtn = root.querySelector("#courtDownloadMd");
    if (jsonBtn) jsonBtn.addEventListener("click", function () {
      var text = JSON.stringify(d, null, 2);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          jsonBtn.textContent = "Copied";
          setTimeout(function () { jsonBtn.textContent = "Copy JSON receipt"; }, 1200);
        }).catch(function () { download("claim-autopsy-receipt.json", text, "application/json"); });
      } else {
        download("claim-autopsy-receipt.json", text, "application/json");
      }
    });
    if (mdBtn) mdBtn.addEventListener("click", function () {
      download(multi ? "claim-autopsy-multi-receipt.md" : "claim-autopsy-receipt.md",
        multi ? receiptMarkdownMulti(d) : receiptMarkdown(d),
        "text/markdown");
    });
  }

  function bindSourceFile() {
    var input = document.getElementById("courtSourceFile");
    var note = document.getElementById("courtFileName");
    var area = document.getElementById("courtSource");
    if (!input || !note || !area) return;
    function show(name, text) {
      area.value = text;
      note.textContent = name + " · " + text.length.toLocaleString() + " chars" +
        (text.length > 20000 ? " · over the 20,000 limit" : "");
    }
    function read(file) {
      if (!file) return;
      if (file.size > 4 * 1024 * 1024) {
        note.textContent = "File is too large; paste the relevant passage instead.";
        return;
      }
      var reader = new FileReader();
      reader.onload = function () { show(file.name, String(reader.result || "").trim()); };
      reader.onerror = function () { note.textContent = "Could not read that file; paste the passage instead."; };
      reader.readAsText(file);
    }
    input.addEventListener("change", function () { read(input.files && input.files[0]); });
    area.addEventListener("dragover", function (e) { e.preventDefault(); });
    area.addEventListener("drop", function (e) {
      if (!e.dataTransfer || !e.dataTransfer.files || !e.dataTransfer.files.length) return;
      e.preventDefault();
      read(e.dataTransfer.files[0]);
    });
  }

  window.COURT_RECEIPT = function () {
    if (currentMulti) return receiptMarkdownMulti(currentMulti);
    return currentDossier ? receiptMarkdown(currentDossier) : "";
  };

  function badge(d) {
    var el = document.getElementById("courtModeBadge");
    if (!el) return;
    if (d.ai_mode === "ai" && d.receipt && d.receipt.model === "adversarial fixture") {
      el.className = "court-badge replay";
      el.textContent = "ADVERSARIAL FIXTURE";
    } else if (isRecording(d)) {
      el.className = "court-badge recorded";
      el.textContent = "RECORDED LIVE AI RUN · JUDGE VERIFIED";
    } else if (d.ai_mode === "ai" && d.receipt && d.receipt.model) {
      el.className = "court-badge live";
      el.textContent = "LIVE AI · JUDGE VERIFIED";
    } else {
      el.className = "court-badge replay";
      el.textContent = isLocalServer ? "RULES-ONLY DOCKET" : "RECORDED · RULES-ONLY";
    }
  }

  function argHtml(a) {
    var status = a.status === "accepted" ? "accepted" : "struck";
    var reason = a.strike_reason ? '<div class="strike">STRUCK: ' + esc(a.strike_reason) + "</div>" : "";
    var start = (a.char_start === null || a.char_start === undefined) ? "?" : a.char_start;
    var end = (a.char_end === null || a.char_end === undefined) ? "?" : a.char_end;
    return '<div class="court-arg ' + status + '">' +
      '<div class="ah"><span class="ast ' + status + '">' + status.toUpperCase() + "</span>" +
      '<span class="aid">' + (a.origin === "ai" ? "AI · " : "RULE · ") + esc(a.evidence_id) + " · chars " + start + "–" + end + "</span></div>" +
      "<blockquote>" + esc(a.quote) + "</blockquote>" +
      (a.rationale ? '<div class="ar">' + esc(a.rationale) + "</div>" : "") +
      '<div class="am">' + esc(a.relation || "") + " · " + Math.round((a.coverage || 0) * 100) + "% coverage</div>" +
      reason + "</div>";
  }

  function aiStrip(d) {
    if (d.ai_mode !== "ai") {
      return '<div class="ai-strip rules"><b>RULES-ONLY DOCKET</b><span>No model called. The same deterministic judge decides.</span></div>';
    }
    var meta = (d.trace && d.trace[0] && d.trace[0].meta) || {};
    var p = meta.prosecution || {};
    var f = meta.defense || {};
    var latency = Math.max(p.latency_ms || 0, f.latency_ms || 0);
    var model = (d.receipt && d.receipt.model) || p.model || "local model";
    if (model === "adversarial fixture") {
      return '<div class="ai-strip rules"><b>ADVERSARIAL FIXTURE</b> <span>No model run. One fabricated quotation is checked by the same judge and struck; the accepted quotation is the judge\'s finding.</span></div>';
    }
    var label = isRecording(d) ? "RECORDED LIVE AI RUN" : "LIVE AI ADVOCATES";
    var tail = isRecording(d) ? " Re-run it with <code>python serve.py</code>; this static page is a recording." : "";
    var aiN = (d.summary && d.summary.ai_arguments) || 0;
    var aiOk = (d.summary && d.summary.ai_accepted) || 0;
    var aiStruck = (d.summary && d.summary.ai_struck) || 0;
    var ruleN = (d.summary && d.summary.rule_arguments) || 0;
    var verdict = aiN ? ("AI proposed " + aiN + "; judge accepted " + aiOk + ", struck " + aiStruck +
      (ruleN ? ". Rules added " + ruleN + " more." : ".")) :
      "AI returned no usable argument; the rules-only docket still produced a verdict.";
    return '<div class="ai-strip ' + (isRecording(d) ? "recorded" : "live") + '"><b>' + label + '</b> <span>' +
      esc(model) + " · " + (latency ? (latency / 1000).toFixed(1) + "s · " : "") +
      esc(verdict) + tail + "</span></div>";
  }

  function colHtml(title, side, args) {
    return '<div class="court-col"><h4><span><span class="side-dot ' + side + '"></span> ' +
      title + "</span><span>" + args.length + "</span></h4>" +
      (args.length ? args.map(argHtml).join("") : '<div class="court-empty">No usable argument on this side.</div>') +
      "</div>";
  }

  function trapBanner(d) {
    var struck = (d.arguments || []).filter(function (a) {
      return a.status === "struck" && (a.strike_codes || []).length;
    })[0];
    if (!struck) return "";
    var accepted = (d.arguments || []).filter(function (a) {
      return a.status === "accepted";
    })[0];
    var atom = (d.atoms || [])[0] || {};
    var sourceQuote = accepted ? accepted.quote :
      (atom.nearest && atom.nearest.quote) || "No accepted quotation.";
    var code = (struck.strike_codes || []).join(", ");
    var reason = struck.strike_reason || "quotation cannot be verified";
    var verdict = String(atom.verdict || "undetermined").replace(/_/g, " ");
    var fixture = d.receipt && d.receipt.model === "adversarial fixture";
    return '<div class="court-proof-verdict" id="courtProofVerdict">' +
      '<h4>' + (fixture ? "Adversarial trap · one fabricated quotation" : "Judge strike · what the model got wrong") + '</h4>' +
      '<div class="pv-row bad"><span class="pv-label">AI proposed</span><div><q>' + esc(struck.quote) +
      '</q><span class="pv-code">' + esc(code) + '</span></div></div>' +
      '<div class="pv-row good"><span class="pv-label">Source says</span><div><q>' + esc(sourceQuote) + '</q></div></div>' +
      '<div class="pv-row"><span class="pv-label">Judge</span><div class="pv-verdict"><b>' + esc(verdict) +
      '</b> — ' + esc(reason) + '. The strike does not change the verdict; the source does.</div></div>' +
      '</div>';
  }

  function render(d, key) {
    var root = document.getElementById("courtResult");
    var err = document.getElementById("courtError");
    if (err) { err.style.display = "none"; err.textContent = ""; }
    if (!d || d.error) {
      if (err) {
        err.style.display = "block";
        err.textContent = "The court could not read this input: " + (d && d.error ? d.error : "unknown error");
      }
      return;
    }
    var s = d.summary || {};
    currentDossier = d;
    currentMulti = null;
    var summary = '<div class="court-summary">' +
      '<div class="court-stat"><b>' + (s.claims || 0) + "</b><span>atoms</span></div>" +
      '<div class="court-stat"><b>' + (s.supported || 0) + "</b><span>supported</span></div>" +
      '<div class="court-stat"><b>' + (s.refuted || 0) + "</b><span>refuted</span></div>" +
      '<div class="court-stat"><b>' + (s.not_in_source || 0) + "</b><span>not in source</span></div>" +
      '<div class="court-stat"><b>' + (s.struck_arguments || 0) + "</b><span>struck</span></div>" +
      "</div>";

    var atoms = (d.atoms || []).map(function (atom) {
      var args = (d.arguments || []).filter(function (a) { return a.atom_id === atom.atom_id; });
      var pro = args.filter(function (a) { return a.side === "prosecution"; });
      var def = args.filter(function (a) { return a.side === "defense"; });
      var accepted = args.filter(function (a) { return a.status === "accepted"; });
      var quote = accepted.length ? '<div class="rq">“' + esc(accepted[0].quote) + "”<br><span class=\"am\">" +
        esc(accepted[0].evidence_id) + " · chars " + accepted[0].char_start + "–" + accepted[0].char_end + "</span></div>" : "";
      var near = atom.nearest ? '<div class="near">Nearest sentence: “' + esc(atom.nearest.quote) +
        "” · " + Math.round((atom.nearest.coverage || 0) * 100) + "% coverage</div>" : "";
      return '<div class="court-atom">' +
        '<div class="court-atom-head"><span class="vbadge ' + esc(atom.verdict) + '">' + esc(atom.verdict).replace(/_/g, " ") + "</span>" +
        '<div><p class="ct">' + esc(atom.claim) + '</p><p class="cr">' + esc(atom.reason) + "</p></div></div>" +
        '<div class="court-cols">' +
        colHtml("Prosecution", "prosecution", pro) +
        colHtml("Defence", "defense", def) +
        '<div class="court-col"><h4><span><span class="side-dot judge"></span> Judge’s ruling</span></h4>' +
        '<div class="court-rule">' + esc(atom.reason) + quote +
        '<div class="wc"><b>What would change it:</b> ' + esc(atom.what_would_change_it) + "</div>" + near + "</div></div>" +
        "</div></div>";
    }).join("");

    var accepted = (d.arguments || []).filter(function (a) { return a.status === "accepted"; });
    var src = d.input ? d.input.source_name : "source";
    var sourceText = d.__source || "";
    var marked = sourceText;
    if (accepted.length && sourceText) {
      var q = accepted[0].quote;
      var i = sourceText.indexOf(q);
      if (i >= 0) {
        marked = esc(sourceText.slice(0, i)) + "<mark>" + esc(q) + "</mark>" + esc(sourceText.slice(i + q.length));
      } else {
        marked = esc(sourceText);
      }
    } else {
      marked = esc(sourceText);
    }

    root.innerHTML = trapBanner(d) + summary + aiStrip(d) + atoms +
      '<div class="court-source"><h4>Source · exact span highlighted</h4><p>' + (marked || esc("(source not shown in replay)")) + "</p></div>" +
      '<div class="court-foot"><span>receipt ' + esc((d.receipt || {}).run_id || "") + " · " +
      esc((d.receipt || {}).engine || "") + (d.receipt && d.receipt.model ? " · model " + esc(d.receipt.model) : "") +
      "</span><span>every accepted argument has an exact quotation</span></div>" +
      '<div class="court-actions"><button type="button" id="courtCopyJson">Copy JSON receipt</button>' +
      '<button type="button" id="courtDownloadMd">Download Markdown receipt</button></div>' +
      '<div class="court-disclaimer">' + esc(d.disclaimer || "") + "</div>";
    root.style.display = "block";
    bindExports(root, d, false);
    badge(d);
    var st = document.getElementById("courtStatus");
    if (st) st.textContent = d.demo_label || (d.ai_mode === "ai" ? "Live AI advocates · deterministic judge" : "Rules-only docket · no model called");
  }

  function sourceRow(name, text) {
    var rows = document.getElementById("courtSourceRows");
    if (!rows) return;
    var count = rows.querySelectorAll(".court-source-row").length;
    if (count >= maxSources) return;
    var n = count + 1;
    var row = document.createElement("div");
    row.className = "court-source-row";
    row.innerHTML = '<div class="court-source-row-head"><input class="src-name" maxlength="60" ' +
      'placeholder="Source name" value="' + esc(name || ("Source " + n)) + '">' +
      '<button type="button" class="src-remove">Remove</button></div>' +
      '<textarea class="src-text" placeholder="Paste this candidate source. Up to 20,000 characters."></textarea>';
    row.querySelector(".src-text").value = text || "";
    row.querySelector(".src-remove").addEventListener("click", function () {
      row.remove();
      renumberSources();
    });
    rows.appendChild(row);
    renumberSources();
  }

  function renumberSources() {
    var rows = document.getElementById("courtSourceRows");
    if (!rows) return;
    var list = rows.querySelectorAll(".court-source-row");
    for (var i = 0; i < list.length; i++) {
      var input = list[i].querySelector(".src-name");
      if (input && !input.value.trim()) input.value = "Source " + (i + 1);
    }
    var add = document.getElementById("courtAddSource");
    if (add) add.disabled = list.length >= maxSources;
  }

  function collectSources() {
    var rows = document.getElementById("courtSourceRows");
    var out = [];
    if (!rows) return out;
    var list = rows.querySelectorAll(".court-source-row");
    for (var i = 0; i < list.length; i++) {
      var text = list[i].querySelector(".src-text").value.trim();
      if (!text) continue;
      var name = list[i].querySelector(".src-name").value.trim() || ("Source " + (i + 1));
      out.push({ name: name, text: text });
    }
    return out;
  }

  function loadBatchExample() {
    var claim = "Getting a flu vaccine gives you the flu.";
    var replay = window.COURT_BATCH_REPLAY && window.COURT_BATCH_REPLAY.cases;
    var p = replay && replay[claim];
    setMode(true);
    document.getElementById("courtClaim").value = claim;
    var rows = document.getElementById("courtSourceRows");
    if (rows) rows.innerHTML = "";
    var sources = (p && p.replay_sources) || [];
    sources.forEach(function (s) { sourceRow(s.name, s.text); });
    if (p) renderMulti(p);
  }

  function setMode(multi) {
    batchMode = !!multi;
    if (batchMode) hideProgress();
    var single = document.getElementById("singleSourcePane");
    var pane = document.getElementById("multiSourcePane");
    var singleBtn = document.getElementById("courtModeSingle");
    var multiBtn = document.getElementById("courtModeMulti");
    var run = document.getElementById("courtRun");
    var st = document.getElementById("courtStatus");
    if (single) single.style.display = batchMode ? "none" : "block";
    if (pane) pane.style.display = batchMode ? "block" : "none";
    if (singleBtn) singleBtn.className = batchMode ? "" : "active";
    if (multiBtn) multiBtn.className = batchMode ? "active" : "";
    if (run) run.textContent = batchMode ? "Audit all sources →" : "Open the trial →";
    if (st) st.textContent = batchMode
      ? "One claim against up to 8 sources · rules triage first, AI only on unsettled sources"
      : (isLocalServer ? "Live judge · local AI advocates" : "Static demo · recorded rules-only dossier");
    if (batchMode && document.getElementById("courtSourceRows") &&
        !document.getElementById("courtSourceRows").children.length) {
      sourceRow("Source 1", "");
      sourceRow("Source 2", "");
    }
  }

  function renderMulti(p) {
    hideProgress();
    var root = document.getElementById("courtResult");
    var err = document.getElementById("courtError");
    if (err) { err.style.display = "none"; err.textContent = ""; }
    if (!p || p.error) {
      if (err) {
        err.style.display = "block";
        err.textContent = "The batch court could not run: " + (p && p.error ? p.error : "unknown error");
      }
      return;
    }
    currentMulti = p;
    currentDossier = null;
    var s = p.summary || {};
    var summary = '<div class="court-batch-summary">' +
      '<div class="court-stat"><b>' + (s.sources || 0) + "</b><span>sources</span></div>" +
      '<div class="court-stat"><b>' + (s.supported || 0) + "</b><span>supported</span></div>" +
      '<div class="court-stat"><b>' + (s.refuted || 0) + "</b><span>refuted</span></div>" +
      '<div class="court-stat"><b>' + (s.not_in_source || 0) + "</b><span>not in source</span></div>" +
      '<div class="court-stat"><b>' + (s.ai_used || 0) + "</b><span>AI sources</span></div></div>";
    var conflict = s.cross_source_conflict
      ? '<div class="court-conflict"><b>Cross-source conflict.</b> At least one supplied source supports and one refutes the claim. ' +
        'The court reports the split; it does not decide which source is right.</div>' : "";
    var rows = (p.rows || []).map(function (r) {
      var q = r.quote;
      var quote = q ? '<div class="court-batch-quote">“' + esc(q.quote) + "”<br>" +
        '<span class="court-batch-meta">' + esc(q.evidence_id) + " · chars " + q.char_start + "–" + q.char_end +
        " · " + (q.origin === "ai" ? "AI ACCEPTED" : "RULE ACCEPTED") + "</span>" +
        (q.bridge ? '<br><span class="court-batch-meta">AI bridge: ' +
          esc((q.bridge.anchors || []).map(function (x) { return x[0] + " → " + x[1]; }).join(", ")) +
          "</span>" : "") + "</div>" :
        '<div class="court-batch-quote">No accepted quotation in this source.</div>';
      var near = (!q && r.dossier && r.dossier.atoms && r.dossier.atoms[0] && r.dossier.atoms[0].nearest)
        ? '<div class="court-batch-meta">Nearest sentence: “' + esc(r.dossier.atoms[0].nearest.quote) + "” · " +
          Math.round((r.dossier.atoms[0].nearest.coverage || 0) * 100) + "% coverage</div>" : "";
      return '<div class="court-batch-row"><div class="court-batch-head">' +
        '<span class="vbadge ' + esc(r.verdict) + '">' + esc(r.verdict).replace(/_/g, " ") + "</span>" +
        "<h4>" + esc(r.name) + "</h4>" +
        '<span class="court-batch-meta">' + r.source_id + " · " + (r.mode === "ai" ? "AI + JUDGE" : "RULES") +
        " · " + (r.sha256 || "").slice(0, 12) + "…" + "</span></div>" + quote + near + "</div>";
    }).join("");
    var ai = s.ai_used
      ? '<div class="ai-strip live"><b>TARGETED LIVE AI</b> <span>' + s.ai_used + " of " + s.sources +
        " sources received AI advocates · " + Math.round((s.total_ai_ms || 0) / 100) / 10 + "s · " +
        esc((p.receipt || {}).model || "local model") + " · every quote still verified by the judge.</span></div>"
      : '<div class="ai-strip rules"><b>RULES TRIAGE ONLY</b><span>Every source had a rule-side quotation or was left not in source. No model call was needed.</span></div>';
    root.innerHTML = summary + conflict + ai + rows +
      '<div class="court-foot"><span>receipt ' + esc((p.receipt || {}).run_id || "") + " · multi-source · " +
      esc((p.receipt || {}).engine || "") + "</span><span>one claim × " + s.sources + " sources</span></div>" +
      '<div class="court-actions"><button type="button" id="courtCopyJson">Copy JSON receipt</button>' +
      '<button type="button" id="courtDownloadMd">Download Markdown receipt</button></div>' +
      '<div class="court-disclaimer">' + esc(p.disclaimer || "") + "</div>";
    root.style.display = "block";
    bindExports(root, p, true);
    var el = document.getElementById("courtModeBadge");
    if (el) {
      el.className = "court-badge replay";
      el.textContent = "MULTI-SOURCE · " + s.sources + " SOURCES";
    }
    var st = document.getElementById("courtStatus");
    if (st) st.textContent = "Audited " + s.sources + " sources · " + (s.cross_source_conflict ? "cross-source conflict" : "no cross-source conflict");
  }

  function runBatch() {
    var claim = document.getElementById("courtClaim").value.trim();
    var sources = collectSources();
    var st = document.getElementById("courtStatus");
    var err = document.getElementById("courtError");
    if (!claim || !sources.length) {
      if (err) {
        err.style.display = "block";
        err.textContent = "Paste a claim and at least one candidate source.";
      }
      return;
    }
    if (sources.length > maxSources) {
      if (err) { err.style.display = "block"; err.textContent = "The batch court accepts up to 8 sources."; }
      return;
    }
    for (var i = 0; i < sources.length; i++) {
      if (sources[i].text.length > 20000) {
        if (err) {
          err.style.display = "block";
          err.textContent = sources[i].name + " is over the 20,000 character limit.";
        }
        return;
      }
    }
    if (!isLocalServer) {
      var replay = window.COURT_BATCH_REPLAY;
      if (replay && replay.cases && replay.cases[claim]) {
        renderMulti(replay.cases[claim]);
      } else {
        if (err) {
          err.style.display = "block";
          err.textContent = "The static page replays one recorded batch. Run `python serve.py` to audit your own sources.";
        }
      }
      return;
    }
    if (st) st.textContent = "Rules triage on " + sources.length + " sources; AI only on unsettled ones…";
    fetch("/api/trial_multi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: claim, sources: sources, live: true, ai_limit: 3 })
    }).then(function (r) { return r.json(); }).then(function (p) {
      if (p && p.error) {
        if (err) { err.style.display = "block"; err.textContent = "Batch court error: " + p.error; }
        renderMulti(p);
      } else {
        renderMulti(p);
      }
    }).catch(function () {
      if (st) st.textContent = "Server unreachable; batch auditing needs `python serve.py`.";
    });
  }

  function fill(example, renderNow) {
    hideProgress();
    setMode(false);
    var d = (window.COURT_REPLAY && window.COURT_REPLAY.cases || {})[example.key];
    if (!d) return;
    document.getElementById("courtClaim").value = d.input.claim;
    document.getElementById("courtSource").value = d.__source || "";
    var note = document.getElementById("courtFileName");
    if (note) note.textContent = "or paste the source above · 20,000 character limit";
    if (renderNow !== false) render(d, example.key);
    activeKey = example.key;
  }

  function localExample(claim, source) {
    var cases = (window.COURT_REPLAY && window.COURT_REPLAY.cases) || {};
    for (var k in cases) {
      if (!Object.prototype.hasOwnProperty.call(cases, k)) continue;
      var d = cases[k];
      if (d.input && d.input.claim === claim && d.__source === source) return d;
    }
    return null;
  }

  var PROGRESS_PHASES = [
    { key: "rules", title: "Rules triage", detail: "Splitting the claim and checking negation, scope and numbers.", width: 12 },
    { key: "evidence", title: "Evidence packet", detail: "Hashing the source and indexing candidate sentences.", width: 28 },
    { key: "ai", title: "AI advocates", detail: "The local model drafts grounded arguments for both sides.", width: 58 },
    { key: "judge", title: "Judge verifies", detail: "Every quote is checked character by character; the model never writes the verdict.", width: 88 }
  ];

  function nowMs() {
    return (window.performance && performance.now) ? performance.now() : Date.now();
  }

  function elapsedSeconds() {
    if (!liveProgress) return 0;
    return Math.max(0, (nowMs() - liveProgress.started) / 1000);
  }

  function setRunning(running) {
    var run = document.getElementById("courtRun");
    if (run) run.disabled = !!running;
  }

  function setProgressElapsed(seconds) {
    var el = document.getElementById("cpElapsed");
    if (!el) return;
    var value = typeof seconds === "number" && isFinite(seconds) ? seconds : elapsedSeconds();
    el.textContent = value.toFixed(1) + "s";
  }

  function beginProgress() {
    var box = document.getElementById("courtProgress");
    liveToken += 1;
    liveProgress = { token: liveToken, started: nowMs(), running: true, phase: "rules", skipped: {} };
    if (box) {
      box.style.display = "block";
      box.className = "court-progress";
      box.setAttribute("data-running", "1");
      box.setAttribute("data-phase", "rules");
    }
    ["rules", "evidence", "ai", "judge"].forEach(function (key) {
      var step = document.getElementById("cpStep-" + key);
      if (step) step.className = "cp-step";
    });
    var title = document.getElementById("cpTitle");
    if (title) title.textContent = "Running the court…";
    var note = document.getElementById("cpNote");
    if (note) note.textContent = "Deterministic checks run first. AI is only asked for grounded bridges; the judge still owns the verdict.";
    var fill = document.getElementById("cpFill");
    if (fill) fill.style.width = "8%";
    setProgressElapsed(0);
    setRunning(true);
    setProgressPhase("rules", {});
    if (liveTimer) clearInterval(liveTimer);
    var token = liveToken;
    liveTimer = setInterval(function () {
      if (!liveProgress || liveProgress.token !== token) return;
      setProgressElapsed();
    }, 100);
    return liveProgress;
  }

  function setProgressPhase(phase, event) {
    if (!liveProgress || !event) return;
    var order = PROGRESS_PHASES.map(function (p) { return p.key; }).indexOf(phase);
    if (order < 0) return;
    liveProgress.phase = phase;
    if (event.status === "skipped") liveProgress.skipped[phase] = true;
    var box = document.getElementById("courtProgress");
    if (box) {
      box.className = "court-progress" + (phase === "ai" ? " ai" : "");
      box.setAttribute("data-phase", phase);
    }
    ["rules", "evidence", "ai", "judge"].forEach(function (key, i) {
      var step = document.getElementById("cpStep-" + key);
      if (!step) return;
      if (i < order) {
        step.className = "cp-step " + (liveProgress.skipped[key] ? "skipped" : "done");
      } else if (i === order) {
        step.className = "cp-step " + (event.status === "skipped" ? "skipped" : "active");
      } else if (liveProgress.skipped[key]) {
        step.className = "cp-step skipped";
      } else {
        step.className = "cp-step";
      }
    });
    var meta = PROGRESS_PHASES[order];
    var title = document.getElementById("cpTitle");
    if (title) title.textContent = event.status === "skipped" ? "AI unavailable · rules-only docket" : meta.title;
    var note = document.getElementById("cpNote");
    if (note) note.textContent = event.detail || meta.detail;
    var fill = document.getElementById("cpFill");
    if (fill && typeof meta.width === "number") fill.style.width = meta.width + "%";
    setProgressElapsed(typeof event.elapsed === "number" ? event.elapsed : elapsedSeconds());
  }

  function finishProgress(d) {
    if (!liveProgress) return;
    liveProgress.running = false;
    if (liveTimer) clearInterval(liveTimer);
    liveTimer = null;
    var failed = !!(d && d.error);
    var box = document.getElementById("courtProgress");
    if (box) {
      box.className = "court-progress " + (failed ? "failed" : "done");
      box.setAttribute("data-running", "0");
    }
    ["rules", "evidence", "ai", "judge"].forEach(function (key) {
      var step = document.getElementById("cpStep-" + key);
      if (step) step.className = "cp-step " + (liveProgress.skipped[key] ? "skipped" : "done");
    });
    var title = document.getElementById("cpTitle");
    var note = document.getElementById("cpNote");
    var fill = document.getElementById("cpFill");
    if (failed) {
      if (title) title.textContent = "Court could not finish";
      if (note) note.textContent = "The judge rejected the input before a docket was written. Nothing was guessed.";
    } else {
      var s = (d && d.summary) || {};
      var bridges = s.ai_bridges || 0;
      if (title) title.textContent = "Judge verified";
      if (note) {
        note.textContent = "Accepted " + (s.accepted_arguments || 0) + " · struck " + (s.struck_arguments || 0) +
          (bridges ? " · " + bridges + " semantic bridge" + (bridges === 1 ? "" : "s") : "") +
          ". The model argued; the judge decided.";
      }
      if (fill) fill.style.width = "100%";
    }
    setProgressElapsed(elapsedSeconds());
    setRunning(false);
  }

  function hideProgress() {
    if (liveTimer) clearInterval(liveTimer);
    liveTimer = null;
    liveProgress = null;
    var box = document.getElementById("courtProgress");
    if (box) {
      box.style.display = "none";
      box.setAttribute("data-running", "0");
    }
    setRunning(false);
  }

  function consumeStreamLine(line, state) {
    if (!line || !line.trim()) return;
    var event;
    try {
      event = JSON.parse(line);
    } catch (err) {
      return;
    }
    if (!event || !event.type) return;
    if (event.type === "phase") {
      setProgressPhase(event.phase, event);
    } else if (event.type === "tick") {
      setProgressElapsed(event.elapsed);
    } else if (event.type === "result") {
      state.payload = event.payload;
    } else if (event.type === "error") {
      state.payload = { error: event.error || "trial_failed" };
    }
  }

  function streamTrial(claim, source) {
    if (!window.fetch || !window.TextDecoder) return Promise.reject(new Error("stream_unavailable"));
    return fetch("/api/trial_stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: claim, source: source, live: true })
    }).then(function (response) {
      if (!response.ok || !response.body || !response.body.getReader) {
        throw new Error("stream_unavailable");
      }
      var reader = response.body.getReader();
      var decoder = new TextDecoder("utf-8");
      var buffer = "";
      var state = { payload: null };
      function pump() {
        return reader.read().then(function (chunk) {
          if (chunk.done) {
            if (buffer) consumeStreamLine(buffer, state);
            if (state.payload) return state.payload;
            throw new Error("stream_without_result");
          }
          buffer += decoder.decode(chunk.value, { stream: true });
          var parts = buffer.split("\n");
          buffer = parts.pop();
          parts.forEach(function (line) { consumeStreamLine(line, state); });
          return pump();
        });
      }
      return pump();
    });
  }

  function plainTrial(claim, source, force) {
    return fetch("/api/trial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: claim, source: source, live: !!force })
    }).then(function (r) { return r.json(); });
  }

  window.COURT_PROGRESS = function () {
    if (!liveProgress) return null;
    return {
      phase: liveProgress.phase,
      running: liveProgress.running,
      elapsed: elapsedSeconds(),
      skipped: Object.keys(liveProgress.skipped)
    };
  };

  function runLive(force) {
    if (batchMode) { runBatch(); return; }
    if (liveProgress && liveProgress.running) return;
    var claim = document.getElementById("courtClaim").value.trim();
    var source = document.getElementById("courtSource").value.trim();
    var st = document.getElementById("courtStatus");
    if (!claim || !source) {
      var err = document.getElementById("courtError");
      err.style.display = "block";
      err.textContent = "Paste both a claim and the source you want to check.";
      return;
    }
    if (source.length > 20000) {
      var err2 = document.getElementById("courtError");
      err2.style.display = "block";
      err2.textContent = "Source is " + source.length.toLocaleString() + " characters; the court accepts up to 20,000. Trim to the passage the claim cites.";
      return;
    }
    if (!isLocalServer) {
      var d = localExample(claim, source);
      if (d) { d.demo_label = "RECORDED DOSSIER · no model called"; render(d, activeKey); }
      else {
        var e = document.getElementById("courtError");
        e.style.display = "block";
        e.textContent = "This static page replays recorded dossiers. Run `python serve.py` for any claim and for live AI.";
      }
      return;
    }
    if (force) {
      beginProgress();
      var progressToken = liveProgress.token;
      streamTrial(claim, source).then(function (d) {
        if (!liveProgress || liveProgress.token !== progressToken) return;
        if (d && !d.error) d.__source = source;
        render(d, activeKey);
        finishProgress(d);
      }).catch(function () {
        if (!liveProgress || liveProgress.token !== progressToken) return;
        hideProgress();
        if (st) st.textContent = "Stream unavailable · falling back to the one-shot trial…";
        plainTrial(claim, source, force).then(function (d) {
          if (d && !d.error) d.__source = source;
          render(d, activeKey);
        }).catch(function () {
          if (st) st.textContent = "Server unreachable · showing a recorded dossier";
          var replay = localExample(claim, source);
          if (replay) render(replay, activeKey);
        });
      });
      return;
    }
    if (st) st.textContent = "Running the court…";
    plainTrial(claim, source, false).then(function (d) {
      if (d && !d.error) d.__source = source;
      render(d, activeKey);
    }).catch(function () {
      if (st) st.textContent = "Server unreachable · showing a recorded dossier";
      var replay = localExample(claim, source);
      if (replay) render(replay, activeKey);
    });
  }

  function showProof(kind) {
    var ex = PROOF_CASES[kind];
    if (!ex) return;
    fill(ex);
    var root = document.getElementById("courtResult");
    if (root) {
      setTimeout(function () {
        root.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    }
  }

  function scrollToResult() {
    setTimeout(function () {
      var root = document.getElementById("courtResult");
      if (root) root.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

  function scrollToReceipt() {
    setTimeout(function () {
      var actions = document.querySelector("#courtResult .court-actions");
      if (!actions) return;
      actions.scrollIntoView({ behavior: "smooth", block: "center" });
      actions.classList.add("receipt-pulse");
      setTimeout(function () { actions.classList.remove("receipt-pulse"); }, 1600);
    }, 140);
  }

  function markJudgeStep(i) {
    var buttons = document.querySelectorAll("[data-judge-step]");
    for (var n = 0; n < buttons.length; n++) {
      var idx = parseInt(buttons[n].getAttribute("data-judge-step"), 10);
      buttons[n].classList.toggle("active", idx === i);
      buttons[n].classList.toggle("done", idx < i);
    }
    var next = document.getElementById("courtJudgeNext");
    if (next) next.textContent = i >= JUDGE_STEPS.length - 1 ? "Restart ↺" : "Next →";
    var status = document.getElementById("courtStatus");
    if (status) {
      status.textContent = "Judge path " + (i + 1) + "/5 · " + JUDGE_STEPS[i].label;
    }
  }

  function judgeStep(i) {
    if (i < 0 || i >= JUDGE_STEPS.length) return;
    JUDGE_STEPS[i].run();
    judgeStepIndex = i;
    markJudgeStep(i);
  }

  function judgeNext() {
    judgeStep(judgeStepIndex >= JUDGE_STEPS.length - 1 ? 0 : judgeStepIndex + 1);
  }

  function init() {
    var chips = document.getElementById("courtExamples");
    if (chips) {
      EXAMPLES.forEach(function (ex) {
        var b = document.createElement("button");
        b.className = "court-chip";
        b.type = "button";
        b.textContent = ex.label;
        b.addEventListener("click", function () {
          fill(ex);
          if (isLocalServer) runLive(true);
        });
        chips.appendChild(b);
      });
    }
    var initial = EXAMPLES[0];
    if (queryDemo) {
      var wanted = DEMO_ALIASES[queryDemo] || queryDemo;
      var found = EXAMPLES.filter(function (ex) { return ex.key === wanted; })[0];
      if (found) initial = found;
    }
    if (queryJudge) {
      document.body.classList.add("court-judge-mode");
      var enter = document.getElementById("courtJudgeEnter");
      if (enter) {
        enter.textContent = "Full demo";
        enter.setAttribute("href", "?demo=struck");
      }
    } else if (queryDemo) {
      fill(initial, false);
      var proofStatus = document.getElementById("courtStatus");
      if (proofStatus) proofStatus.textContent = "Proof loaded · click Show the fabricated quote";
    } else {
      fill(initial);
    }
    bindSourceFile();
    var proofBtn = document.getElementById("courtProofRun");
    if (proofBtn) proofBtn.addEventListener("click", function () { showProof("fake"); });
    var proofReal = document.getElementById("courtProofReal");
    if (proofReal) proofReal.addEventListener("click", function () { showProof("real"); });
    var judgeButtons = document.querySelectorAll("[data-judge-step]");
    for (var jb = 0; jb < judgeButtons.length; jb++) {
      judgeButtons[jb].addEventListener("click", function () {
        judgeStep(parseInt(this.getAttribute("data-judge-step"), 10));
      });
    }
    var judgeNextBtn = document.getElementById("courtJudgeNext");
    if (judgeNextBtn) judgeNextBtn.addEventListener("click", judgeNext);
    var singleBtn = document.getElementById("courtModeSingle");
    var multiBtn = document.getElementById("courtModeMulti");
    if (singleBtn) singleBtn.addEventListener("click", function () { setMode(false); });
    if (multiBtn) multiBtn.addEventListener("click", function () { setMode(true); });
    var addBtn = document.getElementById("courtAddSource");
    if (addBtn) addBtn.addEventListener("click", function () { sourceRow("", ""); });
    var batchExample = document.getElementById("courtBatchExample");
    if (batchExample) batchExample.addEventListener("click", loadBatchExample);
    document.getElementById("courtRun").addEventListener("click", function () { runLive(true); });
    document.getElementById("showLegacy").addEventListener("click", function () {
      var legacy = document.getElementById("legacyAudit");
      var shell = document.getElementById("courtShell");
      var showing = legacy.style.display !== "none";
      legacy.style.display = showing ? "none" : "block";
      shell.style.display = showing ? "block" : "none";
      this.textContent = showing ? "Legacy audit" : "Back to court";
    });
    if (isLocalServer) {
      fetch("/api/status").then(function (r) { return r.json(); }).then(function (s) {
        if (s && s.ai_available) {
          document.getElementById("courtLive").style.display = "inline-block";
          if (queryDemo) {
            document.getElementById("courtStatus").textContent = "Recorded proof loaded · click Open the trial for live AI";
          } else {
            document.getElementById("courtStatus").textContent = "Local AI ready · running the first docket…";
            runLive(true);
          }
        } else {
          document.getElementById("courtStatus").textContent = "Server ready · rules-only (no local model or key)";
        }
      }).catch(function () {});
      document.getElementById("courtLive").addEventListener("click", function () {
        if (batchMode) runBatch(); else runLive(true);
      });
    }
    if (queryJudge) judgeStep(0);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
