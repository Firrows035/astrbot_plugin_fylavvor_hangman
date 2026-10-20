# astrbot_plugin_fylavvor_hangman

AstrBot 的经典 Hangman（猜词）游戏插件：机器人随机抽一个长度不少于 6 的英文单词，
玩家用字母或整词来猜，6 次机会用完或 1 分钟内无人猜测就公布答案。

## 指令

| 指令 | 说明 |
| --- | --- |
| `/startguess`（别名 `/猜词`） | 开始一轮猜词。当前会话已有未结束的对局时，会提示继续该局 |
| `/guess <字母或单词>`（别名 `/猜`） | 单个字母 → 揭示它在答案中的全部位置；多个字母 → 先查词库，再与答案比较 |
| `/giveup` | 放弃本轮，直接公布答案 |

- 不区分大小写，`/guess D` 与 `/guess d` 等价。
- 猜错字母、猜错单词会消耗 1 次机会（共 6 次）。
- 词库中不存在的单词只提示，不消耗机会。
- 所有字母被揭示或整词猜中即获胜；机会耗尽则公布答案。
- 每次产生实际进展的猜测都会把 1 分钟倒计时重置，超时后自动公布答案。

## 交互示例

```
/startguess
游戏开始！
待猜测词语：？？？？？？？？？？
剩余尝试次数：6
已猜测：

/guess c
成功揭示：c
待猜测词语：？？c？？？？？c？
剩余尝试次数：6
已猜测：c
```

## 词库

- `dict/answers.txt`：答案池，8716 个词（已剔除复数形式）。
- `dict/words.txt`：猜词合法性校验词表，8999 个词（包含全部答案与复数形式）。

两表均为长度 ≥ 6 的纯字母单词，且已统一为小写。替换词表时保持同样的格式
（每行一个单词）即可，答案池必须是校验词表的子集。

答案池不含复数名词：判定依据是 ECDICT 的 `s:` 变形标注（例如 `story` 的 `s:stories`），
共剔除 261 个词；`words.txt` 仍保留这些复数形式，玩家猜它们时按“合法词汇”处理而不是“词库外”。
学科名与集合名词（`aerodynamics`、`mechanics`、`police`、`cattle` 等 11 个）不会被误判为复数，仍保留在答案池。

内置词表由两部分合并而成：

- 基础词表来自 [KyleBing/english-vocabulary](https://github.com/KyleBing/english-vocabulary)（BSD-3-Clause），
  经由 [astrbot_plugin_wordle](https://github.com/Raven95676/astrbot_plugin_wordle) 的 `classic` 词典筛选；
- 六级、雅思、托福词汇来自 [ECDICT](https://github.com/skywind3000/ECDICT)（MIT），
  按 `cet6` / `ielts` / `toefl` 标签提取，各 3981 / 3678 / 5555 词（去重后与基础词表合并）。

## 平台说明

插件只发送纯文本，适用于 OneBot（aiocqhttp）、QQ 官方机器人、Telegram、Discord、Lark 等平台。
群聊中需要 @机器人 或使用唤醒前缀（默认 `/`）；私聊是否带前缀取决于平台配置。

## 版本

当前版本 v1.0.2，完整更新记录见 [CHANGELOG.md](CHANGELOG.md)。
