// Проверки разбора пульса и завершения проверки сертификата.
// Запуск: node --test 5e_watch/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { evaluatePulse, certDaysLeft } from './external-check.mjs';

const NOW = Date.parse('2026-11-02T12:00:00Z');
const at = (s) => new Date(NOW - s * 1000).toISOString();

test('пульс: пустой, неполный и неверный ответ — отказ', () => {
  assert.equal(evaluatePulse(200, {}, NOW, 600).ok, false);
  assert.equal(evaluatePulse(200, null, NOW, 600).ok, false);
  assert.equal(evaluatePulse(200, { at: at(10) }, NOW, 600).ok, false); // нет ok
  assert.equal(evaluatePulse(200, { ok: 'true', at: at(10) }, NOW, 600).ok, false);
  assert.equal(evaluatePulse(200, { ok: true }, NOW, 600).ok, false); // нет at
  assert.equal(evaluatePulse(200, { ok: true, at: 'вчера' }, NOW, 600).ok, false);
  assert.equal(evaluatePulse(200, { ok: true, at: {} }, NOW, 600).ok, false);
});

test('пульс: HTTP не 200 — отказ', () => {
  assert.equal(evaluatePulse(500, { ok: true, at: at(10) }, NOW, 600).ok, false);
  assert.equal(evaluatePulse(404, { ok: true, at: at(10) }, NOW, 600).ok, false);
});

test('пульс: устаревший, из будущего, итог отказ — отказ', () => {
  assert.equal(evaluatePulse(200, { ok: true, at: at(601) }, NOW, 600).ok, false);
  assert.equal(evaluatePulse(200, { ok: true, at: at(-600) }, NOW, 600).ok, false);
  assert.equal(evaluatePulse(200, { ok: false, at: at(10) }, NOW, 600).ok, false);
});

test('пульс: свежий ok — успех, малое расхождение часов допустимо', () => {
  assert.equal(evaluatePulse(200, { ok: true, at: at(10) }, NOW, 600).ok, true);
  assert.equal(evaluatePulse(200, { ok: true, at: at(-30) }, NOW, 600).ok, true);
});

/** Подменённое соединение: ведёт себя по сценарию `script`. */
function fakeConnect(script) {
  return (_opts, onSecure) => {
    const sock = new EventEmitter();
    sock.destroyed = false;
    sock.destroy = () => {
      sock.destroyed = true;
    };
    sock.getPeerCertificate = () => ({ valid_to: new Date(Date.now() + 30 * 86_400_000).toString() });
    setTimeout(() => script(sock, onSecure), 5);
    return sock;
  };
}

test('сертификат: каждый исход завершает проверку сразу, без сторожевого таймера', async () => {
  const started = Date.now();
  const ok = await certDaysLeft('x', fakeConnect((_s, onSecure) => onSecure()));
  assert.ok(ok > 29 && ok <= 30);
  assert.equal(await certDaysLeft('x', fakeConnect((s) => s.emit('timeout'))), null);
  assert.equal(await certDaysLeft('x', fakeConnect((s) => s.emit('error', new Error('e')))), null);
  assert.equal(await certDaysLeft('x', fakeConnect((s) => s.emit('close'))), null);
  assert.equal(
    await certDaysLeft('x', () => {
      throw new Error('нет сети');
    }),
    null,
  );
  assert.ok(Date.now() - started < 2_000, 'исходы ждали сторожевого таймера');
});

test('сертификат: сокет молчит — сторожевой таймер завершает', { timeout: 20_000 }, async () => {
  const silent = fakeConnect(() => {});
  const started = Date.now();
  assert.equal(await certDaysLeft('x', silent, 200), null);
  assert.ok(Date.now() - started < 5_000);
});
