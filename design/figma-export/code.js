// Read-only export through the editor's Plugin API. No REST calls or tokens.
let busy = false;

function selectionInfo() {
  figma.ui.postMessage({ type: "selection", names: figma.currentPage.selection.map(n => n.name) });
}
figma.on("selectionchange", selectionInfo);

function fileName(node) {
  return (node.name.replace(/[<>:"/\\|?*\x00-\x1f]/g, "_").slice(0, 80) || "frame") + "_" + node.id.replace(/:/g, "-");
}

figma.ui.onmessage = async function (message) {
  if (message.type === "ready") { selectionInfo(); return; }
  if (message.type !== "export" || busy) return;
  const nodes = Array.from(figma.currentPage.selection);
  if (!nodes.length) {
    figma.ui.postMessage({ type: "done", errors: ["Сначала выдели фрейм макета в списке слоёв слева."] });
    return;
  }
  busy = true;
  const errors = [];
  try {
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      const name = fileName(node);
      figma.ui.postMessage({ type: "progress", text: (i + 1) + "/" + nodes.length + ": " + node.name });
      // Each format is independent: a large PNG failure must not lose the JSON.
      for (const format of ["JSON_REST_V1", "PNG"].concat(message.svg ? ["SVG_STRING"] : [])) {
        try {
          const settings = format === "PNG" ? { format: "PNG", constraint: { type: "SCALE", value: 1 } } : { format: format };
          const result = await node.exportAsync(settings);
          const isJSON = format === "JSON_REST_V1";
          const extension = isJSON ? "json" : format === "PNG" ? "png" : "svg";
          const data = isJSON ? JSON.stringify({
            exportVersion: 1,
            exportedAt: new Date().toISOString(),
            fileName: figma.root.name,
            pageName: figma.currentPage.name,
            nodeId: node.id,
            nodeName: node.name,
            data: result
          }, null, 2) : result;
          figma.ui.postMessage({ type: "file", name: name + "." + extension, data: data,
            mime: isJSON ? "application/json" : format === "PNG" ? "image/png" : "image/svg+xml" });
        } catch (error) {
          errors.push(node.name + " / " + format + ": " + String(error.message || error));
        }
      }
    }
  } finally {
    busy = false;
    figma.ui.postMessage({ type: "done", errors: errors });
  }
};

figma.showUI(__html__, { width: 440, height: 520 });
selectionInfo();
