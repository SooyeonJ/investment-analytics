"""
리밸런싱 전후 시뮬레이션 차트
-------------------------------
사용법:
  python 02_리밸런싱_시뮬레이션.py --file <xlsx경로> [--output <png경로>] [--month 6]

인수:
  --file    : GAPS 포트폴리오 xlsx 파일 경로 (필수)
  --output  : 저장할 png 경로 (기본: 스크립트와 같은 폴더)
  --month   : 운용 월 (기본: 6)
"""

import argparse
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pykrx import stock
from datetime import datetime, timedelta
import os

parser = argparse.ArgumentParser()
parser.add_argument('--file',   required=True, help='xlsx 파일 경로')
parser.add_argument('--output', default=None,  help='출력 png 경로')
parser.add_argument('--month',  type=int, default=6, help='운용 월 (기본: 6)')
args = parser.parse_args()

OUTPUT = args.output or os.path.join(os.path.dirname(args.file), f'02_리밸런싱_시뮬레이션_{args.month}월.png')

nanum = [f for f in fm.findSystemFonts() if 'Nanum' in f]
if nanum:
    plt.rcParams['font.family'] = fm.FontProperties(fname=nanum[0]).get_name()
else:
    plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

BG       = '#F4F7FC'
NAVY     = '#0A1F4B'
NAVY_MID = '#1A3A6B'
GRAY_LINE= '#D4DCF0'
GRAY_TEXT= '#7A8FAD'
GRAY_MUT = '#9AADCC'
GREEN    = '#00A651'
RED      = '#D94444'
GOLD     = '#C9A84C'
WHITE    = '#FFFFFF'

# ── 리밸런싱 정보 (매월 변경)
SOLD_TICKER   = '451530'
SOLD_NAME     = 'TIGER 국고채30년스트립액티브'
SOLD_ROW      = '  - TIGER 국고채30년스트립액티브'
BOUGHT_ROW    = '  - RISE 단기특수은행채액티브'
BOUGHT_NAME   = 'RISE 단기특수은행채액티브'
REBAL_DATE    = '2026-06-18'
EVAL_END_DATE = '20260630'

df = pd.read_excel(args.file, header=0, index_col=0)
df = df[sorted(df.columns)]
dates = df.columns

sold_series   = df.loc[SOLD_ROW]
bought_series = df.loc[BOUGHT_ROW]

sold_held  = sold_series[sold_series > 0]
sold_base  = sold_held.iloc[0]
sold_dates = sold_held.index

bought_held = bought_series[bought_series > 0]
bought_base = bought_held.iloc[0]
bought_dates = bought_held.index

actual_dates = list(sold_dates) + list(bought_dates)
actual_cum   = list((sold_held / sold_base - 1) * 100) + \
               list(((bought_held / bought_base - 1) * 100) + ((sold_held.iloc[-1] / sold_base - 1) * 100))

print(f"가상 시나리오용 가격 수집 중... ({SOLD_NAME})")
start_str = sold_dates[0].strftime('%Y%m%d')
px = stock.get_market_ohlcv_by_date(start_str, EVAL_END_DATE, SOLD_TICKER)
if px.empty:
    raise ValueError("가격 데이터를 가져오지 못했습니다. 티커를 확인하세요.")

px_close   = px['종가']
hypo_base  = px_close.iloc[0]
hypo_cum   = (px_close / hypo_base - 1) * 100
hypo_dates = px_close.index

print(f"실제 누적수익률 (최종일): {actual_cum[-1]:.2f}%")
print(f"가상 누적수익률 (최종일): {hypo_cum.iloc[-1]:.2f}%")
print(f"리밸런싱 효과: {actual_cum[-1] - hypo_cum.iloc[-1]:+.2f}%p")

all_dates   = sorted(set(list(actual_dates) + list(hypo_dates)))
date_to_idx = {d: i for i, d in enumerate(all_dates)}

actual_x = [date_to_idx[d] for d in actual_dates]
hypo_x   = [date_to_idx[pd.Timestamp(d)] for d in hypo_dates]

fig, ax = plt.subplots(figsize=(12, 6.5))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.plot(actual_x, actual_cum, color=NAVY, linewidth=2.5, marker='o', markersize=4,
        zorder=4, label=f'실제 운용 (매도→{BOUGHT_NAME})')
ax.plot(hypo_x, hypo_cum.values, color=GOLD, linewidth=2.5, linestyle='--', marker='o', markersize=4,
        zorder=3, label=f'가상 보유 ({SOLD_NAME} 유지 시)')

rebal_idx = date_to_idx.get(pd.Timestamp(REBAL_DATE))
if rebal_idx is not None:
    ax.axvline(rebal_idx, color=RED, linewidth=1.2, linestyle=':', alpha=0.7, zorder=2)
    ymax = max(max(actual_cum), hypo_cum.max()) * 0.85
    ax.text(rebal_idx, ymax, ' 리밸런싱\n 실행일', fontsize=8.5, color=RED, va='top', fontweight='bold')

ax.axhline(0, color=NAVY, linewidth=1, alpha=0.2, zorder=1)

tick_idx = list(range(0, len(all_dates), max(1, len(all_dates)//8)))
ax.set_xticks(tick_idx)
ax.set_xticklabels([all_dates[i].strftime('%m/%d') for i in tick_idx], fontsize=9, color=GRAY_MUT)

ax.set_ylabel('누적수익률 (%)', fontsize=9.5, color=GRAY_TEXT)
ax.tick_params(axis='y', colors=GRAY_MUT, labelsize=9)
ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=GRAY_LINE)
ax.set_axisbelow(True)
for spine in ['top','right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_color(GRAY_LINE)
ax.spines['bottom'].set_color(GRAY_LINE)

ax.legend(loc='best', fontsize=9.5, frameon=False, labelcolor=GRAY_TEXT)

fig.text(0.04, 0.97, '리밸런싱 전후 시뮬레이션', fontsize=15, fontweight='bold', color=NAVY, va='top')
fig.text(0.04, 0.91, f'{SOLD_NAME} → {BOUGHT_NAME}  ·  실행일 {REBAL_DATE}',
         fontsize=10, color=GRAY_TEXT, va='top')
fig.add_artist(plt.Line2D([0.04,0.5],[0.885,0.885], transform=fig.transFigure, color=GREEN, linewidth=1.5, alpha=0.7))
fig.add_artist(plt.Line2D([0.5,0.96],[0.885,0.885], transform=fig.transFigure, color=GRAY_LINE, linewidth=1.5))

tag_ax = fig.add_axes([0.86, 0.915, 0.10, 0.045])
tag_ax.set_facecolor(NAVY)
tag_ax.text(0.5, 0.5, '불사알파', ha='center', va='center', fontsize=9, fontweight='bold', color=WHITE, transform=tag_ax.transAxes)
tag_ax.set_xticks([]); tag_ax.set_yticks([])
for sp in tag_ax.spines.values(): sp.set_visible(False)

effect = actual_cum[-1] - hypo_cum.iloc[-1]
badge_ax = fig.add_axes([0.04, 0.02, 0.28, 0.048])
badge_ax.set_facecolor(NAVY)
badge_ax.text(0.5, 0.5, f'리밸런싱 효과   {effect:+.2f}%p',
              ha='center', va='center', fontsize=11, fontweight='bold', color=WHITE, transform=badge_ax.transAxes)
badge_ax.set_xticks([]); badge_ax.set_yticks([])
for sp in badge_ax.spines.values(): sp.set_visible(False)

fig.text(0.96, 0.03, 'DB GAPS 2026', fontsize=9, color=GRAY_MUT, ha='right', va='bottom', fontweight='bold')

plt.tight_layout(rect=[0, 0.07, 1, 0.88])
plt.savefig(OUTPUT, dpi=180, bbox_inches='tight', facecolor=BG)
print(f"\n완료 → {OUTPUT}")
