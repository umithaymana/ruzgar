const vscode = require("vscode");

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const root = vscode.workspace.workspaceFolders?.[0]?.uri;
  if (!root) {
    return;
  }

  const provider = new UmitMenuProvider(root);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("umit-asistan.actions", provider)
  );

  const reveal = async (relativePath) => {
    await vscode.commands.executeCommand("workbench.view.explorer");
    const target = vscode.Uri.joinPath(root, ...relativePath.split("/"));
    try {
      await vscode.commands.executeCommand("revealInExplorer", target);
    } catch {
      vscode.window.showWarningMessage(
        `Klasör bulunamadı: ${relativePath}`
      );
    }
  };

  const cmds = [
    ["umit-asistan.dosya", () => vscode.commands.executeCommand("workbench.view.explorer")],
    ["umit-asistan.duzen", () => vscode.commands.executeCommand("workbench.action.showCommands")],
    ["umit-asistan.uretim", () => reveal("ilim-assistant")],
    ["umit-asistan.gelisim", () => reveal("ilim-mobile")],
    ["umit-asistan.ses", () => reveal("ilim-voice")],
    ["umit-asistan.okuma", () => reveal("ilim-assistant/knowledge")],
    ["umit-asistan.video", () => reveal("ilim-video")],
    ["umit-asistan.programlama", () => reveal("ilim-assistant")],
  ];

  for (const [id, fn] of cmds) {
    context.subscriptions.push(vscode.commands.registerCommand(id, fn));
  }
}

class UmitMenuProvider {
  /**
   * @param {vscode.Uri} root
   */
  constructor(root) {
    this.root = root;
    /** @type {{ label: string, cmd: string }[]} */
    this.rows = [
      { label: "dosya", cmd: "umit-asistan.dosya" },
      { label: "düzen", cmd: "umit-asistan.duzen" },
      { label: "üretim", cmd: "umit-asistan.uretim" },
      { label: "gelişim", cmd: "umit-asistan.gelisim" },
      { label: "ses", cmd: "umit-asistan.ses" },
      { label: "okuma", cmd: "umit-asistan.okuma" },
      { label: "video", cmd: "umit-asistan.video" },
      { label: "programlama", cmd: "umit-asistan.programlama" },
    ];
  }

  /**
   * @param {vscode.TreeItem} element
   */
  getTreeItem(element) {
    return element;
  }

  getChildren() {
    return this.rows.map((r) => {
      const item = new vscode.TreeItem(r.label, vscode.TreeItemCollapsibleState.None);
      item.command = {
        command: r.cmd,
        title: r.label,
      };
      return item;
    });
  }
}

function deactivate() {}

module.exports = { activate, deactivate };
