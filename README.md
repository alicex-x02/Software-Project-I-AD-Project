# 실종자 인상착의 시각화 MVP

웹 폼에서 성별, 나이대, 상의, 하의를 입력하면 FastAPI 서버가 OpenAI로 옷 이미지를 생성하고 `data/generated_garments/`에 캐시한 뒤, VTON 모델로 마네킹에 입혀서 PNG를 만들어 줍니다.

## 구성

```text
softwareproject1/
  app/
  web/
  data/
    mannequins/
    generated_garments/
  outputs/
  scripts/
  models/
```

현재 남는 핵심 데이터는 두 개입니다.

- `data/mannequins/`
- `data/generated_garments/`

## 환경 설정

```bash
conda env create -f environment.yml
conda activate missing-vton
```

또는:

```bash
conda create -n missing-vton python=3.10 -y
conda activate missing-vton
pip install -r requirements.txt
```

프로젝트 루트에 `.env` 파일을 두면 앱이 자동으로 읽습니다.

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_IMAGE_MODEL=gpt-image-1.5
```

## 샘플 마네킹 생성

```bash
python scripts/build_sample_db.py
```

이 스크립트는 `data/mannequins/`에 필요한 마네킹 PNG만 만듭니다. 기존 이미지가 있으면 덮어쓰지 않습니다.

## 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

브라우저 접속:

```text
http://127.0.0.1:8000
```

## 동작 방식

1. 상의와 하의를 텍스트로 입력한다.
2. 앱이 OpenAI 이미지 생성 API로 옷 이미지를 만든다.
3. 생성된 이미지는 `data/generated_garments/<category>/` 아래에 캐시된다.
4. VTON 모델이 마네킹 이미지에 그 옷을 입힌다.
5. 결과 PNG가 `outputs/`에 저장되고 웹에서 미리보기와 다운로드가 가능하다.

같은 옷 설명을 다시 넣으면 캐시된 PNG를 재사용합니다.

## 테스트

```bash
python scripts/test_pipeline.py
```

성공하면 `outputs/pipeline_test_result.png`가 생성됩니다.

## 문제 해결

- OpenAI 키가 없으면 옷 생성이 로컬 placeholder로 대체됩니다.
- VTON 모델 로딩이 실패하면 fallback PNG가 생성됩니다.
- 새 이미지를 만들었는데 예전 결과가 보이면 브라우저 새로고침을 해보세요.
