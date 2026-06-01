# 실종자 인상착의 시각화 MVP

웹 폼에서 성별, 나이대, 인상착의를 입력하면 FastAPI 서버가 마네킹 이미지와 옷 이미지 DB를 선택하고, 결과 PNG를 생성해 미리보기와 다운로드를 제공하는 발표용 MVP입니다.

현재 버전은 CatVTON/IDM-VTON 같은 실제 virtual try-on 모델을 자동 설치하거나 다운로드하지 않습니다. 대신 Pillow 기반 fallback renderer가 항상 PNG를 생성하므로 모델이 없어도 전체 웹 파이프라인을 바로 시연할 수 있습니다.

## Project Structure

```text
softwareproject1/
  README.md
  environment.yml
  requirements.txt
  app/
    main.py
    config.py
    schemas.py
    mannequin_selector.py
    clothing_retriever.py
    image_generator.py
    utils.py
  web/
    index.html
    style.css
    app.js
  data/
    mannequins/
      README.md
    clothes/
      README.md
      metadata.json
  outputs/
  scripts/
    setup_dirs.py
    build_sample_db.py
    test_pipeline.py
  models/
    README.md
```

## 1. Conda 환경 생성

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

## 2. 샘플 DB 생성

```bash
python scripts/build_sample_db.py
```

이 명령은 `data/clothes/`에 dummy clothes PNG와 `metadata.json`을 만들고, `data/mannequins/`에 샘플 마네킹 PNG를 생성합니다.

## 3. 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 브라우저 접속

```text
http://서버IP:8000
```

로컬에서 실행한다면:

```text
http://localhost:8000
```

## 5. 테스트 입력 예시

```text
Gender: male
Age Group: elderly
Top: red checkered shirt
Bottom: black pants
Accessory: black backpack
```

## 6. 출력

`outputs/` 폴더에 PNG가 생성되고, 웹 화면에서 preview 및 download가 가능합니다.

## API

### `GET /`

`web/index.html`을 반환합니다.

### `POST /generate`

Request:

```json
{
  "gender": "male",
  "age_group": "elderly",
  "top": "red checkered shirt",
  "bottom": "black pants",
  "accessory": "black backpack",
  "output_filename": "sample_result"
}
```

Response:

```json
{
  "status": "success",
  "image_url": "/outputs/sample_result.png",
  "selected_mannequin": "data/mannequins/male_elderly.png",
  "selected_clothes": {
    "top": "red checkered shirt (data/clothes/top_004.png)",
    "bottom": "black pants (data/clothes/bottom_001.png)",
    "accessory": "black backpack (data/clothes/accessory_001.png)"
  },
  "message": "PNG generated successfully using the fallback MVP renderer."
}
```

### `GET /outputs/{filename}`

`outputs/` 폴더의 PNG 파일을 반환합니다.

## Pipeline Test

API 없이 이미지 생성 파이프라인만 테스트할 수 있습니다.

```bash
python scripts/build_sample_db.py
python scripts/test_pipeline.py
```

성공하면 `outputs/pipeline_test_result.png`가 생성됩니다.

## Clothing Retriever

초기 버전은 태그 기반 검색입니다.

- 입력 문장을 소문자로 변환
- 공백, 하이픈, 쉼표 기준 토큰화
- metadata의 `tags`, `description`과 비교
- 가장 많이 겹치는 item 선택
- 점수가 0이면 해당 category의 첫 번째 item을 default로 반환

향후에는 `retrieve_best_clothing(description, category)` 함수 내부의 scoring을 CLIP embedding 검색으로 교체할 수 있습니다.

## Real VTON Integration

실제 모델 연동 위치:

- `app/image_generator.py`
- `run_virtual_tryon(...)`

후보:

- CatVTON
- IDM-VTON
- Stable Diffusion Inpainting

주의:

- 현재 MVP에서는 torch, diffusers, transformers 같은 무거운 패키지를 `requirements.txt`에 넣지 않았습니다.
- 모델 가중치를 자동 다운로드하지 않습니다.
- 실제 모델 연결 전까지 `USE_REAL_VTON = False`를 유지하세요.

향후 모델 연결 시 선택 설치 예시:

```bash
# 예시입니다. 실제 모델별 공식 문서를 확인한 뒤 별도 환경에서 설치하세요.
pip install torch diffusers transformers accelerate
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'PIL'`

환경이 활성화되어 있는지 확인한 뒤 패키지를 설치하세요.

```bash
pip install -r requirements.txt
```

### 웹에서 이미지가 안 보이는 경우

먼저 샘플 DB와 파이프라인 테스트를 실행하세요.

```bash
python scripts/build_sample_db.py
python scripts/test_pipeline.py
```

그리고 `outputs/`에 PNG 파일이 생성되었는지 확인하세요.

### `metadata.json`이 비어 있는 경우

```bash
python scripts/build_sample_db.py
```

를 다시 실행하면 샘플 metadata와 dummy image가 재생성됩니다.

### 포트 8000이 이미 사용 중인 경우

다른 포트를 사용하세요.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
