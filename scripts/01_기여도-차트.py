import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ── 폰트 ───────────────────────────────────────────────────
# 나눔폰트 자동 탐색
nanum = [f for f in fm.findSystemFonts() if 'Nanum' in f]
if nanum:
    plt.rcParams['font.family'] = fm.FontProperties(fname=nanum[0]).get_name()
else:
    plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우 기본 한글폰트
plt.rcParams['axes.unicode_minus'] = False

# ── 색상 팔레트 ────────────────────────────────────────────
NAVY       = '#0A1F4B'
NAVY_MID   = '#1A3A6B'
GOLD       = '#C9A84C'
GOLD_LIGHT = '#E8C96A'
CREAM      = '#F7F4EE'
WHITE      = '#FFFFFF'
RED        = '#C0392B'
GRAY_LINE  = '#D0D8E8'

# ── 파일 경로 (여기만 수정) ────────────────────────────────
FILE_PATH = r'C:\Users\여기에\경로\GAPS투자대회_포트폴리오_디비갭스투자대회_260619.xlsx'

# ── 데이터 로드 ────────────────────────────────────────────
df = pd.read_excel(FILE_PATH, header=0, index_col=0)
df = df[sorted(df.columns)]
dates = df.columns
start_date, end_date = dates[0], dates[-1]

total_start = df.loc['팀 전체', start_date]
total_end   = df.loc['팀 전체', end_date]
port_return = (total_end - total_start) / total_start * 100

# ── 자산군 매핑 ────────────────────────────────────────────
asset_classes = {
    '국내주식 지수': '국내주식지수',
    '국내주식 섹터': '국내주식섹터',
    '해외주식 지수': '해외주식지수',
    '해외주식 섹터': '해외주식섹터',
    '해외채권 종합': '해외채권종합',
    '해외채권 회사채': '해외채권회사채',
    '국내채권 종합': '국내채권종합',
}

# ── 기여도 계산 ────────────────────────────────────────────
results = []
for label, key in asset_classes.items():
    series = df.loc[key]
    held = series[series > 0]
    if len(held) == 0:
        continue
    v_start = held.iloc[0]
    v_end   = held.iloc[-1]
    weight  = v_start / total_start
    ret     = (v_end - v_start) / v_start
    contrib = weight * ret * 100
    results.append({'label': label, 'weight': weight * 100, 'ret': ret * 100, 'contrib': contrib})

res_df = pd.DataFrame(results).sort_values('contrib').reset_index(drop=True)

# ── 차트 ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor(NAVY)
ax.set_facecolor(NAVY)

# 배경 스트라이프
for i in range(len(res_df)):
    fc = NAVY_MID if i % 2 == 0 else NAVY
    ax.barh(i, 999, left=-999, color=fc, height=1.0, zorder=0)

# 바
y_pos = range(len(res_df))
bar_colors = [RED if v < 0 else GOLD for v in res_df['contrib']]
bars = ax.barh(y_pos, res_df['contrib'], color=bar_colors, height=0.55, zorder=3, edgecolor='none')

# 바 끝 포인트
for i, bar in enumerate(bars):
    ax.plot(bar.get_width(), i, 'o', color=WHITE, markersize=5, zorder=5)

# 수치 + 비중 레이블
for i, (bar, row) in enumerate(zip(bars, res_df.itertuples())):
    x = bar.get_width()
    offset = 0.06 if x >= 0 else -0.06
    ha = 'left' if x >= 0 else 'right'
    color = GOLD_LIGHT if x >= 0 else '#FF7F7F'
    ax.text(x + offset, i, f'{row.contrib:+.2f}%p',
            va='center', ha=ha, fontsize=10.5, fontweight='bold', color=color, zorder=6)
    ax.text(-1.95, i, f'{row.weight:.1f}%',
            va='center', ha='right', fontsize=8.5, color=GRAY_LINE, zorder=6)

# 축
ax.set_yticks(y_pos)
ax.set_yticklabels(res_df['label'], fontsize=11, color=WHITE, fontweight='bold')
ax.set_xlim(-2.1, res_df['contrib'].max() + 0.55)
ax.set_xlabel('수익률 기여도 (%p)', fontsize=9.5, color=GRAY_LINE, labelpad=8)
ax.tick_params(axis='x', colors=GRAY_LINE, labelsize=9)
ax.tick_params(axis='y', length=0)

# 0선 & 그리드
ax.axvline(0, color=GOLD, linewidth=1.2, zorder=4, alpha=0.7)
ax.xaxis.grid(True, linestyle='--', alpha=0.2, color=WHITE, zorder=1)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_visible(False)

# 타이틀
fig.text(0.04, 0.96, '자산군별 수익률 기여도 분석',
         fontsize=15, fontweight='bold', color=WHITE, va='top')
fig.text(0.04, 0.90,
         f'{start_date.strftime("%Y.%m.%d")} – {end_date.strftime("%Y.%m.%d")}   |   포트폴리오 수익률  {port_return:+.2f}%',
         fontsize=10, color=GOLD_LIGHT, va='top')
fig.add_artist(plt.Line2D([0.04, 0.96], [0.875, 0.875],
               transform=fig.transFigure, color=GOLD, linewidth=1.2, alpha=0.6))
fig.text(0.855, 0.90, '좌측 숫자 = 월초 비중', fontsize=8, color=GRAY_LINE, va='top', ha='right')
fig.text(0.96, 0.96, '불사알파', fontsize=10, color=GOLD, va='top', ha='right', fontweight='bold', alpha=0.8)

plt.tight_layout(rect=[0, 0, 1, 0.87])
plt.savefig('01_자산군별_기여도_차트.png', dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.show()
print("완료 → 01_자산군별_기여도_차트.png 저장됨")
