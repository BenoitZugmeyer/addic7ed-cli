
from addic7ed_cli.request import session
from addic7ed_cli.error import Error


def login(user, password):
    global _current_user

    result = session.post('/dologin.php', data={
        'username': user,
        'password': password,
        'remember': 'true'
    })

    _current_user = None

    if get_current_user():
        return session.cookies['PHPSESSID']

    raise Error(result('center p[align="center"]').text())


_current_user = None


def get_current_user():
    global _current_user

    if _current_user is None:
        page = session.get('/')
        titles = page('.footer_dropup h4')
        if titles and titles[0].text.startswith('Welcome back'):
            _current_user = titles[0].text[13:].strip()
        else:
            _current_user = False

    return _current_user


def set_session(sess):
    global _current_user
    _current_user = None
    session.cookies['PHPSESSID'] = sess
