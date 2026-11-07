# 四 Agent 工作流操作说明

[根目录README](../README.md)是强制流程唯一权威，本文件不重复定义门槛。当前版本1.1，机器阈值见[workflow-contract.json](workflow-contract.json)。主控不得以本文件旧内容替代README。

## 启动与依赖

1. 读取README、最新审美反馈、初始研究材料、全部历史候选，建立本轮历史去重索引。
2. 为Agent 1、2、3、4建立四个独立执行实例；允许顺序启动。记录真实agent_id和execution_ref。主控另记ID。
3. H1内先验收Agent 2搜索计划（search-plan.json/.md及plan-review.json）；计划须逐方向连接具体A1案例、机制、问题、检索路径和取舍。计划通过不自动授权下一阶段。随后按H1至H7交接。每个交付文件含来源、实际阅读范围和真实状态，主控复核后写验收回执。文件被修改后相关哈希与验收回执须重做。
4. 零幸存不跳Agent 4，实际调用后提交零输入判断和英文复查回执。不能把未调用标为完成。

## 每轮文件

目录为research/runs/<run_id>/，至少保存：run.json、cases.json、materials.json、candidates.json、quality.json、screening.json、english.json、handoffs.json、final.json、rejections.json与README.md。

- run.json：protocol_version、run_id、status、coordinator_id、roles（A1至A4），角色包含agent_id、execution_ref、started_at、completed_at和status；完成角色的status为completed。状态为in_progress、incomplete、complete_with_candidates或complete_without_candidates。
- handoffs.json：handoffs数组。每项含id（H1至H7）、status、from、to、timestamp、reason、candidate_ids、input_refs、output_refs；每个ref含path和sha256。路径均为本轮目录内的相对路径；推荐引用不可变的阶段版本，禁止引用handoffs.json自身，以免自引用哈希。
- quality.json：reviews数组。每个评审含candidate_id、language（zh/en）、reviewer（producer/coordinator）、scores与notes；轴名以契约为准。每个notes轴含reason和counter_association；同时记录对方分数未见时已独立提交的执行引用。评审还含name（该次评审的实际中/英文写法）、execution_ref和independent_submission_ref；每个候选每语言每评审版本有一个有效最新评审，旧版本另存返工记录。
- screening.json：chinese、english两个数组；每项含candidate_id、status、queries与registry_checks。queries每项含query、executed_at、result_summary及evidence；有占用命中时evidence含entity_name、match_type、url和access。登记查询逐入口写status，不能以首页访问替代逐名查询。
- final.json：candidates数组，只有最终通过的候选，每项含id、family_id、chinese、english及source_ids。中文储备另列，不放这个数组。
- rejections.json：entries数组，逐名记录candidate_id、name、language、stage、reason_code、reason和evidence；明确占用条目evidence必须含entity_name、match_type、url、checked_at和access。

候选名和家族的起源见candidates.json：candidates数组每项至少含id、name、family_id、material_ids、principle_ids、meaning、combination_reason、weakness和history_check（status与reason）。素材来源见materials.json的materials数组；每项含id、family_id、category、reading_scope、source_urls、fact与is_classical。案例研究cases.json需含cases、principles和counterexamples。英文english.json含entries数组，每项关联candidate_id并记录name与status，包含所有生成但落选的版本。

## 验收与失败

完整轮次须满足所有角色完成、H1至H7回执齐全、文件引用与哈希有效、双语门槛、独立查重、家族去重及逐名淘汰记录。进行中轮次允许阶段缺项，但必须保留真实进行中状态；不能列最终通过名。

JSON校验只是形式核对。真实执行、来源支持、独立评审和审美由主控审核。2026-11-06与2026-11-06-round2是明确的历史例外，仅作数据一致性校验，不改成1.0合规轮次。

模板和验收格式变更必须同步README与契约并获得用户批准。参考现有历史数据时不能照搬它缺失回执的结构用于新轮次。

## 机器字段约定

案例cases每项含id、category（broad_tech/current_ai/rsi_labs）、name、word_origin_fact、naming_analysis、reading_scope和sources；每个source含url、access（body表示已读正文）及supports。principles每项含id、positive_example、counterexample、boundary，counterexamples数组独立列至少3条。每个案例至少一个已读正文来源。

素材source_type为book/news/other；reading_scope为full_text/chapter/excerpt/abstract/snippet，reading_location注明读到哪里。书籍用book_id区分；新闻用published_at记录实际发表日期。计入阅读数量的只能是full_text/chapter/excerpt且有reading_location；不把摘要计作正文。

查询记录含kind，其枚举见契约。占用命中evidence逐条含entity_name、match_type、url、access；未命中仍含实际查询词、执行时间和结果摘要。筛查status通过值为pass_public_precheck，其余为reject_exact_use、hold_near_match、hold_unverified或not_screened_editorial。阳性对照positive_controls每项含entity_type（company/product）、detected:true及来源url。

最终候选的中文筛查记录须有CN/company、CN/trademark_9、CN/trademark_42及至少一个境外company登记尝试；每项含region、type、status、url、attempted_at、detail。最终候选中不允许这些项目仍为not_checked；入口失效用unavailable并披露。英文复查独立记录自己的queries。此要求是尝试与披露，不是保证注册可用。

run.json还含date、research_mode（bootstrap/continuation）；首个1.0轮次默认bootstrap，只有实际读取过已验收案例基线时才能用continuation，须在交接回执中引用该基线。handoffs.json每项from/to以A1/A2/A3/A4/coordinator/user标识角色。

rework.json为可选返工日志，entries每项含candidate_id、language、attempt（1或2）、reason、responsible_role及前后版本引用；有返工就必填，次数不可静默重置。将最终仍无合格英文的中文归储备时，去留记录用NO_ENGLISH_PAIR，不计完整候选。

交接output_refs至少覆盖契约handoff_output_files规定的角色交付文件名；允许放在本轮不可变阶段子目录中。H3至H6的candidate_ids必须与实际进入筛查/通过上游的人口一致，不能用空回执跳过实际幸存者。

## 1.1研究链条补充

依README“二之一”执行搜索计划→6–8张素材小批审阅→扩批→中文创作。计划-only任务不创建虚假素材或候选；run.json标incomplete并明确用户审阅节点。search-plan的入口在实际阅读前标planned_not_read。主控逐方向写accept/return及理由，记录整体状态；只有方向覆盖、案例与机制推理都成立才能验收，不以字段填满代替质量。

新完整轮次的1.1机器检查增加计划文件、六方向覆盖、案例ID引用、主控验收状态，以及材料/候选研究谱系字段。机器不判断推理好坏；主控仍逐项审读。旧1.0产物按原版本读取，不补造新要求下的执行。

## 持续积累与统一入口（2026年11月7日用户授权）

调度与总库政策见根README第六节：取消每天20及到数停止。沿用同一个聊天自动任务，每小时接续`research/continuation-queue.json`，不重复启动已运行的四Agent。总库位于`research/catalog/README.md`，分类使用105组案例六个来源世界；不同英文版本关联同一中文，不增加创意家族数。

本项只改变调度、发布方式与总库组织，不降低研究规模、审美评分、使用查重、角色交接或返工标准，也不追认历史轮次为生产协议全合规。新研究未通过之前只写队列和真实状态，不加入讨论备选。
