"""
[최종 수정] 빵 트렌드 분석기 (2025.11 버전)
- 검색어 변경: '빵' -> '빵지순례' (광고/일상글 노이즈 제거)
- 추출 로직: 최신 유행어(밤티라미수, 크루키 등) 사전 매칭 후 형태소 분석
- 기간: 2022.01 ~ 2025.11
- IP 차단 방지: 체크포인트, 랜덤 딜레이, 주기적 휴식
"""

import os
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from datetime import datetime
from calendar import monthrange
import re
from collections import Counter

# KoNLPy 설정 (설치되어 있으면 사용, 없으면 패턴 매칭만 수행)
try:
    from konlpy.tag import Okt
    okt = Okt()
    KONLPY_AVAILABLE = True
except ImportError:
    print("⚠️  KoNLPy 미설치: 단순 패턴 매칭으로 진행합니다.")
    KONLPY_AVAILABLE = False
    okt = None

# 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
if not os.path.exists(DATA_PROCESSED_DIR):
    os.makedirs(DATA_PROCESSED_DIR)


def setup_driver():
    """크롬 드라이버 설정"""
    options = Options()
    # 봇 탐지 우회 설정
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def collect_urls_by_month(driver, year, month, max_pages=5):
    results = []
    last_day = monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    search_keyword = "빵지순례"

    for page in range(1, max_pages + 1):
        try:
            url = (
                f"https://section.blog.naver.com/Search/Post.naver?"
                f"pageNo={page}&rangeType=PERIOD"
                f"&startDate={start_date}&endDate={end_date}"
                f"&orderBy=sim&keyword={search_keyword}"
            )

            driver.get(url)

            time.sleep(random.uniform(1.5, 2.5))

            links = driver.find_elements(By.CSS_SELECTOR, "a.desc_inner[ng-href*='blog.naver.com']")

            if not links:
                break

            for link in links:
                try:
                    href = link.get_attribute('ng-href')
                    title = link.find_element(By.CLASS_NAME, "title_post").text
                    if href:
                        results.append({'year': year, 'month': month, 'title': title, 'link': href})
                except:
                    continue

            # 페이지 넘길 때 랜덤 딜레이
            time.sleep(random.uniform(0.8, 1.5))

        except Exception:
            break

    return results


def extract_full_content(driver, url):
    try:
        driver.get(url)

        time.sleep(random.uniform(2, 4))

        # iframe 진입
        try:
            driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
        except:
            pass

        content = ""
        date_res = None

        # 본문 추출
        try:
            paragraphs = driver.find_elements(By.CLASS_NAME, "se-text-paragraph")
            content = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
        except:
            pass

        # 날짜 추출
        try:
            date_elem = driver.find_element(By.CLASS_NAME, "se_publishDate")
            date_res = date_elem.text.strip()
        except:
            pass

        # iframe 빠져나오기
        try:
            driver.switch_to.default_content()
        except:
            pass

        return {'date': date_res, 'content': content}

    except Exception:
        return {'date': None, 'content': None}


def extract_bread_keywords(text):
    if not text:
        return []

    text_nospace = text.replace(" ", "")
    found_keywords = []

    trend_dict = {
        # [2024-2025 최신 유행 & 바이럴]
        '밤티라미수': '밤티라미수', '마롱티라미수': '밤티라미수', '밤티라미슈': '밤티라미수',
        '크루키': '크루키', '크루아상쿠키': '크루키',
        '수건케이크': '수건케이크', '크레이프롤': '수건케이크',
        '티슈식빵': '티슈식빵', '천겹식빵': '티슈식빵',

        # [메인 카테고리 & 전문점 트렌드]
        '프레첼': '프레첼', '프레즐': '프레첼', '쪽파프레첼': '프레첼',
        '베이글': '베이글', '런던베이글': '베이글',
        '소금빵': '소금빵', '시오빵': '소금빵', '초코소금빵': '소금빵',
        '앙버터소금빵': '소금빵', '명란소금빵': '소금빵',
        '메론소금빵': '소금빵', '생크림소금빵': '소금빵',
        '휘낭시에': '휘낭시에', '마들렌': '마들렌',
        '에그타르트': '에그타르트', '스콘': '스콘',
        '까눌레': '까눌레', '카눌레': '까눌레',
        '크루아상': '크루아상', '크로와상': '크루아상',
        '퀸아망': '퀸아망', '퀴니아망': '퀸아망',
        '잠봉뵈르': '잠봉뵈르', '앙버터': '앙버터',
        '화이트롤': '화이트롤', '크룽지': '크룽지',
        '메론빵': '메론빵', '야끼소바빵': '야끼소바빵',
        '맘모스': '맘모스빵', '맘모스빵': '맘모스빵',
        '감자빵': '감자빵', '고구마빵': '고구마빵',
        '슈톨렌': '슈톨렌', '수톨렌': '슈톨렌',
        '파네토네': '파네토네', '팡도르': '팡도르'
    }

    for key, val in trend_dict.items():
        if key in text or key in text_nospace:
            found_keywords.append(val)

    if KONLPY_AVAILABLE:
        try:
            nouns = okt.nouns(text)
            for noun in nouns:
                if len(noun) >= 2:
                    if '빵' in noun and noun not in ['빵집', '빵순이', '빵지순례', '오빵', '아빵', '식빵']:
                        found_keywords.append(noun)
                    elif noun in ['케이크', '샌드위치', '토스트', '타르트', '파이', '쿠키', '도넛', '츄러스']:
                        found_keywords.append(noun)
        except:
            pass

    return list(set(found_keywords))


def save_checkpoint(results, checkpoint_file):
    """중간 저장 (IP 차단 방지용)"""
    df = pd.DataFrame(results)
    df.to_csv(checkpoint_file, index=False, encoding='utf-8-sig')


def load_checkpoint(checkpoint_file):
    """재개"""
    if os.path.exists(checkpoint_file):
        df = pd.read_csv(checkpoint_file)
        return df.to_dict('records')
    return []


def analyze_trends(df):
    """결과 분석 및 출력"""
    print("\n" + "="*70)
    print("📊 연도별 빵 트렌드 분석 결과")
    print("="*70)

    # 전체 키워드 풀기
    df['keywords_list'] = df['bread_keywords'].apply(lambda x: x.split(', ') if x else [])

    # 연도별 집계
    years = sorted(df['year'].unique())

    for year in years:
        year_df = df[df['year'] == year]
        all_words = []
        for kw_list in year_df['keywords_list']:
            all_words.extend(kw_list)

        counter = Counter(all_words)
        print(f"\n📅 {year}년 TOP 15 키워드:")
        for rank, (word, count) in enumerate(counter.most_common(15), 1):
            # 시각적 그래프 표현
            bar = "■" * (count // 2)
            print(f" {rank:2d}. {word:12s} ({count:3d}회) {bar}")


def main():
    print("=" * 70)
    print("🚀 빵 트렌드 크롤러 (검색어: 빵지순례)")
    print("=" * 70)
    print()

    # 1. 수집 기간 설정
    years_months = []
    # 2022 ~ 2024 (전체)
    for year in [2022, 2023, 2024]:
        for month in range(1, 13):
            years_months.append((year, month))
    # 2025 (1~11월)
    for month in range(1, 12):
        years_months.append((2025, month))

    total_months = len(years_months)
    print(f"📅 수집 기간: 2022-01 ~ 2025-11 ({total_months}개월)")
    print(f"📄 월당 페이지: 5페이지 (약 35개)")
    print(f"🎯 예상 URL: 약 {total_months * 35}개")
    print()

    # URL 저장 파일
    url_file = os.path.join(DATA_PROCESSED_DIR, 'bread_urls_refined.csv')

    # Step 1: URL 수집 (파일 없으면 실행)
    if not os.path.exists(url_file):
        print("=" * 70)
        print("📥 Step 1: URL 수집")
        print("=" * 70)
        print()

        driver = setup_driver()
        all_urls = []

        try:
            for idx, (year, month) in enumerate(years_months, 1):
                print(f"[{idx:2d}/{total_months}] {year}-{month:02d} ", end="", flush=True)

                urls = collect_urls_by_month(driver, year, month)
                all_urls.extend(urls)

                print(f"→ {len(urls)}개")

                # 랜덤 딜레이 (월별 수집 사이)
                time.sleep(random.uniform(1, 2))

        finally:
            driver.quit()

        df_urls = pd.DataFrame(all_urls)
        df_urls.drop_duplicates(subset=['link'], inplace=True)
        df_urls.to_csv(url_file, index=False, encoding='utf-8-sig')

        print()
        print(f"✅ URL 수집 완료: {len(df_urls)}개 (중복 제거)")
        print(f"💾 저장: {os.path.basename(url_file)}")
    else:
        print("💾 기존 URL 파일 사용")
        df_urls = pd.read_csv(url_file)
        print(f"   {len(df_urls)}개")

    # Step 2: 본문 크롤링 및 키워드 추출
    print()
    print("=" * 70)
    print("📝 Step 2: 본문 크롤링")
    print("=" * 70)
    print()

    total = len(df_urls)
    print(f"📊 크롤링 대상: {total}개")
    print(f"⏱️  예상 시간: 약 {total * 3 / 3600:.1f}시간")
    print()

    # 체크포인트 파일
    checkpoint_file = os.path.join(DATA_PROCESSED_DIR, 'bread_checkpoint_refined.csv')
    existing = load_checkpoint(checkpoint_file)

    if existing:
        print(f"💾 이전 진행: {len(existing)}개")
        resume = input("이어서 진행? (yes/no): ")
        if resume.lower() == 'yes':
            results = existing
            completed = {r['link'] for r in results if 'link' in r}
            df_urls = df_urls[~df_urls['link'].isin(completed)]
            print(f"✅ 남은: {len(df_urls)}개\n")
        else:
            results = []
    else:
        results = []

    if len(df_urls) == 0:
        print("✅ 이미 완료!")
        if results:
            df_result = pd.DataFrame(results)
            analyze_trends(df_result)
        return

    driver = setup_driver()
    success = 0
    fail = 0
    start_time = time.time()

    try:
        for idx, row in df_urls.iterrows():
            num = len(results) + 1

            print(f"[{num:4d}/{total}] {row['year']}-{row['month']:02d} ", end="", flush=True)

            # 본문 추출
            res = extract_full_content(driver, row['link'])

            # 키워드 추출
            keywords = extract_bread_keywords(res['content'])

            if res['content']:
                if keywords:
                    print(f"✅ {res['date']} | {', '.join(keywords[:5])}")
                    success += 1
                else:
                    print(f"⚪ {res['date']}")
                    success += 1
            else:
                print("❌")
                fail += 1

            results.append({
                'year': row['year'],
                'month': row['month'],
                'title': row['title'],
                'link': row['link'],
                'date': res['date'],
                'bread_keywords': ", ".join(keywords) if keywords else ""
            })

            # 🔒 IP 차단 방지: 50개마다 저장 & 휴식
            if num % 50 == 0:
                save_checkpoint(results, checkpoint_file)

                elapsed = (time.time() - start_time) / 60
                remaining = (len(df_urls) - (num - len(existing))) * 3 / 60

                print()
                print(f"   💾 체크포인트 ({num}개)")
                print(f"   ✅ 성공: {success} | ❌ 실패: {fail}")
                print(f"   ⏱️  경과: {elapsed:.1f}분 | 남은: {remaining:.0f}분")
                print(f"   😴 2분 휴식...")
                print()

                time.sleep(120)  # 2분 휴식

            # 랜덤 딜레이 (각 글마다)
            time.sleep(random.uniform(3, 5))

    except KeyboardInterrupt:
        print("\n\n⚠️  중단됨 (Ctrl+C)")
        save_checkpoint(results, checkpoint_file)
        print(f"💾 진행상황 저장: {len(results)}개")

    finally:
        driver.quit()

    # 최종 저장
    if results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = os.path.join(DATA_PROCESSED_DIR, f'bread_trend_final_{timestamp}.csv')

        df_result = pd.DataFrame(results)
        df_result.to_csv(save_path, index=False, encoding='utf-8-sig')

        elapsed = (time.time() - start_time) / 3600

        print()
        print("=" * 70)
        print("✅ 크롤링 완료!")
        print("=" * 70)
        print(f"총: {len(results)}개")
        print(f"성공: {success}개 ({success/len(results)*100:.1f}%)")
        print(f"시간: {elapsed:.1f}시간")
        print(f"💾 저장: {os.path.basename(save_path)}")

        # 체크포인트 삭제
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

        # 결과 바로 분석
        analyze_trends(df_result)


if __name__ == "__main__":
    main()