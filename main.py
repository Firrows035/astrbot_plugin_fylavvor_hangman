"""Hangman word guessing game plugin for AstrBot.

Each chat session owns one round. Players either reveal a letter or guess the
whole word, and the answer is published when nobody makes an effective guess
within three minutes.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register

PLUGIN_VERSION = "1.0.3"
MAX_ATTEMPTS = 6
IDLE_TIMEOUT_MINUTES = 3
IDLE_TIMEOUT_SECONDS = IDLE_TIMEOUT_MINUTES * 60
MIN_WORD_LENGTH = 6
MASK_CHAR = "？"
DICT_DIR = Path(__file__).resolve().parent / "dict"

START_PROMPT = "游戏开始！"
NO_GAME_PROMPT = "当前没有进行中的猜词游戏，请先使用 /startguess 或 /猜词 开始。"
RUNNING_PROMPT = (
    "本会话已有进行中的猜词游戏，请使用 /guess 或 /猜 继续，或使用 /giveup 放弃。"
)
EMPTY_GUESS_PROMPT = "请输入要猜的字母或单词，例如：/guess a"
INVALID_GUESS_PROMPT = "请输入英文字母或单词。"
UNKNOWN_WORD_PROMPT = "词汇不在词库中，请输入正确单词"
ROUND_OVER = "本轮猜词结束"


@dataclass
class HangmanGame:
    """A single hangman round."""

    answer: str
    attempts_left: int = MAX_ATTEMPTS
    guesses: list[str] = field(default_factory=list)

    def mask(self) -> str:
        """Return the answer with unrevealed letters replaced by MASK_CHAR."""
        revealed = {guess for guess in self.guesses if len(guess) == 1}
        return "".join(char if char in revealed else MASK_CHAR for char in self.answer)

    def status_text(self) -> str:
        """Return the status block shown after every effective guess."""
        return (
            f"待猜测词语：{self.mask()}\n"
            f"剩余尝试次数：{self.attempts_left}\n"
            f"已猜测：{' '.join(self.guesses)}"
        )

    def is_solved(self) -> bool:
        """Return True when every letter of the answer has been revealed."""
        return MASK_CHAR not in self.mask()


@register(
    "astrbot_plugin_fylavvor_hangman",
    "Ferrin Fylavvor",
    "经典 Hangman 猜词游戏，支持字母揭示与整词猜测。",
    PLUGIN_VERSION,
)
class FylavvorHangman(Star):
    """Hangman game plugin."""

    def __init__(self, context: Context):
        super().__init__(context)
        self.games: dict[str, HangmanGame] = {}
        self.answers: list[str] = []
        self.words: set[str] = set()
        self._timers: dict[str, asyncio.Task] = {}
        self._round_ids: dict[str, int] = {}
        self._round_counter = 0

    async def initialize(self):
        """Load the bundled answer pool and the dictionary of valid words."""
        try:
            answer_text = (DICT_DIR / "answers.txt").read_text(encoding="utf-8")
            word_text = (DICT_DIR / "words.txt").read_text(encoding="utf-8")
        except OSError as exc:
            logger.error(f"[Hangman] Failed to load word lists: {exc}")
            return

        self.answers = sorted(
            {
                token.lower()
                for token in answer_text.split()
                if token.isalpha() and len(token) >= MIN_WORD_LENGTH
            }
        )
        self.words = {
            token.lower()
            for token in word_text.split()
            if token.isalpha() and len(token) >= MIN_WORD_LENGTH
        }
        logger.info(
            f"[Hangman] Loaded {len(self.answers)} answers and "
            f"{len(self.words)} dictionary words."
        )

    @filter.command("startguess", alias={"猜词"})
    async def startguess(self, event: AstrMessageEvent):
        """Start a new round in the current session."""
        session = event.unified_msg_origin
        game = self.games.get(session)
        if game is not None:
            yield event.plain_result(f"{RUNNING_PROMPT}\n{game.status_text()}")
            return
        if not self.answers:
            yield event.plain_result("词库为空，请检查插件 dict 目录下的词表文件。")
            return

        game = HangmanGame(answer=random.choice(self.answers))
        self.games[session] = game
        self._restart_timer(session)
        yield event.plain_result(f"{START_PROMPT}\n{game.status_text()}")

    @filter.command("guess", alias={"猜"})
    async def guess(self, event: AstrMessageEvent, text: str = ""):
        """Reveal a letter or compare a whole word with the answer."""
        session = event.unified_msg_origin
        game = self.games.get(session)
        if game is None:
            yield event.plain_result(NO_GAME_PROMPT)
            return

        text = text.strip().lower()
        if not text:
            yield event.plain_result(EMPTY_GUESS_PROMPT)
            return
        if not (text.isascii() and text.isalpha()):
            yield event.plain_result(INVALID_GUESS_PROMPT)
            return

        if len(text) == 1:
            if text in game.guesses:
                yield event.plain_result(
                    f"字母 {text} 已经猜过了。\n{game.status_text()}"
                )
                return
            game.guesses.append(text)
            if text in game.answer:
                message = f"成功揭示：{text}"
            else:
                game.attempts_left -= 1
                message = f"未能揭示：{text}"
        else:
            if text in game.guesses:
                yield event.plain_result(
                    f"单词 {text} 已经猜过了。\n{game.status_text()}"
                )
                return
            if text not in self.words:
                yield event.plain_result(f"{UNKNOWN_WORD_PROMPT}\n{game.status_text()}")
                return
            game.guesses.append(text)
            if text == game.answer:
                self._end_round(session)
                yield event.plain_result(f"答对了！答案：{game.answer}\n{ROUND_OVER}")
                return
            game.attempts_left -= 1
            message = f"猜词错误：{text}"

        if game.is_solved():
            self._end_round(session)
            yield event.plain_result(f"答对了！答案：{game.answer}\n{ROUND_OVER}")
            return
        if game.attempts_left <= 0:
            self._end_round(session)
            yield event.plain_result(
                f"尝试次数已用完！答案：{game.answer}\n{ROUND_OVER}"
            )
            return

        # Only guesses that changed the game state refresh the idle timer.
        self._restart_timer(session)
        yield event.plain_result(f"{message}\n{game.status_text()}")

    @filter.command("giveup")
    async def giveup(self, event: AstrMessageEvent):
        """Abandon the current round and reveal the answer."""
        game = self._end_round(event.unified_msg_origin)
        if game is None:
            yield event.plain_result(NO_GAME_PROMPT)
            return
        yield event.plain_result(f"已放弃本轮猜词！答案：{game.answer}\n{ROUND_OVER}")

    def _restart_timer(self, session: str) -> None:
        """Restart the idle timer that publishes the answer after a timeout."""
        timer = self._timers.pop(session, None)
        if timer is not None:
            timer.cancel()
        self._round_counter += 1
        self._round_ids[session] = self._round_counter
        self._timers[session] = asyncio.create_task(
            self._reveal_after_timeout(session, self._round_counter)
        )

    def _end_round(self, session: str) -> HangmanGame | None:
        """Remove the session round and cancel its idle timer."""
        timer = self._timers.pop(session, None)
        if timer is not None:
            timer.cancel()
        self._round_ids.pop(session, None)
        return self.games.pop(session, None)

    async def _reveal_after_timeout(self, session: str, round_id: int) -> None:
        """Publish the answer once the session stayed idle for a full timeout."""
        await asyncio.sleep(IDLE_TIMEOUT_SECONDS)

        # A newer round may have replaced this one while we were sleeping.
        if self._round_ids.get(session) != round_id:
            return
        game = self.games.pop(session, None)
        self._round_ids.pop(session, None)
        self._timers.pop(session, None)
        if game is None:
            return
        try:
            await self.context.send_message(
                session,
                MessageChain().message(
                    f"{IDLE_TIMEOUT_MINUTES}分钟内无人猜测：公布答案："
                    f"{game.answer}\n{ROUND_OVER}"
                ),
            )
        except Exception as exc:
            logger.error(f"[Hangman] Failed to send timeout message: {exc}")

    async def terminate(self):
        """Cancel pending timers when the plugin is unloaded or reloaded."""
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
        self._round_ids.clear()
        self.games.clear()
