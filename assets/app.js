/* Renders the parts that change: project list and the build log.
   Both come from JSON so the page never needs a rebuild of its own code. */

const $ = (sel, root = document) => root.querySelector(sel);

const fmtDay = (iso) => {
  const d = new Date(iso);
  return `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

const fmtAgo = (iso) => {
  const diff = Date.now() - new Date(iso).getTime();
  const hour = 36e5;
  if (diff < hour) return `${Math.max(1, Math.round(diff / 6e4))} 分钟前`;
  if (diff < 24 * hour) return `${Math.round(diff / hour)} 小时前`;
  if (diff < 72 * hour) return `${Math.round(diff / (24 * hour))} 天前`;
  return fmtDay(iso);
};

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function loadJSON(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

function renderProjects(projects) {
  const list = $("#project-list");
  list.innerHTML = projects
    .map(
      (p, i) => `
      <li class="project">
        <span class="project-index" aria-hidden="true">${String(i + 1).padStart(2, "0")}</span>
        <div>
          <h3><a href="${esc(p.url)}" rel="noopener">${esc(p.name)}</a></h3>
          <p class="project-why">${esc(p.why)}</p>
        </div>
        <div class="project-meta">
          ${p.stack.map((s) => `<span class="tag">${esc(s)}</span>`).join("")}
          <span>${esc(p.note)}</span>
        </div>
      </li>`
    )
    .join("");
}

function renderLog(data) {
  const entries = data.entries ?? [];
  const timeline = $("#timeline");

  $('[data-counter="commits"]').textContent = data.totals.commits;
  $('[data-counter="repos"]').textContent = data.totals.repos;
  const built = $('[data-counter="built"]');
  built.textContent = fmtAgo(data.generated_at);
  built.classList.add("is-text");
  built.title = new Date(data.generated_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });

  $("#log-sub").textContent = `最近 ${data.window_days} 天，我按下过的 ${entries.length} 个 commit`;

  if (!entries.length) {
    timeline.innerHTML = '<li class="empty">这阵子没提交——要么在憋大的，要么在摸鱼 🐟</li>';
    return;
  }

  const fresh = Date.now() - 24 * 36e5;
  timeline.innerHTML = entries
    .map((e, i) => {
      const isFresh = new Date(e.date).getTime() > fresh ? " is-fresh" : "";
      return `
      <li class="entry${isFresh}" style="--i:${i}">
        <span class="entry-when">${fmtDay(e.date)}</span>
        <p class="entry-msg"><a href="${esc(e.url)}" rel="noopener">${esc(e.message)}</a></p>
        <p class="entry-ctx">
          <span class="repo">${esc(e.repo)}</span>
          · <a class="entry-sha" href="${esc(e.url)}" rel="noopener">${esc(e.short)}</a>
          · ${fmtAgo(e.date)}
        </p>
      </li>`;
    })
    .join("");
}

(async function main() {
  try {
    const [site, updates] = await Promise.all([loadJSON("data/site.json"), loadJSON("data/updates.json")]);
    renderProjects(site.projects);
    renderLog(updates);
  } catch (err) {
    console.error(err);
    $("#timeline").innerHTML =
      '<li class="empty">数据没读到，可能是本地直接打开文件、或者脚本还没跑过。线上不会这样。</li>';
  }
})();
