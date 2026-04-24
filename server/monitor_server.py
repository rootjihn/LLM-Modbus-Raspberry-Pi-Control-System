from pymodbus.client import ModbusTcpClient
import time
import sys

# PC 자기 자신(127.0.0.1)의 서버(5020 포트)를 지켜봅니다.
client = ModbusTcpClient("127.0.0.1", port=5020)

print("=========================================")
print("  🖥️ 모드버스 서버 실시간 모니터링 가동  ")
print("=========================================")

if client.connect():
    try:
        while True:
            # 주소 1번부터 연속으로 3개의 데이터를 한 번에 싹 읽어옵니다.
            # 1: 카운터, 2: 비상정지 여부, 3: 작업 상태
            result = client.read_holding_registers(address=1, count=3, slave=1)
            
            if not result.isError():
                count = result.registers[0]
                e_stop = "🚨 비상 잠금!" if result.registers[1] == 1 else "✅ 정상"
                status = "🌟 작동 중..." if result.registers[2] == 1 else "💤 대기 중"
                
                # '\r'을 사용하면 터미널 화면이 밑으로 도배되지 않고 한 줄에서 값만 깔끔하게 바뀝니다!
                sys.stdout.write(f"\r[실시간 데이터] 카운터: {count} | 상태: {status} | 안전: {e_stop}          ")
                sys.stdout.flush()
            
            time.sleep(0.5) # 0.5초마다 화면 갱신
            
    except KeyboardInterrupt:
        print("\n\n모니터링을 종료합니다.")
    finally:
        client.close()
else:
    print("❌ 서버에 연결할 수 없습니다. 모드버스 서버 프로그램이 켜져 있는지 확인하세요.")
