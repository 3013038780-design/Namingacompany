# 命名研究台

固定网站的界面源文件。纯文字排版，中文名字用楷体字体栈，英文用 Times New Roman；搜索、六方向筛选、名字详情、每日记录和研究去留分别展示。

网站数据来自 `research/catalog/website.json`，由 `python3 scripts/build_site_feed.py` 生成。只把正式总库条目放进名字库；草案、未核实和否决项在研究页及每日记录中展示，不提升为推荐。数据在公开仓库更新后，网站打开时读取最新版，每60秒再检查一次；不能连接时明确显示随发布保存的快照。

日常研究只更新数据文件，不需要重复部署界面或建立第二个定时任务。每次实质工作段完成后，先保存真实结果/冻结决策及队列，再重建总库和网站数据，随现有PR推送。已有每小时任务负责研究与上游数据更新；电脑/应用不可用时该任务也不能运行。

部署身份见 `research/site.json`，独立Sites源目录 `/Users/olivialee/Documents/ChatGPT/临时项目/naming-research-site`。界面修改后将本目录三个文件复制到该Site的 `dist/`，将最新 `website.json` 复制为 `dist/data.json` 作为离线快照；依Sites工作流保存并发布。保持原project_id和访问范围。不得把源凭证或外部全文放进仓库。
