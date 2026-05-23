window.KF_API = (() => {
  const BASE = window.KF_API_BASE || "http://localhost:8000";

  async function req(path, opts = {}) {
    const r = await fetch(BASE + path, opts);
    if (!r.ok) {
      const text = await r.text().catch(() => "");
      throw new Error(`KF API ${r.status} ${path}: ${text}`);
    }
    if (r.status === 204) return null;
    return r.json();
  }

  function mapItem(it) {
    const now = Date.now();
    const ts = it.collected_at ? new Date(it.collected_at).getTime() : now;
    const ageMs = now - ts;
    const ageH = ageMs / 3_600_000;
    let time;
    if (ageH < 1) time = `${Math.round(ageH * 60)}m`;
    else if (ageH < 24) time = `${Math.round(ageH)}h`;
    else time = `${Math.round(ageH / 24)}d`;

    const meta = it.metadata && typeof it.metadata === "object" ? it.metadata : {};
    const todayStart = new Date(); todayStart.setHours(0, 0, 0, 0);
    const isNew = ts >= todayStart.getTime() && !it.is_read;

    return {
      id: it.id,
      source: it.source_id,
      quest: it.quest_id || it.category,
      title: it.title || "",
      summary: it.summary || "",
      body: it.body || "",
      url: it.url || "",
      points: meta.points || meta.score || 0,
      comments: meta.comments || meta.num_comments || 0,
      time,
      new: isNew,
      score: it.score || 0,
      tags: Array.isArray(it.tags) ? it.tags : [],
      category: it.category,
      is_read: it.is_read,
    };
  }

  return {
    mapItem,

    fetchItems(params = {}) {
      const q = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => { if (v != null) q.set(k, v); });
      const qs = q.toString();
      return req(`/items${qs ? "?" + qs : ""}`);
    },

    fetchSources() {
      return req("/sources");
    },

    addSource(body) {
      return req("/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    },

    deleteSource(id) {
      return req(`/sources/${encodeURIComponent(id)}`, { method: "DELETE" });
    },

    patchItem(id, body) {
      return req(`/items/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    },

    fetchHealth() {
      return req("/health");
    },
  };
})();
