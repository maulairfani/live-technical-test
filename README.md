# 🎬 Content Recommendation System

Sistem rekomendasi konten berbasis FastAPI yang menyediakan rekomendasi **global (trending)** dan **personal (user-based collaborative filtering)**.

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Tech Stack](#-tech-stack)
- [Struktur Project](#-struktur-project)
- [Instalasi](#-instalasi)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [API Endpoints](#-api-endpoints)
- [Pseudocode Services](#-pseudocode-services)
  - [Global Recommendation Service](#1-global-recommendation-service)
  - [Personal Recommendation Service](#2-personal-recommendation-service)

---

## ✨ Fitur

- **Global Recommendations**: Rekomendasi konten trending berdasarkan agregasi interaksi pengguna
- **Personal Recommendations**: Rekomendasi personal menggunakan User-Based Collaborative Filtering
- **Hybrid Similarity**: Kombinasi similarity berbasis interaksi dan demografi (usia)
- **Genre Boosting**: Preferensi genre favorit user diprioritaskan
- **Cold Start Handling**: Fallback ke global recommendations untuk user baru

---

## 🛠 Tech Stack

| Kategori | Teknologi |
|----------|-----------|
| **Web Framework** | FastAPI >= 0.109.0 |
| **ASGI Server** | Uvicorn >= 0.27.0 |
| **Data Processing** | Pandas >= 2.0.0, NumPy >= 1.24.0 |
| **Machine Learning** | Scikit-learn >= 1.3.0 |
| **Validation** | Pydantic >= 2.0.0 |

---

## 📁 Struktur Project

```
live_test/
├── data/
│   ├── data_joined.csv      # Data gabungan user-item-events
│   ├── events.csv           # Log interaksi user
│   ├── items.csv            # Katalog konten
│   └── users.csv            # Data user
├── src/
│   ├── exceptions.py        # Custom exceptions
│   ├── main.py              # FastAPI app entry point
│   ├── repositories/
│   │   └── content_repo.py  # Repository akses data konten
│   ├── router/
│   │   ├── api.py           # Router aggregator
│   │   └── v1/
│   │       └── recommendation.py  # Endpoints rekomendasi
│   ├── schemas/
│   │   └── content.py       # Schema Content
│   └── services/
│       ├── global_recommendation_service/
│       │   ├── schema.py    # Request/Response schemas
│       │   └── service.py   # Logika trending
│       └── personal_recommendation_service/
│           ├── schema.py    # Request/Response schemas
│           └── service.py   # Logika collaborative filtering
├── tests/
├── requirements.txt
└── README.md
```

---

## 🚀 Instalasi

```bash
# Clone repository
git clone <repository-url>
cd live_test

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Menjalankan Aplikasi

```bash
# Development mode (auto-reload)
uvicorn src.main:app --reload

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Akses dokumentasi API di: `http://localhost:8000/docs`

---

## 🔌 API Endpoints

### Health Check
```
GET /health
Response: { "status": "ok" }
```

### Popular/Trending Recommendations
```
POST /v1/popular
```
**Request Body:**
```json
{
  "top_k": 10,
  "date": "2024-01-15T00:00:00",
  "content_types": ["series", "movie", "microdrama", "tv"],
  "lookback_days": 30
}
```

### Personal Recommendations
```
POST /v1/recommendations
```
**Request Body:**
```json
{
  "user_id": "user_123",
  "top_k": 10,
  "content_types": ["series", "movie", "microdrama", "tv"],
  "top_p": 10
}
```

---

## 📝 Pseudocode Services

### 1. Global Recommendation Service

Service ini menghasilkan rekomendasi trending berdasarkan agregasi skor interaksi user dalam periode waktu tertentu.

```
CLASS GlobalRecommendationService:
    
    FUNCTION __init__(data_path):
        # 1. Load data interaksi dari CSV
        data = LOAD_CSV(data_path)
        
        # 2. Parse timestamp
        data.timestamp = CONVERT_TO_DATETIME(data.timestamp)
        
        # 3. Hitung quality score untuk setiap interaksi
        FOR EACH row IN data:
            row.rating = calculate_quality_score(row)
    
    
    FUNCTION calculate_quality_score(row) -> float:
        """
        Bobot interaksi berdasarkan event type:
        - Like/Complete/Save = 5 poin (high engagement)
        - Play > 60 detik     = 3 poin (medium engagement)
        - Lainnya             = 1 poin (low engagement)
        """
        IF row.event_type IN ["like", "complete", "save"]:
            RETURN 5.0
        ELSE IF row.event_type == "play" AND row.watch_seconds > 60:
            RETURN 3.0
        ELSE:
            RETURN 1.0
    
    
    FUNCTION recommend_popular(request) -> Response:
        """
        Algoritma Trending/Popular Recommendations
        """
        
        # STEP 1: Set default date ke tanggal terbaru jika tidak ada
        IF request.date IS NULL:
            request.date = MAX(data.timestamp)
        
        # STEP 2: Filter data berdasarkan lookback period
        cutoff_date = request.date - lookback_days
        recent_data = FILTER data WHERE timestamp >= cutoff_date
        
        IF recent_data IS EMPTY:
            RAISE NoRecommendationsAvailableException
        
        # STEP 3: Filter berdasarkan content types yang diminta
        recent_data = FILTER recent_data WHERE content_type IN request.content_types
        
        IF recent_data IS EMPTY:
            RAISE NoRecommendationsAvailableException
        
        # STEP 4: Agregasi - Hitung total score per item
        #         Formula: Score(item) = SUM(quality_score) untuk semua interaksi
        trending_scores = GROUP recent_data BY item_id
                          CALCULATE SUM(rating)
        
        # STEP 5: Sort descending dan ambil Top K
        top_items = SORT trending_scores BY rating DESC
                    TAKE TOP request.top_k
        
        # STEP 6: Format output dengan detail konten
        results = []
        FOR EACH item IN top_items:
            content = content_repo.get_content_by_id(item.item_id)
            IF content EXISTS:
                content.score = item.total_score
                results.APPEND(content)
        
        RETURN GlobalRecommendationResponse(top_k, results)
```

**Kompleksitas Algoritma:**
- Time: O(n log n) dimana n = jumlah interaksi dalam lookback period
- Space: O(m) dimana m = jumlah item unik

---

### 2. Personal Recommendation Service

Service ini menghasilkan rekomendasi personal menggunakan **User-Based Collaborative Filtering** dengan kombinasi similarity berbasis interaksi dan demografi.

```
CLASS PersonalRecommendationService:
    
    FUNCTION __init__(data_path):
        # 1. Load data interaksi
        data = LOAD_CSV(data_path)
        
        # 2. Hitung implicit rating untuk setiap interaksi
        FOR EACH row IN data:
            row.rating = calculate_implicit_rating(row)
        
        # 3. Clean data - ambil rating maksimum per user-item pair
        data_clean = GROUP data BY [user_id, item_id, age, content_type, genre]
                     CALCULATE MAX(rating)
        
        # 4. Hitung genre favorit untuk setiap user
        user_top_genre = {}
        FOR EACH user IN UNIQUE(data_clean.user_id):
            user_items = FILTER data_clean WHERE user_id == user
            genre_scores = GROUP user_items BY genre CALCULATE SUM(rating)
            user_top_genre[user] = GENRE WITH MAX(score)
        
        # 5. Buat User-Item Matrix (sparse matrix)
        matrix = PIVOT data_clean
                 INDEX = user_id
                 COLUMNS = item_id
                 VALUES = rating
                 FILL_NA = 0
        
        # 6. Hitung Similarity Matrix berbasis interaksi (Cosine Similarity)
        sim_interaction = COSINE_SIMILARITY(matrix)
        
        # 7. Hitung Similarity Matrix berbasis umur
        #    Formula: sim_age = 1 / (1 + |age_i - age_j| / 10)
        age_diff = ABS(ages - ages.T)
        sim_age = 1 / (1 + age_diff / 10)
        
        # 8. Combine kedua similarity dengan bobot
        #    70% interaksi + 30% demografi
        similarity_matrix = (0.7 * sim_interaction) + (0.3 * sim_age)
    
    
    FUNCTION calculate_implicit_rating(row) -> float:
        """
        Sama dengan GlobalRecommendationService
        """
        IF row.event_type IN ["like", "complete", "save"]:
            RETURN 5.0
        ELSE IF row.event_type == "play" AND row.watch_seconds > 60:
            RETURN 3.0
        ELSE:
            RETURN 1.0
    
    
    FUNCTION recommend_for_user(request) -> Response:
        """
        Algoritma User-Based Collaborative Filtering
        dengan Genre Boosting
        """
        user_id = request.user_id
        
        # STEP 1: Cold Start Check - User baru fallback ke global
        IF user_id NOT IN known_users:
            LOG "User not found, using fallback"
            global_service = GlobalRecommendationService()
            global_result = global_service.recommend_popular(
                top_k = request.top_k,
                content_types = request.content_types
            )
            RETURN PersonalRecommendationResponse(
                user_id, top_k, global_result.items, fallback_used=True
            )
        
        # STEP 2: Ambil similarity scores untuk target user
        user_idx = user_to_idx[user_id]
        sim_scores = similarity_matrix[user_idx]
        
        # STEP 3: Cari Top P neighbors (user paling mirip)
        #         Exclude user itu sendiri
        neighbor_indices = ARGSORT(sim_scores) DESCENDING
                           TAKE TOP request.top_p
                           EXCLUDE self
        
        IF neighbor_indices IS EMPTY:
            RAISE SimilarUsersNotFoundException
        
        # STEP 4: Ambil item yang sudah ditonton oleh target user
        watched_items = GET items WHERE user_id == target_user
        
        # STEP 5: Ambil genre favorit target user
        fav_genre = user_top_genre[user_id]
        
        # STEP 6: Kumpulkan kandidat item dari neighbors
        candidates = {}
        
        FOR EACH neighbor_idx IN neighbor_indices:
            similarity = sim_scores[neighbor_idx]
            neighbor_ratings = matrix[neighbor_idx]
            
            # Ambil item yang di-like oleh neighbor (rating > 0)
            liked_items = GET items WHERE neighbor_ratings > 0
            
            FOR EACH item_id IN liked_items:
                # Skip jika sudah ditonton
                IF item_id IN watched_items:
                    CONTINUE
                
                # Skip jika content type tidak sesuai
                content = content_repo.get_content_by_id(item_id)
                IF content.content_type NOT IN request.content_types:
                    CONTINUE
                
                # Hitung score: similarity × rating
                rating_value = neighbor_ratings[item_id]
                score = similarity * rating_value
                
                # Genre Boosting: +20% jika genre favorit
                IF content.genre == fav_genre:
                    score = score * 1.2
                
                # Akumulasikan score (bisa dari multiple neighbors)
                candidates[item_id] += score
        
        IF candidates IS EMPTY:
            RAISE NoRecommendationsAvailableException
        
        # STEP 7: Sort kandidat dan ambil Top K
        sorted_candidates = SORT candidates BY score DESC
        top_items = TAKE TOP request.top_k FROM sorted_candidates
        
        # STEP 8: Format output
        results = []
        FOR EACH (item_id, score) IN top_items:
            content = content_repo.get_content_by_id(item_id)
            IF content EXISTS:
                content.score = score
                results.APPEND(content)
        
        RETURN PersonalRecommendationResponse(
            user_id, top_k, results, fallback_used=False
        )
```

**Kompleksitas Algoritma:**
- **Preprocessing** (sekali saat init):
  - Time: O(n²) untuk cosine similarity, dimana n = jumlah user
  - Space: O(n² + n×m) untuk similarity matrix dan user-item matrix
- **Inference** (per request):
  - Time: O(P × I) dimana P = top_p neighbors, I = rata-rata item per neighbor
  - Space: O(C) dimana C = jumlah kandidat item

---

## 📊 Formula Yang Digunakan

### Implicit Rating (Quality Score)
```
rating = {
    5.0  jika event_type ∈ {like, complete, save}
    3.0  jika event_type = play ∧ watch_seconds > 60
    1.0  lainnya
}
```

### Age-Based Similarity
```
sim_age(i, j) = 1 / (1 + |age_i - age_j| / 10)
```

### Hybrid Similarity
```
sim_hybrid(i, j) = 0.7 × sim_interaction(i, j) + 0.3 × sim_age(i, j)
```

### Collaborative Filtering Score
```
score(user, item) = Σ (sim(user, neighbor) × rating(neighbor, item) × genre_boost)

genre_boost = 1.2 jika item.genre = user.fav_genre, else 1.0
```

---

## ⚠️ Exception Handling

| Exception | Status Code | Trigger |
|-----------|-------------|---------|
| `DataLoadException` | 500 | Gagal load CSV |
| `UserNotFoundException` | 404 | User tidak ditemukan |
| `NoRecommendationsAvailableException` | 404 | Tidak ada rekomendasi |
| `SimilarUsersNotFoundException` | 404 | Tidak ada user mirip |
| `InvalidContentTypeException` | 400 | Content type invalid |
