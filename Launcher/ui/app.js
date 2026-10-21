const fallbackApi = {
 get_config: async () => ({
  game_path: "game\\bin\\client.exe",
  server_url: "http://127.0.0.1:8888",
  auto_server: true,
  close_on_launch: false,
  fov: 60,
  bgm_enabled: true
 }),
 save_config: async cfg => {
  console.log("Saved config:", cfg);
  return true;
 },
 set_fov: async val => {
  console.log("Set FOV:", val);
  return {
   success: true,
   fov: val
  };
 },
 launch_game: async mode => {
  console.log("Launching game mode:", mode);
  return {
   success: true,
   message: "Game started"
  };
 },
 launch_server: async () => {
  console.log("Starting server backend");
  return {
   success: true,
   running: true
  };
 },
 stop_server: async () => ({
  success: true,
  running: false
 }),
 check_server_status: async () => ({
  online: true,
  url: "http://127.0.0.1:8888",
  server_name: "Cyber Hunter Revival"
 }),
 get_launch_status: async () => ({
  status: "idle",
  ready: false,
  running: false
 }),
 kill_game: async () => ({
  success: true
 }),
 master_snapshot: async () => ({
  success: true,
  revival: {
   mode: "local",
   server_ip: "127.0.0.1"
  },
  ports: {
   control_panel: true,
   game_api: true,
   patch: false,
   http_stub: false,
   gateway: false
  },
  launch: {
   status: "idle",
   ready: false,
   running: false
  },
  status_file: {},
  client_pid: 0,
  account: {
   name: "Hunter",
   hero_id: 90101
  },
  log_paths: {
   lobby: "client/runtime/lobby_full.log"
  }
 }),
 master_tail_log: async () => ({
  success: true,
  text: "(browser mock — open in Launcher)\n",
  offset: 0,
  path: "lobby"
 }),
 master_command_catalog: async () => ({
  success: true,
  commands: [ {
   cmd: "home",
   group: "lobby",
   desc: "Home"
  }, {
   cmd: "br",
   group: "match",
   desc: "Start BR"
  }, {
   cmd: "remove all bots",
   group: "test",
   label: "Remove All Bots",
   desc: "Despawn bots & alive=1"
  }, {
   cmd: "remove all lootables",
   group: "test",
   label: "Remove All Lootables",
   desc: "Despawn items & chests"
  }, {
   cmd: "remove safe zone",
   group: "test",
   label: "Remove Safe Zone",
   desc: "Disable circle storm & damage"
  }, {
   cmd: "disable rain",
   group: "test",
   label: "Disable Rain",
   desc: "Clear rain effects, audio & sky"
  }, {
   cmd: "loot",
   group: "match",
   desc: "Reseed loot"
  }, {
   cmd: "reexec",
   group: "debug",
   desc: "Reload payload"
  } ]
 }),
 master_send_cmd: async c => ({
  success: true,
  message: "mock sent: " + c
 }),
 master_kill_client: async () => ({
  success: true,
  message: "mock kill"
 }),
 spawn_mapper_snapshot: async () => ({
  success: true,
  live: {
   open: false,
   kind: "chest",
   type_id: 4106,
   count: 0,
   pose: null
  },
  doc: {
   version: 1,
   marks: []
  },
  paths: {},
  client_running: false
 }),
 spawn_mapper_cmd: async c => ({
  success: true,
  message: "mock mapper: " + c
 }),
 spawn_mapper_update_label: async () => ({
  success: true,
  message: "mock label"
 }),
 spawn_mapper_delete_mark: async () => ({
  success: true,
  message: "mock delete",
  count: 0
 }),
 spawn_mapper_open_folder: async () => ({
  success: true,
  message: "mock folder"
 }),
 verify_game_files: async () => ({
  success: true,
  message: "All 18 core archives verified (100% intact)"
 }),
 open_game_directory: async () => ({
  success: true
 }),
 browse_game_path: async () => "game\\bin\\client.exe",
 is_game_installed: async () => true,
 get_game_download_state: async () => ({
  status: "idle",
  installed: true,
  percent: 0
 }),
 start_game_download: async () => ({
  success: true,
  message: "Mock download started"
 }),
 pause_game_download: async () => ({
  success: true,
  message: "Mock download paused"
 }),
 resume_game_download: async () => ({
  success: true,
  message: "Mock download resumed"
 }),
 create_tester_account: async (u, p, h) => ({
  success: true,
  message: "Tester account created (mock)",
  username: u,
  password: p,
  hero_name: h || u
 }),
 list_tester_accounts: async () => ({
  success: true,
  testers: []
 }),
 dev_ban_player: async u => ({
  success: true,
  message: u + " banned (mock)"
 }),
 dev_unban_player: async () => ({
  success: true,
  message: "Unbanned (mock)"
 }),
 dev_list_bans: async () => ({
  success: true,
  bans: []
 }),
 get_ban_status: async () => ({
  banned: false
 }),
 open_external_url: async url => window.open(url, "_blank"),
 minimize_window: async () => console.log("Minimize"),
 close_window: async () => console.log("Close"),
 account_state: async () => ({
  available: true,
  accounts: [ {
   username: "Hunter",
   hero_name: "Hunter"
  } ],
  signed_in: null
 }),
 account_signup: async (u, p, hero) => ({
  success: true,
  message: "Signed in as " + u,
  account: {
   username: u,
   hero_name: hero || u
  }
 }),
 account_login: async (u, p, remember) => ({
  success: true,
  message: "Signed in as " + u,
  account: {
   username: u,
   hero_name: u
  }
 }),
 account_logout: async () => ({
  success: true,
  message: "Signed out."
 })
};

function getApi() {
 if (window.pywebview && window.pywebview.api) {
  return window.pywebview.api;
 }
 return fallbackApi;
}

const NEWS_DATA = {
 events: [ {
  title: "[Season 1] Reawakening of Quantum Matrix & Cyber Island",
  date: "2026.08.31 • Active Now",
  tag: "EVENT",
  thumb: "assets/map-biohazard-facility.jpg"
 }, {
  title: "[Elite Trial] Dual Weapon Mastery & Photon Droid Arena",
  date: "2026.09.05 • Upcoming",
  tag: "TRIAL",
  thumb: "assets/map-coastal-resort.jpg"
 }, {
  title: "[Global Ranking] Cyberspace Apex Hunters Championship",
  date: "2026.09.12 • Register",
  tag: "TOURNEY",
  thumb: "assets/map-sunken-suburb.jpg"
 } ],
 notices: [ {
  title: "[Maintenance] Private Server Protocol v2.5 Synchronized",
  date: "2026.08.30 • Completed",
  tag: "NOTICE",
  thumb: "assets/map-sunken-suburb.jpg"
 }, {
  title: "[Security] Enhanced Anti-Cheat & Packet Validation Active",
  date: "2026.08.28 • Live",
  tag: "SECURITY",
  thumb: "assets/map-biohazard-facility.jpg"
 } ],
 news: [ {
  title: "[Feature] Full Parkour & Glide Physics Engine Overview",
  date: "2026.08.29 • Dev Blog",
  tag: "DEV BLOG",
  thumb: "assets/hero-bg.jpg"
 }, {
  title: "[Community] Custom Modding Tools & Skin Importer Released",
  date: "2026.08.25 • Community",
  tag: "MODDING",
  thumb: "assets/map-coastal-resort.jpg"
 } ]
};

let currentTab = "events";

let currentNewsIndex = 0;

let newsTimer = null;

let serverPollTimer = null;

let currentConfig = {};

let isAudioMuted = false;

const audioCtx = new (window.AudioContext || window.webkitAudioContext);

function playBeep(freq = 440, type = "sine", duration = .1) {
 if (isAudioMuted) return;
 try {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(.08, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(.001, audioCtx.currentTime + duration);
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.start();
  osc.stop(audioCtx.currentTime + duration);
 } catch (e) {}
}

function showToast(msg, icon = "fa-circle-check") {
 const container = document.getElementById("toastContainer");
 if (!container) return;
 const toast = document.createElement("div");
 toast.className = "toast-msg";
 toast.innerHTML = `<i class="fa-solid ${escHtml(icon)}"></i> <span></span>`;
 toast.querySelector("span").textContent = String(msg == null ? "" : msg);
 container.appendChild(toast);
 setTimeout(() => {
  toast.style.opacity = "0";
  toast.style.transform = "translateY(15px)";
  setTimeout(() => toast.remove(), 300);
 }, 3200);
}

document.addEventListener("DOMContentLoaded", async () => {
 initNavigation();
 initNewsCarousel();
 initSettingsModal();
 initGraphicsSetupModal();
 initAccountModal();
 initAddDevModal();
 initAddTesters();
 initBanPlayersSettings();
 initActions();
 initSocial();
 initTitlebar();
 initMasterConsole();
 initSpawnMapper();
 await apiReady();
 await loadConfiguration();
 await checkGameInstalled();
 startServerPoll();
 startUpdateCheck();
 const st = await refreshAccountState();
 startBanPoll();
 if (!signedInAccount && window.openAccountModal) {
  window.openAccountModal();
 }
});

async function apiReady() {
 if (window.pywebview && window.pywebview.api && window.pywebview.api.get_config) return;
 return new Promise(resolve => {
  const finish = () => resolve();
  window.addEventListener("pywebviewready", finish, {
   once: true
  });
  const timer = setInterval(() => {
   if (window.pywebview && window.pywebview.api && window.pywebview.api.get_config) {
    clearInterval(timer);
    finish();
   }
  }, 40);
  setTimeout(() => {
   clearInterval(timer);
   finish();
  }, 5e3);
 });
}

function initNavigation() {
 const railBtns = document.querySelectorAll(".rail-game-btn");
 const allGamesBtn = document.getElementById("railBtnAllGames");
 const masterBtn = document.getElementById("railBtnMaster");
 const panels = document.querySelectorAll(".game-view-panel");
 function switchView(viewId) {
  playBeep(520, "sine", .08);
  if (viewId === "master") {
   const isDev = !!(signedInAccount && signedInAccount.is_dev);
   if (!isDev) {
    showToast("Developer mode required for Control Panel.", "fa-shield-halved");
    return;
   }
   if (window.__openMasterConsole) window.__openMasterConsole();
   if (masterBtn) masterBtn.classList.add("active");
   if (allGamesBtn) allGamesBtn.classList.remove("active");
   railBtns.forEach(b => b.classList.remove("active"));
   return;
  }
  if (window.__closeMasterConsole) window.__closeMasterConsole();
  if (masterBtn) masterBtn.classList.remove("active");
  panels.forEach(p => p.classList.remove("active"));
  railBtns.forEach(b => b.classList.remove("active"));
  if (allGamesBtn) allGamesBtn.classList.remove("active");
  const targetPanel = document.getElementById(`view-${viewId}`);
  if (targetPanel) {
   targetPanel.classList.add("active");
  }
  if (viewId === "hub") {
   if (allGamesBtn) allGamesBtn.classList.add("active");
  } else {
   const activeBtn = document.querySelector(`.rail-game-btn[data-view="${viewId}"]`);
   if (activeBtn) activeBtn.classList.add("active");
  }
 }
 railBtns.forEach(btn => {
  btn.addEventListener("click", () => {
   const view = btn.dataset.view;
   switchView(view);
  });
 });
 if (allGamesBtn) {
  allGamesBtn.addEventListener("click", () => {
   switchView("hub");
  });
 }
 if (masterBtn) {
  masterBtn.addEventListener("click", () => switchView("master"));
 }
 const hubCards = document.querySelectorAll(".hub-game-card");
 const hubDesc = document.getElementById("hubDescPreview");
 const hubBg = document.getElementById("hubBgPreview");
 hubCards.forEach(card => {
  card.addEventListener("click", () => {
   playBeep(720, "sine", .12);
   card.classList.add("card-click-anim");
   hubCards.forEach(c => c.classList.remove("active"));
   card.classList.add("active");
   const gameId = card.dataset.game;
   const desc = card.dataset.desc;
   const bg = card.dataset.bg;
   if (hubDesc && desc) hubDesc.textContent = desc;
   if (hubBg && bg) hubBg.src = bg;
   setTimeout(() => {
    card.classList.remove("card-click-anim");
    switchView(`game-${gameId}`);
   }, 200);
  });
 });
}

function initNewsCarousel() {
 const tabs = document.querySelectorAll(".news-tab");
 const dots = document.querySelectorAll(".news-dot");
 function renderNews(tab, index) {
  const list = NEWS_DATA[tab] || NEWS_DATA.events;
  if (index >= list.length) index = 0;
  const item = list[index];
  const thumb = document.getElementById("newsThumb");
  const tag = document.getElementById("newsTag");
  const title = document.getElementById("newsTitle");
  const date = document.getElementById("newsDate");
  if (thumb) thumb.src = item.thumb;
  if (tag) tag.textContent = item.tag;
  if (title) title.textContent = item.title;
  if (date) date.textContent = item.date;
  dots.forEach((d, i) => {
   d.classList.toggle("active", i === index);
  });
 }
 tabs.forEach(tab => {
  tab.addEventListener("click", () => {
   tabs.forEach(t => t.classList.remove("active"));
   tab.classList.add("active");
   currentTab = tab.dataset.tab;
   currentNewsIndex = 0;
   renderNews(currentTab, currentNewsIndex);
  });
 });
 dots.forEach(dot => {
  dot.addEventListener("click", () => {
   currentNewsIndex = parseInt(dot.dataset.index);
   renderNews(currentTab, currentNewsIndex);
  });
 });
 if (newsTimer) clearInterval(newsTimer);
 newsTimer = setInterval(() => {
  const list = NEWS_DATA[currentTab] || NEWS_DATA.events;
  currentNewsIndex = (currentNewsIndex + 1) % list.length;
  renderNews(currentTab, currentNewsIndex);
 }, 4500);
 const newsBanner = document.getElementById("newsBanner");
 if (newsBanner) {
  newsBanner.addEventListener("click", () => {
   playBeep(700, "triangle", .1);
   const cs = document.getElementById("comingSoonModal");
   if (cs) cs.classList.add("open");
  });
 }
}

let updateAvailable = false;

let isUpdating = false;

let gameInstalled = true;

let isGameDownloading = false;

let gameDownloadPollTimer = null;

let isLaunching = false;

let isGameRunning = false;

let hasAutoMinimized = false;

let statusPollTimer = null;

function setPlayButtonState(state, customLabel) {
 const btn = document.getElementById("btnPlayMain");
 const label = document.getElementById("btnPlayLabel");
 const statusTag = document.getElementById("installedStatus");
 if (!btn || !label) return;
 btn.classList.remove("is-launching", "is-running", "is-update", "is-updating", "is-banned");
 if ((state === "idle" || state === "download" || state === "update") && currentBan && currentBan.banned) {
  state = "banned";
 }
 if (state === "idle") {
  if (!gameInstalled) state = "download"; else if (updateAvailable) state = "update";
 }
 if (state === "banned") {
  btn.classList.add("is-banned");
  label.innerHTML = `<i class="fa-solid fa-ban btn-play-icon"></i> BANNED`;
  if (statusTag) {
   const until = currentBan && currentBan.expires_at ? ` until ${escHtml(fmtDate(currentBan.expires_at))}` : "";
   statusTag.innerHTML = `<i class="fa-solid fa-ban" style="color:#ff3355"></i> Account banned${until} — ${escHtml(currentBan && currentBan.reason || "Cheating")}`;
  }
  return;
 }
 if (state === "download") {
  btn.classList.add("is-update");
  label.innerHTML = `<i class="fa-solid fa-download btn-play-icon"></i> DOWNLOAD GAME`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-cloud-arrow-down" style="color:#38bdf8"></i> Download available (9.4 GB)`;
  }
 } else if (state === "paused") {
  btn.classList.add("is-update");
  label.innerHTML = `<i class="fa-solid fa-play btn-play-icon"></i> ${customLabel || "CONTINUE DOWNLOAD"}`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-pause" style="color:#fbbf24"></i> Download paused — Ready to continue`;
  }
 } else if (state === "downloading") {
  btn.classList.add("is-updating");
  label.innerHTML = `<i class="fa-solid fa-pause btn-play-icon"></i> ${customLabel || "PAUSE DOWNLOAD"}`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color:#38bdf8"></i> Downloading game files...`;
  }
 } else if (state === "update") {
  btn.classList.add("is-update");
  label.innerHTML = `<i class="fa-solid fa-download btn-play-icon"></i> UPDATE`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-circle-arrow-up" style="color:#fbbf24"></i> Update available`;
  }
 } else if (state === "updating") {
  btn.classList.add("is-updating");
  label.innerHTML = `<i class="fa-solid fa-spinner fa-spin btn-play-icon"></i> ${customLabel || "UPDATING..."}`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color:#fbbf24"></i> Updating...`;
  }
 } else if (state === "launching") {
  btn.classList.add("is-launching");
  label.innerHTML = `<i class="fa-solid fa-spinner fa-spin btn-play-icon"></i> ${customLabel || "LAUNCHING..."}`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-purple"></i> Launching...`;
  }
 } else if (state === "running") {
  btn.classList.add("is-running");
  label.innerHTML = `<i class="fa-solid fa-gamepad btn-play-icon"></i> RUNNING`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-circle-check text-success"></i> Reawakening online`;
  }
 } else {
  label.innerHTML = `<i class="fa-solid fa-play btn-play-icon"></i> PLAY`;
  if (statusTag) {
   statusTag.innerHTML = `<i class="fa-solid fa-circle-check text-success"></i> Navy Games — Ready`;
  }
 }
}

function startLaunchStatusTracking() {
 if (statusPollTimer) clearInterval(statusPollTimer);
 let checkCount = 0;
 statusPollTimer = setInterval(async () => {
  checkCount++;
  try {
   const st = await getApi().get_launch_status();
   if (st.running && (st.ready || st.status === "lobby_ready" || st.status === "server_lobby_ready")) {
    isLaunching = false;
    isGameRunning = true;
    setPlayButtonState("running");
    if (!hasAutoMinimized) {
     hasAutoMinimized = true;
     showToast("Game started — lobby ready", "fa-gamepad");
    }
   } else if (st.running && isLaunching) {
    setPlayButtonState("launching");
   } else if (st.status === "failed") {
    clearInterval(statusPollTimer);
    isLaunching = false;
    isGameRunning = false;
    hasAutoMinimized = false;
    setPlayButtonState("idle");
    showToast(st.error || "Launch failed. Check logs.", "fa-triangle-exclamation");
   } else if (isLaunching) {
    setPlayButtonState("launching");
   }
   if (isGameRunning && !st.running && checkCount > 10) {
    isGameRunning = false;
    isLaunching = false;
    hasAutoMinimized = false;
    clearInterval(statusPollTimer);
    setPlayButtonState("idle");
    showToast("Cyber Hunter closed.", "fa-info-circle");
   }
  } catch (e) {
   console.error("Status polling error", e);
  }
 }, 1200);
}

let currentGfxQuality = 2;

let currentFpsLimit = 120;

function syncSettingsGraphicsUI(quality, fps) {
 const qualityNames = {
  0: "Very Low",
  1: "Low",
  2: "Medium",
  3: "Ultra"
 };
 const badgeQ = document.getElementById("gfxQualityBadge");
 if (badgeQ) badgeQ.textContent = qualityNames[quality] || "Medium";
 const badgeF = document.getElementById("fpsLimitBadge");
 if (badgeF) badgeF.textContent = `${fps} FPS`;
 document.querySelectorAll("#settingsGfxQualitySelector .env-mode-pill").forEach(btn => {
  if (parseInt(btn.dataset.quality) === quality) btn.classList.add("active"); else btn.classList.remove("active");
 });
 document.querySelectorAll("#settingsFpsSelector .env-mode-pill").forEach(btn => {
  if (parseInt(btn.dataset.fps) === fps) btn.classList.add("active"); else btn.classList.remove("active");
 });
}

function openGraphicsSetupModal() {
 playBeep(520, "sine", .08);
 const modal = document.getElementById("graphicsSetupModal");
 if (!modal) return;
 let q = signedInAccount && typeof signedInAccount.graphic_quality !== "undefined" ? signedInAccount.graphic_quality : currentConfig && typeof currentConfig.graphic_quality !== "undefined" ? currentConfig.graphic_quality : 2;
 let f = signedInAccount && typeof signedInAccount.fps_limit !== "undefined" ? signedInAccount.fps_limit : currentConfig && typeof currentConfig.fps_limit !== "undefined" ? currentConfig.fps_limit : 120;
 currentGfxQuality = parseInt(q) || 2;
 currentFpsLimit = parseInt(f) || 120;
 updateGraphicsSetupSelection(currentGfxQuality, currentFpsLimit);
 modal.classList.add("open");
}

function updateGraphicsSetupSelection(quality, fps) {
 currentGfxQuality = quality;
 currentFpsLimit = fps;
 const qualityNames = {
  0: "Very Low (Mode 0)",
  1: "Low (Mode 1)",
  2: "Medium (Mode 2)",
  3: "Ultra (Mode 3)"
 };
 const summaryQ = document.getElementById("gfxSummaryQuality");
 if (summaryQ) summaryQ.textContent = qualityNames[quality] || "Medium (Mode 2)";
 const summaryF = document.getElementById("gfxSummaryFps");
 if (summaryF) summaryF.textContent = `${fps} FPS`;
 document.querySelectorAll("#setupGfxCards .gfx-preset-card").forEach(card => {
  if (parseInt(card.dataset.quality) === quality) card.classList.add("active"); else card.classList.remove("active");
 });
 document.querySelectorAll("#setupFpsPills .fps-select-pill").forEach(pill => {
  if (parseInt(pill.dataset.fps) === fps) pill.classList.add("active"); else pill.classList.remove("active");
 });
}

function initGraphicsSetupModal() {
 const modal = document.getElementById("graphicsSetupModal");
 const btnClose = document.getElementById("btnCloseGraphicsSetup");
 const btnConfirm = document.getElementById("btnConfirmGraphicsSetup");
 const btnOpenWizard = document.getElementById("btnOpenSetupWizard");
 if (btnClose && modal) {
  btnClose.addEventListener("click", () => {
   modal.classList.remove("open");
  });
 }
 if (modal) {
  modal.addEventListener("click", e => {
   if (e.target === modal) modal.classList.remove("open");
  });
 }
 if (btnOpenWizard) {
  btnOpenWizard.addEventListener("click", () => {
   const settingsModal = document.getElementById("settingsModal");
   if (settingsModal) settingsModal.classList.remove("open");
   openGraphicsSetupModal();
  });
 }
 document.querySelectorAll("#setupGfxCards .gfx-preset-card").forEach(card => {
  card.addEventListener("click", async () => {
   playBeep(520, "sine", .08);
   const q = parseInt(card.dataset.quality);
   updateGraphicsSetupSelection(q, currentFpsLimit);
   try {
    await getApi().save_graphics_settings(q, currentFpsLimit, true);
    syncSettingsGraphicsUI(q, currentFpsLimit);
   } catch (_) {}
  });
 });
 document.querySelectorAll("#setupFpsPills .fps-select-pill").forEach(pill => {
  pill.addEventListener("click", async () => {
   playBeep(560, "sine", .08);
   const f = parseInt(pill.dataset.fps);
   updateGraphicsSetupSelection(currentGfxQuality, f);
   try {
    await getApi().save_graphics_settings(currentGfxQuality, f, true);
    syncSettingsGraphicsUI(currentGfxQuality, f);
   } catch (_) {}
  });
 });
 if (btnConfirm) {
  btnConfirm.addEventListener("click", async () => {
   playBeep(750, "sine", .12);
   btnConfirm.disabled = true;
   try {
    const res = await getApi().save_graphics_settings(currentGfxQuality, currentFpsLimit, true);
    if (signedInAccount) {
     signedInAccount.graphics_configured = true;
     signedInAccount.graphic_quality = currentGfxQuality;
     signedInAccount.fps_limit = currentFpsLimit;
    }
    if (currentConfig) {
     currentConfig.graphics_configured = true;
     currentConfig.graphic_quality = currentGfxQuality;
     currentConfig.fps_limit = currentFpsLimit;
    }
    syncSettingsGraphicsUI(currentGfxQuality, currentFpsLimit);
    if (modal) modal.classList.remove("open");
    const qNames = {
     0: "Very Low",
     1: "Low",
     2: "Medium",
     3: "Ultra"
    };
    showToast(`Graphics profile saved: ${currentFpsLimit} FPS (${qNames[currentGfxQuality] || "Medium"})`, "fa-circle-check");
    await triggerPlayLaunch();
   } catch (e) {
    showToast(String(e), "fa-triangle-exclamation");
   } finally {
    btnConfirm.disabled = false;
   }
  });
 }
}

function showOfflineModal(message, reason) {
 let modal = document.getElementById("offlineModal");
 if (!modal) {
  modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "offlineModal";
  modal.innerHTML = `\n      <div class="modal-box" style="max-width:500px; border:2px solid #ffb020; box-shadow:0 0 40px rgba(255,176,32,0.35); background:radial-gradient(circle at top, #1a150b, #09080c);">\n        <div class="modal-header" style="border-bottom:1px solid rgba(255,176,32,0.3); padding:16px 20px;">\n          <div class="modal-title" style="color:#ffb020; font-size:18px; font-weight:800; letter-spacing:1px;">\n            <i class="fa-solid fa-wifi"></i> CONNECTION REQUIRED\n          </div>\n          <button class="modal-close-btn" data-offline-close><i class="fa-solid fa-xmark"></i></button>\n        </div>\n        <div class="modal-body" style="padding:24px 20px; text-align:center;">\n          <div style="width:70px; height:70px; border-radius:50%; background:rgba(255,176,32,0.12); border:2px solid #ffb020; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; color:#ffb020; font-size:30px;">\n            <i class="fa-solid fa-plug-circle-xmark" id="offlineModalIcon"></i>\n          </div>\n          <h2 id="offlineModalTitle" style="color:#ffffff; font-family:var(--font-heading); font-size:24px; letter-spacing:2px; margin-bottom:12px; text-transform:uppercase;">CAN'T CONNECT</h2>\n          <p id="offlineModalMessage" style="color:var(--val-text-muted); font-size:14px; line-height:1.6; margin-bottom:20px;"></p>\n          <div style="display:flex; justify-content:center; gap:12px;">\n            <button type="button" class="tool-btn" data-offline-retry style="background:#ffb020; border:none; color:#111; padding:10px 28px; font-weight:700; border-radius:6px; cursor:pointer;">RETRY</button>\n            <button type="button" class="tool-btn" data-offline-close style="padding:10px 28px; font-weight:700; border-radius:6px; cursor:pointer;">CLOSE</button>\n          </div>\n        </div>\n      </div>`;
  document.body.appendChild(modal);
  modal.querySelectorAll("[data-offline-close]").forEach(b => b.addEventListener("click", () => modal.setAttribute("hidden", "")));
  modal.querySelector("[data-offline-retry]").addEventListener("click", async () => {
   modal.setAttribute("hidden", "");
   await triggerPlayLaunch();
  });
 }
 const msgEl = modal.querySelector("#offlineModalMessage");
 const titleEl = modal.querySelector("#offlineModalTitle");
 if (msgEl) msgEl.textContent = message || "Can't connect. Please connect to the internet.";
 if (titleEl) titleEl.textContent = reason === "server_down" ? "SERVER UNREACHABLE" : "CAN'T CONNECT";
 modal.removeAttribute("hidden");
}

async function triggerPlayLaunch() {
 if (isLaunching) {
  showToast("Launch sequence already in progress...", "fa-clock");
  return;
 }
 if (isGameRunning) {
  showToast("Cyber Hunter is already running!", "fa-gamepad");
  return;
 }
 isLaunching = true;
 setPlayButtonState("launching", "LAUNCHING...");
 showToast("Launching Cyber Hunter...", "fa-rocket");
 try {
  const res = await getApi().launch_game();
  if (res && res.banned) {
   isLaunching = false;
   applyBanState({
    banned: true,
    reason: res.reason,
    ban_type: res.ban_type,
    expires_at: res.expires_at || 0
   });
   setPlayButtonState("idle");
   showBannedModal(currentBan);
   showToast("Access denied: your account is banned.", "fa-ban");
   return;
  }
  if (res && res.offline) {
   isLaunching = false;
   setPlayButtonState("idle");
   showToast(res.message || "Can't connect. Please connect to the internet.", "fa-wifi");
   showOfflineModal(res.message, res.reason);
   return;
  }
  if (res && res.success) {
   showToast(res.message || "Suite initializing...", "fa-circle-check");
   startLaunchStatusTracking();
  } else {
   isLaunching = false;
   setPlayButtonState("idle");
   showToast(res && res.message || "Launch failed", "fa-triangle-exclamation");
  }
 } catch (err) {
  isLaunching = false;
  setPlayButtonState("idle");
  showToast(String(err), "fa-triangle-exclamation");
 }
}

function initActions() {
 const btnPlayMain = document.getElementById("btnPlayMain");
 const comingSoonModal = document.getElementById("comingSoonModal");
 const btnCloseComingSoon = document.getElementById("btnCloseComingSoon");
 const btnJoinDiscordModal = document.getElementById("btnJoinDiscordModal");
 if (btnPlayMain) {
  btnPlayMain.addEventListener("click", async () => {
   playBeep(650, "sine", .12);
   if (isGameDownloading) {
    await pauseGameDownload();
    return;
   }
   if (currentBan && currentBan.banned) {
    showBannedModal(currentBan);
    showToast("Your account is banned. You cannot launch the game.", "fa-ban");
    return;
   }
   if (!signedInAccount) {
    showToast("Please sign in first to download or play the game.", "fa-user-lock");
    if (window.openAccountModal) {
     window.openAccountModal("Please sign in to your account to download or play.");
    }
    return;
   }
   if (!gameInstalled) {
    startGameDownload();
    return;
   }
   if (isUpdating) {
    showToast("Update in progress — please wait.", "fa-download");
    return;
   }
   if (updateAvailable && !isLaunching && !isGameRunning) {
    startGameUpdate();
    return;
   }
   openGraphicsSetupModal();
  });
 }
 const btnDownloadPauseToggle = document.getElementById("btnDownloadPauseToggle");
 if (btnDownloadPauseToggle) {
  btnDownloadPauseToggle.addEventListener("click", async e => {
   e.stopPropagation();
   playBeep(650, "sine", .12);
   if (isGameDownloading) {
    await pauseGameDownload();
   } else {
    await startGameDownload();
   }
  });
 }
 if (btnCloseComingSoon && comingSoonModal) {
  btnCloseComingSoon.addEventListener("click", () => {
   comingSoonModal.classList.remove("open");
  });
 }
 if (comingSoonModal) {
  comingSoonModal.addEventListener("click", e => {
   if (e.target === comingSoonModal) {
    comingSoonModal.classList.remove("open");
   }
  });
 }
 if (btnJoinDiscordModal) {
  btnJoinDiscordModal.addEventListener("click", async () => {
   playBeep(780, "sine", .12);
   const url = btnJoinDiscordModal.dataset.url || "https://discord.gg/uXc8frbz5Y";
   await getApi().open_external_url(url);
   showToast("Opening Official Cyber Hunter Discord...", "fa-brands fa-discord");
  });
 }
 const linkOpenControlPanel = document.getElementById("linkOpenControlPanel");
 if (linkOpenControlPanel) {
  linkOpenControlPanel.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   if (window.__openMasterConsole) window.__openMasterConsole();
   const masterBtn = document.getElementById("railBtnMaster");
   const allGamesBtn = document.getElementById("railBtnAllGames");
   if (masterBtn) masterBtn.classList.add("active");
   if (allGamesBtn) allGamesBtn.classList.remove("active");
   document.querySelectorAll(".rail-game-btn").forEach(b => b.classList.remove("active"));
  });
 }
 const linkSpawnHydrofoil = document.getElementById("linkSpawnHydrofoil");
 if (linkSpawnHydrofoil) {
  linkSpawnHydrofoil.addEventListener("click", async () => {
   playBeep(620, "sine", .1);
   showToast("Spawning Flying Hydrofoil (Titanium)...", "fa-jet-fighter");
   try {
    const res = await getApi().spawn_hydrofoil();
    showToast(res && res.message || "Hydrofoil spawn command sent!", res && res.success ? "fa-circle-check" : "fa-triangle-exclamation");
   } catch (e) {
    showToast(String(e), "fa-triangle-exclamation");
   }
  });
 }
 const linkCheckFiles = document.getElementById("linkCheckFiles");
 if (linkCheckFiles) {
  linkCheckFiles.addEventListener("click", async () => {
   showToast("Verifying game files integrity...", "fa-wrench");
   const res = await getApi().verify_game_files();
   showToast(res.message, "fa-circle-check");
  });
 }
}

const UPDATE_CHECK_INTERVAL_MS = 5 * 60 * 1e3;

let updateCheckTimer = null;

let updatePollTimer = null;

function formatBytes(n) {
 n = Number(n) || 0;
 if (n >= 1024 * 1024 * 1024) return (n / (1024 * 1024 * 1024)).toFixed(2) + " GB";
 if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + " MB";
 if (n >= 1024) return (n / 1024).toFixed(0) + " KB";
 return n.toFixed(0) + " B";
}

function renderUpdateProgress(st) {
 const box = document.getElementById("updateProgress");
 if (!box) return;
 if (!st) {
  box.hidden = true;
  return;
 }
 box.hidden = false;
 const pct = Math.max(0, Math.min(100, Number(st.percent) || 0));
 const fill = document.getElementById("updateProgressFill");
 const phase = document.getElementById("updateProgressPhase");
 const pctEl = document.getElementById("updateProgressPct");
 const size = document.getElementById("updateProgressSize");
 const speed = document.getElementById("updateProgressSpeed");
 if (fill) fill.style.width = pct.toFixed(1) + "%";
 if (phase) phase.textContent = st.phase || "Updating...";
 if (pctEl) pctEl.textContent = Math.floor(pct) + "%";
 if (size) {
  const total = st.total_bytes ? formatBytes(st.total_bytes) : "-- MB";
  const left = st.total_bytes ? " (" + formatBytes(Math.max(0, st.total_bytes - st.received_bytes)) + " left)" : "";
  size.textContent = formatBytes(st.received_bytes) + " / " + total + left;
 }
 if (speed) speed.textContent = st.speed_bps ? formatBytes(st.speed_bps) + "/s" : "-- MB/s";
 const btnPauseToggle = document.getElementById("btnDownloadPauseToggle");
 if (btnPauseToggle) {
  if (st.status === "extracting" || st.status === "done") {
   btnPauseToggle.style.display = "none";
  } else {
   btnPauseToggle.style.display = "inline-flex";
   if (st.status === "paused") {
    btnPauseToggle.innerHTML = '<i class="fa-solid fa-play"></i> <span>Resume</span>';
    btnPauseToggle.classList.add("is-resume");
   } else {
    btnPauseToggle.innerHTML = '<i class="fa-solid fa-pause"></i> <span>Pause</span>';
    btnPauseToggle.classList.remove("is-resume");
   }
  }
 }
}

async function checkForUpdate() {
 if (isUpdating || isLaunching || isGameRunning) return;
 try {
  const api = getApi();
  if (!api || !api.check_for_update) return;
  const st = await api.check_for_update();
  const was = updateAvailable;
  updateAvailable = !!(st && st.status === "available");
  if (updateAvailable !== was && !isLaunching && !isGameRunning) {
   setPlayButtonState("idle");
   if (updateAvailable) showToast("A new update is available. Click UPDATE.", "fa-circle-arrow-up");
  }
 } catch (e) {
  console.error("update check failed", e);
 }
}

function startUpdateCheck() {
 checkForUpdate();
 if (updateCheckTimer) clearInterval(updateCheckTimer);
 updateCheckTimer = setInterval(checkForUpdate, UPDATE_CHECK_INTERVAL_MS);
}

async function startGameUpdate() {
 const api = getApi();
 if (!api || !api.start_update) return;
 const res = await api.start_update();
 if (!res || !res.success) {
  showToast(res && res.message || "Could not start update.", "fa-triangle-exclamation");
  return;
 }
 isUpdating = true;
 setPlayButtonState("updating");
 renderUpdateProgress({
  phase: "Connecting...",
  percent: 0
 });
 if (updatePollTimer) clearInterval(updatePollTimer);
 updatePollTimer = setInterval(async () => {
  let st;
  try {
   st = await api.get_update_state();
  } catch (e) {
   return;
  }
  if (!st) return;
  if (st.status === "updating") {
   renderUpdateProgress(st);
   setPlayButtonState("updating", "UPDATING " + Math.floor(Number(st.percent) || 0) + "%");
   return;
  }
  clearInterval(updatePollTimer);
  updatePollTimer = null;
  isUpdating = false;
  if (st.status === "done") {
   updateAvailable = false;
   renderUpdateProgress(st);
   setPlayButtonState("idle");
   if (st.launcher_changed && api.restart_launcher) {
    showToast("Update installed. Restarting launcher...", "fa-rotate");
    setTimeout(() => api.restart_launcher(), 1500);
   } else {
    showToast("Update installed. Ready to play!", "fa-circle-check");
    setTimeout(() => renderUpdateProgress(null), 4e3);
   }
  } else {
   renderUpdateProgress(null);
   setPlayButtonState("idle");
   showToast(st.message || "Update failed.", "fa-triangle-exclamation");
  }
 }, 500);
}

async function checkGameInstalled() {
 try {
  const api = getApi();
  if (!api || !api.is_game_installed) return true;
  const installed = await api.is_game_installed();
  gameInstalled = !!installed;
  if (!gameInstalled) {
   let st = null;
   if (api.get_game_download_state) {
    try {
     st = await api.get_game_download_state();
    } catch (e) {}
   }
   if (st && (st.status === "paused" || st.status === "downloading" || Number(st.percent) > 0 && st.status !== "done")) {
    isGameDownloading = false;
    setPlayButtonState("paused", "CONTINUE DOWNLOAD");
    renderUpdateProgress(st);
   } else if (!isLaunching && !isGameRunning) {
    setPlayButtonState("download");
   }
  }
  return gameInstalled;
 } catch (e) {
  console.error("checkGameInstalled failed", e);
  return true;
 }
}

async function startGameDownload() {
 if (!signedInAccount) {
  showToast("Please sign in first to download or play the game.", "fa-user-lock");
  if (window.openAccountModal) {
   window.openAccountModal("Please sign in to your account to download or play.");
  }
  return;
 }
 const api = getApi();
 if (!api || !api.start_game_download) return;
 const res = await api.start_game_download();
 if (!res || !res.success) {
  showToast(res && res.message || "Could not start download.", "fa-triangle-exclamation");
  return;
 }
 isGameDownloading = true;
 setPlayButtonState("downloading", "CONNECTING...");
 renderUpdateProgress({
  phase: "Connecting to game server...",
  percent: 0
 });
 if (gameDownloadPollTimer) clearInterval(gameDownloadPollTimer);
 gameDownloadPollTimer = setInterval(async () => {
  let st;
  try {
   st = await api.get_game_download_state();
  } catch (e) {
   return;
  }
  if (!st) return;
  if (st.status === "downloading" || st.status === "extracting") {
   renderUpdateProgress(st);
   const actionLabel = st.status === "extracting" ? "EXTRACTING " : "DOWNLOADING ";
   setPlayButtonState("downloading", actionLabel + Math.floor(Number(st.percent) || 0) + "%");
   return;
  }
  if (st.status === "paused") {
   clearInterval(gameDownloadPollTimer);
   gameDownloadPollTimer = null;
   isGameDownloading = false;
   renderUpdateProgress(st);
   setPlayButtonState("paused", "CONTINUE DOWNLOAD");
   return;
  }
  clearInterval(gameDownloadPollTimer);
  gameDownloadPollTimer = null;
  isGameDownloading = false;
  if (st.status === "done") {
   gameInstalled = true;
   if (st.game_path) {
    currentConfig.game_path = st.game_path;
    const el = document.getElementById("inputGamePath");
    if (el) el.value = st.game_path;
   }
   renderUpdateProgress(st);
   setPlayButtonState("idle");
   showToast("Cyber Hunter downloaded and installed! Ready to play.", "fa-circle-check");
   setTimeout(() => renderUpdateProgress(null), 5e3);
  } else {
   renderUpdateProgress(null);
   setPlayButtonState((st.received_bytes || 0) > 0 ? "paused" : "download");
   showToast(st.message || "Download failed. Please try again.", "fa-triangle-exclamation");
  }
 }, 400);
}

async function pauseGameDownload() {
 const api = getApi();
 if (!api || !api.pause_game_download) return;
 const res = await api.pause_game_download();
 if (res && res.success) {
  isGameDownloading = false;
  if (gameDownloadPollTimer) {
   clearInterval(gameDownloadPollTimer);
   gameDownloadPollTimer = null;
  }
  setPlayButtonState("paused", "CONTINUE DOWNLOAD");
  let st = null;
  try {
   st = await api.get_game_download_state();
  } catch (e) {}
  renderUpdateProgress(st || {
   status: "paused",
   phase: "Download paused"
  });
  showToast("Download paused. Click Continue Download to resume.", "fa-pause");
 }
}

function startServerPoll() {
 checkServer();
 if (serverPollTimer) clearInterval(serverPollTimer);
 serverPollTimer = setInterval(checkServer, 5e3);
 const btnServerQuick = document.getElementById("btnServerQuick");
 const serverTargetBadge = document.getElementById("serverTargetBadge");
 const onServerClick = async () => {
  try {
   const res = await getApi().check_server_status();
   const statusStr = res.online ? "Online" : "Standby";
   showToast(`Reawakening Server — ${statusStr}`, res.online ? "fa-circle-check" : "fa-server");
  } catch (_) {}
 };
 if (btnServerQuick && !btnServerQuick.__bound) {
  btnServerQuick.__bound = true;
  btnServerQuick.addEventListener("click", onServerClick);
 }
 if (serverTargetBadge && !serverTargetBadge.__bound) {
  serverTargetBadge.__bound = true;
  serverTargetBadge.addEventListener("click", onServerClick);
 }
}

async function checkServer() {
 try {
  const res = await getApi().check_server_status();
  const serverDot = document.getElementById("serverDot");
  const serverText = document.getElementById("serverText");
  const serverTargetBadge = document.getElementById("serverTargetBadge");
  const serverTargetText = document.getElementById("serverTargetText");
  const btnServerQuick = document.getElementById("btnServerQuick");
  const isRemote = res.is_remote || res.server_ip && res.server_ip !== "127.0.0.1" && res.server_ip !== "localhost";
  if (serverText) {
   serverText.textContent = "STATUS: REAWAKENING SERVER";
  }
  if (res.online) {
   if (serverDot) serverDot.className = `server-dot online ${isRemote ? "remote" : ""}`;
   if (serverTargetBadge) {
    serverTargetBadge.className = `server-target-badge online ${isRemote ? "remote" : "local"}`;
    serverTargetBadge.title = `Reawakening Server · Online`;
   }
   if (serverTargetText) {
    serverTargetText.textContent = `Reawakening Server (Online)`;
   }
   if (btnServerQuick) {
    btnServerQuick.title = `Reawakening Server — Online`;
   }
  } else {
   if (serverDot) serverDot.className = "server-dot offline";
   if (serverTargetBadge) {
    serverTargetBadge.className = "server-target-badge offline";
    serverTargetBadge.title = `Reawakening Server · Standby`;
   }
   if (serverTargetText) {
    serverTargetText.textContent = `Reawakening Server (Standby)`;
   }
   if (btnServerQuick) {
    btnServerQuick.title = `Reawakening Server — Standby`;
   }
  }
 } catch (e) {}
}

function initSocial() {
 const links = document.querySelectorAll(".social-link");
 links.forEach(l => {
  l.addEventListener("click", async e => {
   e.preventDefault();
   playBeep(580, "sine", .05);
   const url = l.dataset.url;
   if (url) await getApi().open_external_url(url);
  });
 });
}

function initTitlebar() {
 const btnMin = document.getElementById("btnMinimize");
 const btnClose = document.getElementById("btnClose");
 const btnMaster = document.getElementById("btnOpenMaster");
 if (btnMin) {
  btnMin.addEventListener("click", async () => {
   await getApi().minimize_window();
  });
 }
 if (btnClose) {
  btnClose.addEventListener("click", async () => {
   await getApi().close_window();
  });
 }
 if (btnMaster) {
  btnMaster.addEventListener("click", () => {
   const isDev = !!(signedInAccount && signedInAccount.is_dev);
   if (!isDev) {
    showToast("Developer mode required for Control Panel.", "fa-shield-halved");
    return;
   }
   playBeep(520, "sine", .08);
   if (window.__openMasterConsole) window.__openMasterConsole();
   const masterBtn = document.getElementById("railBtnMaster");
   const allGamesBtn = document.getElementById("railBtnAllGames");
   if (masterBtn) masterBtn.classList.add("active");
   if (allGamesBtn) allGamesBtn.classList.remove("active");
   document.querySelectorAll(".rail-game-btn").forEach(b => b.classList.remove("active"));
  });
 }
}

async function loadConfiguration() {
 try {
  currentConfig = await getApi().get_config();
  const inputPath = document.getElementById("inputGamePath");
  const inputUrl = document.getElementById("inputServerUrl");
  const toggleAuto = document.getElementById("toggleAutoServer");
  const toggleClose = document.getElementById("toggleCloseOnLaunch");
  if (inputPath) inputPath.value = currentConfig.game_path || "";
  if (inputUrl) inputUrl.value = currentConfig.server_url || "http://136.64.14.144:8888";
  if (toggleAuto) toggleAuto.checked = !!currentConfig.auto_server;
  if (toggleClose) toggleClose.checked = !!currentConfig.close_on_launch;
  const inputFov = document.getElementById("inputFov");
  const fovBadge = document.getElementById("fovValueBadge");
  const fovVal = currentConfig && typeof currentConfig.fov !== "undefined" ? parseInt(currentConfig.fov) : 60;
  if (inputFov) inputFov.value = fovVal;
  if (fovBadge) fovBadge.textContent = `${fovVal}°`;
  let envMode = currentConfig.env_mode;
  if (!envMode) {
   if (typeof currentConfig.auto_weather !== "undefined" && currentConfig.auto_weather) {
    envMode = "auto";
   } else if (typeof currentConfig.night_mode !== "undefined") {
    envMode = currentConfig.night_mode ? "night" : "day";
   }
  }
  if (!envMode) {
   try {
    const st = await getApi().get_day_night_state();
    if (st && st.mode) envMode = st.mode; else if (st && typeof st.night !== "undefined") envMode = st.night ? "night" : "day";
   } catch (_) {}
  }
  if (!envMode) envMode = "day";
  updateDayNightUI(envMode);
  const qVal = currentConfig && typeof currentConfig.graphic_quality !== "undefined" ? parseInt(currentConfig.graphic_quality) : 2;
  const fpsVal = currentConfig && typeof currentConfig.fps_limit !== "undefined" ? parseInt(currentConfig.fps_limit) : 120;
  syncSettingsGraphicsUI(qVal, fpsVal);
 } catch (e) {
  console.error("Failed loading configuration", e);
 }
}

function updateDayNightUI(mode) {
 if (typeof mode === "boolean") {
  mode = mode ? "night" : "day";
 }
 mode = (mode || "night").toLowerCase();
 const meta = {
  auto: {
   label: "AI Weather (Auto)",
   badge: "AI Weather Active (Random 1 Weather Per Match)",
   icon: "fa-solid fa-wand-magic-sparkles",
   color: "#38bdf8"
  },
  day: {
   label: "Day Sky (F10)",
   badge: "Day Sky Active (Clear Sun)",
   icon: "fa-solid fa-sun",
   color: "#facc15"
  },
  dawn: {
   label: "Dawn Sky (F10)",
   badge: "Dawn Sky Active (Soft Peach)",
   icon: "fa-solid fa-cloud-sun",
   color: "#ff9a8b"
  },
  sunset: {
   label: "Sunset Sky (F10)",
   badge: "Sunset Sky Active (Golden Orange)",
   icon: "fa-solid fa-mountain-sun",
   color: "#ff7020"
  },
  autumn: {
   label: "Autumn Weather (F10)",
   badge: "Autumn Weather Active (Orange Foliage & Sunset)",
   icon: "fa-solid fa-leaf",
   color: "#f97316"
  },
  night: {
   label: "Night Sky (F10)",
   badge: "Night Sky Active (Stars & Moon)",
   icon: "fa-solid fa-moon",
   color: "#815eff"
  },
  rain: {
   label: "Rain Weather (F10)",
   badge: "Rain Weather Active (Overcast Storm)",
   icon: "fa-solid fa-cloud-showers-heavy",
   color: "#38bdf8"
  },
  rainy_night: {
   label: "Rainy Night (F10)",
   badge: "Rainy Night Active (Dark Storm)",
   icon: "fa-solid fa-cloud-moon-rain",
   color: "#7cb3f2"
  },
  snow: {
   label: "Snow Weather (F10)",
   badge: "Snow Day Active (Winter World)",
   icon: "fa-solid fa-snowflake",
   color: "#c7e9fe"
  },
  snowy_night: {
   label: "Snowy Night (F10)",
   badge: "Snowy Night Active (Winter Night)",
   icon: "fa-solid fa-icicles",
   color: "#93c5fd"
  }
 }[mode] || {
  label: "AI Weather (Auto)",
  badge: "AI Weather Active (Random 1 Weather Per Match)",
  icon: "fa-solid fa-wand-magic-sparkles",
  color: "#38bdf8"
 };
 const quickLabel = document.getElementById("quickDayNightLabel");
 const quickIcon = document.getElementById("quickDayNightIcon");
 const badgeText = document.getElementById("badgeDayNightText");
 const badgeIcon = document.getElementById("badgeDayNightIcon");
 if (quickLabel) quickLabel.textContent = meta.label;
 if (quickIcon) {
  quickIcon.className = meta.icon;
  quickIcon.style.color = meta.color;
 }
 if (badgeText) badgeText.textContent = meta.badge;
 if (badgeIcon) {
  badgeIcon.className = meta.icon;
  badgeIcon.style.color = meta.color;
 }
 document.querySelectorAll(".env-mode-pill").forEach(pill => {
  if (pill.dataset.mode === mode) {
   pill.classList.add("active");
  } else {
   pill.classList.remove("active");
  }
 });
}

async function toggleDayNightMode(target) {
 playBeep(520, "sine", .08);
 try {
  const res = await getApi().toggle_day_night(target);
  if (res && res.success) {
   const mode = res.mode || (res.night ? "night" : "day");
   updateDayNightUI(mode);
   if (currentConfig) {
    currentConfig.env_mode = mode;
    currentConfig.auto_weather = mode === "auto";
    currentConfig.night_mode = [ "night", "rainy_night", "snowy_night" ].includes(mode);
    currentConfig.rain_mode = [ "rain", "rainy_night" ].includes(mode);
    currentConfig.snow_mode = [ "snow", "snowy_night" ].includes(mode);
   }
   const iconMap = {
    auto: "fa-wand-magic-sparkles",
    day: "fa-sun",
    dawn: "fa-cloud-sun",
    sunset: "fa-mountain-sun",
    autumn: "fa-leaf",
    night: "fa-moon",
    rain: "fa-cloud-showers-heavy",
    rainy_night: "fa-cloud-moon-rain",
    snow: "fa-snowflake",
    snowy_night: "fa-icicles"
   };
   showToast(res.message + (res.client_running ? " (applied live in match)" : ""), iconMap[mode] || "fa-wand-magic-sparkles");
  }
 } catch (err) {
  showToast(String(err), "fa-triangle-exclamation");
 }
}

function initSettingsModal() {
 const modal = document.getElementById("settingsModal");
 const btnOpen = document.getElementById("btnOpenSettings");
 const btnClose = document.getElementById("btnCloseSettings");
 const btnSave = document.getElementById("btnSaveSettings");
 const btnBrowse = document.getElementById("btnBrowseGamePath");
 const btnCheck = document.getElementById("btnCheckServer");
 const linkDayNight = document.getElementById("linkToggleDayNight");
 document.querySelectorAll(".env-mode-pill").forEach(pill => {
  pill.addEventListener("click", () => {
   const m = pill.dataset.mode;
   if (m) toggleDayNightMode(m);
  });
 });
 if (linkDayNight) {
  linkDayNight.addEventListener("click", () => toggleDayNightMode());
 }
 const inputFov = document.getElementById("inputFov");
 const fovBadge = document.getElementById("fovValueBadge");
 const btnResetFov = document.getElementById("btnResetFov");
 if (inputFov) {
  inputFov.addEventListener("input", e => {
   const val = parseInt(e.target.value) || 60;
   if (fovBadge) fovBadge.textContent = `${val}°`;
   if (currentConfig) currentConfig.fov = val;
   try {
    if (typeof isGameRunning !== "undefined" && isGameRunning) {
     getApi().set_fov(val);
    }
   } catch (_) {}
  });
 }
 if (btnResetFov) {
  btnResetFov.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   const defVal = 60;
   if (inputFov) inputFov.value = defVal;
   if (fovBadge) fovBadge.textContent = `${defVal}°`;
   if (currentConfig) currentConfig.fov = defVal;
   try {
    if (typeof isGameRunning !== "undefined" && isGameRunning) {
     getApi().set_fov(defVal);
    }
   } catch (_) {}
   showToast("FOV reset to normal (60°)", "fa-rotate-left");
  });
 }
 document.querySelectorAll("#settingsGfxQualitySelector .env-mode-pill").forEach(pill => {
  pill.addEventListener("click", async () => {
   playBeep(520, "sine", .08);
   const q = parseInt(pill.dataset.quality);
   const fpsPill = document.querySelector("#settingsFpsSelector .env-mode-pill.active");
   const f = fpsPill ? parseInt(fpsPill.dataset.fps) : currentConfig && currentConfig.fps_limit || 120;
   syncSettingsGraphicsUI(q, f);
   try {
    const res = await getApi().save_graphics_settings(q, f, true);
    if (res && res.success) {
     if (currentConfig) {
      currentConfig.graphic_quality = q;
      currentConfig.fps_limit = f;
     }
     const qNames = {
      0: "Very Low",
      1: "Low",
      2: "Medium",
      3: "Ultra"
     };
     const live = typeof isGameRunning !== "undefined" && isGameRunning;
     showToast(live ? `Graphics → ${qNames[q] || "Medium"} applied to game` : `Graphics preset saved: ${qNames[q] || "Medium"}`, live ? "fa-circle-check" : "fa-floppy-disk");
    }
   } catch (_) {}
  });
 });
 document.querySelectorAll("#settingsFpsSelector .env-mode-pill").forEach(pill => {
  pill.addEventListener("click", async () => {
   playBeep(560, "sine", .08);
   const f = parseInt(pill.dataset.fps);
   const gfxPill = document.querySelector("#settingsGfxQualitySelector .env-mode-pill.active");
   const q = gfxPill ? parseInt(gfxPill.dataset.quality) : currentConfig && currentConfig.graphic_quality || 2;
   syncSettingsGraphicsUI(q, f);
   try {
    const res = await getApi().save_graphics_settings(q, f, true);
    if (res && res.success) {
     if (currentConfig) {
      currentConfig.graphic_quality = q;
      currentConfig.fps_limit = f;
     }
     const live = typeof isGameRunning !== "undefined" && isGameRunning;
     showToast(live ? `FPS → ${f} FPS applied to game` : `FPS limit saved: ${f} FPS`, live ? "fa-circle-check" : "fa-floppy-disk");
    }
   } catch (_) {}
  });
 });
 [ [ "btnOpenInstaller", "open_installer", "Opening installer..." ] ].forEach(([id, method, busy]) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("click", async () => {
   showToast(busy, "fa-hourglass-half");
   try {
    const res = await getApi()[method]();
    showToast(res && res.message || "Done", res && res.success ? "fa-circle-check" : "fa-triangle-exclamation");
   } catch (err) {
    showToast(String(err), "fa-triangle-exclamation");
   }
  });
 });
 const btnAccount = document.getElementById("btnOpenAccount");
 if (btnAccount) {
  btnAccount.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   if (modal) modal.classList.remove("open");
   if (typeof window.openAccountModal === "function") {
    window.openAccountModal();
   } else {
    showToast("Account panel unavailable", "fa-triangle-exclamation");
   }
  });
 }
 const btnSettingsOpenProf = document.getElementById("btnSettingsOpenProfile");
 if (btnSettingsOpenProf) {
  btnSettingsOpenProf.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   if (modal) modal.classList.remove("open");
   if (typeof window.openAccountModal === "function") {
    window.openAccountModal(null, "profile");
   } else {
    showToast("Profile panel unavailable", "fa-triangle-exclamation");
   }
  });
 }
 const btnSpawnMapper = document.getElementById("btnOpenSpawnMapper");
 if (btnSpawnMapper) {
  btnSpawnMapper.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   if (modal) modal.classList.remove("open");
   if (typeof window.openSpawnMapper === "function") {
    window.openSpawnMapper();
   } else {
    showToast("Spawn Mapper unavailable", "fa-triangle-exclamation");
   }
  });
 }
 const btnSpawnHydrofoilTool = document.getElementById("btnSpawnHydrofoilTool");
 if (btnSpawnHydrofoilTool) {
  btnSpawnHydrofoilTool.addEventListener("click", async () => {
   playBeep(620, "sine", .1);
   if (modal) modal.classList.remove("open");
   showToast("Spawning Flying Hydrofoil (Titanium)...", "fa-jet-fighter");
   try {
    const res = await getApi().spawn_hydrofoil();
    showToast(res && res.message || "Hydrofoil spawn command sent!", res && res.success ? "fa-circle-check" : "fa-triangle-exclamation");
   } catch (err) {
    showToast(String(err), "fa-triangle-exclamation");
   }
  });
 }
 const recMap = [ {
  id: "btnRecMovement",
  ch: "movement",
  label: "Player Movements"
 }, {
  id: "btnRecCountdown",
  ch: "countdown",
  label: "Countdown Warmup"
 }, {
  id: "btnRecCombat",
  ch: "combat",
  label: "Combat Triggers"
 }, {
  id: "btnRecLooting",
  ch: "looting",
  label: "Looting Animations"
 }, {
  id: "btnRecLanding",
  ch: "plane_landing",
  label: "Plane Jumping & Landing"
 } ];
 const updateRecUi = async () => {
  try {
   const st = await getApi().get_recording_state();
   if (!st) return;
   const activeChs = new Set(st.channels || []);
   recMap.forEach(({id: id, ch: ch}) => {
    const el = document.getElementById(id);
    if (el) {
     if (st.recording && activeChs.has(ch)) {
      el.classList.add("is-recording");
     } else {
      el.classList.remove("is-recording");
     }
    }
   });
   const btnAnalyze = document.getElementById("btnAnalyzeProfile");
   if (btnAnalyze) {
    if (st.has_profile) btnAnalyze.classList.add("is-trained"); else btnAnalyze.classList.remove("is-trained");
   }
  } catch (e) {}
 };
 recMap.forEach(({id: id, ch: ch, label: label}) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("click", async () => {
   playBeep(440, "sine", .06);
   try {
    const res = await getApi().toggle_recording(ch);
    if (res && res.success) {
     showToast(res.message, res.recording ? "fa-record-vinyl" : "fa-circle-stop");
    }
    await updateRecUi();
   } catch (err) {
    showToast(String(err), "fa-triangle-exclamation");
   }
  });
 });
 const btnAnalyze = document.getElementById("btnAnalyzeProfile");
 if (btnAnalyze) {
  btnAnalyze.addEventListener("click", async () => {
   playBeep(660, "sine", .1);
   showToast("Compiling player telemetry & training bot AI...", "fa-hourglass-half");
   try {
    const res = await getApi().analyze_recordings();
    if (res && res.success) {
     showToast(res.message, "fa-circle-check");
     btnAnalyze.classList.add("is-trained");
    } else {
     showToast(res && res.message || "Analysis failed", "fa-triangle-exclamation");
    }
   } catch (err) {
    showToast(String(err), "fa-triangle-exclamation");
   }
  });
 }
 if (btnOpen) {
  btnOpen.addEventListener("click", () => {
   updateRecUi();
  });
 }
 const btnVerify = document.getElementById("btnVerifyFiles");
 const btnOpenDir = document.getElementById("btnOpenGameDir");
 if (btnOpen && modal) {
  btnOpen.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   const q = currentConfig && typeof currentConfig.graphic_quality !== "undefined" ? currentConfig.graphic_quality : 2;
   const f = currentConfig && typeof currentConfig.fps_limit !== "undefined" ? currentConfig.fps_limit : 120;
   syncSettingsGraphicsUI(q, f);
   modal.classList.add("open");
   if (signedInAccount && signedInAccount.is_dev) {
    if (window.refreshTesterList) window.refreshTesterList();
    if (window.refreshBanList) window.refreshBanList();
   }
   getApi().get_config().then(cfg => {
    const el = document.getElementById("inputGamePath");
    if (cfg && el && cfg.game_path && !el.value) el.value = cfg.game_path;
   }).catch(() => {});
  });
 }
 if (btnClose && modal) {
  btnClose.addEventListener("click", () => {
   modal.classList.remove("open");
  });
 }
 if (modal) {
  modal.addEventListener("click", e => {
   if (e.target === modal) modal.classList.remove("open");
  });
 }
 if (btnBrowse) {
  btnBrowse.addEventListener("click", async () => {
   const selected = await getApi().browse_game_path();
   if (selected) {
    document.getElementById("inputGamePath").value = selected;
   }
  });
 }
 if (btnCheck) {
  btnCheck.addEventListener("click", async () => {
   await checkServer();
   showToast("Server ping check completed", "fa-satellite-dish");
  });
 }
 if (btnVerify) {
  btnVerify.addEventListener("click", async () => {
   showToast("Starting full game assets verification...", "fa-wrench");
   const res = await getApi().verify_game_files();
   showToast(res.message, "fa-circle-check");
  });
 }
 if (btnOpenDir) {
  btnOpenDir.addEventListener("click", async () => {
   await getApi().open_game_directory();
   showToast("Opened installation directory", "fa-folder");
  });
 }
 if (btnSave && modal) {
  btnSave.addEventListener("click", async () => {
   playBeep(750, "sine", .12);
   const activePill = document.querySelector(".env-mode-pill.active");
   const selectedEnv = activePill && activePill.dataset.mode || currentConfig.env_mode || "day";
   const isNight = [ "night", "rainy_night", "snowy_night" ].includes(selectedEnv);
   const isRain = [ "rain", "rainy_night" ].includes(selectedEnv);
   const isSnow = [ "snow", "snowy_night" ].includes(selectedEnv);
   const isAuto = selectedEnv === "auto";
   const inputGamePathEl = document.getElementById("inputGamePath");
   const inputServerUrlEl = document.getElementById("inputServerUrl");
   const toggleAutoServerEl = document.getElementById("toggleAutoServer");
   const toggleCloseOnLaunchEl = document.getElementById("toggleCloseOnLaunch");
   const inputFovEl = document.getElementById("inputFov");
   const selectedFov = inputFovEl ? parseInt(inputFovEl.value) || 60 : currentConfig.fov || 60;
   const activeGfx = document.querySelector("#settingsGfxQualitySelector .env-mode-pill.active");
   const selectedGfx = activeGfx ? parseInt(activeGfx.dataset.quality) : (currentConfig && currentConfig.graphic_quality) ?? 2;
   const activeFps = document.querySelector("#settingsFpsSelector .env-mode-pill.active");
   const selectedFps = activeFps ? parseInt(activeFps.dataset.fps) : (currentConfig && currentConfig.fps_limit) ?? 120;
   const newConfig = Object.assign({}, currentConfig, {
    game_path: inputGamePathEl ? inputGamePathEl.value : currentConfig.game_path || "",
    server_url: inputServerUrlEl ? inputServerUrlEl.value : currentConfig.server_url || "http://136.64.14.144:8888",
    auto_server: toggleAutoServerEl ? toggleAutoServerEl.checked : !!currentConfig.auto_server,
    close_on_launch: toggleCloseOnLaunchEl ? toggleCloseOnLaunchEl.checked : !!currentConfig.close_on_launch,
    fov: selectedFov,
    graphic_quality: selectedGfx,
    fps_limit: selectedFps,
    graphics_configured: true,
    env_mode: selectedEnv,
    auto_weather: isAuto,
    night_mode: isNight,
    rain_mode: isRain,
    snow_mode: isSnow,
    bgm_enabled: true
   });
   await getApi().save_config(newConfig);
   await getApi().save_graphics_settings(selectedGfx, selectedFps, true);
   currentConfig = newConfig;
   if (signedInAccount) {
    signedInAccount.graphics_configured = true;
    signedInAccount.graphic_quality = selectedGfx;
    signedInAccount.fps_limit = selectedFps;
   }
   modal.classList.remove("open");
   showToast("Settings saved and applied successfully!", "fa-check");
  });
 }
}

let accountMode = "login";

let signedInAccount = null;

function setAccountMessage(text, ok) {
 const el = document.getElementById("accountMsg");
 if (!el) return;
 el.textContent = text || "";
 el.classList.toggle("is-error", !!(text && !ok));
 el.classList.toggle("is-ok", !!(text && ok));
}

function setAccountMode(mode) {
 accountMode = mode === "profile" ? "profile" : mode === "signup" ? "signup" : "login";
 const isProfile = accountMode === "profile";
 const signup = accountMode === "signup";
 const t = document.getElementById("accountTitle");
 const label = document.getElementById("btnAccountSubmitLabel");
 const hero = document.getElementById("groupHeroName");
 const pass = document.getElementById("inputAccountPass");
 const authFields = document.getElementById("accountAuthFields");
 const profileFields = document.getElementById("accountProfileFields");
 const authFooter = document.getElementById("accountFooterAuth");
 const discordNotice = document.getElementById("accountDiscordNotice");
 if (isProfile) {
  if (t) t.innerHTML = '<i class="fa-solid fa-id-badge"></i> PROFILE SETTINGS';
  if (authFields) authFields.style.display = "none";
  if (profileFields) profileFields.style.display = "block";
  if (discordNotice) discordNotice.style.display = "none";
  if (authFooter) authFooter.style.display = "none";
  if (signedInAccount) {
   const dispUser = document.getElementById("profileDisplayUser");
   const dispHero = document.getElementById("profileDisplayHero");
   const devBadge = document.getElementById("profileDevBadge");
   const inHero = document.getElementById("inputProfileHeroName");
   const inOldPass = document.getElementById("inputProfileOldPass");
   const inNewPass = document.getElementById("inputProfileNewPass");
   const inConfirmPass = document.getElementById("inputProfileConfirmPass");
   if (dispUser) dispUser.textContent = signedInAccount.username;
   if (dispHero) dispHero.textContent = signedInAccount.hero_name || signedInAccount.username;
   if (devBadge) devBadge.style.display = signedInAccount.is_dev ? "inline-block" : "none";
   if (inHero) inHero.value = signedInAccount.hero_name || signedInAccount.username;
   if (inOldPass) inOldPass.value = "";
   if (inNewPass) inNewPass.value = "";
   if (inConfirmPass) inConfirmPass.value = "";
  }
 } else if (signup) {
  if (t) t.innerHTML = '<i class="fa-brands fa-discord" style="color:#5865F2"></i> GET ACCESS';
  if (authFields) authFields.style.display = "none";
  if (profileFields) profileFields.style.display = "none";
  if (discordNotice) discordNotice.style.display = "block";
  if (authFooter) authFooter.style.display = "none";
  setAccountMessage("Join our Discord server to get access.", true);
 } else {
  if (t) t.textContent = "SIGN IN";
  if (label) label.textContent = "SIGN IN";
  if (hero) hero.hidden = true;
  if (pass) pass.setAttribute("autocomplete", "current-password");
  if (authFields) authFields.style.display = "block";
  if (profileFields) profileFields.style.display = "none";
  if (discordNotice) discordNotice.style.display = "none";
  if (authFooter) authFooter.style.display = "flex";
 }
 [ "tabProfile", "tabSignIn", "tabSignUp" ].forEach(function(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("is-active", el.dataset.mode === accountMode);
 });
 if (!signup) setAccountMessage("", true);
}

function renderAccountLink() {
 const link = document.getElementById("linkAccount");
 if (link) {
  link.textContent = signedInAccount ? signedInAccount.hero_name || signedInAccount.username : "Sign in";
  link.title = signedInAccount ? "Signed in as " + signedInAccount.username + (signedInAccount.is_dev ? " [Developer]" : "") + " - click to manage profile or switch account" : "Sign in or create an account";
 }
 const stName = document.getElementById("settingsProfileName");
 const stDesc = document.getElementById("settingsProfileDesc");
 if (stName && stDesc) {
  if (signedInAccount) {
   stName.textContent = signedInAccount.username + (signedInAccount.is_dev ? " [Developer]" : "");
   stDesc.textContent = "Game Name: " + (signedInAccount.hero_name || signedInAccount.username);
  } else {
   stName.textContent = "Not Signed In";
   stDesc.textContent = "Sign in or create an account to customize your profile";
  }
 }
}

function updateDevModeUi() {
 const isDev = !!(signedInAccount && signedInAccount.is_dev);
 const btnOpenMaster = document.getElementById("btnOpenMaster");
 if (btnOpenMaster) {
  btnOpenMaster.style.display = isDev ? "inline-flex" : "none";
 }
 const railBtnMaster = document.getElementById("railBtnMaster");
 if (railBtnMaster) {
  railBtnMaster.style.display = isDev ? "flex" : "none";
 }
 document.body.classList.toggle("is-dev", isDev);
 document.querySelectorAll(".dev-only-feature").forEach(el => {
  el.style.display = isDev ? "" : "none";
 });
 if (!isDev && window.__closeMasterConsole) {
  window.__closeMasterConsole();
 }
}

async function refreshAccountState() {
 try {
  const st = await getApi().account_state();
  if (!st || !st.available) {
   signedInAccount = null;
   renderAccountLink();
   updateDevModeUi();
   return st;
  }
  signedInAccount = st.signed_in || null;
  if (signedInAccount && typeof signedInAccount.graphic_quality !== "undefined") {
   syncSettingsGraphicsUI(signedInAccount.graphic_quality, signedInAccount.fps_limit || 120);
  }
  renderAccountLink();
  updateDevModeUi();
  applyBanState(signedInAccount ? st.ban : null);
  return st;
 } catch (e) {
  console.error("account_state failed", e);
  return null;
 }
}

function initAccountModal() {
 const modal = document.getElementById("accountModal");
 const link = document.getElementById("linkAccount");
 const btnClose = document.getElementById("btnCloseAccount");
 const btnSubmit = document.getElementById("btnAccountSubmit");
 const btnToggle = document.getElementById("btnTogglePass");
 const user = document.getElementById("inputAccountUser");
 const pass = document.getElementById("inputAccountPass");
 const hero = document.getElementById("inputHeroName");
 const remember = document.getElementById("toggleRemember");
 const btnSignOut = document.getElementById("btnSignOut");
 const tabProfile = document.getElementById("tabProfile");
 const inputProfileHero = document.getElementById("inputProfileHeroName");
 const btnSaveHero = document.getElementById("btnSaveHeroName");
 const inputOldPass = document.getElementById("inputProfileOldPass");
 const inputNewPass = document.getElementById("inputProfileNewPass");
 const inputConfirmPass = document.getElementById("inputProfileConfirmPass");
 const btnToggleOldPass = document.getElementById("btnToggleProfileOldPass");
 const btnToggleNewPass = document.getElementById("btnToggleProfileNewPass");
 const btnSavePass = document.getElementById("btnSavePassword");
 const btnProfSignOut = document.getElementById("btnProfileSignOut");
 if (!modal) return;
 const close = function() {
  if (!signedInAccount) {
   return;
  }
  modal.classList.remove("open");
 };
 const open = async function(msg, preferMode) {
  const st = await refreshAccountState();
  const none = !st || !st.accounts || st.accounts.length === 0;
  if (tabProfile) {
   tabProfile.style.display = signedInAccount ? "inline-block" : "none";
  }
  let targetMode = preferMode;
  if (!targetMode) {
   if (signedInAccount) {
    targetMode = "profile";
   } else {
    targetMode = "login";
   }
  }
  setAccountMode(targetMode);
  if (btnSignOut) btnSignOut.hidden = !signedInAccount;
  if (btnClose) btnClose.style.display = signedInAccount ? "inline-flex" : "none";
  if (signedInAccount) {
   if (targetMode === "profile") {
    setAccountMessage("Manage your in-game character name and account password below.", true);
   } else {
    setAccountMessage("Signed in as " + signedInAccount.username + ". Sign in as someone else, or sign out.", true);
   }
   if (user) user.value = "";
  } else if (st && st.accounts && st.accounts.length && user) {
   user.value = st.accounts[0].username;
  }
  if (pass) pass.value = "";
  if (msg) {
   setAccountMessage(msg, false);
  } else if (!signedInAccount) {
   setAccountMessage("Please sign in to continue. To get access, join our Discord.", false);
  }
  modal.classList.add("open");
  setTimeout(function() {
   if (targetMode === "profile") {
    if (inputProfileHero) inputProfileHero.focus();
   } else {
    const f = user && !user.value ? user : pass;
    if (f) f.focus();
   }
  }, 60);
 };
 if (link) link.addEventListener("click", function() {
  playBeep(520, "sine", .08);
  open();
 });
 window.openAccountModal = open;
 if (btnClose) btnClose.addEventListener("click", close);
 modal.addEventListener("click", function(e) {
  if (e.target === modal && signedInAccount) close();
 });
 document.addEventListener("keydown", function(e) {
  if (e.key === "Escape" && modal.classList.contains("open") && signedInAccount) {
   close();
  }
 });
 [ "tabProfile", "tabSignIn", "tabSignUp" ].forEach(function(id) {
  const el = document.getElementById(id);
  if (el) el.addEventListener("click", function() {
   setAccountMode(el.dataset.mode);
  });
 });
 if (btnToggle && pass) {
  btnToggle.addEventListener("click", function() {
   const show = pass.type === "password";
   pass.type = show ? "text" : "password";
   btnToggle.textContent = show ? "Hide" : "Show";
  });
 }
 if (btnToggleOldPass && inputOldPass) {
  btnToggleOldPass.addEventListener("click", function() {
   const show = inputOldPass.type === "password";
   inputOldPass.type = show ? "text" : "password";
   btnToggleOldPass.textContent = show ? "Hide" : "Show";
  });
 }
 if (btnToggleNewPass && inputNewPass) {
  btnToggleNewPass.addEventListener("click", function() {
   const show = inputNewPass.type === "password";
   inputNewPass.type = show ? "text" : "password";
   btnToggleNewPass.textContent = show ? "Hide" : "Show";
  });
 }
 if (btnSaveHero && inputProfileHero) {
  const doSaveHero = async function() {
   if (!signedInAccount) return;
   const val = (inputProfileHero.value || "").trim();
   if (!val) {
    setAccountMessage("In-game name cannot be empty.", false);
    inputProfileHero.focus();
    return;
   }
   if (val.length > 24) {
    setAccountMessage("In-game name cannot exceed 24 characters.", false);
    inputProfileHero.focus();
    return;
   }
   btnSaveHero.disabled = true;
   setAccountMessage("Updating in-game name...", true);
   try {
    const res = await getApi().account_set_hero_name(signedInAccount.username, val);
    if (res && res.success) {
     playBeep(750, "sine", .12);
     signedInAccount.hero_name = val;
     const dispHero = document.getElementById("profileDisplayHero");
     if (dispHero) dispHero.textContent = val;
     renderAccountLink();
     setAccountMessage(res.message || "In-game name updated!", true);
     showToast("Game name updated to " + val, "fa-circle-check");
    } else {
     setAccountMessage(res && res.message || "Failed to update game name.", false);
    }
   } catch (e) {
    setAccountMessage(String(e), false);
   } finally {
    btnSaveHero.disabled = false;
   }
  };
  btnSaveHero.addEventListener("click", doSaveHero);
  inputProfileHero.addEventListener("keydown", function(e) {
   if (e.key === "Enter") doSaveHero();
  });
 }
 if (btnSavePass) {
  const doSavePass = async function() {
   if (!signedInAccount) return;
   const oldP = inputOldPass && inputOldPass.value || "";
   const newP = inputNewPass && inputNewPass.value || "";
   const confP = inputConfirmPass && inputConfirmPass.value || "";
   if (!oldP) {
    setAccountMessage("Please enter your current password.", false);
    if (inputOldPass) inputOldPass.focus();
    return;
   }
   if (!newP || newP.length < 6) {
    setAccountMessage("New password must be at least 6 characters.", false);
    if (inputNewPass) inputNewPass.focus();
    return;
   }
   if (newP !== confP) {
    setAccountMessage("New passwords do not match.", false);
    if (inputConfirmPass) inputConfirmPass.focus();
    return;
   }
   btnSavePass.disabled = true;
   setAccountMessage("Updating password...", true);
   try {
    const res = await getApi().account_change_password(signedInAccount.username, oldP, newP, true);
    if (res && res.success) {
     playBeep(750, "sine", .12);
     if (inputOldPass) inputOldPass.value = "";
     if (inputNewPass) inputNewPass.value = "";
     if (inputConfirmPass) inputConfirmPass.value = "";
     setAccountMessage(res.message || "Password changed successfully.", true);
     showToast("Password updated successfully!", "fa-circle-check");
    } else {
     setAccountMessage(res && res.message || "Failed to update password.", false);
    }
   } catch (e) {
    setAccountMessage(String(e), false);
   } finally {
    btnSavePass.disabled = false;
   }
  };
  btnSavePass.addEventListener("click", doSavePass);
  [ inputOldPass, inputNewPass, inputConfirmPass ].forEach(function(el) {
   if (el) el.addEventListener("keydown", function(e) {
    if (e.key === "Enter") doSavePass();
   });
  });
 }
 if (btnProfSignOut) {
  btnProfSignOut.addEventListener("click", async function() {
   const res = await getApi().account_logout();
   signedInAccount = null;
   renderAccountLink();
   updateDevModeUi();
   if (tabProfile) tabProfile.style.display = "none";
   setAccountMode("login");
   if (btnSignOut) btnSignOut.hidden = true;
   if (btnClose) btnClose.style.display = "none";
   setAccountMessage(res && res.message || "Signed out.", true);
   showToast("Signed out", "fa-right-from-bracket");
  });
 }
 const submit = async function() {
  if (accountMode === "signup") {
   setAccountMessage("Join our Discord server to get access.", true);
   showToast("Join our Discord server to get access.", "fa-brands fa-discord");
   return;
  }
  const u = (user && user.value || "").trim();
  const p = pass && pass.value || "";
  if (!u || !p) {
   setAccountMessage("Enter a username and password.", false);
   return;
  }
  if (btnSubmit) btnSubmit.disabled = true;
  setAccountMessage("Signing in...", true);
  try {
   const api = getApi();
   const res = await api.account_login(u, p, true);
   setAccountMessage(res && res.message || "Done", !!(res && res.success));
   if (res && res.banned) {
    showBannedModal(res);
   }
   if (res && res.success) {
    playBeep(750, "sine", .12);
    signedInAccount = res.account || null;
    if (signedInAccount && typeof signedInAccount.graphic_quality !== "undefined") {
     syncSettingsGraphicsUI(signedInAccount.graphic_quality, signedInAccount.fps_limit || 120);
    }
    renderAccountLink();
    updateDevModeUi();
    if (tabProfile) tabProfile.style.display = "inline-block";
    if (btnSignOut) btnSignOut.hidden = false;
    if (btnClose) btnClose.style.display = "inline-flex";
    if (pass) pass.value = "";
    setTimeout(function() {
     modal.classList.remove("open");
    }, 700);
    showToast("Signed in as " + (res.account && res.account.username || u), "fa-circle-check");
    if (api.get_ban_status) {
     api.get_ban_status(true).then(applyBanState).catch(() => {});
    }
   }
  } catch (e) {
   setAccountMessage(String(e), false);
  } finally {
   if (btnSubmit) btnSubmit.disabled = false;
  }
 };
 const btnDiscordAcc = document.getElementById("btnJoinDiscordAccount");
 if (btnDiscordAcc) {
  btnDiscordAcc.addEventListener("click", async () => {
   playBeep(650, "sine", .1);
   const url = "https://discord.gg/uXc8frbz5Y";
   try {
    const api = getApi();
    if (api && api.open_external_url) await api.open_external_url(url); else window.open(url, "_blank");
   } catch (e) {
    window.open(url, "_blank");
   }
   showToast("Opening Official Cyber Hunter Discord...", "fa-brands fa-discord");
  });
 }
 if (btnSubmit) btnSubmit.addEventListener("click", submit);
 [ user, pass, hero ].forEach(function(el) {
  if (el) el.addEventListener("keydown", function(e) {
   if (e.key === "Enter") submit();
  });
 });
 if (btnSignOut) {
  btnSignOut.addEventListener("click", async function() {
   const res = await getApi().account_logout();
   signedInAccount = null;
   renderAccountLink();
   updateDevModeUi();
   if (tabProfile) tabProfile.style.display = "none";
   setAccountMode("login");
   btnSignOut.hidden = true;
   if (btnClose) btnClose.style.display = "none";
   setAccountMessage(res && res.message || "Signed out.", true);
   showToast("Signed out", "fa-right-from-bracket");
  });
 }
}

function initAddDevModal() {
 const modal = document.getElementById("addDevModal");
 const btnOpen = document.getElementById("btnOpenAddDevModal");
 const btnClose = document.getElementById("btnCloseAddDev");
 const btnSubmit = document.getElementById("btnSubmitAddDev");
 const inputUser = document.getElementById("inputDevUsername");
 const devTags = document.getElementById("devTagsContainer");
 const msgEl = document.getElementById("devModalMsg");
 if (!modal) return;
 const close = () => {
  modal.classList.remove("open");
 };
 const setMsg = (txt, ok) => {
  if (!msgEl) return;
  msgEl.textContent = txt || "";
  msgEl.className = "account-msg " + (ok ? "is-ok" : "is-err");
 };
 const renderDevList = async () => {
  if (!devTags) return;
  try {
   const devs = await getApi().get_dev_list();
   devTags.innerHTML = "";
   if (Array.isArray(devs) && devs.length > 0) {
    devs.forEach(d => {
     const tag = document.createElement("span");
     tag.className = "dev-user-tag";
     tag.innerHTML = `<i class="fa-solid fa-code"></i> ${escHtml(d)}`;
     devTags.appendChild(tag);
    });
   } else {
    devTags.innerHTML = '<span style="color:var(--val-text-muted); font-size:12px;">No developers listed.</span>';
   }
  } catch (_) {}
 };
 const open = async () => {
  setMsg("", true);
  if (inputUser) inputUser.value = "";
  await renderDevList();
  modal.classList.add("open");
  if (inputUser) setTimeout(() => inputUser.focus(), 80);
 };
 if (btnOpen) btnOpen.addEventListener("click", () => {
  playBeep(520, "sine", .08);
  open();
 });
 if (btnClose) btnClose.addEventListener("click", close);
 modal.addEventListener("click", e => {
  if (e.target === modal) close();
 });
 const submit = async () => {
  const u = (inputUser && inputUser.value || "").trim();
  if (!u) {
   setMsg("Please enter a username.", false);
   return;
  }
  if (btnSubmit) btnSubmit.disabled = true;
  try {
   const res = await getApi().add_dev_account(u);
   setMsg(res && res.message || "Done", !!(res && res.success));
   if (res && res.success) {
    playBeep(750, "sine", .12);
    showToast(`'${u}' added to developers`, "fa-circle-check");
    if (inputUser) inputUser.value = "";
    await renderDevList();
    await refreshAccountState();
   }
  } catch (e) {
   setMsg(String(e), false);
  } finally {
   if (btnSubmit) btnSubmit.disabled = false;
  }
 };
 if (btnSubmit) btnSubmit.addEventListener("click", submit);
 if (inputUser) {
  inputUser.addEventListener("keydown", e => {
   if (e.key === "Enter") submit();
  });
 }
}

function escHtml(v) {
 return String(v == null ? "" : v).replace(/[&<>"']/g, c => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
 }[c]));
}

function fmtDate(ts) {
 if (!ts) return "—";
 try {
  return new Date(ts * 1e3).toLocaleString();
 } catch (e) {
  return "—";
 }
}

function setDevMsg(el, text, kind) {
 if (!el) return;
 el.textContent = text || "";
 el.classList.remove("ok", "err");
 if (kind) el.classList.add(kind);
}

function copyText(text) {
 if (navigator.clipboard && navigator.clipboard.writeText) {
  return navigator.clipboard.writeText(text).then(() => true).catch(() => false);
 }
 return Promise.resolve(false);
}

function generateTesterPassword() {
 const alphabet = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
 const bytes = new Uint32Array(12);
 (window.crypto || window.msCrypto).getRandomValues(bytes);
 let out = "";
 for (let i = 0; i < bytes.length; i++) {
  out += alphabet[bytes[i] % alphabet.length];
  if (i === 3 || i === 7) out += "-";
 }
 return out;
}

function initAddTesters() {
 const inputUser = document.getElementById("inputTesterUser");
 const inputHero = document.getElementById("inputTesterHero");
 const inputPass = document.getElementById("inputTesterPass");
 const btnGen = document.getElementById("btnGenTesterPass");
 const btnCreate = document.getElementById("btnCreateTester");
 const msg = document.getElementById("testerMsg");
 const list = document.getElementById("testerList");
 const btnRefresh = document.getElementById("btnRefreshTesters");
 const btnCopyAll = document.getElementById("btnCopyAllTesterCreds");
 const created = [];
 function credsText() {
  return "Cyber Hunter Reawakening - Tester Access\n" + created.map(c => `Username: ${c.username}\nPassword: ${c.password}`).join("\n\n");
 }
 function render(testers) {
  if (!list) return;
  const newNames = new Set(created.map(c => c.username.toLowerCase()));
  const rows = (testers || []).slice();
  created.forEach(c => {
   if (!rows.some(t => String(t.username).toLowerCase() === c.username.toLowerCase())) {
    rows.unshift({
     username: c.username,
     hero_name: c.hero_name,
     created: Math.floor(Date.now() / 1e3)
    });
   }
  });
  if (!rows.length) {
   list.innerHTML = '<div class="dev-list-empty">No tester accounts yet.</div>';
   return;
  }
  list.innerHTML = rows.map(t => {
   const isNew = newNames.has(String(t.username).toLowerCase());
   const cred = created.find(c => c.username.toLowerCase() === String(t.username).toLowerCase());
   const sub = cred ? `Password: <span class="dev-cred">${escHtml(cred.password)}</span>` : `IGN ${escHtml(t.hero_name || t.username)} · created ${escHtml(fmtDate(t.created))}${t.created_by ? " by " + escHtml(t.created_by) : ""} · last login ${escHtml(fmtDate(t.last_login))}`;
   const copyBtn = cred ? `<button type="button" class="dev-mini-btn" data-copy-tester="${escHtml(cred.username)}"><i class="fa-solid fa-copy"></i> Copy</button>` : "";
   return `<div class="dev-list-row${isNew ? " is-new" : ""}">\n        <div class="dev-list-main"><div class="dev-list-name">${escHtml(t.username)}</div><div class="dev-list-sub">${sub}</div></div>\n        <div>${copyBtn}</div></div>`;
  }).join("");
  list.querySelectorAll("[data-copy-tester]").forEach(btn => {
   btn.addEventListener("click", async () => {
    const c = created.find(x => x.username === btn.getAttribute("data-copy-tester"));
    if (!c) return;
    const ok = await copyText(`Cyber Hunter Reawakening - Tester Access\nUsername: ${c.username}\nPassword: ${c.password}`);
    showToast(ok ? `Copied ${c.username}'s credentials` : "Copy failed", ok ? "fa-copy" : "fa-triangle-exclamation");
   });
  });
  if (btnCopyAll) btnCopyAll.hidden = created.length < 1;
 }
 async function refresh() {
  if (!list || !signedInAccount || !signedInAccount.is_dev) return;
  const api = getApi();
  if (!api.list_tester_accounts) {
   render([]);
   return;
  }
  list.innerHTML = '<div class="dev-list-empty"><i class="fa-solid fa-spinner fa-spin"></i> Loading testers…</div>';
  try {
   const res = await api.list_tester_accounts();
   if (res && res.success === false && res.message) setDevMsg(msg, res.message, "err");
   render(res && res.testers || []);
  } catch (e) {
   render([]);
  }
 }
 window.refreshTesterList = refresh;
 if (btnGen && inputPass) {
  btnGen.addEventListener("click", () => {
   playBeep(650, "sine", .08);
   inputPass.value = generateTesterPassword();
  });
 }
 if (btnRefresh) btnRefresh.addEventListener("click", refresh);
 if (btnCopyAll) {
  btnCopyAll.addEventListener("click", async () => {
   if (!created.length) return;
   const ok = await copyText(credsText());
   showToast(ok ? `Copied ${created.length} tester credential(s)` : "Copy failed", ok ? "fa-copy" : "fa-triangle-exclamation");
  });
 }
 let busy = false;
 async function submit() {
  if (busy) return;
  const u = (inputUser && inputUser.value || "").trim();
  let p = (inputPass && inputPass.value || "").trim();
  const h = (inputHero && inputHero.value || "").trim();
  if (!/^[A-Za-z0-9_.\- ]{3,24}$/.test(u)) {
   setDevMsg(msg, "Username must be 3-24 characters: letters, numbers, space, . _ -", "err");
   if (inputUser) inputUser.focus();
   return;
  }
  if (!p) {
   p = generateTesterPassword();
   if (inputPass) inputPass.value = p;
  }
  if (p.length < 6) {
   setDevMsg(msg, "Password must be at least 6 characters.", "err");
   if (inputPass) inputPass.focus();
   return;
  }
  busy = true;
  if (btnCreate) btnCreate.disabled = true;
  setDevMsg(msg, "Creating tester on server…");
  try {
   const res = await getApi().create_tester_account(u, p, h || u);
   if (res && res.success) {
    playBeep(750, "sine", .12);
    created.unshift({
     username: res.username || u,
     password: p,
     hero_name: res.hero_name || h || u
    });
    copyText(`Cyber Hunter Reawakening - Tester Access\nUsername: ${res.username || u}\nPassword: ${p}`);
    setDevMsg(msg, `Created ${res.username || u} — credentials copied. Add the next tester below.`, "ok");
    showToast(`Tester '${res.username || u}' created`, "fa-circle-check");
    if (inputUser) {
     inputUser.value = "";
     inputUser.focus();
    }
    if (inputHero) inputHero.value = "";
    if (inputPass) inputPass.value = "";
    await refresh();
   } else {
    setDevMsg(msg, res && res.message || "Failed to create tester account.", "err");
   }
  } catch (err) {
   setDevMsg(msg, String(err), "err");
  } finally {
   busy = false;
   if (btnCreate) btnCreate.disabled = false;
  }
 }
 if (btnCreate) btnCreate.addEventListener("click", submit);
 [ inputUser, inputHero, inputPass ].forEach(el => {
  if (el) el.addEventListener("keydown", e => {
   if (e.key === "Enter") submit();
  });
 });
}

function initBanPlayersSettings() {
 const inputUser = document.getElementById("inputBanUser");
 const selDur = document.getElementById("selectBanDuration");
 const selReason = document.getElementById("selectBanReason");
 const inputNotes = document.getElementById("inputBanNotes");
 const btnBan = document.getElementById("btnBanPlayerSettings");
 const msg = document.getElementById("banMsg");
 const list = document.getElementById("banList");
 const btnRefresh = document.getElementById("btnRefreshBans");
 function render(bans) {
  if (!list) return;
  if (!bans || !bans.length) {
   list.innerHTML = '<div class="dev-list-empty">No active bans.</div>';
   return;
  }
  list.innerHTML = bans.map(b => {
   const until = b.expires_at ? "until " + fmtDate(b.expires_at) : "permanent";
   return `<div class="dev-list-row">\n        <div class="dev-list-main">\n          <div class="dev-list-name">${escHtml(b.username || b.account_id)}</div>\n          <div class="dev-list-sub">${escHtml(b.reason)} · ${escHtml(until)} · by ${escHtml(b.banned_by || "system")} · ${escHtml(fmtDate(b.banned_at))}${b.notes ? " · " + escHtml(b.notes) : ""}</div>\n        </div>\n        <div><button type="button" class="dev-mini-btn danger" data-unban="${escHtml(b.ban_id)}" data-name="${escHtml(b.username || "")}"><i class="fa-solid fa-user-check"></i> Unban</button></div>\n      </div>`;
  }).join("");
  list.querySelectorAll("[data-unban]").forEach(btn => {
   btn.addEventListener("click", () => {
    const id = btn.getAttribute("data-unban");
    const name = btn.getAttribute("data-name");
    devConfirm("CONFIRM UNBAN", `Remove the ban from ${name}?`, async () => {
     btn.disabled = true;
     try {
      const res = await getApi().dev_unban_player("", id, "Developer review");
      setDevMsg(msg, res && res.message || "Done", res && res.success ? "ok" : "err");
      if (res && res.success) showToast(res.message, "fa-circle-check");
     } catch (e) {
      setDevMsg(msg, String(e), "err");
     }
     await refresh();
    });
   });
  });
 }
 async function refresh() {
  if (!list || !signedInAccount || !signedInAccount.is_dev) return;
  const api = getApi();
  if (!api.dev_list_bans) {
   render([]);
   return;
  }
  list.innerHTML = '<div class="dev-list-empty"><i class="fa-solid fa-spinner fa-spin"></i> Loading bans…</div>';
  try {
   const res = await api.dev_list_bans();
   if (res && res.success === false && res.message) setDevMsg(msg, res.message, "err");
   render(res && res.bans || []);
  } catch (e) {
   render([]);
  }
 }
 window.refreshBanList = refresh;
 if (btnRefresh) btnRefresh.addEventListener("click", refresh);
 async function submit() {
  const u = (inputUser && inputUser.value || "").trim();
  if (!u) {
   setDevMsg(msg, "Enter the username of the account to ban.", "err");
   if (inputUser) inputUser.focus();
   return;
  }
  const hours = parseFloat(selDur && selDur.value || "0") || 0;
  const reason = selReason && selReason.value || "Cheating";
  const notes = (inputNotes && inputNotes.value || "").trim();
  const what = hours > 0 ? `ban ${u} for ${selDur.options[selDur.selectedIndex].text}` : `PERMANENTLY ban ${u}`;
  devConfirm(hours > 0 ? "CONFIRM BAN" : "PERMANENT BAN", `Are you sure you want to ${what}?\n\nReason: ${reason}\n\nThey will not be able to launch the game.`, async () => {
   if (btnBan) btnBan.disabled = true;
   setDevMsg(msg, "Applying ban…");
   try {
    const res = await getApi().dev_ban_player(u, reason, hours, notes);
    setDevMsg(msg, res && res.message || "Done", res && res.success ? "ok" : "err");
    if (res && res.success) {
     showToast(res.message, "fa-ban");
     if (inputUser) inputUser.value = "";
     if (inputNotes) inputNotes.value = "";
     await refresh();
    }
   } catch (e) {
    setDevMsg(msg, String(e), "err");
   } finally {
    if (btnBan) btnBan.disabled = false;
   }
  });
 }
 if (btnBan) btnBan.addEventListener("click", submit);
 if (inputUser) inputUser.addEventListener("keydown", e => {
  if (e.key === "Enter") submit();
 });
}

function devConfirm(title, message, onProceed) {
 if (window.devShowConfirm) window.devShowConfirm(title, message, onProceed); else onProceed();
}

let currentBan = null;

let banModalShownFor = "";

let banPollTimer = null;

function showBannedModal(ban) {
 const modal = document.getElementById("bannedModal");
 if (!modal) return;
 const reasonEl = document.getElementById("banModalReason");
 const titleEl = document.getElementById("banModalTitle");
 const textEl = document.getElementById("banModalText");
 const temp = ban && ban.expires_at;
 if (reasonEl) reasonEl.textContent = ban && ban.reason || "Cheating";
 if (titleEl) titleEl.textContent = temp ? "YOU ARE TEMPORARILY BANNED" : "YOU ARE PERMANENTLY BANNED";
 if (textEl) {
  textEl.textContent = temp ? `You cannot launch Cyber Hunter Reawakening until ${fmtDate(ban.expires_at)}.` : "Access to Cyber Hunter Reawakening has been permanently restricted.";
 }
 modal.removeAttribute("hidden");
}

function applyBanState(ban) {
 const was = !!(currentBan && currentBan.banned);
 currentBan = ban && ban.banned ? ban : null;
 const key = currentBan ? `${signedInAccount && signedInAccount.username || ""}|${currentBan.ban_id || currentBan.reason}` : "";
 if (currentBan && banModalShownFor !== key) {
  banModalShownFor = key;
  showBannedModal(currentBan);
 }
 if (!currentBan) banModalShownFor = "";
 if (was !== !!currentBan && !isLaunching && !isGameRunning && !isGameDownloading && !isUpdating) {
  setPlayButtonState("idle");
 }
}

function startBanPoll() {
 if (banPollTimer) clearInterval(banPollTimer);
 banPollTimer = setInterval(async () => {
  if (!signedInAccount || signedInAccount.is_dev) return;
  try {
   const api = getApi();
   if (!api.get_ban_status) return;
   applyBanState(await api.get_ban_status(false));
  } catch (e) {}
 }, 6e4);
}

function initMasterConsole() {
 const root = document.getElementById("masterConsole");
 if (!root) return;
 const logView = document.getElementById("masterLogView");
 const logPath = document.getElementById("masterLogPath");
 const feedback = document.getElementById("masterFeedback");
 const followEl = document.getElementById("masterLogFollow");
 const cmdInput = document.getElementById("masterCmdInput");
 const matchGrid = document.getElementById("masterCmdMatch");
 const testGrid = document.getElementById("masterCmdTest");
 const vehicleGrid = document.getElementById("masterCmdVehicle");
 const playerGrid = document.getElementById("masterCmdPlayer");
 let logWhich = "lobby";
 let logOffset = 0;
 let pollTimer = null;
 let open = false;
 function setFeedback(msg, ok) {
  if (!feedback) return;
  feedback.textContent = msg || "";
  feedback.classList.toggle("is-ok", !!ok);
  feedback.classList.toggle("is-err", ok === false);
 }
 function renderSnapshot(snap) {
  if (!snap) return;
  const rev = snap.revival || {};
  const launch = snap.launch || {};
  const ports = snap.ports || {};
  const acct = snap.account || {};
  const set = (id, v) => {
   const el = document.getElementById(id);
   if (el) el.textContent = v;
  };
  set("msMode", (rev.mode || "—") + " @ " + (rev.server_ip || "—"));
  set("msLaunch", (launch.status || "idle") + (launch.ready ? " · ready" : ""));
  set("msClient", snap.client_pid ? "pid " + snap.client_pid : "offline");
  const up = Object.keys(ports).filter(k => ports[k]).join(" ") || "none";
  set("msPorts", up);
  set("msHero", (acct.name || "—") + (acct.hero_id != null ? " #" + acct.hero_id : ""));
 }
 async function refreshSnapshot() {
  try {
   const snap = await getApi().master_snapshot();
   renderSnapshot(snap);
   return snap;
  } catch (e) {
   setFeedback(String(e), false);
   return null;
  }
 }
 async function tailOnce() {
  try {
   const res = await getApi().master_tail_log(logWhich, logOffset, 64e3);
   if (!res || !res.success) {
    setFeedback(res && res.message || "tail failed", false);
    return;
   }
   if (logPath) logPath.textContent = res.path || logWhich;
   if (res.missing) {
    if (logView && !logView.textContent) logView.textContent = "(file missing)\n";
    return;
   }
   if (res.text && logView) {
    if (logOffset === 0) logView.textContent = res.text; else logView.textContent += res.text;
    if (logView.textContent.length > 4e5) {
     logView.textContent = logView.textContent.slice(-3e5);
    }
    if (!followEl || followEl.checked) {
     logView.scrollTop = logView.scrollHeight;
    }
   }
   logOffset = res.offset || logOffset;
  } catch (e) {
   setFeedback(String(e), false);
  }
 }
 function startPoll() {
  stopPoll();
  pollTimer = setInterval(async () => {
   if (!open) return;
   await tailOnce();
   await refreshSnapshot();
  }, 1200);
 }
 function stopPoll() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
 }
 async function openConsole() {
  const isDev = !!(signedInAccount && signedInAccount.is_dev);
  if (!isDev) {
   showToast("Developer mode required for Control Panel.", "fa-shield-halved");
   return;
  }
  root.hidden = false;
  open = true;
  try {
   const res = await getApi().master_command_catalog();
   if (res && res.commands) fillCmds(res.commands);
  } catch (_) {}
  await refreshSnapshot();
  if (logOffset === 0) await tailOnce();
  startPoll();
 }
 function closeConsole() {
  root.hidden = true;
  open = false;
  stopPoll();
  const masterBtn = document.getElementById("railBtnMaster");
  if (masterBtn) masterBtn.classList.remove("active");
 }
 window.__openMasterConsole = openConsole;
 window.__closeMasterConsole = closeConsole;
 async function sendCmd(cmd) {
  const c = (cmd || "").trim();
  if (!c) return;
  setFeedback("sending…", true);
  try {
   const res = await getApi().master_send_cmd(c);
   setFeedback(res && res.message || "done", !!(res && res.success));
   showToast(res && res.message || c, res && res.success ? "fa-terminal" : "fa-triangle-exclamation");
  } catch (e) {
   setFeedback(String(e), false);
  }
 }
 function fillCmds(commands) {
  const test = (commands || []).filter(c => c.group === "test");
  const match = (commands || []).filter(c => c.group === "match" || c.group === "lobby" || c.group === "test" && !testGrid);
  const vehicle = (commands || []).filter(c => c.group === "vehicle");
  const player = (commands || []).filter(c => c.group === "player" || c.group === "debug");
  const paint = (el, list) => {
   if (!el) return;
   el.innerHTML = "";
   list.forEach(item => {
    const b = document.createElement("button");
    b.type = "button";
    const label = item.label || item.cmd;
    b.innerHTML = label + (item.desc ? "<small>" + item.desc + "</small>" : "");
    b.title = item.desc || item.cmd;
    b.addEventListener("click", () => sendCmd(item.cmd));
    el.appendChild(b);
   });
  };
  if (testGrid) paint(testGrid, test);
  paint(matchGrid, match);
  paint(vehicleGrid, vehicle);
  paint(playerGrid, player);
 }
 getApi().master_command_catalog().then(res => {
  if (res && res.commands) fillCmds(res.commands);
 }).catch(() => {});
 const src = document.getElementById("masterLogSource");
 if (src) {
  src.querySelectorAll("button").forEach(btn => {
   btn.addEventListener("click", async () => {
    src.querySelectorAll("button").forEach(b => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    logWhich = btn.dataset.log || "lobby";
    logOffset = 0;
    if (logView) logView.textContent = "";
    await tailOnce();
   });
  });
 }
 const btnClose = document.getElementById("btnMasterClose");
 const btnRefresh = document.getElementById("btnMasterRefresh");
 const btnClear = document.getElementById("btnMasterClearLog");
 const btnSend = document.getElementById("btnMasterSend");
 const btnKill = document.getElementById("btnMasterKillClient");
 const btnSpawnHydrofoilDirect = document.getElementById("btnSpawnHydrofoilDirect");
 if (btnSpawnHydrofoilDirect) {
  btnSpawnHydrofoilDirect.addEventListener("click", () => {
   playBeep(620, "sine", .1);
   sendCmd("hydrofoil");
  });
 }
 if (btnClose) btnClose.addEventListener("click", closeConsole);
 if (btnRefresh) btnRefresh.addEventListener("click", async () => {
  await refreshSnapshot();
  await tailOnce();
 });
 if (btnClear) btnClear.addEventListener("click", () => {
  if (logView) logView.textContent = "";
 });
 if (btnSend) btnSend.addEventListener("click", () => sendCmd(cmdInput && cmdInput.value));
 if (cmdInput) {
  cmdInput.addEventListener("keydown", e => {
   if (e.key === "Enter") sendCmd(cmdInput.value);
  });
 }
 if (btnKill) {
  btnKill.addEventListener("click", async () => {
   const res = await getApi().master_kill_client();
   setFeedback(res && res.message || "kill", !!(res && res.success));
   await refreshSnapshot();
  });
 }
}

function initSpawnMapper() {
 const modal = document.getElementById("spawnMapperModal");
 if (!modal) return;
 let pollTimer = null;
 let lastOpen = false;
 let autoOpened = false;
 const badge = document.getElementById("spawnMapperBadge");
 const msgEl = document.getElementById("spawnMapperMsg");
 function setMsg(text, ok) {
  if (!msgEl) return;
  msgEl.textContent = text || "";
  msgEl.classList.toggle("is-ok", !!ok);
  msgEl.classList.toggle("is-err", ok === false);
 }
 function fmt3(n) {
  const v = Number(n);
  return Number.isFinite(v) ? v.toFixed(2) : "—";
 }
 function renderPose(live) {
  const open = !!(live && live.open);
  if (badge) {
   badge.textContent = open ? "ON" : "OFF";
   badge.classList.toggle("is-on", open);
  }
  const pose = live && live.pose || null;
  const set = (id, val) => {
   const el = document.getElementById(id);
   if (el) el.textContent = val;
  };
  set("smPoseStatus", !live ? "Waiting for game…" : open ? "Mapper open in-game" : live.client_hint || "Mapper closed — press F11 in-game");
  set("smPoseKind", live ? `${live.kind || "—"} / type ${live.type_id != null ? live.type_id : "—"}` : "—");
  if (pose && pose.pos) {
   set("smPoseXyz", `${fmt3(pose.pos[0])}, ${fmt3(pose.pos[1])}, ${fmt3(pose.pos[2])}`);
   set("smPoseAngles", `${fmt3(pose.yaw)} / ${fmt3(pose.pitch)}`);
   const d = pose.dir || [];
   set("smPoseDir", `${fmt3(d[0])}, ${fmt3(d[1])}, ${fmt3(d[2])}`);
  } else {
   set("smPoseXyz", "—");
   set("smPoseAngles", "—");
   set("smPoseDir", "—");
  }
  set("smPoseCount", String((live && live.count) != null ? live.count : 0));
 }
 function renderTable(doc) {
  const tbody = document.getElementById("spawnMapperTbody");
  if (!tbody) return;
  const marks = doc && doc.marks || [];
  if (!marks.length) {
   tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No marks yet — open mapper in-game with F11 and press M.</td></tr>';
   return;
  }
  tbody.innerHTML = marks.map(m => {
   const pos = m.pos || [ 0, 0, 0 ];
   const id = String(m.id || "");
   const label = (m.label || "").replace(/"/g, "&quot;");
   return `<tr data-id="${id}">\n        <td>${id}</td>\n        <td>${m.kind || ""}</td>\n        <td>${m.type_id != null ? m.type_id : ""}</td>\n        <td>${fmt3(pos[0])}, ${fmt3(pos[1])}, ${fmt3(pos[2])}</td>\n        <td>${fmt3(m.yaw)}</td>\n        <td><input class="sm-label" data-id="${id}" value="${label}" spellcheck="false"></td>\n        <td><button type="button" class="sm-del" data-id="${id}" title="Delete"><i class="fa-solid fa-trash"></i></button></td>\n      </tr>`;
  }).join("");
  tbody.querySelectorAll("input.sm-label").forEach(inp => {
   inp.addEventListener("change", async () => {
    const res = await getApi().spawn_mapper_update_label(inp.dataset.id, inp.value);
    setMsg(res && res.message || "label", !!(res && res.success));
   });
  });
  tbody.querySelectorAll("button.sm-del").forEach(btn => {
   btn.addEventListener("click", async () => {
    const res = await getApi().spawn_mapper_delete_mark(btn.dataset.id);
    setMsg(res && res.message || "delete", !!(res && res.success));
    await refresh();
   });
  });
 }
 async function refresh() {
  try {
   const snap = await getApi().spawn_mapper_snapshot();
   const live = snap && snap.live || {};
   if (snap && snap.client_running === false && !live.pose) {
    live.client_hint = "No client.exe — click Play first";
   }
   renderPose(live);
   renderTable(snap && snap.doc || {});
   const open = !!(live && live.open);
   if (open && !lastOpen && !modal.classList.contains("open") && !autoOpened) {
    autoOpened = true;
    openModal();
    showToast("Spawn Mapper opened (F11)", "fa-map-location-dot");
   }
   if (!open) autoOpened = false;
   lastOpen = open;
  } catch (e) {
   setMsg(String(e), false);
  }
 }
 function openModal() {
  modal.classList.add("open");
  refresh();
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(refresh, 500);
 }
 function closeModal() {
  modal.classList.remove("open");
  if (pollTimer) {
   clearInterval(pollTimer);
   pollTimer = null;
  }
 }
 async function send(cmd) {
  setMsg("Sending…", true);
  try {
   const res = await getApi().spawn_mapper_cmd(cmd);
   setMsg(res && res.message || "sent", !!(res && res.success));
   setTimeout(refresh, 400);
  } catch (e) {
   setMsg(String(e), false);
  }
 }
 window.openSpawnMapper = openModal;
 const btnClose = document.getElementById("btnCloseSpawnMapper");
 if (btnClose) btnClose.addEventListener("click", closeModal);
 modal.addEventListener("click", e => {
  if (e.target === modal) closeModal();
 });
 const bind = (id, cmd) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("click", () => send(cmd));
 };
 bind("smBtnToggle", "toggle");
 bind("smBtnMarkChest", "mark chest");
 bind("smBtnMarkVeh", "mark vehicle");
 bind("smBtnMarkLoot", "mark loot");
 bind("smBtnUndo", "undo");
 bind("smBtnExport", "export");
 bind("smBtnApply", "apply");
 const btnFolder = document.getElementById("smBtnFolder");
 if (btnFolder) {
  btnFolder.addEventListener("click", async () => {
   const res = await getApi().spawn_mapper_open_folder();
   setMsg(res && res.message || "folder", !!(res && res.success));
  });
 }
 setInterval(async () => {
  if (modal.classList.contains("open")) return;
  try {
   const snap = await getApi().spawn_mapper_snapshot();
   const open = !!(snap && snap.live && snap.live.open);
   if (open && !lastOpen && !autoOpened) {
    autoOpened = true;
    openModal();
    showToast("Spawn Mapper opened (F11)", "fa-map-location-dot");
   }
   if (!open) autoOpened = false;
   lastOpen = open;
  } catch (_) {}
 }, 1500);
}

function initModerationSystem() {
 const btnModBan = document.getElementById("btnModBan");
 const btnModUnban = document.getElementById("btnModUnban");
 const btnModViewBans = document.getElementById("btnModViewBans");
 const btnModViewFlags = document.getElementById("btnModViewFlags");
 const modalBan = document.getElementById("modalBanPlayer");
 const modalUnban = document.getElementById("modalUnbanPlayer");
 const modalViewBans = document.getElementById("modalViewBans");
 const modalViewFlags = document.getElementById("modalViewFlags");
 const modalConfirm = document.getElementById("modalConfirmAction");
 const modalBanned = document.getElementById("bannedModal");
 let pendingConfirmAction = null;
 let selectedBanPlayer = null;
 let selectedUnbanRecord = null;
 let allBansCache = [];
 let currentBansTab = "active";
 function showConfirm(title, message, onProceed) {
  if (!modalConfirm) return;
  const titleEl = document.getElementById("confirmActionTitle");
  const msgEl = document.getElementById("confirmActionMessage");
  if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${escHtml(title)}`;
  if (msgEl) msgEl.textContent = message;
  pendingConfirmAction = onProceed;
  modalConfirm.removeAttribute("hidden");
 }
 window.devShowConfirm = showConfirm;
 const btnConfirmProceed = document.getElementById("btnConfirmActionProceed");
 const btnConfirmCancel = document.getElementById("btnConfirmActionCancel");
 const btnCloseConfirm = document.getElementById("btnCloseConfirmAction");
 if (btnConfirmProceed) {
  btnConfirmProceed.addEventListener("click", () => {
   if (modalConfirm) modalConfirm.setAttribute("hidden", "");
   if (pendingConfirmAction) {
    const action = pendingConfirmAction;
    pendingConfirmAction = null;
    action();
   }
  });
 }
 if (btnConfirmCancel && modalConfirm) {
  btnConfirmCancel.addEventListener("click", () => modalConfirm.setAttribute("hidden", ""));
 }
 if (btnCloseConfirm && modalConfirm) {
  btnCloseConfirm.addEventListener("click", () => modalConfirm.setAttribute("hidden", ""));
 }
 const btnCloseBanned = document.getElementById("btnCloseBannedModal");
 const btnAcknowledgeBan = document.getElementById("btnAcknowledgeBan");
 if (btnCloseBanned && modalBanned) {
  btnCloseBanned.addEventListener("click", () => modalBanned.setAttribute("hidden", ""));
 }
 if (btnAcknowledgeBan && modalBanned) {
  btnAcknowledgeBan.addEventListener("click", () => modalBanned.setAttribute("hidden", ""));
 }
 if (btnModBan && modalBan) {
  btnModBan.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   selectedBanPlayer = null;
   const searchInput = document.getElementById("inputBanSearch");
   const resultsContainer = document.getElementById("banSearchResults");
   const form = document.getElementById("banPlayerForm");
   const confirmBtn = document.getElementById("btnConfirmBan");
   if (searchInput) searchInput.value = "";
   if (resultsContainer) resultsContainer.innerHTML = '<div style="padding:14px; text-align:center; color:var(--val-text-dim); font-size:13px;">Enter a player name and search above</div>';
   if (form) form.style.display = "none";
   if (confirmBtn) confirmBtn.disabled = true;
   modalBan.removeAttribute("hidden");
  });
  const btnClose = document.getElementById("btnCloseBanPlayer");
  const btnCancel = document.getElementById("btnCancelBan");
  if (btnClose) btnClose.addEventListener("click", () => modalBan.setAttribute("hidden", ""));
  if (btnCancel) btnCancel.addEventListener("click", () => modalBan.setAttribute("hidden", ""));
  const searchBtn = document.getElementById("btnBanSearchPlayer");
  const searchInput = document.getElementById("inputBanSearch");
  const doSearch = async () => {
   const q = (searchInput && searchInput.value || "").trim();
   const resultsContainer = document.getElementById("banSearchResults");
   if (!resultsContainer) return;
   resultsContainer.innerHTML = '<div style="padding:14px; text-align:center; color:var(--val-text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Searching players...</div>';
   try {
    const results = await getApi().moderation_search_players(q);
    if (!results || !results.length) {
     resultsContainer.innerHTML = '<div style="padding:14px; text-align:center; color:var(--val-text-muted);">No matching players found</div>';
     return;
    }
    let html = '<table style="width:100%; border-collapse:collapse; font-size:12px;">';
    html += '<thead style="background:#161426; color:var(--val-text-muted); text-align:left;"><tr>';
    html += '<th style="padding:6px 10px;">In-game Name</th>';
    html += '<th style="padding:6px 10px;">Account ID</th>';
    html += '<th style="padding:6px 10px;">Status</th>';
    html += '<th style="padding:6px 10px;">Flags</th>';
    html += '<th style="padding:6px 10px;">Prior Bans</th>';
    html += '<th style="padding:6px 10px;">Action</th>';
    html += "</tr></thead><tbody>";
    results.forEach((p, idx) => {
     const isBanned = p.is_banned;
     html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.05); cursor:pointer; background:${escHtml(idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)")};" data-idx="${escHtml(idx)}">`;
     html += `<td style="padding:8px 10px; font-weight:700; color:#fff;">${escHtml(p.in_game_name)}</td>`;
     html += `<td style="padding:8px 10px; font-family:var(--font-mono); color:#c7b8ff;">${escHtml(p.account_id)}</td>`;
     html += `<td style="padding:8px 10px;"><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#00ff88; margin-right:4px;"></span>${escHtml(p.online_status || "Offline")}</td>`;
     html += `<td style="padding:8px 10px; color:${escHtml(p.previous_flags > 0 ? "#fcd535" : "var(--val-text-dim)")};">${escHtml(p.previous_flags)}</td>`;
     html += `<td style="padding:8px 10px; color:${escHtml(p.previous_bans > 0 ? "#ff3355" : "var(--val-text-dim)")};">${escHtml(p.previous_bans)}${escHtml(isBanned ? " (Active)" : "")}</td>`;
     html += `<td style="padding:8px 10px;"><button type="button" class="btn-select-player" data-idx="${escHtml(idx)}" style="padding:4px 10px; font-size:11px; background:#815eff; border:none; border-radius:4px; color:#fff; cursor:pointer;">Select</button></td>`;
     html += "</tr>";
    });
    html += "</tbody></table>";
    resultsContainer.innerHTML = html;
    resultsContainer.querySelectorAll(".btn-select-player").forEach(btn => {
     btn.addEventListener("click", e => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.idx, 10);
      const player = results[idx];
      selectedBanPlayer = player;
      const nameEl = document.getElementById("banSelectedName");
      const acctEl = document.getElementById("banSelectedAcct");
      const form = document.getElementById("banPlayerForm");
      const confirmBtn = document.getElementById("btnConfirmBan");
      if (nameEl) nameEl.textContent = player.in_game_name;
      if (acctEl) acctEl.textContent = player.account_id;
      if (form) form.style.display = "block";
      if (confirmBtn) confirmBtn.disabled = false;
     });
    });
   } catch (err) {
    resultsContainer.innerHTML = `<div style="padding:14px; text-align:center; color:#ff3355;">Error: ${escHtml(err)}</div>`;
   }
  };
  if (searchBtn) searchBtn.addEventListener("click", doSearch);
  if (searchInput) searchInput.addEventListener("keydown", e => {
   if (e.key === "Enter") doSearch();
  });
  const selectBanType = document.getElementById("selectBanType");
  const groupDuration = document.getElementById("groupBanDuration");
  if (selectBanType && groupDuration) {
   selectBanType.addEventListener("change", () => {
    groupDuration.style.display = selectBanType.value === "Temporary" ? "block" : "none";
   });
  }
  const confirmBanBtn = document.getElementById("btnConfirmBan");
  if (confirmBanBtn) {
   confirmBanBtn.addEventListener("click", () => {
    if (!selectedBanPlayer) return;
    const banType = selectBanType ? selectBanType.value : "Permanent";
    const reason = (document.getElementById("selectBanReason") || {}).value || "Cheating";
    const notes = (document.getElementById("inputBanNotes") || {}).value || "";
    const durationHours = parseInt((document.getElementById("inputBanDuration") || {}).value || "24", 10);
    const durationSec = banType === "Temporary" ? durationHours * 3600 : 0;
    const isPermanent = banType === "Permanent";
    const confirmMsg = isPermanent ? `Are you sure you want to PERMANENTLY BAN ${selectedBanPlayer.in_game_name} (ID: ${selectedBanPlayer.account_id})?\n\nReason: ${reason}\n\nAccess to Cyber Hunter Reawakening will be permanently restricted across all game servers and launcher.` : `Apply a temporary ${durationHours}-hour ban to ${selectedBanPlayer.in_game_name} for ${reason}?`;
    showConfirm(isPermanent ? "PERMANENT BAN CONFIRMATION" : "CONFIRM BAN", confirmMsg, async () => {
     showToast(`Applying ${banType.toLowerCase()} ban...`, "fa-spinner fa-spin");
     try {
      const res = await getApi().moderation_ban_player(selectedBanPlayer.account_id, selectedBanPlayer.in_game_name, banType, reason, notes, durationSec);
      if (res && res.success) {
       showToast(res.message || "Player banned successfully!", "fa-circle-check");
       modalBan.setAttribute("hidden", "");
      } else {
       showToast(res && res.message || "Failed to ban player", "fa-triangle-exclamation");
      }
     } catch (e) {
      showToast(String(e), "fa-triangle-exclamation");
     }
    });
   });
  }
 }
 if (btnModUnban && modalUnban) {
  btnModUnban.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   selectedUnbanRecord = null;
   const searchInput = document.getElementById("inputUnbanSearch");
   const detailsContainer = document.getElementById("unbanDetailsContainer");
   const confirmBtn = document.getElementById("btnConfirmUnban");
   if (searchInput) searchInput.value = "";
   if (detailsContainer) detailsContainer.style.display = "none";
   if (confirmBtn) confirmBtn.disabled = true;
   modalUnban.removeAttribute("hidden");
  });
  const btnClose = document.getElementById("btnCloseUnbanPlayer");
  const btnCancel = document.getElementById("btnCancelUnban");
  if (btnClose) btnClose.addEventListener("click", () => modalUnban.setAttribute("hidden", ""));
  if (btnCancel) btnCancel.addEventListener("click", () => modalUnban.setAttribute("hidden", ""));
  const searchBtn = document.getElementById("btnUnbanSearch");
  const searchInput = document.getElementById("inputUnbanSearch");
  const doUnbanSearch = async () => {
   const q = (searchInput && searchInput.value || "").trim().toLowerCase();
   if (!q) {
    showToast("Please enter in-game name or account ID to search", "fa-triangle-exclamation");
    return;
   }
   try {
    const bans = await getApi().moderation_get_bans();
    const found = (bans || []).find(b => b.active_status && (b.account_id && b.account_id.toLowerCase() === q || b.in_game_name && b.in_game_name.toLowerCase() === q || b.ban_id && b.ban_id.toLowerCase() === q));
    const detailsContainer = document.getElementById("unbanDetailsContainer");
    const confirmBtn = document.getElementById("btnConfirmUnban");
    if (!found) {
     showToast(`No active ban record found for "${q}"`, "fa-circle-info");
     if (detailsContainer) detailsContainer.style.display = "none";
     if (confirmBtn) confirmBtn.disabled = true;
     return;
    }
    selectedUnbanRecord = found;
    const nameEl = document.getElementById("unbanPlayerName");
    const acctEl = document.getElementById("unbanAccountID");
    const reasonEl = document.getElementById("unbanReasonDisplay");
    const dateEl = document.getElementById("unbanDateDisplay");
    const byEl = document.getElementById("unbanBannedByDisplay");
    const typeEl = document.getElementById("unbanTypeDisplay");
    const evidenceEl = document.getElementById("unbanEvidenceDisplay");
    if (nameEl) nameEl.textContent = found.in_game_name;
    if (acctEl) acctEl.textContent = found.account_id;
    if (reasonEl) reasonEl.textContent = found.reason;
    if (dateEl) dateEl.textContent = found.banned_at ? new Date(found.banned_at * 1e3).toLocaleString() : "—";
    if (byEl) byEl.textContent = found.banned_by || "System";
    if (typeEl) typeEl.textContent = found.ban_type;
    if (evidenceEl) evidenceEl.textContent = JSON.stringify(found.anti_cheat_evidence || {}, null, 2);
    if (detailsContainer) detailsContainer.style.display = "block";
    if (confirmBtn) confirmBtn.disabled = false;
   } catch (err) {
    showToast(String(err), "fa-triangle-exclamation");
   }
  };
  if (searchBtn) searchBtn.addEventListener("click", doUnbanSearch);
  if (searchInput) searchInput.addEventListener("keydown", e => {
   if (e.key === "Enter") doUnbanSearch();
  });
  const confirmUnbanBtn = document.getElementById("btnConfirmUnban");
  if (confirmUnbanBtn) {
   confirmUnbanBtn.addEventListener("click", () => {
    if (!selectedUnbanRecord) return;
    const reason = (document.getElementById("inputUnbanReason") || {}).value || "Developer review";
    showConfirm("CONFIRM UNBAN", `Are you sure you want to remove the ban from ${selectedUnbanRecord.in_game_name} (${selectedUnbanRecord.account_id})?\n\nThe ban history will be preserved as an inactive audit record.`, async () => {
     showToast("Lifting ban record...", "fa-spinner fa-spin");
     try {
      const res = await getApi().moderation_unban_player(selectedUnbanRecord.ban_id, reason);
      if (res && res.success) {
       showToast(res.message || "Player unbanned successfully!", "fa-circle-check");
       modalUnban.setAttribute("hidden", "");
      } else {
       showToast(res && res.message || "Failed to unban player", "fa-triangle-exclamation");
      }
     } catch (e) {
      showToast(String(e), "fa-triangle-exclamation");
     }
    });
   });
  }
 }
 async function loadBansTable() {
  const container = document.getElementById("bansTableContainer");
  if (!container) return;
  container.innerHTML = '<div style="padding:16px; text-align:center; color:var(--val-text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Loading ban records...</div>';
  try {
   allBansCache = await getApi().moderation_get_bans() || [];
   renderBansList();
  } catch (err) {
   container.innerHTML = `<div style="padding:16px; text-align:center; color:#ff3355;">Error loading bans: ${escHtml(err)}</div>`;
  }
 }
 function renderBansList() {
  const container = document.getElementById("bansTableContainer");
  if (!container) return;
  const filtered = currentBansTab === "active" ? allBansCache.filter(b => b.active_status) : allBansCache;
  if (!filtered.length) {
   container.innerHTML = `<div style="padding:20px; text-align:center; color:var(--val-text-muted);">No ${currentBansTab === "active" ? "active " : ""}bans found.</div>`;
   return;
  }
  let html = '<table style="width:100%; border-collapse:collapse; font-size:12px;">';
  html += '<thead style="background:#161426; color:var(--val-text-muted); text-align:left;"><tr>';
  html += '<th style="padding:8px 10px;">Player Name</th>';
  html += '<th style="padding:8px 10px;">Account ID</th>';
  html += '<th style="padding:8px 10px;">Type</th>';
  html += '<th style="padding:8px 10px;">Reason</th>';
  html += '<th style="padding:8px 10px;">Banned By</th>';
  html += '<th style="padding:8px 10px;">Date</th>';
  html += '<th style="padding:8px 10px;">Status</th>';
  html += "</tr></thead><tbody>";
  filtered.forEach((b, idx) => {
   const active = b.active_status;
   const dateStr = b.banned_at ? new Date(b.banned_at * 1e3).toLocaleDateString() : "—";
   html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.05); background:${escHtml(idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)")};">`;
   html += `<td style="padding:8px 10px; font-weight:700; color:#fff;">${escHtml(b.in_game_name || "—")}</td>`;
   html += `<td style="padding:8px 10px; font-family:var(--font-mono); color:#c7b8ff;">${escHtml(b.account_id || "—")}</td>`;
   html += `<td style="padding:8px 10px; color:${escHtml(b.ban_type === "Permanent" ? "#ff3355" : "#fcd535")}; font-weight:700;">${escHtml(b.ban_type)}</td>`;
   html += `<td style="padding:8px 10px;">${escHtml(b.reason)}</td>`;
   html += `<td style="padding:8px 10px; color:var(--val-text-dim);">${escHtml(b.banned_by || "System")}</td>`;
   html += `<td style="padding:8px 10px; color:var(--val-text-muted);">${escHtml(dateStr)}</td>`;
   html += `<td style="padding:8px 10px;"><span style="display:inline-block; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700; background:${escHtml(active ? "rgba(255,51,85,0.2)" : "rgba(100,100,120,0.2)")}; color:${escHtml(active ? "#ff3355" : "#888")}; border:1px solid ${escHtml(active ? "#ff3355" : "#555")};">${escHtml(active ? "ACTIVE" : "INACTIVE")}</span></td>`;
   html += "</tr>";
  });
  html += "</tbody></table>";
  container.innerHTML = html;
 }
 if (btnModViewBans && modalViewBans) {
  btnModViewBans.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   modalViewBans.removeAttribute("hidden");
   loadBansTable();
  });
  const btnClose = document.getElementById("btnCloseViewBans");
  if (btnClose) btnClose.addEventListener("click", () => modalViewBans.setAttribute("hidden", ""));
  const btnRefresh = document.getElementById("btnRefreshBans");
  if (btnRefresh) btnRefresh.addEventListener("click", loadBansTable);
  const tabActive = document.getElementById("tabBansActive");
  const tabAll = document.getElementById("tabBansAll");
  if (tabActive && tabAll) {
   tabActive.addEventListener("click", () => {
    tabActive.classList.add("is-active");
    tabAll.classList.remove("is-active");
    currentBansTab = "active";
    renderBansList();
   });
   tabAll.addEventListener("click", () => {
    tabAll.classList.add("is-active");
    tabActive.classList.remove("is-active");
    currentBansTab = "all";
    renderBansList();
   });
  }
 }
 async function loadFlagsTable() {
  const container = document.getElementById("flagsTableContainer");
  if (!container) return;
  container.innerHTML = '<div style="padding:16px; text-align:center; color:var(--val-text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Loading anti-cheat flags...</div>';
  try {
   const flags = await getApi().moderation_get_flags() || [];
   if (!flags.length) {
    container.innerHTML = '<div style="padding:20px; text-align:center; color:#00ff88;"><i class="fa-solid fa-circle-check"></i> No violation flags detected. All client telemetry clean.</div>';
    return;
   }
   let html = '<table style="width:100%; border-collapse:collapse; font-size:12px;">';
   html += '<thead style="background:#161426; color:var(--val-text-muted); text-align:left;"><tr>';
   html += '<th style="padding:8px 10px;">Time</th>';
   html += '<th style="padding:8px 10px;">Player</th>';
   html += '<th style="padding:8px 10px;">Account ID</th>';
   html += '<th style="padding:8px 10px;">Violation Type</th>';
   html += '<th style="padding:8px 10px;">Score</th>';
   html += '<th style="padding:8px 10px;">Details</th>';
   html += '<th style="padding:8px 10px;">Action</th>';
   html += "</tr></thead><tbody>";
   flags.forEach((f, idx) => {
    const timeStr = f.timestamp ? new Date(f.timestamp * 1e3).toLocaleTimeString() : "—";
    const d = f.details || {};
    const reason = d.reason || JSON.stringify(d);
    html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.05); background:${escHtml(idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)")};">`;
    html += `<td style="padding:8px 10px; color:var(--val-text-muted);">${escHtml(timeStr)}</td>`;
    html += `<td style="padding:8px 10px; font-weight:700; color:#fff;">${escHtml(f.in_game_name || "—")}</td>`;
    html += `<td style="padding:8px 10px; font-family:var(--font-mono); color:#c7b8ff;">${escHtml(f.account_id || "—")}</td>`;
    html += `<td style="padding:8px 10px; color:#ff3355; font-weight:700;">${escHtml(f.violation_type)}</td>`;
    html += `<td style="padding:8px 10px; font-weight:700; color:${escHtml(f.violation_score >= 20 ? "#ff3355" : f.violation_score >= 10 ? "#fcd535" : "#38bdf8")};">+${escHtml(f.violation_score)}</td>`;
    html += `<td style="padding:8px 10px; max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--val-text-dim);" title="${escHtml(reason)}">${escHtml(reason)}</td>`;
    html += `<td style="padding:8px 10px;"><button type="button" class="btn-quick-ban" data-acct="${escHtml(f.account_id)}" data-name="${escHtml(f.in_game_name)}" style="padding:3px 8px; font-size:10px; font-weight:700; background:#ff3355; color:#fff; border:none; border-radius:3px; cursor:pointer;">BAN</button></td>`;
    html += "</tr>";
   });
   html += "</tbody></table>";
   container.innerHTML = html;
   container.querySelectorAll(".btn-quick-ban").forEach(btn => {
    btn.addEventListener("click", () => {
     modalViewFlags.setAttribute("hidden", "");
     if (btnModBan) btnModBan.click();
     const searchInput = document.getElementById("inputBanSearch");
     if (searchInput) searchInput.value = btn.dataset.name;
     const searchBtn = document.getElementById("btnBanSearchPlayer");
     if (searchBtn) searchBtn.click();
    });
   });
  } catch (err) {
   container.innerHTML = `<div style="padding:16px; text-align:center; color:#ff3355;">Error loading flags: ${escHtml(err)}</div>`;
  }
 }
 if (btnModViewFlags && modalViewFlags) {
  btnModViewFlags.addEventListener("click", () => {
   playBeep(520, "sine", .08);
   modalViewFlags.removeAttribute("hidden");
   loadFlagsTable();
  });
  const btnClose = document.getElementById("btnCloseViewFlags");
  if (btnClose) btnClose.addEventListener("click", () => modalViewFlags.setAttribute("hidden", ""));
  const btnRefresh = document.getElementById("btnRefreshFlags");
  if (btnRefresh) btnRefresh.addEventListener("click", loadFlagsTable);
 }
}

if (document.readyState === "loading") {
 document.addEventListener("DOMContentLoaded", () => {
  initModerationSystem();
  initOneOnOneSystem();
 });
} else {
 initModerationSystem();
 initOneOnOneSystem();
}

function initOneOnOneSystem() {
 const railBtn1v1 = document.getElementById("railBtn1v1");
 const btn1v1MatchTrigger = document.getElementById("btn1v1MatchTrigger");
 const railBtn1v1Panel = document.getElementById("railBtn1v1Panel");
 const modalMatch = document.getElementById("modalOneOnOneMatch");
 const modalControl = document.getElementById("modalOneOnOneControl");
 const btnCloseMatch = document.getElementById("btnClose1v1Match");
 const btnCancelMatch = document.getElementById("btn1v1Cancel");
 const btnCloseControl = document.getElementById("btnClose1v1Control");
 const btnCloseControlBottom = document.getElementById("btnClose1v1ControlBottom");
 const inputOpponent = document.getElementById("input1v1Opponent");
 const btnCheckOpponent = document.getElementById("btn1v1CheckOpponent");
 const btnMatchNow = document.getElementById("btn1v1MatchNow");
 const statusBox = document.getElementById("status1v1Match");
 const statusIcon = document.getElementById("status1v1Icon");
 const statusText = document.getElementById("status1v1Text");
 const activeBanner = document.getElementById("active1v1Banner");
 const activeDetails = document.getElementById("active1v1Details");
 const btnOpen1v1CPFromMatch = document.getElementById("btnOpen1v1CPFromMatch");
 const cpArena = document.getElementById("cp1v1Arena");
 const cpOpponent = document.getElementById("cp1v1Opponent");
 const cpSessionId = document.getElementById("cp1v1SessionId");
 const tagStatus = document.getElementById("tag1v1Status");
 const btnRefreshStatus = document.getElementById("btnRefresh1v1Status");
 let current1v1Session = null;
 function setMatchStatus(type, message) {
  if (!statusBox) return;
  statusBox.style.display = "flex";
  statusBox.className = "one-on-one-status-box " + (type || "");
  if (type === "error") {
   statusIcon.className = "fa-solid fa-circle-exclamation";
  } else if (type === "success") {
   statusIcon.className = "fa-solid fa-circle-check";
  } else if (type === "info") {
   statusIcon.className = "fa-solid fa-circle-info";
  } else {
   statusIcon.className = "fa-solid fa-circle-notch fa-spin";
  }
  statusText.textContent = message;
 }
 function clearMatchStatus() {
  if (statusBox) statusBox.style.display = "none";
 }
 async function checkSessionStatus() {
  try {
   const api = getApi();
   if (!api || !api.one_on_one_get_status) return null;
   const res = await api.one_on_one_get_status();
   if (res && res.active) {
    current1v1Session = res;
    if (railBtn1v1Panel) railBtn1v1Panel.style.display = "flex";
    if (railBtn1v1) railBtn1v1.classList.add("session-active");
    if (btn1v1MatchTrigger) btn1v1MatchTrigger.classList.add("session-active");
    if (activeBanner) {
     activeBanner.style.display = "flex";
     if (activeDetails) {
      const oppName = res.opponent_name || (res.p1_name === signedInAccount?.username ? res.p2_name : res.p1_name);
      activeDetails.textContent = `Arena: ${res.arena} | Opponent: ${oppName}`;
     }
    }
    if (cpArena) cpArena.textContent = res.arena || "Arena";
    const oppDisplayName = res.opponent_name || (res.p1_name === signedInAccount?.username ? res.p2_name : res.p1_name) || "Opponent";
    if (cpOpponent) cpOpponent.textContent = oppDisplayName;
    if (cpSessionId) cpSessionId.textContent = res.session_id || "#session";
    if (tagStatus) tagStatus.textContent = (res.state || "active").toUpperCase();
    return res;
   } else {
    current1v1Session = null;
    if (railBtn1v1Panel) railBtn1v1Panel.style.display = "none";
    if (railBtn1v1) railBtn1v1.classList.remove("session-active");
    if (btn1v1MatchTrigger) btn1v1MatchTrigger.classList.remove("session-active");
    if (activeBanner) activeBanner.style.display = "none";
    return null;
   }
  } catch (e) {
   return null;
  }
 }
 function openMatchModal() {
  playBeep(520, "sine", .08);
  clearMatchStatus();
  checkSessionStatus();
  if (modalMatch) modalMatch.classList.add("open");
  if (inputOpponent) inputOpponent.focus();
 }
 function closeMatchModal() {
  playBeep(420, "sine", .06);
  if (modalMatch) modalMatch.classList.remove("open");
 }
 function openControlModal() {
  playBeep(560, "sine", .08);
  checkSessionStatus();
  if (modalControl) modalControl.classList.add("open");
 }
 function closeControlModal() {
  playBeep(420, "sine", .06);
  if (modalControl) modalControl.classList.remove("open");
 }
 [ railBtn1v1, btn1v1MatchTrigger ].forEach(btn => {
  if (btn) {
   btn.addEventListener("click", async () => {
    const active = await checkSessionStatus();
    if (active) {
     openControlModal();
    } else {
     openMatchModal();
    }
   });
  }
 });
 if (railBtn1v1Panel) {
  railBtn1v1Panel.addEventListener("click", () => {
   openControlModal();
  });
 }
 if (btnCloseMatch) btnCloseMatch.addEventListener("click", closeMatchModal);
 if (btnCancelMatch) btnCancelMatch.addEventListener("click", closeMatchModal);
 if (btnCloseControl) btnCloseControl.addEventListener("click", closeControlModal);
 if (btnCloseControlBottom) btnCloseControlBottom.addEventListener("click", closeControlModal);
 if (btnOpen1v1CPFromMatch) {
  btnOpen1v1CPFromMatch.addEventListener("click", () => {
   closeMatchModal();
   openControlModal();
  });
 }
 if (btnCheckOpponent && inputOpponent) {
  btnCheckOpponent.addEventListener("click", async () => {
   const opp = inputOpponent.value.trim();
   if (!opp) {
    setMatchStatus("error", "Please enter an opponent username.");
    return;
   }
   setMatchStatus("loading", `Checking availability of '${opp}'...`);
   try {
    const api = getApi();
    const res = await api.one_on_one_check_opponent(opp);
    if (res && res.available) {
     setMatchStatus("success", `Player '${opp}' is ONLINE and ready for 1v1!`);
    } else {
     setMatchStatus("error", res?.reason || res?.message || `Player '${opp}' is not available.`);
    }
   } catch (e) {
    setMatchStatus("error", `Check failed: ${e.message || e}`);
   }
  });
 }
 if (btnMatchNow && inputOpponent) {
  btnMatchNow.addEventListener("click", async () => {
   const opp = inputOpponent.value.trim();
   if (!opp) {
    setMatchStatus("error", "Please enter an opponent username.");
    return;
   }
   setMatchStatus("loading", `Initializing 1v1 match against '${opp}'...`);
   btnMatchNow.disabled = true;
   try {
    const api = getApi();
    const res = await api.one_on_one_match_now(opp);
    if (res && res.success) {
     setMatchStatus("success", res.message || "1v1 Session created! Joining arena...");
     showToast(`1v1 Session created: ${res.arena || "Arena"}!`, "fa-crosshairs");
     setTimeout(() => {
      closeMatchModal();
      openControlModal();
     }, 800);
    } else {
     setMatchStatus("error", res?.message || "Failed to start 1v1 match.");
    }
   } catch (e) {
    setMatchStatus("error", `Match creation error: ${e.message || e}`);
   } finally {
    btnMatchNow.disabled = false;
   }
  });
 }
 async function send1v1Cmd(cmd, args, successMsg) {
  try {
   playBeep(640, "sine", .05);
   const api = getApi();
   const res = await api.one_on_one_control_cmd(cmd, args || {});
   if (res && res.success) {
    if (successMsg) showToast(successMsg, "fa-check");
   } else {
    showToast(res?.error || res?.message || `Command ${cmd} failed`, "fa-triangle-exclamation");
   }
   return res;
  } catch (e) {
   showToast(`Error: ${e.message || e}`, "fa-circle-xmark");
  }
 }
 const btnCubes500 = document.getElementById("btn1v1Cubes500");
 if (btnCubes500) {
  btnCubes500.addEventListener("click", () => {
   send1v1Cmd("fill_cubes", {
    amount: 500
   }, "Added 500 Quantum Cubes!");
  });
 }
 const btnSetCustomCubes = document.getElementById("btn1v1SetCustomCubes");
 const inputCustomCubes = document.getElementById("input1v1CustomCubes");
 if (btnSetCustomCubes && inputCustomCubes) {
  btnSetCustomCubes.addEventListener("click", () => {
   const amt = parseInt(inputCustomCubes.value) || 500;
   send1v1Cmd("fill_cubes", {
    amount: amt
   }, `Set Quantum Cubes to ${amt}!`);
  });
 }
 const btnRefillAmmo = document.getElementById("btn1v1RefillAmmo");
 if (btnRefillAmmo) {
  btnRefillAmmo.addEventListener("click", () => {
   send1v1Cmd("refill_ammo", {
    reserve: 9999
   }, "Refilled all weapon ammo to max!");
  });
 }
 const btnRestoreVitals = document.getElementById("btn1v1RestoreVitals");
 if (btnRestoreVitals) {
  btnRestoreVitals.addEventListener("click", () => {
   send1v1Cmd("restore_vitals", {}, "Restored full HP (100) & Shield (100)!");
  });
 }
 const btnGiveMeds = document.getElementById("btn1v1GiveMeds");
 if (btnGiveMeds) {
  btnGiveMeds.addEventListener("click", () => {
   send1v1Cmd("give_meds", {}, "Added medkits, energy drinks & armor supplies!");
  });
 }
 const btnTeleportCloser = document.getElementById("btn1v1TeleportCloser");
 if (btnTeleportCloser) {
  btnTeleportCloser.addEventListener("click", () => {
   send1v1Cmd("teleport_closer", {}, "Teleported closer to opponent (35m)!");
  });
 }
 const btnForceRespawn = document.getElementById("btn1v1ForceRespawn");
 if (btnForceRespawn) {
  btnForceRespawn.addEventListener("click", () => {
   send1v1Cmd("respawn_player", {}, "Instant respawn executed!");
  });
 }
 const btnApplyWeapons = document.getElementById("btn1v1ApplyWeapons");
 const selPrimary = document.getElementById("sel1v1PrimaryWeapon");
 const selSecondary = document.getElementById("sel1v1SecondaryWeapon");
 const chkAttachments = document.getElementById("chk1v1FullAttachments");
 if (btnApplyWeapons && selPrimary && selSecondary) {
  btnApplyWeapons.addEventListener("click", () => {
   const pri = parseInt(selPrimary.value) || 3100;
   const sec = parseInt(selSecondary.value) || 3200;
   const atts = chkAttachments && chkAttachments.checked ? [ 8e3, 8001, 8002, 8003 ] : [];
   send1v1Cmd("select_weapons", {
    primary: pri,
    secondary: sec,
    attachments: atts
   }, "Custom 1v1 weapon loadout applied!");
  });
 }
 const btnGiveThrowables = document.getElementById("btn1v1GiveThrowables");
 if (btnGiveThrowables) {
  btnGiveThrowables.addEventListener("click", () => {
   send1v1Cmd("select_throwables", {
    throwables: [ 7e3, 7001 ]
   }, "Added Frag Grenades & Smoke Grenades!");
  });
 }
 const btnResetSkills = document.getElementById("btn1v1ResetSkills");
 if (btnResetSkills) {
  btnResetSkills.addEventListener("click", () => {
   send1v1Cmd("select_skills", {}, "Refreshed Droid Skills!");
  });
 }
 const btnClearInventory = document.getElementById("btnClearInventory");
 if (btnClearInventory) {
  btnClearInventory.addEventListener("click", () => {
   send1v1Cmd("clear_inventory", {}, "Cleared inventory items & weapons.");
  });
 }
 const btnResetLoadout = document.getElementById("btnResetLoadout");
 if (btnResetLoadout) {
  btnResetLoadout.addEventListener("click", () => {
   send1v1Cmd("reset_loadout", {}, "Reset to standard 1v1 loadout.");
  });
 }
 const btnSpawnVehicle = document.getElementById("btn1v1SpawnVehicle");
 const selVehicle = document.getElementById("sel1v1Vehicle");
 if (btnSpawnVehicle && selVehicle) {
  btnSpawnVehicle.addEventListener("click", () => {
   const veh = parseInt(selVehicle.value) || 4200;
   send1v1Cmd("spawn_vehicle", {
    vehicle_type: veh
   }, "Spawned vehicle in front of player!");
  });
 }
 const btnRepairVehicle = document.getElementById("btn1v1RepairVehicle");
 if (btnRepairVehicle) {
  btnRepairVehicle.addEventListener("click", () => {
   send1v1Cmd("repair_vehicle", {}, "Repaired and refueled active vehicles!");
  });
 }
 const btnRemoveVehicles = document.getElementById("btn1v1RemoveVehicles");
 if (btnRemoveVehicles) {
  btnRemoveVehicles.addEventListener("click", () => {
   send1v1Cmd("remove_vehicle", {}, "Removed vehicles from arena.");
  });
 }
 const btnRestartMatch = document.getElementById("btn1v1RestartMatch");
 if (btnRestartMatch) {
  btnRestartMatch.addEventListener("click", () => {
   send1v1Cmd("restart_match", {}, "Restarted 1v1 match round!");
  });
 }
 const btnEndSession = document.getElementById("btn1v1EndSession");
 if (btnEndSession) {
  btnEndSession.addEventListener("click", async () => {
   if (confirm("End this 1v1 session and return both players safely to lobby?")) {
    await send1v1Cmd("end_session", {}, "1v1 session ended. Returning to lobby...");
    closeControlModal();
    checkSessionStatus();
   }
  });
 }
 if (btnRefreshStatus) {
  btnRefreshStatus.addEventListener("click", () => {
   checkSessionStatus();
   showToast("1v1 session status updated", "fa-rotate");
  });
 }
 setInterval(() => {
  checkSessionStatus();
 }, 6e3);
}