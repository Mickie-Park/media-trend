import sys
import time
from playwright.sync_api import sync_playwright

# 대시보드 기본 주소 (?user=admin 제외한 순수 도메인)
APP_URL = "https://media-trend.streamlit.app"

def wake_up():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 가상 브라우저 기동 및 접속 시도: {APP_URL}")
    with sync_playwright() as p:
        # 백그라운드 가상 크롬 브라우저 기동
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 사이트 접속 (최대 60초 대기)
            page.goto(APP_URL, timeout=60000, wait_until="domcontentloaded")
            print("웹페이지 DOM 로드 완료. 웹소켓(WebSocket) 세션 연결 유지 중...")
            
            # 2. 웹소켓 세션이 서버에 완전히 체결되도록 15초간 대기
            time.sleep(15)

            # 3. 혹시 앱이 잠들어 있어 '깨우기 버튼'이 떠 있는지 검사 및 자동 클릭
            wake_buttons = [
                "button:has-text('Yes, get this app back up')",
                "button:has-text('Wake up')",
                "text=Yes, get this app back up"
            ]
            
            clicked = False
            for btn_selector in wake_buttons:
                btn = page.query_selector(btn_selector)
                if btn and btn.is_visible():
                    print("⚠️ 수면 모드 감지! [Yes, get this app back up] 버튼을 클릭하여 깨웁니다.")
                    btn.click()
                    clicked = True
                    # 컨테이너 부팅 대기 (20초)
                    time.sleep(20)
                    break

            if not clicked:
                print("✅ 앱이 이미 정상적으로 활성 상태(Live)임을 확인했습니다.")

            print("Streamlit 유휴 타이머 갱신 성공. 브라우저를 안전하게 종료합니다.")

        except Exception as e:
            print(f"접속 중 예외 발생: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    wake_up()
