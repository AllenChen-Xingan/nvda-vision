# NVDA 插件开发实践第六篇： 更进一步，丢掉魔术数字，正则表达式来帮忙 - NVDA 中文站

这是 NVDA 插件开发实践系列文章的第六篇。你可以通过下面的“传送门”查看之前的章节：

*   [第一篇（画饼篇）](https://nvdacn.com/index.php/archives/1296/)
*   [第二篇：预备篇—确定需求，寻找已有方案](https://nvdacn.com/index.php/archives/1319/)
*   [第三篇： 敢想敢做——写出你的第一行代码，控制台不可怕](https://nvdacn.com/index.php/archives/1381/)
*   [第四篇： 开发插件就是把一堆实验代码整理出来](https://nvdacn.com/index.php/archives/1410/)
*   [第五篇： 实现功能了吗？还差点啥？有哪些调试技巧？](https://nvdacn.com/index.php/archives/1411/)

## 前言

大家好呀！上一篇的内容很丰富，尤其调试的部分是重中之重，不知道你掌握了没有呢？

在上一篇中，我们初步实现了读取 VS Code 行号的功能。通过索引 `statusBar.children[12]`，我们成功地获取到了包含行号信息的文本并朗读出来。然而，细心的你可能已经意识到，这种方法存在一个明显的缺陷：**硬编码的索引值 `12` 依赖于状态栏子对象的顺序**。

状态栏的结构并非一成不变。VS Code 的更新、用户自定义设置、甚至不同工作区或文件类型，都可能导致状态栏子对象的数量和排列顺序发生变化。一旦状态栏结构改变，我们硬编码的索引值 `12` 就可能指向错误的子对象，甚至导致程序报错。

为了解决这个问题，我们需要一种更**健壮**的方法来定位包含行号信息的子对象。本篇，我们将引入**正则表达式**，通过**模式匹配**的方式，精确地从状态栏子对象中找到我们需要的行号信息，并学习如何将代码**拆分到单独的函数**中，提高代码的可维护性。

## 索引的脆弱性

让我们再次回顾上一篇的代码片段：

```
@script(gesture="kb:NVDA+Shift+Control+L", description="Report current line in vscode.")
def script_reportLine(self, gesture):
    statusBar = api.getStatusBar()
    ui.message(statusBar.children[12].name)
```

`statusBar.children[12]` 这行代码看似简洁，却隐藏着潜在的风险。设想一下，如果 VS Code 在状态栏中增加/去掉了一个新的图标或信息显示，原本索引为 `12` 的行号信息子对象，其索引可能会变为更大或者更小的值。这时，我们的插件就无法正确读取行号了。

这种依赖索引的硬编码方式，在软件开发中被称为“**魔术数字 (Magic Number)**”。魔术数字降低了代码的可读性和可维护性，使得代码难以理解和修改。我们应该尽量避免在代码中使用魔术数字，而采用更具描述性和灵活性的方法。

## 正则表达式：模式匹配的利器

为了相对可靠地定位行号信息，我们需要一种方法来**识别**状态栏子对象是否包含行号。观察 VS Code 状态栏中行号信息的文本，我们通常会看到类似 "Ln 123, Col 45" 或 "行 456，列 78"（安装了中文语言包以后） 这样的格式。

这些文本都遵循一定的**模式**，我们不妨来找一下规律：以 "Ln" 或 "行" 开头，后跟数字表示行号，再跟 ", " 或 "，" 分隔符，接着是 "Col" 或 "列" 开头，最后是数字表示列号。

**正则表达式 (Regular Expression)** 正是用于描述和匹配文本模式的强大工具。通过编写合适的正则表达式，我们可以精确地匹配包含行号信息的文本，而无需依赖其在状态栏中的位置。

这里的“匹配（Match）”一词，你可能觉得有点陌生，我们就粗浅的理解为某个表达式能够描述某个**文本的规律**，比如正则表达式 `\d+` 可以描述“由一个或多个**数字 (digit)** 组成的字符串”这一规律 (其中 `\d` 就是 **digit** 的缩写，代表数字字符)，像 “123”，“007” 这样的字符串都符合这个规律，可以被它“匹配”到。

那么该如何用正则表达式描述我们在上面找到的规律呢？

Python 内置了 `re` 模块，提供了对正则表达式的支持。要使用正则表达式，首先需要导入 `re` 模块：

```
import re

PATTERN = re.compile(r'(?:Ln|行)\s+(\d+)\s*[,，]\s*(?:Col|列)\s+(\d+)')
```

这行代码定义了一个名为 `PATTERN` 的常量，它存储了一个**编译后的正则表达式对象**。 让我们来逐步解读这个正则表达式：

*   **`r'...'`**: `r` 前缀表示这是一个**原始字符串**（raw string）。在正则表达式中，反斜杠 `\` 经常被用作转义字符。使用原始字符串可以避免 Python 自身对反斜杠的转义，使得正则表达式的编写更加简洁明了。
*   **`(?:Ln|行)`**: 使用**`(?:...)`** 创建了一个**非捕获组**， **`|`** 表示**或**。 这一部分匹配 "Ln" 或 "行" 字符串，但 *不会* 捕获这个匹配结果。我们只需要知道行号前面是 "Ln" 还是 "行"，而不需要单独提取这个 "Ln" 或 "行" 字符串。
*   **`\s+`**: `\s` 匹配任何**空白字符**，包括空格、制表符、换行符等。 **`+`** 表示匹配**一个或多个**前面的字符。所以 `\s+` 匹配一个或多个空白字符。
*   **`(\d+)`**: `\d` 匹配任何**数字字符**（0-9）。 `+` 的含义同上，表示匹配一个或多个数字字符。 **括号 `()`** 创建了一个**捕获组**，用于 *捕获* 匹配到的数字，也就是我们需要的行号。
*   **`\s*`**: `\s` 依然是匹配空白字符，** `*`** 表示匹配**零个或多个**前面的字符。所以 `\s*` 匹配零个或多个空白字符。
*   **`[,，]`**: 使用**方括号 `[]`** 创建一个**字符集**，匹配方括号中任意一个字符。这里匹配半角逗号 "," 或全角逗号 "，"。
*   **(?:Col|列)**: 类似于 `(?:Ln|行)`，匹配 "Col" 或 "列" 字符串，但 *不会* 捕获这个匹配结果。
*   **`\s+`**: 再次匹配一个或多个空白字符。
*   **`(\d+)`**: 再次使用 `(\d+)` 匹配并 *捕获* 列号。

总而言之，这个正则表达式能够匹配包含 "Ln" 或 "行"、行号、", " 或 "，"、"Col" 或 "列"、列号的文本模式，并且能够**捕获**行号和列号这两组数字。

第一次接触的新手，不妨直接照抄，后续可以阅读更多正则表达式的学习资料，现在有了 LLM 写正则表达式，看懂正则表达式的任务完全可以交给 LLM 去做，你只需要大致能看懂，会调试就可以，再也不用头秃啦！

## 使用正则表达式匹配状态栏子对象

有了正则表达式，我们就可以编写一个函数，遍历状态栏的子对象，并使用正则表达式来匹配子对象的文本内容。如果匹配成功，则说明该子对象包含了行号信息。

那么，我们来写一个 `find_sb_child` 函数完成这项任务：

```
def find_sb_child(self, children):
    """
    Finds and returns the first child that matches the pattern in the children list.
    :param children: List of child elements to search through.
    :return: Matched child element or None if no match is found.
    """
    return next((item for item in children if self.PATTERN.search(item.name)), None)
```

让我们来分析一下 `find_sb_child` 函数：

*   `def find_sb_child(self, children):`： 定义函数 `find_sb_child`，接受 `self` 和 `children` 两个参数。`children` 参数是一个状态栏子对象的列表。
*   `return next((...), None)`： 使用 `next` 函数返回迭代器的下一个元素。如果迭代器耗尽，则返回 `None`。
*   `(item for item in children if self.PATTERN.search(item.name))`： 这是一个**生成器表达式 (Generator Expression)**，用于创建一个迭代器。
    *   `for item in children`： 遍历 `children` 列表中的每个子对象 `item`。
    *   `if PATTERN.search(item.name)`： 使用 `self.PATTERN.search(item.name)` 检查子对象 `item` 的 `name` 属性（即文本内容）是否与正则表达式 `self.PATTERN` 匹配。`re.search` 函数在字符串中搜索匹配正则表达式模式的第一个位置，如果找到匹配，则返回一个匹配对象，否则返回 `None`。
*   `next((...), None)`： `next` 函数从生成器表达式返回的迭代器中获取**第一个**匹配成功的子对象。如果遍历完所有子对象都没有找到匹配的，则 `next` 函数返回默认值 `None`。

简而言之，`find_sb_child` 函数的功能是：**在给定的子对象列表中，找到第一个文本内容与 `self.PATTERN` 正则表达式匹配的子对象，并返回该子对象。如果没有找到匹配的子对象，则返回 `None`。**

## 更新 `script_reportLine` 函数

现在，我们可以修改 `script_reportLine` 函数，使用 `find_sb_child` 函数来定位行号信息子对象，并获取其文本内容：

```
@script(gesture="kb:NVDA+Shift+Control+L", description="Report current line in vscode.")
def script_reportLine(self, gesture):
    statusBar = api.getStatusBar()
    if statusBar and statusBar.children: # 确保状态栏对象和子对象列表都存在
        sb_child = self.find_sb_child(statusBar.children)
        if sb_child: # 确保找到了匹配的子对象
            ui.message(sb_child.name)
        else:
            ui.message(_("No line number information found"))
    else:
            ui.message(_("No status bar found"))
```

修改后的 `script_reportLine` 函数，首先获取状态栏对象及其子对象列表。然后，调用 `self.find_sb_child(statusBar.children)` 函数，尝试在子对象列表中找到匹配正则表达式的子对象。

*   如果找到了匹配的子对象 `sb_child`，则使用 `ui.message(sb_child.name)` 朗读其文本内容。
*   如果没有找到匹配的子对象，或者状态栏对象或子对象列表不存在，则使用 `ui.message` 给出相应的提示信息，例如 "未找到行号信息" 或 "未找到状态栏"。

这样的修改，使得我们的插件不再依赖硬编码的索引值，而是通过正则表达式**动态**地查找行号信息子对象，大大提高了插件的**健壮性**和**适应性**。

## 完整的 `AppModule` 代码

结合以上修改，我们得到了更完善的 `AppModule` 代码：

```
import api
import appModuleHandler
import ui
from scriptHandler import script
import re

class AppModule(appModuleHandler.AppModule):
    scriptCategory = "Vscode-line-numbers"
    PATTERN = re.compile(r'(?:Ln|行)\s+(\d+)\s*[,，]\s*(?:Col|列)\s+(\d+)')

    @script(gesture="kb:NVDA+Shift+Control+L", description="Report current line in vscode.")
    def script_reportLine(self, gesture):
        statusBar = api.getStatusBar()
        if statusBar and statusBar.children:
            sb_child = self.find_sb_child(statusBar.children)
            if sb_child:
                ui.message(_(sb_child.name)) # 使用 _() 进行国际化
            else:
                ui.message(_("No line number information found"))
        else:
            ui.message(_("No status bar found"))

    def find_sb_child(self, children):
        """
        Finds and returns the first child that matches the pattern in the children list.
        :param children: List of child elements to search through.
        :return: Matched child element or None if no match is found.
        """
        return next((item for item in children if self.PATTERN.search(item.name)), None)
```

## 总结

在本篇中，我们意识到了上一篇代码中存在的索引硬编码问题，并学习了使用**正则表达式**进行**模式匹配**，从而更健壮地定位状态栏中的行号信息。我们详细解读了正则表达式 `PATTERN` 和 `find_sb_child` 函数，并更新了 `script_reportLine` 函数，使其能够使用正则表达式来查找行号信息子对象。

通过本篇的学习，你掌握了以下知识点：

*   **魔术数字的危害**：了解了硬编码索引值（魔术数字）的弊端。
*   **正则表达式的应用**：学习了如何使用正则表达式进行文本模式匹配，并应用于 NVDA 插件开发中。
*   **插件代码的健壮性**：认识到提高插件代码健壮性的重要性。

一如既往，欢迎你在评论区留下你的反馈和问题。