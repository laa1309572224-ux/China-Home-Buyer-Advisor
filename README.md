# 中国购房决策助手

一个零第三方依赖、数据本地保存的购房候选清单。它把房源导入、价格快照、可解释评分、筛选对比和决策提示放在一起。

## 运行

Windows 双击 `启动购房助手.cmd`，或运行：

```bash
python app.py
```

打开 <http://127.0.0.1:8766>。首次启动会载入 3 条明确标记的演示数据。

## 导入真实数据

页面支持 JSON 数组，必填字段：`title`、`total_price`（万元）、`unit_price`（元/㎡）、`area`（㎡）。建议同时提供 `source_url`、`city`、`district`、`community`、`year`、`commute_minutes`、`school_score`、`risk_score`。相同 `source_url` 再次导入会更新房源并保存当天价格快照。

后端还提供 `POST /api/collect`，接收 `{"url":"https://..."}`，只允许链家/贝壳 HTTPS 单房源链接。平台可能要求登录或改变页面结构；解析不完整时，先补齐字段再保存。系统不绕过验证码，不读取浏览器 Cookie，也不做高频批量请求。

## 评分口径

总分 = 预算 32% + 通勤 26% + 楼龄 14% + 教育 14% + 风险 14%。80 分以上“优先看房”，65–79.9“保留比较”，其余“谨慎考虑”。这是透明的启发式评分，不是房价预测或金融建议。

## 测试

```bash
python -m unittest -v
```

研究项目与 Star 排名见 [RESEARCH.md](RESEARCH.md)。
