"""
ETF 모멘텀 스코어 랭킹 차트 (2026-06 운용 기준)
-------------------------------
사용법:
  python 03_모멘텀-스코어_2026-06.py --date 20260630 [--output <png경로>] [--month 6] [--output-dir <폴더>]

인수:
  --date       : 기준일 (YYYYMMDD, 필수)
  --output     : 저장할 png 경로 전체 지정 (지정 시 타임스탬프 없이 이 이름 그대로 저장)
  --output-dir : 저장 폴더 (기본: Downloads). 파일명은 자동으로 생성일시가 붙음
  --month      : 운용 월 (기본: 6)

※ 반드시 KRX_ID / KRX_PW 환경변수가 설정되어 있어야 한다 (KRX 데이터마켓플레이스 회원 로그인 필요).
※ 모멘텀 스코어 = 1M + 3M + 6M 수익률 합산 (12M 제외).
※ ETF_MAP은 2026-06-30 기준 실제 보유 16종목으로 갱신 (매도분 3종 제거, 신규매수 3종 추가).
"""

import argparse
import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
from pykrx import stock
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()
parser.add_argument('--date',       required=True, help='기준일 (YYYYMMDD)')
parser.add_argument('--output',     default=None, help='출력 png 경로 전체 (지정 시 타임스탬프 미적용)')
parser.add_argument('--output-dir', default=os.path.expanduser('~/Downloads'), help='저장 폴더 (기본: Downloads)')
parser.add_argument('--month',      type=int, default=6, help='운용 월 (기본: 6)')
args = parser.parse_args()

BASE_DATE = args.date

# 저장 경로 결정: --output 있으면 그대로, 없으면 output-dir + 생성일시 파일명
if args.output:
    OUTPUT = args.output
else:
    os.makedirs(args.output_dir, exist_ok=True)
    _ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT = os.path.join(args.output_dir, f'03_모멘텀_스코어_{args.month}월_{_ts}.png')

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

# 2026-06-30 기준 실제 보유 16종목
# [제거] 229200 KODEX 코스닥150 (6/22경 매도 -> TIGER 200으로 교체)
# [제거] 488500 TIGER 미국S&P500동일가중 (6/22경 매도 -> ACE 글로벌반도체TOP4 Plus로 교체)
# [제거] 451530 TIGER 국고채30년스트립액티브 (6/18경 매도 -> RISE 단기특수은행채액티브로 교체)
# [추가] 102110 TIGER 200
# [추가] 446770 ACE 글로벌반도체TOP4 Plus
# [추가] 0061Z0 RISE 단기특수은행채액티브 (구글드라이브 188 ETF 리스트 기준 티커)
ETF_MAP = {
    '069500': 'KODEX 200',
    '102110': 'TIGER 200',
    '091180': 'KODEX 자동차',
    '395160': 'KODEX AI반도체',
    '434730': 'HANARO 원자력iSelect',
    '445290': 'KODEX 로봇액티브',
    '487240': 'KODEX AI전력핵심설비',
    '414780': 'TIGER 차이나과창판STAR50',
    '446770': 'ACE 글로벌반도체TOP4 Plus',
    '457480': 'ACE 테슬라밸류체인액티브',
    '465580': 'ACE 미국빅테크TOP7 Plus',
    '453850': 'ACE 미국30년국채액티브(H)',
    '458250': 'TIGER 미국30년국채스트립(H)',
    '455660': 'ACE 미국하이일드액티브(H)',
    '468380': 'KODEX iShares미국하이일드',
    '0061Z0': 'RISE 단기특수은행채액티브',
}

base = BASE_DATE
d1m  = (datetime.strptime(base,'%Y%m%d') - timedelta(days=30)).strftime('%Y%m%d')
d3m  = (datetime.strptime(base,'%Y%m%d') - timedelta(days=91)).strftime('%Y%m%d')
d6m  = (datetime.strptime(base,'%Y%m%d') - timedelta(days=182)).strftime('%Y%m%d')

def get_price(ticker, date_str):
    start = (datetime.strptime(date_str,'%Y%m%d') - timedelta(days=7)).strftime('%Y%m%d')
    df = stock.get_market_ohlcv_by_date(start, date_str, ticker)
    if df.empty:
        return None
    return df['종가'].iloc[-1]

print(f"기준일: {base}")
print("ETF 가격 수집 중...\n")

results = []
for ticker, name in ETF_MAP.items():
    try:
        p_base = get_price(ticker, base)
        p_1m   = get_price(ticker, d1m)
        p_3m   = get_price(ticker, d3m)
        p_6m   = get_price(ticker, d6m)

        if None in [p_base, p_1m, p_3m, p_6m]:
            print(f"  [스킵] {name}: 데이터 부족")
            continue

        r1m  = (p_base - p_1m)  / p_1m  * 100
        r3m  = (p_base - p_3m)  / p_3m  * 100
        r6m  = (p_base - p_6m)  / p_6m  * 100
        score = r1m + r3m + r6m

        results.append({'ticker': ticker, 'name': name,
                        '1M': round(r1m,2), '3M': round(r3m,2),
                        '6M': round(r6m,2), 'score': round(score,2)})
        print(f"  {name}: 1M={r1m:.1f}% 3M={r3m:.1f}% 6M={r6m:.1f}% → {score:.1f}")

    except Exception as e:
        print(f"  [오류] {name}: {e}")

res_df = pd.DataFrame(results).sort_values('score', ascending=False).reset_index(drop=True)
n = len(res_df)
max_abs = res_df['score'].abs().max() * 1.4

fig, ax = plt.subplots(figsize=(13, n * 0.62 + 2))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

for i in range(n):
    ax.barh(i, max_abs*2, left=-max_abs, color='#EBF0FA' if i%2==0 else BG, height=1.0, zorder=0)

for i, row in res_df.iterrows():
    v = row['score']
    pos = v >= 0
    ax.barh(i, v, left=0, height=0.52, color=GREEN_A if pos else RED_A, zorder=3, edgecolor='none')
    ax.plot([v,v], [i-0.26, i+0.26], color=GREEN if pos else RED, linewidth=2.5, zorder=4)
    offset = max_abs * 0.025
    val_color = '#007A3D' if pos else '#B03030'
    sign = '+' if pos else ''
    ax.text(v+(offset if pos else -offset), i, f'{sign}{v:.1f}',
            va='center', ha='left' if pos else 'right',
            fontsize=9.5, fontweight='bold', color=val_color, zorder=5)
    detail = f"1M {row['1M']:+.1f}%   3M {row['3M']:+.1f}%   6M {row['6M']:+.1f}%"
    ax.text(max_abs + max_abs*0.03, i, detail,
            va='center', ha='left', fontsize=7.5, color=GRAY_MUT, zorder=5)
    ax.text(-max_abs - max_abs*0.02, i, f'#{i+1}',
            va='center', ha='right', fontsize=9, color=NAVY_MID, fontweight='bold', zorder=5)

ax.axvline(0, color=NAVY, linewidth=1.2, alpha=0.2, zorder=2)
ax.set_yticks(range(n))
ax.set_yticklabels(res_df['name'], fontsize=10.5, color=NAVY_MID, fontweight='bold')
ax.set_xlim(-max_abs - max_abs*0.1, max_abs + max_abs*1.05)
ax.set_xlabel('모멘텀 스코어 (1M+3M+6M 수익률 합산, %)', fontsize=9.5, color=GRAY_TEXT, labelpad=8)
ax.tick_params(axis='x', colors=GRAY_MUT, labelsize=9)
ax.tick_params(axis='y', length=0, pad=8)
ax.xaxis.grid(True, linestyle='--', alpha=0.3, color=GRAY_LINE, zorder=1)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_visible(False)

fig.text(0.04, 0.97, 'ETF 모멘텀 스코어 랭킹', fontsize=15, fontweight='bold', color=NAVY, va='top')
fig.text(0.04, 0.915, f'기준일: {BASE_DATE[:4]}.{BASE_DATE[4:6]}.{BASE_DATE[6:]}  ·  스코어 = 1M+3M+6M 수익률 합산  ·  좌측 = 순위',
         fontsize=10, color=GRAY_TEXT, va='top')
fig.add_artist(plt.Line2D([0.04,0.5],[0.885,0.885], transform=fig.transFigure, color=GREEN, linewidth=1.5, alpha=0.7))
fig.add_artist(plt.Line2D([0.5,0.96],[0.885,0.885], transform=fig.transFigure, color=GRAY_LINE, linewidth=1.5))

tag_ax = fig.add_axes([0.86, 0.928, 0.10, 0.042])
tag_ax.set_facecolor(NAVY)
tag_ax.text(0.5, 0.5, '불사알파', ha='center', va='center', fontsize=9, fontweight='bold', color=WHITE, transform=tag_ax.transAxes)
tag_ax.set_xticks([]); tag_ax.set_yticks([])
for sp in tag_ax.spines.values(): sp.set_visible(False)

badge_ax = fig.add_axes([0.04, 0.015, 0.16, 0.042])
badge_ax.set_facecolor(NAVY)
badge_ax.text(0.5, 0.5, f'보유 ETF {n}종목',
              ha='center', va='center', fontsize=10, fontweight='bold', color=WHITE, transform=badge_ax.transAxes)
badge_ax.set_xticks([]); badge_ax.set_yticks([])
for sp in badge_ax.spines.values(): sp.set_visible(False)

green_patch = mpatches.Patch(facecolor=GREEN_A, edgecolor=GREEN, linewidth=1.5, label='양(+) 모멘텀')
red_patch   = mpatches.Patch(facecolor=RED_A,   edgecolor=RED,   linewidth=1.5, label='음(-) 모멘텀')
ax.legend(handles=[green_patch, red_patch], loc='upper right', fontsize=9, frameon=False,
          labelcolor=GRAY_TEXT)
fig.text(0.96, 0.02, 'DB GAPS 2026', fontsize=9, color=GRAY_MUT, ha='right', va='bottom', fontweight='bold')

plt.tight_layout(rect=[0, 0.055, 1, 0.9])
plt.savefig(OUTPUT, dpi=180, bbox_inches='tight', facecolor=BG)
print(f"\n완료 → {OUTPUT}")
