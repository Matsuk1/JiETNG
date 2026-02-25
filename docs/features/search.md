# 歌曲搜索和记录查询

查找 『maimai でらっくす』 歌曲信息，获取随机歌曲，并探索完整的歌曲数据库。

## 歌曲信息搜索

通过歌曲名、缩写或关键词搜索，获取详细信息。

### 基本搜索

**命令格式：**

```
[歌曲名] + info  
[歌曲名] + song-info  
[歌曲名] + ってどんな曲
```

**示例：**

```
blew moon info  
グリーンライツ・セレナーデ ってどんな曲  
AMAZING MIGHTYYYY song-info
```

### 搜索行为

- **模糊匹配**：采用智能匹配（相似度阈值 85%）  
- **多结果返回**：最多显示 6 首匹配歌曲
- **部分名称匹配**：如 “amazing might” 可匹配 “AMAZING MIGHTYYYY!!!!!”

:::tip 搜索提示
- 可使用英文或日文名称  
- 支持全名与缩写  
- 不区分大小写  
- 特殊符号通常可省略  
:::

### 显示内容

每个结果包括：

- **歌曲标题**（英文与日文）
- **封面图**
- **艺术家**
- **版本信息**
- **可用难度**（Basic / Advanced / Expert / Master / Re:MASTER）
- **谱面定数**
- **谱面类型**（Standard / DX）
- **分类（Genre）**

---

## 按版本查看歌曲

查看某个 『maimai でらっくす』 版本新增的所有歌曲。

**命令格式：**

```
[版本名] + version  
[版本名] + version-list  
[版本名] + のバージョンリスト
```

**示例：**

```
FESTiVAL version  
BUDDiES PLUS のバージョンリスト  
Splash version-list  
でらっくす PLUS version
```

:::tip 提示
- `FESTiVAL+` 会自动识别为 `FESTiVAL PLUS`
:::

**显示内容：**
- 歌曲列表

---

## 按艺术家搜索

通过艺术家名搜索所有相关歌曲。

**命令格式：**

```
artist [关键词]
artist [关键词] [页码]
```

**示例：**

```
artist DECO*27
artist しーけー
artist Hiro 2
```

**显示内容：**
- 歌曲名称
- 艺术家名
- 谱面类型（DX / STD / UTAGE）

:::warning 仅限私聊
为防止群聊刷屏，此命令仅限私聊使用。
:::

---

## 按谱师搜索

通过谱面设计师名搜索所有相关歌曲。

**命令格式：**

```
designer [关键词]
designer [关键词] [页码]
```

**示例：**

```
designer Jack
designer はっぴー
designer rioN 3
```

**显示内容：**
- 歌曲名称
- 匹配的谱师名及对应难度标签（如 `Jack [EXP]`、`はっぴー [MAS]`）
- 谱面类型（DX / STD / UTAGE）

:::warning 仅限私聊
为防止群聊刷屏，此命令仅限私聊使用。
:::

---

## 成绩查询

查看你在某首歌的游玩记录。

**命令格式：**

```
[歌曲名] + record  
[歌曲名] + song-record  
[歌曲名] + のレコード
```

**示例：**

```
blew moon record  
オンゲキ音頭 のレコード  
AMAZING MIGHTYYYY song-record
```

:::warning 需绑定账号
成绩功能需要先绑定 SEGA ID。详见 [账户绑定](/guide/binding)
:::

**显示内容：**
- 达成率
- DX 分数
- 完成状态（FC / FC+ / AP / AP+）
- 同步状态（FS / FS+ / FDX / FDX+）
- 评级贡献值

若显示“未找到记录”：
- 可能未游玩此曲  
- 成绩未更新（尝试 `maimai update`）  
- 名称匹配错误（可先使用 info 搜索）

---

## 按等级查看成绩

查看指定等级下的全部成绩。

**命令格式：**

```
[等级] + record-list  
[等级] + records  
[等级] + のレコードリスト
```

**示例：**

```
14 record-list  
13+ のレコードリスト  
15 records
```

分页：
```
14 record-list 2  
13+ のレコードリスト 3
```

