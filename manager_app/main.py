"""SOGANG Print Manager 실행 진입점.

GUI를 시작하는 역할만 맡고, 서버 실행과 업무 로직은 app 패키지의 전용 모듈로 분리한다.
"""

from app.gui_manager import launch_manager_gui

if __name__ == "__main__":
    launch_manager_gui()
