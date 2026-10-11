// 全片文字都在这里：改台词只改这个文件，改完跑一次 `python3 gen_chars.py`
export const FPS = 30;
export const DURATION = 175; // 与随附的默认背景音乐配合

// 字幕：【】= 暖色高亮（刀子），〖〗= 冷色；每屏最多两行、每句至少 1.5 秒、单行超过约 25 字就拆
export type Cap = {s: number; e: number; text: string; flash?: number};
export const captions: Cap[] = [
  {s: 0.3, e: 2.9, text: '这是开场第一句，6 秒内进片名。'},
  {s: 3.1, e: 5.9, text: '刀子落在【你】身上，冷色写〖另一边〗。'},
  {s: 7.0, e: 10.5, text: '片名'},
];

// 左上 HUD：大字（年份/时刻/关键词）+ 小字（场记）
export type Hud = {s: number; e: number; big: string; small: string; cold?: boolean};
export const huds: Hud[] = [
  {s: 0.2, e: 5.9, big: '23:41', small: '昨天 · 你的床头'},
];

// 右上引用卡：seal 只用「研究 / 报道 / 推测 / 猜想」，推测和猜想自动变冷色章
export type Cite = {s: number; e: number; year: string; latin: string; title: string; author: string; seal: string};
export const cites: Cite[] = [
  {s: 3.1, e: 5.9, year: '2024 · 作者', latin: 'Original English Title', title: '《片中短题》', author: '一句话说清它证明了什么，不加码', seal: '研究'},
];
