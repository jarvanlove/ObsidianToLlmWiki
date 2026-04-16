# 私有库 AGENTS 模板

这个文件放在 `ObsidianToWiki-private` 根目录。

它的作用很简单：告诉 Codex 这里是你的真实知识库。

```yaml
vault_root: <private-vault-root>
scaffold_root: <public-scaffold-root>
current_project:
default_project_index: 20_projects/索引.md
default_personal_index: 10_personal/索引.md
default_shared_index: 30_shared/索引.md
default_output_index: 40_outputs/索引.md
```

## 规则

- 把这个私有库当作个人和项目知识的真实存储层
- 改结构前先读 `README-zh.md` 和 `使用手册.md`
- 写内容前先看 `index.md` 和相关项目 `索引.md`
- 原始资料保持在 `01_inbox/raw/` 中不直接改写
- 可复用内容提升到 `30_shared/`
