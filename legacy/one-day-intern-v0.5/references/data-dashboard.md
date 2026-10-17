# E02 数据看板

## 目的

把业务数据作为正式、可回看的飞书看板交付给玩家。群聊不复述 KPI，不用三条消息刷数字；只发送一个看板链接和一个问题卡提示。

## 固定内容

工作簿标题：`青橙视频 · 短视频发布体验数据看板 · <run_id后六位>`。

只创建一个子表 `数据看板`，包含以下三行。百分比必须以数值写入，不得写成字符串：

| 指标 | 当前值 | 数据口径 | 产品提示 |
|---|---:|---|---|
| 进入发布页后24小时未发布率 | 0.41 | 新手创作者进入发布页后的24小时观察 | 越低越好 |
| 设置选择困难反馈占比 | 0.47 | 放弃发布反馈中提到封面、标题、话题或可见范围的占比 | 反馈信号，不代表单一原因 |
| 发布后5分钟删除或重编率 | 0.18 | 新手创作者已发布视频的5分钟观察 | 越低越好 |

看板底部或说明区必须注明：`本看板使用虚构训练数据；三个指标的分母不同，只能用于发现问题信号，不能直接证明因果。`

## 视觉规格

- 使用年轻、清爽但可读的橙色主题：主色 `#FF6B35`，浅底色 `#FFF3EC`，正文 `#1F2937`。
- 表头白字、主色背景、加粗并冻结首行。
- `当前值` 使用真实百分比格式 `0%`，加粗、居中、浅橙底；不要手工写 `%` 字符。
- `数据口径` 列开启自动换行；列宽至少 300 px。
- 创建一张原生横向条形图，标题为 `短视频发布关键问题信号`，数据源为 `数据看板!A1:B4`。不得用本地图片代替原生图表。
- 图表比较的是三个问题信号，不得把它命名为“发布漏斗”或暗示三个比例拥有同一分母。

## 创建协议

首次调用前完整读取 `lark-sheets` 与 `lark-shared`。使用 user 身份创建，确保玩家天然可访问。标题包含 `run_id` 后六位，作为恢复查重标记。

先以 typed 数据和样式一步创建工作簿：

```bash
lark-cli sheets +workbook-create --as user \
  --title "青橙视频 · 短视频发布体验数据看板 · <run_suffix>" \
  --sheets '{"sheets":[{"name":"数据看板","columns":["指标","当前值","数据口径","产品提示"],"data":[["进入发布页后24小时未发布率",0.41,"新手创作者进入发布页后的24小时观察","越低越好"],["设置选择困难反馈占比",0.47,"放弃发布反馈中提到封面、标题、话题或可见范围的占比","反馈信号，不代表单一原因"],["发布后5分钟删除或重编率",0.18,"新手创作者已发布视频的5分钟观察","越低越好"],["说明",null,"本看板使用虚构训练数据；三个指标的分母不同，只能用于发现问题信号，不能直接证明因果。",""]],"dtypes":{"指标":"object","当前值":"float64","数据口径":"object","产品提示":"object"},"formats":{"当前值":"0%"}}]}' \
  --styles '{"styles":[{"name":"数据看板","cell_styles":[{"range":"A1:D1","background_color":"#FF6B35","font_color":"#FFFFFF","font_weight":"bold","horizontal_alignment":"center","vertical_alignment":"middle"},{"range":"A2:D4","font_color":"#1F2937","border":{"style":"solid","weight":"thin","color":"#E5E7EB"},"vertical_alignment":"middle"},{"range":"B2:B4","background_color":"#FFF3EC","font_color":"#D94A16","font_weight":"bold","font_size":16,"horizontal_alignment":"center","number_format":"0%"},{"range":"C2:C5","word_wrap":"auto-wrap"},{"range":"A5:D5","background_color":"#FFF8F4","font_color":"#6B7280","font_style":"italic"}],"row_sizes":[{"range":"1:1","type":"pixel","size":36},{"range":"2:5","type":"auto"}],"col_sizes":[{"range":"A:A","type":"pixel","size":220},{"range":"B:B","type":"pixel","size":110},{"range":"C:C","type":"pixel","size":360},{"range":"D:D","type":"pixel","size":180}],"freeze":{"rows":1}}]}' \
  --json
```

保存返回的 spreadsheet token 与 URL，再用 `+workbook-info --as user` 获取真实 `sheet_id`。不要猜默认 sheet 名或 ID。

创建原生图表：

```bash
lark-cli sheets +chart-create --as user \
  --url "<spreadsheet_url>" --sheet-id "<sheet_id>" \
  --properties - --json <<'JSON'
{"position":{"row":1,"col":"F"},"size":{"width":680,"height":380},"snapshot":{"title":{"text":"短视频发布关键问题信号"},"plotArea":{"plot":{"type":"bar"}},"data":{"refs":[{"value":"'数据看板'!A1:B4"}],"dim1":{"serie":{"index":1}},"dim2":{"series":[{"index":2}]}}}}
JSON
```

## 回读验证

全部验证通过后才能把链接发给玩家：

1. `+workbook-info --as user`：确认只有目标子表并取得真实 `sheet_id`。
2. `+csv-get --as user --range A1:D5`：确认三项百分比、三条口径和说明行均存在。
3. `+chart-list --as user`：确认标题为 `短视频发布关键问题信号` 的图表唯一存在。
4. `+revision-get --as user`：保存最新 revision。
5. 将 `artifacts.data_dashboard.status` 写为 `ready`，并保存 `url`、`token`、`sheet_id`、`chart_ids`、`revision`。

## 幂等与恢复

- 工作簿动作键：`E02.dashboard.workbook.create`；图表动作键：`E02.dashboard.chart.create`。
- 写入前登记 `pending` 回执，参数摘要必须包含完整标题和 `run_id`。
- 若工作簿回执为 `done` 且状态已有 URL，直接回读验证，不得重建。
- 若回执为 `pending` 但 URL 尚未写盘，读取 `lark-drive` 后以 user 身份按完整标题搜索；只认领标题与本局后六位完全匹配的唯一表格。零个才重建，多个则停止并说明，不猜最近一个。
- 图表回执未落盘时，先用 `+chart-list` 按标题查重；唯一同名图表可认领，零个才创建，多个则停止。
- Sheets 创建或验证失败时保持 E02，不得退回聊天逐条发送 KPI，也不得声称看板已完成。

## 聊天消息上限

看板准备好后，本幕业务消息最多两条：

1. Vincent在老板 Chat 发送一句目标压力，不包含具体 KPI。
2. kris姐在导师 Chat 发送看板链接和一张问题卡要求，不复述看板里的数字。
