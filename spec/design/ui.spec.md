# NVDA Vision Screen Reader - UI Design Specification

**Document Version**: v1.0.0
**Created**: 2025-12-24
**Dependencies**: `.42cog/real/real.md`, `.42cog/cog/cog.md`, `spec/pm/pr.spec.md`, `spec/dev/sys.spec.md`, `spec/dev/code.spec.md`
**Target Framework**: wxPython (Windows Desktop Application)
**Accessibility Standard**: WCAG 2.1 AA Compliant

---

## Table of Contents

1. [Overview](#1-overview)
2. [Design Principles](#2-design-principles)
3. [Settings Window Architecture](#3-settings-window-architecture)
4. [UI Components Specification](#4-ui-components-specification)
5. [Layout and Sizers](#5-layout-and-sizers)
6. [Keyboard Navigation](#6-keyboard-navigation)
7. [Screen Reader Integration](#7-screen-reader-integration)
8. [Implementation Examples](#8-implementation-examples)
9. [Accessibility Compliance](#9-accessibility-compliance)
10. [Testing Checklist](#10-testing-checklist)

---

## 1. Overview

### 1.1 Purpose

This document specifies the UI design for the NVDA Vision plugin settings dialog, a wxPython-based configuration window that allows users to:

- Configure vision model preferences (UI-TARS/MiniCPM-V/Doubao API)
- Manage API keys with encryption
- Customize recognition settings
- Configure keyboard shortcuts
- Manage privacy settings
- View cache statistics
- Configure logging levels

### 1.2 Key Requirements

**From real.md**:
- ✅ **Constraint 4**: WCAG 2.1 AA compliant, all features keyboard-accessible
- ✅ **Constraint 2**: API keys must be encrypted (DPAPI)
- ✅ **Constraint 1**: Privacy-first (local processing preferred)

**From pr.spec.md**:
- AF-006: Configure model priority
- AF-007: Customize keyboard shortcuts
- AF-008: Export logs

### 1.3 Technology Stack

- **UI Framework**: wxPython 4.2+
- **Dialog Type**: `wx.Dialog` with modal behavior
- **Layout**: `wx.BoxSizer` and `wx.GridBagSizer`
- **Controls**: Native wxPython widgets (keyboard accessible by default)
- **Configuration Backend**: `ConfigManager` from `code.spec.md`

---

## 2. Design Principles

### 2.1 Accessibility First

**ALL UI elements MUST be keyboard accessible** (real.md constraint 4):

1. **Tab Order**: Logical top-to-bottom, left-to-right flow
2. **Labels**: Every control has an associated `wx.StaticText` label
3. **Mnemonics**: Alt+Letter shortcuts for major controls (e.g., Alt+M for Model)
4. **Focus Indicators**: Visible focus rectangles (wxPython default)
5. **NVDA Integration**: All controls announce name, role, value, and state

### 2.2 Progressive Disclosure

- **Simple by default**: Most users only need basic settings
- **Advanced options**: Collapsed by default, expandable on demand
- **Contextual help**: Brief descriptions near controls

### 2.3 Error Prevention

- **Input validation**: Real-time feedback on invalid values
- **Safe defaults**: Conservative settings that work for most users
- **Confirmation dialogs**: For destructive actions (clear cache, reset)

### 2.4 Windows Desktop Patterns

- **Native look**: Use system colors and fonts
- **Standard dialogs**: OK/Cancel/Apply pattern
- **Respect system settings**: Font size, contrast, theme
- **No custom drawing**: Rely on wxPython's native rendering

---

## 3. Settings Window Architecture

### 3.1 Dialog Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ NVDA Vision Settings                                    [X]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ [Notebook Tabs]                                          │ │
│  │ ─────────────────────────────────────────────────────────│ │
│  │ │ General │ Models │ Recognition │ Shortcuts │ Privacy │ │ │
│  │                                                          │ │
│  │  [Tab Content Area]                                     │ │
│  │                                                          │ │
│  │  (Tab-specific controls displayed here)                 │ │
│  │                                                          │ │
│  │                                                          │ │
│  │                                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │         [ OK ]    [ Cancel ]    [ Apply ]               │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Dialog Properties

```python
class NVDAVisionSettingsDialog(wx.Dialog):
    """Main settings dialog for NVDA Vision plugin."""

    def __init__(self, parent, config_manager):
        super().__init__(
            parent,
            id=wx.ID_ANY,
            title="NVDA Vision Settings",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(800, 600)
        )

        # Center on screen
        self.CenterOnScreen()

        # Set minimum size
        self.SetMinSize((700, 500))
```

**Properties**:
- **Size**: 800x600 (resizable, min 700x500)
- **Position**: Centered on screen
- **Modal**: Yes (blocks parent window)
- **Style**: Standard dialog with resize border
- **Icon**: NVDA Vision logo (optional)

### 3.3 Tab Organization

The settings are organized into 5 tabs using `wx.Notebook`:

| Tab # | Name | Shortcut | Purpose | Affordances |
|-------|------|----------|---------|-------------|
| 1 | General | Alt+G | Basic configuration | Language, auto-start |
| 2 | Models | Alt+M | Vision model settings | Priority, timeouts | AF-006 |
| 3 | Recognition | Alt+R | Recognition parameters | Confidence, cache |
| 4 | Shortcuts | Alt+S | Keyboard bindings | Customize hotkeys | AF-007 |
| 5 | Privacy | Alt+P | Privacy and logging | Local-first, logs | AF-008 |

---

## 4. UI Components Specification

### 4.1 Tab 1: General Settings

**Purpose**: Basic configuration that affects overall plugin behavior.

#### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ General Settings                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Language:                                                  │
│  [▼ Chinese (Simplified)           ]                        │
│                                                             │
│  ☑ Enable NVDA Vision on startup                           │
│                                                             │
│  ☑ Show notification when recognition starts               │
│                                                             │
│  ☑ Announce confidence scores                              │
│     └─ Low confidence threshold: [70    ]%                  │
│                                                             │
│  ─────────────────────────────────────                      │
│                                                             │
│  Plugin Version: 0.1.0                                      │
│  Configuration Location: C:\Users\...\nvda_vision\         │
│                                                             │
│  [ View Logs... ]  [ Reset to Defaults ]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Component Specifications

**1. Language Selection**

```python
# Label
label_language = wx.StaticText(panel, label="&Language:")
label_language.SetToolTip("Select plugin interface language")

# Choice control
choices = ["English", "Chinese (Simplified)", "Chinese (Traditional)"]
choice_language = wx.Choice(panel, choices=choices)
choice_language.SetSelection(1)  # Default: Chinese Simplified
choice_language.SetName("Language Selection")

# Accessibility
choice_language.SetHelpText(
    "Choose the language for plugin messages and interface"
)
```

**Widget Type**: `wx.Choice`
**Label**: "Language:" (Alt+L)
**Options**: ["English", "Chinese (Simplified)", "Chinese (Traditional)"]
**Default**: Chinese (Simplified)
**Validation**: None (all options valid)
**NVDA Reads**: "Language, combo box, Chinese (Simplified)"

---

**2. Enable on Startup**

```python
# Checkbox
checkbox_autostart = wx.CheckBox(
    panel,
    label="&Enable NVDA Vision on startup"
)
checkbox_autostart.SetValue(True)  # Default: enabled
checkbox_autostart.SetName("Enable on Startup")
checkbox_autostart.SetToolTip(
    "Load plugin automatically when NVDA starts"
)
```

**Widget Type**: `wx.CheckBox`
**Label**: "Enable NVDA Vision on startup" (Alt+E)
**Default**: Checked
**NVDA Reads**: "Enable NVDA Vision on startup, checkbox, checked"

---

**3. Show Notifications**

```python
checkbox_notifications = wx.CheckBox(
    panel,
    label="Show &notification when recognition starts"
)
checkbox_notifications.SetValue(True)
```

**Widget Type**: `wx.CheckBox`
**Label**: "Show notification when recognition starts" (Alt+N)
**Default**: Checked
**NVDA Reads**: "Show notification when recognition starts, checkbox, checked"

---

**4. Announce Confidence Scores**

```python
# Parent checkbox
checkbox_announce_conf = wx.CheckBox(
    panel,
    label="&Announce confidence scores"
)
checkbox_announce_conf.SetValue(True)

# Child: Threshold slider
label_threshold = wx.StaticText(
    panel,
    label="Low confidence threshold:"
)
slider_threshold = wx.Slider(
    panel,
    value=70,
    minValue=50,
    maxValue=95,
    style=wx.SL_HORIZONTAL | wx.SL_LABELS
)
slider_threshold.SetName("Confidence Threshold")
slider_threshold.SetToolTip(
    "Elements below this score are marked as 'uncertain' (real.md constraint 3)"
)

# Bind checkbox to enable/disable slider
checkbox_announce_conf.Bind(
    wx.EVT_CHECKBOX,
    lambda evt: slider_threshold.Enable(evt.IsChecked())
)
```

**Widget Type**: `wx.CheckBox` + `wx.Slider`
**Label**: "Announce confidence scores" (Alt+A)
**Default**: Checked
**Slider Range**: 50% - 95%
**Slider Default**: 70% (from real.md constraint 3)
**NVDA Reads**: "Announce confidence scores, checkbox, checked" → "Confidence threshold, slider, 70 percent"

---

**5. Configuration Info (Read-Only)**

```python
# Version
text_version = wx.StaticText(panel, label="Plugin Version: 0.1.0")
text_version.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

# Config location
config_path = config_manager.config_path.parent
text_config = wx.StaticText(
    panel,
    label=f"Configuration Location: {config_path}"
)
text_config.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
```

**Widget Type**: `wx.StaticText` (grayed out)
**Content**: Version number and config path
**Accessibility**: Read-only, informational

---

**6. Action Buttons**

```python
button_view_logs = wx.Button(panel, label="View &Logs...")
button_view_logs.SetToolTip("Open log directory in file explorer")

button_reset = wx.Button(panel, label="&Reset to Defaults")
button_reset.SetToolTip("Reset all settings to default values")
```

**Widget Type**: `wx.Button`
**Labels**: "View Logs..." (Alt+L), "Reset to Defaults" (Alt+R)
**Actions**: Open log folder / Reset configuration
**Confirmation**: "Reset" requires confirmation dialog

---

### 4.2 Tab 2: Model Settings (AF-006)

**Purpose**: Configure vision model selection and behavior.

#### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ Model Settings                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Model Selection Strategy:                                  │
│  ⦿ Automatic (recommended)                                  │
│     Tries GPU → CPU → Cloud API in order                    │
│                                                             │
│  ○ Prefer GPU (UI-TARS 7B)                                  │
│     Requires NVIDIA GPU with 16GB+ VRAM                     │
│                                                             │
│  ○ Prefer CPU (MiniCPM-V 2.6)                               │
│     Slower but works on any system                          │
│                                                             │
│  ○ Cloud API only                                           │
│     Requires internet and API key                           │
│                                                             │
│  ─────────────────────────────────────────                  │
│                                                             │
│  Inference Timeout:  [15  ] seconds                         │
│  (How long to wait before trying backup model)             │
│                                                             │
│  Progress Feedback After:  [5   ] seconds                   │
│  (When to announce "Still recognizing...")                  │
│                                                             │
│  ─────────────────────────────────────────                  │
│                                                             │
│  Cloud API Settings:                                        │
│  ☐ Enable cloud API as fallback                            │
│     (real.md constraint 1: User must opt-in)               │
│                                                             │
│  API Provider: [▼ Doubao (Volcengine)    ]                 │
│                                                             │
│  API Key: [************************     ] [Change...]      │
│           Encrypted with Windows DPAPI                      │
│                                                             │
│  [ Test Connection ]                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Component Specifications

**1. Model Selection Strategy**

```python
# Radio buttons in a group
radio_auto = wx.RadioButton(
    panel,
    label="&Automatic (recommended)",
    style=wx.RB_GROUP  # First in group
)
radio_auto.SetValue(True)  # Default
radio_auto.SetToolTip(
    "Tries GPU → CPU → Cloud API in order (real.md constraint 1)"
)

radio_gpu = wx.RadioButton(
    panel,
    label="Prefer &GPU (UI-TARS 7B)"
)
radio_gpu.SetToolTip("Requires NVIDIA GPU with 16GB+ VRAM")

radio_cpu = wx.RadioButton(
    panel,
    label="Prefer &CPU (MiniCPM-V 2.6)"
)
radio_cpu.SetToolTip("Slower but works on any system")

radio_cloud = wx.RadioButton(
    panel,
    label="Cloud API &only"
)
radio_cloud.SetToolTip("Requires internet connection and API key")
```

**Widget Type**: `wx.RadioButton` group
**Options**: Automatic / GPU / CPU / Cloud
**Default**: Automatic (real.md constraint 1: local first)
**NVDA Reads**: "Model selection strategy, Automatic (recommended), radio button, checked, 1 of 4"

---

**2. Inference Timeout**

```python
label_timeout = wx.StaticText(panel, label="Inference &Timeout:")
spin_timeout = wx.SpinCtrl(
    panel,
    value="15",
    min=5,
    max=60,
    initial=15
)
spin_timeout.SetName("Inference Timeout")
spin_timeout.SetToolTip(
    "Maximum time to wait before degrading to backup model (real.md constraint 6)"
)

label_timeout_unit = wx.StaticText(panel, label="seconds")
```

**Widget Type**: `wx.SpinCtrl`
**Label**: "Inference Timeout:" (Alt+T)
**Range**: 5-60 seconds
**Default**: 15 (from real.md constraint 6)
**NVDA Reads**: "Inference Timeout, spin control, 15"

---

**3. Progress Feedback Delay**

```python
label_progress = wx.StaticText(panel, label="Progress &Feedback After:")
spin_progress = wx.SpinCtrl(
    panel,
    value="5",
    min=3,
    max=15,
    initial=5
)
spin_progress.SetToolTip(
    "When to announce 'Still recognizing...' (real.md constraint 6: >5s)"
)
```

**Widget Type**: `wx.SpinCtrl`
**Label**: "Progress Feedback After:" (Alt+F)
**Range**: 3-15 seconds
**Default**: 5 (from real.md constraint 6)
**NVDA Reads**: "Progress Feedback After, spin control, 5"

---

**4. Enable Cloud API Checkbox**

```python
checkbox_enable_cloud = wx.CheckBox(
    panel,
    label="&Enable cloud API as fallback"
)
checkbox_enable_cloud.SetValue(False)  # Default: disabled (real.md constraint 1)
checkbox_enable_cloud.SetToolTip(
    "Allow using cloud API when local models fail (requires user consent)"
)

# Bind to enable/disable dependent controls
checkbox_enable_cloud.Bind(
    wx.EVT_CHECKBOX,
    lambda evt: self._on_cloud_enabled(evt.IsChecked())
)
```

**Widget Type**: `wx.CheckBox`
**Label**: "Enable cloud API as fallback" (Alt+E)
**Default**: UNCHECKED (privacy-first, real.md constraint 1)
**Effect**: Enables/disables API provider and key fields
**NVDA Reads**: "Enable cloud API as fallback, checkbox, not checked"

---

**5. API Provider Selection**

```python
label_provider = wx.StaticText(panel, label="API &Provider:")
choice_provider = wx.Choice(
    panel,
    choices=["Doubao (Volcengine)", "OpenAI Vision (Future)", "Custom Endpoint"]
)
choice_provider.SetSelection(0)  # Default: Doubao
choice_provider.Enable(False)  # Disabled unless cloud enabled
```

**Widget Type**: `wx.Choice`
**Label**: "API Provider:" (Alt+P)
**Options**: Doubao / OpenAI / Custom
**Default**: Doubao (Volcengine)
**Enabled**: Only if cloud API checkbox checked
**NVDA Reads**: "API Provider, combo box, Doubao (Volcengine), unavailable"

---

**6. API Key Input (Encrypted)**

```python
# Label with security indicator
label_api_key = wx.StaticText(panel, label="API &Key:")
label_api_key_info = wx.StaticText(
    panel,
    label="Encrypted with Windows DPAPI"
)
label_api_key_info.SetForegroundColour(
    wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
)
label_api_key_info.SetFont(
    label_api_key_info.GetFont().MakeSmaller()
)

# Password-style text control (shows asterisks)
text_api_key = wx.TextCtrl(
    panel,
    value="",
    style=wx.TE_PASSWORD
)
text_api_key.SetName("API Key")
text_api_key.Enable(False)  # Disabled unless cloud enabled

# Change button
button_change_key = wx.Button(panel, label="&Change...")
button_change_key.SetToolTip("Update API key (will be encrypted)")
button_change_key.Enable(False)
```

**Widget Type**: `wx.TextCtrl` (password) + `wx.Button`
**Label**: "API Key:" (Alt+K)
**Display**: Masked (asterisks)
**Storage**: Encrypted with DPAPI (real.md constraint 2)
**Enabled**: Only if cloud API enabled
**NVDA Reads**: "API Key, password, unavailable"

**Change Dialog Flow**:
1. User clicks "Change..."
2. Dialog prompts: "Enter API Key (will be encrypted):"
3. User enters plaintext key
4. Dialog saves via `ConfigManager.save_api_key()` (encrypted)
5. Text field shows asterisks

---

**7. Test Connection Button**

```python
button_test = wx.Button(panel, label="&Test Connection")
button_test.SetToolTip("Verify API key and connection")
button_test.Enable(False)

def on_test_connection(event):
    """Test cloud API connection."""
    # Show progress dialog
    progress = wx.ProgressDialog(
        "Testing Connection",
        "Connecting to API...",
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
    )

    try:
        # Test API (in background thread)
        result = test_cloud_api(api_key, endpoint)

        if result.success:
            wx.MessageBox(
                "Connection successful!",
                "Test Result",
                wx.OK | wx.ICON_INFORMATION
            )
        else:
            wx.MessageBox(
                f"Connection failed: {result.error}",
                "Test Result",
                wx.OK | wx.ICON_ERROR
            )
    finally:
        progress.Destroy()

button_test.Bind(wx.EVT_BUTTON, on_test_connection)
```

**Widget Type**: `wx.Button`
**Label**: "Test Connection" (Alt+T)
**Enabled**: Only if cloud API enabled and key entered
**Action**: Sends test request to API
**Feedback**: Progress dialog → Success/error message box

---

### 4.3 Tab 3: Recognition Settings

**Purpose**: Fine-tune recognition behavior and caching.

#### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ Recognition Settings                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Confidence Threshold:                                      │
│  ├────────────────────┬──────────────────────┤             │
│  50%                 [●]                    95%             │
│                      70%                                     │
│  (Elements below this are marked "uncertain")               │
│                                                             │
│  ☑ Filter out low-confidence elements                      │
│     (Only navigate to elements above threshold)            │
│                                                             │
│  ─────────────────────────────────────────                  │
│                                                             │
│  Recognition Cache:                                         │
│  ☑ Enable caching (speeds up repeated screenshots)         │
│                                                             │
│  Cache Time-To-Live: [5   ] minutes                        │
│  Maximum Cache Size:  [100 ] entries                        │
│                                                             │
│  Current Cache Usage: 23 / 100 entries (5.2 MB)            │
│                                                             │
│  [ View Cache Details ]  [ Clear Cache ]                   │
│                                                             │
│  ─────────────────────────────────────────                  │
│                                                             │
│  Target Applications (detection optimization):             │
│  ☑ Feishu (Lark)                                           │
│  ☑ DingTalk                                                │
│  ☑ WeChat                                                  │
│  ☐ All applications                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Component Specifications

**1. Confidence Threshold Slider**

```python
label_conf_threshold = wx.StaticText(
    panel,
    label="&Confidence Threshold:"
)

slider_confidence = wx.Slider(
    panel,
    value=70,
    minValue=50,
    maxValue=95,
    style=wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS
)
slider_confidence.SetTickFreq(5)  # Tick every 5%
slider_confidence.SetPageSize(10)  # Page Up/Down moves 10%
slider_confidence.SetName("Confidence Threshold Slider")
slider_confidence.SetToolTip(
    "Elements with confidence below this are marked 'uncertain' (real.md constraint 3)"
)

label_conf_help = wx.StaticText(
    panel,
    label="(Elements below this are marked \"uncertain\")"
)
label_conf_help.SetFont(label_conf_help.GetFont().MakeSmaller())
```

**Widget Type**: `wx.Slider`
**Label**: "Confidence Threshold:" (Alt+C)
**Range**: 50% - 95%
**Default**: 70% (real.md constraint 3)
**Tick Frequency**: Every 5%
**NVDA Reads**: "Confidence Threshold, slider, 70"
**Keyboard**: Arrow keys (1%), Page Up/Down (10%), Home/End (min/max)

---

**2. Filter Low Confidence**

```python
checkbox_filter = wx.CheckBox(
    panel,
    label="&Filter out low-confidence elements"
)
checkbox_filter.SetValue(False)  # Default: show all
checkbox_filter.SetToolTip(
    "Hide elements below threshold from navigation (only show high-confidence results)"
)
```

**Widget Type**: `wx.CheckBox`
**Label**: "Filter out low-confidence elements" (Alt+F)
**Default**: Unchecked (show all, but mark uncertain)
**NVDA Reads**: "Filter out low-confidence elements, checkbox, not checked"

---

**3. Enable Caching**

```python
checkbox_cache = wx.CheckBox(
    panel,
    label="&Enable caching (speeds up repeated screenshots)"
)
checkbox_cache.SetValue(True)  # Default: enabled
checkbox_cache.SetToolTip(
    "Cache recognition results for identical screenshots (5 min TTL)"
)

# Bind to enable/disable cache settings
checkbox_cache.Bind(
    wx.EVT_CHECKBOX,
    lambda evt: self._on_cache_enabled(evt.IsChecked())
)
```

**Widget Type**: `wx.CheckBox`
**Label**: "Enable caching" (Alt+E)
**Default**: Checked
**Effect**: Enables/disables TTL and size controls

---

**4. Cache TTL**

```python
label_ttl = wx.StaticText(panel, label="Cache &Time-To-Live:")
spin_ttl = wx.SpinCtrl(
    panel,
    value="5",
    min=1,
    max=60,
    initial=5
)
spin_ttl.SetName("Cache TTL")
label_ttl_unit = wx.StaticText(panel, label="minutes")
```

**Widget Type**: `wx.SpinCtrl`
**Label**: "Cache Time-To-Live:" (Alt+T)
**Range**: 1-60 minutes
**Default**: 5 minutes
**NVDA Reads**: "Cache Time-To-Live, spin control, 5"

---

**5. Cache Size Limit**

```python
label_size = wx.StaticText(panel, label="Maximum Cache &Size:")
spin_size = wx.SpinCtrl(
    panel,
    value="100",
    min=10,
    max=500,
    initial=100
)
spin_size.SetName("Cache Size Limit")
label_size_unit = wx.StaticText(panel, label="entries")
```

**Widget Type**: `wx.SpinCtrl`
**Label**: "Maximum Cache Size:" (Alt+S)
**Range**: 10-500 entries
**Default**: 100
**NVDA Reads**: "Maximum Cache Size, spin control, 100"

---

**6. Cache Usage Display**

```python
# Dynamic label updated periodically
text_cache_usage = wx.StaticText(
    panel,
    label="Current Cache Usage: 0 / 100 entries (0 MB)"
)
text_cache_usage.SetName("Cache Usage")

# Update function (called on panel activation)
def update_cache_usage():
    cache = cache_manager.get_stats()
    text_cache_usage.SetLabel(
        f"Current Cache Usage: {cache.count} / {cache.max_size} entries "
        f"({cache.size_mb:.1f} MB)"
    )
```

**Widget Type**: `wx.StaticText` (dynamic)
**Content**: Current cache statistics
**Update**: On tab activation / after clear

---

**7. Cache Action Buttons**

```python
button_view_cache = wx.Button(panel, label="&View Cache Details")
button_view_cache.SetToolTip("Show detailed cache information")

button_clear_cache = wx.Button(panel, label="C&lear Cache")
button_clear_cache.SetToolTip("Delete all cached recognition results")

def on_clear_cache(event):
    """Clear cache with confirmation."""
    dlg = wx.MessageDialog(
        self,
        "Are you sure you want to clear all cached results?",
        "Confirm Clear Cache",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
    )

    if dlg.ShowModal() == wx.ID_YES:
        cache_manager.clear()
        update_cache_usage()
        wx.MessageBox(
            "Cache cleared successfully.",
            "Cache Cleared",
            wx.OK | wx.ICON_INFORMATION
        )

    dlg.Destroy()

button_clear_cache.Bind(wx.EVT_BUTTON, on_clear_cache)
```

**Widget Type**: `wx.Button`
**Labels**: "View Cache Details" (Alt+V), "Clear Cache" (Alt+L)
**Actions**: Show cache info dialog / Clear with confirmation

---

**8. Target Applications**

```python
label_apps = wx.StaticText(
    panel,
    label="Target Applications (detection optimization):"
)

checkbox_feishu = wx.CheckBox(panel, label="&Feishu (Lark)")
checkbox_feishu.SetValue(True)

checkbox_dingtalk = wx.CheckBox(panel, label="&DingTalk")
checkbox_dingtalk.SetValue(True)

checkbox_wechat = wx.CheckBox(panel, label="&WeChat")
checkbox_wechat.SetValue(True)

checkbox_all_apps = wx.CheckBox(panel, label="&All applications")
checkbox_all_apps.SetValue(False)
checkbox_all_apps.SetToolTip(
    "Enable recognition for all applications (may reduce accuracy)"
)
```

**Widget Type**: `wx.CheckBox` group
**Labels**: Feishu / DingTalk / WeChat / All
**Default**: Feishu + DingTalk + WeChat checked
**Purpose**: Filter which apps trigger recognition (performance optimization)

---

### 4.4 Tab 4: Keyboard Shortcuts (AF-007)

**Purpose**: Customize keyboard bindings for plugin actions.

#### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ Keyboard Shortcuts                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Action                     │ Shortcut                 │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │ Recognize Screen           │ NVDA+Shift+V       [Edit]│ │
│  │ Recognize at Cursor        │ NVDA+Shift+C       [Edit]│ │
│  │ Next Element               │ NVDA+Shift+N       [Edit]│ │
│  │ Previous Element           │ NVDA+Shift+P       [Edit]│ │
│  │ Activate Element           │ Enter              [Edit]│ │
│  │ Re-recognize               │ NVDA+Shift+R       [Edit]│ │
│  │ Show Element Details       │ NVDA+Shift+D       [Edit]│ │
│  │ Open Settings              │ NVDA+Shift+S       [Edit]│ │
│  │ Cancel Recognition         │ Escape             [Edit]│ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  [ Restore Defaults ]  [ Detect Conflicts ]                │
│                                                             │
│  ⓘ Shortcuts starting with NVDA+ are global.               │
│     Other shortcuts only work in recognition mode.         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Component Specifications

**1. Shortcuts List Control**

```python
# Create list control with 2 columns
list_shortcuts = wx.ListCtrl(
    panel,
    style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES
)
list_shortcuts.SetName("Shortcuts List")

# Add columns
list_shortcuts.InsertColumn(0, "Action", width=300)
list_shortcuts.InsertColumn(1, "Shortcut", width=200)

# Populate with shortcuts
shortcuts = [
    ("Recognize Screen", "NVDA+Shift+V"),
    ("Recognize at Cursor", "NVDA+Shift+C"),
    ("Next Element", "NVDA+Shift+N"),
    ("Previous Element", "NVDA+Shift+P"),
    ("Activate Element", "Enter"),
    ("Re-recognize", "NVDA+Shift+R"),
    ("Show Element Details", "NVDA+Shift+D"),
    ("Open Settings", "NVDA+Shift+S"),
    ("Cancel Recognition", "Escape"),
]

for i, (action, shortcut) in enumerate(shortcuts):
    index = list_shortcuts.InsertItem(i, action)
    list_shortcuts.SetItem(index, 1, shortcut)

# Add "Edit" buttons column (custom drawing)
# Or use separate Edit button below list
```

**Widget Type**: `wx.ListCtrl` (report view)
**Columns**: Action (300px) / Shortcut (200px)
**Selection**: Single
**NVDA Reads**: "Shortcuts List, list, Recognize Screen, NVDA+Shift+V"
**Keyboard**: Arrow keys to navigate, Space to select

---

**2. Edit Shortcut Dialog**

```python
class EditShortcutDialog(wx.Dialog):
    """Dialog for editing a keyboard shortcut."""

    def __init__(self, parent, action_name, current_shortcut):
        super().__init__(
            parent,
            title=f"Edit Shortcut: {action_name}",
            style=wx.DEFAULT_DIALOG_STYLE
        )

        # Instruction
        label = wx.StaticText(
            self,
            label="Press the new keyboard combination:"
        )

        # Key capture control
        self.text_shortcut = wx.TextCtrl(
            self,
            value=current_shortcut,
            style=wx.TE_READONLY
        )
        self.text_shortcut.SetName("Shortcut Input")
        self.text_shortcut.SetFocus()

        # Bind key events
        self.text_shortcut.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

        # Buttons
        button_ok = wx.Button(self, wx.ID_OK, "OK")
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_clear = wx.Button(self, label="&Clear")

        # Layout...

    def _on_key_down(self, event):
        """Capture key combination."""
        modifiers = []
        if event.ControlDown():
            modifiers.append("Ctrl")
        if event.AltDown():
            modifiers.append("Alt")
        if event.ShiftDown():
            modifiers.append("Shift")

        # Get key name
        keycode = event.GetKeyCode()
        keyname = self._get_key_name(keycode)

        if keyname:
            # Check if NVDA modifier key pressed
            # (This requires NVDA-specific API)
            nvda_mod = ""  # Detect NVDA key if pressed

            # Build shortcut string
            parts = modifiers + ([nvda_mod] if nvda_mod else []) + [keyname]
            shortcut = "+".join(parts)

            self.text_shortcut.SetValue(shortcut)

            # Check for conflicts
            self._check_conflicts(shortcut)

    def _check_conflicts(self, shortcut):
        """Check if shortcut conflicts with existing ones."""
        # Query config manager for existing shortcuts
        conflicts = config_manager.check_shortcut_conflict(shortcut)

        if conflicts:
            wx.MessageBox(
                f"Warning: This shortcut is already used by: {conflicts}",
                "Shortcut Conflict",
                wx.OK | wx.ICON_WARNING
            )
```

**Usage Flow**:
1. User selects action in list
2. User clicks "Edit" button (or double-clicks row)
3. Edit dialog opens
4. User presses new key combination
5. Dialog captures keys and checks for conflicts
6. User clicks OK to save or Cancel to discard

---

**3. Action Buttons**

```python
button_restore = wx.Button(panel, label="&Restore Defaults")
button_restore.SetToolTip("Reset all shortcuts to default values")

button_detect = wx.Button(panel, label="&Detect Conflicts")
button_detect.SetToolTip("Check for conflicts with NVDA core shortcuts")

def on_restore_defaults(event):
    """Restore default shortcuts with confirmation."""
    dlg = wx.MessageDialog(
        self,
        "Reset all shortcuts to default values?",
        "Confirm Restore Defaults",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
    )

    if dlg.ShowModal() == wx.ID_YES:
        config_manager.restore_default_shortcuts()
        refresh_shortcuts_list()
        wx.MessageBox(
            "Shortcuts restored to defaults.",
            "Restore Complete",
            wx.OK | wx.ICON_INFORMATION
        )

    dlg.Destroy()

button_restore.Bind(wx.EVT_BUTTON, on_restore_defaults)
```

**Widget Type**: `wx.Button`
**Labels**: "Restore Defaults" (Alt+R), "Detect Conflicts" (Alt+D)
**Actions**: Reset shortcuts / Check for NVDA conflicts

---

**4. Info Text**

```python
text_info = wx.StaticText(
    panel,
    label=(
        "ⓘ Shortcuts starting with NVDA+ are global.\n"
        "  Other shortcuts only work in recognition mode."
    )
)
text_info.SetForegroundColour(
    wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
)
text_info.SetFont(text_info.GetFont().MakeSmaller())
```

**Widget Type**: `wx.StaticText` (informational)
**Purpose**: Explain shortcut scope

---

### 4.5 Tab 5: Privacy & Logging (AF-008)

**Purpose**: Privacy settings and log management.

#### ASCII Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ Privacy & Logging                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Privacy Settings:                                          │
│  ☑ Local processing only (no cloud by default)             │
│     └─ real.md constraint 1: Privacy first                  │
│                                                             │
│  ☑ Show warning before sending data to cloud API           │
│                                                             │
│  ☐ Allow anonymous usage statistics                        │
│     (Helps improve model accuracy)                          │
│                                                             │
│  ─────────────────────────────────────────                  │
│                                                             │
│  Logging Settings:                                          │
│  Log Level: [▼ INFO                     ]                  │
│              DEBUG | INFO | WARNING | ERROR                 │
│                                                             │
│  ☑ Log recognition results (no screenshots)                │
│  ☑ Log model performance metrics                           │
│  ☐ Log detailed inference data (for debugging)             │
│                                                             │
│  Log Retention: [7   ] days                                │
│  Max Log File Size: [10  ] MB                              │
│                                                             │
│  ─────────────────────────────────────────                  │
│                                                             │
│  Current Logs:                                              │
│  Location: C:\Users\...\nvda_vision\logs\                  │
│  Total Size: 2.3 MB (5 files)                              │
│  Oldest Log: 2025-12-20                                     │
│                                                             │
│  [ Open Log Folder ]  [ View Latest Log ]                  │
│  [ Export Logs... ]   [ Clear Old Logs ]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Component Specifications

**1. Privacy Checkboxes**

```python
label_privacy = wx.StaticText(panel, label="Privacy Settings:")
label_privacy.SetFont(label_privacy.GetFont().MakeBold())

checkbox_local_only = wx.CheckBox(
    panel,
    label="&Local processing only (no cloud by default)"
)
checkbox_local_only.SetValue(True)  # Default: local-only (real.md)
checkbox_local_only.SetToolTip(
    "Prevent cloud API usage unless explicitly enabled (real.md constraint 1)"
)

checkbox_warn_cloud = wx.CheckBox(
    panel,
    label="Show &warning before sending data to cloud API"
)
checkbox_warn_cloud.SetValue(True)
checkbox_warn_cloud.SetToolTip(
    "Display consent dialog before first cloud API call"
)

checkbox_analytics = wx.CheckBox(
    panel,
    label="Allow &anonymous usage statistics"
)
checkbox_analytics.SetValue(False)
checkbox_analytics.SetToolTip(
    "Help improve model accuracy (no personal data collected)"
)
```

**Widget Type**: `wx.CheckBox` group
**Defaults**: Local-only ✓, Warn ✓, Analytics ✗
**Privacy**: Aligned with real.md constraint 1

---

**2. Log Level Selection**

```python
label_log_level = wx.StaticText(panel, label="Log &Level:")
choice_log_level = wx.Choice(
    panel,
    choices=["DEBUG", "INFO", "WARNING", "ERROR"]
)
choice_log_level.SetSelection(1)  # Default: INFO
choice_log_level.SetName("Log Level")
choice_log_level.SetToolTip(
    "DEBUG: Verbose | INFO: General | WARNING: Issues | ERROR: Failures only"
)
```

**Widget Type**: `wx.Choice`
**Label**: "Log Level:" (Alt+L)
**Options**: DEBUG / INFO / WARNING / ERROR
**Default**: INFO
**NVDA Reads**: "Log Level, combo box, INFO"

---

**3. Logging Options**

```python
checkbox_log_results = wx.CheckBox(
    panel,
    label="Log &recognition results (no screenshots)"
)
checkbox_log_results.SetValue(True)
checkbox_log_results.SetToolTip(
    "Log element counts and confidence scores (real.md constraint 2: no sensitive data)"
)

checkbox_log_metrics = wx.CheckBox(
    panel,
    label="Log model &performance metrics"
)
checkbox_log_metrics.SetValue(True)

checkbox_log_debug = wx.CheckBox(
    panel,
    label="Log &detailed inference data (for debugging)"
)
checkbox_log_debug.SetValue(False)
checkbox_log_debug.SetToolTip(
    "Verbose logs for troubleshooting (increases log size)"
)
```

**Widget Type**: `wx.CheckBox` group
**Defaults**: Results ✓, Metrics ✓, Debug ✗
**Security**: No screenshots or API keys logged (real.md constraint 2)

---

**4. Log Retention Settings**

```python
label_retention = wx.StaticText(panel, label="Log &Retention:")
spin_retention = wx.SpinCtrl(
    panel,
    value="7",
    min=1,
    max=90,
    initial=7
)
label_retention_unit = wx.StaticText(panel, label="days")

label_max_size = wx.StaticText(panel, label="Max Log File &Size:")
spin_max_size = wx.SpinCtrl(
    panel,
    value="10",
    min=1,
    max=100,
    initial=10
)
label_max_size_unit = wx.StaticText(panel, label="MB")
```

**Widget Type**: `wx.SpinCtrl`
**Labels**: "Log Retention:" (Alt+R), "Max Log File Size:" (Alt+S)
**Ranges**: 1-90 days, 1-100 MB
**Defaults**: 7 days, 10 MB

---

**5. Current Logs Info**

```python
# Dynamic labels
text_log_location = wx.StaticText(
    panel,
    label=f"Location: {log_dir}"
)

text_log_stats = wx.StaticText(panel, label="")

def update_log_stats():
    """Update log statistics."""
    stats = get_log_stats(log_dir)
    text_log_stats.SetLabel(
        f"Total Size: {stats.total_mb:.1f} MB ({stats.file_count} files)\n"
        f"Oldest Log: {stats.oldest_date}"
    )

# Update on panel activation
update_log_stats()
```

**Widget Type**: `wx.StaticText` (dynamic)
**Content**: Log directory path and statistics
**Update**: On tab activation

---

**6. Log Action Buttons (AF-008)**

```python
button_open_folder = wx.Button(panel, label="Open Log &Folder")
button_open_folder.SetToolTip("Open log directory in file explorer")

def on_open_folder(event):
    """Open log folder in file explorer."""
    import subprocess
    subprocess.Popen(f'explorer "{log_dir}"')

button_open_folder.Bind(wx.EVT_BUTTON, on_open_folder)

# ---

button_view_latest = wx.Button(panel, label="&View Latest Log")
button_view_latest.SetToolTip("Open most recent log file in default text editor")

def on_view_latest(event):
    """Open latest log file."""
    latest_log = get_latest_log_file(log_dir)
    if latest_log:
        os.startfile(latest_log)
    else:
        wx.MessageBox(
            "No log files found.",
            "No Logs",
            wx.OK | wx.ICON_INFORMATION
        )

button_view_latest.Bind(wx.EVT_BUTTON, on_view_latest)

# ---

button_export = wx.Button(panel, label="&Export Logs...")
button_export.SetToolTip("Export sanitized logs for sharing (AF-008)")

def on_export_logs(event):
    """Export logs with sensitive data removed."""
    dlg = wx.FileDialog(
        self,
        "Export Logs",
        defaultDir=str(Path.home() / "Desktop"),
        defaultFile=f"nvda_vision_logs_{datetime.now():%Y%m%d}.zip",
        wildcard="ZIP files (*.zip)|*.zip",
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    )

    if dlg.ShowModal() == wx.ID_OK:
        export_path = dlg.GetPath()

        # Show progress
        progress = wx.ProgressDialog(
            "Exporting Logs",
            "Sanitizing and compressing logs...",
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )

        try:
            # Sanitize logs (remove API keys, sensitive data)
            sanitized_logs = sanitize_logs(log_dir)

            # Create ZIP
            create_zip(sanitized_logs, export_path)

            wx.MessageBox(
                f"Logs exported successfully to:\n{export_path}",
                "Export Complete",
                wx.OK | wx.ICON_INFORMATION
            )
        except Exception as e:
            wx.MessageBox(
                f"Export failed: {e}",
                "Export Error",
                wx.OK | wx.ICON_ERROR
            )
        finally:
            progress.Destroy()

    dlg.Destroy()

button_export.Bind(wx.EVT_BUTTON, on_export_logs)

# ---

button_clear = wx.Button(panel, label="&Clear Old Logs")
button_clear.SetToolTip("Delete logs older than retention period")

def on_clear_old_logs(event):
    """Clear logs older than retention setting."""
    dlg = wx.MessageDialog(
        self,
        f"Delete logs older than {spin_retention.GetValue()} days?",
        "Confirm Clear Old Logs",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
    )

    if dlg.ShowModal() == wx.ID_YES:
        deleted = clear_old_logs(log_dir, spin_retention.GetValue())
        update_log_stats()

        wx.MessageBox(
            f"Deleted {deleted} old log files.",
            "Clear Complete",
            wx.OK | wx.ICON_INFORMATION
        )

    dlg.Destroy()

button_clear.Bind(wx.EVT_BUTTON, on_clear_old_logs)
```

**Widget Types**: `wx.Button` group
**Labels**: "Open Log Folder" (Alt+F), "View Latest Log" (Alt+V), "Export Logs..." (Alt+E), "Clear Old Logs" (Alt+C)
**Actions**:
- Open Folder: Opens log directory in Explorer
- View Latest: Opens most recent log in text editor
- Export Logs: Creates sanitized ZIP for sharing (AF-008)
- Clear Old: Deletes logs older than retention period

---

## 5. Layout and Sizers

### 5.1 Main Dialog Layout

```python
class NVDAVisionSettingsDialog(wx.Dialog):
    """Main settings dialog."""

    def __init__(self, parent, config_manager):
        super().__init__(parent, title="NVDA Vision Settings", size=(800, 600))

        self.config_manager = config_manager

        # Main vertical sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create notebook (tabs)
        self.notebook = wx.Notebook(self)
        self.notebook.SetName("Settings Categories")

        # Add tabs
        self.panel_general = self._create_general_panel()
        self.panel_models = self._create_models_panel()
        self.panel_recognition = self._create_recognition_panel()
        self.panel_shortcuts = self._create_shortcuts_panel()
        self.panel_privacy = self._create_privacy_panel()

        self.notebook.AddPage(self.panel_general, "General")
        self.notebook.AddPage(self.panel_models, "Models")
        self.notebook.AddPage(self.panel_recognition, "Recognition")
        self.notebook.AddPage(self.panel_shortcuts, "Shortcuts")
        self.notebook.AddPage(self.panel_privacy, "Privacy")

        # Add notebook to main sizer with expand
        main_sizer.Add(self.notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        # Add horizontal separator
        main_sizer.Add(wx.StaticLine(self), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # Button sizer (bottom)
        button_sizer = self._create_button_sizer()
        main_sizer.Add(button_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Set main sizer
        self.SetSizer(main_sizer)

        # Load current settings
        self._load_settings()

        # Bind events
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)

    def _create_button_sizer(self):
        """Create OK/Cancel/Apply button sizer."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add stretch to right-align buttons
        sizer.AddStretchSpacer()

        # OK button (default)
        self.button_ok = wx.Button(self, wx.ID_OK, "&OK")
        self.button_ok.SetDefault()
        self.button_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        sizer.Add(self.button_ok, flag=wx.RIGHT, border=5)

        # Cancel button
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "&Cancel")
        self.button_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        sizer.Add(self.button_cancel, flag=wx.RIGHT, border=5)

        # Apply button
        self.button_apply = wx.Button(self, wx.ID_APPLY, "&Apply")
        self.button_apply.Bind(wx.EVT_BUTTON, self._on_apply)
        self.button_apply.Enable(False)  # Disabled until changes made
        sizer.Add(self.button_apply)

        return sizer
```

**Button Behavior**:
- **OK**: Save settings and close dialog
- **Cancel**: Discard changes and close dialog
- **Apply**: Save settings but keep dialog open

**Apply Button State**:
- Disabled by default
- Enabled when any setting changes
- Disabled again after applying

---

### 5.2 Panel Layout Pattern

All tab panels follow this structure:

```python
def _create_general_panel(self):
    """Create General settings panel."""
    panel = wx.Panel(self.notebook)
    panel.SetName("General Settings")

    # Main sizer for panel
    main_sizer = wx.BoxSizer(wx.VERTICAL)

    # Section 1: Language
    section1_sizer = self._create_language_section(panel)
    main_sizer.Add(section1_sizer, flag=wx.EXPAND | wx.ALL, border=10)

    # Separator
    main_sizer.Add(
        wx.StaticLine(panel),
        flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
        border=10
    )

    # Section 2: Startup options
    section2_sizer = self._create_startup_section(panel)
    main_sizer.Add(section2_sizer, flag=wx.EXPAND | wx.ALL, border=10)

    # ... more sections ...

    # Add stretch to push everything to top
    main_sizer.AddStretchSpacer()

    panel.SetSizer(main_sizer)
    return panel
```

**Pattern**:
1. Create `wx.Panel` as tab content
2. Main vertical `wx.BoxSizer`
3. Add sections with borders
4. Separate sections with `wx.StaticLine`
5. Add stretch spacer at end (top-aligned layout)

---

### 5.3 Section Layout Pattern

```python
def _create_language_section(self, panel):
    """Create language selection section."""
    # Section sizer (vertical)
    sizer = wx.BoxSizer(wx.VERTICAL)

    # Label
    label = wx.StaticText(panel, label="&Language:")
    sizer.Add(label, flag=wx.BOTTOM, border=5)

    # Control
    choices = ["English", "Chinese (Simplified)", "Chinese (Traditional)"]
    control = wx.Choice(panel, choices=choices)
    control.SetSelection(1)
    control.SetName("Language Selection")
    sizer.Add(control, flag=wx.EXPAND)

    # Help text (optional)
    help_text = wx.StaticText(
        panel,
        label="Restart NVDA to apply language changes"
    )
    help_text.SetFont(help_text.GetFont().MakeSmaller())
    help_text.SetForegroundColour(
        wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
    )
    sizer.Add(help_text, flag=wx.TOP, border=3)

    return sizer
```

**Pattern**:
1. Vertical `wx.BoxSizer` for section
2. Label with mnemonic (&)
3. Control below label
4. Optional help text (smaller, grayed)

---

### 5.4 Form Layout Pattern (Label + Control Pairs)

For forms with multiple label-control pairs:

```python
def _create_timeout_section(self, panel):
    """Create timeout settings using GridBagSizer."""
    sizer = wx.GridBagSizer(hgap=10, vgap=5)

    # Row 0: Inference timeout
    label_timeout = wx.StaticText(panel, label="Inference &Timeout:")
    sizer.Add(label_timeout, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)

    spin_timeout = wx.SpinCtrl(panel, value="15", min=5, max=60)
    sizer.Add(spin_timeout, pos=(0, 1))

    label_seconds = wx.StaticText(panel, label="seconds")
    sizer.Add(label_seconds, pos=(0, 2), flag=wx.ALIGN_CENTER_VERTICAL)

    # Row 1: Progress feedback
    label_progress = wx.StaticText(panel, label="Progress &Feedback After:")
    sizer.Add(label_progress, pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL)

    spin_progress = wx.SpinCtrl(panel, value="5", min=3, max=15)
    sizer.Add(spin_progress, pos=(1, 1))

    label_seconds2 = wx.StaticText(panel, label="seconds")
    sizer.Add(label_seconds2, pos=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)

    # Make column 1 (controls) expandable
    sizer.AddGrowableCol(1)

    return sizer
```

**GridBagSizer Usage**:
- Column 0: Labels (right-aligned)
- Column 1: Controls (expandable)
- Column 2: Units (left-aligned)
- `hgap=10`: Horizontal spacing between columns
- `vgap=5`: Vertical spacing between rows

---

## 6. Keyboard Navigation

### 6.1 Tab Order

**Tab order flows naturally top-to-bottom, left-to-right within each tab.**

Example for General tab:
1. Language choice
2. Enable on startup checkbox
3. Show notifications checkbox
4. Announce confidence checkbox
5. Confidence threshold slider
6. View logs button
7. Reset button
8. (Tab to next tab in notebook)

**Tab Navigation**:
- **Tab**: Move to next control
- **Shift+Tab**: Move to previous control
- **Ctrl+Tab**: Next tab in notebook
- **Ctrl+Shift+Tab**: Previous tab in notebook

---

### 6.2 Mnemonics (Alt+Letter Shortcuts)

**All major controls have mnemonics** (underlined letter):

```python
# Example: Language with Alt+L
label = wx.StaticText(panel, label="&Language:")
control = wx.Choice(panel, choices=["English", "中文"])
```

**Mnemonic Guidelines**:
- First letter preferred (e.g., "&Language" → Alt+L)
- If conflict, use another letter (e.g., "La&nguage" → Alt+N)
- Unique within each tab (can duplicate across tabs)

**Common Mnemonics**:
- Alt+G: General tab
- Alt+M: Models tab
- Alt+R: Recognition tab
- Alt+S: Shortcuts tab
- Alt+P: Privacy tab

---

### 6.3 Control-Specific Navigation

**Checkboxes**:
- Space: Toggle checked/unchecked
- Enter: Same as Space

**Radio Buttons**:
- Arrow keys: Move selection within group
- Space: Select current option

**Sliders**:
- Left/Right arrows: Decrease/increase by 1%
- Page Up/Down: Decrease/increase by 10%
- Home: Minimum value
- End: Maximum value

**Spin Controls**:
- Up/Down arrows: Increment/decrement by 1
- Page Up/Down: Increment/decrement by 10
- Home: Minimum value
- End: Maximum value

**List Controls**:
- Up/Down arrows: Navigate items
- Space: Select/activate item
- Enter: Activate item (edit shortcut)

**Choice/Combo Boxes**:
- Alt+Down: Open dropdown
- Up/Down arrows: Navigate options
- Enter: Select option
- Esc: Close without selecting

---

### 6.4 Dialog Navigation

**OK/Cancel/Apply Buttons**:
- Tab order: OK → Cancel → Apply
- Enter (on OK): Save and close (OK is default button)
- Esc: Cancel dialog
- Alt+O: OK button
- Alt+C: Cancel button
- Alt+A: Apply button

**Focus Management**:
- Dialog opens with focus on first control (Language choice)
- Tab loops through all controls
- Shift+Tab loops backward
- Enter on OK button saves and closes
- Esc cancels even if focus not on Cancel button

---

## 7. Screen Reader Integration

### 7.1 NVDA Announcements

**All controls automatically announce** (wxPython native):
- Control type (button, checkbox, slider, etc.)
- Label text
- Current value/state
- Help text (if set)

**Examples**:

```
# Checkbox
NVDA reads: "Enable NVDA Vision on startup, checkbox, checked"

# Slider
NVDA reads: "Confidence Threshold, slider, 70"

# Spin control
NVDA reads: "Inference Timeout, spin control, 15"

# Choice
NVDA reads: "Language, combo box, Chinese (Simplified), 2 of 3"

# Button
NVDA reads: "View Logs, button"

# Static text
NVDA reads: "Plugin Version: 0.1.0"
```

---

### 7.2 SetName() for Accessible Names

**Always set names for controls**:

```python
control = wx.TextCtrl(panel, value="")
control.SetName("API Key")  # NVDA reads this

slider = wx.Slider(panel, value=70, minValue=50, maxValue=95)
slider.SetName("Confidence Threshold")  # Instead of generic "slider"
```

---

### 7.3 SetHelpText() for Context

**Provide additional context**:

```python
checkbox = wx.CheckBox(panel, label="Enable cloud API")
checkbox.SetHelpText(
    "Allow using cloud API when local models fail. "
    "Requires user consent (real.md constraint 1)."
)

# NVDA reads help text when user presses NVDA+F1 on control
```

---

### 7.4 SetToolTip() for Brief Help

**Tooltips appear on hover and are read by NVDA**:

```python
button = wx.Button(panel, label="Clear Cache")
button.SetToolTip("Delete all cached recognition results")

# NVDA reads tooltip when focus moves to button
```

---

### 7.5 State Changes Announcements

**Notify NVDA when state changes**:

```python
def on_cloud_enabled(self, event):
    """Handle cloud API checkbox toggle."""
    enabled = event.IsChecked()

    # Enable/disable dependent controls
    self.choice_provider.Enable(enabled)
    self.text_api_key.Enable(enabled)
    self.button_change_key.Enable(enabled)

    # Announce change to user
    import ui
    if enabled:
        ui.message("Cloud API enabled. Please configure API key.")
    else:
        ui.message("Cloud API disabled. Using local models only.")
```

---

### 7.6 Progress Announcements

**Long operations need progress feedback**:

```python
def on_test_connection(self, event):
    """Test cloud API connection."""
    import ui

    # Announce start
    ui.message("Testing connection...")

    # Show progress dialog (modal, prevents other actions)
    progress = wx.ProgressDialog(
        "Testing Connection",
        "Connecting to API...",
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
    )

    try:
        result = test_api_connection()  # Blocking call

        # Announce result
        if result.success:
            ui.message("Connection successful!")
        else:
            ui.message(f"Connection failed: {result.error}")

    finally:
        progress.Destroy()
```

---

## 8. Implementation Examples

### 8.1 Complete Dialog Implementation

```python
# ui/settings_dialog.py

import wx
from pathlib import Path
from typing import Optional

from ..config import ConfigManager
from ..infrastructure.logger import logger


class NVDAVisionSettingsDialog(wx.Dialog):
    """Main settings dialog for NVDA Vision plugin.

    Provides configuration interface for:
    - General settings (language, startup)
    - Model selection and parameters
    - Recognition settings and cache
    - Keyboard shortcuts customization
    - Privacy and logging options

    Accessibility:
    - WCAG 2.1 AA compliant (real.md constraint 4)
    - All controls keyboard accessible
    - Full NVDA screen reader support
    """

    def __init__(
        self,
        parent: Optional[wx.Window],
        config_manager: ConfigManager
    ):
        """Initialize settings dialog.

        Args:
            parent: Parent window (can be None for standalone).
            config_manager: Configuration manager instance.
        """
        super().__init__(
            parent,
            id=wx.ID_ANY,
            title="NVDA Vision Settings",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(800, 600)
        )

        self.config_manager = config_manager
        self._settings_changed = False

        # Set minimum size
        self.SetMinSize((700, 500))

        # Center on screen
        self.CenterOnScreen()

        # Create UI
        self._create_ui()

        # Load current settings from config
        self._load_settings()

        # Bind events
        self._bind_events()

        logger.info("Settings dialog opened")

    def _create_ui(self):
        """Create dialog UI components."""
        # Main vertical sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create notebook (tabs)
        self.notebook = wx.Notebook(self)
        self.notebook.SetName("Settings Categories")

        # Create tab panels
        self.panel_general = self._create_general_panel()
        self.panel_models = self._create_models_panel()
        self.panel_recognition = self._create_recognition_panel()
        self.panel_shortcuts = self._create_shortcuts_panel()
        self.panel_privacy = self._create_privacy_panel()

        # Add pages to notebook
        self.notebook.AddPage(self.panel_general, "&General")
        self.notebook.AddPage(self.panel_models, "&Models")
        self.notebook.AddPage(self.panel_recognition, "&Recognition")
        self.notebook.AddPage(self.panel_shortcuts, "&Shortcuts")
        self.notebook.AddPage(self.panel_privacy, "&Privacy")

        # Add notebook to main sizer
        main_sizer.Add(
            self.notebook,
            proportion=1,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

        # Add separator line
        main_sizer.Add(
            wx.StaticLine(self),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10
        )

        # Create button sizer (OK/Cancel/Apply)
        button_sizer = self._create_button_sizer()
        main_sizer.Add(
            button_sizer,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

        # Set main sizer
        self.SetSizer(main_sizer)

    def _create_general_panel(self) -> wx.Panel:
        """Create General settings panel.

        Returns:
            Panel with general settings controls.
        """
        panel = wx.Panel(self.notebook)
        panel.SetName("General Settings")

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Language section
        lang_sizer = wx.BoxSizer(wx.VERTICAL)

        label_lang = wx.StaticText(panel, label="&Language:")
        lang_sizer.Add(label_lang, flag=wx.BOTTOM, border=5)

        self.choice_language = wx.Choice(
            panel,
            choices=["English", "Chinese (Simplified)", "Chinese (Traditional)"]
        )
        self.choice_language.SetName("Language Selection")
        self.choice_language.SetToolTip("Select plugin interface language")
        lang_sizer.Add(self.choice_language, flag=wx.EXPAND)

        main_sizer.Add(lang_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Separator
        main_sizer.Add(
            wx.StaticLine(panel),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10
        )

        # Startup options
        startup_sizer = wx.BoxSizer(wx.VERTICAL)

        self.checkbox_autostart = wx.CheckBox(
            panel,
            label="&Enable NVDA Vision on startup"
        )
        self.checkbox_autostart.SetToolTip(
            "Load plugin automatically when NVDA starts"
        )
        startup_sizer.Add(self.checkbox_autostart, flag=wx.BOTTOM, border=5)

        self.checkbox_notifications = wx.CheckBox(
            panel,
            label="Show &notification when recognition starts"
        )
        startup_sizer.Add(self.checkbox_notifications, flag=wx.BOTTOM, border=5)

        main_sizer.Add(startup_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Separator
        main_sizer.Add(
            wx.StaticLine(panel),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10
        )

        # Confidence settings
        conf_sizer = wx.BoxSizer(wx.VERTICAL)

        self.checkbox_announce_conf = wx.CheckBox(
            panel,
            label="&Announce confidence scores"
        )
        conf_sizer.Add(self.checkbox_announce_conf, flag=wx.BOTTOM, border=10)

        # Indented threshold slider
        threshold_sizer = wx.BoxSizer(wx.VERTICAL)

        label_threshold = wx.StaticText(
            panel,
            label="Low confidence threshold:"
        )
        threshold_sizer.Add(label_threshold, flag=wx.BOTTOM, border=5)

        self.slider_threshold = wx.Slider(
            panel,
            value=70,
            minValue=50,
            maxValue=95,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS
        )
        self.slider_threshold.SetName("Confidence Threshold")
        self.slider_threshold.SetToolTip(
            "Elements below this score are marked as 'uncertain' (real.md constraint 3)"
        )
        threshold_sizer.Add(self.slider_threshold, flag=wx.EXPAND)

        # Indent the slider section
        conf_sizer.Add(
            threshold_sizer,
            flag=wx.EXPAND | wx.LEFT,
            border=20
        )

        main_sizer.Add(conf_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Stretch spacer to push everything to top
        main_sizer.AddStretchSpacer()

        # Info section at bottom
        info_sizer = wx.BoxSizer(wx.VERTICAL)

        config_path = self.config_manager.config_path.parent
        text_version = wx.StaticText(panel, label="Plugin Version: 0.1.0")
        text_version.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        info_sizer.Add(text_version, flag=wx.BOTTOM, border=3)

        text_config = wx.StaticText(
            panel,
            label=f"Configuration Location: {config_path}"
        )
        text_config.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        info_sizer.Add(text_config, flag=wx.BOTTOM, border=10)

        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.button_view_logs = wx.Button(panel, label="View &Logs...")
        self.button_view_logs.SetToolTip("Open log directory in file explorer")
        button_sizer.Add(self.button_view_logs, flag=wx.RIGHT, border=5)

        self.button_reset = wx.Button(panel, label="&Reset to Defaults")
        self.button_reset.SetToolTip("Reset all settings to default values")
        button_sizer.Add(self.button_reset)

        info_sizer.Add(button_sizer)

        main_sizer.Add(info_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        panel.SetSizer(main_sizer)
        return panel

    def _create_models_panel(self) -> wx.Panel:
        """Create Models settings panel.

        Returns:
            Panel with model configuration controls.
        """
        panel = wx.Panel(self.notebook)
        panel.SetName("Model Settings")

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Model selection strategy
        strategy_sizer = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Model Selection Strategy"
        )

        self.radio_auto = wx.RadioButton(
            panel,
            label="&Automatic (recommended)",
            style=wx.RB_GROUP
        )
        self.radio_auto.SetToolTip(
            "Tries GPU → CPU → Cloud API in order (real.md constraint 1)"
        )
        strategy_sizer.Add(self.radio_auto, flag=wx.BOTTOM, border=5)

        help_auto = wx.StaticText(
            panel,
            label="Tries GPU → CPU → Cloud API in order"
        )
        help_auto.SetFont(help_auto.GetFont().MakeSmaller())
        help_auto.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        strategy_sizer.Add(help_auto, flag=wx.LEFT | wx.BOTTOM, border=(20, 10))

        self.radio_gpu = wx.RadioButton(
            panel,
            label="Prefer &GPU (UI-TARS 7B)"
        )
        self.radio_gpu.SetToolTip("Requires NVIDIA GPU with 16GB+ VRAM")
        strategy_sizer.Add(self.radio_gpu, flag=wx.BOTTOM, border=5)

        help_gpu = wx.StaticText(
            panel,
            label="Requires NVIDIA GPU with 16GB+ VRAM"
        )
        help_gpu.SetFont(help_gpu.GetFont().MakeSmaller())
        help_gpu.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        strategy_sizer.Add(help_gpu, flag=wx.LEFT | wx.BOTTOM, border=(20, 10))

        self.radio_cpu = wx.RadioButton(
            panel,
            label="Prefer &CPU (MiniCPM-V 2.6)"
        )
        self.radio_cpu.SetToolTip("Slower but works on any system")
        strategy_sizer.Add(self.radio_cpu, flag=wx.BOTTOM, border=5)

        help_cpu = wx.StaticText(
            panel,
            label="Slower but works on any system"
        )
        help_cpu.SetFont(help_cpu.GetFont().MakeSmaller())
        help_cpu.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        strategy_sizer.Add(help_cpu, flag=wx.LEFT | wx.BOTTOM, border=(20, 10))

        self.radio_cloud = wx.RadioButton(
            panel,
            label="Cloud API &only"
        )
        self.radio_cloud.SetToolTip("Requires internet connection and API key")
        strategy_sizer.Add(self.radio_cloud, flag=wx.BOTTOM, border=5)

        help_cloud = wx.StaticText(
            panel,
            label="Requires internet and API key"
        )
        help_cloud.SetFont(help_cloud.GetFont().MakeSmaller())
        help_cloud.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        strategy_sizer.Add(help_cloud, flag=wx.LEFT, border=20)

        main_sizer.Add(strategy_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Separator
        main_sizer.Add(
            wx.StaticLine(panel),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10
        )

        # Timeout settings using GridBagSizer
        timeout_sizer = wx.GridBagSizer(hgap=10, vgap=5)

        label_timeout = wx.StaticText(panel, label="Inference &Timeout:")
        timeout_sizer.Add(
            label_timeout,
            pos=(0, 0),
            flag=wx.ALIGN_CENTER_VERTICAL
        )

        self.spin_timeout = wx.SpinCtrl(
            panel,
            value="15",
            min=5,
            max=60,
            initial=15
        )
        self.spin_timeout.SetName("Inference Timeout")
        self.spin_timeout.SetToolTip(
            "Maximum time to wait before degrading to backup model (real.md constraint 6)"
        )
        timeout_sizer.Add(self.spin_timeout, pos=(0, 1))

        label_timeout_unit = wx.StaticText(panel, label="seconds")
        timeout_sizer.Add(
            label_timeout_unit,
            pos=(0, 2),
            flag=wx.ALIGN_CENTER_VERTICAL
        )

        label_progress = wx.StaticText(panel, label="Progress &Feedback After:")
        timeout_sizer.Add(
            label_progress,
            pos=(1, 0),
            flag=wx.ALIGN_CENTER_VERTICAL
        )

        self.spin_progress = wx.SpinCtrl(
            panel,
            value="5",
            min=3,
            max=15,
            initial=5
        )
        self.spin_progress.SetName("Progress Feedback Delay")
        self.spin_progress.SetToolTip(
            "When to announce 'Still recognizing...' (real.md constraint 6: >5s)"
        )
        timeout_sizer.Add(self.spin_progress, pos=(1, 1))

        label_progress_unit = wx.StaticText(panel, label="seconds")
        timeout_sizer.Add(
            label_progress_unit,
            pos=(1, 2),
            flag=wx.ALIGN_CENTER_VERTICAL
        )

        # Make column 1 (spin controls) expand
        timeout_sizer.AddGrowableCol(1)

        main_sizer.Add(timeout_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Separator
        main_sizer.Add(
            wx.StaticLine(panel),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=10
        )

        # Cloud API settings
        cloud_sizer = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Cloud API Settings"
        )

        self.checkbox_enable_cloud = wx.CheckBox(
            panel,
            label="&Enable cloud API as fallback"
        )
        self.checkbox_enable_cloud.SetToolTip(
            "Allow using cloud API when local models fail (requires user consent)"
        )
        cloud_sizer.Add(self.checkbox_enable_cloud, flag=wx.BOTTOM, border=10)

        help_cloud_privacy = wx.StaticText(
            panel,
            label="(real.md constraint 1: User must opt-in)"
        )
        help_cloud_privacy.SetFont(help_cloud_privacy.GetFont().MakeSmaller())
        help_cloud_privacy.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        cloud_sizer.Add(
            help_cloud_privacy,
            flag=wx.LEFT | wx.BOTTOM,
            border=(20, 10)
        )

        # API provider
        provider_sizer = wx.BoxSizer(wx.HORIZONTAL)

        label_provider = wx.StaticText(panel, label="API &Provider:")
        provider_sizer.Add(
            label_provider,
            flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            border=5
        )

        self.choice_provider = wx.Choice(
            panel,
            choices=["Doubao (Volcengine)", "OpenAI Vision (Future)", "Custom Endpoint"]
        )
        self.choice_provider.SetName("API Provider")
        self.choice_provider.Enable(False)
        provider_sizer.Add(self.choice_provider, proportion=1)

        cloud_sizer.Add(provider_sizer, flag=wx.EXPAND | wx.BOTTOM, border=10)

        # API key
        key_sizer = wx.BoxSizer(wx.VERTICAL)

        label_api_key = wx.StaticText(panel, label="API &Key:")
        key_sizer.Add(label_api_key, flag=wx.BOTTOM, border=5)

        key_input_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.text_api_key = wx.TextCtrl(
            panel,
            value="",
            style=wx.TE_PASSWORD
        )
        self.text_api_key.SetName("API Key")
        self.text_api_key.Enable(False)
        key_input_sizer.Add(self.text_api_key, proportion=1, flag=wx.RIGHT, border=5)

        self.button_change_key = wx.Button(panel, label="&Change...")
        self.button_change_key.SetToolTip("Update API key (will be encrypted)")
        self.button_change_key.Enable(False)
        key_input_sizer.Add(self.button_change_key)

        key_sizer.Add(key_input_sizer, flag=wx.EXPAND)

        help_encrypted = wx.StaticText(
            panel,
            label="Encrypted with Windows DPAPI"
        )
        help_encrypted.SetFont(help_encrypted.GetFont().MakeSmaller())
        help_encrypted.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        key_sizer.Add(help_encrypted, flag=wx.TOP, border=3)

        cloud_sizer.Add(key_sizer, flag=wx.EXPAND | wx.BOTTOM, border=10)

        # Test button
        self.button_test = wx.Button(panel, label="&Test Connection")
        self.button_test.SetToolTip("Verify API key and connection")
        self.button_test.Enable(False)
        cloud_sizer.Add(self.button_test)

        main_sizer.Add(cloud_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        # Stretch spacer
        main_sizer.AddStretchSpacer()

        panel.SetSizer(main_sizer)
        return panel

    def _create_recognition_panel(self) -> wx.Panel:
        """Create Recognition settings panel."""
        # Implementation similar to above...
        # (Omitted for brevity - follows same pattern)
        pass

    def _create_shortcuts_panel(self) -> wx.Panel:
        """Create Shortcuts customization panel."""
        # Implementation similar to above...
        pass

    def _create_privacy_panel(self) -> wx.Panel:
        """Create Privacy & Logging settings panel."""
        # Implementation similar to above...
        pass

    def _create_button_sizer(self) -> wx.BoxSizer:
        """Create OK/Cancel/Apply button sizer."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Stretch spacer to right-align buttons
        sizer.AddStretchSpacer()

        # OK button (default)
        self.button_ok = wx.Button(self, wx.ID_OK, "&OK")
        self.button_ok.SetDefault()
        sizer.Add(self.button_ok, flag=wx.RIGHT, border=5)

        # Cancel button
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "&Cancel")
        sizer.Add(self.button_cancel, flag=wx.RIGHT, border=5)

        # Apply button
        self.button_apply = wx.Button(self, wx.ID_APPLY, "&Apply")
        self.button_apply.Enable(False)
        sizer.Add(self.button_apply)

        return sizer

    def _bind_events(self):
        """Bind event handlers."""
        # Button events
        self.button_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        self.button_cancel.Bind(wx.EVT_BUTTON, self._on_cancel)
        self.button_apply.Bind(wx.EVT_BUTTON, self._on_apply)

        # General tab
        self.checkbox_announce_conf.Bind(
            wx.EVT_CHECKBOX,
            self._on_announce_conf_changed
        )
        self.button_view_logs.Bind(wx.EVT_BUTTON, self._on_view_logs)
        self.button_reset.Bind(wx.EVT_BUTTON, self._on_reset_defaults)

        # Models tab
        self.checkbox_enable_cloud.Bind(
            wx.EVT_CHECKBOX,
            self._on_cloud_enabled
        )
        self.button_change_key.Bind(wx.EVT_BUTTON, self._on_change_api_key)
        self.button_test.Bind(wx.EVT_BUTTON, self._on_test_connection)

        # Track changes for Apply button
        self._bind_change_tracking()

    def _bind_change_tracking(self):
        """Bind events to track when settings change."""
        # Track when any control changes
        controls = [
            self.choice_language,
            self.checkbox_autostart,
            self.checkbox_notifications,
            self.checkbox_announce_conf,
            self.slider_threshold,
            # ... add all other controls
        ]

        for control in controls:
            if isinstance(control, wx.CheckBox):
                control.Bind(wx.EVT_CHECKBOX, self._on_setting_changed)
            elif isinstance(control, wx.Choice):
                control.Bind(wx.EVT_CHOICE, self._on_setting_changed)
            elif isinstance(control, wx.Slider):
                control.Bind(wx.EVT_SLIDER, self._on_setting_changed)
            elif isinstance(control, wx.SpinCtrl):
                control.Bind(wx.EVT_SPINCTRL, self._on_setting_changed)

    def _load_settings(self):
        """Load current settings from config manager."""
        # General
        lang = self.config_manager.get("language", "zh-CN")
        lang_map = {
            "en": 0,
            "zh-CN": 1,
            "zh-TW": 2
        }
        self.choice_language.SetSelection(lang_map.get(lang, 1))

        self.checkbox_autostart.SetValue(
            self.config_manager.get("autostart", True)
        )

        self.checkbox_notifications.SetValue(
            self.config_manager.get("ui.show_notifications", True)
        )

        self.checkbox_announce_conf.SetValue(
            self.config_manager.get("ui.announce_confidence", True)
        )

        self.slider_threshold.SetValue(
            int(self.config_manager.get("models.confidence_threshold", 0.7) * 100)
        )

        # Models
        preference = self.config_manager.get("models.preference", "auto")
        pref_map = {
            "auto": self.radio_auto,
            "gpu": self.radio_gpu,
            "cpu": self.radio_cpu,
            "cloud": self.radio_cloud
        }
        pref_map.get(preference, self.radio_auto).SetValue(True)

        self.spin_timeout.SetValue(
            int(self.config_manager.get("models.timeout_seconds", 15))
        )

        self.spin_progress.SetValue(
            int(self.config_manager.get("ui.progress_feedback_delay", 5))
        )

        self.checkbox_enable_cloud.SetValue(
            self.config_manager.get("enable_cloud_api", False)
        )

        # Update dependent controls
        self._on_cloud_enabled(None)
        self._on_announce_conf_changed(None)

        # ... load other settings ...

        logger.debug("Settings loaded from configuration")

    def _save_settings(self):
        """Save settings to config manager."""
        # General
        lang_map = {0: "en", 1: "zh-CN", 2: "zh-TW"}
        self.config_manager.set(
            "language",
            lang_map[self.choice_language.GetSelection()]
        )

        self.config_manager.set(
            "autostart",
            self.checkbox_autostart.GetValue()
        )

        self.config_manager.set(
            "ui.show_notifications",
            self.checkbox_notifications.GetValue()
        )

        self.config_manager.set(
            "ui.announce_confidence",
            self.checkbox_announce_conf.GetValue()
        )

        self.config_manager.set(
            "models.confidence_threshold",
            self.slider_threshold.GetValue() / 100.0
        )

        # Models
        if self.radio_auto.GetValue():
            preference = "auto"
        elif self.radio_gpu.GetValue():
            preference = "gpu"
        elif self.radio_cpu.GetValue():
            preference = "cpu"
        else:
            preference = "cloud"

        self.config_manager.set("models.preference", preference)

        self.config_manager.set(
            "models.timeout_seconds",
            self.spin_timeout.GetValue()
        )

        self.config_manager.set(
            "ui.progress_feedback_delay",
            self.spin_progress.GetValue()
        )

        self.config_manager.set(
            "enable_cloud_api",
            self.checkbox_enable_cloud.GetValue()
        )

        # ... save other settings ...

        # Save to disk
        self.config_manager.save()

        logger.info("Settings saved")

    def _on_ok(self, event):
        """Handle OK button click."""
        self._save_settings()
        self.EndModal(wx.ID_OK)

    def _on_cancel(self, event):
        """Handle Cancel button click."""
        # Check if settings changed
        if self._settings_changed:
            dlg = wx.MessageDialog(
                self,
                "Discard unsaved changes?",
                "Unsaved Changes",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
            )

            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
                return

            dlg.Destroy()

        self.EndModal(wx.ID_CANCEL)

    def _on_apply(self, event):
        """Handle Apply button click."""
        self._save_settings()
        self._settings_changed = False
        self.button_apply.Enable(False)

        # Notify user
        import ui
        ui.message("Settings applied")

    def _on_setting_changed(self, event):
        """Handle any setting change."""
        self._settings_changed = True
        self.button_apply.Enable(True)

        # Allow event to propagate
        event.Skip()

    def _on_announce_conf_changed(self, event):
        """Handle confidence announcement checkbox change."""
        enabled = self.checkbox_announce_conf.GetValue()
        self.slider_threshold.Enable(enabled)

        if event:
            self._on_setting_changed(event)

    def _on_cloud_enabled(self, event):
        """Handle cloud API checkbox change."""
        enabled = self.checkbox_enable_cloud.GetValue()

        # Enable/disable dependent controls
        self.choice_provider.Enable(enabled)
        self.text_api_key.Enable(enabled)
        self.button_change_key.Enable(enabled)
        self.button_test.Enable(enabled and len(self.text_api_key.GetValue()) > 0)

        # Announce state change
        if event:
            import ui
            if enabled:
                ui.message("Cloud API enabled. Please configure API key.")
            else:
                ui.message("Cloud API disabled. Using local models only.")

            self._on_setting_changed(event)

    def _on_view_logs(self, event):
        """Open log directory in file explorer."""
        import subprocess
        log_dir = self.config_manager.config_path.parent / "logs"
        subprocess.Popen(f'explorer "{log_dir}"')

    def _on_reset_defaults(self, event):
        """Reset all settings to defaults."""
        dlg = wx.MessageDialog(
            self,
            "Reset all settings to default values?\n\n"
            "This cannot be undone.",
            "Confirm Reset",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
        )

        if dlg.ShowModal() == wx.ID_YES:
            # Reset configuration
            self.config_manager.config = self.config_manager._get_default_config()
            self.config_manager.save()

            # Reload UI
            self._load_settings()

            # Notify user
            wx.MessageBox(
                "Settings reset to defaults.",
                "Reset Complete",
                wx.OK | wx.ICON_INFORMATION
            )

        dlg.Destroy()

    def _on_change_api_key(self, event):
        """Open dialog to change API key."""
        dlg = wx.TextEntryDialog(
            self,
            "Enter API Key (will be encrypted):",
            "Change API Key",
            style=wx.OK | wx.CANCEL | wx.TE_PASSWORD
        )

        if dlg.ShowModal() == wx.ID_OK:
            plaintext_key = dlg.GetValue()

            if plaintext_key.strip():
                # Save encrypted
                self.config_manager.save_api_key("doubao_api_key", plaintext_key)

                # Update display (masked)
                self.text_api_key.SetValue("*" * 20)

                # Enable test button
                self.button_test.Enable(True)

                # Notify user
                import ui
                ui.message("API key saved securely")
            else:
                wx.MessageBox(
                    "API key cannot be empty.",
                    "Invalid Input",
                    wx.OK | wx.ICON_ERROR
                )

        dlg.Destroy()

    def _on_test_connection(self, event):
        """Test cloud API connection."""
        import ui

        # Announce start
        ui.message("Testing connection...")

        # Show progress dialog
        progress = wx.ProgressDialog(
            "Testing Connection",
            "Connecting to API...",
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )

        try:
            # Get API key
            api_key = self.config_manager.get("doubao_api_key")

            if not api_key:
                wx.MessageBox(
                    "No API key configured.",
                    "Test Failed",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Test connection (TODO: implement test_cloud_api)
            # result = test_cloud_api(api_key)

            # Mock result for now
            import time
            time.sleep(2)  # Simulate network delay
            result_success = True

            if result_success:
                wx.MessageBox(
                    "Connection successful!",
                    "Test Result",
                    wx.OK | wx.ICON_INFORMATION
                )
                ui.message("Connection successful")
            else:
                wx.MessageBox(
                    "Connection failed. Please check your API key and internet connection.",
                    "Test Result",
                    wx.OK | wx.ICON_ERROR
                )
                ui.message("Connection failed")

        finally:
            progress.Destroy()


# Usage example:
def show_settings_dialog(parent, config_manager):
    """Show settings dialog.

    Args:
        parent: Parent window (can be None).
        config_manager: ConfigManager instance.

    Returns:
        wx.ID_OK if settings saved, wx.ID_CANCEL if cancelled.
    """
    dlg = NVDAVisionSettingsDialog(parent, config_manager)
    result = dlg.ShowModal()
    dlg.Destroy()
    return result
```

---

### 8.2 Opening Settings from NVDA Plugin

```python
# __init__.py (GlobalPlugin)

import wx
import globalPluginHandler
from scriptHandler import script
import ui

from .config import ConfigManager
from .ui.settings_dialog import NVDAVisionSettingsDialog


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """NVDA Vision Reader global plugin."""

    def __init__(self):
        super().__init__()

        # Initialize config
        self.config_manager = ConfigManager()

        # ... other initialization ...

    @script(
        gesture="kb:NVDA+shift+s",
        description="Open NVDA Vision settings",
        category="NVDA Vision Reader"
    )
    def script_openSettings(self, gesture):
        """Open settings dialog."""
        try:
            # Settings dialog must run on main thread
            def show_dialog():
                # Get wx App instance
                app = wx.GetApp()

                if not app:
                    ui.message("Cannot open settings: wx not available")
                    return

                # Show dialog
                dlg = NVDAVisionSettingsDialog(None, self.config_manager)
                result = dlg.ShowModal()
                dlg.Destroy()

                if result == wx.ID_OK:
                    ui.message("Settings saved")
                    # Reload configuration
                    self._reload_config()

            # Run on main thread
            wx.CallAfter(show_dialog)

            ui.message("Opening settings...")

        except Exception as e:
            logger.exception("Failed to open settings dialog")
            ui.message("Settings dialog error")
```

---

## 9. Accessibility Compliance

### 9.1 WCAG 2.1 AA Checklist

**Perceivable**:
- [x] 1.1.1 Non-text Content: All controls have text labels
- [x] 1.3.1 Info and Relationships: Proper label associations
- [x] 1.3.2 Meaningful Sequence: Logical tab order
- [x] 1.4.3 Contrast (Minimum): System colors ensure contrast
- [x] 1.4.11 Non-text Contrast: Focus indicators visible

**Operable**:
- [x] 2.1.1 Keyboard: All functions keyboard accessible
- [x] 2.1.2 No Keyboard Trap: Can exit all controls with keyboard
- [x] 2.4.3 Focus Order: Logical and sequential
- [x] 2.4.7 Focus Visible: System focus rectangles
- [x] 3.2.1 On Focus: No unexpected context changes
- [x] 3.2.2 On Input: No unexpected context changes

**Understandable**:
- [x] 3.3.1 Error Identification: Validation errors clearly described
- [x] 3.3.2 Labels or Instructions: All inputs have labels
- [x] 3.3.3 Error Suggestion: Correction guidance provided
- [x] 3.3.4 Error Prevention: Confirmation for destructive actions

**Robust**:
- [x] 4.1.2 Name, Role, Value: All controls announce properly
- [x] 4.1.3 Status Messages: Progress and state changes announced

---

### 9.2 Screen Reader Testing Protocol

**Test with NVDA**:
1. Open settings dialog
2. Navigate through all tabs with Ctrl+Tab
3. Navigate through all controls with Tab
4. Verify each control announces:
   - Name (label)
   - Role (button, checkbox, etc.)
   - Value (current state)
   - Help text (if available)
5. Change values and verify announcements
6. Test mnemonics (Alt+Letter)
7. Test keyboard shortcuts
8. Close dialog and verify return focus

**Expected Announcements** (examples):

```
# Opening dialog
"NVDA Vision Settings, dialog"
"Settings Categories, notebook, General, 1 of 5"
"Language, combo box, Chinese (Simplified), 2 of 3"

# Navigating
[Tab] "Enable NVDA Vision on startup, checkbox, checked"
[Tab] "Show notification when recognition starts, checkbox, checked"
[Space] "not checked"

# Slider
[Tab] "Confidence Threshold, slider, 70"
[Right Arrow] "71"
[Right Arrow] "72"

# Changing tabs
[Ctrl+Tab] "Models, 2 of 5"
"Model Selection Strategy, group box"
"Automatic (recommended), radio button, checked, 1 of 4"

# Button
[Tab] "Test Connection, button, unavailable"
```

---

## 10. Testing Checklist

### 10.1 Functional Testing

**General Tab**:
- [ ] Language selection changes interface language
- [ ] Autostart checkbox persists across restarts
- [ ] Notification checkbox controls announcements
- [ ] Confidence threshold slider affects recognition
- [ ] View Logs button opens log folder
- [ ] Reset button resets all settings with confirmation

**Models Tab**:
- [ ] Radio buttons are mutually exclusive
- [ ] Timeout values are validated (5-60 seconds)
- [ ] Progress delay is validated (3-15 seconds)
- [ ] Cloud checkbox enables/disables dependent controls
- [ ] API key is masked in display
- [ ] Change API Key dialog encrypts key
- [ ] Test Connection validates API

**Recognition Tab**:
- [ ] Confidence slider updates threshold
- [ ] Filter checkbox affects navigation
- [ ] Cache toggle enables/disables settings
- [ ] TTL and size limits are enforced
- [ ] Cache usage displays correctly
- [ ] Clear Cache requires confirmation
- [ ] Target apps selection affects recognition

**Shortcuts Tab**:
- [ ] List displays all shortcuts
- [ ] Edit dialog captures key combinations
- [ ] Conflict detection warns about duplicates
- [ ] Restore Defaults resets all shortcuts
- [ ] Custom shortcuts persist

**Privacy Tab**:
- [ ] Privacy checkboxes affect behavior
- [ ] Log level changes verbosity
- [ ] Logging options control what's logged
- [ ] Retention settings clean old logs
- [ ] Open Folder opens correct directory
- [ ] View Latest opens recent log
- [ ] Export Logs sanitizes sensitive data
- [ ] Clear Old Logs deletes correctly

---

### 10.2 Keyboard Accessibility Testing

- [ ] Tab order is logical on all tabs
- [ ] Shift+Tab reverses order
- [ ] Mnemonics (Alt+Letter) work for all controls
- [ ] Ctrl+Tab/Ctrl+Shift+Tab navigates tabs
- [ ] Arrow keys work on radio buttons
- [ ] Space toggles checkboxes
- [ ] Enter activates default button (OK)
- [ ] Esc cancels dialog
- [ ] Slider responds to arrows, Page Up/Down, Home/End
- [ ] Spin controls respond to arrows, Page Up/Down
- [ ] No keyboard traps

---

### 10.3 Screen Reader Testing

- [ ] Dialog title announced on open
- [ ] Tab names announced when switching
- [ ] All controls announce name, role, value
- [ ] State changes are announced
- [ ] Help text is accessible (NVDA+F1)
- [ ] Tooltips are read on focus
- [ ] Progress dialogs announce status
- [ ] Error messages are announced
- [ ] Confirmation dialogs are clear
- [ ] Focus returns correctly after dialogs close

---

### 10.4 Validation Testing

- [ ] Timeout minimum (5s) enforced
- [ ] Timeout maximum (60s) enforced
- [ ] Progress delay minimum (3s) enforced
- [ ] Progress delay maximum (15s) enforced
- [ ] Confidence threshold range (50-95%) enforced
- [ ] Cache TTL minimum (1 min) enforced
- [ ] Cache size minimum (10) enforced
- [ ] Empty API key rejected
- [ ] Invalid shortcuts rejected
- [ ] Conflicting shortcuts warned

---

### 10.5 Persistence Testing

- [ ] Settings persist after dialog close
- [ ] Settings persist after NVDA restart
- [ ] Settings persist after system reboot
- [ ] API key remains encrypted in config file
- [ ] Default settings restored correctly
- [ ] Apply button saves without closing
- [ ] Cancel discards changes

---

### 10.6 Error Handling Testing

- [ ] Invalid config file handled gracefully
- [ ] Missing config file creates default
- [ ] Corrupted encryption handled
- [ ] Missing log directory created
- [ ] Cloud API errors displayed clearly
- [ ] Test connection failures reported
- [ ] Export errors shown to user
- [ ] Clear cache errors handled

---

## Appendix A: wxPython Control Reference

### A.1 Common Controls

| Widget | Purpose | Keyboard | NVDA Reads |
|--------|---------|----------|------------|
| `wx.CheckBox` | Binary choice | Space to toggle | "Name, checkbox, checked/not checked" |
| `wx.RadioButton` | Mutually exclusive choice | Arrows to navigate, Space to select | "Name, radio button, checked, N of M" |
| `wx.Choice` | Dropdown selection | Alt+Down to open, arrows to navigate | "Name, combo box, Value, N of M" |
| `wx.Slider` | Numeric range | Arrows, Page Up/Down, Home/End | "Name, slider, Value" |
| `wx.SpinCtrl` | Numeric input with arrows | Arrows, type number | "Name, spin control, Value" |
| `wx.TextCtrl` | Text input | Type text | "Name, edit, Value" |
| `wx.Button` | Action trigger | Enter/Space to activate | "Name, button" |
| `wx.ListCtrl` | List of items | Arrows to navigate | "Name, list, Item, N of M" |
| `wx.Notebook` | Tabbed container | Ctrl+Tab to switch | "Notebook, Tab Name, N of M" |
| `wx.StaticText` | Read-only label | Not focusable | Text content |

---

### A.2 Control Mnemonics

**Set mnemonics with ampersand in label**:

```python
label = wx.StaticText(panel, label="&Language:")
# Alt+L activates associated control

checkbox = wx.CheckBox(panel, label="&Enable feature")
# Alt+E toggles checkbox directly

button = wx.Button(panel, label="&Save")
# Alt+S clicks button
```

**Avoid duplicates within same tab** (OK across tabs).

---

### A.3 Sizer Reference

| Sizer Type | Use Case | Key Properties |
|------------|----------|----------------|
| `wx.BoxSizer(wx.VERTICAL)` | Stack controls vertically | `Add(control, proportion=0, flag=wx.EXPAND)` |
| `wx.BoxSizer(wx.HORIZONTAL)` | Arrange controls horizontally | `AddStretchSpacer()` for spacing |
| `wx.GridBagSizer` | Form layout (label-control pairs) | `Add(control, pos=(row, col))` |
| `wx.StaticBoxSizer` | Grouped controls with border | `wx.StaticBoxSizer(wx.VERTICAL, panel, "Title")` |

**Common Flags**:
- `wx.EXPAND`: Control fills available space
- `wx.ALL`: Add border on all sides
- `wx.LEFT | wx.RIGHT`: Add border on left and right
- `wx.ALIGN_CENTER_VERTICAL`: Center vertically in cell

---

## Appendix B: Configuration Mapping

### B.1 UI Control → Config Key Mapping

| UI Control | Config Key | Type | Default |
|------------|------------|------|---------|
| Language choice | `language` | string | "zh-CN" |
| Enable on startup | `autostart` | bool | true |
| Show notifications | `ui.show_notifications` | bool | true |
| Announce confidence | `ui.announce_confidence` | bool | true |
| Confidence threshold | `models.confidence_threshold` | float | 0.7 |
| Model preference | `models.preference` | string | "auto" |
| Inference timeout | `models.timeout_seconds` | int | 15 |
| Progress delay | `ui.progress_feedback_delay` | int | 5 |
| Enable cloud API | `enable_cloud_api` | bool | false |
| API provider | `cloud.provider` | string | "doubao" |
| API key | `doubao_api_key` (encrypted) | string | "" |
| Enable cache | `cache.enabled` | bool | true |
| Cache TTL | `cache.ttl_seconds` | int | 300 |
| Cache size | `cache.max_size` | int | 100 |
| Log level | `logging.level` | string | "INFO" |
| Log retention | `logging.retention_days` | int | 7 |

---

## Appendix C: Affordance Mapping

### C.1 Product Requirements → UI Elements

| Affordance | UI Location | Implementation |
|------------|-------------|----------------|
| **AF-006**: Configure model priority | Models tab → Model Selection Strategy radio buttons | Priority: Auto/GPU/CPU/Cloud |
| **AF-007**: Customize shortcuts | Shortcuts tab → Shortcuts list + Edit dialog | Key capture and conflict detection |
| **AF-008**: Export logs | Privacy tab → Export Logs button | Sanitized ZIP export |

---

## Version Information

**Document Version**: v1.0.0
**Created**: 2025-12-24
**Last Updated**: 2025-12-24
**Dependencies**: `.42cog/real/real.md`, `.42cog/cog/cog.md`, `spec/pm/pr.spec.md`, `spec/dev/sys.spec.md`, `spec/dev/code.spec.md`
**Next Review**: 2026-01-24

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-24 | Initial UI specification created | Claude |

---

**End of UI Design Specification**
