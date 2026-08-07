/* ===== 码上飞升 前端主控制器 ===== */
"use strict";

const App = {
  state: null,
  editor: null,
  editorCodes: {},       // taskId -> 玩家编辑中的代码
  currentTaskId: null,   // 当前任务
  currentMode: null,     // main | debug | wave | branch
  hintShown: 0,
  solutionShown: false,
  spiritRoot: "金",
  slots: [],
  npcs: [],
  hintLevels: {},   // taskId -> 已请求的师尊提示等级
};

const $ = (id) => document.getElementById(id);

/* ---------- 工具 ---------- */

function showScreen(id) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.add("hidden"));
  $(id).classList.remove("hidden");
  window.scrollTo(0, 0);
}

function showIntroModal() {
  if (localStorage.getItem("ca_intro_seen") === "1") return;
  localStorage.setItem("ca_intro_seen", "1");
  $("modal-intro").classList.remove("hidden");
}

function showMessage(text) {
  $("modal-message-text").textContent = text;
  $("modal-message").classList.remove("hidden");
}

function hideMessage() {
  $("modal-message").classList.add("hidden");
}

function taskInputsText(task) {
  const inputs = (task && task.check && task.check.inputs) || [];
  return inputs.length ? "输入：" + inputs.join("，") : "";
}

function renderOutput(run) {
  const el = $("task-output");
  el.classList.remove("error", "timeout", "memory");
  if (!run) {
    el.textContent = "（尚未运行）";
    return;
  }
  let text = run.stdout || "";
  if (run.stderr) text += (text ? "\n" : "") + run.stderr;
  if (run.status === "ok") {
    el.textContent = text || "（无输出）";
  } else {
    el.classList.add(run.status === "timeout" ? "timeout" : run.status === "memory" ? "memory" : "error");
    el.textContent = "【" + run.message + "】" + (run.detail ? "\n" + run.detail : "");
  }
  $("run-status").textContent = "耗时 " + run.wall_time_ms + " ms";
}

function renderTaskResult(outcome) {
  const box = $("task-result");
  box.classList.remove("hidden", "pass", "fail");
  const title = $("result-title");
  const details = $("result-details");
  if (outcome.passed) {
    box.classList.add("pass");
    title.textContent = "✓ " + (outcome.message || "功法运转如意，大道可期！");
    const rows = (outcome.details || [])
      .filter((d) => !d.pass)
      .map((d) => "<div class='case'><span class='ok'>通过</span></div>");
    details.innerHTML = rows.join("") || "全部用例通过，+修为入账。";
  } else {
    box.classList.add("fail");
    title.textContent = "✗ " + (outcome.message || "灵力尚有不谐之处");
    const cases = outcome.details || [];
    let html = "";
    if (cases.length) {
      html = cases.map((d) => {
        if (d.pass) return "<div class='case'><span class='ok'>✓ 通过</span></div>";
        const exp = d.expected !== undefined ? "期望：" + d.expected : "";
        const act = d.actual !== undefined ? "实际：" + d.actual : "";
        const reason = d.reason || d.error || "";
        return "<div class='case'><span class='bad'>✗ 未通过</span><span>" + [exp, act, reason].filter(Boolean).join("　") + "</span></div>";
      }).join("");
    }
    if (outcome.run && outcome.run.status === "timeout") {
      html += "<div class='case'><span class='bad'>运行超时</span><span>疑似无限循环，检查循环条件</span></div>";
    }
    details.innerHTML = html || "请根据输出调整代码后再次提交。";
  }
}

function appendRewardLine(rewards) {
  const parts = [];
  if (rewards.cultivation) parts.push("修为+" + rewards.cultivation);
  if (rewards.comprehension) parts.push("悟性+" + rewards.comprehension);
  if (rewards.debug_exp) parts.push("Debug经验+" + rewards.debug_exp);
  if (rewards.items && rewards.items.length) parts.push("丹药 " + rewards.items.join("、"));
  if (!parts.length) return;
  const el = $("result-details");
  el.innerHTML += "<div class='case reward-line'>✦ 奖励入账：" + parts.join("　") + "</div>";
}

function flashAttrChanges(prev, next) {
  if (!prev || !next) return;
  const map = { cultivation: "#map-cultivation", comprehension: "#map-comprehension", mindset: "#map-mindset", debug_exp: "#map-debug-exp" };
  Object.keys(map).forEach((key) => {
    if (next[key] !== prev[key]) {
      const el = document.querySelector(map[key]);
      if (el) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
    }
  });
}

/* ---------- 界面渲染 ---------- */

async function renderTitle() {
  try {
    const data = await apiGet("/api/slots");
    App.slots = data.slots || [];
  } catch (e) {
    App.slots = [];
  }
  const list = $("slot-list");
  if (App.slots.length) {
    const sorted = App.slots.slice().sort((a, b) => (b.mtime || 0) - (a.mtime || 0));
    list.innerHTML = sorted.map((s) => {
      const p = s.player || {};
      return "<div class='slot-item' data-slot='" + escapeHtml(s.slot) + "'>" +
        "<span class='slot-name'>" + escapeHtml(p.name || s.slot) + "</span>" +
        "<span class='slot-info'>" + escapeHtml(p.realm_key || "凡人") + " · 修为 " + (p.cultivation || 0) + "</span></div>";
    }).join("");
  } else {
    list.innerHTML = "";
  }
  $("btn-continue").classList.toggle("hidden", !App.slots.length);
}

function renderMap() {
  const p = App.state.player;
  const realm = App.state.realm;
  $("map-player-name").textContent = p.name;
  const major = realm.major || {};
  $("map-player-realm").textContent = major.name === realm.name ? realm.name : (major.name + " · " + realm.name);
  $("map-player-title").textContent = p.title ? "「" + p.title + "」" : "";
  $("map-cultivation").textContent = p.cultivation;
  $("map-comprehension").textContent = p.comprehension;
  $("map-mindset").textContent = p.mindset;
  $("map-debug-exp").textContent = p.debug_exp;

  // 洞府修行卡片
  const cardTask = $("card-cultivate-task");
  const cultivateBtn = document.querySelector("#card-cultivate .btn");
  if (p.founded && App.state.current_task) {
    cardTask.textContent = "当前机缘：" + App.state.current_task.title;
    cultivateBtn.textContent = "进入修行";
    cultivateBtn.dataset.action = "task";
  } else if (p.founded && p.pending_breakthrough) {
    cardTask.textContent = "道基已成，可冲击金丹";
    cultivateBtn.textContent = "运功突破";
    cultivateBtn.dataset.action = "breakthrough";
  } else if (p.founded) {
    cardTask.textContent = "已筑基，道途初成";
    cultivateBtn.textContent = "回首道途";
    cultivateBtn.dataset.action = "complete";
  } else if (p.pending_breakthrough) {
    if (App.state.tribulation.unlocked && App.state.tribulation.waves.every((w) => w.passed)) {
      cardTask.textContent = "天劫已渡，可筑基！";
      cultivateBtn.textContent = "运功筑基";
      cultivateBtn.dataset.action = "breakthrough";
    } else if (App.state.tribulation.unlocked) {
      cardTask.textContent = "境界圆满，天劫将至";
      cultivateBtn.textContent = "前往渡劫台";
      cultivateBtn.dataset.action = "tribulation";
    } else {
      cardTask.textContent = "境界圆满，可突破！";
      cultivateBtn.textContent = "运功突破";
      cultivateBtn.dataset.action = "breakthrough";
    }
  } else if (App.state.current_task) {
    cardTask.textContent = "当前机缘：" + App.state.current_task.title;
    cultivateBtn.textContent = "进入修行";
    cultivateBtn.dataset.action = "task";
  } else {
    cardTask.textContent = "暂无任务";
    cultivateBtn.textContent = "闭关修炼";
    cultivateBtn.dataset.action = "none";
  }

  // 炼丹房
  const debugList = $("card-debug-list");
  if (App.state.debug_tasks.length) {
    debugList.innerHTML = App.state.debug_tasks
      .map((d) => "<div class='mini-task'>☠ " + d.title + "</div>")
      .join("");
  } else {
    debugList.innerHTML = "<div class='mini-task locked'>尚未发现心魔</div>";
  }

  // 渡劫台
  const tribCard = $("card-tribulation");
  const tribBtn = document.querySelector("#card-tribulation .btn");
  const tribState = $("card-tribulation-state");
  const trib = App.state.tribulation;
  if (trib.unlocked) {
    tribCard.classList.remove("locked");
    $("card-tribulation-desc").textContent = "天劫已现，渡过即筑基。";
    const passedCount = trib.waves.filter((w) => w.passed).length;
    tribState.textContent = "已渡 " + passedCount + " / " + trib.waves.length + " 重天劫";
    tribBtn.dataset.action = "tribulation";
  } else {
    tribCard.classList.add("locked");
    $("card-tribulation-desc").textContent = "炼气大圆满后开启。";
    tribState.textContent = "尚未开启";
    tribBtn.dataset.action = "locked";
  }

  // 机缘簿（支线）
  const branchList = $("card-branch-list");
  if (App.state.branch_tasks && App.state.branch_tasks.length) {
    branchList.innerHTML = App.state.branch_tasks
      .map((b) => "<div class='mini-task' data-branch='" + escapeHtml(b.id) + "'>✦ " + escapeHtml(b.title) + "</div>")
      .join("");
  } else {
    branchList.innerHTML = "<div class='mini-task locked'>暂无机缘</div>";
  }

  // 藏经阁
  const techs = App.state.techniques || [];
  const unlockedCount = techs.filter((t) => t.unlocked).length;
  $("card-library-state").textContent = "已参悟 " + unlockedCount + " / " + techs.length + " 门功法";

  // 储物袋
  const items = App.state.items || [];
  const owned = items.filter((it) => it.count > 0).length;
  $("card-bag-state").textContent = owned ? "丹药符箓 " + owned + " 种" : "空空如也";
  $("card-bag-desc").textContent = "随身携带的丹药与符箓（" + items.filter((it) => it.count > 0).map((it) => it.name + "×" + it.count).join("、") + "）。";

  // 成就碑
  const achList = App.state.achievements || [];
  const achOwned = achList.filter((a) => a.unlocked).length;
  $("card-achievement-state").textContent = "已证 " + achOwned + " / " + achList.length + " 项道果";

  // 秘境入口
  const secretRealms = App.state.secret_realms || [];
  const secretUnlocked = secretRealms.filter((r) => r.unlocked).length;
  const secretEnterable = secretRealms.filter((r) => r.enterable).length;
  const secretCleared = secretRealms.reduce((s, r) => s + (r.cleared || 0), 0);
  $("card-secret-desc").textContent = secretEnterable
    ? "机缘已至，可入 " + secretEnterable + " 处秘境。"
    : secretUnlocked ? "秘境已标记于罗盘，待境界圆满。" : "云游子在此守望，机缘自成。";
  $("card-secret-state").textContent = "已通 " + secretCleared + " 次 · 已探 " + secretUnlocked + " / " + secretRealms.length + " 处";

  // NPC
  const npcStrip = $("npc-list");
  npcStrip.innerHTML = (App.npcs || [])
    .map((n) =>
      "<div class='npc-chip' data-npc='" + escapeHtml(n.id) + "'>" +
      "<span class='npc-icon'>" + (n.icon || "🧙") + "</span>" +
      "<span><span class='npc-name'>" + escapeHtml(n.name) + "</span>" +
      "<span class='npc-title'>" + escapeHtml(n.title || "") + "</span></span></div>"
    ).join("");
}

/* ---------- 任务界面 ---------- */

function setupEditor() {
  if (App.editor) return;
  App.editor = CodeMirror.fromTextArea($("code-editor"), {
    mode: "python",
    lineNumbers: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    matchBrackets: true,
    autoCloseBrackets: false,
    styleActiveLine: true,
  });
}

async function openTask(taskId, mode, taskDef) {
  App.currentTaskId = taskId;
  App.currentMode = mode;
  const task = taskDef || (await apiGet("/api/tasks/" + taskId));
  App.currentTaskDef = task;
  setupEditor();

  $("task-title").textContent = task.title;
  $("task-realm").textContent = App.state.realm.name;
  const tag = $("task-mode-tag");
  const isTrial = task.kind === "trial";
  tag.className = "tag " + (mode === "debug" ? "tag-debug" : mode === "wave" ? "tag-wave" : mode === "branch" ? "tag-branch" : mode === "secret" ? "tag-secret" : isTrial ? "tag-trial" : "tag-main");
  tag.textContent = mode === "debug" ? "炼丹房 · 心魔" : mode === "wave" ? "渡劫台 · 天劫" : mode === "branch" ? "机缘簿 · 支线" : mode === "secret" ? "秘境 · 试炼" : isTrial ? "综合试炼" : "主线修行";

  $("task-story").textContent = task.story;

  // 功法讲解：当前境界教学（天劫时显示天劫说明）
  const teaching = App.state.realm.teaching || [];
  $("task-teaching").innerHTML = teaching.map((t) =>
    "<h5 style='color:var(--gold);margin:10px 0 6px;'>" + escapeHtml(t.title) + "</h5>" + renderMarkdown(t.body)
  ).join("");

  // 提示
  App.hintShown = 0;
  App.solutionShown = false;
  if (!(taskId in App.hintLevels)) App.hintLevels[taskId] = 0;
  $("task-hints").innerHTML = (task.hints || []).map((h) => "<li class='hidden'>" + escapeHtml(h) + "</li>").join("");
  $("btn-reveal-hint").classList.remove("hidden");
  const solutionRow = $("solution-row");
  solutionRow.innerHTML = "";
  if (task.no_solution) {
    solutionRow.classList.add("hidden");
  } else {
    solutionRow.classList.remove("hidden");
    solutionRow.innerHTML = '<button id="btn-show-solution" class="btn btn-small btn-ghost">查看参考答案</button>';
    $("btn-show-solution").addEventListener("click", showSolution);
  }
  $("master-advice").innerHTML = "青玄子静坐于旁，等你叩问。";

  // 编辑器内容
  if (!(taskId in App.editorCodes)) {
    App.editorCodes[taskId] = task.starter_code || "";
  }
  App.editor.setValue(App.editorCodes[taskId]);
  App.editor.refresh();

  $("run-status").textContent = taskInputsText(task);
  renderOutput(null);
  $("task-result").classList.add("hidden");
  showScreen("screen-task");
}

async function runCurrent() {
  const taskId = App.currentTaskId;
  const code = App.editor.getValue();
  App.editorCodes[taskId] = code;
  $("run-status").textContent = "运行中…";
  try {
    const url = App.currentMode === "secret"
      ? "/api/secret-realms/" + App.currentTaskDef.secret_realm + "/run"
      : "/api/tasks/" + taskId + "/run";
    const data = await apiPost(url, { code });
    renderOutput(data.run);
  } catch (e) {
    $("task-output").textContent = "【" + e.message + "】";
    $("task-output").classList.add("error");
    $("run-status").textContent = "";
  }
}

async function askMaster() {
  const taskId = App.currentTaskId;
  const level = (App.hintLevels[taskId] || 0) + 1;
  App.hintLevels[taskId] = level;
  $("master-advice").innerHTML = "青玄子掐指推演…";
  try {
    const data = await apiPost("/api/ai/guidance", { task_id: taskId, hint_level: level });
    const levelNames = ["", "方向提示", "范围缩小", "明确线索", "查看答案"];
    $("master-advice").innerHTML =
      "<span class='master-level'>L" + data.level + " · " + (levelNames[data.level] || "") + "</span>" +
      escapeHtml(data.text);
  } catch (e) {
    $("master-advice").textContent = "师尊闭目不语……（" + e.message + "）";
  }
}

async function askAnalyze() {
  const taskId = App.currentTaskId;
  const code = App.editor.getValue();
  App.editorCodes[taskId] = code;
  $("master-advice").innerHTML = "青玄子凝神观你运功…";
  try {
    const data = await apiPost("/api/ai/analyze", { task_id: taskId, code });
    $("master-advice").innerHTML =
      "<span class='master-level'>师尊诊断</span>" + escapeHtml(data.analysis);
    if (data.run && data.run.status !== "ok") {
      const el = $("task-output");
      el.classList.add(data.run.status === "timeout" ? "timeout" : data.run.status === "memory" ? "memory" : "error");
      el.textContent = "【" + data.run.message + "】" + (data.run.detail ? "\n" + data.run.detail : "");
    }
  } catch (e) {
    $("master-advice").textContent = "师尊凝眉……（" + e.message + "）";
  }
}

async function submitCurrent() {
  const taskId = App.currentTaskId;
  const code = App.editor.getValue();
  App.editorCodes[taskId] = code;
  const btn = $("btn-submit");
  btn.disabled = true;
  btn.textContent = "验证中…";
  const mindsetBefore = App.state.player ? App.state.player.mindset : 100;
  try {
    const url = App.currentMode === "secret"
      ? "/api/secret-realms/" + App.currentTaskDef.secret_realm + "/submit"
      : "/api/tasks/" + taskId + "/submit";
    const data = await apiPost(url, { code });
    const prevPlayer = App.state.player;
    App.state = data.state;
    renderTaskResult(data.outcome);
    $("task-result").classList.remove("hidden");
    if (data.outcome.passed && data.events && data.events.rewards) {
      appendRewardLine(data.events.rewards);
    }
    flashAttrChanges(prevPlayer, App.state.player);
    if (data.outcome.passed) {
      if (App.currentMode === "secret") {
        await handleSecretClear(data);
      } else {
        await handleCompletionEvents(data.events);
      }
    } else {
      const delta = App.state.player.mindset - mindsetBefore;
      if (delta < 0) {
        const el = $("result-details");
        el.innerHTML += "<div class='case'><span class='bad'>心境 -" + (-delta) + "</span><span>心魔侵扰，道心受损；连续失败会让师尊更早出手。</span></div>";
      }
    }
    showAchievementPopup(data.new_achievements);
  } catch (e) {
    showMessage(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "⚔ 提交验证";
  }
}

async function handleCompletionEvents(events) {
  const rewards = events.rewards || {};
  const rewardText = [];
  if (rewards.cultivation) rewardText.push("修为+" + rewards.cultivation);
  if (rewards.comprehension) rewardText.push("悟性+" + rewards.comprehension);
  if (rewards.debug_exp) rewardText.push("Debug经验+" + rewards.debug_exp);
  if (events.task_completed && !events.realm_complete && !App.state.player.pending_breakthrough) {
    renderMap();
    showScreen("screen-map");
    if (rewardText.length) showMessage("机缘了结，奖励入账：" + rewardText.join("，") + "。");
    return;
  }
  if (events.wave_completed) {
    const allPassed = App.state.tribulation.waves.every((w) => w.passed);
    if (allPassed) {
      showMessage("三道天劫皆已渡过！雷云散去，道基在望——去运功筑基吧。");
    } else {
      showMessage("又一重天劫已渡！继续前往渡劫台。");
    }
    renderMap();
    showScreen("screen-map");
    return;
  }
  if (events.tribulation_unlocked) {
    showMessage("炼气大圆满！渡劫台已开启——渡过天劫，便可筑基。");
    renderMap();
    showScreen("screen-map");
    return;
  }
  if (App.state.player.pending_breakthrough) {
    openBreakthroughModal();
    return;
  }
  // debug 任务完成
  renderMap();
  showScreen("screen-map");
}

async function handleSecretClear(data) {
  const ev = data.events || {};
  const rewards = ev.rewards || {};
  const parts = [];
  if (rewards.cultivation) parts.push("修为+" + rewards.cultivation);
  if (rewards.comprehension) parts.push("悟性+" + rewards.comprehension);
  if (rewards.debug_exp) parts.push("Debug经验+" + rewards.debug_exp);
  if (rewards.items && rewards.items.length) parts.push("获得丹药 " + rewards.items.join("、"));
  const head = ev.first_clear ? "首通秘境，机缘入账！" : "秘境再临，收获不菲。";
  renderMap();
  showScreen("screen-map");
  showMessage(head + (parts.length ? "（" + parts.join("，") + "）" : ""));
}

/* ---------- 突破弹窗 ---------- */

function openBreakthroughModal() {
  const p = App.state.player;
  const realm = App.state.realm;
  $("bt-title").textContent = "境界圆满";
  $("bt-desc").textContent = realm.name + "已至巅峰，灵力翻涌。是时候冲击下一境界了！";
  $("btn-breakthrough").textContent = "运功突破";
  $("modal-breakthrough").classList.remove("hidden");
  $("btn-breakthrough").dataset.step = "go";
}

async function doBreakthrough() {
  const btn = $("btn-breakthrough");
  const prevTechIds = (App.state.techniques || []).filter((t) => t.unlocked).map((t) => t.id);
  if (btn.dataset.step === "done") {
    $("modal-breakthrough").classList.add("hidden");
    renderMap();
    showScreen("screen-map");
    return;
  }
  btn.disabled = true;
  try {
    const data = await apiPost("/api/breakthrough");
    App.state = data.state;
    btn.disabled = false;
    const ev = data.event;
    if (ev.founded) {
      $("bt-title").textContent = "筑基成功！";
      $("bt-desc").textContent = "天劫已渡，道基已成。自此，你正式踏入修仙之途。";
      btn.textContent = "继续";
      btn.dataset.step = "done";
      $("modal-breakthrough").classList.add("hidden");
      showAchievementPopup(data.new_achievements);
      renderComplete();
      return;
    }
    const from = realmNameOf(ev.from);
    const to = realmNameOf(ev.to);
    $("bt-title").textContent = "突破成功！";
    $("bt-desc").textContent = from + " → " + to + "。灵力奔涌如潮，你已更进一步。";
    renderBreakthroughDetail(prevTechIds);
    btn.textContent = "继续";
    btn.dataset.step = "done";
    showAchievementPopup(data.new_achievements);
  } catch (e) {
    btn.disabled = false;
    $("modal-breakthrough").classList.add("hidden");
    showMessage(e.message);
  }
}

function renderBreakthroughDetail(prevTechIds) {
  const parts = [];
  const realm = App.state.realm;
  if (realm && realm.intro) {
    const first = realm.intro.split("。")[0];
    if (first) parts.push("新境感悟：" + first + "。");
  }
  const techs = App.state.techniques || [];
  const newly = techs.filter((t) => t.unlocked && (prevTechIds || []).indexOf(t.id) < 0);
  if (newly.length) {
    parts.push("新参悟功法：" + newly.map((t) => t.title || t.name).join("、"));
  }
  $("bt-detail").textContent = parts.join("\n");
}

function realmNameOf(key) {
  if (App.state && App.state.realm_names && App.state.realm_names[key]) {
    return App.state.realm_names[key];
  }
  return key;
}

/* ---------- 藏经阁 / 对话 / 储物袋 ---------- */

async function loadNpcs() {
  try {
    const data = await apiGet("/api/npcs");
    App.npcs = data.npcs || [];
  } catch (e) {
    App.npcs = [];
  }
}

function openLibrary() {
  $("library-realm").textContent = App.state.realm.name;
  const techs = App.state.techniques || [];
  $("technique-list").innerHTML = techs.map((t) => {
    const body = t.unlocked
      ? (t.teaching || []).map((b) => "<h5>" + escapeHtml(b.title) + "</h5>" + renderMarkdown(b.body)).join("")
      : "";
    const hasBody = !!body;
    return (
      "<div class='technique-item" + (t.unlocked ? "" : " locked") + "' data-tech='" + escapeHtml(t.id) + "'>" +
      "<div class='tech-head" + (hasBody ? " tech-toggle' data-toggle='" + escapeHtml(t.id) + "'" : "'") + ">" +
      "<span class='tech-name'>" + escapeHtml(t.title) + " · " + escapeHtml(t.name) + "</span>" +
      "<span class='tech-state'>" + (t.unlocked ? (hasBody ? "▸ 展开讲解" : "已参悟") : "🔒 未解锁") + "</span></div>" +
      (hasBody ? "<div class='technique-body collapsed'>" + body + "</div>" : "") +
      "</div>"
    );
  }).join("");
  showScreen("screen-library");
}

async function openDialogue(npcId) {
  try {
    const data = await apiGet("/api/dialogues/" + npcId);
    App.dialogueNpc = npcId;
    renderDialogue(data.dialogue);
    $("modal-dialogue").classList.remove("hidden");
  } catch (e) {
    showMessage(e.message);
  }
}

function renderDialogue(dlg) {
  App.dialogueNodeId = dlg.node_id;
  const npc = (App.npcs || []).find((n) => n.id === dlg.npc_id) || {};
  $("dlg-icon").textContent = npc.icon || "🧙";
  $("dlg-name").textContent = npc.name || dlg.npc_id;
  $("dlg-title").textContent = npc.title || "";
  $("dlg-text").textContent = dlg.text || "……";
  $("dlg-effects").textContent = (dlg.effects || []).join("　");
  $("dlg-options").innerHTML = (dlg.options || [])
    .map((o, i) => "<button class='btn btn-ghost dlg-option' data-option='" + i + "'>" + escapeHtml(o.text) + "</button>")
    .join("") || "";
}

async function chooseDialogue(npcId, nodeId, optionIndex) {
  try {
    const data = await apiPost("/api/dialogues/" + npcId + "/choose", {
      node_id: nodeId,
      option_index: optionIndex,
    });
    App.state = data.state;
    if (data.dialogue.ended) {
      $("modal-dialogue").classList.add("hidden");
      renderMap();
      showAchievementPopup(data.new_achievements);
      return;
    }
    renderDialogue(data.dialogue);
    showAchievementPopup(data.new_achievements);
  } catch (e) {
    showMessage(e.message);
  }
}

function openAchievements() {
  const achs = App.state.achievements || [];
  $("achievement-list").innerHTML = achs.map((a) =>
    "<div class='achievement-item" + (a.unlocked ? "" : " locked") + "'>" +
    "<span class='ach-icon'>" + (a.unlocked ? (a.icon || "🏅") : "🔒") + "</span>" +
    "<div class='ach-main'><div class='ach-name'>" + escapeHtml(a.name) + "</div>" +
    "<div class='ach-desc'>" + escapeHtml(a.desc) + "</div></div>" +
    "<span class='ach-state'>" + (a.unlocked ? (a.title ? "称号「" + a.title + "」" : "已达成") : "未达成") + "</span>" +
    "</div>"
  ).join("");
  $("modal-achievement").classList.remove("hidden");
}

function showAchievementPopup(list) {
  if (!list || !list.length) return;
  const ach = list[list.length - 1];
  $("ach-pop-icon").textContent = ach.icon || "🏅";
  $("ach-pop-name").textContent = ach.name;
  $("ach-pop-desc").textContent = ach.desc;
  const rw = [];
  if (ach.reward && ach.reward.cultivation) rw.push("修为+" + ach.reward.cultivation);
  if (ach.reward && ach.reward.comprehension) rw.push("悟性+" + ach.reward.comprehension);
  if (ach.reward && ach.reward.debug_exp) rw.push("除魔经验+" + ach.reward.debug_exp);
  $("ach-pop-reward").textContent = rw.length ? "奖励：" + rw.join("，") : "";
  $("modal-ach-pop").classList.remove("hidden");
}

function openBag() {
  const items = (App.state.items || []).filter((it) => it.count > 0);
  $("bag-items").innerHTML = items.length
    ? items.map((it) =>
        "<div class='bag-item'>" +
        "<div class='bag-item-main'><span>" + (it.icon || "📦") + "</span>" +
        "<div><div class='bag-name'>" + escapeHtml(it.name) + " ×" + it.count + "</div>" +
        "<div class='bag-desc'>" + escapeHtml(it.desc) + "</div></div></div>" +
        "<button class='btn btn-small btn-jade' data-use='" + escapeHtml(it.id) + "'>使用</button>" +
        "</div>"
      ).join("")
    : "<div class='bag-empty'>储物袋空空如也。去完成机缘，获取丹药吧。</div>";
  $("modal-bag").classList.remove("hidden");
}

async function useItem(itemId) {
  try {
    const data = await apiPost("/api/items/" + itemId + "/use");
    App.state = data.state;
    $("modal-bag").classList.add("hidden");
    renderMap();
    showMessage(data.result.message);
    showAchievementPopup(data.new_achievements);
  } catch (e) {
    showMessage(e.message);
  }
}

/* ---------- 秘境 ---------- */

async function openSecretRealms() {
  let data;
  try {
    data = await apiGet("/api/secret-realms");
  } catch (e) {
    showMessage(e.message);
    return;
  }
  App.state.secret_realms = data.secret_realms || [];
  $("secret-screen-realm").textContent = App.state.realm.name;
  const list = App.state.secret_realms;
  $("secret-realm-list").innerHTML = list.map((r) => {
    const stateText = r.cleared > 0 ? "已通 " + r.cleared + " 次" : r.enterable ? "可进入" : r.unlocked ? "境界未至" : "未解锁";
    const btn = r.enterable
      ? "<button class='btn btn-gold btn-small' data-enter='" + escapeHtml(r.id) + "'>进入秘境</button>"
      : "";
    return (
      "<div class='secret-realm-card" + (r.enterable ? "" : " locked") + "'>" +
      "<div class='secret-realm-icon'>" + (r.icon || "🌀") + "</div>" +
      "<div class='secret-realm-main'>" +
      "<div class='secret-realm-name'>" + escapeHtml(r.name) + "</div>" +
      "<div class='secret-realm-desc'>" + escapeHtml(r.desc || "") + "</div>" +
      "</div>" +
      "<div class='secret-realm-side'><span class='secret-state'>" + stateText + "</span>" + btn + "</div>" +
      "</div>"
    );
  }).join("") || "<div class='bag-empty'>暂无可探秘境。</div>";
  showScreen("screen-secret");
}

async function enterSecretRealm(realmId) {
  try {
    const data = await apiPost("/api/secret-realms/" + realmId + "/enter");
    await openTask("secret:" + realmId, "secret", data.challenge);
  } catch (e) {
    showMessage(e.message);
  }
}

/* ---------- 渡劫台 ---------- */

async function openTribulation() {
  const trib = App.state.tribulation;
  $("tribulation-intro").innerHTML = renderMarkdown(trib.intro);
  const waves = trib.waves;
  $("tribulation-waves").innerHTML = waves.map((w) => {
    const stateCls = w.passed ? "passed" : w.current ? "current" : "locked";
    const stateText = w.passed ? "已渡过" : w.current ? "迎劫中" : "未开启";
    const btn = w.current
      ? "<button class='btn btn-red btn-small' data-wave='" + w.key + "'>迎劫</button>"
      : "";
    return (
      "<div class='wave-card'>" +
      "<div class='wave-num'>" + w.order + "</div>" +
      "<div class='wave-info'><h3>" + escapeHtml(w.title) + "</h3><p>" + escapeHtml(w.intro || "") + "</p></div>" +
      "<span class='wave-state " + stateCls + "'>" + stateText + "</span>" + btn +
      "</div>"
    );
  }).join("");
  showScreen("screen-tribulation");
}

/* ---------- 筑基完成 ---------- */

function renderComplete() {
  const p = App.state.player;
  $("complete-name").textContent = p.name;
  $("complete-cultivation").textContent = p.cultivation;
  $("complete-tasks").textContent = p.completed_tasks.length + p.debug_completed.length;
  showScreen("screen-complete");
}

function showSolution() {
  if (App.solutionShown) return;
  App.solutionShown = true;
  $("solution-row").innerHTML =
    "<span class='solution-code'>" + escapeHtml(App.currentTaskDef.solution || "") + "</span>";
}

/* ---------- 事件绑定 ---------- */

function bindEvents() {
  $("btn-start-new").addEventListener("click", () => {
    $("input-slot").value = "";
    showScreen("screen-create");
  });
  $("btn-continue").addEventListener("click", async () => {
    const slots = App.slots || [];
    if (!slots.length) return;
    const latest = slots.slice().sort((a, b) => (b.mtime || 0) - (a.mtime || 0))[0];
    try {
      const state = await apiPost("/api/game/load", { slot: latest.slot });
      App.state = state;
      renderMap();
      showScreen("screen-map");
    } catch (e) {
      showMessage(e.message);
    }
  });
  $("slot-list").addEventListener("click", async (e) => {
    const item = e.target.closest("[data-slot]");
    if (!item) return;
    try {
      const state = await apiPost("/api/game/load", { slot: item.dataset.slot });
      App.state = state;
      renderMap();
      showScreen("screen-map");
    } catch (err) {
      showMessage(err.message);
    }
  });

  $("btn-create-back").addEventListener("click", () => showScreen("screen-title"));
  $("btn-create-confirm").addEventListener("click", async () => {
    const name = $("input-name").value.trim() || "无名散修";
    const slot = $("input-slot").value.trim() || "default";
    try {
      const state = await apiPost("/api/game/new", { name, slot, spirit_root: App.spiritRoot });
      App.state = state;
      renderMap();
      showScreen("screen-map");
      showIntroModal();
    } catch (e) {
      showMessage(e.message);
    }
  });
  document.querySelectorAll(".spirit-root").forEach((el) => {
    el.addEventListener("click", () => {
      document.querySelectorAll(".spirit-root").forEach((x) => x.classList.remove("selected"));
      el.classList.add("selected");
      App.spiritRoot = el.dataset.root;
    });
  });

  $("btn-save").addEventListener("click", async () => {
    try {
      const r = await apiPost("/api/game/save");
      showMessage("已存入轮回印记（存档成功）。");
    } catch (e) {
      showMessage(e.message);
    }
  });
  $("btn-exit").addEventListener("click", () => showScreen("screen-title"));

  // 洞府卡片
  document.querySelector("#card-cultivate .btn").addEventListener("click", async () => {
    const action = document.querySelector("#card-cultivate .btn").dataset.action;
    await handleCultivateAction(action);
  });
  document.querySelector("#card-debug .btn").addEventListener("click", async () => {
    if (!App.state.debug_tasks.length) {
      showMessage("尚未发现心魔，先去修炼主线吧。");
      return;
    }
    await openTask(App.state.debug_tasks[0].id, "debug");
  });
  document.querySelector("#card-tribulation .btn").addEventListener("click", async () => {
    if (App.state.tribulation.unlocked) await openTribulation();
    else showMessage("渡劫台尚未开启，先修炼至炼气大圆满。");
  });
  document.querySelector("#card-library .btn").addEventListener("click", () => openLibrary());
  document.querySelector("#card-bag .btn").addEventListener("click", () => openBag());
  document.querySelector("#card-achievement .btn").addEventListener("click", () => openAchievements());
  $("btn-achievement-close").addEventListener("click", () => $("modal-achievement").classList.add("hidden"));
  $("btn-ach-pop-close").addEventListener("click", () => $("modal-ach-pop").classList.add("hidden"));
  $("modal-achievement").addEventListener("click", (e) => {
    if (e.target === $("modal-achievement")) $("modal-achievement").classList.add("hidden");
  });
  document.querySelector("#card-branch .btn").addEventListener("click", () => {
    if (!App.state.branch_tasks.length) {
      showMessage("暂无机缘。去与宗门同道攀谈，或许会有奇遇。");
      return;
    }
    const first = App.state.branch_tasks[0];
    openTask(first.id, "branch");
  });
  $("card-branch-list").addEventListener("click", async (e) => {
    const item = e.target.closest("[data-branch]");
    if (!item) return;
    await openTask(item.dataset.branch, "branch");
  });
  document.querySelector("#card-secret .btn").addEventListener("click", () => openSecretRealms());
  $("btn-secret-back").addEventListener("click", () => {
    renderMap();
    showScreen("screen-map");
  });
  $("secret-realm-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-enter]");
    if (!btn) return;
    await enterSecretRealm(btn.dataset.enter);
  });
  $("npc-list").addEventListener("click", (e) => {
    const chip = e.target.closest("[data-npc]");
    if (!chip) return;
    openDialogue(chip.dataset.npc);
  });

  // 任务界面
  $("btn-task-back").addEventListener("click", () => {
    renderMap();
    showScreen("screen-map");
  });
  $("btn-run").addEventListener("click", runCurrent);
  $("btn-submit").addEventListener("click", submitCurrent);
  $("btn-reset").addEventListener("click", () => {
    if (App.currentTaskDef) {
      App.editorCodes[App.currentTaskId] = App.currentTaskDef.starter_code || "";
      App.editor.setValue(App.editorCodes[App.currentTaskId]);
    }
  });
  $("btn-ask-master").addEventListener("click", askMaster);
  $("btn-ask-analyze").addEventListener("click", askAnalyze);
  $("btn-reveal-hint").addEventListener("click", () => {
    const items = document.querySelectorAll("#task-hints li.hidden");
    if (!items.length) {
      $("btn-reveal-hint").classList.add("hidden");
      return;
    }
    items[0].classList.remove("hidden");
  });
  $("btn-show-solution").addEventListener("click", showSolution);

  // 藏经阁
  $("btn-library-back").addEventListener("click", () => {
    renderMap();
    showScreen("screen-map");
  });
  $("technique-list").addEventListener("click", (e) => {
    const head = e.target.closest(".tech-toggle");
    if (!head) return;
    const body = head.closest(".technique-item").querySelector(".technique-body");
    if (!body) return;
    const collapsed = body.classList.toggle("collapsed");
    const stateEl = head.querySelector(".tech-state");
    if (stateEl) stateEl.textContent = collapsed ? "▸ 展开讲解" : "▾ 收起讲解";
  });

  // 对话
  $("btn-dlg-close").addEventListener("click", () => {
    $("modal-dialogue").classList.add("hidden");
    renderMap();
  });
  $("dlg-options").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-option]");
    if (!btn || !App.dialogueNpc) return;
    chooseDialogue(App.dialogueNpc, App.dialogueNodeId, Number(btn.dataset.option));
  });
  $("modal-dialogue").addEventListener("click", (e) => {
    if (e.target === $("modal-dialogue")) $("modal-dialogue").classList.add("hidden");
  });

  // 储物袋
  $("btn-bag-close").addEventListener("click", () => $("modal-bag").classList.add("hidden"));
  $("bag-items").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-use]");
    if (!btn) return;
    useItem(btn.dataset.use);
  });
  $("modal-bag").addEventListener("click", (e) => {
    if (e.target === $("modal-bag")) $("modal-bag").classList.add("hidden");
  });

  // 渡劫台
  $("btn-tribulation-back").addEventListener("click", () => {
    renderMap();
    showScreen("screen-map");
  });
  $("tribulation-waves").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-wave]");
    if (!btn) return;
    const wave = App.state.tribulation.waves.find((w) => w.key === btn.dataset.wave);
    if (!wave || !wave.current) return;
    await openTask(wave.task_id, "wave");
  });

  // 完成界面
  $("btn-complete-back").addEventListener("click", () => {
    renderMap();
    showScreen("screen-map");
  });
  $("btn-complete-restart").addEventListener("click", () => showScreen("screen-create"));

  // 弹窗
  $("btn-breakthrough").addEventListener("click", doBreakthrough);
  $("btn-modal-close").addEventListener("click", hideMessage);
  $("btn-intro-go").addEventListener("click", () => {
    $("modal-intro").classList.add("hidden");
    if (App.state && App.state.current_task) {
      const btn = document.querySelector("#card-cultivate .btn");
      if (btn && btn.dataset.action === "task") btn.classList.add("pulse-cta");
    }
  });
  $("modal-intro").addEventListener("click", (e) => {
    if (e.target === $("modal-intro")) $("modal-intro").classList.add("hidden");
  });
  $("modal-message").addEventListener("click", (e) => {
    if (e.target === $("modal-message")) hideMessage();
  });
}

async function handleCultivateAction(action) {
  if (action === "task" && App.state.current_task) {
    await openTask(App.state.current_task.id, "main");
  } else if (action === "breakthrough") {
    openBreakthroughModal();
  } else if (action === "tribulation") {
    await openTribulation();
  } else if (action === "complete") {
    renderComplete();
  } else if (action === "none") {
    showMessage("此地灵气已尽，静待机缘。");
  }
}

/* ---------- 初始化 ---------- */

async function init() {
  bindEvents();
  setupEditor();
  try {
    const state = await apiGet("/api/state");
    App.state = state;
    await loadNpcs();
    await renderTitle();
    showScreen("screen-title");
  } catch (e) {
    showMessage("无法连接天地规则（服务器）。请确认服务已启动。");
    showScreen("screen-title");
  }
}

document.addEventListener("DOMContentLoaded", init);
