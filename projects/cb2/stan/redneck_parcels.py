#!/usr/bin/env python3
"""Five Parcels — redneck land boss game (Cal → MO · no beer)."""

from __future__ import annotations


def parcels_game_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<title>Five Parcels</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #0f0c08;
    color: #f2e8d0;
    min-height: 100dvh;
    padding: max(0.75rem, env(safe-area-inset-top)) 0.75rem 1.5rem;
    touch-action: manipulation;
  }
  header { text-align: center; margin-bottom: 0.75rem; }
  .badge {
    font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase;
    color: #c45c26; margin-bottom: 0.25rem;
  }
  h1 { font-size: 1.35rem; color: #e8c547; font-weight: 700; }
  .sub { font-size: 0.82rem; color: #9a8870; margin-top: 0.25rem; line-height: 1.35; }
  .stats {
    display: flex; justify-content: center; gap: 1rem; margin: 0.75rem 0;
    font-size: 0.75rem; color: #888;
  }
  .stats b { color: #7bed9f; font-size: 1rem; display: block; }
  .grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;
    max-width: 22rem; margin: 0 auto;
  }
  .parcel {
    aspect-ratio: 1;
    border: 2px solid #3d3020;
    border-radius: 12px;
    background: linear-gradient(145deg, #1a2818 0%, #0f180f 100%);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 0.5rem; cursor: pointer; transition: border-color 0.15s, transform 0.1s;
    -webkit-tap-highlight-color: transparent;
  }
  .parcel:active { transform: scale(0.97); }
  .parcel.open { border-color: #c45c26; box-shadow: 0 0 20px rgba(196,92,38,0.25); }
  .parcel.done { border-color: #7bed9f; opacity: 0.85; }
  .parcel .num { font-size: 1.5rem; font-weight: 800; color: #5a4a32; }
  .parcel.done .num { color: #7bed9f; }
  .parcel .label { font-size: 0.65rem; color: #888; margin-top: 0.2rem; text-align: center; }
  .parcel.done .label::after { content: " ✓"; color: #7bed9f; }
  .task-box {
    max-width: 22rem; margin: 0.75rem auto 0;
    background: #1a1510; border: 1px solid #3d3020; border-radius: 14px;
    padding: 1rem; min-height: 5.5rem; text-align: center;
  }
  .task-box.empty { color: #555; font-size: 0.9rem; padding: 1.5rem 1rem; }
  .task-box h2 { font-size: 0.95rem; color: #e8c547; margin-bottom: 0.35rem; }
  .task-box p { font-size: 0.85rem; color: #bbb; line-height: 1.4; }
  .fuel { font-size: 0.7rem; color: #c45c26; margin-top: 0.5rem; }
  .btn {
    display: block; width: 100%; max-width: 22rem; margin: 0.75rem auto 0;
    padding: 0.9rem; border: none; border-radius: 999px;
    background: #c45c26; color: #fff; font-size: 1rem; font-weight: 700;
    cursor: pointer;
  }
  .btn:disabled { background: #333; color: #666; }
  .btn.win { background: #7bed9f; color: #0a0a12; }
  .toast {
    position: fixed; bottom: 1rem; left: 50%; transform: translateX(-50%);
    background: #e8c547; color: #0a0a12; padding: 0.5rem 1rem; border-radius: 999px;
    font-size: 0.85rem; font-weight: 600; opacity: 0; transition: opacity 0.3s;
    pointer-events: none; z-index: 9;
  }
  .toast.show { opacity: 1; }
  .cert {
    display: none; max-width: 22rem; margin: 1rem auto; padding: 1.25rem;
    border: 3px double #e8c547; border-radius: 12px; text-align: center;
    background: #1a1510;
  }
  .cert.show { display: block; }
  .cert h2 { color: #e8c547; font-size: 1.1rem; margin-bottom: 0.5rem; }
  .cert p { font-size: 0.85rem; color: #ccc; line-height: 1.45; }
  footer { text-align: center; margin-top: 1rem; font-size: 0.7rem; color: #444; }
  footer a { color: #7bed9f; }
</style>
</head>
<body>
  <header>
    <p class="badge">Cal → Missouri · redneck approved</p>
    <h1>Five Parcels</h1>
    <p class="sub">Left the coast. Bought dirt. Now you're the boss.<br>No beer required — sweet tea runs fine.</p>
  </header>

  <div class="stats">
    <div><b id="done">0</b>parcels fixed</div>
    <div><b id="tea">5</b>sweet tea left</div>
    <div><b id="pride">0</b>redneck pride</div>
  </div>

  <div class="grid" id="grid"></div>

  <div class="task-box empty" id="taskBox">Tap a parcel to see what needs doing.</div>

  <button class="btn" id="doBtn" disabled>Do the work</button>

  <div class="cert" id="cert">
    <h2>🏆 Redneck Land Boss</h2>
    <p>Five parcels. One Missourian. California couldn't hold you.</p>
    <p style="margin-top:0.75rem;color:#e8c547">Screenshot this. Send it to Brian.</p>
  </div>

  <footer><a href="/dirt-strong">DIRT STRONG</a> · share when you win</footer>
  <div class="toast" id="toast"></div>

  <script>
(function(){
  const TASKS = [
    { t: "Mend the fence", d: "Cattle don't care about your old area code.", f: "1 sweet tea" },
    { t: "Clear the brush", d: "Missouri grows it back twice as fast.", f: "1 sweet tea" },
    { t: "Set corner posts", d: "Five parcels means five lines somebody respects.", f: "1 sweet tea" },
    { t: "Gravel the drive", d: "Mud is honest. Gravel is pride.", f: "1 sweet tea" },
    { t: "Raise the flag", d: "Your land. Your rules. Redneck legal.", f: "1 sweet tea" },
    { t: "Fix the gate", d: "If it squeaks, every neighbor heard it.", f: "1 sweet tea" },
    { t: "Plant the garden", d: "California had farmers markets. You have dirt.", f: "1 sweet tea" },
    { t: "Patch the roof", d: "Rain doesn't text first.", f: "1 sweet tea" },
    { t: "Fill the feeder", d: "Wildlife votes redneck.", f: "1 sweet tea" },
    { t: "Run the chainsaw", d: "Ear protection optional. Dignity required.", f: "1 sweet tea" },
  ];
  const LABELS = ["North 40", "Back 20", "Hollow", "Creek side", "Road front"];

  let parcels = [0,1,2,3,4].map(i => ({ id: i, done: false, task: null }));
  let selected = null;
  let tea = 5;
  let pride = 0;

  const grid = document.getElementById("grid");
  const taskBox = document.getElementById("taskBox");
  const doBtn = document.getElementById("doBtn");
  const toast = document.getElementById("toast");
  const cert = document.getElementById("cert");

  function pickTask() {
    return TASKS[Math.floor(Math.random() * TASKS.length)];
  }

  function render() {
    grid.innerHTML = "";
    parcels.forEach(p => {
      const el = document.createElement("div");
      el.className = "parcel" + (p.done ? " done" : "") + (selected === p.id ? " open" : "");
      el.innerHTML = '<span class="num">' + (p.id + 1) + '</span><span class="label">' + LABELS[p.id] + '</span>';
      if (!p.done) el.onclick = () => select(p.id);
      grid.appendChild(el);
    });
    const done = parcels.filter(p => p.done).length;
    document.getElementById("done").textContent = done;
    document.getElementById("tea").textContent = tea;
    document.getElementById("pride").textContent = pride;
    if (done === 5) {
      doBtn.className = "btn win";
      doBtn.textContent = "You win — land boss";
      doBtn.disabled = true;
      cert.classList.add("show");
      if (navigator.share) {
        doBtn.disabled = false;
        doBtn.textContent = "Share victory";
        doBtn.onclick = () => navigator.share({ title: "Redneck Land Boss", url: location.href });
      }
    }
  }

  function select(id) {
    if (tea <= 0) { flash("Out of sweet tea — rest up, boss"); return; }
    selected = id;
    const p = parcels[id];
    if (!p.task) p.task = pickTask();
    taskBox.className = "task-box";
    taskBox.innerHTML = '<h2>' + p.task.t + '</h2><p>' + p.task.d + '</p><p class="fuel">Costs ' + p.task.f + '</p>';
    doBtn.disabled = false;
    doBtn.textContent = "Do the work";
    render();
  }

  function flash(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2200);
  }

  doBtn.onclick = function() {
    if (selected === null || parcels[selected].done) return;
    if (tea <= 0) { flash("Sweet tea empty. Even rednecks rest."); return; }
    tea--;
    pride += 10 + Math.floor(Math.random() * 15);
    parcels[selected].done = true;
    flash(["Attaboy.", "That's Missouri.", "Redneck legal.", "Cal couldn't do that."][Math.floor(Math.random()*4)]);
    selected = null;
    taskBox.className = "task-box empty";
    taskBox.textContent = parcels.every(p => p.done) ? "All five. You own it." : "Pick the next parcel.";
    doBtn.disabled = true;
    render();
  };

  render();
})();
  </script>
</body>
</html>"""
