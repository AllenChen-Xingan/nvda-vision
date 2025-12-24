# NVDA 插件开发实践第七篇： 插件是个什么东西？如何创建插件包？ - NVDA 中文站

这是 NVDA 插件开发实践系列文章的第七篇。你可以通过下面的“传送门”查看之前的章节：

*   [第一篇（画饼篇）](https://nvdacn.com/index.php/archives/1296/)
*   [第二篇：预备篇—确定需求，寻找已有方案](https://nvdacn.com/index.php/archives/1319/)
*   [第三篇： 敢想敢做——写出你的第一行代码，控制台不可怕](https://nvdacn.com/index.php/archives/1381/)
*   [第四篇： 开发插件就是把一堆实验代码整理出来](https://nvdacn.com/index.php/archives/1410/)
*   [第五篇： 实现功能了吗？还差点啥？有哪些调试技巧？](https://nvdacn.com/index.php/archives/1411/)
*   [第六篇： 更进一步，丢掉魔术数字，正则表达式来帮忙](https://nvdacn.com/index.php/archives/1425/)

## 前言

我们在上一篇中进一步完善了我们的代码，目前这个实现已经可以在 VS Code 中通过按下快捷键直接读出状态栏的行列信息了。  
然而，我们目前的代码被保存在 `%appdata%\nvda\scratchpad`目录下，仍然是实验性代码，

## 从头手动创建插件包

你可能已经手痒了，如果我们想将当前的代码分享给其他人，应该如何制作成一个插件包呢？在本篇中，我们一起来学习一下 NVDA 插件包的生成。

### 插件包就是一个遵循约定的 zip 压缩文件

如果你手上有一个 NVDA 插件包，你就可以将其扩展名（.nvda-addon）更改为 .zip 随后用压缩软件将其打开或解压为一堆特定的文件/文件夹。

倘若你已经探索过了，应该总结出以下规律：

1.  插件包内至少包含一个 `manifest.ini` 清单文件。
2.  至少包含以下 appModules、brailleDisplayDrivers、globalPlugins、synthDrivers等常见的插件类型（一个或多个）。
3.  根据压缩包目录结构反向观察：如果你手动创建插件包，压缩以上文件时不应该压缩其父级目录，很重要。

### 插件清单文件

之所以 NVDA 能够将一个压缩文件识别为有效的 NVDA 插件包，除了扩展名以外，正确的目录结构和清单文件是绝对必要的。  
一个清单文件可能包括name、summary、description、author、version、minimumNVDAVersion和lastTestedNVDAVersion等。  
有些是必须的，有些是非必须的，但你无需记忆他们，笔者也并不推荐你手写这些字段，在正式开发过程中清单文件是自动生成的。

### 创建插件包

你可以创建一个名为`manifest.ini`的 UTF-8 编码的文本文档，随后复制以下字段并保存。

```
name = Vscode-line-numbers
summary = "reportVscodeLineNumber"
description = """This addon can be used to easily report the current line and column in vscode."""
author = "NVDACN"
version = 1.0.0
minimumNVDAVersion = 2024.1.0
lastTestedNVDAVersion = 2024.4.2
```

然后将 `%appdata%\nvda\scratchpad` 中的 `appModules` 目录也复制到与 `manifest.ini` 相同的位置。此时 `appModules` 文件夹内应该只包含一个 `code.py`。

最后，选中 manifest.ini 和 `appModules` 两项，创建一个 .zip 压缩包。创建完成后，将扩展名从 '.zip' 改为 “.nvda-addon”，此时如果 NVDA 正在运行，打开该压缩包即可弹出安装向导。  
**注意：在最后这一步，一定要搞清楚目录结构，选中要包含在插件包中的文件/文件夹，而不是直接压缩其父级目录，请务必理解这一点。**

## 社区插件开发模板

你可能已经意识到了，手动创建目录结构，编写清单文件，压缩成插件包，修改扩展名，编写版本号，这些步骤在开发过程中重复且容易出错。  
那么，基于这样的背景，社区内创建了一个插件开发模板，旨在简化插件开发流程——一行命令即可生成插件包。  
使用插件开发模板虽然不是强制性要求，但绝大多数插件开发者都很愿意将其作为插件开发流程的一部分。在本系列教程中，笔者也更推荐使用该模板进行插件的开发和日常维护。

### 设置开发环境

1.  将插件开发模板 clone 到本地： `git clone git@github.com:nvdaaddons/AddonTemplate.git`
2.  安装 python 3.11 选择适用于 Windows 32-位的 3.11.9 或更高版本：[https://www.python.org/downloads/release/python-3117/](https://www.python.org/downloads/release/python-3117/)
3.  使用 pip 安装必须的依赖：
    *   `pip install scons`
    *   `pip install markdown`
4.  下载并安装： GNU Gettext （保持默认安装将自动配置环境变量）： [https://mlocati.github.io/articles/gettext-iconv-windows.html](https://mlocati.github.io/articles/gettext-iconv-windows.html)
5.  下载并安装 Poedit 免费版： [https://poedit.net/download](https://poedit.net/download)

**一般而言，无需在安装时指定版本，如果你愿意，可以了解以下信息：**

*   使用 SCons 4, 版本 4.6.0 或更高版本用于生成插件包： [http://www.scons.org/](http://www.scons.org/)
*   使用 Markdown 3.5.1 或更高版本，用于生成插件文档： [https://pypi.python.org/pypi/Markdown/3.5.1/](https://pypi.python.org/pypi/Markdown/3.5.1/)
*   对于步骤（4）的 GNU Gettext 其实也可以直接使用步骤（5）安装的 Poedit 内置的版本，但你需要手动配置环境变量。
*   Poedit 用于翻译 NVDA 插件。NVDA 对3.5 及更高版本支持更好，可参见 NVDA 用户指南中的相关章节。

### 插件开发模板的目录结构

在你将插件开发模板 `clone` 到本地后，你会看到模板仓库本身包含了一些文件和文件夹。一个使用该模板的典型插件项目结构大致如下：

```
你的插件项目文件夹/
├── .github/             # (可选) 用于 GitHub Actions 自动构建
├── addon/               # 核心！你的插件代码放在这里
│   ├── appModules/      # 应用模块代码（例如我们的 code.py）
│   ├── globalPlugins/   # 全局插件代码
│   ├── synthDrivers/    # 语音合成器驱动代码
│   ├── brailleDisplays/ # 盲文显示器驱动代码
│   ├── doc/             # 插件文档（多语言）
│   │   └── zh_CN/       # 中文文档
│   │       └── readme.md
│   ├── locale/          # 插件翻译文件
│   │   └── zh_CN/       # 中文 UI 翻译
│   │       └── LC_MESSAGES/       # 注意大小写敏感
│   │           └── nvda.po
├── site_scons/          # SCons 构建脚本的辅助模块 (必须)
├── buildVars.py         # 构建变量配置文件 (核心！必须)
├── manifest.ini.tpl     # 清单文件模板 (必须)
├── manifest-translated.ini.tpl # 本地化清单模板 (用于翻译 summary/description)
├── sconstruct           # SCons 主构建脚本 (必须)
├── .gitignore           # (推荐) Git 忽略文件配置
├── .gitattributes       # (推荐) Git 属性配置
├── .pre-commit-config.yaml # (可选) 用于 pre-commit 钩子
└── readme.md            # (推荐) 插件项目的说明文档 (通常需要替换成自己的)
├── ... 还有其他的一些，比如 VS Code 工作区配置，暂不提及
```

**关键点：**

1.  `addon` 文件夹是存放你所有插件 Python 代码、文档 (`doc`) 和翻译文件 (`locale`) 的地方。
2.  根目录下的 `buildVars.py`, `manifest.ini.tpl`, `manifest-translated.ini.tpl`, `sconstruct` 以及 `site_scons` 文件夹是模板的核心构建文件，必须保留。
3.  像 `.github`, `.gitignore` 等是可选的，但对于使用 Git 和 GitHub 进行版本控制和自动化构建非常有帮助，笔者推荐使用这套工作流。

### 使用模板创建我们的 VS Code 行号朗读插件

现在，让我们把之前在 `scratchpad` 里的实验代码，迁移到使用插件开发模板的新项目中。一个推荐且直观的方法是直接复制模板：

1.  **复制模板文件夹：** 将你 `git clone` 下来的整个 `AddonTemplate` 文件夹复制一份。
2.  **重命名文件夹：** 将这个复制出来的文件夹重命名为你想要的插件项目名称，例如 `ReportVscodeLineNumber`。现在，这个文件夹就是你的插件项目根目录了。
3.  **清理（可选但推荐）：** 进入这个重命名的 `ReportVscodeLineNumber` 文件夹。你可能需要删除或修改一些模板自带的根目录文件，比如模板本身的 `README.md`、`LICENSE` 等，稍后替换为你自己项目的信息。
4.  **迁移代码：**
    *   在你的项目文件夹 (`ReportVscodeLineNumber`) 内找到 `addon` 文件夹。
    *   在 `addon` 文件夹内，创建一个名为 `appModules` 的新文件夹。
    *   将之前放在 `%appdata%\nvda\scratchpad\appModules\` 目录下的 `code.py` 文件，**移动**到我们刚刚创建的 `ReportVscodeLineNumber\addon\appModules\` 文件夹内。

现在，你的项目文件结构和代码已经就位。下一步是配置构建信息。

### 配置构建变量 `buildVars.py`

`buildVars.py` 文件是插件开发模板的核心。它是一个 Python 文件，定义了构建插件所需的所有元数据和配置。SCons 构建脚本 (`sconstruct`) 会读取这个文件来生成 `manifest.ini` 清单文件、确定最终插件包的名称等。

打开你项目根目录下的 `buildVars.py` 文件，你会看到里面定义了很多变量。对于我们这个简单的插件，主要需要关注和修改以下几个部分：

**1\. `addon_info` 字典：** 这是最核心的部分，包含了插件的基本信息。

```
# -*- coding: UTF-8 -*-
# ... (文件顶部的注释和 fake _ 函数保持不变) ...

# Add-on information variables
addon_info = {
    # add-on Name/identifier, internal for NVDA (插件内部名称，驼峰式，必须唯一)
    "addon_name": "reportVscodeLineNumber",
    # Add-on summary/title, usually the user visible name of the add-on (插件摘要，显示在插件商店和安装界面，可翻译)
    # Translators: Summary/title for this add-on ...
    "addon_summary": _("Report VS Code Line Number"),
    # Add-on description (插件详细描述，可翻译)
    # Translators: Long description ...
    "addon_description": _("""Provides a command to report the current line and column number from the VS Code status bar."""),
    # version (插件版本号，推荐遵循 major.minor.patch 格式)
    "addon_version": "1.0.0",
    # Author(s) (插件作者信息)
    "addon_author": u"NVDACN <support@nvdacn.com>",
    # URL for the add-on documentation support (插件主页或信息页面 URL)
    "addon_url": "https://nvdacn.com/",
    # URL for the add-on repository where the source code can be found (插件源代码仓库 URL)
    "addon_sourceURL": "https://github.com/nvdacn/reportVscodeLineNumber", # 请替换为你自己的仓库地址或留空
    # Documentation file name (插件文档文件名，通常由 readme.md 生成)
    "addon_docFileName": "readme.html",
    # Minimum NVDA version supported (插件兼容的最低 NVDA 版本)
    "addon_minimumNVDAVersion": "2024.1",
    # Last NVDA version supported/tested (插件最后测试兼容的 NVDA 版本)
    "addon_lastTestedNVDAVersion": "2024.4",
    # Add-on update channel (插件更新通道，stable/dev/beta 或 None)
    "addon_updateChannel": "stable",
    # Add-on license such as GPL 2 (插件许可证类型)
    "addon_license": "GPL v2", # NVDA 插件通常使用 GPL v2
    # URL for the license document the ad-on is licensed under (插件许可证原文 URL)
    "addon_licenseURL": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
}

# ... (其他变量定义如下) ...
```

**2\. `pythonSources` 列表：** 定义了插件包含哪些 Python 源文件。对于我们的插件，只有一个 `code.py` 文件在 `appModules` 目录下。

```
# Define the python files that are the sources of your add-on.
pythonSources = ["addon/appModules/code.py"] # 列出你的 Python 文件路径
```

**3\. `i18nSources` 列表：** 定义了哪些文件需要被扫描以提取可翻译的字符串。通常它包含 `pythonSources` 和 `buildVars.py` 本身。

```
# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources + ["buildVars.py"] # 通常保持这样即可
```

**4\. `excludedFiles` 列表：** 定义了在最终打包时需要排除哪些文件。

```
# Files that will be ignored when building the nvda-addon file
excludedFiles = [] # 模板默认可能包含排除 .po/.pot 的规则，如果没有特殊需求，保持默认或为空即可
```

**5\. `baseLanguage` 变量：** 指定插件的原始语言。

```
# Base language for the NVDA add-on
baseLanguage = "en" # 笔者推荐以英语为基础语言，便于其他社区的用户将我们的插件本地化为更多语言
```

**请注意：**

*   你需要将 `addon_info` 字典中的示例值替换为你插件的实际信息。
*   `addon_minimumNVDAVersion` 和 `addon_lastTestedNVDAVersion` 非常重要，请根据你实际使用的 NVDA API 和测试情况填写。
*   `pythonSources` 必须准确列出你所有的 Python 代码文件。
*   `baseLanguage` 如前所述，笔者推荐以英语编写。然而还是看你的喜好。
*   模板中还有 `markdownExtensions`, `brailleTables`, `symbolDictionaries` 等变量，用于更高级的功能（如支持 Markdown 表格、自定义盲文表、自定义符号字典），对于我们这个简单插件，保持默认的空列表或空字典即可。

**详细了解 `buildVars.py` 中所有变量的含义和配置方法，请务必仔细阅读插件开发模板仓库根目录下的 `readme.md` 文件。** 那里有最权威和全面的解释。

### 打包你的第一个插件包 (`scons`)

当你配置好 `buildVars.py` 文件后，生成插件包就变得非常简单了。

1.  **打开命令行：** 打开你的命令提示符 (cmd)、PowerShell 或 Git Bash。
    
2.  **切换目录：** 使用 `cd` 命令切换到你的插件项目根目录（也就是你重命名后的那个 `ReportVscodeLineNumber` 文件夹）。如果你恰好位于该目录，可以直接在文件资源管理器的地址栏输入 `cmd` 并回车，以在命令行中打开当前目录。
    
3.  **运行 SCons：** 输入以下命令并回车：
    
    ```
    scons
    ```
    
    SCons 会开始执行构建过程。它的工作流程大概如下：
    
    *   读取 `buildVars.py` 获取信息。
    *   根据 `manifest.ini.tpl` 和 `buildVars.py` 生成 `addon/manifest.ini` 文件。
    *   （如果存在）编译 `.po` 文件为 `.mo` 文件。
    *   （如果存在）将 Markdown 文档 (`.md`) 转换为 HTML 文档 (`.html`)。
    *   收集 `pythonSources` 列出的文件以及 `addon` 目录下的其他必要文件（并根据 `excludedFiles` 进行排除）。
    *   将收集到的文件打包成一个 `.zip` 文件。
    *   根据 `buildVars.py` 中的 `addon_name` 和 `addon_version` 将 `.zip` 文件重命名为 `.nvda-addon` 文件，例如 `nvda-reportVscodeLineNumber-1.0.0.nvda-addon`。
4.  **检查结果：** 构建成功后，你会在项目根目录下找到生成的 `.nvda-addon` 文件。现在你可以双击这个文件来安装你的插件了！
    

**如果构建失败，请根据命令行中的错误信息调整`buildVars.py`中的内容，或者检查目录结构、文件命名（大小写敏感）是否正确。**

### 自定义构建版本 (`scons` 命令行参数)

有时，你可能想在不修改 `buildVars.py` 的情况下，临时生成一个特定版本的插件包，例如一个开发版。`scons` 命令支持一些命令行参数来实现这一点：

*   **指定版本号:**
    
    ```
    scons version=1.1.0-beta1
    ```
    
    这会覆盖 `buildVars.py` 中定义的 `addon_version`。
    
*   **生成开发版:**
    
    ```
    scons dev=True
    ```
    
    这通常会自动将版本号设置为当前日期（例如 `20250331.1.0`）这对于快速测试构建非常有用。
    

**同样，关于所有可用的 `scons` 命令行参数，请参考插件开发模板的 `readme.md` 文件。**

## 总结

在本篇中，我们了解了 NVDA 插件包的本质（一个特殊结构的 ZIP 文件），并通过实例学习了如何手动创建插件包。更重要的是，我们引入了社区维护的 NVDA 插件开发模板，它极大地简化了插件的构建、打包和维护流程。我们重点学习了如何使用这个模板来组织项目文件（通过复制并重命名模板文件夹），如何根据实际模板内容配置核心的 `buildVars.py` 文件，以及如何使用 `scons` 命令来生成插件包。

掌握了插件模板的使用，你就拥有了一个更规范、更高效的插件开发工作流。现在，你可以轻松地将你的 VS Code 行号朗读插件分享给朋友了！

如果你希望更加规范的进行软件开发，你应该学习一些版本控制的知识了，比如 git 这几乎是开发者的一项必备技能。如果文中还有一些你不明白的术语，不妨动手查一下吧！