# Changelog

本插件的版本更新记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.1] - 2026-10-20

### 新增

- 词库扩充：从 [ECDICT](https://github.com/skywind3000/ECDICT)（MIT）中按 `cet6` / `ielts` / `toefl`
  标签提取六级、雅思、托福词汇（长度 ≥ 6、纯字母），去重后合并进内置词表。
- 指令中文别名：`/startguess` 支持 `/猜词`，`/guess` 支持 `/猜`。

### 变更

- 答案池由 4696 词扩充到 8977 词，合法性校验词表由 4773 词扩充到 8999 词；
  校验词表仍为答案池的超集，专有名词（如 `african`）只用于校验、不会被抽为答案。
- README 更新词库规模、数据来源与别名说明，并新增本 CHANGELOG。

## [1.0.0] - 2026-10-20

### 新增

- 首个版本：经典 Hangman 猜词游戏。
- `/startguess`、`/guess`、`/giveup` 三条指令，按会话（`event.unified_msg_origin`）隔离对局。
- 单字母揭示全部出现位置，整词猜测先校验词库再比较答案，全程不区分大小写。
- 固定 6 次猜测机会：猜错字母或猜错单词各消耗 1 次，词库外单词只提示、不消耗次数。
- 1 分钟空闲计时：每次产生实际进展的猜测都会重置，超时后主动推送答案并结束本局。
- 状态块统一展示待猜测词语、剩余尝试次数与已猜测内容。
- 内置词库（长度 ≥ 6 的纯字母单词），来自 KyleBing/english-vocabulary（BSD-3-Clause），
  经由 astrbot_plugin_wordle 的 `classic` 词典筛选。
