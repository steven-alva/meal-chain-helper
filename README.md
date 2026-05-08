# 接龙点餐小助手

一个给主管日常用的微信群接龙点餐小工具。

它可以做三件事：

- 勾选今天要发的菜单。
- 生成可以直接发微信群的接龙文案。
- 接龙结束后，把群里的接龙整理成主管查看版下单清单。

## 主管怎么安装

打开 Mac 的「终端」，复制下面几行后回车：

```bash
cd ~/Desktop
git clone https://github.com/steven-alva/meal-chain-helper.git
cd meal-chain-helper
./start.command
```

第一次启动会自动准备环境，可能需要一两分钟。

如果提示仓库不存在或没有权限，需要先把主管的 GitHub 账号加入这个 private 仓库。

如果电脑提示要安装 Command Line Tools，点「安装」即可。安装完成后重新复制上面的命令。

如果网页没有自动打开，手动访问：

```text
http://localhost:8501
```

## 以后怎么打开

以后不用重新下载。打开「终端」，复制：

```bash
cd ~/Desktop/meal-chain-helper
./start.command
```

## 以后怎么更新

如果我这边更新了小助手，主管复制：

```bash
cd ~/Desktop/meal-chain-helper
git pull
./start.command
```

## 今天怎么用

1. 在「今日菜单」里勾选今天要发的菜。
2. 点「生成今日群文案」，复制到微信群。
3. 接龙结束后，把微信群接龙粘贴到「今日接龙」。
4. 点「整理下单清单」。
5. 看「主管查看版下单清单」，按餐厅和菜品下单。

## 菜单怎么维护

页面底部有「菜单库维护：导入历史菜单 / 保存模板」。

平时不用管。只有换菜单时再打开：

1. 粘贴历史菜单文本。
2. 点「提取菜单」。
3. 确认没问题后点「保存模板」。

## 开发者检查

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

## 当前边界

- 不会自动下单。
- 不会自动付款。
- 不会登录外卖平台。
- 不会识别图片。
- 不会记录人员名单。
