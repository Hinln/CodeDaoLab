/* 前端端到端测试（playwright-core + 系统 Chrome） */
const { spawn } = require("child_process");
const path = require("path");
const { chromium } = require(path.join(__dirname, "..", ".tools", "node_modules", "playwright-core"));

const ROOT = path.resolve(__dirname, "..");
const PORT = 8760;
const BASE = "http://127.0.0.1:" + PORT;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let CURRICULUM_CACHE = null;
async function getCurriculum() {
  if (!CURRICULUM_CACHE) CURRICULUM_CACHE = await (await fetch(BASE + "/api/curriculum")).json();
  return CURRICULUM_CACHE;
}
async function realmTaskIds(realmKey) {
  const cur = await getCurriculum();
  const realm = cur.realms.find((r) => r.key === realmKey);
  return realm ? realm.tasks : [];
}
async function closeAchievementPopup(page) {
  if (await page.isVisible("#modal-ach-pop")) {
    await page.click("#btn-ach-pop-close");
    await page.waitForFunction(() => document.querySelector("#modal-ach-pop").classList.contains("hidden"));
  }
}

async function submitSolution(taskId) {
  const task = await (await fetch(BASE + "/api/tasks/" + taskId)).json();
  const sub = await (await fetch(BASE + "/api/tasks/" + taskId + "/submit", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: task.solution }),
  })).json();
  if (!sub.outcome.passed) throw new Error("task failed: " + taskId);
  return sub;
}

// 根据秘境挑战的 starter_code 合成参考答案（仅用于 E2E 通关）
function solveSecretChallenge(starter) {
  if (/def calc\(/.test(starter)) {
    return "def calc(a, b):\n    return a * b";
  }
  const sumMatch = starter.match(/range\(1, (\d+) \+ 1\)/);
  if (sumMatch) {
    const n = Number(sumMatch[1]);
    return "count = 0\ntotal = 0\nfor i in range(1, " + n + " + 1):\n    if i % 3 == 0:\n        count += 1\n        total += i\nprint(count)\nprint(total)";
  }
  const wordMatch = starter.match(/w = "([^"]+)"/);
  if (wordMatch) {
    return "w = \"" + wordMatch[1] + "\"\nprint(w.upper(), len(w))";
  }
  if (/^lst = \[/m.test(starter)) {
    const line = starter.split("\n")[0];
    return line + "\nprint(min(lst))\nprint(max(lst))\nprint(sum(lst))";
  }
  return null;
}

async function closeIntroModal(page) {
  if (await page.isVisible("#modal-intro")) {
    await page.click("#btn-intro-go");
    await page.waitForFunction(() => document.querySelector("#modal-intro").classList.contains("hidden"));
  }
}

async function moveWorld(page, locationId, expectedName) {
  await page.click("[data-world-location='" + locationId + "']");
  await page.waitForFunction(
    (name) => document.querySelector("#world-current-location").textContent.includes(name),
    expectedName
  );
  await page.$eval("#modal-message", (el) => el.click());
  await page.waitForFunction(() => document.querySelector("#modal-message").classList.contains("hidden"));
}

async function main() {
  const server = spawn("python", ["run.py", "--no-browser", "--port", String(PORT)], {
    cwd: ROOT,
    stdio: "ignore",
    env: { ...process.env, CA_SAVE_DIR: path.join(ROOT, ".tools", "e2e_saves") },
  });
  await sleep(4000);
  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push("PAGEERROR: " + e.message));

  try {
    // 标题 → 创建角色
    await page.goto(BASE + "/", { waitUntil: "networkidle" });
    await page.waitForSelector("#screen-title:not(.hidden)");
    console.log("PASS title screen");

    await page.click("#btn-start-new");
    await page.fill("#input-name", "云中子");
    await page.click(".spirit-root[data-root='水']");
    await page.click("#btn-create-confirm");
    await page.waitForSelector("#screen-map:not(.hidden)");
    const realmText = await page.textContent("#map-player-realm");
    if (!realmText.includes("凡人")) throw new Error("realm not 凡人: " + realmText);
    console.log("PASS character creation -> map");
    // V0.2.5 入道启程弹窗：关闭以免遮挡地图卡片点击
    await closeIntroModal(page);

    // V0.3-A 世界地图：地点可见、相邻移动、返回洞府
    await page.waitForSelector("#world-map:not(.hidden)");
    const worldLocationCount = await page.$$eval(".world-location", (els) => els.length);
    if (worldLocationCount < 12) throw new Error("world locations missing: " + worldLocationCount);
    await page.click("[data-world-location='gate']");
    await page.waitForFunction(() => document.querySelector("#world-current-location").textContent.includes("山门"));
    await page.$eval("#modal-message", (el) => el.click());
    await page.waitForFunction(() => document.querySelector("#modal-message").classList.contains("hidden"));
    await page.click("[data-world-location='dormitory']");
    await page.waitForFunction(() => document.querySelector("#world-current-location").textContent.includes("洞府"));
    await page.$eval("#modal-message", (el) => el.click());
    await page.waitForFunction(() => document.querySelector("#modal-message").classList.contains("hidden"));
    console.log("PASS V0.3-A world map movement (" + worldLocationCount + " locations)");

    // Achievement board card: 0/16 at creation
    const achState0 = await page.textContent("#card-achievement-state");
    if (!achState0.includes("\u5df2\u8bc1 0 / 23")) throw new Error("ach board init wrong: " + achState0);
    console.log("PASS achievement board (0/23)");

    // V0.3-E 长期成长：贡献、图鉴、关系与自由目标
    await page.click("#btn-progression");
    await page.waitForSelector("#modal-progression:not(.hidden)");
    const techCodexStat = await page.textContent("#progression-tech-stat");
    const encounterCodexStat = await page.textContent("#progression-encounter-stat");
    const objectiveCount = await page.$$eval("#progression-objectives .progression-item", (els) => els.length);
    const relationCount = await page.$$eval("#progression-relations .progression-item", (els) => els.length);
    if (!techCodexStat.includes("1 / 13")) throw new Error("technique codex stat wrong: " + techCodexStat);
    if (!encounterCodexStat.includes("0 / 8")) throw new Error("encounter codex stat wrong: " + encounterCodexStat);
    if (objectiveCount < 5 || relationCount !== 4) throw new Error("progression panels incomplete");
    await page.click("#btn-progression-close");
    await page.waitForFunction(() => document.querySelector("#modal-progression").classList.contains("hidden"));
    console.log("PASS long-term progression dashboard");

    // V0.3-B：NPC 位于世界地点，不再使用固定横条
    for (const sel of ["#world-regions", "#btn-bag-map", "#btn-achievement-map"]) {
      await page.waitForSelector(sel);
    }
    const npcCount = await page.$$eval("#world-regions .npc-chip", (els) => els.length);
    if (npcCount < 4) throw new Error("NPC chips missing: " + npcCount);
    if (await page.$("#npc-list")) throw new Error("legacy NPC strip still exists");
    console.log("PASS V0.3-B NPCs bound to world locations (" + npcCount + " npcs)");

    // NPC 对话：青玄子 聆听教诲 → 悟性 +1
    await page.click(".npc-chip[data-npc='master_qingxuan']");
    await page.waitForSelector("#modal-dialogue:not(.hidden)");
    const dlgName = await page.textContent("#dlg-name");
    if (!dlgName.includes("青玄子")) throw new Error("dialogue npc wrong: " + dlgName);
    await page.click("#dlg-options .dlg-option:nth-child(2)");
    await page.waitForFunction(() => document.querySelector("#dlg-effects").textContent.includes("悟性"));
    await page.click("#btn-dlg-close");
    await page.waitForFunction(() => document.querySelector("#modal-dialogue").classList.contains("hidden"));
    const comp = await page.textContent("#map-comprehension");
    if (comp.trim() !== "11") throw new Error("comprehension not +1: " + comp);
    console.log("PASS NPC dialogue (comprehension 10 -> 11)");

    // 储物袋（初始为空）
    await page.click("#btn-bag-map");
    await page.waitForSelector("#modal-bag:not(.hidden)");
    const bagEmpty = await page.textContent("#bag-items");
    if (!bagEmpty.includes("空空")) throw new Error("bag should be empty");
    await page.click("#btn-bag-close");
    await page.waitForFunction(() => document.querySelector("#modal-bag").classList.contains("hidden"));
    console.log("PASS bag empty state");

    // 进入任务界面
    await page.click("[data-location-action='cultivate']");
    await page.waitForSelector("#screen-task:not(.hidden)");
    const taskTitle = await page.textContent("#task-title");
    const starter = await page.evaluate(() => App.editor.getValue());
    if (!starter.includes("print")) throw new Error("starter missing print");
    console.log("PASS task screen: " + taskTitle.trim());

    // 师尊指点：L1 方向提示 + 诊断
    await page.click("#btn-ask-master");
    await page.waitForFunction(() => document.querySelector("#master-advice").textContent.includes("方向"));
    const masterText = await page.textContent("#master-advice");
    if (!masterText.includes("L1")) throw new Error("master level missing: " + masterText);
    await page.click("#btn-ask-analyze");
    await page.waitForFunction(() => document.querySelector("#master-advice").textContent.includes("师尊诊断"));
    console.log("PASS master guidance + analyze");

    // 运行
    await page.click("#btn-run");
    await page.waitForFunction(() => document.querySelector("#run-status").textContent.includes("耗时"));
    const out1 = await page.textContent("#task-output");
    console.log("PASS run: " + JSON.stringify(out1.trim()));

    // 错误提交被拒绝
    await page.evaluate(() => App.editor.setValue("print('wrong')"));
    await page.click("#btn-submit");
    await page.waitForSelector("#task-result.fail");
    console.log("PASS wrong submit rejected");

    // 正确提交 + 突破
    await page.evaluate(() => App.editor.setValue('print("天地玄黄，宇宙洪荒。")'));
    await page.click("#btn-submit");
    await page.waitForSelector("#task-result.pass");
    // Achievement popup: first_awaken +10 cultivation
    await page.waitForSelector("#modal-ach-pop:not(.hidden)");
    const popName = await page.textContent("#ach-pop-name");
    if (!popName.includes("\u521d\u9192\u4e4b\u7f18")) throw new Error("ach popup name wrong: " + popName);
    const popReward = await page.textContent("#ach-pop-reward");
    if (!popReward.includes("\u4fee\u4e3a+10")) throw new Error("ach popup reward wrong: " + popReward);
    console.log("PASS achievement popup (first_awaken +10)");
    await page.click("#btn-ach-pop-close");
    await page.waitForFunction(() => document.querySelector("#modal-ach-pop").classList.contains("hidden"));
    await page.waitForSelector("#modal-breakthrough:not(.hidden)");
    await page.click("#btn-breakthrough");
    await page.waitForFunction(() => document.querySelector("#btn-breakthrough").dataset.step === "done");
    await closeAchievementPopup(page); // achievement popup may cover continue button
    await page.click("#btn-breakthrough");
    await page.waitForSelector("#screen-map:not(.hidden)");
    const realmAfter = await page.textContent("#map-player-realm");
    if (!realmAfter.includes("炼气一层")) throw new Error("breakthrough failed: " + realmAfter);
    console.log("PASS breakthrough -> " + realmAfter.trim());

    // V0.3-B：前往藏经阁，与所在地的玄机长老交谈并解锁支线
    await page.click("[data-world-location='library']");
    await page.waitForFunction(() => document.querySelector("#world-current-location").textContent.includes("藏经阁"));
    await page.$eval("#modal-message", (el) => el.click());
    await page.waitForFunction(() => document.querySelector("#modal-message").classList.contains("hidden"));
    await page.click("[data-location-action='library']");
    await page.waitForSelector("#screen-library:not(.hidden)");
    const techUnlocked = await page.$$eval("#technique-list .technique-item:not(.locked)", (els) => els.length);
    if (techUnlocked !== 2) throw new Error("technique unlock count != 2: " + techUnlocked);
    await page.click("#btn-library-back");
    await page.waitForSelector("#screen-map:not(.hidden)");
    const techTotal = await page.$$eval("#technique-list .technique-item", (els) => els.length);
    console.log("PASS library location action (2/" + techTotal + " unlocked)");
    await page.click(".npc-chip[data-npc='elder_library']");
    await page.waitForSelector("#modal-dialogue:not(.hidden)");
    await page.click("#dlg-options .dlg-option:nth-child(1)");
    await page.waitForFunction(() => document.querySelector("#dlg-effects").textContent.includes("支线"));
    await page.click("#btn-dlg-close");
    await page.waitForFunction(() => document.querySelector("#modal-dialogue").classList.contains("hidden"));
    console.log("PASS NPC location interaction + branch unlock");

    // V0.3-C：沿功法树前往演武场，以真实代码修炼并考核至小成
    await moveWorld(page, "mission_hall", "任务堂");
    await moveWorld(page, "training_ground", "演武场");
    await page.click("[data-open-training]");
    await page.waitForSelector("#modal-training:not(.hidden)");
    await page.click("[data-practice-tech='mortal']");
    await page.fill("#training-code", 'print("Hello, World!")');
    await page.click("#btn-training-submit");
    await page.waitForFunction(() => {
      const button = document.querySelector("[data-practice-tech='mortal']");
      return button && button.closest(".training-technique").textContent.includes("50/100");
    });
    await page.click("#btn-training-submit");
    await page.waitForFunction(() => {
      const button = document.querySelector("[data-practice-tech='mortal']");
      return button && button.closest(".training-technique").textContent.includes("80/100");
    });
    await page.click("[data-exam-tech='mortal']");
    await page.waitForFunction(() => document.querySelector("#btn-training-submit").textContent.includes("提交考核"));
    await page.fill("#training-code", 'print("Hello, World!")');
    await page.click("#btn-training-submit");
    await page.waitForFunction(() => {
      const button = document.querySelector("[data-practice-tech='mortal']");
      return button && button.closest(".training-technique").textContent.includes("小成");
    });
    const mortalCard = await page.$eval("[data-practice-tech='mortal']", (el) => el.closest(".training-technique").textContent);
    if (!mortalCard.includes("小成")) throw new Error("technique exam did not reach 小成: " + mortalCard);
    await page.click("#btn-training-close");
    await moveWorld(page, "cauldron", "炼丹房");
    await moveWorld(page, "dormitory", "洞府");
    console.log("PASS technique practice + code exam -> 小成");

    // 藏经阁渲染
    await page.click("[data-location-action='cultivate']");
    await page.waitForSelector("#screen-task:not(.hidden)");
    const teachingLen = await page.evaluate(() => document.querySelector("#task-teaching").textContent.length);
    if (teachingLen < 20) throw new Error("teaching not rendered");
    console.log("PASS teaching rendered (len=" + teachingLen + ")");

    // API 快进：全部主线（按当前任务动态推进）
    let guard = 0;
    while (guard++ < 60) {
      const st = await (await fetch(BASE + "/api/state")).json();
      const p = st.player;
      if (p.founded) break;
      if (st.current_task) {
        await submitSolution(st.current_task.id);
        continue;
      }
      if (p.pending_breakthrough) {
        if (st.tribulation.unlocked) break;
        const br = await (await fetch(BASE + "/api/breakthrough", { method: "POST" })).json();
        if (!br.event) throw new Error("breakthrough failed at " + p.realm_key);
        continue;
      }
      throw new Error("stuck at realm " + p.realm_key);
    }
    let stCheck = await (await fetch(BASE + "/api/state")).json();
    if (!stCheck.tribulation.unlocked) throw new Error("qi10 not reached");
    console.log("PASS API fast-forward through qi10");

    // 刷新页面，从存档继续（此时已到 qi10，debug/渡劫台已解锁）
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForSelector("#screen-title:not(.hidden)");
    await page.click("#btn-continue");
    await page.waitForSelector("#screen-map:not(.hidden)");
    const q10Realm = await page.textContent("#map-player-realm");
    if (!q10Realm.includes("炼气大圆满")) throw new Error("not at qi10: " + q10Realm);
    console.log("PASS continue at qi10");

    // 秘境：引路人解锁青云秘境 → 面板 → 进入 → 通关
    await moveWorld(page, "gate", "山门");
    await moveWorld(page, "mountain_path", "后山山道");
    await moveWorld(page, "encounter_site", "奇遇点");
    await page.click("[data-trigger-encounter]");
    await page.waitForSelector("#modal-story:not(.hidden)");
    const encounterTitle = await page.textContent("#story-title");
    if (!encounterTitle.trim()) throw new Error("encounter challenge missing");
    await page.click("#btn-story-close");
    await page.waitForFunction(() => document.querySelector("#modal-story").classList.contains("hidden"));
    console.log("PASS random encounter triggered: " + encounterTitle.trim());
    await moveWorld(page, "secret_gate", "秘境入口");
    await page.click(".npc-chip[data-npc='guide_realm']");
    await page.waitForSelector("#modal-dialogue:not(.hidden)");
    await page.click("#dlg-options .dlg-option:nth-child(1)");
    await page.waitForFunction(() => document.querySelector("#dlg-effects").textContent.includes("\u7f57\u76d8"));
    await page.click("#btn-dlg-close");
    await page.waitForFunction(() => document.querySelector("#modal-dialogue").classList.contains("hidden"));
    await page.click("[data-location-action='secret']");
    await page.waitForSelector("#screen-secret:not(.hidden)");
    const secretCardCount = await page.$$eval("#secret-realm-list .secret-realm-card", (els) => els.length);
    if (secretCardCount !== 3) throw new Error("secret realm cards != 3: " + secretCardCount);
    const enterableCount = await page.$$eval("#secret-realm-list .secret-realm-card:not(.locked)", (els) => els.length);
    if (enterableCount !== 1) throw new Error("enterable secret != 1: " + enterableCount);
    console.log("PASS secret realm board (1/3 enterable)");
    await page.click("#secret-realm-list .secret-realm-card:not(.locked) [data-enter]");
    await page.waitForSelector("#screen-task:not(.hidden)");
    const secretTag = await page.textContent("#task-mode-tag");
    if (!secretTag.includes("\u79d8\u5883")) throw new Error("secret tag wrong: " + secretTag);
    console.log("PASS enter qingyun (tag=" + secretTag.trim() + ")");
    const secretStarter = await page.evaluate(() => App.editor.getValue());
    const secretSolution = solveSecretChallenge(secretStarter);
    if (!secretSolution) throw new Error("cannot synthesize secret solution");
    await page.evaluate((code) => App.editor.setValue(code), secretSolution);
    await page.click("#btn-run");
    await page.waitForFunction(() => document.querySelector("#run-status").textContent.includes("\u8017\u65f6"));
    await page.click("#btn-submit");
    // 通关后自动返回洞府，任务结果可能已隐藏；以消息弹窗（成功）或失败态为准
    await page.waitForFunction(() => {
      const mr = document.querySelector("#modal-message");
      if (mr && !mr.classList.contains("hidden")) return true;
      const tr = document.querySelector("#task-result");
      return tr && tr.classList.contains("fail");
    });
    const secretFailed = await page.evaluate(() => document.querySelector("#task-result").classList.contains("fail"));
    if (secretFailed) throw new Error("secret submit failed");
    // 消息弹窗在 DOM 中位于成就弹窗之后（顶层），先关消息再关成就
    await page.waitForFunction(() => document.querySelector("#modal-message:not(.hidden)"));
    const secretMsg = await page.textContent("#modal-message-text");
    if (!secretMsg.includes("\u79d8\u5883")) throw new Error("secret clear message wrong: " + secretMsg);
    console.log("PASS qingyun secret clear: " + secretMsg.trim());
    await page.click("#btn-modal-close");
    await page.waitForFunction(() => document.querySelector("#modal-message").classList.contains("hidden"));
    await closeAchievementPopup(page);
    await page.waitForSelector("#screen-map:not(.hidden)");
    const secretState = await page.textContent("#card-secret-state");
    if (!secretState.includes("\u5df2\u901a 1")) throw new Error("secret cleared state wrong: " + secretState);
    console.log("PASS secret cleared state: " + secretState.trim());

    // 炼丹房界面（此时 debug 任务尚未完成）
    await moveWorld(page, "mountain_path", "后山山道");
    await moveWorld(page, "gate", "山门");
    await moveWorld(page, "dormitory", "洞府");
    await moveWorld(page, "cauldron", "炼丹房");
    await page.click("[data-location-action='debug']");
    await page.waitForSelector("#screen-task:not(.hidden)");
    const debugTag = await page.textContent("#task-mode-tag");
    if (!debugTag.includes("心魔")) throw new Error("debug tag wrong: " + debugTag);
    console.log("PASS debug room task screen");
    await page.click("#btn-task-back");
    await page.waitForSelector("#screen-map:not(.hidden)");

    // 渡劫台界面（未渡劫）
    await moveWorld(page, "trial_platform", "渡劫台");
    await page.click("[data-location-action='tribulation']");
    await page.waitForSelector("#screen-tribulation:not(.hidden)");
    const waveCount0 = await page.evaluate(() => document.querySelectorAll(".wave-card").length);
    if (waveCount0 !== 3) throw new Error("wave cards != 3");
    const currentWave = await page.evaluate(() => document.querySelector(".wave-state.current").textContent);
    if (!currentWave.includes("迎劫")) throw new Error("no current wave");
    console.log("PASS tribulation screen (3 waves, first active)");
    await page.click("#btn-tribulation-back");
    await page.waitForSelector("#screen-map:not(.hidden)");

    // debug + 渡劫（API 完成）
    let st = await (await fetch(BASE + "/api/state")).json();
    for (const d of st.debug_tasks) await submitSolution(d.id);
    st = await (await fetch(BASE + "/api/state")).json();
    for (const w of st.tribulation.waves) await submitSolution(w.task_id);
    const br = await (await fetch(BASE + "/api/breakthrough", { method: "POST" })).json();
    if (!br.event || !br.event.founded) throw new Error("final breakthrough failed");
    console.log("PASS API full completion + foundation");

    // 刷新页面：继续游戏
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForSelector("#screen-title:not(.hidden)");
    await page.click("#btn-continue");
    await page.waitForSelector("#screen-map:not(.hidden)");
    const finalRealm = await page.textContent("#map-player-realm");
    console.log("PASS continue from save: realm=" + finalRealm.trim());
    const restoredV03 = await page.evaluate(async () => (await fetch("/api/state")).json());
    if ((restoredV03.player.npc_affinity.master_qingxuan || 0) < 5) throw new Error("NPC affinity not restored");
    if (restoredV03.player.technique_level.mortal !== 2) throw new Error("technique level not restored");
    if (!restoredV03.story.active_encounter) throw new Error("active encounter not restored");
    console.log("PASS V0.3 save restore (location/affinity/technique/encounter)");
    // Achievement board after completion: several unlocked + title check
    const titleAfter = await page.textContent("#map-player-title");
    if (!titleAfter.includes("\u7b51\u57fa\u771f\u4eba")) throw new Error("title missing: " + titleAfter);
    console.log("PASS title " + titleAfter.trim());
    await page.click("#btn-achievement-map");
    await page.waitForSelector("#modal-achievement:not(.hidden)");
    const unlockedCount = await page.evaluate(() => document.querySelectorAll("#achievement-list .achievement-item:not(.locked)").length);
    if (unlockedCount < 5) throw new Error("unlocked achievements too few: " + unlockedCount);
    console.log("PASS achievement board after completion (" + unlockedCount + " unlocked)");
    await page.click("#btn-achievement-close");
    await page.waitForFunction(() => document.querySelector("#modal-achievement").classList.contains("hidden"));

    // 道基巩固（筑基期任务）→ 突破金丹
    await moveWorld(page, "cauldron", "炼丹房");
    await moveWorld(page, "dormitory", "洞府");
    await page.click("[data-location-action='cultivate']");
    await page.waitForSelector("#screen-task:not(.hidden)");
    const foundationTitle = await page.textContent("#task-title");
    if (!foundationTitle.includes("道基巩固")) throw new Error("foundation task wrong: " + foundationTitle);
    console.log("PASS foundation task: " + foundationTitle.trim());
    await page.click("#btn-task-back");
    await page.waitForSelector("#screen-map:not(.hidden)");
    let st2 = await (await fetch(BASE + "/api/state")).json();
    await submitSolution(st2.current_task.id);
    const br2 = await (await fetch(BASE + "/api/breakthrough", { method: "POST" })).json();
    if (!br2.event || br2.event.to !== "gold1") throw new Error("foundation->gold1 breakthrough failed");
    console.log("PASS breakthrough foundation -> 金丹");
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForSelector("#screen-title:not(.hidden)");
    await page.click("#btn-continue");
    await page.waitForSelector("#screen-map:not(.hidden)");
    const goldRealm = await page.textContent("#map-player-realm");
    if (!goldRealm.includes("金丹")) throw new Error("not at 金丹: " + goldRealm);
    console.log("PASS continue at " + goldRealm.trim());
    await page.click("[data-location-action='cultivate']");
    await page.waitForSelector("#screen-task:not(.hidden)");
    const goldTitle = await page.textContent("#task-title");
    if (!goldTitle.includes("净字诀")) throw new Error("gold task wrong: " + goldTitle);
    console.log("PASS golden core task: " + goldTitle.trim());
    await page.click("#btn-task-back");
    await page.waitForSelector("#screen-map:not(.hidden)");

    if (consoleErrors.length) {
      console.log("CONSOLE ERRORS:", consoleErrors);
      throw new Error("console errors present");
    }
    console.log("ALL E2E CHECKS PASSED");
  } finally {
    await browser.close();
    server.kill();
  }
}

main().catch((e) => {
  console.error("E2E FAILED:", e.message);
  process.exit(1);
});
