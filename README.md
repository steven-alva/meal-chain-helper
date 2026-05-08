# 接龙点餐小助手

一个给主管日常用的微信群接龙点餐小工具。

它分成两个独立功能：

- **整理下单清单**：主管把群里的接龙直接贴进去，就能看到可视化点菜清单。
- **发布接龙菜单**：需要发起接龙时，再勾选今天菜单并生成群文案。

## 主管怎么安装

打开 Mac 的「终端」，复制下面几行后回车：

```bash
cd ~/Desktop
rm -rf meal-chain-helper meal-chain-helper-main meal-chain-helper.zip
curl -L --fail -o meal-chain-helper.zip https://github.com/steven-alva/meal-chain-helper/archive/refs/heads/main.zip
unzip -q meal-chain-helper.zip
mv meal-chain-helper-main meal-chain-helper
cd meal-chain-helper
chmod +x start.command
./start.command
```

这套方式不要求电脑提前安装 Python。第一次启动会自动准备 Python 和小助手环境，需要联网，可能需要一两分钟。

如果网页没有自动打开，手动访问：

```text
http://localhost:8501
```

## 以后怎么打开

以后不用重新下载。打开「终端」，复制下面这一行后回车：

```bash
cd ~/Desktop/meal-chain-helper && ./start.command
```

## 以后怎么更新

如果我这边更新了小助手，主管复制：

```bash
cd ~/Desktop
rm -rf meal-chain-helper meal-chain-helper-main meal-chain-helper.zip
curl -L --fail -o meal-chain-helper.zip https://github.com/steven-alva/meal-chain-helper/archive/refs/heads/main.zip
unzip -q meal-chain-helper.zip
mv meal-chain-helper-main meal-chain-helper
cd meal-chain-helper
chmod +x start.command
./start.command
```

## 主管今天怎么整理下单

1. 打开小助手。
2. 把微信群接龙粘贴到「今日接龙」。
3. 点「整理下单清单」。
4. 看「主管查看版下单清单」，按清单下单。

这一步不需要先选菜单。没选菜单时，小助手会先按接龙里的编号生成「待匹配菜单」清单；如果今天已经选过菜单，就会自动归到具体餐厅和菜品。

## 怎么发布今日接龙

1. 在「发布接龙用」下面的「今日菜单」里选今天要发的菜。
2. 「今日标题」会自动带当天日期，例如 `5/9`。
3. 点「生成今日群文案」，复制到微信群。

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
