/* 迷你 Markdown 渲染器（用于藏经阁教学内容） */
function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineBold(text) {
  return escapeHtml(text).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdown(text) {
  if (!text) return "";
  const lines = String(text).replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let inCode = false;
  let codeLang = "";
  let codeBuf = [];
  let listBuf = [];

  const flushList = () => {
    if (listBuf.length) {
      html.push("<ul><li>" + listBuf.join("</li><li>") + "</li></ul>");
      listBuf = [];
    }
  };
  const flushCode = () => {
    if (inCode) {
      html.push("<pre>" + escapeHtml(codeBuf.join("\n")) + "</pre>");
      codeBuf = [];
      inCode = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine;
    if (line.trim().startsWith("```")) {
      flushList();
      if (inCode) {
        flushCode();
      } else {
        codeLang = line.trim().slice(3).trim();
        inCode = true;
        codeBuf = [];
      }
      continue;
    }
    if (inCode) {
      codeBuf.push(line);
      continue;
    }
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    if (bullet) {
      listBuf.push(inlineBold(bullet[1]));
      continue;
    }
    flushList();
    if (line.trim() === "") {
      continue;
    }
    html.push("<p>" + inlineBold(line) + "</p>");
  }
  flushList();
  flushCode();
  return html.join("\n");
}
