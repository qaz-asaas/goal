[app]

title = 目标储蓄
package.name = goal
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy,plyer
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.api = 33
android.ndk = 25b
android.buildtools = 33.0.0
android.accept_sdk_license = True

android.add_assets = goals.json,user_info.json
android.add_permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA

[buildozer]
log_level = 2
warn_on_root = 1