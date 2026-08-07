/* 后端 API 封装 */
async function api(path, options = {}) {
  const opts = {
    headers: { "Content-Type": "application/json" },
    ...options,
  };
  const resp = await fetch(path, opts);
  let data = {};
  try {
    data = await resp.json();
  } catch (e) {
    /* 空响应 */
  }
  if (!resp.ok) {
    const err = new Error(data.error || ("请求失败（" + resp.status + "）"));
    err.status = resp.status;
    throw err;
  }
  return data;
}

async function apiGet(path) {
  return api(path);
}

async function apiPost(path, body) {
  return api(path, { method: "POST", body: JSON.stringify(body || {}) });
}
