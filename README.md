# SupTools · 超级工具箱

macOS 一站式系统工具：监控、清理、卸载、启动项、截图录屏与权限引导。

[![macOS](https://img.shields.io/badge/macOS-13%2B-black)](#)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](#)

**产品页：** 打开仓库的 [GitHub Pages](./docs/index.html)（推送后启用 Pages 即可在线访问）。

## 功能

| 模块 | 说明 |
|------|------|
| 监控 | CPU / 内存 / 磁盘 / 网络 / 进程总览 |
| 清理 | 缓存、浏览器、开发工具、Docker、大文件、废纸篓 |
| 卸载 | 应用 + 关联残留扫描 |
| 启动项 | 登录项与 LaunchAgent 开关 |
| 截图 / 录屏 | 框选、窗口、全屏；标记编辑与快捷键 |
| 连通性 | DNS / TCP / HTTP 检测 |
| 权限 | 集中引导系统隐私权限，开启后显示成功 |

## 快速安装

```bash
git clone https://github.com/linux503/suptools.git
cd suptools
python3 -m pip install -r requirements.txt
./Scripts/install-to-applications.sh
```

安装后打开 `/Applications/SupTools.app`，到 **工具 → 权限** 开通推荐权限。

## 开发运行

```bash
python3 main.py
```

## 重新生成图标

```bash
python3 Scripts/generate-app-icon.py
./Scripts/install-to-applications.sh
```

## 技术栈

- Python + PyObjC（AppKit / WKWebView）
- 原生菜单栏 + 透明毛玻璃窗口
- 无 Electron

## 许可

MIT
