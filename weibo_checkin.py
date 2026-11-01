"""Sign in to explicitly configured Weibo super topics using the web API."""
import argparse
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward the authentication cookie to a login or other host.
        return None


urlopen = build_opener(NoRedirect()).open

TOPICS = [('张元英', 'WEIBO_TOPIC_ZHANG_WONYOUNG'), ('IROHA外园彩羽', 'WEIBO_TOPIC_IROHA')]


def topic_id(value):
    value = value.strip()
    if value.startswith('https://'):
        parsed = urlsplit(value)
        if parsed.netloc not in {'weibo.com', 'www.weibo.com'}:
            raise ValueError('超话链接必须来自 https://weibo.com/p/100808…')
        value = parsed.path.removeprefix('/p/').rstrip('/')
    if not re.fullmatch(r'100808[0-9a-fA-F]{32}', value):
        raise ValueError('请填写超话网页链接或完整的 100808 开头的超话 ID')
    return value


def checkin(cookie, identifier):
    # The nested HTTP URL is Weibo's API selector; the actual request uses HTTPS.
    query = urlencode({'api': 'http://i.huati.weibo.com/aj/super/checkin',
                       'id': identifier, 'location': 'page_100808_super_index',
                       '__rnd': time.time_ns() // 1_000_000})
    request = Request('https://weibo.com/p/aj/general/button?' + query, headers={
        'Cookie': cookie, 'Referer': 'https://weibo.com/p/' + identifier,
        'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})
    try:
        with urlopen(request, timeout=30) as response:
            if urlsplit(response.url).netloc not in {'weibo.com', 'www.weibo.com'}:
                raise RuntimeError('登录状态失效或请求被重定向，请更新 WEIBO_COOKIE')
            payload = json.loads(response.read(1_000_000))
    except HTTPError as exc:
        raise RuntimeError(f'微博返回 HTTP {exc.code}') from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError('无法连接微博，请检查网络后重试') from None
    except (ValueError, UnicodeError):
        raise RuntimeError('微博未返回预期 JSON；请检查登录状态或接口变更') from None
    if not isinstance(payload, dict):
        raise RuntimeError('微博响应格式异常')
    if str(payload.get('code')) == '100000':
        return '签到成功'
    message = payload.get('msg', '')
    if isinstance(message, str) and re.fullmatch(r'(?:今天已签到|今日已签到|已经签到|已签到)[！!。.]?', message.strip()):
        return '今天已签到'
    # Never log raw responses, headers, or cookies.
    raise RuntimeError('微博未确认签到成功；请检查账号、关注状态、登录有效期或接口变更')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true', help='仅检查配置格式，不签到')
    args = parser.parse_args()
    configured = []
    try:
        for name, variable in TOPICS:
            value = os.environ.get(variable, '')
            if not value:
                raise ValueError(f'缺少仓库变量 {variable}（{name}的超话链接）')
            configured.append((name, topic_id(value)))
        if configured[0][1] == configured[1][1]:
            raise ValueError('两个超话不能使用同一个 ID')
        cookie = os.environ.get('WEIBO_COOKIE', '').strip()
        if not args.validate_only and (not cookie or '\n' in cookie or '\r' in cookie):
            raise ValueError('请在 GitHub Actions Secrets 中配置有效的 WEIBO_COOKIE')
    except ValueError as exc:
        print(f'配置错误：{exc}', file=sys.stderr)
        return 1
    failed = False
    for name, identifier in configured:
        if args.validate_only:
            print(f'{name}：配置格式有效（未验证页面身份，未签到）')
            continue
        try:
            print(f'{name}：{checkin(cookie, identifier)}')
        except RuntimeError as exc:
            failed = True
            print(f'{name}：失败：{exc}', file=sys.stderr)
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
