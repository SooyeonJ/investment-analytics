"""
자산군별 수익률 기여도 차트
-------------------------------
사용법:
  python3 01_자산군별-기여도.py --month 6
  python3 01_자산군별-기여도.py --month 6 --file "$HOME/Downloads/GAPS투자대회_포트폴리오_디비갭스투자대회_2026-06.xlsx"

※ 엑셀에 기록된 자산군별 금액 변화를 기준으로 수익률 기여도를 계산한다.
※ 기여도 = 월초 비중 × 자산군 수익률
"""

import argparse
import os
from datetime import datetime
import textwrap

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches


# ─────────────────────────────
# Argument
# ─────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument(
    '--file',
    default='/Users/syjeong/Downloads/GAPS투자대회_포트폴리오_디비갭스투자대회_2026-06.xlsx',
    help='포트폴리오 엑셀 경로'
)
parser.add_argument('--output', default=None, help='출력 png 경로 전체')
parser.add_argument('--output-dir', default=os.path.expanduser('~/Downloads'), help='저장 폴더')
parser.add_argument('--month', type=int, default=6, help='운용 월')
args = parser.parse_args()

FILE_PATH = args.file

if args.output:
    OUTPUT = args.output
else:
    os.makedirs(args.output_dir, exist_ok=True)
    _ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT = os.path.join(args.output_dir, f'01_자산군별_기여도_{args.month}월_{_ts}.png')

# ── 폰트 (나눔고딕을 fontManager에 등록 후 전 요소에 강제) ──────
_nanum = [f for f in fm.findSystemFonts() if 'nanumgothic' in f.replace(' ', '').lower()]
if _nanum:
    for _fp in _nanum:
        fm.fontManager.addfont(_fp)
    _fam = fm.FontProperties(fname=sorted(_nanum)[0]).get_name()
else:
    _fam = 'AppleGothic'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [_fam, 'AppleGothic', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# ─────────────────────────────
# Style
# ─────────────────────────────
BG        = '#F4F7FC'
NAVY      = '#0A1F4B'
NAVY_MID  = '#1A3A6B'
GRAY_LINE = '#D4DCF0'
GRAY_TEXT = '#7A8FAD'
GRAY_MUT  = '#9AADCC'
GREEN     = '#00A651'
GREEN_A   = (0, 166/255, 81/255, 0.55)
RED       = '#D94444'
RED_A     = (220/255, 70/255, 70/255, 0.45)
WHITE     = '#FFFFFF'


# ─────────────────────────────
# Data load
# ─────────────────────────────
df = pd.read_excel(FILE_PATH, header=0, index_col=0)
df = df[sorted(df.columns)]

dates = df.columns
start_date, end_date = dates[0], dates[-1]

total_start = df.loc['팀 전체', start_date]
total_end = df.loc['팀 전체', end_date]
port_return = (total_end - total_start) / total_start * 100


# ─────────────────────────────
# Asset class mapping
# ─────────────────────────────
asset_classes = {
    '국내주식 지수': '국내주식지수',
    '국내주식 섹터': '국내주식섹터',
    '해외주식 지수': '해외주식지수',
    '해외주식 섹터': '해외주식섹터',
    '해외채권 종합': '해외채권종합',
    '해외채권 회사채': '해외채권회사채',
    '국내채권 종합': '국내채권종합',
}


# ─────────────────────────────
# Contribution calculation
# ─────────────────────────────
results = []

for label, key in asset_classes.items():
    if key not in df.index:
        print(f"[스킵] {label}: 엑셀에서 '{key}' 행을 찾을 수 없음")
        continue

    series = df.loc[key]
    held = series[series > 0]

    if len(held) == 0:
        print(f"[스킵] {label}: 보유금액 없음")
        continue

    v_start = held.iloc[0]
    v_end = held.iloc[-1]

    weight = v_start / total_start
    ret = (v_end - v_start) / v_start
    contrib = weight * ret * 100

    results.append({
        'label': label,
        'weight': weight * 100,
        'ret': ret * 100,
        'contrib': contrib
    })

res_df = pd.DataFrame(results)

if res_df.empty or 'contrib' not in res_df.columns:
    raise ValueError('자산군별 기여도를 계산할 수 없습니다. 엑셀의 자산군 행과 금액을 확인하세요.')

res_df = res_df.sort_values('contrib', ascending=True).reset_index(drop=True)

n = len(res_df)

max_abs = max(abs(res_df['contrib'].min()), abs(res_df['contrib'].max())) * 1.8
if max_abs == 0:
    max_abs = 1


# 긴 라벨 줄바꿈
res_df['label_wrapped'] = res_df['label'].apply(
    lambda x: '\n'.join(textwrap.wrap(str(x), width=8))
)


# ─────────────────────────────
# Chart
# ─────────────────────────────
fig_height = max(6.8, n * 0.9 + 2.3)
fig, ax = plt.subplots(figsize=(15, fig_height))

fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# 배경 스트라이프
for i in range(n):
    ax.barh(
        i,
        max_abs * 2,
        left=-max_abs,
        color='#EBF0FA' if i % 2 == 0 else BG,
        height=1.0,
        zorder=0
    )

# 바 차트
for i, row in res_df.iterrows():
    v = row['contrib']
    pos = v >= 0

    ax.barh(
        i,
        v,
        left=0,
        height=0.50,
        color=GREEN_A if pos else RED_A,
        edgecolor='none',
        zorder=3
    )

    ax.plot(
        [v, v],
        [i - 0.25, i + 0.25],
        color=GREEN if pos else RED,
        linewidth=2.4,
        zorder=4
    )

    offset = max_abs * 0.03
    val_color = '#007A3D' if pos else '#B03030'
    sign = '+' if pos else ''

    # 기여도 수치: 바 끝 근처
    ax.text(
        v + (offset if pos else -offset),
        i,
        f'{sign}{v:.2f}%p',
        va='center',
        ha='left' if pos else 'right',
        fontsize=10,
        fontweight='bold',
        color=val_color,
        zorder=5
    )

    # 우측 상세: 별도 고정 구역에 배치
    detail = f"월초비중 {row['weight']:.1f}%   자산군수익률 {row['ret']:+.2f}%"

    ax.text(
        max_abs * 1.25,
        i,
        detail,
        va='center',
        ha='left',
        fontsize=8.2,
        color=GRAY_MUT,
        zorder=5
    )

    # 좌측 순위
    ax.text(
        -max_abs * 1.10,
        i,
        f'#{i + 1}',
        va='center',
        ha='right',
        fontsize=9,
        color=NAVY_MID,
        fontweight='bold',
        zorder=5
    )


# 축 설정
ax.axvline(0, color=NAVY, linewidth=1.2, alpha=0.2, zorder=2)

ax.set_yticks(range(n))
ax.set_yticklabels(
    res_df['label_wrapped'],
    fontsize=10.2,
    color=NAVY_MID,
    fontweight='bold'
)

# 우측 상세 텍스트 공간까지 확보
ax.set_xlim(-max_abs * 1.18, max_abs * 2.05)

ax.set_xlabel(
    '수익률 기여도 (%p)',
    fontsize=9.5,
    color=GRAY_TEXT,
    labelpad=8
)

ax.tick_params(axis='x', colors=GRAY_MUT, labelsize=9)
ax.tick_params(axis='y', length=0, pad=10)
ax.xaxis.grid(True, linestyle='--', alpha=0.3, color=GRAY_LINE, zorder=1)
ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)


# ─────────────────────────────
# Title / subtitle
# ─────────────────────────────
fig.text(
    0.04,
    0.97,
    '자산군별 수익률 기여도 분석',
    fontsize=15,
    fontweight='bold',
    color=NAVY,
    va='top'
)

fig.text(
    0.04,
    0.922,
    f'{start_date.strftime("%Y.%m.%d")} – {end_date.strftime("%Y.%m.%d")}  ·  '
    f'포트폴리오 수익률 {port_return:+.2f}%  ·  '
    f'기여도 = 월초 비중 × 자산군 수익률',
    fontsize=10,
    color=GRAY_TEXT,
    va='top'
)

fig.add_artist(
    plt.Line2D(
        [0.04, 0.5],
        [0.89, 0.89],
        transform=fig.transFigure,
        color=GREEN,
        linewidth=1.5,
        alpha=0.7
    )
)

fig.add_artist(
    plt.Line2D(
        [0.5, 0.96],
        [0.89, 0.89],
        transform=fig.transFigure,
        color=GRAY_LINE,
        linewidth=1.5
    )
)


# ─────────────────────────────
# Team badge
# ─────────────────────────────
tag_ax = fig.add_axes([0.86, 0.928, 0.10, 0.042])
tag_ax.set_facecolor(NAVY)
tag_ax.text(
    0.5,
    0.5,
    '불사알파',
    ha='center',
    va='center',
    fontsize=9,
    fontweight='bold',
    color=WHITE,
    transform=tag_ax.transAxes
)
tag_ax.set_xticks([])
tag_ax.set_yticks([])

for sp in tag_ax.spines.values():
    sp.set_visible(False)


# ─────────────────────────────
# Bottom badge
# ─────────────────────────────
badge_ax = fig.add_axes([0.04, 0.015, 0.22, 0.042])
badge_ax.set_facecolor(NAVY)
badge_ax.text(
    0.5,
    0.5,
    f'분석 자산군 {n}개',
    ha='center',
    va='center',
    fontsize=10,
    fontweight='bold',
    color=WHITE,
    transform=badge_ax.transAxes
)
badge_ax.set_xticks([])
badge_ax.set_yticks([])

for sp in badge_ax.spines.values():
    sp.set_visible(False)


# ─────────────────────────────
# Legend / footer
# ─────────────────────────────
green_patch = mpatches.Patch(
    facecolor=GREEN_A,
    edgecolor=GREEN,
    linewidth=1.5,
    label='양(+) 기여도'
)

red_patch = mpatches.Patch(
    facecolor=RED_A,
    edgecolor=RED,
    linewidth=1.5,
    label='음(-) 기여도'
)

ax.legend(
    handles=[green_patch, red_patch],
    loc='upper right',
    bbox_to_anchor=(1.0, 1.06),
    fontsize=9,
    frameon=False,
    labelcolor=GRAY_TEXT
)

fig.text(
    0.96,
    0.02,
    'DB GAPS 2026',
    fontsize=9,
    color=GRAY_MUT,
    ha='right',
    va='bottom',
    fontweight='bold'
)

plt.tight_layout(rect=[0.03, 0.06, 0.97, 0.88])
plt.savefig(OUTPUT, dpi=180, bbox_inches='tight', facecolor=BG)
plt.show()

print(f"완료 → {OUTPUT}")

