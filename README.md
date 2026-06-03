# 실종자 인상착의 시각화 MVP

웹 폼에서 성별, 나이대, 인상착의를 입력하면 FastAPI 서버가 마네킹 이미지와 옷 이미지 DB를 선택하고, 결과 PNG를 생성해 미리보기와 다운로드를 제공하는 발표용 MVP입니다.

현재 버전은 기본적으로 Pillow 기반 fallback renderer가 항상 PNG를 생성합니다. 동시에 `USE_REAL_VTON=1`이면 FASHN VTON v1.5를 lazy-load해서 실제 virtual try-on 추론을 먼저 시도하고, 실패하면 즉시 fallback으로 돌아갑니다.  
또한 `OPENAI_API_KEY`가 설정되어 있으면, 입력된 의상 설명을 OpenAI 이미지 생성 API로 먼저 옷 이미지로 만들고 `data/generated_garments/`에 캐시한 뒤 그 이미지를 VTON에 넣습니다. 같은 의상을 다시 넣으면 캐시 이미지를 재사용합니다.

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
    person_refs/
      README.md
      metadata.json
    dresscode/
      README.md
    viton_hd/
      README.md
    clothes/
      README.md
      metadata.json
    generated_garments/
      README.md
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

VITON-HD 데이터셋이 없을 때는 이 dummy sample DB가 자동 fallback으로 사용됩니다.

## 2-0. OpenAI 옷 이미지 생성 캐시

입력한 `Top`, `Bottom`, `Accessory` 설명이 있으면 앱이 먼저 OpenAI 이미지 생성 API로 해당 의상 이미지를 만듭니다. 생성된 이미지는 `data/generated_garments/` 아래에 저장되고, 같은 설명이 다시 들어오면 다시 생성하지 않고 캐시된 PNG를 재사용합니다.

`.env` 파일로 두고 싶으면 프로젝트 루트에 아래처럼 적어두면 됩니다. 앱이 시작할 때 자동으로 읽습니다.

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_IMAGE_MODEL=gpt-image-1.5
```

필수 설정:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

선택 설정:

```bash
export OPENAI_IMAGE_MODEL="gpt-image-1.5"
```

키가 없거나 OpenAI 호출이 실패하면 기존 데이터셋 기반 fallback으로 내려갑니다. 즉, 앱 자체는 계속 실행됩니다.

## 2-1. DressCode 데이터셋 배치

DressCode는 하의까지 포함하는 메인 의상 데이터셋입니다. 공식 저장소의 승인형 요청 절차를 통해 받은 뒤 `data/dresscode/` 아래에 풀어두면 됩니다.

공식 자료:

- [DressCode GitHub](https://github.com/aimagelab/dress-code)
- [DressCode paper](https://arxiv.org/abs/2204.08532)

배치 확인:

```bash
python scripts/check_dresscode.py
```

옷 메타데이터 등록:

```bash
python scripts/import_dresscode_clothes.py --limit 80
```

`top`과 `bottom` 검색은 DressCode를 우선 사용합니다. 필요하면 `--include-dresses`로 원피스도 포함할 수 있습니다.

## 2-2. VITON-HD 데이터셋 배치

실제 옷/사람 이미지를 fallback PNG에 포함하려면 VITON-HD 데이터셋을 아래 위치에 둡니다.

```text
data/viton_hd/
```

지원하는 폴더 구조:

```text
data/viton_hd/
  test/
    cloth/
      000001_00.jpg
      ...
    image/
      000001_00.jpg
      ...
```

또는:

```text
data/viton_hd/
  cloth/
  image/
```

VITON-HD 원본 데이터는 용량이 크므로 git에 올리지 않도록 `.gitignore`에 제외되어 있습니다.

배치 확인:

```bash
python scripts/check_viton_hd.py
```

`Status: ready`가 나오면 import할 수 있습니다.

## 2-3. VITON-HD 이미지 metadata 등록

VITON-HD cloth 이미지를 `data/clothes/metadata.json`에 등록합니다. VITON-HD는 주로 upper-body cloth이므로 초기 category는 `top`으로 등록합니다.

```bash
python scripts/import_viton_clothes.py --limit 30
```

수동 태그를 한 번에 추가하고 싶으면:

```bash
python scripts/import_viton_clothes.py --limit 30 --manual-tags "shirt,top,casual"
```

VITON-HD person/model 이미지를 `data/person_refs/metadata.json`에 등록합니다.

```bash
python scripts/import_viton_persons.py --limit 12
```

기본 동작은 선택된 person/model 이미지를 `data/person_refs/viton/`에 복사하고 metadata에 등록하는 것입니다. 원본 VITON-HD 파일 경로만 참조하고 싶으면:

```bash
python scripts/import_viton_persons.py --limit 12 --no-copy
```

수동 태그 예시:

```bash
python scripts/import_viton_persons.py --limit 12 --manual-tags "adult,front-view"
```

metadata는 처음에 파일명 기반 id와 기본 태그를 넣습니다. 색상/종류를 더 정확히 맞추고 싶으면 `manual_tags`를 직접 편집하세요.

예시:

```json
{
  "id": "viton_top_000001_00",
  "category": "top",
  "image_path": "data/viton_hd/test/cloth/000001_00.jpg",
  "tags": ["viton", "viton-hd", "cloth", "clothing", "top", "shirt", "upper"],
  "manual_tags": ["red", "checkered"],
  "description": "VITON-HD top 000001_00",
  "source_dataset": "VITON-HD",
  "source_path": "data/viton_hd/test/cloth/000001_00.jpg",
  "needs_manual_tags": true
}
```

VITON-HD는 이제 보조 fallback 용도입니다. DressCode가 없을 때만 사용합니다.

현재 웹/API 입력은 `gender=male|female`, `age_group=adult|kids`만 받습니다. `kids`는 내부적으로 `data/mannequins/kids.png` 자산을 우선 사용합니다.

## 3. 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

실제 모델 모드로 돌리고 싶으면 다음처럼 실행하세요.

```bash
export USE_REAL_VTON=1
export VTON_MODEL_ID=fashn-ai/fashn-vton-1.5
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

첫 생성 시 모델 파일이 Hugging Face에서 자동 다운로드될 수 있습니다. GPU와 충분한 VRAM이 있으면 실제 try-on 결과를 먼저 시도하고, 의존성이나 모델 로딩에 실패하면 기존 fallback PNG가 대신 생성됩니다.

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
Age Group: adult
Top: red checkered shirt
Bottom: black pants
Accessory: black backpack
```

## 6. 출력

`outputs/` 폴더에 PNG가 생성되고, 웹 화면에서 preview 및 download가 가능합니다.

## Real VTON Model

현재 연결된 실제 모델은 `fashn-ai/fashn-vton-1.5`입니다.

- 입력: 사람 이미지 + 옷 이미지
- 동작: Hugging Face에서 가중치를 lazy-load한 뒤 try-on 생성 시도
- 실패 시: 기존 fallback renderer로 자동 전환

필수 패키지:

```bash
pip install diffusers safetensors
pip install git+https://github.com/fashn-AI/fashn-vton-1.5.git
```

`torch`는 이 환경에 이미 설치되어 있다고 가정합니다. 새 환경이라면 별도로 PyTorch를 설치해야 합니다.

## API

### `GET /`

`web/index.html`을 반환합니다.

### `POST /generate`

Request:

```json
{
  "gender": "male",
  "age_group": "adult",
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
  "selected_mannequin": "data/mannequins/male_adult.png",
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

DressCode 데이터셋이 있는 경우:

```bash
python scripts/check_dresscode.py
python scripts/import_dresscode_clothes.py --limit 80
python scripts/test_pipeline.py
```

이 경우 검색과 try-on에 DressCode 옷 이미지가 우선 사용됩니다.

## Clothing Retriever

초기 버전은 태그 기반 검색입니다.

- 입력 문장을 소문자로 변환
- 공백, 하이픈, 쉼표 기준 토큰화
- metadata의 `tags`, `description`과 비교
- 가장 많이 겹치는 item 선택
- 점수가 0이면 해당 category의 첫 번째 item을 default로 반환
- DressCode가 등록되어 있으면 dummy sample보다 DressCode 항목을 우선 검색

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

- 실제 모델 모드에서는 `fashn-vton` 패키지와 모델 가중치를 첫 실행 시 자동으로 내려받습니다.
- 모델 가중치는 `models/fashn_vton/` 아래에 저장됩니다.
- `USE_REAL_VTON=0`으로 두면 기존 fallback PNG만 사용합니다.

향후 모델 연결 시 선택 설치 예시:

```bash
# 예시입니다. 실제 모델별 공식 문서를 확인한 뒤 별도 환경에서 설치하세요.
pip install torch diffusers safetensors
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

### DressCode를 넣었는데 dummy 이미지가 나오는 경우

먼저 데이터셋 폴더가 인식되는지 확인하세요.

```bash
python scripts/check_dresscode.py
```

그다음 metadata import를 다시 실행하세요.

```bash
python scripts/import_viton_clothes.py --limit 30
python scripts/import_viton_persons.py --limit 12
```

서버를 `--reload` 없이 실행 중이었다면 재시작해야 새 metadata와 코드가 반영됩니다.

### 포트 8000이 이미 사용 중인 경우

다른 포트를 사용하세요.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
