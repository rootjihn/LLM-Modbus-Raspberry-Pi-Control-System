import threading
import ollama
import re
import time
import logging
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# 폭포수처럼 쏟아지는 통신 로그 숨기기 (에러만 표시)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR)

# 1. 서버 데이터 저장소 설정 (0번부터 10칸 넉넉히 생성)
initial_data = [0] * 10
unit1 = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, initial_data))
context = ModbusServerContext(slaves={1: unit1}, single=False)

def qwen_command_process():
    """LLM 명령어 입력 루프 (백그라운드 실행)"""
    time.sleep(1) # 서버 켜질 때까지 1초 대기
    print("\n=========================================")
    print(" 🤖 지능형 AI 스마트 팩토리 제어 시스템 켜짐 ")
    print("=========================================")
    print("💬 [명령 예시] '세 번 깜빡여줘', '시작버튼 눌러줘', '초기화해줘'\n")
    
    while True:
        try:
            user_input = input("👉 명령: ")
            if user_input == "종료": 
                print("시스템을 종료합니다.")
                break
            
            # 시작 신호 처리
            if "시작" in user_input or "눌러" in user_input:
                context[1].setValues(3, 3, [1]) # 3번 주소를 1로 변경
                print("🤖 [LLM] 시작 명령을 전송했습니다.")
                continue
                
            # 초기화 신호 처리
            if "초기화" in user_input or "리셋" in user_input or "0" in user_input:
                context[1].setValues(3, 1, [0]) # 1번 주소를 0으로 변경
                print("🤖 [LLM] 카운터를 0으로 초기화했습니다.")
                continue

            # 숫자 추출 처리
            system_prompt = "사용자의 요청에서 반복 횟수만 찾아 숫자만 답해. 예: '5'"
            response = ollama.chat(model='qwen3:4b', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input}
            ])
            content = response['message']['content'].strip()
            match = re.findall(r'\d+', content)
            
            if match:
                val = int(match[0])
                context[1].setValues(3, 1, [val]) # 1번 주소에 숫자 저장
                print(f"🤖 [LLM] 카운터를 {val}(으)로 설정했습니다.")
            else:
                print("❓ 숫자를 파악하지 못했습니다.")
                
        except Exception as e:
            print(f"❌ LLM 에러: {e}")

if __name__ == "__main__":
    # 입력창을 백그라운드 쓰레드로 분리하여 서버 멈춤 방지
    llm_thread = threading.Thread(target=qwen_command_process, daemon=True)
    llm_thread.start()
    
    # 모드버스 서버를 메인에서 지속 실행
    print("🚀 모드버스 서버 가동 준비 완료 (Port: 5020)")
    StartTcpServer(context=context, address=("0.0.0.0", 5020))
