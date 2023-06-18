import contextlib
import datetime
import io
import pathlib
import uuid

from src.auto import shutdown as auto_shutdown
from src.core import LogFile

log_head_text = pathlib.Path(__file__, '../head.log').read_text('utf8').strip()

player_uuid = uuid.uuid4()

# 切断形跡のあるログ
log_text_exited = f"""
{log_head_text}
[00:10:00] [User Authenticator #0/INFO]: UUID of player Taro is {player_uuid}
[00:10:00] [Server thread/INFO]: Taro joined the game
[01:00:00] [Server thread/INFO]: Taro lost connection: Disconnected
[01:00:00] [Server thread/INFO]: Taro left the game
[01:01:00] [Server thread/INFO]: ...
""".lstrip()

# 切断形跡のないログ
log_text_no_exited = f"""
{log_head_text}
[00:10:00] [User Authenticator #0/INFO]: UUID of player Taro is {player_uuid}
[00:10:00] [Server thread/INFO]: Taro joined the game
[01:01:00] [Server thread/INFO]: ...
""".lstrip()


class MockRcon:
    def __init__(self, *_args, **_kwargs):
        ...

    @contextlib.contextmanager
    def connect(self):
        yield self

    def list(self):
        raise NotImplementedError

    def stop(self):
        print('Called MockRcon.stop()')


def datetime_from(date, time):
    return datetime.datetime.combine(date, datetime.time.fromisoformat(time))


class ShutdownFunctionCalled(Exception):
    ...


def mock_shutdown():
    raise ShutdownFunctionCalled


def prepare_auto_shutdown_test(date, log_file_exited, log_file_no_exited):
    rcon = MockRcon()

    def test(Execute):
        # : normal
        execute = Execute(rcon, log_file_exited, shutdown=mock_shutdown)

        # : : 最後の切断から一時間以上
        execute.now = lambda: datetime_from(date, '02:00')

        # : : : まだ遊んでいる
        rcon.list = lambda: ['aaaa', 'bbbb']

        try:
            execute()
        except ShutdownFunctionCalled:
            raise AssertionError('shutdown() が呼ばれてはいけません。')
        else:
            ...  # OK

        # : : : もう遊んでいない
        rcon.list = lambda: []

        try:
            execute()
        except ShutdownFunctionCalled:
            ...  # OK
        else:
            raise AssertionError('shutdown() が呼ばれないといけません。')

        # : : 最後の切断から一時間未満
        execute.now = lambda: datetime_from(date, '01:59')

        # : : : まだ遊んでいる
        rcon.list = lambda: ['aaaa', 'bbbb']

        try:
            execute()
        except ShutdownFunctionCalled:
            raise AssertionError('shutdown() が呼ばれてはいけません。')
        else:
            ...  # OK

        # : : : もう遊んでいない
        rcon.list = lambda: []

        try:
            execute()
        except ShutdownFunctionCalled:
            raise AssertionError('shutdown() が呼ばれてはいけません。')
        else:
            ...  # OK

        # : abnormal
        execute = Execute(rcon, log_file_no_exited, shutdown=mock_shutdown)

        # : : 最後の接続から一時間以上
        execute.now = lambda: datetime_from(date, '01:10')

        # : : : まだ遊んでいる
        rcon.list = lambda: ['aaaa', 'bbbb']

        try:
            execute()
        except ShutdownFunctionCalled:
            raise AssertionError('shutdown() が呼ばれてはいけません。')
        else:
            ...  # OK

        # : : : もう遊んでいない
        rcon.list = lambda: []

        try:
            execute()
        except ShutdownFunctionCalled:
            ...  # OK
        else:
            raise AssertionError('shutdown() が呼ばれないといけません。')

        # : : 最後の接続から一時間未満
        execute.now = lambda: datetime_from(date, '01:09')

        # : : : まだ遊んでいる
        rcon.list = lambda: ['aaaa', 'bbbb']

        try:
            execute()
        except ShutdownFunctionCalled:
            raise AssertionError('shutdown() が呼ばれてはいけません。')
        else:
            ...  # OK

        # : : : もう遊んでいない
        rcon.list = lambda: []

        try:
            execute()
        except ShutdownFunctionCalled:
            raise AssertionError('shutdown() が呼ばれてはいけません。')
        else:
            ...  # OK

    return test


date = datetime.date.fromisoformat('2023-01-01')

log_file_exited = LogFile(io.StringIO(log_text_exited), date=date)
log_file_no_exited = LogFile(io.StringIO(log_text_no_exited), date=date)

with log_file_exited.open() as log:
    assert len(list(log.parse())) == len(log_text_exited.splitlines())

test = prepare_auto_shutdown_test(date, log_file_exited, log_file_no_exited)

execute_auto_shutdown_classes = [auto_shutdown.StrictExecute]

if auto_shutdown.OpenAIExecute.enable:
    execute_auto_shutdown_classes.append(auto_shutdown.OpenAIExecute)

for Execute in execute_auto_shutdown_classes:
    test(Execute)
