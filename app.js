(() => {
  const $ = (id) => document.getElementById(id);
  const setText = (id, s) => { $(id).textContent = s || ""; };
  const show = (id, yes) => { $(id).classList.toggle("hidden", !yes); };

  const BACKEND_URL = window.APP_CONFIG?.backendUrl;
  const TIMEOUT_MS = window.APP_CONFIG?.requestTimeoutMs ?? 30000;

  let CFG = null;
  let AUTH = { ok:false, user_id:"", pin:"", role:"" };
  let ACTIVE_BLOCKS = [];
  let CURRENT_MODE = "ALTURA";
  let CURRENT_N = 0;

  let REPLACE_OLD_SESSION = null;
  let LOADED_SESSION = null;

  function timeout_(ms) {
    return new Promise((_, rej) => setTimeout(() => rej(new Error("Timeout backend")), ms));
  }

  async function api(action, data = {}) {
    if (!BACKEND_URL) throw new Error("Falta BACKEND_URL en config.js");

    // Header simple text/plain para reducir preflight
    const p = fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ action, ...data })
    });

    const res = await Promise.race([p, timeout_(TIMEOUT_MS)]);
    const json = await res.json();
    return json;
  }

  function parseNum(x){
    const s = String(x||"").trim().replace(",",".");
    if(!s) return null;
    const v = Number(s);
    return Number.isFinite(v) ? v : null;
  }
  function inRange(v,r){ return (v!==null && v>=r.min && v<=r.max); }

  function fillBlocksDatalist(list){
    ACTIVE_BLOCKS = list || [];
    const dl = $("dlBloques");
    dl.innerHTML = "";
    ACTIVE_BLOCKS.forEach(b=>{
      const opt=document.createElement("option");
      opt.value=b;
      dl.appendChild(opt);
    });
    setText("bloqueHint", `${ACTIVE_BLOCKS.length} bloques ACTIVO cargados.`);
  }

  function updateHints(){
    if(!CFG) return;
    setText("modoHint", `ALTURA default=${CFG.defaults.nAltura} · COMPLETO default=${CFG.defaults.nCompleto}`);
    setText("nHint", `Validaciones: altura [${CFG.validation.altura_cm.min}, ${CFG.validation.altura_cm.max}] cm · estructura [${CFG.validation.estructura_cm.min}, ${CFG.validation.estructura_cm.max}] cm · diámetro [${CFG.validation.diametro_mm.min}, ${CFG.validation.diametro_mm.max}] mm`);
  }

  function disableSubmitIfInvalid(){
    const inputs = [...document.querySelectorAll("#tableArea input[data-field]")];
    if(!inputs.length){ $("btnSubmit").disabled = true; return; }

    for(const inp of inputs){
      const field = inp.dataset.field;
      const v = parseNum(inp.value);
      const ok = inRange(v, CFG.validation[field]);
      inp.classList.toggle("bad", inp.value && !ok);
      if(!inp.value || !ok){ $("btnSubmit").disabled = true; return; }
    }
    $("btnSubmit").disabled = false;
  }

  function enablePasteFill(input, list){
    input.addEventListener("paste", (ev)=>{
      const text = (ev.clipboardData || window.clipboardData).getData("text");
      if(!text || !text.includes("\n")) return;
      ev.preventDefault();
      const lines = text.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
      const start = list.indexOf(input);
      for(let i=0;i<lines.length;i++){
        const idx = start + i;
        if(idx>=list.length) break;
        list[idx].value = lines[i];
        list[idx].dispatchEvent(new Event("input"));
      }
    });
  }

  function renderTable(mode, n, prefillSamples){
    CURRENT_MODE = mode;
    CURRENT_N = n;

    const cols = (mode==="COMPLETO")
      ? ["altura_cm","estructura_cm","diametro_mm"]
      : ["altura_cm"];

    let html = `<table><thead><tr><th>Muestra</th>`;
    html += (mode==="COMPLETO")
      ? `<th>Altura (cm)</th><th>Estructura (cm)</th><th>Diámetro (mm)</th>`
      : `<th>Altura (cm)</th>`;
    html += `</tr></thead><tbody>`;

    for(let i=1;i<=n;i++){
      html += `<tr><td>${i}</td>`;
      for(const c of cols){
        const val = prefillSamples?.[i-1]?.[c] ?? "";
        html += `<td><input data-i="${i}" data-field="${c}" inputmode="decimal" placeholder="0" value="${String(val)}"></td>`;
      }
      html += `</tr>`;
    }
    html += `</tbody></table>`;
    $("tableArea").innerHTML = html;

    const inputs = [...document.querySelectorAll("#tableArea input[data-field]")];
    const colMap = {};
    for(const c of cols) colMap[c] = [];

    inputs.forEach(inp=>{
      colMap[inp.dataset.field].push(inp);
      inp.addEventListener("input", disableSubmitIfInvalid);
      inp.addEventListener("keydown", (e)=>{
        if(e.key==="Enter"){
          e.preventDefault();
          const all = [...document.querySelectorAll("#tableArea input[data-field]")];
          const idx = all.indexOf(inp);
          if(idx>=0 && all[idx+1]) all[idx+1].focus();
        }
      });
    });

    for(const c of cols){
      colMap[c].forEach(inp => enablePasteFill(inp, colMap[c]));
    }

    disableSubmitIfInvalid();
  }

  async function loadBlocks(){
    setText("msg","Cargando bloques…");
    const r = await api("get_blocks", { user_id: AUTH.user_id, pin: AUTH.pin });
    if(!r.ok) throw new Error(r.error || "No se pudo cargar bloques.");
    fillBlocksDatalist(r.bloques);
    setText("msg","");
  }

  async function checkDup(){
    const bloque = $("bloque").value.trim();
    const modo = $("modo").value;
    if(!bloque || !ACTIVE_BLOCKS.includes(bloque)) return;

    const r = await api("list_sessions_today", { user_id: AUTH.user_id, pin: AUTH.pin, bloque, modo });
    if(!r.ok) return;

    if(r.sessions && r.sessions.length){
      show("dupBox", true);
      setText("dupText", `Ya existe(n) ${r.sessions.length} sesión(es) vigentes HOY (${r.fecha}) para este bloque/modo. Se permitirá guardar, pero se marcará DUPLICADO.`);
    } else {
      show("dupBox", false);
      setText("dupText", "");
    }
  }

  function resetFormOnly(){
    $("obs").value = "";
    $("tableArea").innerHTML = "";
    $("btnSubmit").disabled = true;
    show("dupBox", false);
    setText("submitMsg","");
    setText("finalMsg","");
  }

  async function init(){
    try{
      setText("statusTop","Inicializando…");
      CFG = await api("defaults");
      if(!CFG.ok) throw new Error(CFG.error || "defaults falló");
      updateHints();

      const ping = await api("ping");
      setText("statusTop", `Servidor OK · TZ=${ping.tz}`);

    } catch(e){
      setText("statusTop", "Error inicializando: " + e.message);
    }
  }

  // EVENTS
  $("btnLogin").onclick = async ()=>{
    try{
      setText("loginMsg","Validando…");
      const user_id = $("user_id").value.trim();
      const pin = $("pin").value.trim();

      const r = await api("auth", { user_id, pin });
      if(!r.ok){ setText("loginMsg", r.error || "Login inválido."); return; }

      AUTH = { ok:true, user_id, pin, role: r.user.role };
      setText("loginMsg","OK.");

      show("loginBox", false);
      show("appBox", true);

      setText("who", AUTH.user_id);
      setText("role", AUTH.role);
      setText("fecha", new Date().toLocaleDateString("es-EC"));

      $("modo").value = "ALTURA";
      $("n").value = CFG.defaults.nAltura;

      show("btnAdminToggle", AUTH.role === "admin");

      await loadBlocks();
      await checkDup();

    } catch(e){
      setText("loginMsg", e.message);
    }
  };

  $("btnLogout").onclick = ()=> location.reload();

  $("btnReloadBlocks").onclick = async ()=>{
    try{ await loadBlocks(); } catch(e){ alert(e.message); }
  };

  $("modo").onchange = async ()=>{
    const modo = $("modo").value;
    $("n").value = (modo === "COMPLETO") ? CFG.defaults.nCompleto : CFG.defaults.nAltura;
    REPLACE_OLD_SESSION = null;
    LOADED_SESSION = null;
    resetFormOnly();
    await checkDup();
  };

  $("bloque").onchange = async ()=>{
    REPLACE_OLD_SESSION = null;
    LOADED_SESSION = null;
    resetFormOnly();
    await checkDup();
  };

  $("btnBuild").onclick = async ()=>{
    const bloque = $("bloque").value.trim();
    const modo = $("modo").value;
    const n = Math.floor(Number($("n").value));

    if(!ACTIVE_BLOCKS.includes(bloque)){ setText("msg","Bloque inválido/no ACTIVO."); return; }
    if(!Number.isFinite(n) || n<1){ setText("msg","N inválido."); return; }

    setText("msg","");
    renderTable(modo, n, null);
    await checkDup();
  };

  $("btnClear").onclick = ()=>{
    $("bloque").value = "";
    $("modo").value = "ALTURA";
    $("n").value = CFG.defaults.nAltura;
    REPLACE_OLD_SESSION = null;
    LOADED_SESSION = null;
    resetFormOnly();
  };

  $("btnSubmit").onclick = async ()=>{
    try{
      setText("submitMsg","Validando…");
      const bloque = $("bloque").value.trim();
      const modo = $("modo").value;
      const n = Math.floor(Number($("n").value));
      const obs = $("obs").value.trim();

      if(!ACTIVE_BLOCKS.includes(bloque)) throw new Error("Bloque no ACTIVO.");
      if(!["ALTURA","COMPLETO"].includes(modo)) throw new Error("Modo inválido.");
      if(!Number.isFinite(n) || n<1) throw new Error("N inválido.");
      if(!CURRENT_N) throw new Error("Primero crea el formulario.");

      const samples = [];
      for(let i=1;i<=n;i++){
        const altura = parseNum(document.querySelector(`#tableArea input[data-i="${i}"][data-field="altura_cm"]`)?.value);
        if(!inRange(altura, CFG.validation.altura_cm)) throw new Error(`Altura inválida en muestra ${i}`);

        let estructura = "";
        let diametro = "";
        if(modo==="COMPLETO"){
          estructura = parseNum(document.querySelector(`#tableArea input[data-i="${i}"][data-field="estructura_cm"]`)?.value);
          diametro   = parseNum(document.querySelector(`#tableArea input[data-i="${i}"][data-field="diametro_mm"]`)?.value);
          if(!inRange(estructura, CFG.validation.estructura_cm)) throw new Error(`Estructura inválida en muestra ${i}`);
          if(!inRange(diametro,   CFG.validation.diametro_mm))   throw new Error(`Diámetro inválido en muestra ${i}`);
        }

        samples.push({ altura_cm: altura, estructura_cm: estructura, diametro_mm: diametro });
      }

      if(REPLACE_OLD_SESSION){
        setText("submitMsg","Reemplazando sesión (auditoría)…");
        const r = await api("replace_session", {
          user_id: AUTH.user_id, pin: AUTH.pin,
          payload: { old_session_id: REPLACE_OLD_SESSION, bloque, modo, n, observacion: obs, samples }
        });
        if(!r.ok) throw new Error(r.error || "Error reemplazando.");

        setText("submitMsg", `OK reemplazo. Nueva sesión=${r.session_id_new}. Reemplazadas=${r.replacedCount}. Insertadas=${r.inserted}.`);
        setText("finalMsg", `Auditoría OK: viejas FALSE, nuevas TRUE.`);
        REPLACE_OLD_SESSION = null;
        LOADED_SESSION = null;
        return;
      }

      setText("submitMsg","Enviando…");
      const r = await api("submit", {
        user_id: AUTH.user_id, pin: AUTH.pin,
        payload: { bloque, modo, n, observacion: obs, samples }
      });
      if(!r.ok) throw new Error(r.error || "Error guardando.");

      let msg = `OK. session_id=${r.session_id}. Filas=${n}.`;
      if(r.duplicate_warning) msg += " (DUPLICADO marcado)";
      setText("submitMsg", msg);
      setText("finalMsg", r.duplicate_warning ? "Advertencia: guardado como DUPLICADO." : "");

      $("tableArea").innerHTML = "";
      $("btnSubmit").disabled = true;

    } catch(e){
      setText("submitMsg", "Error: " + e.message);
    }
  };

  $("btnAdminToggle").onclick = ()=>{
    $("adminBox").classList.toggle("hidden");
    setText("admMsg","");
    $("sessionsList").innerHTML = "";
    setText("replaceHint","");
  };

  $("btnFindSessions").onclick = async ()=>{
    try{
      setText("admMsg","Buscando…");
      const bloque = $("admBloque").value.trim();
      const modo = $("admModo").value;
      if(!ACTIVE_BLOCKS.includes(bloque)){ setText("admMsg","Bloque inválido/no ACTIVO."); return; }

      const r = await api("list_sessions_today", {
        user_id: AUTH.user_id, pin: AUTH.pin, bloque, modo
      });
      if(!r.ok) throw new Error(r.error || "Error.");

      const box = $("sessionsList");
      box.innerHTML = "";
      if(!r.sessions.length){
        setText("admMsg","No hay sesiones vigentes hoy para ese bloque/modo.");
        return;
      }
      setText("admMsg", `Sesiones hoy (${r.fecha}): ${r.sessions.length}`);

      r.sessions.forEach(s=>{
        const div = document.createElement("div");
        div.className = "warnBox";
        div.style.marginTop = "10px";
        div.innerHTML = `
          <div><b>${s.session_id}</b></div>
          <div class="muted" style="margin-top:6px">filas=${s.count}</div>
          <div class="row" style="margin-top:10px">
            <button class="btn">Cargar para editar y reemplazar</button>
          </div>
        `;
        div.querySelector("button").onclick = async ()=>{
          setText("replaceHint","Cargando sesión…");
          const g = await api("get_session", {
            user_id: AUTH.user_id, pin: AUTH.pin, session_id: s.session_id
          });
          if(!g.ok) throw new Error(g.error || "No se pudo cargar sesión.");

          LOADED_SESSION = g.session;
          REPLACE_OLD_SESSION = g.session.session_id;

          $("bloque").value = g.session.bloque;
          $("modo").value = g.session.modo;
          $("n").value = g.session.n;
          $("obs").value = `REEMPLAZO de ${g.session.session_id}`;

          const prefill = g.session.samples.map(x => ({
            altura_cm: x.altura_cm ?? "",
            estructura_cm: x.estructura_cm ?? "",
            diametro_mm: x.diametro_mm ?? ""
          }));

          renderTable(g.session.modo, g.session.n, prefill);
          await checkDup();

          setText("replaceHint", `Modo REEMPLAZO activo: al enviar se reemplazará ${g.session.session_id}.`);
        };

        box.appendChild(div);
      });

    } catch(e){
      setText("admMsg", "Error: " + e.message);
    }
  };

  init();
})();

