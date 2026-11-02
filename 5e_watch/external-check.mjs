#!/usr/bin/env node
/**
 * Внешняя проверка платформы по публичным именам (временная мера, инцидент
 * 2026-11-02 — Beget DNS лёг, VPS жив, узнали из новостей).
 *
 * Запускается ВНЕ нашего VPS (GitHub Actions по расписанию) и проверяет то,
 * что видит пользователь:
 *   - имена разрешаются через два независимых публичных резолвера (DoH
 *     Cloudflare и Google) и указывают на ожидаемый адрес;
 *   - HTTPS по имени отдаёт ожидаемый код (сайт — 200; files — 404 на обычный
 *     GET, так задано контрактом; загрузка проверяется отдельно);
 *   - если по имени не открывается — то же по IP с правильными Host и SNI,
 *     чтобы тревога различала «DNS не отвечает, сервер жив» и «сервер лежит»;
 *   - срок сертификата и регистрации домена;
 *   - свежесть пульса, если задан EXTERNAL_PULSE_URL.
 *
 * Тревога в Telegram — при смене состояния и напоминание раз в час, пока
 * проблема держится. Состояние между запусками — файл EXTERNAL_STATE_FILE
 * (в workflow его переносит кеш). Расписание GitHub может задерживаться и
 * пропускать запуски: гарантированного времени обнаружения нет.
 *
 * Переменные: EXTERNAL_TARGETS (JSON, по умолчанию — ниже), EXTERNAL_IP,
 * EXTERNAL_DOMAIN, EXTERNAL_PULSE_URL, EXTERNAL_PULSE_MAX_AGE_S,
 * EXTERNAL_STATE_FILE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
 * Ключ --dry: только отчёт, без Telegram.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import https from 'node:https';
import tls from 'node:tls';
import { pathToFileURL } from 'node:url';

const IP = process.env.EXTERNAL_IP || '193.233.217.210';
const DOMAIN = process.env.EXTERNAL_DOMAIN || '5espace.com';
const TARGETS = process.env.EXTERNAL_TARGETS
  ? JSON.parse(process.env.EXTERNAL_TARGETS)
  : [
      { name: '5espace.com', path: '/', expect: 200 },
      { name: 'files.5espace.com', path: '/', expect: 404 },
    ];
const PULSE_URL = process.env.EXTERNAL_PULSE_URL || '';
const PULSE_MAX_AGE_S = Number(process.env.EXTERNAL_PULSE_MAX_AGE_S || 600);
const STATE_FILE = process.env.EXTERNAL_STATE_FILE || '.external-check/state.json';
const CERT_WARN_DAYS = 14;
const DOMAIN_WARN_DAYS = 30;
const REMIND_MS = 60 * 60 * 1000;
const TIMEOUT_MS = 12_000;
const DRY = process.argv.includes('--dry');

const RESOLVERS = {
  Cloudflare: (n) => `https://cloudflare-dns.com/dns-query?name=${n}&type=A`,
  Google: (n) => `https://dns.google/resolve?name=${n}&type=A`,
};

async function resolveVia(resolver, name) {
  try {
    const res = await fetch(RESOLVERS[resolver](name), {
      headers: { accept: 'application/dns-json' },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    const j = await res.json();
    const ips = (j.Answer || []).filter((a) => a.type === 1).map((a) => a.data);
    return { ok: ips.includes(IP), detail: ips.length ? ips.join(',') : `Status ${j.Status}` };
  } catch (e) {
    return { ok: false, detail: `нет ответа резолвера (${e.name})` };
  }
}

/** GET по адресу `connectTo` с Host и SNI = name; сертификат проверяется. */
function httpsGet(name, path, connectTo) {
  return new Promise((resolve) => {
    const req = https.request(
      {
        host: connectTo,
        servername: name,
        headers: { host: name, 'user-agent': '5e-external-check' },
        path,
        method: 'GET',
        timeout: TIMEOUT_MS,
      },
      (res) => {
        res.resume();
        resolve({ code: res.statusCode });
      },
    );
    req.on('timeout', () => req.destroy(new Error('таймаут')));
    req.on('error', (e) => resolve({ code: 0, error: e.code || e.message }));
    req.end();
  });
}

/**
 * Дней до конца сертификата или null. Любой исход — рукопожатие, ошибка,
 * таймаут, закрытие до рукопожатия — завершает ожидание (замечание Тэнка:
 * зависшая проверка не должна блокировать отправку тревог). Сверх таймаута
 * сокета — общий сторожевой таймер.
 */
export function certDaysLeft(name, connect = tls.connect, guardMs = TIMEOUT_MS + 1_000) {
  return new Promise((resolve) => {
    let done = false;
    let sock;
    const finish = (value) => {
      if (done) return;
      done = true;
      clearTimeout(guard);
      sock?.destroy();
      resolve(value);
    };
    const guard = setTimeout(() => finish(null), guardMs);
    try {
      sock = connect({ host: IP, port: 443, servername: name, timeout: TIMEOUT_MS }, () => {
        const cert = sock.getPeerCertificate();
        const left = cert?.valid_to ? (new Date(cert.valid_to) - Date.now()) / 86_400_000 : NaN;
        finish(Number.isFinite(left) ? left : null);
      });
    } catch {
      finish(null);
      return;
    }
    sock.on('timeout', () => finish(null));
    sock.on('error', () => finish(null));
    sock.on('close', () => finish(null));
  });
}

/**
 * Оценка пульса: подтверждён только ответ 200 с JSON, где ok строго true, а
 * время at корректно, не старше порога и не из будущего (больше допуска на
 * расхождение часов). Пустой, неполный или неверный ответ — отказ.
 */
export const PULSE_FUTURE_SKEW_S = 120;
export function evaluatePulse(status, body, now = Date.now(), maxAgeS = PULSE_MAX_AGE_S) {
  if (status !== 200)
    return { ok: false, line: `HTTP ${status}`, text: `пульс: ответ HTTP ${status}` };
  if (!body || typeof body !== 'object')
    return { ok: false, line: 'не JSON', text: 'пульс: ответ не JSON' };
  const at =
    typeof body.at === 'string' || typeof body.at === 'number' ? new Date(body.at).getTime() : NaN;
  if (!Number.isFinite(at))
    return { ok: false, line: 'нет времени', text: 'пульс: нет корректного времени at' };
  const age = (now - at) / 1000;
  if (age < -PULSE_FUTURE_SKEW_S)
    return {
      ok: false,
      line: `время из будущего (${Math.round(-age)} с)`,
      text: `пульс: время в будущем на ${Math.round(-age)} с`,
    };
  if (age > maxAgeS)
    return {
      ok: false,
      line: `${Math.round(age)} с назад`,
      text: `пульс устарел: ${Math.round(age)} с (порог ${maxAgeS})`,
    };
  if (body.ok !== true)
    return {
      ok: false,
      line: `${Math.round(age)} с назад, итог не ok`,
      text: 'пульс: итог проверки Zabbix — отказ',
    };
  return { ok: true, line: `${Math.round(Math.max(age, 0))} с назад, ok` };
}

async function domainDaysLeft() {
  try {
    const res = await fetch(`https://rdap.verisign.com/com/v1/domain/${DOMAIN}`, {
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    const j = await res.json();
    const ev = (j.events || []).find((e) => e.eventAction === 'expiration');
    return ev ? (new Date(ev.eventDate) - Date.now()) / 86_400_000 : null;
  } catch {
    return null;
  }
}

async function run() {
  const problems = []; // { key, text }
  const lines = [];

  for (const t of TARGETS) {
    const dns = {};
    for (const r of Object.keys(RESOLVERS)) dns[r] = await resolveVia(r, t.name);
    const dnsOk = Object.values(dns).some((d) => d.ok);
    lines.push(
      `${t.name} DNS: ` +
        Object.entries(dns)
          .map(([r, d]) => `${r} ${d.ok ? 'ok' : 'FAIL'} (${d.detail})`)
          .join('; '),
    );

    const byName = dnsOk ? await httpsGet(t.name, t.path, t.name) : null;
    const byIp = await httpsGet(t.name, t.path, IP);
    const ipOk = byIp.code === t.expect;
    lines.push(
      `${t.name} HTTPS GET ${t.path}, ожидается ${t.expect}: по имени ${
        byName ? byName.code || byName.error : 'не проверено (DNS)'
      }; по IP ${byIp.code || byIp.error}`,
    );

    if (!dnsOk) {
      problems.push({
        key: `dns:${t.name}`,
        text: ipOk
          ? `${t.name}: имя не разрешается (DNS), сервер по IP отвечает ${byIp.code} — пользователи сайт не откроют, VPS исправен`
          : `${t.name}: имя не разрешается (DNS) И по IP нет ожидаемого ответа (${byIp.code || byIp.error})`,
      });
    } else if (byName.code !== t.expect) {
      problems.push({
        key: `http:${t.name}`,
        text: `${t.name}: по имени ${byName.code || byName.error}, ожидается ${t.expect}; по IP ${
          byIp.code || byIp.error
        }`,
      });
    }

    const days = await certDaysLeft(t.name);
    lines.push(
      `${t.name} сертификат: ${days === null ? 'не прочитан' : `${Math.floor(days)} дн.`}`,
    );
    if (days === null)
      problems.push({ key: `cert:${t.name}`, text: `${t.name}: сертификат не прочитан` });
    else if (days < CERT_WARN_DAYS)
      problems.push({
        key: `cert:${t.name}`,
        text: `${t.name}: сертификат истекает через ${Math.floor(days)} дн.`,
      });
  }

  const dd = await domainDaysLeft();
  lines.push(`${DOMAIN} регистрация: ${dd === null ? 'не прочитана' : `${Math.floor(dd)} дн.`}`);
  if (dd !== null && dd < DOMAIN_WARN_DAYS)
    problems.push({
      key: 'domain',
      text: `${DOMAIN}: регистрация истекает через ${Math.floor(dd)} дн.`,
    });

  if (PULSE_URL) {
    let verdict;
    try {
      const res = await fetch(PULSE_URL, { signal: AbortSignal.timeout(TIMEOUT_MS) });
      let body = null;
      try {
        body = await res.json();
      } catch {
        /* не JSON — оценка ниже даст отказ */
      }
      verdict = evaluatePulse(res.status, body);
    } catch (e) {
      verdict = { ok: false, line: `нет ответа (${e.name})`, text: 'пульс не читается' };
    }
    lines.push(`пульс: ${verdict.line}`);
    if (!verdict.ok) problems.push({ key: 'pulse', text: verdict.text });
  }

  return { problems, lines };
}

function loadState() {
  try {
    return JSON.parse(readFileSync(STATE_FILE, 'utf8'));
  } catch {
    return { open: {} };
  }
}

async function telegram(text) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chat = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chat) return false;
  try {
    const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: chat, text }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function main() {
  const { problems, lines } = await run();
  const now = Date.now();
  const state = loadState();
  const messages = [];
  const open = {};

  for (const p of problems) {
    const prev = state.open[p.key];
    if (!prev) {
      messages.push(`🔴 5Э снаружи: ${p.text}`);
      open[p.key] = { since: now, notified: now };
    } else if (now - prev.notified >= REMIND_MS) {
      const min = Math.round((now - prev.since) / 60_000);
      messages.push(`🔴 5Э снаружи, держится ${min} мин: ${p.text}`);
      open[p.key] = { since: prev.since, notified: now };
    } else {
      open[p.key] = prev;
    }
  }
  for (const [key, prev] of Object.entries(state.open)) {
    if (!open[key]) {
      const min = Math.round((now - prev.since) / 60_000);
      messages.push(`🟢 5Э снаружи: восстановлено (${key}), длилось ~${min} мин`);
    }
  }

  console.log(lines.join('\n'));
  console.log(problems.length ? `ПРОБЛЕМ: ${problems.length}` : 'всё в порядке');

  let sent = true;
  if (messages.length && !DRY) {
    sent = await telegram(messages.join('\n'));
    console.log(sent ? 'тревога отправлена' : 'ТРЕВОГА НЕ ОТПРАВЛЕНА (Telegram)');
  }
  // Неотправленное не помечаем отправленным — повторим в следующем запуске.
  if (!DRY && sent) {
    mkdirSync(dirname(STATE_FILE), { recursive: true });
    writeFileSync(STATE_FILE, JSON.stringify({ open, at: now }));
  }
  // Красный запуск — только когда тревога НЕ дошла до Telegram: тогда письмо
  // GitHub о провале становится запасным каналом. Сама проблема запуск не
  // краснит — иначе письмо приходило бы каждые 5 минут, пока она держится.
  process.exitCode = sent ? 0 : 1;
}

// Запуск только как программа; при импорте (тесты) — ничего не делаем.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();
