## 로드 오브 히어로즈 스토리 영상용 대사 추출기
로오히 서비스 종료 위기감으로(...) 대충 만든 스토리 백업 프로그램(일렉트론)



### 프로젝트 구조
OCR 엔진 서버: 파이썬(FastAPI)

프론트엔드: Vue.js

### 입력
로드 오브 히어로즈 단말접속>아카이브 내 시나리오, 마도대전, 레코드 등 스토리 선택 후 녹화한 비디오 

썸네일 예)
<img width="1280" height="720" alt="KRecord_01_01" src="https://github.com/user-attachments/assets/e8ea4e78-ed5f-44dc-b8d0-e1804af1a07f" />


### 출력
UI: 수정 가능한 대사 리스트

예)
<img width="980" height="546" alt="스크린샷 2026-02-15 154958" src="https://github.com/user-attachments/assets/18e6a767-d6f5-4fbd-a6bc-01bbc7f03fbe" />


최종 저장: JSON 포맷

예)
```
{
  "source": "XRecorder_20260207_02.mp4",
  "dialogues": [
    {
      "speaker": "시녀장",
      "text": "왕자님"
    },
    {
      "speaker": "시녀장",
      "text": "이제 일어나셔야 합니다."
    },
    {
      "speaker": "시녀장",
      "text": "이제 일어나셔야 합니다.\n오늘은 레오스 공화국에서 귀빈이\n오셨다고 말씀드렸잖아요!"
    }
  ]
}
```

### 제약사항
영상 포맷: mp4

해상도: 1280x720 권장 (더 클 경우 OCR 작업 시간 증가, 작을 경우 결과 품질 보장 불가)
