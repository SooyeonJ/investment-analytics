"""
자산군별 수익률 기여도 분석 차트
-------------------------------
사용법:
  python 01_기여도_차트.py --file <xlsx경로> [--output <png경로>] [--month 6]

인수:
  --file    : GAPS 포트폴리오 xlsx 파일 경로 (필수)
  --output  : 저장할 png 경로 (기본: 스크립트와 같은 폴더)
  --month   : 운용 월 (6-8월)
"""

import argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np
import os

parser = argparse.ArgumentParser()
parser.add_argument('--file',   required=True, help='xlsx 파일 경로')
parser.add_argument('--output', default=None,  help='출력 png 경로')
parser.add_argument('--month',  type=int, default=6, help='운용 월 (기본: 6)')
args = parser.parse_args()

OUTPUT = args.output or os.path.join(os.path.dirname(args.file), f'01_자산군별_기여도_{args.month}월.png')

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
GREEN_A  = (0, 166/255, 81/255, 0.55)
RED      = '#D94444'
RED_A    = (220/255, 70/255, 70/255, 0.45)
WHITE    = '#FFFFFF'

df = pd.read_excel(args.file, header=0, index_col=0)
df = df[sorted(df.columns)]
dates = df.columns
start_date, end_date = dates[0], dates[-1]
total_start = df.loc['팀 전체', start_date]
total_end   = df.loc['팀 전체', end_date]
port_return = (total_end - total_start) / total_start * 100

# 자산군별 분리
asset_classes = {
    '국내주식 지수': '국내주식지수',
    '국내주식 섹터': '국내주식섹터',
    '해외주식 지수': '해외주식지수',
    '해외주식 섹터': '해외주식섹터',
    '해외채권 종합': '해외채권종합',
    '해외채권 회사채': '해외채권회사채',
    '국내채권 종합': '국내채권종합',
    '국내채권 회사채': '국내채권회사채',
    'FX 및 원자재': 'FX 및 원자재',
    '금리연계형/초단기채권': '금리연계형초단기채권',
}

results = []
for label, key in asset_classes.items():
    if key not in df.index:
        continue
    series = df.loc[key]
    held = series[series > 0]
    if len(held) == 0:
        continue
    v_start = held.iloc[0]
    v_end   = held.iloc[-1]
    weight  = v_start / total_start
    ret     = (v_end - v_start) / v_start
    contrib = weight * ret * 100
    results.append({'label': label, 'weight': weight*100, 'ret': ret*100, 'contrib': contrib})

res_df = pd.DataFrame(results).sort_values('contrib').reset_index(drop=True)
n = len(res_df)
max_abs = res_df['contrib'].abs().max() * 1.6

fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

for i in range(n):
    ax.barh(i, max_abs*2, left=-max_abs, color='#EBF0FA' if i%2==0 else BG, height=1.0, zorder=0)

for i, row in res_df.iterrows():
    v = row['contrib']
    pos = v >= 0
    ax.barh(i, v, left=0, height=0.52, color=GREEN_A if pos else RED_A, zorder=3, edgecolor='none')
    ax.plot([v,v], [i-0.26, i+0.26], color=GREEN if pos else RED, linewidth=2.5, zorder=4)
    offset = max_abs * 0.05
    if pos:
        ax.text(v+offset, i, f'+{v:.2f}%p', va='center', ha='left', fontsize=10, fontweight='bold', color='#007A3D', zorder=5)
    else:
        ax.text(v-offset, i, f'{v:.2f}%p', va='center', ha='right', fontsize=10, fontweight='bold', color='#B03030', zorder=5)
    ax.text(-max_abs-0.05, i, f'{row["weight"]:.1f}%', va='center', ha='right', fontsize=9, color=GRAY_MUT, zorder=5)

ax.axvline(0, color=NAVY, linewidth=1.2, alpha=0.2, zorder=2)
ax.set_yticks(range(n))
ax.set_yticklabels(res_df['label'], fontsize=11.5, color=NAVY_MID, fontweight='bold')
ax.set_xlim(-max_abs-0.35, max_abs+0.35)
ax.set_xlabel('수익률 기여도 (%p)', fontsize=9.5, color=GRAY_TEXT, labelpad=8)
ax.tick_params(axis='x', colors=GRAY_MUT, labelsize=9)
ax.tick_params(axis='y', length=0, pad=8)
ax.xaxis.grid(True, linestyle='--', alpha=0.3, color=GRAY_LINE, zorder=1)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_visible(False)

fig.text(0.04, 0.97, '자산군별 수익률 기여도 분석', fontsize=15, fontweight='bold', color=NAVY, va='top')
fig.text(0.04, 0.91, f'{start_date.strftime("%Y.%m.%d")} – {end_date.strftime("%Y.%m.%d")}  ·  좌측 숫자 = 월초 비중',
         fontsize=10, color=GRAY_TEXT, va='top')
fig.add_artist(plt.Line2D([0.04,0.5],[0.885,0.885], transform=fig.transFigure, color=GREEN, linewidth=1.5, alpha=0.7))
fig.add_artist(plt.Line2D([0.5,0.96],[0.885,0.885], transform=fig.transFigure, color=GRAY_LINE, linewidth=1.5))

tag_ax = fig.add_axes([0.86, 0.915, 0.10, 0.045])
tag_ax.set_facecolor(NAVY)
tag_ax.text(0.5, 0.5, '불사알파', ha='center', va='center', fontsize=9, fontweight='bold', color=WHITE, transform=tag_ax.transAxes)
tag_ax.set_xticks([]); tag_ax.set_yticks([])
for sp in tag_ax.spines.values(): sp.set_visible(False)

ax.text(-max_abs-0.05, n+0.3, '비중', ha='right', va='bottom', fontsize=8, color=GRAY_MUT)
ax.text(-0.05, n+0.3, '← 손실 기여', ha='right', va='bottom', fontsize=8, color=GRAY_MUT)
ax.text(0.05, n+0.3, '수익 기여 →', ha='left', va='bottom', fontsize=8, color=GRAY_MUT)

badge_ax = fig.add_axes([0.04, 0.02, 0.22, 0.048])
badge_ax.set_facecolor(NAVY)
badge_ax.text(0.5, 0.5, f'포트폴리오 수익률   +{port_return:.2f}%',
              ha='center', va='center', fontsize=11, fontweight='bold', color=WHITE, transform=badge_ax.transAxes)
badge_ax.set_xticks([]); badge_ax.set_yticks([])
for sp in badge_ax.spines.values(): sp.set_visible(False)

green_patch = mpatches.Patch(facecolor=GREEN_A, edgecolor=GREEN, linewidth=1.5, label='수익 기여')
red_patch   = mpatches.Patch(facecolor=RED_A,   edgecolor=RED,   linewidth=1.5, label='손실 기여')
ax.legend(handles=[green_patch, red_patch], loc='lower right', fontsize=9, frameon=False,
          labelcolor=GRAY_TEXT, bbox_to_anchor=(1, -0.12))
fig.text(0.96, 0.03, 'DB GAPS 2026', fontsize=9, color=GRAY_MUT, ha='right', va='bottom', fontweight='bold')

plt.tight_layout(rect=[0, 0.07, 1, 0.88])
plt.savefig(OUTPUT, dpi=180, bbox_inches='tight', facecolor=BG)
print(f"완료 → {OUTPUT}")
print(f"기간: {start_date.date()} ~ {end_date.date()}  |  포트폴리오 수익률: +{port_return:.2f}%")
