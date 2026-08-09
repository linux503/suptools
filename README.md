<p align="center">
  <img src="docs/assets/icon-256.png" width="120" height="120" alt="SupTools" />
</p>

<h1 align="center">SupTools</h1>

<p align="center">
  <strong>超级工具箱</strong> · macOS 一站式系统工具
</p>

<p align="center">
  监控 · 清理 · 卸载 · 启动项 · 截图录屏 · 权限引导
</p>

<p align="center">
  <a href="https://linux503.github.io/suptools/"><img src="https://img.shields.io/badge/Website-引导页-0a7a92?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/linux503/suptools"><img src="https://img.shields.io/badge/macOS-13%2B-111111?style=flat-square" alt="macOS" /></a>
  <a href="https://github.com/linux503/suptools"><img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square" alt="Python" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square" alt="License" /></a>
</p>

<p align="center">
  <a href="https://linux503.github.io/suptools/">产品引导页</a>
  ·
  <a href="#快速安装">快速安装</a>
  ·
  <a href="#功能">功能</a>
  ·
  <a href="#权限">权限</a>
</p>

---

## 为什么是 SupTools

原生 macOS 应用（Python + PyObjC / WKWebView），不是 Electron。  
菜单栏常驻 + 毛玻璃面板，把日常运维工具收进一个窗口。

---

## 功能

|  | 模块 | 做什么 |
|:--:|:---|:---|
| 01 | **监控** | CPU / 内存 / 磁盘 / 网络 / 进程总览 |
| 02 | **清理** | 缓存、浏览器、开发工具、Docker、大文件、废纸篓 |
| 03 | **卸载** | 应用本体 + Library 关联残留扫描 |
| 04 | **启动项** | 登录项与 LaunchAgent 开关 |
| 05 | **截图 / 录屏** | 框选、窗口、全屏；标记编辑与全局快捷键 |
| 06 | **连通性** | DNS / TCP / HTTP 延迟检测 |
| 07 | **权限** | 集中引导系统隐私权限，开启后显示成功 |

---

## 快速安装

```bash
git clone https://github.com/linux503/suptools.git
cd suptools
python3 -m pip install -r requirements.txt
./Scripts/install-to-applications.sh
```

安装完成后：

1. 打开 `/Applications/SupTools.app`
2. 进入 **工具 → 权限**
3. 开通推荐权限后再使用清理 / 截图 / 录屏等功能

---

## 开发运行

```bash
python3 main.py
```

### 重新生成图标

```bash
python3 Scripts/generate-app-icon.py
./Scripts/install-to-applications.sh
```

---

## 权限

| 权限 | 用途 | 是否推荐 |
|:---|:---|:---:|
| 屏幕录制 | 截图 · 录屏 | 必需 |
| 辅助功能 | 全局快捷键 | 必需 |
| 自动化 | 启动项 · 剪贴板 · Finder | 必需 |
| 完全磁盘访问 | 清理 · 卸载扫全 | 建议 |
| 文件与文件夹 | 大文件 / 安装包 | 建议 |
| 麦克风 | 录屏旁白 | 可选 |
| 通知 | 阈值告警 | 可选 |

应用内已有 **权限引导页**：开启后会自动检测，并提示「已开启」。

---

## 技术栈

- **Python 3.9+** + **PyObjC**（AppKit / WebKit）
- 原生菜单栏、透明毛玻璃窗口
- 无 Electron / 无常驻后台服务依赖

---

## 目录结构

```text
suptools/
├── docs/                 # GitHub Pages 引导页
├── Scripts/              # 打包 / 安装 / 图标生成
├── Resources/            # Info.plist · 图标资源
├── systemmonit/          # 应用源码
├── main.py               # 入口
└── requirements.txt
```

---

## 许可

[MIT](LICENSE) © SupTools
