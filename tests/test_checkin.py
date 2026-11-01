import io
import json
import unittest
from unittest.mock import patch
import weibo_checkin as app


class Response(io.BytesIO):
    url = 'https://weibo.com/p/aj/general/button'


class CheckinTests(unittest.TestCase):
    def test_topic_link(self):
        identifier = '100808' + 'a' * 32
        self.assertEqual(app.topic_id('https://weibo.com/p/' + identifier + '?from=test'), identifier)

    def test_invalid_topic(self):
        for value in ['张元英', 'https://evil.example/p/100808' + 'a' * 32, '100808abc']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                app.topic_id(value)

    def check_response(self, payload):
        with patch.object(app, 'urlopen', return_value=Response(json.dumps(payload).encode())) as opened:
            result = app.checkin('fake-cookie', '100808' + 'a' * 32)
            self.assertTrue(opened.call_args.args[0].full_url.startswith('https://weibo.com/'))
            return result

    def test_success(self):
        self.assertEqual(self.check_response({'code': '100000'}), '签到成功')

    def test_already_signed(self):
        self.assertEqual(self.check_response({'code': '382004', 'msg': '今天已签到'}), '今天已签到')

    def test_failure_is_not_success(self):
        for payload in [{'code': '100001', 'msg': '请先登录'}, {}, [], {'code': '100001', 'msg': '签到失败'}, {'code': '100001', 'msg': '无法确认已签到'}]:
            with self.subTest(payload=payload), self.assertRaises(RuntimeError):
                self.check_response(payload)

    def test_non_json(self):
        with patch.object(app, 'urlopen', return_value=Response(b'<html>login</html>')):
            with self.assertRaises(RuntimeError):
                app.checkin('fake-cookie', '100808' + 'a' * 32)

    def test_both_topics_attempted_after_failure(self):
        values = {'WEIBO_TOPIC_ZHANG_WONYOUNG': '100808' + 'a' * 32,
                  'WEIBO_TOPIC_IROHA': '100808' + 'b' * 32, 'WEIBO_COOKIE': 'fake-cookie'}
        with patch.dict(app.os.environ, values, clear=True), patch('sys.argv', ['checkin']), patch.object(app, 'checkin', side_effect=[RuntimeError('failed'), '签到成功']) as send:
            self.assertEqual(app.main(), 1)
            self.assertEqual(send.call_count, 2)


if __name__ == '__main__':
    unittest.main()
