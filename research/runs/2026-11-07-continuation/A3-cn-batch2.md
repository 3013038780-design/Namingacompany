# A3-cn-batch2：实际查重结果

实际候选查询 22 组，阳性对照另见 A3-controls.json，不计入候选。

| ID | 名称 | 结果 | 依据 |
|---|---|---|---|
| CT-C05 | 拨码 | public_use_screen_pass | 未见完整中文拨码作为同名科技/AI公司、模型或软件品牌；大量拨码开关通用术语。拼音Boma已有AI技术使用线索，不能直接选作英文，中文需另配。 |
| CT-C07 | 念头引擎 | public_use_screen_pass | 未见完整同名公司、模型或软件品牌；检到念头池/引擎组合描述的心潮开源项目，名称不同。 |
| CT-C08 | 多想一步 | public_use_screen_pass | 未见完整同名公司、模型或软件品牌。科技公司宣传、文章和App介绍中的普通短语不自动视为品牌。 |

逐名实际查询、正文阅读范围、来源与登记入口限制见同名JSON。大陆公司及第9/42类入口403；英国逐名URL不可访问，均未取得登记查询结果。

## CT-C05 拨码

- [primary_body_read](https://www.biwin.com/webls-zh-tw/index.html)：百瑩科技、SAB SWITCHES为主体/品牌，撥碼型只是开关产品分类，不叫拨码公司。
- [search_text_open_timeout](https://www.bomalabs.ai/about)：检索显示Boma/Yeah Innovations AI工作流基础设施，正文打开超时；不声称已读官网全文或核验登记。
- [search_text_open_404](https://pypi.org/project/boma/)：检索显示Boma Python SDK building AI agents/workflows；打开404，只保留索引线索。

## CT-C07 念头引擎

- [primary_body_read](https://github.com/tianyupaipai-cmd/xinchao-dynamic-mind)：About为AI动态心智状态引擎，提及念头池；仓库名心潮/xinchao-dynamic-mind，非念头引擎。

## CT-C08 多想一步

- [search_text_open_no_readable_body](https://www.gferp.com/)：检索主体金友伟业，宣传一起多想一步，不是公司或产品全名。
- [primary_government_body_read](https://keid.nat.gov.tw/branding-taiwan/Case/more1?id=2025c3b01093446f8eba60d0a77b0e5c)：主体研揚科技；搜索返回为客戶多想一步，打开正文确认为研揚科技品牌案例，不是该短语命名。
- [primary_product_body_read](https://askfish.app/zh)：实际App名钓问/AskFish；多想一步为宣传短语，不同名品牌。
