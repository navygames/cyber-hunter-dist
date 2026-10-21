"use strict";

const fs = require("fs");

const path = require("path");

const SRC_DIR = __dirname;

const ROOT = path.resolve(SRC_DIR, "..", "..");

const ENV_FILE = path.join(SRC_DIR, "..", ".env");

const CORE = path.join(SRC_DIR, "supabase_core.js");

function hasDbConfig() {
 if (process.env.SUPABASE_DATABASE_URL || process.env.DATABASE_URL) return true;
 try {
  const txt = fs.readFileSync(ENV_FILE, "utf8");
  return /^\s*(SUPABASE_DATABASE_URL|DATABASE_URL)\s*=\s*\S+/m.test(txt);
 } catch (e) {
  return false;
 }
}

function readKv(file) {
 const out = {};
 try {
  const txt = fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
  for (const raw of txt.split(/\r?\n/)) {
   const line = raw.trim();
   if (!line || line.startsWith("#") || line.indexOf("=") < 0) continue;
   const i = line.indexOf("=");
   out[line.slice(0, i).trim()] = line.slice(i + 1).trim().replace(/^["']|["']$/g, "");
  }
 } catch (e) {}
 return out;
}

function revivalConfig() {
 const candidates = [ path.join(ROOT, "Config", "revival_config.env"), path.join(ROOT, "revival_config.env"), path.join(ROOT, "revival_config.env.example") ];
 for (const c of candidates) {
  if (fs.existsSync(c)) return readKv(c);
 }
 return {};
}

function runtimeDir() {
 const alt = path.join(ROOT, "Runtime", "runtime");
 return fs.existsSync(alt) ? alt : path.join(ROOT, "client", "runtime");
}

const SESSION_FILE = path.join(runtimeDir(), "relay_session.json");

function loadSessions() {
 try {
  const s = JSON.parse(fs.readFileSync(SESSION_FILE, "utf8"));
  if (s && typeof s === "object" && s.tokens && typeof s.tokens === "object") return s;
 } catch (e) {}
 return {
  last: "",
  tokens: {}
 };
}

function saveSessions(s) {
 try {
  fs.mkdirSync(path.dirname(SESSION_FILE), {
   recursive: true
  });
  const tmp = SESSION_FILE + "." + process.pid + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(s));
  fs.renameSync(tmp, SESSION_FILE);
 } catch (e) {}
}

function actingUser(cmd, arg) {
 const o = arg && typeof arg === "object" ? arg : null;
 const s = typeof arg === "string" ? arg : "";
 switch (cmd) {
 case "give_praise":
 case "send_gift":
  return o ? o.from_username || "" : "";

 case "social_request":
  return o ? o.from || "" : s;

 case "set_hero_name":
 case "save_user_stats":
 case "record_match":
 case "list_friends":
 case "social_friends":
 case "social_accept":
 case "social_reject":
 case "social_remove":
  return o ? o.username || "" : s;

 default:
  return "";
 }
}

function pickToken(sessions, user) {
 const now = Math.floor(Date.now() / 1e3);
 const keys = [];
 if (user) keys.push(String(user).toLowerCase());
 if (sessions.last) keys.push(sessions.last);
 for (const k of keys) {
  const t = sessions.tokens[k];
  if (t && t.token && (!t.exp || t.exp > now)) return t.token;
 }
 return "";
}

function post(host, port, caPem, body, token) {
 const https = require("https");
 return new Promise((resolve, reject) => {
  const data = Buffer.from(JSON.stringify(body), "utf8");
  const req = https.request({
   host: host,
   port: port,
   method: "POST",
   path: "/sync",
   ca: caPem,
   headers: {
    "Content-Type": "application/json",
    "Content-Length": data.length,
    Authorization: token ? "Bearer " + token : ""
   },
   timeout: 7e3
  }, res => {
   const chunks = [];
   res.on("data", c => chunks.push(c));
   res.on("end", () => {
    if (res.statusCode !== 200) return reject(new Error("HTTP " + res.statusCode));
    try {
     resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
    } catch (e) {
     reject(e);
    }
   });
  });
  req.on("timeout", () => req.destroy(new Error("timeout")));
  req.on("error", reject);
  req.end(data);
 });
}

function loadPins() {
 const files = [ path.join(ROOT, "tools", "private_server", "certs", "server_pins.json"), path.join(ROOT, "Runtime", "tools", "certs", "server_pins.json") ];
 const out = new Set;
 for (const f of files) {
  try {
   const d = JSON.parse(fs.readFileSync(f, "utf8"));
   for (const h of d.sha256 || []) {
    const x = String(h).toLowerCase().replace(/[^0-9a-f]/g, "");
    if (x.length === 64) out.add(x);
   }
  } catch (e) {}
 }
 return out;
}

function postPinned(host, port, pins, body, token) {
 const tls = require("tls");
 const crypto = require("crypto");
 return new Promise((resolve, reject) => {
  const data = Buffer.from(JSON.stringify(body), "utf8");
  const sock = tls.connect({
   host: host,
   port: port,
   rejectUnauthorized: false,
   servername: undefined
  });
  const chunks = [];
  let ok = false;
  sock.setTimeout(7e3, () => sock.destroy(new Error("timeout")));
  sock.on("secureConnect", () => {
   const cert = sock.getPeerCertificate(false);
   const fp = cert && cert.raw ? crypto.createHash("sha256").update(cert.raw).digest("hex") : "";
   if (!pins.has(fp)) {
    sock.destroy(new Error("PIN mismatch"));
    return;
   }
   ok = true;
   sock.write("POST /sync HTTP/1.1\r\nHost: " + host + ":" + port + "\r\n" + "Content-Type: application/json\r\nContent-Length: " + data.length + "\r\n" + (token ? "Authorization: Bearer " + token + "\r\n" : "") + "Connection: close\r\n\r\n");
   sock.write(data);
  });
  sock.on("data", c => chunks.push(c));
  sock.on("error", reject);
  sock.on("end", () => {
   if (!ok) return reject(new Error("closed"));
   const raw = Buffer.concat(chunks).toString("utf8");
   const i = raw.indexOf("\r\n\r\n");
   const head = i >= 0 ? raw.slice(0, i) : raw;
   let bodyTxt = i >= 0 ? raw.slice(i + 4) : "";
   const m = /^HTTP\/1\.[01] (\d{3})/.exec(head);
   const status = m ? parseInt(m[1], 10) : 0;
   if (/transfer-encoding:\s*chunked/i.test(head)) {
    let out = "", rest = bodyTxt;
    while (rest.length) {
     const j = rest.indexOf("\r\n");
     if (j < 0) break;
     const n = parseInt(rest.slice(0, j), 16);
     if (!n) break;
     out += rest.substr(j + 2, n);
     rest = rest.slice(j + 2 + n + 2);
    }
    bodyTxt = out;
   }
   if (status !== 200) return reject(new Error("HTTP " + status));
   try {
    resolve(JSON.parse(bodyTxt));
   } catch (e) {
    reject(e);
   }
  });
 });
}

async function relayMain() {
 const argv = process.argv.slice(2);
 let outPath = null;
 const outIdx = argv.findIndex(a => typeof a === "string" && a.startsWith("--out="));
 if (outIdx !== -1) {
  outPath = argv[outIdx].slice("--out=".length);
  argv.splice(outIdx, 1);
  try {
   fs.writeFileSync(outPath, "");
  } catch (e) {}
 }
 const emit = obj => {
  const line = JSON.stringify(obj) + "\n";
  if (outPath) {
   try {
    fs.appendFileSync(outPath, line);
   } catch (e) {}
  } else process.stdout.write(line);
 };
 const cmd = argv[0] || "";
 let arg = argv[1] || "";
 if (arg && arg.startsWith("@")) {
  try {
   arg = fs.readFileSync(arg.slice(1), "utf8").replace(/^\uFEFF/, "");
  } catch (e) {
   arg = "";
  }
 }
 let parsedArg = arg;
 if (arg && (arg.startsWith("{") || arg.startsWith("["))) {
  try {
   parsedArg = JSON.parse(arg);
  } catch (e) {}
 }
 if (!cmd || cmd === "seed" || cmd === "test_stats") process.exit(1);
 const cfg = revivalConfig();
 const host = (cfg.REVIVAL_SERVER_IP || "").trim();
 if (!host || host === "127.0.0.1" || host === "localhost") process.exit(1);
 const port = parseInt(cfg.REVIVAL_SYNC_PORT || "3443", 10) || 3443;
 const caCandidates = [ path.join(ROOT, "tools", "private_server", "certs", "ca.cert.pem"), path.join(ROOT, "Runtime", "tools", "certs", "ca.cert.pem") ];
 const caFile = caCandidates.find(p => fs.existsSync(p));
 const pins = loadPins();
 if (!caFile && !pins.size) process.exit(1);
 const caPem = caFile ? fs.readFileSync(caFile) : null;
 const sessions = loadSessions();
 const token = pickToken(sessions, actingUser(cmd, parsedArg));
 let reply = null;
 const ports = [ port ].concat(port === 443 ? [] : [ 443 ]);
 for (let i = 0; i < ports.length; i++) {
  let err = null;
  if (caPem) {
   try {
    reply = await post(host, ports[i], caPem, {
     cmd: cmd,
     arg: parsedArg
    }, token);
    break;
   } catch (e) {
    err = e;
   }
  }
  const certErr = !caPem || err && (err.code || "").match(/CERT|SIGNATURE|ISSUER|SELF_SIGNED|ALTNAME/);
  if (pins.size && certErr) {
   try {
    reply = await postPinned(host, ports[i], pins, {
     cmd: cmd,
     arg: parsedArg
    }, token);
    break;
   } catch (e) {
    err = e;
   }
  }
  if (err && /^HTTP \d+/.test(String(err.message))) process.exit(1);
 }
 if (!reply || reply.ok !== true) process.exit(1);
 const result = reply.result;
 if ((cmd === "login" || cmd === "signup") && reply.relay_token && result && result.success) {
  const u = String(result.user && result.user.username || parsedArg && parsedArg.username || "").toLowerCase();
  if (u) {
   sessions.tokens[u] = {
    token: reply.relay_token,
    exp: reply.relay_exp || 0
   };
   sessions.last = u;
   saveSessions(sessions);
  }
 }
 if (result === undefined || result === null) process.exit(1);
 emit(result);
}

if (hasDbConfig() && fs.existsSync(CORE)) {
 const core = require(CORE);
 core.main().catch(err => {
  console.error("Supabase DB error:", err);
  process.exit(1);
 });
} else {
 relayMain().catch(() => process.exit(1));
}