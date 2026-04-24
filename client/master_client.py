from gpiozero import Button, LED
from time import sleep
from pymodbus.client import ModbusTcpClient

# ==========================================
# 📡 1. 통신 설정 (PC 서버 주소)
# ==========================================
SERVER_IP = "192.168.110.106" 
PORT = 5020
client = ModbusTcpClient(SERVER_IP, port=PORT)

def send_to_server(address, value):
    try:
        client.write_register(address=address, value=value, slave=1)
    except:
        pass

# ==========================================
# 💡 2. 하드웨어 핀 설정
# ==========================================
fnd = [LED(5), LED(6), LED(13), LED(19), LED(26), LED(16), LED(20), LED(21)]
count_button = Button(4, pull_up=False)    # 증가
reset_button = Button(17, pull_up=False)   # 초기화
start_button = Button(23, pull_up=False)   # 시작
e_stop_button = Button(27, pull_up=False)  # 비상정지
warning_led = LED(22)                      # 경고등 (빨강)
action_led = LED(24)                       # 작동등 (초록)

digits = [
    [1, 1, 1, 1, 1, 1, 0, 0], [0, 1, 1, 0, 0, 0, 0, 0],
    [1, 1, 0, 1, 1, 0, 1, 0], [1, 1, 1, 1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0, 1, 1, 0], [1, 0, 1, 1, 0, 1, 1, 0],
    [1, 0, 1, 1, 1, 1, 1, 0], [1, 1, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 0, 1, 1, 0]
]

def display_number(num):
    for i in range(8):
        if digits[num][i] == 1: fnd[i].on()
        else: fnd[i].off()

# ==========================================
# 🚀 3. 메인 실행 로직
# ==========================================
count = 0
is_emergency = False 

print("====== 🏭 IoT 통합 제어 시스템 시작 ======")
if client.connect():
    print("✅ PC 모드버스 서버 연결 성공!")
    send_to_server(1, count)
    send_to_server(2, 0)
    send_to_server(3, 0)
else:
    print("❌ 연결 실패 (단독 모드로 동작합니다)")

display_number(count)

try:
    while True:
        # 🚨 [ 비상 정지 발동 ]
        if e_stop_button.is_pressed and not is_emergency:
            is_emergency = True
            send_to_server(2, 1) # 비상 상태 서버 보고
            for led in fnd: led.off()
            warning_led.blink(on_time=0.5, off_time=0.5) 
            
        # 🟢 [ 정상 작동 모드 ]
        if not is_emergency:
            
            # 📡 [서버 감시] 숫자와 시작 신호를 독립적으로 읽어옵니다.
            res_count = client.read_holding_registers(address=1, count=1, slave=1)
            res_start = client.read_holding_registers(address=3, count=1, slave=1)
            
            # 두 데이터 모두 정상적으로 읽혔을 때만 실행 (들여쓰기 완벽 수정)
            if not res_count.isError() and not res_start.isError():
                
                # 1) 서버 숫자가 내 카운트와 다르면 7세그먼트 갱신 (LLM 세팅)
                server_count = res_count.registers[0]
                if server_count != count:
                    count = server_count
                    display_number(count)
                    print(f"📡 [서버 동기화] 숫자가 {count}로 변경되었습니다.")
                
                # 2) 서버에서 시작 신호(1)가 왔거나 물리 시작 버튼이 눌렸을 때
                remote_start = res_start.registers[0]
                if remote_start == 1 or start_button.is_pressed:
                    if count > 0:
                        print(f"▶️ [작업 시작] 초록 불이 {count}번 깜빡입니다.")
                        send_to_server(3, 1) # 작업 중임을 서버에 알림
                        
                        for i in range(count):
                            action_led.on()
                            sleep(0.3)
                            action_led.off()
                            sleep(0.3)
                            
                        print("✅ [작업 완료] 대기 상태로 복귀합니다.")
                        send_to_server(3, 0) # 작업 종료 알림 및 신호 끄기
                    else:
                        print(">>> 숫자가 0입니다. 숫자를 먼저 올려주세요.")
                        send_to_server(3, 0) # 신호 끄기

            # 수동 물리 버튼들 로직
            if count_button.is_pressed:
                count = 0 if count >= 9 else count + 1
                display_number(count)
                send_to_server(1, count)
                sleep(0.3) 
            
            if reset_button.is_pressed:
                count = 0
                display_number(count)
                send_to_server(1, count)
                sleep(0.3)

        sleep(0.1)

except KeyboardInterrupt:
    print("\n시스템을 안전하게 종료합니다.")
finally:
    client.close()
    for led in fnd: led.off()
    warning_led.off()
    action_led.off()
