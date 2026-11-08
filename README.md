# virtual-wardrobe

[English](README.en.md)

把衣服照片和购物小票整理成 Mac 上的衣橱，再让 ChatGPT 用你已有的衣服搭配造型。

## 第一次使用

打开插件，发一句「我该怎么开始？」。你也可以直接这样说：

- **拍照入柜**：上传一张衣服照片，说「把这件加进衣橱」。确认颜色、类别和描述后保存。支持 JPEG、PNG、WebP，单张最大 5 MiB。
- **从小票添加**：「在 Gmail 里找我最近买衣服的小票。」也可以用已连接的 Apple Mail，或直接粘贴小票。选出留下的单品后，插件会记住你的选择。只有文字记录时，它会询问是否查找商品图，并优先选用款式和颜色相符的单品平铺图。
- **选穿搭**：「用我的白色上衣搭一套正式面试装。」插件会展示已有单品的照片，并说明还缺哪些衣服。「想穿得像童话里的海妖」这类开放式请求会在衣橱搭得出来时并排给出两套造型。
- **调整搭配**：「保留第一套的裤子，把上衣换掉，让整体更神秘一点。」你也可以告诉它你喜欢的松紧程度，或自愿提供身高、体重、内长等信息，作为本次聊天的搭配参考。

## 在 Mac 上安装

需要 Python 3.11 或更高版本，以及支持本地插件的 Codex CLI。在终端运行：

```sh
git clone https://github.com/mikotokuroko/virtual-wardrobe.git
cd virtual-wardrobe
pilot="$HOME/.local/share/wardrobe-pilot"
mkdir -p "$pilot"
cp wardrobe.py wardrobe_local.py "$pilot/"
cp -R skills "$pilot/"
python3 -m venv "$pilot/venv"
"$pilot/venv/bin/python" -m pip install -r requirements.txt
codex plugin marketplace add "$PWD/desktop"
codex plugin add wardrobe-local@wardrobe-pilot
```

保留下载的仓库目录，重启桌面应用，在新聊天中选择 **virtual-wardrobe**。

## 本地存储

衣橱数据库和用于展示的图片缓存保存在 `~/Library/Application Support/Virtual Wardrobe Pilot/`。问「我的衣橱在 Mac 上占了多少空间？」即可查看当前的衣橱用量和插件安装大小。
