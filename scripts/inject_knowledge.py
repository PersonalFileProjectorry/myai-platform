import chromadb
from chromadb import Settings  # 이 줄 추가
from sentence_transformers import SentenceTransformer
import uuid

KNOWLEDGE_BASE = [
    {
        "category": "circuit",
        "topic": "LDO 레귤레이터",
        "content": "LDO 레귤레이터 설계. 입력전압은 출력전압보다 최소 0.3V에서 1V 높아야 함. 출력 커패시터 10uF에서 100uF. 대표 IC: AMS1117, LM7805, MCP1700. PCB에서 커패시터를 IC 최대한 가깝게 배치."
    },
    {
        "category": "circuit",
        "topic": "H브리지 모터드라이버",
        "content": "H브리지 DC모터 드라이버. IC: L298N 2A, DRV8833 1.5A, TB6612FNG 1.2A. 프리휠링 다이오드 필수. PWM으로 속도제어, DIR핀으로 방향제어. 모터전원과 로직전원 분리 필요."
    },
    {
        "category": "pcb",
        "topic": "PCB 설계 규칙",
        "content": "PCB 설계 기본 규칙. 최소 트레이스 폭 신호선 0.2mm 전원선 0.5mm 이상. 비아 크기 드릴 0.3mm 패드 0.6mm 최소. 부품간 간격 최소 0.5mm. 디커플링 커패시터는 IC 전원핀에서 1mm 이내. 고주파 신호는 90도 꺾임 금지."
    },
    {
        "category": "embedded",
        "topic": "Arduino 기초",
        "content": "Arduino 핵심 함수. pinMode OUTPUT INPUT INPUT_PULLUP. digitalWrite HIGH LOW. analogWrite 0에서 255 PWM출력. analogRead 0에서 1023 10bit ADC. delay millis 타이머. Serial.begin 9600. Wire.begin I2C. SPI.begin SPI통신."
    },
    {
        "category": "embedded",
        "topic": "ESP32 WiFi",
        "content": "ESP32 WiFi 연결. WiFi.begin ssid password. WiFi.status WL_CONNECTED 확인. HTTPClient로 HTTP 요청. http.begin URL. http.GET. http.getString으로 응답 수신. PubSubClient로 MQTT 연결."
    },
    {
        "category": "node-red",
        "topic": "Node-RED 기초",
        "content": "Node-RED 핵심 노드. inject 주기적 트리거. function JavaScript로 msg 처리. switch 조건분기. change msg 속성 변경. debug 디버그 출력. http in out REST API. mqtt in out MQTT 브로커. dashboard UI 위젯."
    },
    {
        "category": "code",
        "topic": "Python 시리얼 통신",
        "content": "Python Arduino 시리얼 통신. import serial. ser serial.Serial COM3 9600 timeout 1. ser.write로 데이터 전송. ser.readline으로 수신. decode utf-8. Linux에서는 /dev/ttyUSB0 사용."
    },
    {
        "category": "pcb",
        "topic": "KiCad 사용법",
        "content": "KiCad PCB 설계 툴. Schematic Editor에서 회로도 작성. PCB Editor에서 부품 배치 및 라우팅. Footprint 라이브러리에서 부품 패키지 선택. DRC로 설계 규칙 검사. Gerber 파일로 제조 출력."
    },
    {
        "category": "circuit",
        "topic": "전원 설계",
        "content": "전원 회로 설계. 벅 컨버터 강압형 SMPS 효율 90% 이상. 부스트 컨버터 승압형. LDO 저잡음 선형 레귤레이터. 바이패스 커패시터 100nF 세라믹을 각 IC 전원핀에 배치. 전원 시퀀싱 주의."
    },
    {
        "category": "embedded",
        "topic": "I2C 통신",
        "content": "I2C 통신 프로토콜. SDA 데이터선 SCL 클럭선. 풀업 저항 4.7k 필요. 주소 7비트. Arduino Wire 라이브러리 사용. Wire.beginTransmission 주소. Wire.write 데이터. Wire.endTransmission. Wire.requestFrom으로 수신."
    },
]

def inject_knowledge():
    client = chromadb.HttpClient(
    host="myai-chromadb",
    port=8000,
    settings=chromadb.Settings(
        chroma_api_impl="chromadb.api.fastapi.FastAPI",
        chroma_server_host="myai-chromadb",
        chroma_server_http_port=8000,
    )
)
    collection = client.get_or_create_collection("myai_memory")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"기존 메모리: {collection.count()}개")

    for item in KNOWLEDGE_BASE:
        text = f"[{item['category']}] {item['topic']}: {item['content']}"
        embedding = embedder.encode(text).tolist()
        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[text],
            metadatas={
                "category": item["category"],
                "topic": item["topic"],
                "provider": "knowledge_base",
                "rating": 5,
            }
        )
        print(f"완료: {item['topic']}")

    print(f"\n총 메모리: {collection.count()}개")

if __name__ == "__main__":
    inject_knowledge()