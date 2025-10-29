# 트레이딩 시스템 프로젝트

이 프로젝트는 실시간 자동 매매, 시장 데이터 수집, 트레이딩 전략 구현을 위한 시스템입니다. 업비트(Upbit) 거래소를 기반으로 한 자동화된 트레이딩 봇을 구현하고 있습니다.

## 프로젝트 구조

### 루트 디렉토리
- `.env` - 환경 변수 및 민감한 설정값 (API 키 등)
- `requirements.txt` - 파이썬 패키지 의존성 목록
- `phase1.3_*.csv` - 백테스팅용 거래 및 포지션 데이터 파일
  - `phase1.3_train_*.csv` - 학습용 데이터
  - `phase1.3_test_*.csv` - 테스트용 데이터

### `/app` - 메인 애플리케이션
핵심 애플리케이션 코드가 모듈별로 구성된 디렉토리입니다.

#### `/app/trading` - 트레이딩 코어
- `live_trading_bot.py` - 메인 트레이딩 봇 구현체. 시장 데이터를 모니터링하고 거래 신호에 따라 주문을 실행합니다.
- `order_manager.py` - 주문 실행 및 관리를 담당. 주문 생성, 수정, 취소, 상태 추적 등의 기능을 제공합니다.
- `strategy.py` - 다양한 트레이딩 전략이 구현된 모듈. 기술적 지표 기반의 매매 신호를 생성합니다.

#### `/app/data` - 데이터 관리
- `data_collector.py` - 업비트 API를 통해 시장 데이터를 수집하고 전처리하는 모듈. 캔들스틱, 호가창, 체결 내역 등을 수집합니다.

#### `/app/config` - Configuration
- `root_config.py` - Main configuration settings (moved from root)
- `config.py` - Additional configuration (existing file)

#### `/app/websocket` - 웹소켓 구현
- `manager.py` - 실시간 시장 데이터 스트리밍을 위한 WebSocket 연결을 관리하고, 구독자에게 데이터를 브로드캐스팅합니다.
- (기타 WebSocket 관련 파일들)

#### `/app/api` - API 엔드포인트
- RESTful API 엔드포인트 구현. 외부 시스템과의 연동을 담당합니다.
- 거래 내역 조회, 계좌 정보 확인 등의 기능을 제공합니다.

#### `/app/utils` - Utility Functions
- Helper functions and utilities

### `/tests` - 테스트 스위트
- `test_connection.py` - API 및 WebSocket 연결 테스트
- `test_order.py` - 주문 생성 및 관리 기능 테스트
- `check_current_signal.py` - 현재 시장 상황에서의 트레이딩 신호 확인 유틸리티

## 시작하기

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:
```
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here
```

### 3. 트레이딩 봇 실행
```bash
python -m app.trading.live_trading_bot
```

### 4. 백테스트 실행 (선택사항)
```bash
python -m tests.test_strategy
```

## Directory Structure

```
.
├── .env
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── trading/
│   │   ├── live_trading_bot.py
│   │   ├── order_manager.py
│   │   └── strategy.py
│   ├── data/
│   │   └── data_collector.py
│   ├── config/
│   │   ├── config.py
│   │   └── root_config.py
│   ├── websocket/
│   │   └── manager.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── utils/
└── tests/
    ├── test_connection.py
    ├── test_order.py
    └── check_current_signal.py
```

## 주요 기능
- **실시간 시장 모니터링**: WebSocket을 통한 실시간 시세 모니터링
- **다양한 트레이딩 전략**: RSI, MACD, 볼린저 밴드 등 다양한 기술적 지표 기반 전략 지원
- **리스크 관리**: 손절매, 익절매, 포지션 사이징 등 기본적인 리스크 관리 기능 내장
- **백테스팅**: 과거 데이터를 활용한 전략 검증 기능
- **로깅**: 상세한 거래 내역 및 시스템 로그 기록

## 개발 가이드라인
1. **코드 스타일**: PEP 8 스타일 가이드 준수
2. **테스트**: 새로운 기능 추가 시 반드시 테스트 코드 작성
3. **커밋 메시지**: 명확하고 간결한 커밋 메시지 사용
4. **문서화**: 모든 주요 함수와 클래스에 독스트링 작성

## 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 기여 방법
1. 이슈를 생성하여 변경사항을 논의합니다.
2. 포크하여 기능 브랜치를 만듭니다.
3. 변경사항을 커밋하고 푸시합니다.
4. 풀 리퀘스트를 생성합니다.

## 문의
추가 문의사항이 있으시면 이슈를 생성해 주세요.
