"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";

  const STATE_LABELS = {
    idle: "Pregătire",
    checks: "Verificări GO/NO-GO",
    hold: "HOLD – așteptăm",
    ready: "Gata de lansare",
    countdown: "Numărătoare inversă",
    flight: "În zbor",
    orbit: "Pe orbită!",
    scrub: "Lansare anulată",
    abort: "ABORT",
    quiz: "Quiz",
    parts: "Piesele rachetei",
  };
  const PRE_LAUNCH = new Set(["idle", "checks", "hold", "ready", "scrub"]);
  // Aici ABORT apăsat scurt pornește/oprește vocea.
  const VOICE_TOGGLE = new Set(["idle", "orbit", "scrub", "abort"]);

  // Culorile cerului în funcție de altitudine (km): [alt, sus, jos]
  const SKY = [
    [0, [61, 143, 214], [169, 220, 255]],
    [10, [29, 79, 156], [94, 164, 224]],
    [30, [11, 31, 74], [42, 95, 165]],
    [60, [5, 10, 31], [15, 35, 80]],
    [100, [0, 0, 5], [5, 11, 30]],
  ];
  const PX_PER_KM = 80;
  const ROCKET_RISE = 150;
  const PAD_Y = 545;

  const params = new URLSearchParams(location.search);
  const showControls = params.has("control");
  // ?kiosk=1: afișare pe monitorul legat la Pi, fără cursor
  if (params.has("kiosk")) document.body.classList.add("kiosk");

  let mission = null;
  let snap = null;
  let prevFired = [];
  let prevState = null;
  let prevVoiceOn = null;
  const view = { alt: 0, t: 0 };
  let toastTimer = null;
  let build = null;

  // ---------- inițializare ----------
  function makeStars() {
    const g = $("stars");
    let seed = 7;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 160; i++) {
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", (-700 + rnd() * 2000).toFixed(1));
      c.setAttribute("cy", (-900 + rnd() * 1400).toFixed(1));
      c.setAttribute("r", (0.6 + rnd() * 1.6).toFixed(1));
      c.setAttribute("fill", "#fff");
      g.appendChild(c);
    }
  }

  function placeQuizCells() {
    // Răspunsurile stau în același colț ca butoanele de pe panou.
    const layout = mission.button_layout || {};
    for (const cell of document.querySelectorAll(".quiz-cell")) {
      if (layout[cell.dataset.btn]) cell.style.gridArea = layout[cell.dataset.btn];
    }
  }

  function buildLists() {
    $("mission-name").textContent = mission.name;
    $("checks").innerHTML = "";
    for (const name of mission.checks) {
      const li = document.createElement("li");
      li.innerHTML = '<span class="mark"></span><span class="name"></span>';
      li.querySelector(".name").textContent = name;
      $("checks").appendChild(li);
    }
    $("timeline").innerHTML = "";
    for (const ev of mission.events) {
      const li = document.createElement("li");
      li.dataset.key = ev.key;
      li.innerHTML = '<span class="mark"></span><span class="time"></span><span class="name"></span>';
      li.querySelector(".time").textContent = ev.clock;
      li.querySelector(".name").textContent = ev.title;
      $("timeline").appendChild(li);
    }
  }

  // ---------- panou ----------
  function fmtAlt(km) {
    return km < 100
      ? km.toLocaleString("ro-RO", { minimumFractionDigits: 1, maximumFractionDigits: 1 })
      : Math.round(km).toLocaleString("ro-RO");
  }

  function renderPanel(s) {
    $("clock").textContent = s.clock || "T-0:10";
    $("clock").style.visibility = s.clock ? "visible" : "hidden";
    const st = $("state");
    st.dataset.state = s.state;
    st.textContent = STATE_LABELS[s.state] || s.state;

    $("alt").textContent = fmtAlt(s.alt_km);
    $("vel").textContent = s.vel_kmh.toLocaleString("ro-RO");
    if (mission) {
      $("alt-bar").style.width = Math.min(100, (100 * s.alt_km) / mission.max_alt_km) + "%";
      $("vel-bar").style.width = Math.min(100, (100 * s.vel_kmh) / mission.max_vel_kmh) + "%";
    }

    $("info-title").textContent = s.info.title;
    $("info-text").textContent = s.info.text;
    // Unde ABORT schimbă vocea: cum se pornește/oprește; în rest, doar dacă e oprită.
    const note = $("voice-note");
    const canToggle = VOICE_TOGGLE.has(s.state);
    note.hidden = !canToggle && s.voice_on;
    note.textContent = !canToggle
      ? "🔇 Fără voce"
      : s.voice_on
        ? "🔊 Vocea citește explicațiile. Apăsați ABORT ca s-o opriți."
        : "🔇 Vocea e oprită. Apăsați ABORT ca s-o porniți.";
    $("lcd1").textContent = s.lcd[0];
    $("lcd2").textContent = s.lcd[1];

    const preLaunch = PRE_LAUNCH.has(s.state);
    $("checks").hidden = !preLaunch;
    $("timeline").hidden = preLaunch;

    [...$("checks").children].forEach((li, i) => {
      const status = s.checks[i];
      li.className = status === "go" ? "done" : status;
      li.querySelector(".mark").textContent =
        status === "go" ? "✓" : status === "hold" ? "!" : status === "current" ? "?" : "·";
    });
    const last = s.fired[s.fired.length - 1];
    [...$("timeline").children].forEach((li) => {
      const done = s.fired.includes(li.dataset.key);
      const current = li.dataset.key === last && s.state === "flight";
      // cu text mare, lista poate ieși din ecran: etapa curentă rămâne la vedere
      if (current && !li.classList.contains("current")) li.scrollIntoView({ block: "nearest" });
      li.className = current ? "current" : done ? "done" : "";
      li.querySelector(".mark").textContent = done ? "✓" : "·";
    });

    $("stage-banner").hidden = !s.awaiting_stage;
    $("ff-banner").hidden = !s.fast_forward || s.awaiting_stage;
    if (s.fast_forward) $("ff-banner").textContent = `⏩ Timp accelerat ×${s.fast_forward}`;
    $("controls").hidden = !(showControls && s.web_control);

    const big = $("big-count");
    big.hidden = s.state !== "countdown";
    if (s.state === "countdown") big.textContent = Math.max(1, Math.ceil(-s.t));
  }

  // ---------- quiz ----------
  const VERDICTS = { correct: "Corect! +1", wrong: "Greșit!", timeout: "Timpul a expirat!" };

  function renderQuiz(q) {
    $("quiz").hidden = !q;
    document.body.classList.toggle("quiz-on", !!q);
    if (!q) return;
    const playing = q.phase === "question" || q.phase === "feedback";

    const progress = $("quiz-progress");
    if (progress.children.length !== q.total) {
      progress.innerHTML = "";
      for (let i = 0; i < q.total; i++) progress.appendChild(document.createElement("li"));
    }
    [...progress.children].forEach((li, i) => {
      const result = q.results[i];
      const current = q.phase === "question" && i === q.index - 1;
      li.className = result === true ? "ok" : result === false ? "bad" : current ? "current" : "";
      li.textContent = result === true ? "✓" : result === false ? "✗" : i + 1;
    });
    $("quiz-score").textContent = q.score;
    $("quiz-count").textContent = playing ? `· întrebarea ${q.index} din ${q.total}` : "";

    const timer = $("quiz-timer");
    timer.hidden = q.phase !== "question";
    if (q.phase === "question") {
      $("quiz-timer-bar").style.width = (100 * q.time_left) / q.time_total + "%";
      $("quiz-timer-text").textContent = Math.ceil(q.time_left) + " s";
      timer.classList.toggle("urgent", q.time_left <= 5);
    }

    if (q.phase === "intro") {
      $("quiz-question").textContent = "Sunteți gata de lansare?";
      $("quiz-sub").textContent =
        `${q.total} întrebări, câte ${q.time_total} secunde fiecare. ` +
        "Apăsați butonul din colțul răspunsului corect.";
    } else if (q.phase === "result") {
      $("quiz-question").textContent = `Scor: ${q.score} din ${q.total}`;
      $("quiz-sub").textContent = `🏅 Gradul vostru: ${q.grade}`;
    } else {
      $("quiz-question").textContent = q.question;
      $("quiz-sub").textContent = "";
    }

    const feedback = $("quiz-feedback");
    feedback.hidden = q.phase !== "feedback";
    if (q.phase === "feedback") {
      feedback.dataset.outcome = q.outcome;
      $("quiz-verdict").textContent = VERDICTS[q.outcome];
      $("quiz-explanation").textContent = q.explanation;
    }

    for (const cell of document.querySelectorAll(".quiz-cell")) {
      const btn = cell.dataset.btn;
      let text = "";
      let cls = "";
      if (btn === "abort") {
        text = "Ieșire";
        cls = "exit";
      } else if (!playing) {
        text = btn === "go" ? (q.phase === "intro" ? "Începem!" : "Rundă nouă") : "";
        cls = btn === "go" ? "action" : "dim";
      } else {
        text = q.options[btn];
        if (q.phase === "feedback") {
          cls = btn === q.correct ? "correct" : btn === q.chosen ? "wrong" : "dim";
        }
      }
      cell.querySelector(".quiz-text").textContent = text;
      cell.className = "quiz-cell " + cls;
    }
    $("quiz-confirm").hidden = !q.confirm_exit;
  }

  // ---------- evenimente ----------
  function toast(text, kind = "") {
    const el = $("toast");
    el.textContent = text;
    el.className = "toast " + kind;
    el.hidden = false;
    // repornește animația de apariție
    void el.offsetWidth;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (el.hidden = true), 4000);
  }

  function resetRocket() {
    const rocket = $("rocket");
    rocket.classList.add("no-anim");
    ["booster", "les", "stack", "capsule"].forEach((id) => $(id).classList.remove("gone", "fall", "escape"));
    void rocket.getBoundingClientRect();
    requestAnimationFrame(() => rocket.classList.remove("no-anim"));
  }

  function handleChanges(s) {
    if (s.fired.length < prevFired.length || (s.state === "idle" && prevState !== "idle")) {
      resetRocket();
      view.alt = s.alt_km;
      view.t = 0;
    }
    if (mission) {
      for (const key of s.fired) {
        if (prevFired.includes(key)) continue;
        const ev = mission.events.find((e) => e.key === key);
        if (ev) toast(ev.title, key === "seco" ? "success" : "");
      }
    }
    $("booster").classList.toggle("gone", s.fired.includes("separation"));
    $("les").classList.toggle("gone", s.fired.includes("les"));

    if (s.state !== prevState) {
      if (s.state === "abort") {
        $("capsule").classList.add("escape");
        $("stack").classList.add("fall");
        toast("ABORT! Capsula se salvează", "danger");
      } else if (s.state === "hold") {
        toast("HOLD! " + s.info.title.replace("HOLD: ", ""), "danger");
      } else if (s.state === "scrub") {
        toast("Lansare anulată", "danger");
      } else if (s.state === "ready") {
        toast("Toate stațiile: GO!", "success");
      }
    }
    if (prevVoiceOn !== null && s.voice_on !== prevVoiceOn) {
      toast(s.voice_on ? "🔊 Vocea e pornită" : "🔇 Vocea e oprită");
    }
    prevFired = s.fired.slice();
    prevState = s.state;
    prevVoiceOn = s.voice_on;
  }

  // ---------- scena ----------
  const lerp = (a, b, f) => a + (b - a) * f;
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

  function skyColors(alt) {
    let i = 0;
    while (i < SKY.length - 2 && alt > SKY[i + 1][0]) i++;
    const [a0, top0, bot0] = SKY[i];
    const [a1, top1, bot1] = SKY[i + 1];
    const f = clamp((alt - a0) / (a1 - a0), 0, 1);
    const mixc = (c0, c1) => `rgb(${c0.map((v, k) => Math.round(lerp(v, c1[k], f))).join(",")})`;
    return [mixc(top0, top1), mixc(bot0, bot1)];
  }

  function drawScene() {
    const alt = view.alt;
    const px = alt * PX_PER_KM;
    const rise = Math.min(px, ROCKET_RISE);
    const offset = Math.max(0, px - ROCKET_RISE);
    const flying = snap && ["flight", "orbit", "abort"].includes(snap.state);
    const tilt = flying ? clamp((view.t - 12) / 250, 0, 1) * 25 : 0;

    $("rocket").setAttribute("transform", `translate(300 ${PAD_Y - rise}) rotate(${tilt.toFixed(2)} 0 -117)`);
    $("world").setAttribute("transform", `translate(0 ${offset.toFixed(1)})`);

    const [top, bottom] = skyColors(alt);
    $("sky-top").setAttribute("stop-color", top);
    $("sky-bottom").setAttribute("stop-color", bottom);
    $("stars").setAttribute("opacity", clamp((alt - 15) / 45, 0, 1).toFixed(2));

    const earthH = clamp((alt - 40) / 160, 0, 1) * 120;
    $("earth").setAttribute("opacity", earthH > 0 ? "1" : "0");
    $("earth").setAttribute("transform", `translate(0 ${(-earthH).toFixed(1)})`);

    if (snap) {
      const engine = snap.engine_on && snap.state !== "abort";
      const separated = snap.fired.includes("separation");
      $("flame1").classList.toggle("on", engine && !separated);
      $("flame2").classList.toggle("on", engine && snap.fired.includes("stage2"));
      $("smoke").classList.toggle("on", engine && alt < 1.5);
      $("shake").classList.toggle("on", engine && alt < 3);
    }
  }

  let lastFrame = performance.now();
  function frame(now) {
    const dt = Math.min(0.1, (now - lastFrame) / 1000);
    lastFrame = now;
    if (snap) {
      const k = Math.min(1, dt * 6);
      view.alt = Math.abs(snap.alt_km - view.alt) > 30 ? snap.alt_km : lerp(view.alt, snap.alt_km, k);
      view.t = snap.t == null ? 0 : lerp(view.t, snap.t, k);
    }
    drawScene();
    requestAnimationFrame(frame);
  }

  // ---------- piesele rachetei ----------
  const SVG_NS = "http://www.w3.org/2000/svg";
  const LABEL_UP = 150;
  const LABEL_DOWN = 420;

  // Pune numărul și numele fiecărei piese deasupra sau dedesubt (alternativ, de la stânga
  // la dreapta), cu o linie până la piesă. Numerotarea merge de la vârf (1) spre bază.
  function buildPartLabels() {
    const layer = $("parts-labels");
    layer.innerHTML = "";
    if (!mission || !mission.parts) return;
    const placed = mission.parts
      .map((p, i) => ({ ...p, num: i + 1, el: document.querySelector(`.part[data-part="${p.key}"]`) }))
      .filter((p) => p.el)
      .map((p) => {
        const box = p.el.getBBox();
        return { ...p, cx: box.x + box.width / 2, top: box.y, bottom: box.y + box.height };
      })
      .sort((a, b) => a.cx - b.cx);
    placed.forEach((p, i) => {
      const down = i % 2 === 0;
      const y = down ? LABEL_DOWN : LABEL_UP;
      const g = document.createElementNS(SVG_NS, "g");
      g.setAttribute("class", "part-label");
      g.dataset.part = p.key;
      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("x1", p.cx);
      line.setAttribute("x2", p.cx);
      line.setAttribute("y1", down ? p.bottom + 6 : p.top - 6);
      line.setAttribute("y2", down ? y - 16 : y + 16);
      const circle = document.createElementNS(SVG_NS, "circle");
      circle.setAttribute("r", 14);
      const num = document.createElementNS(SVG_NS, "text");
      num.setAttribute("class", "num");
      num.textContent = p.num;
      const name = document.createElementNS(SVG_NS, "text");
      name.setAttribute("class", "name");
      name.textContent = p.label;
      g.append(line, circle, num, name);
      layer.appendChild(g);
      // număr + nume centrate împreună sub/deasupra piesei
      const width = 34 + name.getComputedTextLength();
      const left = Math.min(Math.max(p.cx - width / 2, 8), 1592 - width);
      circle.setAttribute("cx", left + 14);
      circle.setAttribute("cy", y);
      num.setAttribute("x", left + 14);
      num.setAttribute("y", y);
      name.setAttribute("x", left + 34);
      name.setAttribute("y", y);
    });
  }

  function renderParts(p) {
    $("parts").hidden = !p;
    document.body.classList.toggle("parts-on", !!p);
    if (!p) return;
    if (!$("parts-labels").childElementCount) buildPartLabels();
    $("parts-count").textContent = `Piesa ${p.index} din ${p.total}`;
    $("parts-name").textContent = p.name;
    $("parts-text").textContent = p.text;
    $("parts-svg").classList.add("has-active");
    for (const el of document.querySelectorAll(".part, .part-label")) {
      el.classList.toggle("active", el.dataset.part === p.key);
    }
  }

  // ---------- conexiune ----------
  function onSnapshot(s) {
    snap = s;
    handleChanges(s);
    renderPanel(s);
    renderQuiz(s.quiz);
    renderParts(s.parts);
  }

  function connect() {
    const es = new EventSource("/events");
    es.onopen = () => {
      $("conn").classList.remove("off");
      $("conn").title = "Conectat";
    };
    es.onerror = () => {
      $("conn").classList.add("off");
      $("conn").title = "Reconectare…";
    };
    es.onmessage = (e) => onSnapshot(JSON.parse(e.data));
    // După o actualizare (git pull + repornirea serviciului) pagina se reîncarcă singură.
    es.addEventListener("hello", (e) => {
      if (build && e.data !== build) location.reload();
      build = e.data;
    });
  }

  const press = (button) => fetch("/api/press/" + button, { method: "POST" });

  $("controls").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-btn]");
    if (btn) press(btn.dataset.btn);
  });
  // Cu ?control=1, cardurile quiz-ului se pot și apăsa (util la teste).
  $("quiz-grid").addEventListener("click", (e) => {
    const cell = e.target.closest("[data-btn]");
    if (cell && showControls && snap && snap.web_control) press(cell.dataset.btn);
  });

  // Aceleași taste ca în modul --sim; merg și pe monitorul Pi-ului, cu o tastatură USB.
  const KEYS = { g: "go", l: "launch", s: "stage", a: "abort", r: "reset", z: "quiz", p: "parts" };
  document.addEventListener("keydown", (e) => {
    if (e.repeat || e.ctrlKey || e.metaKey || e.altKey || !snap || !snap.web_control) return;
    const button = KEYS[e.key.toLowerCase()];
    if (button) {
      e.preventDefault();
      press(button);
    }
  });

  // Z ținut apăsat = GO ținut apăsat: în zbor accelerează timpul până la eliberare.
  document.addEventListener("keyup", (e) => {
    if (e.key.toLowerCase() === "z" && snap && snap.web_control) press("go_up");
  });

  makeStars();
  fetch("/api/mission")
    .then((r) => r.json())
    .then((m) => {
      mission = m;
      buildLists();
      placeQuizCells();
      if (snap) {
        renderPanel(snap);
        renderParts(snap.parts);
      }
    })
    .finally(connect);
  requestAnimationFrame(frame);
})();
