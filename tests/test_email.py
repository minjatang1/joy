from pathlib import Path
import smtplib
import tempfile
import unittest
from unittest.mock import patch

import notify_email as app


class EmailTests(unittest.TestCase):
    def test_message_preserves_each_topic_result_and_link(self):
        message = app.build_message('sender@example.com', 'recipient@example.com', 'failure',
                                    '张元英：今天已签到\nIROHA外园彩羽：失败', 'https://github.com/a/b/actions/runs/1')
        self.assertIn('需要检查', str(message['Subject']))
        self.assertIn('张元英：今天已签到', message.get_content())
        self.assertIn('IROHA外园彩羽：失败', message.get_content())
        self.assertIn('https://github.com/a/b/actions/runs/1', message.get_content())

    def test_missing_credentials_do_not_break_checkin(self):
        with patch.dict(app.os.environ, {}, clear=True), patch.object(app.smtplib, 'SMTP_SSL') as smtp:
            self.assertEqual(app.main(), 0)
            smtp.assert_not_called()

    def test_sends_over_tls_and_reports_delivery_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'weibo-result.txt').write_text('张元英：签到成功', encoding='utf-8')
            values = dict(SMTP_USERNAME='sender@example.com', SMTP_PASSWORD='fake-password',
                          MAIL_TO='recipient@example.com', RUNNER_TEMP=folder,
                          GITHUB_REPOSITORY='a/b', GITHUB_RUN_ID='1', CHECKIN_OUTCOME='success')
            with patch.dict(app.os.environ, values, clear=True), patch.object(app.smtplib, 'SMTP_SSL') as smtp:
                self.assertEqual(app.main(), 0)
                client = smtp.return_value.__enter__.return_value
                client.login.assert_called_once_with('sender@example.com', 'fake-password')
                sent = client.send_message.call_args.args[0]
                self.assertEqual(sent['To'], 'recipient@example.com')
                self.assertNotIn('fake-password', sent.as_string())
                self.assertEqual(smtp.call_args.args, ('smtp.gmail.com', 465))
                client.send_message.side_effect = smtplib.SMTPException('private server details')
                self.assertEqual(app.main(), 1)
