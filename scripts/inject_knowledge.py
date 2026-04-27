import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# Q&A 쌍 형태로 구성된 전문 지식 (검색 정확도 향상)
KNOWLEDGE_BASE = [
    # LDO 레귤레이터
    {"q": "AMS1117 최소 드롭아웃 전압은?",
     "a": "약 1.2V. 3.3V 출력 시 최소 4.5V 입력 필요. 5V 입력이 일반적.",
     "tags": ["LDO", "AMS1117", "dropout", "레귤레이터"]},

    {"q": "LDO 레귤레이터 출력 커패시터 선택 기준은?",
     "a": "10uF~100uF 세라믹 또는 전해 커패시터. 안정성을 위해 입력에도 1uF~10uF 추가.",
     "tags": ["LDO", "커패시터", "안정성"]},

    {"q": "5V를 3.3V로 변환하는 가장 간단한 회로는?",
     "a": "AMS1117-3.3 사용. VIN에 5V 입력, VOUT에서 3.3V 출력. 입출력에 10uF 커패시터 추가.",
     "tags": ["LDO", "AMS1117", "3.3V", "5V변환"]},

    # H브리지
    {"q": "DC모터 정역회전 제어 IC 추천은?",
     "a": "L298N(2A), DRV8833(1.5A), TB6612FNG(1.2A). 소형은 DRV8833, 대전류는 L298N.",
     "tags": ["H브리지", "모터드라이버", "DC모터"]},

    {"q": "H브리지에서 프리휠링 다이오드가 필요한 이유는?",
     "a": "모터 역기전력으로부터 회로 보호. L298N은 내장, DRV8833도 내장. 외부 추가 불필요.",
     "tags": ["H브리지", "다이오드", "역기전력"]},

    # PCB 설계
    {"q": "PCB 신호선 최소 트레이스 폭은?",
     "a": "신호선 0.2mm 이상, 전원선 0.5mm 이상, 고전류선은 IPC-2221 기준으로 계산.",
     "tags": ["PCB", "트레이스", "설계규칙"]},

    {"q": "PCB 디커플링 커패시터 배치 방법은?",
     "a": "IC 전원핀에서 1mm 이내 배치. 100nF 세라믹 필수. 추가로 10uF 벌크 커패시터 병렬.",
     "tags": ["PCB", "디커플링", "커패시터", "노이즈"]},

    {"q": "PCB 고주파 신호 라우팅 주의사항은?",
     "a": "90도 꺾임 금지, 45도 또는 곡선 사용. 차동쌍은 동일 길이 유지. 접지 플레인 필수.",
     "tags": ["PCB", "고주파", "RF", "라우팅"]},

    # Arduino
    {"q": "Arduino analogWrite 함수 사용법은?",
     "a": "analogWrite(pin, 0~255). PWM 출력. 3,5,6,9,10,11번 핀만 지원. 주파수 약 490Hz.",
     "tags": ["Arduino", "PWM", "analogWrite"]},

    {"q": "Arduino I2C 통신 기본 코드는?",
     "a": "Wire.begin() 초기화. Wire.beginTransmission(주소). Wire.write(데이터). Wire.endTransmission().",
     "tags": ["Arduino", "I2C", "Wire"]},

    {"q": "Arduino 인터럽트 사용법은?",
     "a": "attachInterrupt(digitalPinToInterrupt(2), ISR함수, RISING). 2번, 3번 핀만 지원(Uno기준).",
     "tags": ["Arduino", "인터럽트", "ISR"]},

    # ESP32
    {"q": "ESP32 WiFi 연결 기본 코드는?",
     "a": "WiFi.begin(ssid, password). while(WiFi.status()!=WL_CONNECTED) delay(500). 연결 완료.",
     "tags": ["ESP32", "WiFi", "연결"]},

    {"q": "ESP32와 Arduino 차이점은?",
     "a": "ESP32는 듀얼코어 240MHz, WiFi/BT 내장, 4MB Flash. Arduino Uno는 단일코어 16MHz, 통신모듈 없음.",
     "tags": ["ESP32", "Arduino", "비교"]},

    # Node-RED
    {"q": "Node-RED function 노드에서 msg 반환 방법은?",
     "a": "return msg; 로 단일 출력. return [msg, null]; 로 첫번째 출력만. return null; 로 중단.",
     "tags": ["Node-RED", "function", "msg"]},

    {"q": "Node-RED MQTT 연결 설정 방법은?",
     "a": "mqtt in/out 노드 사용. 브로커 주소, 포트(1883), 토픽 설정. mosquitto 브로커 권장.",
     "tags": ["Node-RED", "MQTT", "IoT"]},

    # KiCad
    {"q": "KiCad Gerber 파일 출력 방법은?",
     "a": "PCB Editor → File → Plot. 레이어 선택(F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen, Edge.Cuts). 드릴파일 별도 생성.",
     "tags": ["KiCad", "Gerber", "제조"]},

    {"q": "KiCad DRC 오류 해결 방법은?",
     "a": "Inspect → Design Rules Checker 실행. Clearance 오류는 트레이스 간격 조정. Unconnected 오류는 라우팅 완료 필요.",
     "tags": ["KiCad", "DRC", "오류"]},

    # 전원 설계
    {"q": "벅 컨버터와 LDO 차이점은?",
     "a": "벅: 효율 90%이상, 스위칭 노이즈 있음. LDO: 효율 낮음, 저잡음. 배터리는 벅, 아날로그회로는 LDO.",
     "tags": ["전원", "벅컨버터", "LDO", "효율"]},

    {"q": "USB Type-C 5V 입력 3.3V 출력 회로 설계는?",
     "a": "USB-C 커넥터 → AMS1117-3.3 → 3.3V출력. BOM: AMS1117-3.3, 10uF캡 x2. CC핀에 5.1kΩ 저항 필요.",
     "tags": ["USB-C", "전원", "AMS1117", "3.3V"]},

    # Python 코딩
    {"q": "Python으로 Arduino 시리얼 통신 코드는?",
     "a": "import serial. ser=serial.Serial('COM3',9600). ser.write(b'data'). line=ser.readline().decode(). Linux는 /dev/ttyUSB0.",
     "tags": ["Python", "시리얼", "Arduino", "통신"]},

     # STM32
    {"q": "STM32 GPIO 출력 설정 방법은?",
     "a": "HAL_GPIO_Init으로 GPIO_MODE_OUTPUT_PP 설정. HAL_GPIO_WritePin으로 HIGH/LOW 제어. CubeMX로 자동생성 권장.",
     "tags": ["STM32", "GPIO", "HAL"]},

    {"q": "STM32 UART 통신 기본 코드는?",
     "a": "HAL_UART_Transmit(&huart1, data, len, timeout). HAL_UART_Receive로 수신. DMA 모드 사용시 효율적.",
     "tags": ["STM32", "UART", "통신"]},

    {"q": "STM32 타이머 PWM 설정 방법은?",
     "a": "CubeMX에서 TIM 선택, PWM Generation 모드. HAL_TIM_PWM_Start. CCR값으로 듀티사이클 조절.",
     "tags": ["STM32", "타이머", "PWM"]},

    {"q": "STM32 ADC 사용 방법은?",
     "a": "HAL_ADC_Start. HAL_ADC_PollForConversion. HAL_ADC_GetValue로 값 읽기. 12bit 해상도 0~4095.",
     "tags": ["STM32", "ADC", "아날로그"]},

    # SPI 통신
    {"q": "SPI 통신 4선 구성은?",
     "a": "MOSI(마스터출력), MISO(마스터입력), SCK(클럭), CS(칩선택). 전이중 통신. 속도 최대 수십MHz.",
     "tags": ["SPI", "통신", "프로토콜"]},

    {"q": "Arduino SPI 기본 코드는?",
     "a": "SPI.begin(). digitalWrite(CS, LOW). SPI.transfer(data). digitalWrite(CS, HIGH). SPI.end().",
     "tags": ["SPI", "Arduino", "코드"]},

    # UART
    {"q": "UART와 USART 차이점은?",
     "a": "UART는 비동기만 지원. USART는 동기/비동기 모두 지원. 일반적으로 UART 모드로 사용. 보레이트 양쪽 동일해야 함.",
     "tags": ["UART", "USART", "통신"]},

    {"q": "UART 보레이트 설정 기준은?",
     "a": "9600(저속), 115200(일반), 921600(고속). 양쪽 장치 동일하게 설정 필수. 오차 2% 이내 권장.",
     "tags": ["UART", "보레이트", "설정"]},

    # 배터리 관리
    {"q": "리튬이온 배터리 충전 IC 추천은?",
     "a": "TP4056(단셀, 1A), MCP73831(단셀, 500mA), BQ24195(멀티셀). 보호회로 IC 별도 필요.",
     "tags": ["배터리", "충전IC", "리튬이온"]},

    {"q": "배터리 과방전 보호 회로 설계는?",
     "a": "DW01A + FS8205A 조합. 과방전 2.4V, 과충전 4.28V, 과전류 보호. 대부분 배터리 팩에 내장.",
     "tags": ["배터리", "보호회로", "과방전"]},

    {"q": "리튬배터리 3.7V를 5V로 승압하는 방법은?",
     "a": "부스트 컨버터 사용. MT3608(2A), XL6009(4A). 효율 85~93%. 인덕터, 다이오드, 커패시터 필요.",
     "tags": ["배터리", "부스트", "승압", "5V"]},

    # RTOS
    {"q": "FreeRTOS 태스크 생성 방법은?",
     "a": "xTaskCreate(함수, 이름, 스택크기, 파라미터, 우선순위, 핸들). vTaskStartScheduler()로 시작.",
     "tags": ["FreeRTOS", "RTOS", "태스크"]},

    {"q": "FreeRTOS 세마포어 사용 목적은?",
     "a": "공유자원 접근 제어. xSemaphoreCreateMutex로 생성. xSemaphoreTake로 획득, xSemaphoreGive로 반환.",
     "tags": ["FreeRTOS", "세마포어", "동기화"]},

    # 센서
    {"q": "DHT22 온습도 센서 Arduino 코드는?",
     "a": "DHT dht(pin, DHT22). dht.begin(). float t=dht.readTemperature(). float h=dht.readHumidity(). 라이브러리 필요.",
     "tags": ["DHT22", "온도센서", "Arduino"]},

    {"q": "MPU6050 자이로센서 I2C 주소는?",
     "a": "기본 0x68. AD0핀 HIGH시 0x69. Wire.beginTransmission(0x68). 6축 IMU(가속도+자이로).",
     "tags": ["MPU6050", "자이로", "I2C", "IMU"]},

    {"q": "초음파센서 HC-SR04 사용법은?",
     "a": "Trig핀 10us HIGH펄스. Echo핀 펄스폭 측정. 거리=펄스폭*0.034/2 (cm). 측정범위 2~400cm.",
     "tags": ["HC-SR04", "초음파", "거리센서"]},

    # 전력 전자
    {"q": "MOSFET 게이트 드라이버가 필요한 이유는?",
     "a": "고속 스위칭시 게이트 커패시턴스 충방전 전류 공급. IR2110, TC4420 사용. 없으면 스위칭 손실 증가.",
     "tags": ["MOSFET", "게이트드라이버", "스위칭"]},

    {"q": "옵토커플러 사용 목적은?",
     "a": "고압/저압 회로 전기적 절연. PC817 일반용, HCPL-2630 고속용. LED+포토트랜지스터 구조.",
     "tags": ["옵토커플러", "절연", "PC817"]},

    # 통신 프로토콜
    {"q": "CAN 버스 통신 특징은?",
     "a": "자동차/산업용 표준. 최대 1Mbps. 차동신호(CANH/CANL). 멀티마스터. 120Ω 종단저항 필수.",
     "tags": ["CAN", "통신", "자동차", "산업"]},

    {"q": "RS-485 통신 특징은?",
     "a": "최대 1200m 장거리. 멀티드롭(32노드). 차동신호. 산업현장 표준. MAX485 IC 사용. 120Ω 종단.",
     "tags": ["RS485", "장거리통신", "산업"]},

    # Python 심화
    {"q": "Python asyncio 기본 사용법은?",
     "a": "async def 함수정의. await로 비동기 호출. asyncio.run()으로 실행. FastAPI는 asyncio 기반.",
     "tags": ["Python", "asyncio", "비동기"]},

    {"q": "Python numpy 배열 연산 기본은?",
     "a": "np.array([1,2,3]). np.zeros((3,3)). 브로드캐스팅으로 행렬연산. np.dot으로 행렬곱.",
     "tags": ["Python", "numpy", "배열"]},

    # Docker
    {"q": "Docker 컨테이너 로그 확인 방법은?",
     "a": "docker logs 컨테이너명. -f 옵션으로 실시간. --tail 100으로 마지막 100줄. docker compose logs.",
     "tags": ["Docker", "로그", "디버깅"]},

    {"q": "Docker 볼륨 마운트 사용 목적은?",
     "a": "컨테이너 재시작해도 데이터 유지. -v 호스트경로:컨테이너경로. docker compose volumes 섹션.",
     "tags": ["Docker", "볼륨", "데이터유지"]},

    # Git
    {"q": "Git 기본 워크플로우는?",
     "a": "git add . 스테이징. git commit -m 메시지. git push 원격저장소. git pull 최신화.",
     "tags": ["Git", "버전관리", "워크플로우"]},

    {"q": "Git 브랜치 생성 및 병합 방법은?",
     "a": "git branch 브랜치명. git checkout 브랜치명. 작업 후 git merge. 충돌시 수동해결 후 커밋.",
     "tags": ["Git", "브랜치", "병합"]},

    # KiCad 심화
    {"q": "KiCad 커스텀 풋프린트 만드는 방법은?",
     "a": "Footprint Editor에서 새 풋프린트 생성. 패드 배치, 실크스크린 추가. 라이브러리 저장 후 PCB에서 사용.",
     "tags": ["KiCad", "풋프린트", "커스텀"]},

    {"q": "KiCad 3D 뷰어 사용 방법은?",
     "a": "PCB Editor → View → 3D Viewer. 부품 3D모델은 .step 파일 연결. MCAD 검토에 활용.",
     "tags": ["KiCad", "3D뷰어", "검토"]},

    # 임베디드 심화
    {"q": "부트로더란 무엇인가?",
     "a": "전원 인가시 제일 먼저 실행되는 프로그램. 펌웨어 업데이트 담당. Arduino는 Optiboot 사용.",
     "tags": ["부트로더", "임베디드", "펌웨어"]},

    {"q": "JTAG 디버깅 인터페이스란?",
     "a": "하드웨어 디버깅 표준. STLink, JLink 사용. 중단점 설정, 레지스터 확인, 메모리 뷰 가능.",
     "tags": ["JTAG", "디버깅", "STM32"]},

     # 복잡한 회로 설계 (다층 구조)
    {"q": "Arduino 온도모니터링 전체 시스템 회로 설계는?",
     "a": """회로 JSON:
{
  "type": "circuit",
  "title": "Arduino 온도모니터링",
  "components": [
    {"id":"VCC","type":"power","value":"5V","x":1,"y":6},
    {"id":"R1","type":"resistor","value":"10kΩ","x":3,"y":6},
    {"id":"DHT22","type":"ic","value":"온도센서","x":5,"y":6},
    {"id":"R2","type":"resistor","value":"330Ω","x":3,"y":4},
    {"id":"LED1","type":"led","value":"경고LED","x":5,"y":4},
    {"id":"ARD","type":"ic","value":"Arduino","x":5,"y":2},
    {"id":"GND","type":"ground","value":"0V","x":7,"y":6}
  ],
  "connections": [
    {"from":"VCC","to":"R1"},{"from":"R1","to":"DHT22"},
    {"from":"DHT22","to":"ARD"},{"from":"VCC","to":"R2"},
    {"from":"R2","to":"LED1"},{"from":"LED1","to":"ARD"},
    {"from":"DHT22","to":"GND"},{"from":"LED1","to":"GND"}
  ]
}""",
     "tags": ["Arduino", "DHT22", "온도모니터링", "회로설계"]},

    {"q": "ESP32 IoT 센서허브 Node-RED 플로우 설계는?",
     "a": """플로우 JSON:
{
  "type": "nodered",
  "title": "ESP32 IoT 센서허브",
  "nodes": [
    {"id":"1","name":"온도센서","type":"mqtt in","x":0,"y":0},
    {"id":"2","name":"습도센서","type":"mqtt in","x":0,"y":1.5},
    {"id":"3","name":"데이터검증","type":"function","x":2.5,"y":0},
    {"id":"4","name":"임계값체크","type":"switch","x":2.5,"y":1.5},
    {"id":"5","name":"DB저장","type":"http out","x":5,"y":0},
    {"id":"6","name":"경보알림","type":"mqtt out","x":5,"y":1.5},
    {"id":"7","name":"대시보드","type":"debug","x":5,"y":3}
  ],
  "connections": [
    {"from":"1","to":"3"},{"from":"2","to":"4"},
    {"from":"3","to":"5"},{"from":"3","to":"7"},
    {"from":"4","to":"6"},{"from":"4","to":"7"}
  ]
}""",
     "tags": ["ESP32", "Node-RED", "IoT", "MQTT", "센서허브"]},

    {"q": "STM32 모터제어 시스템 회로 설계는?",
     "a": """회로 JSON:
{
  "type": "circuit",
  "title": "STM32 모터제어 시스템",
  "components": [
    {"id":"VCC12","type":"power","value":"12V","x":1,"y":8},
    {"id":"VCC5","type":"power","value":"5V","x":1,"y":5},
    {"id":"VCC33","type":"power","value":"3.3V","x":1,"y":2},
    {"id":"LDO","type":"ic","value":"AMS1117","x":3,"y":5},
    {"id":"STM32","type":"ic","value":"STM32F4","x":5,"y":2},
    {"id":"DRV","type":"ic","value":"DRV8833","x":5,"y":5},
    {"id":"MOTOR","type":"ic","value":"DC모터","x":7,"y":5},
    {"id":"ENC","type":"ic","value":"엔코더","x":7,"y":2},
    {"id":"C1","type":"capacitor","value":"100uF","x":3,"y":8},
    {"id":"GND","type":"ground","value":"0V","x":9,"y":8}
  ],
  "connections": [
    {"from":"VCC12","to":"C1"},{"from":"C1","to":"DRV"},
    {"from":"VCC5","to":"LDO"},{"from":"LDO","to":"VCC33"},
    {"from":"VCC33","to":"STM32"},{"from":"STM32","to":"DRV"},
    {"from":"DRV","to":"MOTOR"},{"from":"ENC","to":"STM32"},
    {"from":"MOTOR","to":"GND"},{"from":"STM32","to":"GND"}
  ]
}""",
     "tags": ["STM32", "모터제어", "DRV8833", "엔코더"]},

    {"q": "배터리 관리 시스템 전체 회로 설계는?",
     "a": """회로 JSON:
{
  "type": "circuit",
  "title": "배터리 관리 시스템",
  "components": [
    {"id":"BAT","type":"power","value":"Li-Ion","x":1,"y":6},
    {"id":"PROT","type":"ic","value":"DW01A","x":3,"y":6},
    {"id":"CHG","type":"ic","value":"TP4056","x":3,"y":4},
    {"id":"BOOST","type":"ic","value":"MT3608","x":5,"y":6},
    {"id":"LDO","type":"ic","value":"AMS1117","x":5,"y":4},
    {"id":"MCU","type":"ic","value":"ESP32","x":7,"y":5},
    {"id":"LED1","type":"led","value":"충전표시","x":7,"y":3},
    {"id":"USBC","type":"ic","value":"USB-C","x":1,"y":4},
    {"id":"GND","type":"ground","value":"0V","x":9,"y":6}
  ],
  "connections": [
    {"from":"USBC","to":"CHG"},{"from":"CHG","to":"BAT"},
    {"from":"BAT","to":"PROT"},{"from":"PROT","to":"BOOST"},
    {"from":"BOOST","to":"MCU"},{"from":"CHG","to":"LDO"},
    {"from":"LDO","to":"MCU"},{"from":"CHG","to":"LED1"},
    {"from":"MCU","to":"GND"},{"from":"BOOST","to":"GND"}
  ]
}""",
     "tags": ["배터리", "BMS", "TP4056", "MT3608", "ESP32"]},
]


def inject_knowledge():
    client = chromadb.HttpClient(host="myai-chromadb", port=8000)
    collection = client.get_or_create_collection("myai_memory")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # 기존 데이터 초기화
    try:
        client.delete_collection("myai_memory")
        collection = client.get_or_create_collection("myai_memory")
        print("기존 데이터 초기화 완료")
    except:
        pass

    for item in KNOWLEDGE_BASE:
        # Q&A 쌍으로 임베딩 (검색 정확도 향상)
        text = f"질문: {item['q']}\n답변: {item['a']}\n태그: {', '.join(item['tags'])}"
        embedding = embedder.encode(text).tolist()

        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[text],
            metadatas={
                "question": item["q"],
                "tags": ", ".join(item["tags"]),
                "provider": "knowledge_base",
                "rating": 5,
            }
        )
        print(f"완료: {item['q'][:40]}...")

    print(f"\n총 메모리: {collection.count()}개")


if __name__ == "__main__":
    inject_knowledge()


if __name__ == "__main__":
    inject_knowledge()
