[app]

title = 目标储蓄
package.name = goal
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# 依赖: pyjnius 是 android 模块操作的关键
requirements = python3,kivy==2.2.1,plyer,android,pyjnius
orientation = portrait
fullscreen = 0

# Android 配置
android.api = 33
android.ndk = 25b
android.buildtools = 33.0.0
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = True
android.enable_androidx = True

# 权限
android.add_permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# 添加 assets 文件
android.add_assets = goals.json,user_info.json

# 启用日志方便调试
android.logcat_filters = *:S python:D

# 启用 AndroidX / Jetifier
android.gradle_dependencies = androidx.appcompat:appcompat:1.3.1

# Python 与 Kivy 版本
osx.python_version = 3
osx.kivy_version = 2.2.1

# 忽略 plyer 的相机/音频等不需要的模块，减少包体积
android.add_jar = 

[buildozer]
log_level = 2
warn_on_root = 1