<p align="center">
  <img src="docs/assets/icon-256.png" width="96" height="96" alt="SupTools" />
</p>

<h1 align="center">SupTools</h1>

<p align="center">
  <strong>超级工具箱</strong> · Mac 常用工具合集
</p>

<p align="center">
  总览 · 清理 · 卸载 · 启动项 · 截图录屏 · 权限
</p>

<p align="center">
  <a href="https://linux503.github.io/suptools/"><img src="https://img.shields.io/badge/Website-引导页-0a7a92?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/linux503/suptools"><img src="https://img.shields.io/badge/macOS-13%2B-111111?style=flat-square" alt="macOS" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square" alt="License" /></a>
</p>

<p align="center">
  <a href="https://linux503.github.io/suptools/">引导页</a>
  ·
  <a href="https://github.com/linux503/suptools/releases/latest">下载</a>
</p>

---

<p align="center">
  <img src="docs/assets/shot-overview-web.jpg" width="860" alt="SupTools 总览" />
</p>

---

## 功能

|  | 做什么 |
|:--|:---|
| **总览** | CPU / 内存 / 网络 / 磁盘 + 占用最高进程 |
| **清理** | 缓存、浏览器、开发文件、废纸篓 |
| **卸载** | 应用 + 关联残留 |
| **启动项** | 登录项与 LaunchAgent |
| **截图 / 录屏** | 框选 / 窗口 / 全屏，标记与快捷键 |
| **权限** | 集中开通系统隐私权限 |

---

## 安装

前往最新 Release 下载安装包（推荐 Universal 综合版）：

**https://github.com/linux503/suptools/releases/latest**

| 包 | 文件 |
|:---|:---|
| **Universal（推荐）** | `SupTools-*-Universal.dmg` — 同时支持 M 系列与 Intel |
| Apple Silicon | `SupTools-*-AppleSilicon.dmg` |
| Intel | `SupTools-*-Intel.dmg` |

打开 DMG → 拖到「应用程序」→ 打开后进 **权限** 按提示开通。

### 源码安装

```bash
git clone https://github.com/linux503/suptools.git
cd suptools
python3 -m pip install -r requirements.txt
./Scripts/install-to-applications.sh
```

---

## 开发

```bash
python3 main.py
```

---

## 许可

[MIT](LICENSE)
