<p align="center">
  <img src="docs/assets/icon-256.png" width="88" height="88" alt="SupTools" />
</p>

<h1 align="center">SupTools</h1>

<p align="center">
  <strong>超级工具箱</strong> — Mac 常用工具合集<br/>
  总览 · 清理 · 卸载 · 启动项 · 截图录屏 · 权限
</p>

<p align="center">
  <b>中文</b> · <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/linux503/suptools/releases/latest"><img src="https://img.shields.io/github/v/release/linux503/suptools?style=flat-square&color=0d7a6c" alt="Release" /></a>
  <a href="https://github.com/linux503/suptools/releases"><img src="https://img.shields.io/badge/macOS-13%2B-111111?style=flat-square" alt="macOS 13+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square" alt="License" /></a>
</p>

<p align="center">
  <a href="https://github.com/linux503/suptools/releases/download/v1.29.0/SupTools-1.29.0-Universal.dmg"><strong>下载 Universal DMG</strong></a>
  ·
  <a href="https://linux503.github.io/suptools/">官网</a>
  ·
  <a href="https://github.com/linux503/suptools/releases">全部版本</a>
</p>

---

<p align="center">
  <img src="docs/assets/shot-overview-web.jpg" width="860" alt="SupTools 总览" />
</p>

---

## 功能

一个窗口完成 Mac 日常维护。Universal 安装包同时支持 M 系列与 Intel。

| 模块 | 做什么 |
|------|--------|
| **总览** | CPU / 内存 / 网络 / 磁盘，以及占用最高的进程 |
| **清理** | 缓存、浏览器、开发文件、废纸篓 |
| **卸载** | 应用本体 + 关联残留 |
| **启动项** | 登录项与 LaunchAgent |
| **截图 / 录屏** | 框选 / 窗口 / 全屏，标记与快捷键 |
| **权限** | 集中开通系统隐私权限 |

<p align="center">
  <img src="docs/assets/shot-clean-web.jpg" width="270" alt="清理" />
  <img src="docs/assets/shot-uninstall-web.jpg" width="270" alt="卸载" />
  <img src="docs/assets/shot-startup-web.jpg" width="270" alt="启动项" />
</p>

## 安装

推荐 Universal 综合版：

**[SupTools-1.29.0-Universal.dmg](https://github.com/linux503/suptools/releases/download/v1.29.0/SupTools-1.29.0-Universal.dmg)**

| 包 | 文件 |
|----|------|
| **Universal（推荐）** | `SupTools-*-Universal.dmg` — M 系列与 Intel |
| Apple Silicon | `SupTools-*-AppleSilicon.dmg` |
| Intel | `SupTools-*-Intel.dmg` |

打开 DMG → 拖到「应用程序」→ 打开后进 **权限** 按提示开通。需要 **macOS 13+**。

### 从源码安装

```bash
git clone https://github.com/linux503/suptools.git
cd suptools
python3 -m pip install -r requirements.txt
./Scripts/install-to-applications.sh
```

开发运行：

```bash
python3 main.py
```

## 其它工具

| 应用 | 说明 |
|------|------|
| [Flare Pro](https://github.com/linux503/Flare) | 截图与录屏 |
| [ZipX](https://github.com/linux503/ZipX) | 压缩 / 解压 / 预览 |
| [MacText](https://github.com/linux503/MacText) | 原生文本编辑器 |
| [FilesDesk](https://github.com/linux503/FilesDesk) | 批量重命名 |
| [MacFan](https://github.com/linux503/MacFan) | 风扇转速 |

## 许可

[MIT](LICENSE)
