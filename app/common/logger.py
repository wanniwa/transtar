import datetime
import logging
import os
import sys

from pathlib import Path

from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.rule import Rule

# 这行代码的作用是将当前工作目录改变到相对于当前脚本所在目录的上一级目录‌。
os.chdir(os.path.join(os.path.dirname(__file__), '../../'))


# 空配置防止重复日志
def empty_function(*args, **kwargs):
    pass


logging.basicConfig = empty_function

# True的作用是当日志事件发生时，如果未找到处理器（handler），则会抛出异常
logging.raiseExceptions = True

logger_debug = False
logger = logging.getLogger('transtar')
logger.setLevel(logging.DEBUG if logger_debug else logging.INFO)
file_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d | %(filename)20s:%(lineno)04d | %(levelname)8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
console_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d │ %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
gui_formatter = logging.Formatter(
    fmt='| %(asctime)s.%(msecs)03d | %(message)08s', datefmt='%H:%M:%S')

# ======================================================================================================================
#            Set console logger
# ======================================================================================================================

rich_console_Handler = RichHandler(
    console=Console(
        width=160
    ),
    show_path=False,
    show_time=False,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
    tracebacks_extra_lines=3,
    tracebacks_width=160

)
rich_console_Handler.setFormatter(console_formatter)
logger.addHandler(rich_console_Handler)


# ======================================================================================================================
#            Set file
# ======================================================================================================================
class RichFileHandler(RichHandler):
    # Rename
    pass


pyw_name = Path(sys.argv[0]).stem


def set_file_logger(name=pyw_name):
    if '_' in name:
        # wan1_config => wan1
        name = name.split('_', 1)[0]
    log_file = f'./log/{datetime.date.today()}_{name}.txt'

    # 创建日志文件夹
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    # mode='a'：如果文件存在，新的数据将被添加到文件的末尾；如果文件不存在，将创建一个新文件。
    file = open(log_file, mode='a', encoding='utf-8')

    file_console = Console(
        file=file,
        no_color=True,
        highlight=False,
        width=160,
    )

    rich_file_handler = RichFileHandler(
        console=file_console,
        show_path=False,
        show_time=False,
        show_level=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=3,
        tracebacks_width=160,
        highlighter=NullHighlighter(),
    )
    rich_file_handler.setFormatter(file_formatter)

    logger.handlers = [h for h in logger.handlers if not isinstance(
        h, (logging.FileHandler, RichFileHandler))]
    logger.addHandler(rich_file_handler)
    logger.log_file = log_file


#
# # ======================================================================================================================
# #            Set flutter
# # ======================================================================================================================
# class FlutterHandler(RichHandler):
#     # Rename
#     pass
#
#
# class FlutterConsole(Console):
#     """
#     Force full feature console
#     but not working lol :(
#     """
#
#     @property
#     def options(self) -> ConsoleOptions:
#         return ConsoleOptions(
#             max_height=self.size.height,
#             size=self.size,
#             legacy_windows=False,
#             min_width=1,
#             max_width=self.width,
#             encoding='utf-8',
#             is_terminal=False,
#         )
#
#
# class FlutterLogStream(TextIOBase):
#     def __init__(self, *args, func: Callable[[ConsoleRenderable], None] = None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._func = func
#
#     def write(self, msg: str) -> int:
#         if isinstance(msg, bytes):
#             msg = msg.decode("utf-8")
#         self._func(msg)
#         return len(msg)
#
#
# def set_func_logger(func):
#     stream = FlutterLogStream(func=func)
#     stream_console = Console(
#         file=stream,
#         force_terminal=False,
#         force_interactive=False,
#         no_color=True,
#         highlight=False,
#         width=80,
#     )
#     hdlr = FlutterHandler(
#         console=stream_console,
#         show_path=False,
#         show_time=False,
#         show_level=True,
#         rich_tracebacks=True,
#         tracebacks_show_locals=True,
#         tracebacks_extra_lines=3,
#         highlighter=NullHighlighter(),
#     )
#     hdlr.setFormatter(flutter_formatter)
#     logger.addHandler(hdlr)
#

# ======================================================================================================================
#            Set print format
# ======================================================================================================================


# def _get_renderables(
#         self: Console, *objects, sep=" ", end="\n", justify=None, emoji=None, markup=None, highlight=None,
# ) -> List[ConsoleRenderable]:
#     """
#     Refer to rich.console.Console.print()
#     """
#     if not objects:
#         objects = (NewLine(),)

#     render_hooks = self._render_hooks[:]
#     with self:
#         renderables = self._collect_renderables(
#             objects,
#             sep,
#             end,
#             justify=justify,
#             emoji=emoji,
#             markup=markup,
#             highlight=highlight,
#         )
#         for hook in render_hooks:
#             renderables = hook.process_renderables(renderables)
#     return renderables


def print(*objects: ConsoleRenderable, **kwargs):
    for hdlr in logger.handlers:
        # if isinstance(hdlr, FlutterHandler):
        #     for renderable in _get_renderables(hdlr.console, *objects, **kwargs):
        #         hdlr.console.file._func(str(renderable))
        # elif isinstance(hdlr, RichHandler):
        #     hdlr.console.print(*objects)
        if isinstance(hdlr, RichHandler):
            hdlr.console.print(*objects)


class GuiRule(Rule):
    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        options.max_width = 80
        return super().__rich_console__(console, options)

    def __str__(self):
        total_width = 80
        cell_len = len(self.title) + 2
        aside_len = (total_width - cell_len) // 2
        left = self.characters * aside_len
        right = self.characters * (total_width - cell_len - aside_len)
        if self.title:
            space = ' '
        else:
            space = self.characters
        return f"{left}{space}{self.title}{space}{right}\n"

    def __repr__(self):
        return self.__str__()


def rule(title="", *, characters="─", style="rule.line", end="\n", align="center"):
    rule = GuiRule(title=title, characters=characters,
                   style=style, end=end)
    print(rule)


def hr(title, level=3):
    title = str(title).upper()
    if level == 1:
        logger.rule(title, characters='═')
        logger.info(title)
    if level == 2:
        logger.rule(title, characters='─')
        logger.info(title)
    if level == 3:
        logger.info(f"[bold]<<< {title} >>>[/bold]", extra={"markup": True})
    if level == 0:
        logger.rule(characters='═')
        logger.rule(title, characters='─')
        logger.rule(characters='═')


def attr(name, text):
    logger.info('[%s] %s' % (str(name), str(text)))


def attr_align(name, text, front='', align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front):]
    logger.info('%s: %s' % (name, str(text)))


def show():
    logger.info('INFO')
    logger.warning('WARNING')
    logger.debug('DEBUG')
    logger.error('ERROR')
    logger.critical('CRITICAL')
    logger.hr('hr0', 0)
    logger.hr('hr1', 1)
    logger.hr('hr2', 2)
    logger.hr('hr3', 3)
    logger.info(r'Brace { [ ( ) ] }')
    logger.info(r'True, False, None')
    logger.info(r'E:/path\\to/alas/alas.exe, /root/alas/, ./relative/path/log.txt')
    local_var1 = 'This is local variable'
    print(local_var1)
    logger.info(
        'Tests very long strings. Tests very long strings. Tests very long strings. Tests very long strings. Tests very long strings.')

    raise Exception("Exception")


def error_convert(func):
    def error_wrapper(msg, *args, **kwargs):
        if isinstance(msg, Exception):
            msg = f'{type(msg).__name__}: {msg}'
        return func(msg, *args, **kwargs)

    return error_wrapper


logger.error = error_convert(logger.error)
logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
logger.set_file_logger = set_file_logger
# logger.set_func_logger = set_func_logger
logger.rule = rule
logger.print = print

logger.set_file_logger()
logger.hr('Start', level=3)
