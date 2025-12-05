
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

# results 폴더 생성
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_latest_data():
    """가장 최근 분석 파일 로드"""

    files = [f for f in os.listdir(DATA_PROCESSED_DIR) if f.startswith('trend_analysis_')]

    if not files:
        print("❌ trend_analysis 파일이 없습니다!")
        return None

    latest = sorted(files)[-1]
    filepath = os.path.join(DATA_PROCESSED_DIR, latest)

    print(f"📂 로드: {latest}")

    df = pd.read_csv(filepath)
    return df


def clean_data(df):
    """데이터 정제"""

    print()
    print("=" * 70)
    print("🧹 데이터 정제")
    print("=" * 70)
    print()

    print(f"원본 데이터: {len(df)}행")
    print(f"빵 종류: {df['bread'].nunique()}개")
    print()

    # 1. 의심스러운 빵 확인
    print("🔍 전체 빵 종류:")
    all_breads = df.groupby('bread')['count'].sum().sort_values(ascending=False)
    print(all_breads.to_string())
    print()

    # 2. 제거할 빵 (수동으로 확인 후 추가)
    blacklist = {
        '빵빵', '빵터', '빵집', '빵순이', '빵꾸',
        '빵셔틀', '빵터짐', '빵터트'
    }

    before = len(df)
    df = df[~df['bread'].isin(blacklist)]
    removed = before - len(df)

    if removed > 0:
        print(f"✂️  불용어 제거: {removed}행")

    # 3. 최소 빈도 필터링 (전체 기간 합쳐서 10회 미만 제거)
    total_counts = df.groupby('bread')['count'].sum()
    valid_breads = total_counts[total_counts >= 10].index

    before = len(df)
    df = df[df['bread'].isin(valid_breads)]
    removed = before - len(df)

    if removed > 0:
        print(f"✂️  저빈도 제거 (10회 미만): {removed}행")

    print()
    print(f"✅ 정제 완료: {len(df)}행, {df['bread'].nunique()}개 빵")

    return df


def add_derived_features(df):
    """파생 변수 생성"""

    print()
    print("=" * 70)
    print("🔧 파생 변수 생성")
    print("=" * 70)
    print()

    # 피벗 테이블 (year x bread)
    pivot = df.pivot_table(
        index='bread',
        columns='year',
        values='count',
        fill_value=0
    )

    # 1. 전년 대비 증가율
    years = sorted(df['year'].unique())

    for i in range(1, len(years)):
        prev_year = years[i - 1]
        curr_year = years[i]

        col_name = f'growth_{prev_year}_{curr_year}'

        pivot[col_name] = pivot.apply(
            lambda row: (
                ((row[curr_year] - row[prev_year]) / row[prev_year] * 100)
                if row[prev_year] > 0 else 999
            ),
            axis=1
        )

    # 2. 전체 합계
    pivot['total'] = pivot[years].sum(axis=1)

    # 3. 평균
    pivot['average'] = pivot[years].mean(axis=1)

    # 4. 최대/최소 연도
    pivot['max_year'] = pivot[years].idxmax(axis=1)
    pivot['max_count'] = pivot[years].max(axis=1)

    print("✅ 파생 변수:")
    print(f"   - 전년 대비 증가율 ({len(years) - 1}개)")
    print(f"   - 총 언급 횟수")
    print(f"   - 평균 언급 횟수")
    print(f"   - 최대 언급 연도")

    return df, pivot


def visualize_top_breads(df, pivot, top_n=15):
    """TOP N 빵 시각화"""

    print()
    print("=" * 70)
    print(f"📊 TOP {top_n} 빵 시각화")
    print("=" * 70)
    print()

    years = sorted(df['year'].unique())
    top_breads = pivot.nlargest(top_n, 'total').index

    # 1. 연도별 트렌드 (라인 차트)
    plt.figure(figsize=(14, 8))

    for bread in top_breads:
        counts = [pivot.loc[bread, year] for year in years]
        plt.plot(years, counts, marker='o', label=bread, linewidth=2)

    plt.title(f'TOP {top_n} 빵 트렌드 (2022-2025)', fontsize=16, fontweight='bold')
    plt.xlabel('연도', fontsize=12)
    plt.ylabel('언급 횟수', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = os.path.join(RESULTS_DIR, 'top_breads_trend.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"💾 저장: top_breads_trend.png")
    plt.close()

    # 2. 연도별 누적 막대 그래프
    plt.figure(figsize=(12, 8))

    df_top = df[df['bread'].isin(top_breads)]
    pivot_top = df_top.pivot_table(
        index='year',
        columns='bread',
        values='count',
        fill_value=0
    )

    pivot_top.plot(kind='bar', stacked=True, figsize=(12, 8), colormap='tab20')

    plt.title(f'연도별 빵 언급 분포 (TOP {top_n})', fontsize=16, fontweight='bold')
    plt.xlabel('연도', fontsize=12)
    plt.ylabel('언급 횟수', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.xticks(rotation=0)
    plt.tight_layout()

    filepath = os.path.join(RESULTS_DIR, 'yearly_distribution.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"💾 저장: yearly_distribution.png")
    plt.close()

    # 3. 총 언급 횟수 순위 (막대 차트)
    plt.figure(figsize=(12, 8))

    top_total = pivot.nlargest(top_n, 'total')['total'].sort_values()

    top_total.plot(kind='barh', color='skyblue', edgecolor='navy')
    plt.title(f'전체 기간 TOP {top_n} 빵', fontsize=16, fontweight='bold')
    plt.xlabel('총 언급 횟수', fontsize=12)
    plt.ylabel('빵 종류', fontsize=12)

    for i, v in enumerate(top_total.values):
        plt.text(v + 10, i, str(int(v)), va='center', fontweight='bold')

    plt.tight_layout()

    filepath = os.path.join(RESULTS_DIR, 'top_breads_total.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"💾 저장: top_breads_total.png")
    plt.close()


def visualize_growth(df, pivot):
    """급등 빵 시각화"""

    print()
    print("=" * 70)
    print("🔥 급등 빵 분석")
    print("=" * 70)
    print()

    years = sorted(df['year'].unique())

    # 각 연도별 급등 TOP 10
    for i in range(1, len(years)):
        prev_year = years[i - 1]
        curr_year = years[i]
        col_name = f'growth_{prev_year}_{curr_year}'

        # 최소 10회 이상만
        valid = pivot[pivot[curr_year] >= 10].copy()

        top_growth = valid.nlargest(10, col_name)[[prev_year, curr_year, col_name]]

        print(f"\n{prev_year} → {curr_year} 급등 TOP 10:")
        print(top_growth.to_string())

        # 시각화
        plt.figure(figsize=(12, 8))

        x = np.arange(len(top_growth))
        width = 0.35

        plt.bar(x - width / 2, top_growth[prev_year], width, label=f'{prev_year}년', color='lightcoral')
        plt.bar(x + width / 2, top_growth[curr_year], width, label=f'{curr_year}년', color='dodgerblue')

        plt.xlabel('빵 종류', fontsize=12)
        plt.ylabel('언급 횟수', fontsize=12)
        plt.title(f'{prev_year} vs {curr_year} 급등 빵 TOP 10', fontsize=16, fontweight='bold')
        plt.xticks(x, top_growth.index, rotation=45, ha='right')
        plt.legend(fontsize=11)

        for i, bread in enumerate(top_growth.index):
            growth = top_growth.loc[bread, col_name]
            if growth == 999:
                label = '신규'
            else:
                label = f'+{growth:.0f}%'

            y_pos = max(top_growth.loc[bread, [prev_year, curr_year]])
            plt.text(i, y_pos + 5, label, ha='center', fontweight='bold', color='red')

        plt.tight_layout()

        filepath = os.path.join(RESULTS_DIR, f'growth_{prev_year}_{curr_year}.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"💾 저장: growth_{prev_year}_{curr_year}.png")
        plt.close()


def visualize_heatmap(df, pivot, top_n=20):
    """히트맵 시각화"""

    print()
    print("=" * 70)
    print("📈 히트맵 생성")
    print("=" * 70)
    print()

    years = sorted(df['year'].unique())
    top_breads = pivot.nlargest(top_n, 'total').index

    heatmap_data = pivot.loc[top_breads, years]

    plt.figure(figsize=(10, 12))

    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt='g',
        cmap='YlOrRd',
        cbar_kws={'label': '언급 횟수'},
        linewidths=0.5
    )

    plt.title(f'연도별 빵 트렌드 히트맵 (TOP {top_n})', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('연도', fontsize=12)
    plt.ylabel('빵 종류', fontsize=12)
    plt.tight_layout()

    filepath = os.path.join(RESULTS_DIR, 'trend_heatmap.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"💾 저장: trend_heatmap.png")
    plt.close()


def export_summary(df, pivot):
    """요약 통계 엑셀 저장"""

    print()
    print("=" * 70)
    print("📊 요약 통계 저장")
    print("=" * 70)
    print()

    output_file = os.path.join(RESULTS_DIR, 'bread_trend_summary.xlsx')

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. 전체 데이터
        df.to_excel(writer, sheet_name='원본데이터', index=False)

        # 2. 피벗 테이블
        pivot.to_excel(writer, sheet_name='피벗테이블')

        # 3. 연도별 TOP 10
        years = sorted(df['year'].unique())
        for year in years:
            year_data = pivot[[year]].nlargest(10, year)
            year_data.to_excel(writer, sheet_name=f'{year}년_TOP10')

        # 4. 전체 TOP 30
        top_30 = pivot[['total'] + years].nlargest(30, 'total')
        top_30.to_excel(writer, sheet_name='전체_TOP30')

    print(f"💾 저장: bread_trend_summary.xlsx")
    print(f"   시트: 원본데이터, 피벗테이블, 연도별_TOP10, 전체_TOP30")


def main():
    """메인 실행"""

    print("=" * 70)
    print("📊 빵 트렌드 분석 & 시각화")
    print("=" * 70)
    print()

    # 1. 데이터 로드
    df = load_latest_data()
    if df is None:
        return

    print(f"데이터: {len(df)}행, {df['bread'].nunique()}개 빵")
    print()

    # 2. 데이터 정제
    df = clean_data(df)

    # 3. 파생 변수
    df, pivot = add_derived_features(df)

    # 4. 시각화
    visualize_top_breads(df, pivot, top_n=15)
    visualize_growth(df, pivot)
    visualize_heatmap(df, pivot, top_n=20)

    # 5. 요약 저장
    export_summary(df, pivot)

    print()
    print("=" * 70)
    print("✅ 분석 완료!")
    print("=" * 70)
    print()
    print(f"📁 결과 폴더: {RESULTS_DIR}")
    print()
    print("생성된 파일:")
    print("  📊 top_breads_trend.png       - TOP 빵 트렌드")
    print("  📊 yearly_distribution.png    - 연도별 분포")
    print("  📊 top_breads_total.png        - 전체 순위")
    print("  🔥 growth_YYYY_YYYY.png        - 급등 빵 비교")
    print("  📈 trend_heatmap.png           - 히트맵")
    print("  📋 bread_trend_summary.xlsx    - 요약 통계")


if __name__ == "__main__":
    main()