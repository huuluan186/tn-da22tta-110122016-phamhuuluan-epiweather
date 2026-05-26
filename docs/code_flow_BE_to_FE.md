# Code Flow: Backend → Frontend — EpiWeather

Tài liệu này mô tả luồng dữ liệu đi từ database → backend (FastAPI) → frontend (React)
cho từng tính năng chính. Đọc theo thứ tự từ trên xuống.

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Luồng 1 — Risk Map (trang chính)](#2-luồng-1--risk-map-trang-chính)
3. [Luồng 2 — Real-time Prediction (POST /predict)](#3-luồng-2--real-time-prediction)
4. [Luồng 3 — Country Detail / History](#4-luồng-3--country-detail--history)
5. [Luồng 4 — Analytics Page](#5-luồng-4--analytics-page)
6. [State Management — Zustand store](#6-state-management--zustand-store)
7. [Sơ đồ tổng hợp tất cả luồng](#7-sơ-đồ-tổng-hợp)

---

## 1. Tổng quan kiến trúc

```
PostgreSQL 15
    │
    ▼
backend/app/
    ├── models/          ← SQLAlchemy ORM (ánh xạ Python class → DB table)
    ├── crud/            ← Truy vấn SQL thuần, trả về ORM objects
    ├── services/        ← Business logic: tổng hợp crud + ML inference
    ├── schemas/         ← Pydantic: validate input/output, serialize → JSON
    └── api/v1/endpoints/← FastAPI router: nhận HTTP request → gọi service → trả response

        HTTP (JSON)
            │
            ▼
frontend/src/
    ├── api/             ← Axios: gọi HTTP, trả về typed Promise<T>
    ├── hooks/           ← React Query: cache + auto-refetch + loading/error state
    ├── store/uiStore.ts ← Zustand: lưu state toàn app (disease, year, week, region)
    ├── pages/           ← Route-level components, ghép sidebar + map
    └── components/      ← UI thuần: nhận props, render HTML
```

**Nguyên tắc tách tầng:**
- `crud/` KHÔNG biết business logic — chỉ query/insert
- `services/` KHÔNG biết HTTP — chỉ gọi crud + xử lý data
- `endpoints/` KHÔNG xử lý data — chỉ gọi service + trả Pydantic schema
- `hooks/` KHÔNG render UI — chỉ fetch + expose `{data, isLoading, error}`
- `components/` KHÔNG fetch data — chỉ nhận props + render

---

## 2. Luồng 1 — Risk Map (trang chính)

**Mô tả:** Người dùng vào trang chủ `/`, chọn disease/year/week → bản đồ thế giới hiển thị màu
Low/Medium/High cho 197 quốc gia.

### 2.1 Trigger

```
frontend/src/store/uiStore.ts
    disease: "flu" | "dengue"   ← mặc định "flu"
    year: number                ← mặc định năm hiện tại
    week: number                ← mặc định tuần hiện tại
```

Khi user thay đổi disease/year/week trong sidebar → Zustand store update → `useRiskMap`
hook tự re-fetch (React Query dependency).

### 2.2 Frontend: Hook fetch data

**File:** `frontend/src/hooks/useRiskMap.ts`

```typescript
// useRiskMap gọi API, cache kết quả, trả về { data, isLoading, error }
const { data, isLoading } = useRiskMap(disease, year, week);
```

Hook này gọi:
```typescript
// frontend/src/api/infer.ts  (hoặc api/risk.ts)
GET /api/v1/risk-map/{disease}?year={year}&week={week}
```

Nếu API lỗi hoặc chưa có backend → fallback về `lib/mockRisk.ts` (mock data)
để UI vẫn hiển thị được trong quá trình phát triển.

### 2.3 Backend: Router nhận request

**File:** `backend/app/api/v1/endpoints/risk.py`

```python
@router.get("/risk-map/{disease}", response_model=RiskMapResponse)
async def get_risk_map(
    disease: str,
    year: int = Query(...),
    week: int = Query(...),
    db: Session = Depends(get_db),
):
    return await risk_service.get_risk_map(db, disease, year, week)
```

**Việc của endpoint:** validate params, gọi service, trả Pydantic schema.

### 2.4 Backend: Service xử lý business logic

**File:** `backend/app/services/risk_service.py`

```python
async def get_risk_map(db, disease, year, week) -> RiskMapResponse:
    # 1. Lấy predictions từ DB cho (disease, year, week)
    predictions = crud.predictions.list_for_map(db, disease, year, week)

    # 2. Join với countries để lấy lat/lon, who_region
    # 3. Tính risk_level nếu chưa có (so sánh với risk_thresholds)
    # 4. Build response object
    return RiskMapResponse(
        disease=disease,
        iso_year=year,
        iso_week=week,
        count=len(items),
        items=items,   # List[RiskMapItem]
    )
```

### 2.5 Backend: CRUD query DB

**File:** `backend/app/crud/predictions.py`

```python
def list_for_map(db, disease_code, iso_year, iso_week):
    # SELECT predictions JOIN countries JOIN diseases
    # WHERE iso_year = ? AND iso_week = ? AND disease_code = ?
    # Trả về list ORM Prediction objects
```

**Bảng DB liên quan:**
- `predictions` (PARTITION BY iso_year) — predicted_cases, risk_level, prob_high
- `risk_thresholds` — q33, q67 per (iso3, disease)
- `countries` — country_name, latitude, longitude, who_region

### 2.6 Backend: Pydantic Schema serialize → JSON

**File:** `backend/app/schemas/prediction.py`

```python
class RiskMapItem(BaseModel):
    iso3: str
    country_name: str
    latitude: float | None
    longitude: float | None
    who_region: str | None
    predicted_cases: float | None
    risk_level: str | None          # "low" | "medium" | "high" | "critical" | "none"
    risk_q33: float | None
    risk_q67: float | None

class RiskMapResponse(BaseModel):
    disease: str
    iso_year: int
    iso_week: int
    count: int
    items: list[RiskMapItem]
```

### 2.7 Frontend: Type definition

**File:** `frontend/src/types/api.ts`

```typescript
export interface RiskMapItem {
  iso3: string;
  country_name: string;
  latitude: number | null;
  longitude: number | null;
  who_region: string | null;
  predicted_cases: number | null;
  risk_level: "none" | "low" | "medium" | "high" | "critical" | null;
  risk_q33: number | null;
  risk_q67: number | null;
}

export interface RiskMapResponse {
  disease: string;
  iso_year: number;
  iso_week: number;
  count: number;
  items: RiskMapItem[];
}
```

**Lưu ý:** Type TS phải khớp chính xác với Pydantic schema Python. Nếu backend thêm field
mới mà FE không update type → TypeScript không bắt lỗi runtime, chỉ bắt lỗi nếu dùng `strict`.

### 2.8 Frontend: Render components

```
HomePage.tsx
    ├── RiskMapSidebar (trái)  ← nhận { disease, year, week } từ uiStore
    │     ├── DiseaseTabs       ← set store.disease
    │     ├── WeekPicker        ← set store.year + store.week
    │     ├── RegionFilter      ← set store.regions
    │     └── SummaryStats      ← nhận data từ useRiskMap, đếm Low/Med/High
    │
    ├── WorldMap (giữa)         ← nhận items[] từ useRiskMap
    │     └── ECharts map: tô màu từng quốc gia theo risk_level
    │
    └── AlertsSidebar (phải)    ← nhận items[] từ useRiskMap, filter risk_level=high
          ├── AlertItem (×N)
          └── Sparkline
```

**Mapping risk_level → màu:**
```typescript
// frontend/src/types/domain.ts
const RISK_COLORS = {
  none: "#e5e7eb",      // xám nhạt
  low: "#22c55e",       // xanh lá
  medium: "#f59e0b",    // vàng cam
  high: "#ef4444",      // đỏ
  critical: "#7f1d1d",  // đỏ đậm
};
```

---

## 3. Luồng 2 — Real-time Prediction

**Mô tả:** User click vào 1 quốc gia → hệ thống gọi ML model để predict
số ca + risk level cho tuần hiện tại (real-time, không query DB).

### 3.1 Trigger

```
WorldMap → click country → navigate("/country/{iso3}")
DiseaseDetailPage → useEffect → POST /api/v1/infer
```

### 3.2 Frontend: API call

**File:** `frontend/src/api/infer.ts`

```typescript
export async function postPredict(payload: InferRequest): Promise<InferResponse> {
  const { data } = await axiosInstance.post("/infer", payload);
  return data;
}

interface InferRequest {
  iso3: string;
  disease: "flu" | "dengue";
  iso_year: number;
  iso_week: number;
}
```

### 3.3 Backend: Router + Inference Engine

**File:** `backend/app/api/v1/endpoints/infer.py`

```python
@router.post("/infer", response_model=InferResponse)
async def infer(payload: InferRequest, db: Session = Depends(get_db)):
    return await ml_engine.predict(db, payload)
```

**File:** `backend/app/services/ml_engine.py`

```python
async def predict(db, payload):
    # 1. Kiểm tra cache trong predictions table
    # 2. Fetch AR lags từ disease_cases: lag1w, lag2w, lag4w
    # 3. Fetch weather từ OpenWeatherMap API (hoặc ERA5 fallback)
    # 4. Build feature vector (13 features flu / 15 features dengue)
    # 5. model.predict(X) → log1p space
    # 6. expm1() để convert về case count
    # 7. Lookup risk_thresholds(iso3) → classify Low/Med/High
    # 8. Return {predicted_cases, risk_level, prob_high, features_used}
```

**Model được load 1 lần khi startup:**
```python
# backend/app/main.py — lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: load pkl vào memory
    ml_engine.load_models(settings.MODELS_DIR)
    yield
    # SHUTDOWN: cleanup
```

---

## 4. Luồng 3 — Country Detail / History

**Mô tả:** Trang `/country/{iso3}` hiển thị lịch sử dịch bệnh + forecast theo tuần.

### 4.1 API

```
GET /api/v1/history/{disease}/{iso3}?start_year=2020&end_year=2026
```

### 4.2 Backend flow

```
endpoints/analytics.py
    → services/prediction_service.py
        → crud/predictions.py
            SELECT predictions WHERE iso3=? AND disease=? ORDER BY iso_year, iso_week
            JOIN disease_cases WHERE iso3=? (actual reported cases)
        → trả list HistoryPoint: {iso_year, iso_week, actual_cases, predicted_cases, risk_level}
```

### 4.3 Frontend render

```
DiseaseDetailPage.tsx
    ├── useQuery("history", fetchHistory)
    └── Recharts LineChart
          ├── Line: actual_cases (xanh)
          ├── Line: predicted_cases (cam, dashed)
          └── ReferenceArea: risk band (tô màu nền theo risk_level)
```

---

## 5. Luồng 4 — Analytics Page

**Mô tả:** Trang `/analytics` — aggregate statistics toàn cầu, top countries, trend by region.

### 5.1 API

```
GET /api/v1/analytics/summary?disease={disease}&year={year}
GET /api/v1/analytics/top-countries?disease={disease}&year={year}&week={week}&limit=10
```

### 5.2 Backend

**File:** `backend/app/api/v1/endpoints/analytics.py`

Truy vấn materialized view `mv_latest_predictions` thay vì query trực tiếp bảng predictions
(nhanh hơn vì MV đã pre-aggregate, ~50ms vs ~500ms full scan).

---

## 6. State Management — Zustand store

**File:** `frontend/src/store/uiStore.ts`

Zustand là state manager nhẹ, không cần Provider như Redux.

```typescript
interface UIState {
  // Filter state — ảnh hưởng tất cả API calls
  disease: DiseaseId;          // "flu" | "dengue"
  year: number;
  week: number;
  regions: string[];           // WHO region filter: ["AMRO", "EURO", ...]

  // Navigation state
  selectedIso3: string | null; // Quốc gia đang được chọn

  // Actions
  setDisease: (d: DiseaseId) => void;
  setYear: (y: number) => void;
  setWeek: (w: number) => void;
  toggleRegion: (r: string) => void;
  setSelectedIso3: (iso3: string | null) => void;
}
```

**Cách dùng trong component:**
```typescript
// Chỉ subscribe field cần thiết — tránh re-render thừa
const disease = useUIStore(state => state.disease);
const setDisease = useUIStore(state => state.setDisease);
```

**Cách React Query phụ thuộc vào store:**
```typescript
// hooks/useRiskMap.ts
const { disease, year, week } = useUIStore();

return useQuery({
  queryKey: ["riskMap", disease, year, week],  // ← thay đổi → auto re-fetch
  queryFn: () => fetchRiskMap(disease, year, week),
  staleTime: 5 * 60 * 1000,  // cache 5 phút
});
```

---

## 7. Sơ đồ tổng hợp

```
USER ACTION
    │
    ▼
[uiStore.ts] — Zustand state
(disease, year, week, regions, selectedIso3)
    │
    │ subscribe (auto re-fetch khi state đổi)
    ▼
[hooks/useRiskMap.ts] — React Query
    │  queryKey: [disease, year, week]
    │  staleTime: 5min
    │
    ▼
[api/infer.ts | api/countries.ts] — Axios
    │  GET /api/v1/risk-map/{disease}?year=&week=
    │  Authorization header (nếu có)
    │
    ▼  HTTP JSON
[backend/api/v1/endpoints/risk.py] — FastAPI Router
    │  validate params (Pydantic)
    │
    ▼
[backend/services/risk_service.py] — Business Logic
    │  tổng hợp crud + tính risk_level
    │
    ▼
[backend/crud/predictions.py] — SQL Query
    │  SELECT ... FROM predictions JOIN countries
    │
    ▼
[PostgreSQL 15]
    predictions (PARTITION BY iso_year)
    risk_thresholds (q33, q67 per iso3)
    countries (lat, lon, who_region)
    │
    ◄─── kết quả ORM objects ──────────────
    │
[backend/schemas/prediction.py] — Pydantic serialize
    │  ORM object → dict → JSON bytes
    │
    ▼  HTTP 200 JSON
[frontend/types/api.ts] — TypeScript types
    │  parse JSON → typed RiskMapResponse
    │
    ▼
[pages/HomePage.tsx]
    ├── WorldMap ← tô màu 197 quốc gia
    ├── RiskMapSidebar ← filter + stats
    └── AlertsSidebar ← high-risk list


LUỒNG REAL-TIME (khác):
User click country → navigate /country/{iso3}
    → DiseaseDetailPage
    → POST /api/v1/infer {iso3, disease, year, week}
    → ml_engine.py: fetch AR lags + weather → model.predict()
    → InferResponse {predicted_cases, risk_level, prob_high}
    → Recharts LineChart + risk badge
```

---

## Checklist đọc code theo thứ tự

Khi muốn trace một tính năng từ đầu đến cuối, đọc theo thứ tự:

1. **Hiểu endpoint:** `backend/app/api/v1/endpoints/*.py` — URL pattern, params, response type
2. **Hiểu business logic:** `backend/app/services/*.py` — logic tổng hợp là gì
3. **Hiểu DB query:** `backend/app/crud/*.py` — SELECT gì, JOIN gì
4. **Hiểu DB schema:** `backend/app/models/*.py` — table structure, relationships
5. **Hiểu contract:** `backend/app/schemas/*.py` ↔ `frontend/src/types/api.ts` — phải khớp nhau
6. **Hiểu FE fetch:** `frontend/src/hooks/*.ts` + `frontend/src/api/*.ts` — gọi như thế nào
7. **Hiểu FE state:** `frontend/src/store/uiStore.ts` — state nào trigger re-fetch
8. **Hiểu FE render:** `frontend/src/pages/*.tsx` → `frontend/src/components/**/*.tsx`
