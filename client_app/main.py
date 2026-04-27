"""SOGANG Print Client 실행 진입점.

GUI 생성만 담당하고, 설정 로드와 Manager 통신 등 실제 동작은 app 패키지에 둔다.
"""

from app.gui_client import launch_client_gui

if __name__ == "__main__":
    launch_client_gui()
