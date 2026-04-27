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
