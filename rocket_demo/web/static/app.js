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
  };
  const PRE_LAUNCH = new Set(["idle", "checks", "hold", "ready", "scrub"]);

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

  const showControls = new URLSearchParams(location.search).has("control");

  let mission = null;
  let snap = null;
  let prevFired = [];
  let prevState = null;
  const view = { alt: 0, t: 0 };
  let toastTimer = null;

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
      li.className = li.dataset.key === last && s.state === "flight" ? "current" : done ? "done" : "";
      li.querySelector(".mark").textContent = done ? "✓" : "·";
    });

    $("stage-banner").hidden = !s.awaiting_stage;
    $("controls").hidden = !(showControls && s.web_control);

    const big = $("big-count");
    big.hidden = s.state !== "countdown";
    if (s.state === "countdown") big.textContent = Math.max(1, Math.ceil(-s.t));
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
    prevFired = s.fired.slice();
    prevState = s.state;
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

  // ---------- conexiune ----------
  function onSnapshot(s) {
    snap = s;
    handleChanges(s);
    renderPanel(s);
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
  }

  $("controls").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-btn]");
    if (btn) fetch("/api/press/" + btn.dataset.btn, { method: "POST" });
  });

  makeStars();
  fetch("/api/mission")
    .then((r) => r.json())
    .then((m) => {
      mission = m;
      buildLists();
      if (snap) renderPanel(snap);
    })
    .finally(connect);
  requestAnimationFrame(frame);
})();
