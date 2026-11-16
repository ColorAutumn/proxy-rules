# v2rayN 规则集：绕过大陆（含开发者常用服务）

一份给 v2rayN 用的路由规则集，可以直接通过订阅 URL 导入。

核心是「国内直连、其余走代理」，额外把几类**走代理会导致功能异常**的服务补进了直连名单。

## 订阅地址

```
https://cdn.jsdelivr.net/gh/<OWNER>/<REPO>@main/v4-cn-direct.json
```

> 用 jsDelivr 而不是 raw.githubusercontent.com：后者在国内直连会超时。
> 仓库必须是**公开**的，jsDelivr 才能拉取。

## v2rayN 导入步骤

1. 设置 → 路由设置
2. 选中目标规则集（或新建一个）
3. 高级功能 → 添加 → 备注随意填，URL 填上面的订阅地址
4. 点「从订阅 URL 导入规则」
5. 提示是否追加时选 **否**（覆盖，避免重复累积）
6. 保存并启用该规则集

规则更新后，重复第 4 步即可。

## 为什么不能只发布「Part 规则」

v2rayN **一次只启用一个规则集**。如果只发布几条自定义 direct 规则并启用，
原本的 `geosite:cn` 兜底会一起失效，国内网站会全部走代理。
所以这份文件是**完整的一套**，导入后自洽。

## 规则说明

规则从上到下匹配，命中即止。

| # | 出站 | 备注 | 说明 |
|---|---|---|---|
| 0 | direct | MC 资源直连 | Mojang 的大文件（client/server jar）在美国 CDN，走代理会被限速到 200KB/s 以下，Loom 会超时 |
| 1 | direct | Bing 直连 | `geosite:cn` 只收录了 `cn.bing.com`，`www.bing.com` 走代理会切到国际版索引，搜索行为不一致 |
| 2 | direct | 微软服务直连 | Windows 更新的 CDN 就在国内；`msftconnecttest.com` 走代理会导致系统误报「无网络」；账号登录 IP 跳变会触发风控 |
| 3 | direct | 苹果服务直连 | `mzstatic.com` 是 App Store 的图标与预览图 CDN |
| 4 | direct | QQ 组件直连 | `qqsuites.com` 是 `geosite:cn` 唯一遗漏的腾讯域 |
| 5 | block | 阻断 udp443 | 阻断 QUIC，避免代理链路上的 UDP 质量问题；浏览器会回落 TCP |
| 6 | proxy | 代理 Google | 不走 GEO 判定，显式指定 |
| 7-10 | direct | 局域网 / 公共 DNS | 内网与国内公共 DNS 不应经过代理 |
| 11-12 | direct | 中国 IP / 域名 | 兜底 |

## 已知取舍

- `domain:microsoft.com` 会连带 `learn.microsoft.com`、`support.microsoft.com` 等子域一起直连。
  国内访问这些站点能通，只是不算快。如果更在意速度可以改成只列必要子域。
- `xboxlive.com`、`azure.com`、`visualstudio.com` **故意没有**加入直连，走代理更合适。
- Steam / Epic / Battle.net 等游戏平台也不在名单里，国内直连基本不可用。

## 本地校验

```bash
python scripts/validate.py
```

会检查出站标签合法性、`Domain` 是否漏了类型前缀、`Id` 是否重复、
以及 `geosite:cn` 兜底规则是否还在——字段写错 v2rayN 不会报错，只会静默失效。

## 更新

```bash
# 改完 v4-cn-direct.json 后
python scripts/validate.py && git commit -am "update rules" && git push
```

各机器重新执行一次「从订阅 URL 导入规则」即可。
