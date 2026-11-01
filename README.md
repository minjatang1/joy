# 微博超话每日签到

通过 GitHub Actions 每天北京时间 **08:00**（UTC 00:00）尝试为「张元英」及「IROHA外园彩羽」超话签到。支持手动运行。GitHub 定时任务可能延迟，不能保证精确到点执行。

## 首次配置

1. 将本项目提交到 GitHub 仓库的默认分支，在 Actions 中启用工作流。
2. 在仓库 **Settings → Secrets and variables → Actions → Secrets** 新建 `WEIBO_COOKIE`。值为本人已登录微博网页版请求的完整 Cookie 请求头值，不含 `Cookie:` 前缀。Cookie 相当于登录凭据，不要发到聊天、代码或日志中。建议使用私有仓库，仅允许可信人员修改工作流。
3. 工作流已按提供的链接内置两个超话 ID：张元英 `1008080637ba9df8242042bba48c63aa59f947`、IROHA外园彩羽 `1008080910a89e285df865827cd187911623bc`。无需另填变量。如需覆盖，可在同一页面的 **Variables** 新建：

   | 变量 | 内容 |
   | --- | --- |
   | `WEIBO_TOPIC_ZHANG_WONYOUNG` | 张元英超话真实网页链接 |
   | `WEIBO_TOPIC_IROHA` | IROHA外园彩羽超话真实网页链接 |

   支持 `https://weibo.com/p/100808` 加 32 位十六进制 ID 的链接，或直接填写完整 ID。请勿填写搜索页或同名用户主页。程序按 ID 操作，显示名称不会验证页面身份，请仔细核对链接。账号应已关注这两个超话。
4. 在 **Actions → 微博超话每日签到 → Run workflow** 手动运行一次。勾选 `validate_only` 仅检查配置格式，不勾选才实际签到。查看两个超话各自的成功结果后，再确认定时运行。

## 限制与故障

- 使用微博网页的非官方接口，尚需真实账号验证。接口变更、风控或 Cookie 过期会导致失败。需要验证时，请本人在微博完成验证并更新 Secret，不支持绕过验证码。
- 成功或“今天已签到”才算完成；一个超话失败仍会尝试另一个，任务最终以失败退出。不会打印 Cookie 或原始响应。
- 定时任务仅在默认分支运行；公共仓库长期无活动可能被 GitHub 自动停用，需要在 Actions 中重新启用。失败通知取决于 GitHub Actions 通知设置。
- 准备好代码不代表已部署；需要推送、配置真实链接和凭据，并完成首次实际签到验证。

## 每日邮件通知（Gmail）

每次运行结束都会尝试发送各超话结果与本次运行日志链接，签到失败也会尝试通知。请在仓库 **Settings → Secrets and variables → Actions → Secrets** 配置：

| Secret | 内容 |
| --- | --- |
| `SMTP_USERNAME` | 用于发信的完整 Gmail 地址；可用自己的收件邮箱给自己发信 |
| `SMTP_PASSWORD` | 该 Google 账号的应用专用密码，不是日常登录密码 |
| `MAIL_TO` | 收件地址；不填则发给 `SMTP_USERNAME` 本人 |

在 Google 账号启用两步验证后，访问 https://myaccount.google.com/apppasswords 创建名为“微博签到”的应用专用密码，将生成的密码保存到 `SMTP_PASSWORD`，不要发到聊天或提交进代码。部分 Google 账号不支持应用专用密码；此时需换用支持发信的账号或调整发信服务。

配置好后手动运行一次，并检查收件箱与垃圾邮件。程序只记录是否已提交给 Gmail 发信服务器，不能确认最终入箱。未配置发信凭据时通知步骤会提示未启用，不影响签到。邮件发送失败会使工作流失败，但不会撤销已经完成的签到。若 GitHub 没有触发任务、整个任务被强制终止或 GitHub 故障，则无法通过同一工作流发送邮件。

## 本地开发与验证

Python 3.12，仅使用标准库，无需第三方依赖。

```bash
python -m unittest discover -s tests -v
python weibo_checkin.py --validate-only
python weibo_checkin.py
```

后两条命令从环境变量读取上述配置。凭据应安全注入，避免记录到 shell 历史。无需后台服务，定时运行由 GitHub Actions 承担。
