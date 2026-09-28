// Hunter Sistemi — zamanlanmış anlık bildirim gönderici (GitHub Actions)
// Oyun, gönderilecek bildirimlerin planını (S.notif.plan) kayda yazar; bu betik
// her çalıştığında vakti gelenleri kayıtlı cihazlara Web Push ile yollar.
import fs from "node:fs";
import crypto from "node:crypto";
import { pathToFileURL } from "node:url";

const API_KEY = "AIzaSyBsNalG4Fl7crcsluhf2hqDXlWawD6DJ2I";
const PROJECT = "hunter-sistemi";
const WIN = 2 * 3600 * 1000; // vakti geçen bildirim en fazla 2 saat içinde gönderilir

function b64uDec(t) { return Buffer.from(t, "base64url"); }

/* ---- Web Push (RFC 8291 aes128gcm + RFC 8292 VAPID), bağımlılıksız ---- */
const hmac = (k, d) => crypto.createHmac("sha256", k).update(d).digest();
export function encrypt(payload, uaPub, auth, opt = {}) {
  const ecdh = opt.ecdh || crypto.createECDH("prime256v1");
  if (!opt.ecdh) ecdh.generateKeys();
  const asPub = ecdh.getPublicKey();
  const secret = ecdh.computeSecret(uaPub);
  const prkKey = hmac(auth, secret);
  const keyInfo = Buffer.concat([Buffer.from("WebPush: info\0"), uaPub, asPub]);
  const ikm = hmac(prkKey, Buffer.concat([keyInfo, Buffer.from([1])]));
  const salt = opt.salt || crypto.randomBytes(16);
  const prk = hmac(salt, ikm);
  const cek = hmac(prk, Buffer.from("Content-Encoding: aes128gcm\0\x01")).subarray(0, 16);
  const nonce = hmac(prk, Buffer.from("Content-Encoding: nonce\0\x01")).subarray(0, 12);
  const c = crypto.createCipheriv("aes-128-gcm", cek, nonce);
  const ct = Buffer.concat([c.update(Buffer.concat([Buffer.from(payload), Buffer.from([2])])), c.final(), c.getAuthTag()]);
  const rs = Buffer.alloc(4); rs.writeUInt32BE(4096);
  return Buffer.concat([salt, rs, Buffer.from([asPub.length]), asPub, ct]);
}
function vapidAuth(endpoint, v) {
  const aud = new URL(endpoint).origin;
  const h = Buffer.from(JSON.stringify({ typ: "JWT", alg: "ES256" })).toString("base64url");
  const b = Buffer.from(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: v.subject })).toString("base64url");
  const key = crypto.createPrivateKey({ key: { kty: "EC", crv: "P-256", d: v.priv, x: v.x, y: v.y }, format: "jwk" });
  const sig = crypto.sign("sha256", Buffer.from(h + "." + b), { key, dsaEncoding: "ieee-p1363" }).toString("base64url");
  return `vapid t=${h}.${b}.${sig}, k=${v.pub}`;
}
const webpush = {
  v: null,
  setVapidDetails(subject, pub, priv, x, y) { this.v = { subject, pub, priv, x, y }; },
  async sendNotification(sub, payload, o = {}) {
    const body = encrypt(payload, b64uDec(sub.keys.p256dh), b64uDec(sub.keys.auth));
    const r = await fetch(sub.endpoint, { method: "POST", body, headers: {
      "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream",
      TTL: String(o.TTL || 3600), Urgency: o.urgency || "normal", Authorization: vapidAuth(sub.endpoint, this.v) } });
    if (r.status >= 300) { const e = new Error("push reddedildi"); e.statusCode = r.status; e.body = await r.text().catch(() => ""); throw e; }
    return r.status;
  },
};
function log(...a) { console.log(...a); }

function parseSecret(raw) {
  raw = (raw || "").trim();
  if (!raw) return null;
  if (raw.startsWith("HS1.")) raw = raw.slice(4);
  const o = JSON.parse(b64uDec(raw).toString("utf8"));
  const pub = Buffer.concat([Buffer.from([4]), b64uDec(o.x), b64uDec(o.y)]).toString("base64url");
  if (o.p && o.p !== pub) throw new Error("anahtar tutarsız");
  return { codes: (o.c || []).filter(Boolean), priv: o.d, x: o.x, y: o.y, pub };
}

async function loadState(code) {
  const url = `https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents/saves/${encodeURIComponent(code)}?key=${API_KEY}&mask.fieldPaths=state`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`kayıt okunamadı (${r.status})`);
  const j = await r.json();
  const s = j.fields && j.fields.state && j.fields.state.stringValue;
  return s ? JSON.parse(s) : null;
}

export async function run(env = process.env, deps = {}) {
  const wp = deps.webpush || webpush;
  const load = deps.loadState || loadState;
  const NOW = Number(env.PUSH_NOW) || Date.now();
  let cfg;
  try { cfg = parseSecret(env.HUNTER_PUSH); }
  catch (e) { log("HUNTER_PUSH okunamadı:", e.message); return { sent: 0 }; }
  if (!cfg) { log("HUNTER_PUSH tanımlı değil; yapılacak bir şey yok."); return { sent: 0 }; }
  wp.setVapidDetails("mailto:hunter-sistemi@users.noreply.github.com", cfg.pub, cfg.priv, cfg.x, cfg.y);

  const LOG = env.PUSH_LOG || ".pushlog/sent.json";
  let sentLog = {};
  try { sentLog = JSON.parse(fs.readFileSync(LOG, "utf8")); } catch (e) {}
  let total = 0;
  const report = [];
  for (const code of cfg.codes) {
    const tag = code.slice(0, 4);
    let S;
    try { S = await load(code); } catch (e) { log(`[${tag}] ${e.message}`); continue; }
    const N = S && S.notif;
    if (!N || !N.on) { log(`[${tag}] bildirimler kapalı`); continue; }
    const subs = Object.entries(N.subs || {}).filter(([, v]) => v && v.e && v.k);
    if (!subs.length) { log(`[${tag}] kayıtlı cihaz yok`); continue; }
    const sent = N.sent || {};
    const due = (N.plan || []).filter(it => it && it.id && !it.lo && it.at <= NOW && NOW - it.at < WIN && !sent[it.id] && !sentLog[`${code}|${it.id}`]);
    // aynı anda birden çok gün sonu durum kartı birikirse yalnızca sonuncusu yeterli
    const lastSo = due.filter(it => it.so).pop();
    const list = due.filter(it => !it.so || it === lastSo).slice(-4);
    for (const it of list) {
      const payload = JSON.stringify({ id: it.id, ti: it.ti, b: it.b, tag: it.tag, go: it.go, st: it.st, so: it.so });
      let okAny = false;
      for (const [dev, v] of subs) {
        try {
          await wp.sendNotification({ endpoint: v.e, keys: v.k }, payload, { TTL: 3 * 3600, urgency: it.so ? "normal" : "high" });
          okAny = true;
          report.push(`${it.id} → ${v.n || dev}: gönderildi`);
        } catch (e) {
          report.push(`${it.id} → ${v.n || dev}: HATA ${e.statusCode || ""} ${(e.body || e.message || "").toString().slice(0, 120)}`);
        }
      }
      if (okAny) { sentLog[`${code}|${it.id}`] = NOW; total++; }
    }
    log(`[${tag}] plan ${(N.plan || []).length}, vakti gelen ${due.length}, gönderilen ${list.length}`);
  }
  for (const k in sentLog) if (NOW - sentLog[k] > 5 * 86400000) delete sentLog[k];
  fs.mkdirSync(LOG.replace(/\/[^/]*$/, ""), { recursive: true });
  fs.writeFileSync(LOG, JSON.stringify(sentLog));
  report.forEach(r => log("  " + r));
  return { sent: total, report };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().catch(e => { console.log("Beklenmeyen hata:", e && e.message); });
}
