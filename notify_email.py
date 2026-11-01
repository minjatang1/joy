"""Email the current workflow's check-in report using Gmail SMTP over TLS."""
import os
from pathlib import Path
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo


def build_message(sender, recipient, outcome, report, run_url):
    now = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    status = '运行完成' if outcome == 'success' else '需要检查'
    message = EmailMessage()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = f'微博超话签到：{status}（北京时间 {now}）'
    message.set_content(
        f'运行时间：北京时间 {now}\n签到步骤状态：{outcome}\n\n'
        f'{report}\n\n运行日志：{run_url}\n\n'
        '“今天已签到”表示当日已完成；配置检查模式不会执行签到。\n'
    )
    return message


def main():
    sender = os.environ.get('SMTP_USERNAME', '').strip()
    password = os.environ.get('SMTP_PASSWORD', '').strip()
    recipient = os.environ.get('MAIL_TO', '').strip() or sender
    if not sender or not password:
        print('::warning::邮件通知未启用：请配置 SMTP_USERNAME 和 SMTP_PASSWORD Secrets。签到结果不受影响。')
        return 0
    if any('\n' in value or '\r' in value for value in [sender, recipient]):
        print('::error::邮件地址格式错误，请检查发件人与收件人配置。')
        return 1
    report_path = Path(os.environ['RUNNER_TEMP']) / 'weibo-result.txt'
    report = report_path.read_text(encoding='utf-8')[:20_000] if report_path.exists() else '签到步骤未生成结果，可能未执行。请查看运行日志。'
    run_url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    message = build_message(sender, recipient, os.environ.get('CHECKIN_OUTCOME', 'unknown'), report, run_url)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30, context=ssl.create_default_context()) as client:
            client.login(sender, password)
            client.send_message(message)
    except (smtplib.SMTPException, OSError):
        # SMTP errors can echo addresses and authentication details. Do not log them.
        print('::error::邮件发送失败：请检查 Gmail 应用专用密码、账号和 SMTP 连接。')
        return 1
    print('邮件已提交至发信服务器；请检查收件箱或垃圾邮件。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
