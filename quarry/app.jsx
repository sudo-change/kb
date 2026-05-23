/* global React, ReactDOM, TweaksPanel, TweakSection, TweakRadio, TweakToggle, TweakColor, TweakSelect, useTweaks */
const { useState, useEffect, useRef, useMemo, useCallback } = React;

// ============ Sidebar ============
function InlineEditable({ value, onSave, onCancel, className = "nav-item-input" }) {
  const [v, setV] = useState(value);
  const ref = useRef();
  useEffect(() => { ref.current && ref.current.focus(); ref.current && ref.current.select(); }, []);
  return (
    <input
      ref={ref}
      className={className}
      value={v}
      onChange={e => setV(e.target.value)}
      onBlur={() => onSave(v.trim() || value)}
      onKeyDown={e => {
        if (e.key === "Enter") { onSave(v.trim() || value); }
        if (e.key === "Escape") { onCancel(); }
      }}
    />
  );
}

// RSSHub route definitions
const RSSHUB_ROUTES = {
  social: [
    { id: "twitter-user",  label: "X User",       glyph: "X", pattern: "/twitter/user/:username", placeholder: "username (no @)", ex: "samczsun" },
    { id: "twitter-list",  label: "X List",        glyph: "X", pattern: "/twitter/list/:id",      placeholder: "list ID from URL", ex: "12345" },
    { id: "reddit-sub",    label: "Subreddit",     glyph: "r", pattern: "/reddit/subreddit/:sub",  placeholder: "subreddit name",   ex: "netsec" },
    { id: "reddit-user",   label: "Reddit User",   glyph: "r", pattern: "/reddit/user/:user",     placeholder: "username",         ex: "tptacek" },
    { id: "telegram",      label: "Telegram",      glyph: "T", pattern: "/telegram/channel/:name", placeholder: "channel @handle",  ex: "tldrsec" },
    { id: "threads",       label: "Threads",       glyph: "𝕿", pattern: "/threads/:user",          placeholder: "username (no @)",  ex: "swyx" },
  ],
  code: [
    { id: "gh-releases",   label: "GH Releases",  glyph: "G", pattern: "/github/repos/:user/:repo/releases", placeholder: "user/repo", ex: "anthropics/anthropic-sdk-python" },
    { id: "gh-commits",    label: "GH Commits",   glyph: "G", pattern: "/github/repos/:user/:repo/commits",  placeholder: "user/repo", ex: "trailofbits/semgrep-rules" },
    { id: "gh-stars",      label: "GH Stars",     glyph: "G", pattern: "/github/user/starred/:user",        placeholder: "username",  ex: "samczsun" },
    { id: "npm",           label: "npm pkg",      glyph: "n", pattern: "/npm/package/:name",                placeholder: "package",   ex: "@anthropic-ai/sdk" },
    { id: "pypi",          label: "PyPI pkg",     glyph: "P", pattern: "/pypi/package/:name",               placeholder: "package",   ex: "anthropic" },
    { id: "hackernews-user", label: "HN User",    glyph: "Y", pattern: "/hackernews/user/:id",             placeholder: "username",   ex: "pg" },
  ],
  news: [
    { id: "hn-top",        label: "HN Top",       glyph: "Y", pattern: "/hackernews/best",           placeholder: "(no input)",      ex: "" },
    { id: "hn-show",       label: "HN Show",      glyph: "Y", pattern: "/hackernews/show",           placeholder: "(no input)",      ex: "" },
    { id: "hn-ask",        label: "HN Ask",       glyph: "Y", pattern: "/hackernews/ask",            placeholder: "(no input)",      ex: "" },
    { id: "lobsters",      label: "Lobste.rs",    glyph: "L", pattern: "/lobsters/top",              placeholder: "(no input)",      ex: "" },
    { id: "ph-daily",      label: "Product Hunt", glyph: "P", pattern: "/producthunt/today",         placeholder: "(no input)",      ex: "" },
    { id: "arxiv",         label: "arXiv",        glyph: "A", pattern: "/arxiv/search/:query",       placeholder: "query",           ex: "LLM security" },
  ],
  video: [
    { id: "yt-channel",    label: "YT Channel",   glyph: "▶", pattern: "/youtube/channel/:id",      placeholder: "channel ID",       ex: "UC-channelid" },
    { id: "yt-user",       label: "YT Handle",    glyph: "▶", pattern: "/youtube/user/:handle",     placeholder: "@handle",          ex: "@LiveOverflow" },
    { id: "yt-playlist",   label: "YT Playlist",  glyph: "▶", pattern: "/youtube/playlist/:id",     placeholder: "playlist ID",      ex: "PLjV3HijScGMynGvjJrvNNd5Q9pPy255dL" },
    { id: "twitch-live",   label: "Twitch Live",  glyph: "T", pattern: "/twitch/streams/:name",     placeholder: "channel name",     ex: "nahamsec" },
    { id: "twitch-videos", label: "Twitch VODs",  glyph: "T", pattern: "/twitch/videos/:name",      placeholder: "channel name",     ex: "ippsec" },
  ],
  rss: [
    { id: "substack",      label: "Substack",     glyph: "S", pattern: "https://:name.substack.com/feed", placeholder: "publication slug", ex: "pragmaticengineer" },
    { id: "medium-tag",    label: "Medium tag",   glyph: "M", pattern: "/medium/tag/:tag",          placeholder: "tag slug",         ex: "bug-bounty" },
    { id: "medium-pub",    label: "Medium pub",   glyph: "M", pattern: "/medium/publication/:name", placeholder: "pub name",         ex: "googleblog" },
    { id: "devto-tag",     label: "Dev.to tag",   glyph: "D", pattern: "/dev.to/tag/:tag",          placeholder: "tag",              ex: "cybersecurity" },
    { id: "raw-rss",       label: "Raw RSS URL",  glyph: "R", pattern: ":url",                      placeholder: "full RSS/Atom URL", ex: "https://portswigger.net/research/rss" },
  ],
};
const RSSHUB_INSTANCE = "https://rsshub.app";
const ROUTE_CATS = ["social", "code", "news", "video", "rss"];

function AddSourceForm({ onAdd, onCancel }) {
  const [cat, setCat] = useState("news");
  const [route, setRoute] = useState(null);
  const [value, setValue] = useState("");

  const routes = RSSHUB_ROUTES[cat];
  const sel = route ? routes.find(r => r.id === route) : null;

  const buildUrl = () => {
    if (!sel) return "";
    if (sel.pattern.startsWith("https://")) {
      return sel.pattern.replace(":name", value || sel.ex);
    }
    if (sel.pattern === ":url") return value || sel.ex;
    const filled = sel.pattern.replace(/:\w+/g, value || sel.ex || "…");
    return RSSHUB_INSTANCE + filled;
  };

  const submit = () => {
    if (!sel) return;
    const url = buildUrl();
    const name = value
      ? `${sel.label}: ${value}`
      : sel.label;
    const glyph = sel.glyph;
    onAdd({ id: "s" + Date.now(), name, glyph, count: 0, url, rsshub: true, routeId: sel.id });
  };

  return (
    <div className="inline-form">
      <div className="inline-form-label">Add source via RSSHub</div>
      <div className="rsshub-browser">
        <div className="rsshub-tabs">
          {ROUTE_CATS.map(c => (
            <button
              key={c}
              className={cat === c ? "active" : ""}
              onClick={() => { setCat(c); setRoute(null); setValue(""); }}
            >{c}</button>
          ))}
        </div>
        <div className="rsshub-routes">
          {routes.map(r => (
            <button
              key={r.id}
              className={`route-btn ${route === r.id ? "active" : ""}`}
              onClick={() => { setRoute(r.id); setValue(""); }}
            >
              <span style={{
                width: 14, height: 14, display: "grid", placeItems: "center",
                fontSize: 9, fontWeight: 700, borderRadius: 2,
                background: route === r.id ? "rgba(255,255,255,0.2)" : "var(--rule)",
                color: route === r.id ? "#fff" : "var(--ink-2)",
                flexShrink: 0
              }}>{r.glyph}</span>
              {r.label}
            </button>
          ))}
        </div>
        {sel && (
          <div className="route-input-row">
            <div className="route-input-label">{sel.placeholder !== "(no input)" ? sel.placeholder : "no parameter needed"}</div>
            {sel.placeholder !== "(no input)" && (
              <input
                autoFocus
                value={value}
                onChange={e => setValue(e.target.value)}
                placeholder={`e.g. ${sel.ex}`}
                onKeyDown={e => { if (e.key === "Enter") submit(); if (e.key === "Escape") onCancel(); }}
              />
            )}
            <div className="route-preview">{buildUrl()}</div>
          </div>
        )}
      </div>
      <div className="form-actions">
        <button className="btn-mini" onClick={onCancel}>Cancel</button>
        <button className="btn-mini primary" onClick={submit} disabled={!sel}>Add source</button>
      </div>
    </div>
  );
}

function AddQuestForm({ onAdd, onCancel }) {
  const [name, setName] = useState("");
  const COLORS = ["#c97f3f", "#8a6dc9", "#4f8a5e", "#b85a5a", "#5a7fb8", "#c9a13f", "#3f9c9c"];
  const [color, setColor] = useState(COLORS[0]);
  const submit = () => {
    if (!name.trim()) return;
    onAdd({ id: "q" + Date.now(), name: name.trim(), color, count: 0 });
  };
  return (
    <div className="inline-form">
      <div className="inline-form-label">New quest</div>
      <input
        autoFocus
        value={name}
        onChange={e => setName(e.target.value)}
        placeholder="e.g. Macro / rates / liquidity"
        onKeyDown={e => { if (e.key === "Enter") submit(); if (e.key === "Escape") onCancel(); }}
      />
      <div className="color-row">
        {COLORS.map(c => (
          <button
            key={c}
            className={`swatch ${color === c ? "active" : ""}`}
            style={{ background: c }}
            onClick={() => setColor(c)}
          />
        ))}
      </div>
      <div className="form-actions">
        <button className="btn-mini" onClick={onCancel}>Cancel</button>
        <button className="btn-mini primary" onClick={submit} disabled={!name.trim()}>Add quest</button>
      </div>
    </div>
  );
}

function Sidebar({ view, setView, activeQuest, setActiveQuest, activeSource, setActiveSource, activeTags, setActiveTags, stats, quests, setQuests, sources, setSources }) {
  const [adding, setAdding] = useState(null); // 'source' | 'quest' | null
  const [editing, setEditing] = useState(null); // { kind, id }

  const toggleTag = (t) => {
    setActiveTags(activeTags.includes(t) ? activeTags.filter(x => x !== t) : [...activeTags, t]);
  };
  const cells = Array.from({ length: 21 }, (_, i) => (i < stats.streakDays ? "on" : ""));

  const renameQuest = (id, name) => {
    setQuests(quests.map(q => q.id === id ? { ...q, name } : q));
    setEditing(null);
  };
  const renameSource = (id, name) => {
    setSources(sources.map(s => s.id === id ? { ...s, name } : s));
    setEditing(null);
  };
  const removeQuest = (id) => {
    setQuests(quests.filter(q => q.id !== id));
    if (activeQuest === id) setActiveQuest(null);
  };
  const removeSource = (id) => {
    if (window.KF_API) window.KF_API.deleteSource(id).catch(console.error);
    setSources(sources.filter(s => s.id !== id));
    if (activeSource === id) setActiveSource(null);
  };

  return (
    <aside className="sidebar">
      <div>
        <div className="brand">
          <div className="brand-mark">KB</div>
          <div>
            <div className="brand-name">Quarry</div>
            <div className="brand-tag">daily radar · v0.3</div>
          </div>
        </div>
      </div>

      <div className="nav-section">
        <div className="nav-label">Garden</div>
        <button className={`nav-item ${view === "radar" ? "active" : ""}`} onClick={() => setView("radar")}>
          <span className="glyph">◐</span> Daily Radar
          <span className="nav-count">{stats.newToday}</span>
        </button>
        <button className={`nav-item ${view === "library" ? "active" : ""}`} onClick={() => setView("library")}>
          <span className="glyph">▤</span> Memos
          <span className="nav-count">{stats.memosTotal}</span>
        </button>
        <button className={`nav-item ${view === "recall" ? "active" : ""}`} onClick={() => setView("recall")}>
          <span className="glyph">↻</span> Recall
          <span className="nav-count">12</span>
        </button>
      </div>

      <div className="nav-section">
        <div className="nav-label">
          <span>Quests <span className="count">{quests.length}</span></span>
          <button className="add-btn" onClick={() => setAdding(adding === "quest" ? null : "quest")}>+ new</button>
        </div>
        <button
          className={`nav-item ${activeQuest === null ? "active" : ""}`}
          onClick={() => setActiveQuest(null)}
        >
          <span className="dot" style={{ background: "var(--muted)" }}></span>
          All threads
          <span className="nav-count">{quests.reduce((s, q) => s + q.count, 0)}</span>
        </button>
        {quests.map(q => (
          <div key={q.id} className="nav-item-wrap">
            {editing && editing.kind === "quest" && editing.id === q.id ? (
              <InlineEditable
                value={q.name}
                onSave={(name) => renameQuest(q.id, name)}
                onCancel={() => setEditing(null)}
              />
            ) : (
              <>
                <button
                  className={`nav-item ${activeQuest === q.id ? "active" : ""}`}
                  onClick={() => setActiveQuest(activeQuest === q.id ? null : q.id)}
                  onDoubleClick={() => setEditing({ kind: "quest", id: q.id })}
                >
                  <span className="dot" style={{ background: q.color }}></span>
                  {q.name}
                  <span className="nav-count">{q.count}</span>
                </button>
                <button
                  className="nav-item-edit"
                  title="Rename"
                  onClick={(e) => { e.stopPropagation(); setEditing({ kind: "quest", id: q.id }); }}
                >✎</button>
              </>
            )}
          </div>
        ))}
        {adding === "quest" && (
          <AddQuestForm
            onAdd={(q) => { setQuests([...quests, q]); setAdding(null); }}
            onCancel={() => setAdding(null)}
          />
        )}
      </div>

      <div className="nav-section">
        <div className="nav-label">
          <span>Sources <span className="count">{sources.length}</span></span>
          <button className="add-btn" onClick={() => setAdding(adding === "source" ? null : "source")}>+ add</button>
        </div>
        {sources.map(s => (
          <div key={s.id} className="nav-item-wrap">
            {editing && editing.kind === "source" && editing.id === s.id ? (
              <InlineEditable
                value={s.name}
                onSave={(name) => renameSource(s.id, name)}
                onCancel={() => setEditing(null)}
              />
            ) : (
              <>
                <button
                  className={`nav-item ${activeSource === s.id ? "active" : ""}`}
                  onClick={() => setActiveSource(activeSource === s.id ? null : s.id)}
                  onDoubleClick={() => setEditing({ kind: "source", id: s.id })}
                >
                  <span className={`source-badge ${s.id}`} style={{ width: 16, justifyContent: "center", background: s.customColor || undefined }}>{s.glyph}</span>
                  {s.name}
                  <span className="nav-count">{s.count}</span>
                </button>
                <button
                  className="nav-item-edit"
                  title="Rename"
                  onClick={(e) => { e.stopPropagation(); setEditing({ kind: "source", id: s.id }); }}
                >✎</button>
              </>
            )}
          </div>
        ))}
        {adding === "source" && (
          <AddSourceForm
            onAdd={(s) => {
              if (window.KF_API) {
                window.KF_API.addSource({
                  id: s.id, name: s.name,
                  type: s.rsshub ? "rsshub" : "rss",
                  config: { url: s.url }, glyph: s.glyph,
                  category: null, enabled: true,
                }).catch(console.error);
              }
              setSources([...sources, s]);
              setAdding(null);
            }}
            onCancel={() => setAdding(null)}
          />
        )}
      </div>

      <div className="nav-section">
        <div className="nav-label">Tags</div>
        <div className="tag-cloud">
          {window.TAGS.map(t => (
            <button
              key={t}
              className={`tag-chip ${activeTags.includes(t) ? "active" : ""}`}
              onClick={() => toggleTag(t)}
            >#{t}</button>
          ))}
        </div>
      </div>

      <div className="streak-box">
        <div className="streak-num">{stats.streakDays}</div>
        <div className="streak-label">day streak · 1hr drill</div>
        <div className="streak-grid">
          {cells.map((c, i) => <div key={i} className={`streak-cell ${c}`}></div>)}
        </div>
      </div>
    </aside>
  );
}

// ============ Topbar ============
function Topbar({ stats, dark, setDark, density, setDensity, paneOpen, setPaneOpen, qualityFilter, setQualityFilter, search, setSearch, onShowHelp }) {
  const today = new Date("2026-05-12T08:00:00");
  const dateStr = today.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  const searchRef = useRef(null);

  // Expose focus fn via ref for keyboard /
  useEffect(() => {
    window.__focusSearch = () => searchRef.current && searchRef.current.focus();
    return () => { delete window.__focusSearch; };
  }, []);

  return (
    <div className="topbar">
      <div className="topbar-date">{dateStr}</div>
      <div className="topbar-counter">
        <span className="num">{stats.newToday}</span> new · <span className="num">{stats.streakDays}</span> day streak
      </div>
      <div className="spacer"></div>
      <div className="topbar-search">
        <input
          ref={searchRef}
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search radar &amp; memos… (/)"
          onKeyDown={e => e.key === "Escape" && e.target.blur()}
        />
      </div>
      <button
        className={`icon-btn ${qualityFilter ? "active" : ""}`}
        onClick={() => setQualityFilter(!qualityFilter)}
        title={`Quality filter ${qualityFilter ? "on" : "off"} — hides listicles & emoji-led titles`}
      >⚡</button>
      <button
        className="icon-btn"
        onClick={() => setDensity(density === "comfortable" ? "compact" : density === "compact" ? "spacious" : "comfortable")}
        title={`Density: ${density}`}
      >≡</button>
      <button
        className="icon-btn"
        onClick={() => setDark(!dark)}
        title="Toggle theme"
      >{dark ? "☼" : "☾"}</button>
      <button
        className={`icon-btn ${paneOpen ? "active" : ""}`}
        onClick={() => setPaneOpen(!paneOpen)}
        title="Reader / memo pane"
      >▥</button>
      <button
        className="icon-btn"
        onClick={onShowHelp}
        title="Keyboard shortcuts (?)"
      >?</button>
    </div>
  );
}

// ============ Utilities ============
// Parse time strings like "2h", "1d", "3d" into hours
function parseHours(t) {
  if (!t) return 9999;
  const m = t.match(/(\d+)(h|d|w)/);
  if (!m) return 9999;
  const [, n, u] = m;
  return u === "h" ? +n : u === "d" ? +n * 24 : +n * 168;
}

// Quality filter: detect listicles and emoji-led titles
const LISTICLE_RE = /^(\d+\s+(ways|tips|tricks|things|reasons|tools|best|top)|top\s+\d+|best\s+\d+)/i;
const EMOJI_RE = /^\p{Emoji}/u;
function isLowQuality(title) {
  return LISTICLE_RE.test(title) || EMOJI_RE.test(title);
}

// ============ Keyboard Help Modal ============
function KeyboardHelp({ onClose }) {
  return (
    <div className="kb-modal-overlay" onClick={onClose}>
      <div className="kb-modal" onClick={e => e.stopPropagation()}>
        <div className="kb-modal-title">Keyboard shortcuts</div>
        <div className="kb-section">
          <div className="kb-section-label">Navigation</div>
          <div className="kb-row"><span>Next / previous item</span><div className="kb-keys"><span className="kb-key">j</span><span className="kb-key">k</span></div></div>
          <div className="kb-row"><span>Open in reader pane</span><div className="kb-keys"><span className="kb-key">o</span><span className="kb-key">↵</span></div></div>
          <div className="kb-row"><span>Focus search</span><div className="kb-keys"><span className="kb-key">/</span></div></div>
          <div className="kb-row"><span>Close pane / modal</span><div className="kb-keys"><span className="kb-key">Esc</span></div></div>
        </div>
        <div className="kb-section">
          <div className="kb-section-label">Reactions</div>
          <div className="kb-row"><span>Love (save to garden)</span><div className="kb-keys"><span className="kb-key">a</span></div></div>
          <div className="kb-row"><span>Like (boost source)</span><div className="kb-keys"><span className="kb-key">l</span></div></div>
          <div className="kb-row"><span>Dislike (drop source)</span><div className="kb-keys"><span className="kb-key">d</span></div></div>
          <div className="kb-row"><span>Not interested (hide)</span><div className="kb-keys"><span className="kb-key">x</span></div></div>
          <div className="kb-row"><span>Save / unsave</span><div className="kb-keys"><span className="kb-key">s</span></div></div>
          <div className="kb-row"><span>Undo reaction</span><div className="kb-keys"><span className="kb-key">u</span></div></div>
        </div>
        <div className="kb-section">
          <div className="kb-section-label">General</div>
          <div className="kb-row"><span>Show this help</span><div className="kb-keys"><span className="kb-key">?</span></div></div>
        </div>
        <div style={{ marginTop: 20, textAlign: "right" }}>
          <button className="btn ghost" onClick={onClose} style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>Close Esc</button>
        </div>
      </div>
    </div>
  );
}

// ============ Item card ============
function quarryScore(item) { return item.score; }

function Item({ item, selected, focused, onSelect, reaction, setReaction, notInterested, onNotInterested, seen, source }) {
  const r = reaction[item.id];
  const isLoved  = r === "love";
  const isLiked  = r === "like";
  const isDis    = r === "dislike";
  const isNI     = notInterested.has(item.id);
  const isSeen   = seen.has(item.id);
  const quest    = window.QUESTS.find(q => q.id === item.quest);
  const isDedup  = item.sources && item.sources.length > 1;
  const score    = quarryScore(item);

  const react = (val) => {
    setReaction(prev => ({ ...prev, [item.id]: prev[item.id] === val ? null : val }));
  };

  if (isNI) return null;

  return (
    <article
      className={`item ${selected ? "selected" : ""} ${focused ? "kb-focus" : ""} ${isSeen && !selected ? "seen-item" : ""}`}
      onClick={() => onSelect(item.id)}
      data-item-id={item.id}
    >
      <div className="item-score score-wrap">
        <div className={`score-num ${score < 7 ? "lo" : ""}`}>{score.toFixed(1)}</div>
        <div className={`score-bar ${score < 7 ? "lo" : ""}`}>
          <span style={{ width: `${score * 10}%` }}></span>
        </div>
        <div className="score-tip">
          <div className="tip-row"><span>Platform pts</span><span className="tip-accent">{item.points || 0}</span></div>
          <div className="tip-row"><span>Source rel.</span><span className="tip-accent">{item.srcReliability || 82}%</span></div>
          <div className="tip-row"><span>Loves</span><span className="tip-accent">{isLoved ? 1 : 0}</span></div>
          <div className="tip-row"><span>Age</span><span className="tip-accent">{item.time}</span></div>
          <div style={{ borderTop: "1px solid rgba(255,255,255,0.15)", paddingTop: 4, marginTop: 2 }} className="tip-row">
            <span>Quarry score</span><span className="tip-accent">{score.toFixed(1)}</span>
          </div>
          <div style={{ opacity: 0.4, marginTop: 4, fontSize: 8 }}>pts×rel + love×3 / age^0.7</div>
        </div>
      </div>

      <div className="item-body">
        <div className="item-meta">
          {isDedup ? (
            <span className="item-dedup-badges">
              {item.sources.map(s => (
                <span key={s.id} className={`source-badge ${s.id}`}>{s.glyph} {s.name}</span>
              ))}
              <span className="dedup-label">deduped ×{item.sources.length}</span>
            </span>
          ) : (
            <span className={`source-badge ${item.source}`}>{source?.glyph} {source?.name}</span>
          )}
          {quest && <><span style={{ color: "var(--muted-2)" }}>·</span><span style={{ color: quest.color, fontWeight: 600 }}>● {quest.name}</span></>}
          <span style={{ color: "var(--muted-2)" }}>·</span>
          <span>{item.time}</span>
          {item.points > 0 && <><span style={{ color: "var(--muted-2)" }}>·</span><span>{item.points}↑</span></>}
          {item.comments > 0 && <><span style={{ color: "var(--muted-2)" }}>·</span><span>{item.comments}💬</span></>}
          {item.new && <><span style={{ color: "var(--muted-2)" }}>·</span><span className="new-dot"></span><span style={{ color: "var(--accent-ink)" }}>NEW</span></>}
        </div>
        <h2 className="item-title">{item.title}</h2>
        <p className="item-summary">{item.summary}</p>
        {item.tags.length > 0 && (
          <div className="item-tags">
            {item.tags.map(t => <span key={t} className="tag-chip">#{t}</span>)}
          </div>
        )}
      </div>

      <div className="reaction-group" onClick={e => e.stopPropagation()}>
        <button
          className={`act-btn love ${isLoved ? "on" : ""}`}
          onClick={() => react("love")}
          title="Love — saves to garden · key: a"
        >♥</button>
        <button
          className={`act-btn up ${isLiked ? "on" : ""}`}
          onClick={() => react("like")}
          title="Like — boosts source · key: l"
        >△</button>
        <button
          className={`act-btn dn ${isDis ? "on" : ""}`}
          onClick={() => react("dislike")}
          title="Dislike — drops source · key: d"
        >▽</button>
        <button
          className="not-interested-btn"
          onClick={() => onNotInterested(item.id)}
          title="Not interested — hide · key: x"
        >✕</button>
      </div>
    </article>
  );
}

// ============ Feed (Daily Radar) ============
const TIMEFRAMES = [
  { id: "all",   label: "All" },
  { id: "fresh", label: "Fresh",  maxH: 12 },
  { id: "today", label: "Today",  maxH: 24 },
  { id: "3d",    label: "3 days", maxH: 72 },
  { id: "1w",    label: "Week",   maxH: 168 },
];

function Feed({ items, sources, selected, focusedIdx, onSelect, reaction, setReaction, notInterested, onNotInterested, seen, showSeen, setShowSeen, loaded, loading, onLoadMore, stats, timeframe, setTimeframe, qualityFilter }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80 && !loading && loaded < items.length) {
        onLoadMore();
      }
    };
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, [items.length, loaded, loading, onLoadMore]);

  const tf = TIMEFRAMES.find(t => t.id === timeframe);
  const timeFiltered = tf?.maxH ? items.filter(it => parseHours(it.time) <= tf.maxH) : items;
  const qualFiltered = qualityFilter ? timeFiltered.filter(it => !isLowQuality(it.title)) : timeFiltered;
  const visible = qualFiltered.slice(0, loaded);
  const sourceMap = Object.fromEntries((sources || []).map(s => [s.id, s]));
  const seenCount = [...seen].filter(id => qualFiltered.find(it => it.id === id)).length;
  const lovedCount = Object.values(reaction).filter(v => v === "love").length;

  return (
    <>
      <header className="radar-header">
        <h1 className="radar-title">Daily Radar</h1>
        <div className="radar-sub">
          <span><strong>{stats.newToday}</strong> new since 06:00</span>
          <span><strong>{qualFiltered.length}</strong> on radar</span>
          {notInterested.size > 0 && <span><strong>{notInterested.size}</strong> hidden</span>}
          {lovedCount > 0 && <span><strong>{lovedCount}</strong> loved</span>}
          <span title="pts×source_reliability + loves×3 / age^0.7">vote-weighted · hover score</span>
        </div>
      </header>

      <div className="feed" ref={scrollRef}>
        <div className="recall-banner">
          <div className="recall-icon">↻</div>
          <div className="recall-text">
            <div className="recall-title">Weekly recall — 5 memos surfaced from last month</div>
            <div className="recall-sub">"Bug class watchlist — May" and 4 others. Open recall to review or dismiss.</div>
          </div>
          <button className="btn ghost">Review</button>
        </div>

        <div className="feed-info-row">
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div className="timeframe-tabs">
              {TIMEFRAMES.map(t => (
                <button key={t.id} className={`timeframe-tab ${timeframe === t.id ? "active" : ""}`} onClick={() => setTimeframe(t.id)}>{t.label}</button>
              ))}
            </div>
            {seenCount > 0 && (
              <button className="seen-toggle" onClick={() => setShowSeen(s => !s)}>
                {showSeen ? `hide ${seenCount} seen` : `${seenCount} seen`}
              </button>
            )}
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--muted)" }}>
            {qualFiltered.length} items{qualityFilter ? " · quality on" : ""}
          </span>
        </div>

        {visible.map((it, idx) => (
          <Item
            key={it.id}
            item={it}
            source={sourceMap[it.source] || { id: it.source, name: it.source, glyph: "?" }}
            selected={selected === it.id}
            focused={focusedIdx === idx}
            onSelect={onSelect}
            reaction={reaction}
            setReaction={setReaction}
            notInterested={notInterested}
            onNotInterested={onNotInterested}
            seen={seen}
          />
        ))}

        {loaded < qualFiltered.length && (
          <div className="loader">
            {loading ? "scanning sources" : "scroll to load more"}
            <div className="loader-bar"><span></span></div>
          </div>
        )}
        {loaded >= qualFiltered.length && visible.length > 0 && (
          <div className="loader">— end of radar —</div>
        )}
        {visible.length === 0 && (
          <div className="loader">no items match — try a wider timeframe</div>
        )}
      </div>
    </>
  );
}

// ============ Right pane: Reader + Memo ============
function RightPane({ item, source, paneTab, setPaneTab, memo, setMemo, onClose, onSaveMemo, toast }) {
  const hasItem = !!item;
  return (
    <aside className="pane">
      <div className="pane-tabs">
        <button className={`pane-tab ${paneTab === "split" ? "active" : ""}`} onClick={() => setPaneTab("split")}>
          Read · Write
        </button>
        <button className={`pane-tab ${paneTab === "read" ? "active" : ""}`} onClick={() => setPaneTab("read")}>
          Reader
        </button>
        <button className={`pane-tab ${paneTab === "memo" ? "active" : ""}`} onClick={() => setPaneTab("memo")}>
          Today's Memo
        </button>
        <button className="pane-close" onClick={onClose} title="Close pane">×</button>
      </div>

      <div className={`pane-body ${paneTab === "split" && hasItem ? "" : "single"}`}>
        {(paneTab === "split" || paneTab === "read") && hasItem && (
          <div className="reader">
            <div className="reader-meta">
              <span className={`source-badge ${item.source}`}>{source.glyph} {source.name}</span>
              <span>{item.time} ago</span>
              <span>· score {item.score.toFixed(1)}</span>
            </div>
            <h2 className="reader-title">{item.title}</h2>
            <div className="reader-body">
              <p>{item.body || item.summary}</p>
              {item.body && <p style={{ color: "var(--muted)", fontStyle: "italic", fontSize: 13 }}>— preview continues in source —</p>}
            </div>
            <a className="reader-link" href="#" onClick={e => e.preventDefault()}>↗ {item.url}</a>
          </div>
        )}
        {(paneTab === "split" || paneTab === "read") && !hasItem && (
          <div className="reader">
            <div className="reader-meta">no item selected</div>
            <div className="reader-body" style={{ color: "var(--muted)" }}>
              <p>Click any item in the radar to read it here while you write.</p>
            </div>
          </div>
        )}

        {(paneTab === "split" || paneTab === "memo") && (
          <div className={`memo-editor ${paneTab === "memo" ? "full" : ""}`}>
            <div className="memo-header">
              <span className="memo-label">{paneTab === "memo" ? "Today's daily memo" : "Capture · live"}</span>
              <span className="memo-label" style={{ color: "var(--accent-ink)" }}>● recording</span>
            </div>
            <input
              className="memo-title"
              placeholder="Memo title…"
              value={memo.title}
              onChange={e => setMemo({ ...memo, title: e.target.value })}
            />
            <textarea
              className="memo-body"
              placeholder="What did you notice? What pattern is forming across today's radar?"
              value={memo.body}
              onChange={e => setMemo({ ...memo, body: e.target.value })}
            />
            <div className="memo-tags">
              {memo.tags.map(t => (
                <span key={t} className="tag-chip active" onClick={() => setMemo({ ...memo, tags: memo.tags.filter(x => x !== t) })}>#{t} ×</span>
              ))}
              <button className="memo-tag-add">+ tag</button>
            </div>
            <div className="memo-suggested">
              suggested:
              {["ssrf", "claude", "agents", "discipline"].filter(s => !memo.tags.includes(s)).slice(0, 3).map(s => (
                <button key={s} className="tag-chip" onClick={() => setMemo({ ...memo, tags: [...memo.tags, s] })}>+ #{s}</button>
              ))}
            </div>
            <div className="memo-save-row">
              <span className="memo-label">{memo.body.length} chars · autosaved 12s ago</span>
              <div style={{ display: "flex", gap: 6 }}>
                <button className="btn ghost">Discard</button>
                <button className="btn" onClick={onSaveMemo}>Save to garden ↗</button>
              </div>
            </div>
          </div>
        )}
      </div>

      {toast && <div className="train-toast">{toast}</div>}
    </aside>
  );
}

// ============ Memos library ============
function Library({ memos, onOpen, stats }) {
  return (
    <>
      <header className="radar-header">
        <h1 className="radar-title">Memos · garden</h1>
        <div className="radar-sub">
          <span><strong>{memos.length}</strong> memos</span>
          <span><strong>{stats.itemsReviewed}</strong> items reviewed all-time</span>
          <span>last entry: 2h ago</span>
        </div>
      </header>
      <div className="library">
        <div className="recall-banner">
          <div className="recall-icon">⚘</div>
          <div className="recall-text">
            <div className="recall-title">"Bug class watchlist — May" — revisit?</div>
            <div className="recall-sub">Saved 8 days ago · linked to 2 items still on your radar this week.</div>
          </div>
          <button className="btn ghost">Open</button>
        </div>
        {memos.map(m => (
          <article key={m.id} className="memo-card" onClick={() => onOpen(m)}>
            <div className="memo-card-meta">
              <span>{m.date}</span>
              {m.linkedItems.length > 0 && <span>· {m.linkedItems.length} linked items</span>}
            </div>
            <h3 className="memo-card-title">{m.title}</h3>
            <p className="memo-card-body">{m.body}</p>
            <div className="memo-card-footer">
              {m.tags.map(t => <span key={t} className="tag-chip">#{t}</span>)}
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

// ============ App ============
const TWEAK_DEFAULS = /*EDITMODE-BEGIN*/{
  "accent": "#c97f3f",
  "density": "comfortable",
  "showReasons": true,
  "showRecallBanner": true,
  "fontPairing": "serif-sans",
  "layoutVariant": "three-column"
}/*EDITMODE-END*/;

function App() {
  const [view, setView] = useState("radar");
  const [activeQuest, setActiveQuest] = useState(null);
  const [activeSource, setActiveSource] = useState(null);
  const [activeTags, setActiveTags] = useState([]);
  const [selected, setSelected] = useState(null);
  const [focusedIdx, setFocusedIdx] = useState(0);
  // Reactions: { itemId: 'love' | 'like' | 'dislike' | null }
  const [reaction, setReaction] = useState({});
  const [notInterested, setNotInterested] = useState(new Set());
  const [seen, setSeen] = useState(new Set());
  const [showSeen, setShowSeen] = useState(false);
  const [paneOpen, setPaneOpen] = useState(true);
  const [paneTab, setPaneTab] = useState("split");
  const [memo, setMemo] = useState({
    title: "Daily Radar — Tue, May 12",
    body: "Pattern forming: OAuth state desync is having a moment (Reddit $50k + adjacent semgrep ruleset). 2-week window before it's saturated. Also — Haiku 4.5 pricing collapses the floor; reprice the side project this weekend.",
    tags: ["daily-radar", "ssrf"],
  });
  const [memos, setMemos] = useState(window.MEMOS);
  const [quests, setQuests] = useState(window.QUESTS);
  const [sources, setSources] = useState([]);
  const [timeframe, setTimeframe] = useState("all");
  const [qualityFilter, setQualityFilter] = useState(false);
  const [search, setSearch] = useState("");
  const [loaded, setLoaded] = useState(6);
  const [loading, setLoading] = useState(false);
  const [dark, setDark] = useState(false);
  const [density, setDensity] = useState("comfortable");
  const [toast, setToast] = useState(null);
  const [showKbHelp, setShowKbHelp] = useState(false);
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULS);

  // Apply tweaks live
  useEffect(() => {
    const root = document.documentElement;
    if (tweaks.accent) {
      // Convert hex to oklch-friendly: just set as raw color, accent uses var(--accent)
      root.style.setProperty("--accent", tweaks.accent);
      root.style.setProperty("--accent-ink", tweaks.accent);
      // soft variant via color-mix
      root.style.setProperty("--accent-soft", `color-mix(in oklch, ${tweaks.accent} 14%, var(--surface))`);
    }
  }, [tweaks.accent]);

  // Bridge tweak controls -> existing state where it makes sense
  useEffect(() => {
    if (tweaks.density && tweaks.density !== density) setDensity(tweaks.density);
  }, [tweaks.density]);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);

  const [apiItems, setApiItems] = useState([]);
  useEffect(() => {
    if (!window.KF_API) return;
    Promise.all([
      window.KF_API.fetchItems({ limit: 200 }),
      window.KF_API.fetchSources(),
    ]).then(([itemsData, sourcesData]) => {
      setApiItems((itemsData || []).map(window.KF_API.mapItem));
      setSources(sourcesData || []);
    }).catch(err => console.error("KF API fetch failed:", err));
  }, []);

  // Filter items (quest/source/tag/search — timeframe + quality handled in Feed)
  const items = useMemo(() => {
    return apiItems.filter(it => {
      const srcId = it.source || (it.sources && it.sources[0]?.id);
      if (notInterested.has(it.id)) return false;
      if (activeQuest && it.quest !== activeQuest) return false;
      if (activeSource && srcId !== activeSource) return false;
      if (activeTags.length > 0 && !it.tags.some(t => activeTags.includes(t))) return false;
      if (search && !(it.title + " " + it.summary).toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [apiItems, activeQuest, activeSource, activeTags, notInterested, search]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e) => {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") {
        if (e.key === "Escape") document.activeElement.blur();
        return;
      }
      // Get visible items (same filter Feed uses)
      const visibleItems = items.slice(0, loaded);
      const clamp = (n) => Math.max(0, Math.min(n, visibleItems.length - 1));

      switch (e.key) {
        case "j": {
          e.preventDefault();
          setFocusedIdx(i => clamp(i + 1));
          break;
        }
        case "k": {
          e.preventDefault();
          setFocusedIdx(i => clamp(i - 1));
          break;
        }
        case "o":
        case "Enter": {
          if (visibleItems[focusedIdx]) {
            onSelect(visibleItems[focusedIdx].id);
          }
          break;
        }
        case "a": {
          // Love focused item
          if (visibleItems[focusedIdx]) {
            const id = visibleItems[focusedIdx].id;
            setReaction(r => ({ ...r, [id]: r[id] === "love" ? null : "love" }));
            showToast("♥ Loved");
          }
          break;
        }
        case "l": {
          if (visibleItems[focusedIdx]) {
            const id = visibleItems[focusedIdx].id;
            setReaction(r => ({ ...r, [id]: r[id] === "like" ? null : "like" }));
            showToast("△ Liked");
          }
          break;
        }
        case "d": {
          if (visibleItems[focusedIdx]) {
            const id = visibleItems[focusedIdx].id;
            setReaction(r => ({ ...r, [id]: r[id] === "dislike" ? null : "dislike" }));
            showToast("▽ Disliked");
          }
          break;
        }
        case "s": {
          if (visibleItems[focusedIdx]) {
            const id = visibleItems[focusedIdx].id;
            setReaction(r => ({ ...r, [id]: r[id] === "love" ? null : "love" }));
            showToast(reaction[id] === "love" ? "Unsaved" : "+ Saved to garden");
          }
          break;
        }
        case "u": {
          if (visibleItems[focusedIdx]) {
            const id = visibleItems[focusedIdx].id;
            setReaction(r => ({ ...r, [id]: null }));
            showToast("↩ Reaction cleared");
          }
          break;
        }
        case "x": {
          if (visibleItems[focusedIdx]) {
            const id = visibleItems[focusedIdx].id;
            setNotInterested(s => new Set([...s, id]));
            setFocusedIdx(i => clamp(i));
            showToast("✕ Hidden");
          }
          break;
        }
        case "/": {
          e.preventDefault();
          window.__focusSearch && window.__focusSearch();
          break;
        }
        case "?": {
          setShowKbHelp(h => !h);
          break;
        }
        case "Escape": {
          if (showKbHelp) setShowKbHelp(false);
          else if (paneOpen) setPaneOpen(false);
          break;
        }
        default: break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [focusedIdx, items, loaded, reaction, showKbHelp, paneOpen]);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 1400);
  };

  const onLoadMore = useCallback(() => {
    setLoading(true);
    setTimeout(() => {
      setLoaded(n => n + 10);
      setLoading(false);
    }, 700);
  }, []);

  const onSelect = (id) => {
    setSelected(id);
    setSeen(s => new Set([...s, id]));
    if (!paneOpen) setPaneOpen(true);
  };

  const onNotInterested = (id) => {
    setNotInterested(s => new Set([...s, id]));
    showToast("✕ Hidden — not interested");
  };

  const onSaveMemo = () => {
    const lovedIds = Object.entries(reaction).filter(([, v]) => v === "love").map(([k]) => k);
    const newMemo = {
      id: "m" + Date.now(),
      date: "Today",
      title: memo.title,
      body: memo.body,
      tags: memo.tags,
      linkedItems: lovedIds,
    };
    setMemos([newMemo, ...memos]);
    showToast("✓ Memo saved to garden");
  };

  const selectedItem = apiItems.find(i => i.id === selected);
  const sourceMap = Object.fromEntries(sources.map(s => [s.id, s]));
  const stats = {
    ...window.STATS,
    totalToday: items.length || window.STATS.totalToday,
    newToday: apiItems.length > 0 ? items.filter(it => it.new).length : window.STATS.newToday,
  };

  return (
    <div className="app" data-pane-open={paneOpen && view === "radar"} data-density={density} data-screen-label="01 Daily Radar">
      <Sidebar
        view={view} setView={setView}
        activeQuest={activeQuest} setActiveQuest={setActiveQuest}
        activeSource={activeSource} setActiveSource={setActiveSource}
        activeTags={activeTags} setActiveTags={setActiveTags}
        stats={stats}
        quests={quests} setQuests={setQuests}
        sources={sources} setSources={setSources}
      />
      <main className="main">
        <Topbar
          stats={stats}
          dark={dark} setDark={setDark}
          density={density} setDensity={setDensity}
          paneOpen={paneOpen} setPaneOpen={setPaneOpen}
          qualityFilter={qualityFilter} setQualityFilter={setQualityFilter}
          search={search} setSearch={setSearch}
          onShowHelp={() => setShowKbHelp(true)}
        />
        {view === "radar" && (
          <Feed
            items={items}
            sources={sources}
            selected={selected}
            focusedIdx={focusedIdx}
            onSelect={onSelect}
            reaction={reaction} setReaction={setReaction}
            notInterested={notInterested} onNotInterested={onNotInterested}
            seen={seen} showSeen={showSeen} setShowSeen={setShowSeen}
            loaded={loaded} loading={loading}
            onLoadMore={onLoadMore}
            stats={stats}
            timeframe={timeframe} setTimeframe={setTimeframe}
            qualityFilter={qualityFilter}
          />
        )}
        {view === "library" && (
          <Library memos={memos} onOpen={() => {}} stats={stats} />
        )}
        {view === "recall" && (
          <>
            <header className="radar-header">
              <h1 className="radar-title">Recall</h1>
              <div className="radar-sub">
                <span><strong>12</strong> memos due for review</span>
                <span>spaced repetition · 2-7-21-60 day cadence</span>
              </div>
            </header>
            <div className="library">
              <Library memos={memos.slice(0, 3)} onOpen={() => {}} stats={stats} />
            </div>
          </>
        )}
      </main>
      {paneOpen && view === "radar" && (
        <RightPane
          item={selectedItem}
          source={selectedItem ? sourceMap[selectedItem.source] : null}
          paneTab={paneTab} setPaneTab={setPaneTab}
          memo={memo} setMemo={setMemo}
          onClose={() => setPaneOpen(false)}
          onSaveMemo={onSaveMemo}
          toast={toast}
        />
      )}
      {!paneOpen && toast && <div className="train-toast">{toast}</div>}
      {toast && paneOpen && <div className="train-toast">{toast}</div>}
      {showKbHelp && <KeyboardHelp onClose={() => setShowKbHelp(false)} />}

      <TweaksPanel title="Tweaks">
        <TweakSection title="Look">
          <TweakColor
            label="Accent"
            value={tweaks.accent}
            options={["#c97f3f", "#5a7fb8", "#4f8a5e", "#8a6dc9", "#b85a5a", "#14110d"]}
            onChange={v => setTweak("accent", v)}
          />
          <TweakRadio
            label="Density"
            value={tweaks.density}
            options={[
              { value: "compact", label: "Compact" },
              { value: "comfortable", label: "Normal" },
              { value: "spacious", label: "Spacious" },
            ]}
            onChange={v => setTweak("density", v)}
          />
          <TweakSelect
            label="Type pairing"
            value={tweaks.fontPairing}
            options={[
              { value: "serif-sans", label: "Newsreader + Inter (default)" },
              { value: "all-mono", label: "All JetBrains Mono (terminal)" },
              { value: "all-serif", label: "All Newsreader (editorial)" },
            ]}
            onChange={v => {
              setTweak("fontPairing", v);
              const root = document.documentElement;
              if (v === "all-mono") {
                root.style.setProperty("--font-serif", "var(--font-mono)");
                root.style.setProperty("--font-sans", "var(--font-mono)");
              } else if (v === "all-serif") {
                root.style.setProperty("--font-sans", "var(--font-serif)");
                root.style.setProperty("--font-serif", "Newsreader, serif");
              } else {
                root.style.removeProperty("--font-serif");
                root.style.removeProperty("--font-sans");
              }
            }}
          />
        </TweakSection>
        <TweakSection title="Feed">
          <TweakToggle
            label="Quality filter"
            value={qualityFilter}
            onChange={v => setQualityFilter(v)}
          />
          <TweakToggle
            label="Weekly recall banner"
            value={tweaks.showRecallBanner}
            onChange={v => {
              setTweak("showRecallBanner", v);
              document.querySelectorAll(".recall-banner").forEach(el => el.style.display = v ? "" : "none");
            }}
          />
        </TweakSection>
        <TweakSection title="Layout">
          <TweakRadio
            label="Right pane"
            value={paneOpen ? "open" : "closed"}
            options={[
              { value: "open", label: "Open" },
              { value: "closed", label: "Closed" },
            ]}
            onChange={v => setPaneOpen(v === "open")}
          />
          <TweakRadio
            label="Theme"
            value={dark ? "dark" : "light"}
            options={[
              { value: "light", label: "Light" },
              { value: "dark", label: "Dark" },
            ]}
            onChange={v => setDark(v === "dark")}
          />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("app"));
root.render(<App />);
