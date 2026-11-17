'use client';

/**
 * Smart Study page: flip cards, rate recall with confidence, track results.
 *
 * Talks to the Django API (apps/flashcards):
 *   GET  /study/next/?limit=10   weakest cards first
 *   POST /study/attempts/        { flashcard, is_correct, confidence }
 *   GET  /study/stats/           { total, correct, avg_confidence, accuracy }
 *
 * LOGIN (temporary): the accounts app has no login yet, so this page shows a small
 * sign-in form and sends the username/password as HTTP Basic auth (a Django REST
 * Framework default). Replace getToken/signIn below when real login exists.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import styles from './study.module.css';

/* ---------------- API ---------------- */

type Card = { id: number; question: string; answer: string; created_at: string };
type Stats = { total: number; correct: number; avg_confidence: number | null; accuracy: number | null };
type Answer = { correct: boolean; conf: number };

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/flashcards').replace(/\/$/, '');
const TOKEN_KEY = 'access_token';

class ApiError extends Error {
  status: number;
  constructor(status: number) {
    super(`HTTP ${status}`);
    this.status = status;
  }
}

function getToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? '';
  } catch {
    return '';
  }
}

function setToken(token: string) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the user will just be asked to sign in again */
  }
}

/** "Basic <base64(user:password)>", safe for non-ASCII characters. */
function basicToken(username: string, password: string): string {
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  let binary = '';
  bytes.forEach(b => (binary += String.fromCharCode(b)));
  return 'Basic ' + btoa(binary);
}

function authHeader(): Record<string, string> {
  const token = getToken();
  // A stored value with a space ("Basic abc...") is sent as is; a bare token gets "Bearer ".
  return token ? { Authorization: token.includes(' ') ? token : `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(API_BASE + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...authHeader() },
  });
  if (!res.ok) throw new ApiError(res.status);
  return (await res.json()) as T;
}

const getNextCards = (limit = 10) => request<Card[]>(`/study/next/?limit=${limit}`);
const getStats = () => request<Stats>('/study/stats/');
const submitAttempt = (flashcard: number, isCorrect: boolean, confidence: number) =>
  request<unknown>('/study/attempts/', {
    method: 'POST',
    body: JSON.stringify({ flashcard, is_correct: isCorrect, confidence }),
  });

/* ---------------- Page ---------------- */

export default function StudyPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [i, setI] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [correct, setCorrect] = useState<boolean | null>(null);
  const [conf, setConf] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [answers, setAnswers] = useState<Record<number, Answer>>({});
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [signedOut, setSignedOut] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Only the most recent load may update the screen. Without this, an older response
  // (React runs effects twice in dev) can arrive late and reset the card the user just flipped.
  const latestLoad = useRef(0);

  const refreshStats = useCallback(async () => {
    try {
      setStats(await getStats());
    } catch {
      setStats(null);
    }
  }, []);

  const load = useCallback(
    async (afterSignIn = false) => {
      const id = ++latestLoad.current;
      setLoading(true);
      setError('');
      try {
        const next = await getNextCards(10);
        if (id !== latestLoad.current) return;
        setSignedOut(false);
        setLoginError('');
        setCards(next);
        setI(0);
        setAnswers({});
        setFlipped(false);
        setCorrect(null);
        setConf(null);
        void refreshStats();
      } catch (e) {
        if (id !== latestLoad.current) return;
        const status = e instanceof ApiError ? e.status : 0;
        setCards([]);
        if (status === 401 || status === 403) {
          if (afterSignIn) {
            setToken('');
            setLoginError('Wrong username or password.');
          }
          setSignedOut(true);
        } else {
          setError('Could not reach the API. Is the Django server running?');
        }
      } finally {
        if (id === latestLoad.current) setLoading(false);
      }
    },
    [refreshStats]
  );

  useEffect(() => {
    void load();
  }, [load]);

  function signIn(e: React.FormEvent) {
    e.preventDefault();
    if (!username || !password) return;
    setToken(basicToken(username, password));
    setPassword('');
    void load(true);
  }

  function signOut() {
    latestLoad.current++; // ignore any request still in flight
    setToken('');
    setCards([]);
    setStats(null);
    setLoginError('');
    setSignedOut(true);
    setLoading(false);
  }

  const go = useCallback((d: number) => {
    setI(prev => (prev + d < 0 ? prev : prev + d));
    setFlipped(false);
    setCorrect(null);
    setConf(null);
    setError('');
  }, []);

  async function save() {
    if (correct === null || conf === null) return;
    const card = cards[i];
    setSaving(true);
    try {
      await submitAttempt(card.id, correct, conf);
      setAnswers(a => ({ ...a, [card.id]: { correct, conf } }));
      void refreshStats();
      go(1);
    } catch (e) {
      const status = e instanceof ApiError ? e.status : 0;
      setError(
        status === 401 || status === 403
          ? 'Your session is not valid, so that answer was not saved. Sign in again.'
          : 'Could not save that answer. Try again.'
      );
    } finally {
      setSaving(false);
    }
  }

  // Keyboard: space flips, arrows navigate, 1-5 sets confidence, y/n marks right or wrong.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement;
      if (/INPUT|TEXTAREA/.test(t.tagName) || cards.length === 0 || i >= cards.length) return;
      if ((e.key === ' ' || e.key === 'Enter') && t.tagName !== 'BUTTON') {
        e.preventDefault();
        setFlipped(f => !f);
      } else if (e.key === 'ArrowRight') go(1);
      else if (e.key === 'ArrowLeft') go(-1);
      else if (flipped && /^[1-5]$/.test(e.key)) setConf(Number(e.key));
      else if (flipped && e.key.toLowerCase() === 'y') setCorrect(true);
      else if (flipped && e.key.toLowerCase() === 'n') setCorrect(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [cards.length, i, flipped, go]);

  const statsText =
    stats && stats.total
      ? `${Math.round((stats.accuracy ?? 0) * 100)}% accuracy · avg confidence ${(stats.avg_confidence ?? 0).toFixed(1)} · ${stats.total} answered`
      : 'No attempts yet';

  const shell = (body: React.ReactNode) => (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1>Smart Study</h1>
        <div className={styles.headerRight}>
          {!signedOut && !loading && (
            <>
              <span aria-live="polite">{statsText}</span>
              <button className={styles.link} onClick={signOut}>
                Sign out
              </button>
            </>
          )}
        </div>
      </header>
      {body}
    </main>
  );

  if (loading) return shell(<p className={styles.msg}>Loading cards…</p>);

  if (signedOut)
    return shell(
      <form className={styles.form} onSubmit={signIn}>
        <h2>Sign in to study</h2>
        <label>
          Username
          <input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        <button className={styles.primary} type="submit" disabled={!username || !password}>
          Sign in
        </button>
        {loginError && (
          <p className={styles.err} role="alert">
            {loginError}
          </p>
        )}
      </form>
    );

  if (error && cards.length === 0)
    return shell(
      <>
        <p className={styles.msg} role="alert">
          {error}
        </p>
        <div className={styles.center}>
          <button className={styles.primary} onClick={() => void load()}>
            Try again
          </button>
        </div>
      </>
    );

  if (cards.length === 0)
    return shell(
      <>
        <p className={styles.msg}>No flashcards yet. Add some in the Django admin, or generate them.</p>
        <div className={styles.center}>
          <button className={styles.primary} onClick={() => void load()}>
            Reload
          </button>
        </div>
      </>
    );

  if (i >= cards.length) {
    const list = Object.values(answers);
    const right = list.filter(a => a.correct).length;
    const avg = list.length ? list.reduce((s, a) => s + a.conf, 0) / list.length : 0;
    const missed = cards.filter(c => answers[c.id] && !answers[c.id].correct);
    return shell(
      <section className={styles.summary}>
        <h2>Session complete</h2>
        <div className={styles.big}>{list.length ? `${right} / ${list.length}` : '—'}</div>
        <p>
          {list.length
            ? `Average confidence ${avg.toFixed(1)} of 5. Skipped: ${cards.length - list.length}.`
            : 'You skipped every card this round.'}
        </p>
        {missed.length > 0 && (
          <>
            <p>Review these:</p>
            <ul>
              {missed.map(c => (
                <li key={c.id}>{c.question}</li>
              ))}
            </ul>
          </>
        )}
        <button className={styles.primary} onClick={() => void load()}>
          Study weakest cards again
        </button>
      </section>
    );
  }

  const card = cards[i];
  return shell(
    <>
      <div className={styles.progress}>
        <div className={styles.bar} style={{ width: `${(i / cards.length) * 100}%` }} />
      </div>
      <p className={styles.count}>
        Card {i + 1} of {cards.length}
      </p>

      <div className={styles.scene}>
        <div
          className={`${styles.card} ${flipped ? styles.flipped : ''}`}
          role="button"
          tabIndex={0}
          aria-label="Flashcard. Press space to flip."
          onClick={() => setFlipped(f => !f)}
        >
          <div className={styles.face}>
            <span className={styles.tag}>Question</span>
            <div>{card.question}</div>
            <span className={styles.hint}>Try to recall the answer, then flip</span>
          </div>
          <div className={`${styles.face} ${styles.back}`}>
            <span className={styles.tag}>Answer</span>
            <div>{card.answer}</div>
          </div>
        </div>
      </div>

      {flipped && (
        <section className={styles.rate} aria-label="Rate your recall">
          <div className={styles.row}>
            <span className={styles.label}>Did you get it?</span>
            <button className={correct === true ? styles.on : ''} onClick={() => setCorrect(true)}>
              ✓ Got it
            </button>
            <button className={correct === false ? styles.on : ''} onClick={() => setCorrect(false)}>
              ✗ Missed
            </button>
          </div>
          <div className={styles.row}>
            <span className={styles.label}>Confidence</span>
            {[1, 2, 3, 4, 5].map(n => (
              <button
                key={n}
                className={conf === n ? styles.on : ''}
                aria-label={`Confidence ${n} of 5`}
                onClick={() => setConf(n)}
              >
                {n}
              </button>
            ))}
            <small className={styles.hint}>1 = guessing, 5 = certain</small>
          </div>
          <button
            className={styles.primary}
            disabled={correct === null || conf === null || saving}
            onClick={() => void save()}
          >
            Save &amp; next
          </button>
          {error && (
            <p className={styles.err} role="alert">
              {error}
            </p>
          )}
        </section>
      )}

      <nav className={styles.nav}>
        <button onClick={() => go(-1)} disabled={i === 0}>
          ← Previous
        </button>
        <button className={styles.primary} onClick={() => setFlipped(f => !f)}>
          {flipped ? 'Hide answer' : 'Reveal answer'}
        </button>
        <button onClick={() => go(1)}>Skip →</button>
      </nav>
    </>
  );
}