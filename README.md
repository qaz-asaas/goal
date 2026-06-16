# 🎯 目标储蓄应用

一个简洁美观的安卓目标储蓄管理应用，帮助您追踪和管理储蓄目标。

## ✨ 功能特点

- 📋 **目标管理**：添加、编辑和删除储蓄目标
- 💰 **金额追踪**：记录已存金额，自动计算剩余金额
- 📊 **进度显示**：可视化进度条，直观展示完成进度
- 👤 **个人中心**：自定义头像和昵称
- 🎨 **美观界面**：现代化UI设计，清新简洁

## 📱 下载安装

### 方法一：从GitHub Releases下载

1. 访问项目的 [Releases](../../releases) 页面
2. 下载最新的 `.apk` 文件
3. 在手机上打开下载的APK文件
4. 如果提示"未知来源"，请在设置中允许安装未知来源应用
5. 按照提示完成安装

### 方法二：从GitHub Actions下载

1. 点击项目页面的 **Actions** 标签
2. 选择最新的成功构建（绿色勾标记）
3. 在页面底部的 **Artifacts** 区域下载 `goal-app`
4. 解压后得到 `.apk` 文件
5. 在手机上安装APK

## 🔧 本地打包

### 使用GitHub Actions（推荐）

1. Fork本项目到您的GitHub账号
2. 进入Actions页面，点击 "Build Android APK"
3. 点击 "Run workflow" 开始构建
4. 等待构建完成后下载APK

### 使用WSL本地打包

```bash
# 1. 安装WSL
wsl --install -d Ubuntu

# 2. 在WSL中安装依赖
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev automake python3 python3-pip

# 3. 安装Buildozer
pip3 install buildozer cython

# 4. 进入项目目录
cd /mnt/d/pythonwj/goal

# 5. 打包APK
buildozer android debug
```

## 📋 使用说明

1. **添加目标**：点击"+ 添加目标"按钮，输入目标名称和目标金额
2. **添加金额**：点击目标卡片上的"+ 添加金额"按钮，输入要添加的金额
3. **删除目标**：点击"删除"按钮，确认后删除目标
4. **个人设置**：点击底部"我的"按钮，可以更换头像和昵称

## ⚙️ 权限说明

应用需要以下权限：
- 📷 相机：用于拍照设置头像
- 📁 存储读写：用于保存目标和头像图片
- 🌐 网络：用于网络功能

## 📄 许可证

MIT License
