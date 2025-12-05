"""
[최종 통합본] 빵 트렌드 분석 및 시각화 (Final_V9)
- 시각화 목록 (총 7종):
  1. 🎬 Bar Chart Race (GIF): 트렌드 변화 (속도 조절됨)
  2. 👑 Rank Bump Chart: 반기별 순위 변동 (정적 이미지)
  3. 📈 Top 5 Trend: 최상위 5개 경쟁 구도
  4. 🚀 Recent 3-Month Trend: 최근 급상승 (츄러스 등)
  5. 🌸 Seasonal Heatmap: 계절성 빵 (슈톨렌 등)
  6. 💎 BCG Matrix: 포지셔닝 (이모티콘 제거됨)
  7. 📊 Yearly Comparison: 연도별 TOP 10 비교
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import glob
import bar_chart_race as bcr

# ---------------------------------------------------------
# 1. 환경 설정
# ---------------------------------------------------------
plt.rcParams['font.family'] = 'Malgun Gothic' # 윈도우용
plt.rcParams['axes.unicode_minus'] = False

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

os.makedirs(RESULTS_DIR, exist_ok=True)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
def load_data():
    if not os.path.exists(DATA_DIR):
        print("❌ 'data/processed' 폴더가 없습니다.")
        return None
    files = glob.glob(os.path.join(DATA_DIR, 'bread_trend_final_*.csv'))
    if not files:
        print("❌ 데이터 파일이 없습니다.")
        return None
    latest_file = max(files, key=os.path.getmtime)
    print(f"📂 데이터 로드: {os.path.basename(latest_file)}")
    return pd.read_csv(latest_file)

def preprocess_and_clean(df):
    print("🧹 데이터 전처리 중...")
    df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)

    rows = []
    for _, row in df.iterrows():
        if pd.notna(row['bread_keywords']) and row['bread_keywords']:
            keywords = [k.strip() for k in str(row['bread_keywords']).split(',')]
            for keyword in keywords:
                rows.append({
                    'year': row['year'],
                    'month': row['month'],
                    'year_month': row['year_month'],
                    'keyword': keyword
                })
    df_expanded = pd.DataFrame(rows)

    # 🚫 블랙리스트 (비-베이커리류 제거)
    blacklist = {
        '두바이초콜릿', '푸딩', '약과', '건빵', '초콜릿', '마카롱', '과자', '캔디', '젤리',
        '케이크', '쿠키', '샌드위치', '토스트', '파이', '타르트', '빙수', '아이스크림',
        '빵집', '베이커리', '제과점', '베이킹', '홈베이킹', '빵', '식빵', '빵류',
        '제빵', '빵맛', '빵빵', '제과제빵', '빵값', '빵피', '버터빵',
        '빵돌', '처빵', '빵구', '빵수니', '빵안', '빵귿', '애월빵',
        '알빵', '제빵사', '밤빵', '찐빵', '피스타치오'
    }

    df_clean = df_expanded[~df_expanded['keyword'].isin(blacklist)]

    # 빈도수 필터링 (10회 이상)
    keyword_counts = df_clean['keyword'].value_counts()
    valid_keywords = keyword_counts[keyword_counts >= 10].index
    df_clean = df_clean[df_clean['keyword'].isin(valid_keywords)]

    print(f"✅ 전처리 완료: {len(df_clean)}행")
    return df_clean

# ---------------------------------------------------------
# 3. 시각화 함수들
# ---------------------------------------------------------

def create_bar_chart_race(df):
    """[1] Bar Chart Race - 날짜 표시 완벽 버전"""

    print()
    print("=" * 70)
    print("🎬 [1/7] Bar Chart Race 생성")
    print("=" * 70)
    print()

    # 월별 집계
    monthly = df.groupby(['year_month', 'keyword']).size().reset_index(name='count')

    # TOP 10
    top_10 = df['keyword'].value_counts().head(10).index
    monthly_top = monthly[monthly['keyword'].isin(top_10)]

    # 피벗
    pivot = monthly_top.pivot_table(
        index='year_month',
        columns='keyword',
        values='count',
        fill_value=0
    )

    pivot.index = pd.to_datetime(pivot.index + '-01')

    print(f"📊 데이터: {len(pivot)}개월, {len(pivot.columns)}개 키워드")
    print(f"📅 기간: {pivot.index[0].strftime('%Y.%m')} ~ {pivot.index[-1].strftime('%Y.%m')}")
    print()
    print("🎬 애니메이션 생성 중... (2~3분 소요)")

    save_path = os.path.join(RESULTS_DIR, 'bread_rank_race.gif')

    bcr.bar_chart_race(
        df=pivot,
        filename=save_path,

        orientation='h',
        sort='desc',
        n_bars=10,

        title='전국 빵 트렌드 순위 (Bar Chart Race)',
        title_size=18,
        cmap='tab20',
        bar_size=0.9,

        period_label={
            'x': 0.95,
            'y': 0.5,
            'ha': 'right',
            'va': 'center',
            'size': 40,
            'weight': 'bold',
            'color': '#333333',
            'alpha': 0.7
        },
        period_fmt='%Y.%m',  # 이제 작동! ✅

        bar_label_size=12,
        tick_label_size=12,

        period_length=1400,
        interpolate_period=False,

        figsize=(12, 8),
        dpi=100,

        shared_fontdict={
            'family': 'Malgun Gothic',
            'weight': 'bold'
        },

        filter_column_colors=True
    )

    print()
    print("=" * 70)
    print(f"✅ 저장 완료: {os.path.basename(save_path)}")
    print(f"⏱️  영상 길이: 약 {len(pivot) * 1.0:.0f}초")
    print("=" * 70)

def analyze_rank_bump_chart(df):
    """[2] Rank Bump Chart (Static)"""
    print("👑 [2/7] 순위 변동 차트(Bump Chart) 생성...")
    df = df.copy()
    df['period'] = df.apply(lambda x: f"{x['year']}-{'상' if x['month'] <= 6 else '하'}", axis=1)
    df_p = df.groupby(['period', 'keyword']).size().reset_index(name='count')
    df_p['rank'] = df_p.groupby('period')['count'].rank(method='first', ascending=False)

    top_rankers = df_p[df_p['rank'] <= 10]['keyword'].unique()
    df_plot = df_p[df_p['keyword'].isin(top_rankers)]
    last_p = sorted(df_p['period'].unique())[-1]
    final_top10 = df_p[df_p['period'] == last_p].sort_values('count', ascending=False).head(10)['keyword'].tolist()

    plt.figure(figsize=(15, 10))
    periods = sorted(df_p['period'].unique())
    colors = sns.color_palette("husl", len(final_top10))
    cmap = dict(zip(final_top10, colors))

    for kw in df_plot['keyword'].unique():
        d = df_plot[df_plot['keyword'] == kw]
        full = pd.DataFrame({'period': periods})
        d = pd.merge(full, d, on='period', how='left')

        color = cmap[kw] if kw in final_top10 else 'lightgrey'
        alpha = 1.0 if kw in final_top10 else 0.5
        lw = 3 if kw in final_top10 else 1.5
        zorder = 3 if kw in final_top10 else 1
        label = kw if kw in final_top10 else None

        plt.plot(d['period'], d['rank'], marker='o', lw=lw, color=color, alpha=alpha, zorder=zorder, label=label)
        if pd.notna(d['rank'].iloc[0]) and kw in final_top10:
             plt.text(0, d['rank'].iloc[0], kw, ha='right', va='center', fontweight='bold', fontsize=10, color=color)
        if pd.notna(d['rank'].iloc[-1]) and kw in final_top10:
            plt.text(len(periods)-1, d['rank'].iloc[-1], f" {kw}({int(d['rank'].iloc[-1])}위)", va='center', fontweight='bold', color=color)

    plt.gca().invert_yaxis(); plt.yticks(range(1, 16))
    plt.title('빵 트렌드 순위 변동 (2022~2025)', fontsize=20, fontweight='bold', pad=20)
    plt.xlabel('기간 (반기)'); plt.ylabel('순위')
    plt.grid(True, axis='y', ls='--', alpha=0.5); plt.xlim(-0.5, len(periods)-0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'rank_bump_chart.png'), dpi=300)
    plt.close()

def analyze_top5_trend(df):
    """[3] Top 5 Trend (Line)"""
    print("📈 [3/7] 상위 5개 빵 트렌드 차트 생성...")
    df = df.copy()
    df['period'] = df.apply(lambda x: f"{x['year']}-{'상' if x['month'] <= 6 else '하'}", axis=1)
    df_p = df.groupby(['period', 'keyword']).size().reset_index(name='count')
    top5 = df_p.groupby('keyword')['count'].sum().sort_values(ascending=False).head(5).index.tolist()
    df_plot = df_p[df_p['keyword'].isin(top5)]
    periods = sorted(df_p['period'].unique())

    plt.figure(figsize=(14, 8))
    colors = sns.color_palette("Set1", n_colors=5)
    for i, kw in enumerate(top5):
        d = df_plot[df_plot['keyword'] == kw]
        full = pd.DataFrame({'period': periods})
        d = pd.merge(full, d, on='period', how='left').fillna(0)
        plt.plot(d['period'], d['count'], marker='o', lw=3, label=kw, color=colors[i], ms=8)
        plt.text(len(periods)-1+0.1, d['count'].iloc[-1], f"{kw}", va='center', fontweight='bold', color=colors[i], fontsize=11)

    plt.title('빵 트렌드 빅매치: TOP 5 변화 추이', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('기간 (반기)'); plt.ylabel('언급량')
    plt.grid(True, axis='y', ls='--', alpha=0.5); plt.legend(loc='upper left')
    plt.xlim(-0.5, len(periods)-0.5+0.8)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'top5_trend_chart.png'), dpi=300)
    plt.close()


def analyze_recent_3month_trend(df):
    """[2] 최근 3개월 언급량 추이 (단기 예측용)"""
    print("📈 [4/7] 최근 3개월(9~11월) 트렌드 차트 생성...")

    # 최근 3개월 데이터만 필터링
    recent_months = ['2025-09', '2025-10', '2025-11']
    df_recent = df[df['year_month'].isin(recent_months)].copy()

    # 기간 내 언급량 상위 7개 추출
    top_keywords = df_recent['keyword'].value_counts().head(7).index
    df_plot = df_recent[df_recent['keyword'].isin(top_keywords)]

    # 월별 집계
    monthly_counts = df_plot.groupby(['year_month', 'keyword']).size().unstack(fill_value=0)

    plt.figure(figsize=(10, 6))

    # 라인 차트 그리기
    for keyword in monthly_counts.columns:
        plt.plot(monthly_counts.index, monthly_counts[keyword], marker='o', linewidth=2, label=keyword)

        # 마지막 값에 숫자 표시
        last_val = monthly_counts[keyword].iloc[-1]
        plt.text(2, last_val, f"{last_val}", va='bottom', ha='center', fontsize=9, fontweight='bold')

    plt.title('최근 3개월(2025.9~11) 빵 트렌드 급상승 추이', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('월 (Month)', fontsize=12)
    plt.ylabel('언급량', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()

    plt.savefig(os.path.join(RESULTS_DIR, 'recent_3month_trend.png'), dpi=300)
    plt.close()
    print(f"💾 저장 완료: recent_3month_trend.png")

def analyze_seasonal_heatmap(df):
    """[5] Seasonal Heatmap"""
    print("🌸 [5/7] 계절성 히트맵 생성...")
    targets = ['슈톨렌', '팡도르', '파네토네', '감자빵', '고구마빵', '옥수수빵', '밤빵', '딸기케이크']
    avail = [k for k in targets if k in df['keyword'].unique()]
    if not avail: return

    d = df[df['keyword'].isin(avail)]
    h_data = d.groupby(['month', 'keyword']).size().unstack(fill_value=0).T
    h_data = h_data[[m for m in range(1, 13) if m in h_data.columns]]

    plt.figure(figsize=(12, 6))
    sns.heatmap(h_data, annot=True, fmt='g', cmap='YlOrBr', linewidths=0.5)
    plt.title('계절성 빵 인기지도 (Seasonal Heatmap)', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('월 (Month)'); plt.ylabel('빵 종류')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'seasonal_heatmap.png'), dpi=300)
    plt.close()

def analyze_bcg_matrix(df):
    """[6] BCG Matrix (No Emojis)"""
    print("💎 [6/7] BCG 매트릭스 분석...")
    recent = ['2025-06', '2025-07', '2025-08', '2025-09', '2025-10', '2025-11']
    prev = ['2024-12', '2025-01', '2025-02', '2025-03', '2025-04', '2025-05']
    top_kw = df['keyword'].value_counts().head(25).index

    data = []
    for kw in top_kw:
        k_df = df[df['keyword'] == kw]
        rec_avg = len(k_df[k_df['year_month'].isin(recent)])/6
        prev_avg = len(k_df[k_df['year_month'].isin(prev)])/6
        growth = ((rec_avg - prev_avg)/prev_avg)*100 if prev_avg>0 else (100 if rec_avg>0 else 0)
        data.append({'keyword': kw, 'vol': len(k_df), 'growth': growth})

    b_df = pd.DataFrame(data)
    m_vol = b_df['vol'].median(); m_gro = b_df['growth'].median()

    def get_label(r):
        if r['growth']>=m_gro and r['vol']>=m_vol: return "STAR"
        elif r['growth']>=m_gro: return "QUESTION"
        elif r['vol']>=m_vol: return "CASH COW"
        else: return "DOG"
    b_df['Status'] = b_df.apply(get_label, axis=1)

    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=b_df, x='vol', y='growth', hue='Status', s=200, palette='Set2')
    for _, r in b_df.iterrows():
        plt.text(r['vol'], r['growth']+1, r['keyword'], ha='center', fontsize=9, fontweight='bold')

    plt.axvline(m_vol, color='grey', ls='--'); plt.axhline(m_gro, color='grey', ls='--')
    plt.title('빵 트렌드 포지셔닝 (BCG Matrix)', fontsize=15, fontweight='bold')
    plt.xlabel('전체 언급량 (Volume)'); plt.ylabel('성장률 (Growth %)')

    # 텍스트 라벨 (이모지 제거됨)
    x_min, x_max = plt.xlim(); y_min, y_max = plt.ylim()
    box = dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5')
    plt.text(x_max*0.95, y_max*0.95, 'STAR (대세)', ha='right', va='top', bbox=box)
    plt.text(x_min+(x_max-x_min)*0.05, y_max*0.95, 'QUESTION (유망주)', ha='left', va='top', bbox=box)
    plt.text(x_max*0.95, y_min+(y_max-y_min)*0.05, 'CASH COW (스테디셀러)', ha='right', va='bottom', bbox=box)
    plt.text(x_min+(x_max-x_min)*0.05, y_min+(y_max-y_min)*0.05, 'DOG (하락/비주류)', ha='left', va='bottom', bbox=box)

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'bcg_matrix.png'), dpi=300)
    plt.close()
    return b_df

def analyze_yearly_comparison(df):
    """[7] Yearly Comparison"""
    print("📊 [7/7] 연도별 비교 차트 생성...")
    years = sorted(df['year'].unique())
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    for idx, year in enumerate(years):
        if idx >= 4: break
        ax = axes[idx]
        d = df[df['year'] == year]
        top = d['keyword'].value_counts().head(10).sort_values(ascending=True)
        colors = plt.cm.Oranges(np.linspace(0.4, 1.0, len(top)))
        ax.barh(top.index, top.values, color=colors)
        ax.set_title(f'{year}년 TOP 10', fontsize=15, fontweight='bold')
        for i, v in enumerate(top.values): ax.text(v, i, f' {v}', va='center')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'yearly_comparison.png'), dpi=300)
    plt.close()

def export_final_excel(df, bcg_df):
    print("📋 엑셀 리포트 저장 중...")
    path = os.path.join(RESULTS_DIR, 'Bread_Trend_Report_Final.xlsx')
    with pd.ExcelWriter(path) as writer:
        bcg_df.sort_values(['growth'], ascending=False).to_excel(writer, sheet_name='전략_분석', index=False)
        df.groupby(['year_month', 'keyword']).size().unstack(fill_value=0).to_excel(writer, sheet_name='월별_데이터')
    print(f"💾 엑셀 저장 완료: {os.path.basename(path)}")

# ---------------------------------------------------------
# 4. 메인 실행
# ---------------------------------------------------------
def main():
    print("🚀 빵 트렌드 분석 프로세스 시작 (Final_V9)...")
    raw_df = load_data()
    if raw_df is None: return

    df = preprocess_and_clean(raw_df)

    create_bar_chart_race(df)        # 1. GIF
    analyze_rank_bump_chart(df)      # 2. Bump
    analyze_top5_trend(df)           # 3. Top5 Line
    analyze_recent_3month_trend(df)  # 4. Recent Bar
    analyze_seasonal_heatmap(df)     # 5. Heatmap
    bcg_df = analyze_bcg_matrix(df)  # 6. BCG
    analyze_yearly_comparison(df)    # 7. Yearly Bar

    export_final_excel(df, bcg_df)
    print("\n✨ 모든 분석이 완료되었습니다!")
    print(f"📁 결과 폴더: {RESULTS_DIR}")

if __name__ == "__main__":
    main()