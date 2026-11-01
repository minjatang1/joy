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
        for message in ['今天已签到', '您今天已经签到过了！', '今日已经签到', '已经签到']:
            with self.subTest(message=message):
                self.assertEqual(self.check_response({'code': '382004', 'msg': message}), '今天已签到')

    def test_already_signed_code_with_formatted_message(self):
        for code in ['382004', 382004]:
            with self.subTest(code=code):
                self.assertEqual(self.check_response({'code': code, 'msg': '<span>今天已签到</span>'}), '今天已签到')

    def test_unknown_code_is_not_accepted(self):
        with self.assertRaises(RuntimeError):
            self.check_response({'code': '382005', 'msg': '签到失败'})

    def test_safe_error_details(self):
        with self.assertRaises(RuntimeError) as result:
            self.check_response({'code': '100001', 'msg': '请先登录 fake-cookie SUB=secret-token https://example.com'})
        self.assertIn('返回码=100001', str(result.exception))
        self.assertIn('请先登录', str(result.exception))
        self.assertNotIn('fake-cookie', str(result.exception))
        self.assertNotIn('secret-token', str(result.exception))
        self.assertNotIn('example.com', str(result.exception))

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
