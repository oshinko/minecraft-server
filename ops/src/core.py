import contextlib
import datetime
import enum
import inspect
import io
import json
import logging
import os
import pathlib
import re
import subprocess
import urllib.request

import mcrcon

from . import __version__

loglevel = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=loglevel)

parent_name = '.'.join(__name__.split('.')[:-1])
logger = logging.getLogger(parent_name)


def do_webhook(content, username='Minecraft Server'):
    logger.info('do_webhook: content: ' + content)

    webhook = os.environ.get('WEBHOOK')

    if not webhook:
        return

    data = dict(content=content, username=username)

    req = urllib.request.Request(
        webhook,
        data=json.dumps(data).encode('utf8'),
        headers={
            'content-type': 'application/json',
            'user-agent': 'MC-Ops/' + __version__
        }
    )

    with urllib.request.urlopen(req) as resp:
        return resp


def shutdown():
    subprocess.run('sudo shutdown -h now', shell=True)  # run as a sudoer


class RconException(Exception):
    ...


class Rcon:
    def __init__(self, host='localhost',
                 password=os.environ.get('RCON_PASSWORD')):
        self.hostname, *parts = host.split(':', 1)
        self.port = int(parts[0]) if parts else None
        self.password = password

    @contextlib.contextmanager
    def connect(self):
        self._rcon = mcrcon.MCRcon(self.hostname, self.password,
                                   port=self.port)

        try:
            self._rcon.connect()
            yield self
        except Exception as e:
            raise RconException from e
        finally:
            self._rcon.disconnect()

    def command(self, *args, **kwargs):
        try:
            r = self._rcon.command(*args, **kwargs)
            logger.info(f'rcon: command(*{args}, **{kwargs}): {r}')
            return r
        except Exception as e:
            logger.info(f'rcon: command(*{args}, **{kwargs})')
            raise RconException from e

    def list(self):
        try:
            resp = self.command('list')
        except Exception as e:
            raise RconException from e
        _, players = resp.split(': ', 1)
        return [x.strip() for x in players.split(',') if x]

    def stop(self):
        return self.command('stop')


_LOG_TIME_FMT = '%H:%M:%S'
_LOG_TIME_PAT = r'\d{2}:\d{2}:\d{2}'


class LogType(enum.Enum):
    PLAYER_ENTERED = re.compile(
        fr'^\[({_LOG_TIME_PAT})\] \[Server thread/INFO\]: .* joined the game'
    )
    PLAYER_EXITED = re.compile(
        fr'^\[({_LOG_TIME_PAT})\] \[Server thread/INFO\]: .* left the game'
    )
    SERVER_STARTING = re.compile(
        fr'^\[({_LOG_TIME_PAT})\] \[Server thread/INFO\]: Starting '
        r'[Mm]inecraft [Ss]erver'
    )
    SPECIFIED = re.compile(fr'^\[({_LOG_TIME_PAT})\]')
    UNSPECIFIED = re.compile(r'.*')

    @classmethod
    def __iter__(self):
        return (x for x in (self.SERVER_STARTING,
                            self.PLAYER_ENTERED,
                            self.PLAYER_EXITED,
                            self.SPECIFIED,
                            self.UNSPECIFIED))

    def match(self, *args, **kwargs):
        m = self.value.match(*args, **kwargs)

        if m:
            g = m.groups(default=())

            if g:
                t = datetime.datetime.strptime(g[0], _LOG_TIME_FMT).time()
                g = t, *g[1:]

            return m, *g


class LogFile:
    path = None
    buf = None
    text = None

    def __init__(self, path_or_buf, date=None):
        if isinstance(path_or_buf, (pathlib.Path, str)):
            self.path = pathlib.Path(path_or_buf)

            if date:
                self.date = date.date() if hasattr(date, 'date') else date
            else:
                try:
                    dt = datetime.datetime.strptime(
                        self.path.name[:10],
                        '%Y-%m-%d'
                    )
                    self.date = dt.date()
                except ValueError:
                    self.date = datetime.datetime.today()

        else:
            if not date:
                raise ValueError('date is required')
            self.date = date
            self.buf = path_or_buf
            self.text = self.buf.read()
            self.buf.seek(0)

    @contextlib.contextmanager
    def open(self):
        if self.path:
            self.buf = self.path.open()
        elif self.buf.closed:
            self.buf = io.StringIO(self.text)

        try:
            yield self
        finally:
            self.buf.close()

    def read_text(self, encoding='utf8'):
        if self.path:
            return self.path.read_text(encoding)
        elif self.buf.closed:
            self.buf = io.StringIO(self.text)
        else:
            self.buf.seek(0)

        return self.buf.read()

    def parse(self):
        self.buf.seek(0)

        for line in self.buf:
            for type_ in LogType:
                m = type_.match(line)

                if m:
                    yield type_, *m
                    break


server_home = pathlib.Path(os.environ.get('SERVER_HOME', '.'))
latest_log = LogFile(server_home / 'logs/latest.log')


class ChatFunction:
    functions = dict()
    descriptions = dict()
    parameters = dict()

    # ドキュメントでは optional だが、未指定の場合、このようにしないとエラーになる @ 23/6/16
    _no_parameters = {'type': 'object', 'properties': {}}

    def __call__(self, description, class_member=False):
        if not isinstance(description, str):
            raise ValueError

        def decorate(function):
            setattr(self, function.__name__, function)
            self.functions[function.__name__] = function
            self.descriptions[function.__name__] = description

            properties = {}
            required = []

            params = inspect.signature(function).parameters

            for i, (p_name, param) in enumerate(params.items()):
                if i == 0 and class_member:
                    continue  # skip self

                if param.annotation is inspect.Parameter.empty:
                    raise ValueError

                p_type = param.annotation.__origin__
                p_description, = param.annotation.__metadata__

                if param.default is inspect.Parameter.empty:
                    required.append(p_name)

                if p_type is bool:
                    p_json_type = 'boolean'
                if p_type in (float, int):
                    p_json_type = 'number'
                elif p_type is str:
                    p_json_type = 'string'
                else:
                    raise TypeError

                properties[p_name] = {
                    'type': p_json_type,
                    'description': p_description
                }

            if properties:
                self.parameters[function.__name__] = {
                    'type': 'object',
                    'properties': properties,
                    'required': required
                }
            else:
                self.parameters[function.__name__] = self._no_parameters

        return decorate

    @property
    def defs(self):
        return [
            {
                'name': name,
                'description': self.descriptions[name],
                'parameters': self.parameters[name]
            }
            for name in self.functions.keys()
        ]


chat_function = ChatFunction()
