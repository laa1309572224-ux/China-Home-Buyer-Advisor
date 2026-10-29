# 中国房源开源项目调研（2026-10-28）

Star 会变化，下表按调研时可核验的公开页面降序排列；“可借鉴”不等于代码仍可直接运行。

| 排名 | 项目 | Star | 重点 | 结论 |
|---:|---|---:|---|---|
| 1 | [jumper2014/lianjia-beike-spider](https://github.com/jumper2014/lianjia-beike-spider) | 约 2.5k | 21 城、链家/贝壳、多种存储 | 覆盖最全，但核心较老，页面适配需重验 |
| 2 | [waugustus/lianjia-spider](https://github.com/waugustus/lianjia-spider) | 67 | 每日抓取、历史价格、已售迁移、Electron | 历史快照设计最贴近购房决策 |
| 3 | [Yohmien/crawler](https://github.com/Yohmien/crawler) | 49 | 武汉房源、MongoDB、地图可视化 | 适合参考分析展示，不宜照搬数据栈 |
| 4 | [Crush0nyou/beike-lianjia](https://github.com/Crush0nyou/beike-lianjia) | 42 | 小区、二手房、租房、新房 | CSV 输出简单，代码年代较早 |
| 5 | [longxiaofei/spider-lianjia](https://github.com/longxiaofei/spider-lianjia) | 12 | Scrapy、二手房与租房 | 教学价值高，维护与合规能力弱 |
| 6 | [qiaofei32/lianjia](https://github.com/qiaofei32/lianjia) | 2 | 成交、新房、评论、MySQL | 数据维度可参考，活跃度低 |

补充：`MinjieDING/Lianjia` 提供较新的 Selenium 成交采集、断点续跑和验证码人工处理思路；`BENZEMA216/rent-ops` 与 `leonfighting-py/RentMap` 更偏租房，但其“多维评分 + 通勤 + 风险核验”适合迁移到购房场景。

本项目没有复制上述仓库代码，避免引入不明兼容性和许可证义务；只借鉴“本地历史快照”和“透明多维评分”的产品思路。
