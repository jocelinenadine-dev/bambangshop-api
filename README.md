# BambangShop RESTful Catalog API

A complete, working reference implementation of a RESTful API built with **Django 5.2** and **Django REST Framework (DRF)** for Platform-Based Programming (PBP).

## Project Overview

- **Framework:** Django 5.2.18
- **REST Framework:** Django REST Framework 3.18.3
- **API Documentation:** OpenAPI 3.0 via `drf-spectacular` 0.30.0 with Swagger UI and Redoc
- **Filtering:** `django-filter` 26.2 and built-in Search/Ordering filters
- **Authentication:** TokenAuthentication and SessionAuthentication
- **Permissions:** Custom object-level authorization (`IsOwnerOrReadOnly`)

## Project Structure

```text
bambangshop_api/
├── manage.py
├── README.md
├── bambangshop_api/
│   ├── __init__.py
│   ├── settings.py       # DRF & Spectacular configuration
│   ├── urls.py           # Top-level URL routing & Swagger UI
│   └── wsgi.py
└── catalog/
    ├── __init__.py
    ├── apps.py
    ├── models.py         # Category and Product models
    ├── serializers.py    # Serializers with field-level validation
    ├── permissions.py    # Custom IsOwnerOrReadOnly permission
    ├── views.py          # ModelViewSets with custom actions
    ├── urls.py           # DefaultRouter wiring
    └── tests.py          # Automated test suite
```

## Getting Started

### 1. Environment Setup

Activate the virtual environment:

```bash
# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Database Migrations

Apply the database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Running Automated Tests

Run the test suite:

```bash
python manage.py test
```

### 4. Running the Development Server

Start the local server:

```bash
python manage.py runserver
```

Explore the available endpoints:
- **Browsable API Root:** [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/)
- **Interactive Swagger UI:** [http://127.0.0.1:8000/api/docs/swagger/](http://127.0.0.1:8000/api/docs/swagger/)
- **Redoc Documentation:** [http://127.0.0.1:8000/api/docs/redoc/](http://127.0.0.1:8000/api/docs/redoc/)
- **Token Auth Endpoint:** [http://127.0.0.1:8000/api/v1/auth/token/](http://127.0.0.1:8000/api/v1/auth/token/)

---

## Reflections

### Reflection Practice-1

1. *In ProductSerializer, why are owner and category_name configured with read_only=True via ReadOnlyField? What security vulnerability occurs if owner is writable?*
   - Di `ProductSerializer`, field `owner` diset sebagai `ReadOnlyField(source='owner.username')` karena penentuan pemilik produk harus dilakukan di sisi backend berdasarkan user yang sedang login (`request.user`) melalui `serializer.save(owner=request.user)`. Nilai `owner` tidak boleh dimanipulasi melalui request body saat POST atau PUT. Sedangkan `category_name` diset sebagai `ReadOnlyField(source='category.name')` hanya untuk mempermudah frontend membaca nama kategori secara langsung di response JSON tanpa perlu request tambahan, sementara input kategori saat create/update tetap menggunakan foreign key `category` (berupa ID).
   - Jika field `owner` dibiarkan writable, sistem rentan terhadap celah keamanan seperti **Insecure Direct Object Reference (IDOR)** dan **privilege escalation**. User bisa saja menyelipkan ID atau username milik akun lain (termasuk admin) ke dalam payload request. Hal ini memungkinkan seseorang membuat produk atas nama orang lain atau memanipulasi kepemilikan produk. Selain itu, permission check `IsOwnerOrReadOnly` yang bergantung pada perbandingan `obj.owner == request.user` juga bisa ditembus karena data kepemilikan produk di database sudah dimanipulasi sejak awal.

2. *Explain the execution order of field-level validation (validate_price) versus object-level validation (validate). When would you choose one over the other?*
   - **Urutan eksekusinya di DRF:**
     1. **Field-level validation (`validate_<field_name>`)** dijalankan terlebih dahulu untuk setiap field secara individual (misalnya `validate_price` dan `validate_stock`). Fungsi ini memeriksa nilai dari satu field tertentu setelah tipe data dasarnya dicek, lalu mengembalikan nilai tersebut jika valid.
     2. **Object-level validation (`validate`)** dijalankan setelah seluruh field-level validation selesai dan berhasil. Fungsi ini menerima dictionary `attrs` yang berisi seluruh data field yang sudah lolos validasi tahap awal.
   - **Kapan memilih salah satunya:**
     - Gunakan **field-level validation** jika aturan validasi hanya bergantung pada satu atribut saja, contohnya memastikan harga bernilai lebih dari nol (`price > 0`) atau stok tidak bernilai negatif (`stock >= 0`).
     - Gunakan **object-level validation** jika aturan validasi memerlukan perbandingan atau ketergantungan antar beberapa field sekaligus (*cross-field validation*). Contohnya memastikan harga diskon tidak lebih besar dari harga asli (`discount_price < price`), atau memastikan tanggal selesai tidak mendahului tanggal mulai (`end_date > start_date`).

### Reflection Practice-2

1. *When an anonymous user attempts to issue an HTTP DELETE request to `/api/v1/products/1/`, which permission check fails first? Explain the step-by-step evaluation between IsAuthenticatedOrReadOnly and IsOwnerOrReadOnly.*
   - Pengecekan yang gagal pertama kali adalah **`IsAuthenticatedOrReadOnly`** pada tahap view-level permission (`has_permission`). Pengecekan `IsOwnerOrReadOnly` tidak sempat dijalankan sama sekali.
   - **Alur evaluasinya:**
     1. DRF memeriksa permission class yang terdaftar pada ViewSet secara berurutan: `[permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]`.
     2. Sebelum mengambil data dari database, DRF mengevaluasi method `has_permission` pada kelas pertama (`IsAuthenticatedOrReadOnly`).
     3. Karena request menggunakan method `DELETE` (yang bukan termasuk safe method seperti `GET`, `HEAD`, atau `OPTIONS`), DRF memeriksa apakah user sudah login (`request.user.is_authenticated`).
     4. Karena request dikirim oleh user yang belum login (anonymous user), `has_permission` mengembalikan nilai `False`.
     5. DRF langsung menghentikan proses eksekusi (*short-circuit*) dan mengembalikan response error HTTP 401 Unauthorized (atau 403 Forbidden).
     6. Karena proses sudah dihentikan, pengambilan objek dari database (`get_object()`) dibatalkan, sehingga method `has_object_permission` pada `IsOwnerOrReadOnly` tidak pernah dieksekusi.

2. *What actions does DefaultRouter generate automatically for ProductViewSet? List each URL path, supported HTTP method, and corresponding action method.*
   - Untuk pendaftaran `router.register(r'products', ProductViewSet, basename='product')`, `DefaultRouter` secara otomatis membuat rute-rute berikut:

     | URL Path | HTTP Method | Action | Keterangan |
     | :--- | :--- | :--- | :--- |
     | `/api/v1/` | `GET` | `api-root` | Menampilkan index hyperlink ke seluruh endpoint yang tersedia |
     | `/api/v1/products/` | `GET` | `list` | Mengambil daftar produk (dengan filter, search, dan pagination) |
     | `/api/v1/products/` | `POST` | `create` | Menambahkan produk baru |
     | `/api/v1/products/{pk}/` | `GET` | `retrieve` | Mengambil detail satu produk berdasarkan ID |
     | `/api/v1/products/{pk}/` | `PUT` | `update` | Mengubah seluruh data produk berdasarkan ID |
     | `/api/v1/products/{pk}/` | `PATCH` | `partial_update` | Mengubah sebagian data produk berdasarkan ID |
     | `/api/v1/products/{pk}/` | `DELETE` | `destroy` | Menghapus produk dari database berdasarkan ID |

   - `DefaultRouter` juga menyediakan format suffix opsional seperti `.json` (misalnya `/api/v1/products.json`).

### Reflection Practice-3

1. *How does drf-spectacular automatically discover request and response schemas from your ViewSet and ModelSerializer classes?*
   - `drf-spectacular` membuat skema OpenAPI 3.0 secara otomatis melalui introspeksi kode secara dinamis:
     - **Mendeteksi endpoint dan action:** Menelusuri routing URL untuk memetakan method HTTP ke action ViewSet (`list`, `create`, `retrieve`, dll).
     - **Menganalisis serializer:** Memeriksa field pada `ProductSerializer` dan memetakan tipe data Django/DRF ke tipe skema OpenAPI (misalnya `CharField` menjadi `string`, `IntegerField` menjadi `integer`, dan `DecimalField` menjadi `number`). Properti seperti `read_only=True`, `max_length`, dan `required` juga langsung dicatat ke dalam skema.
     - **Mendeteksi filter dan pencarian:** Membaca konfigurasi `filter_backends` untuk menyisipkan parameter query (seperti `?category=`, `?search=`, dan `?ordering=`) pada dokumentasi endpoint list.
     - **Membaca model:** Menginspeksi `queryset` untuk menentukan tipe parameter ID pada URL path (`pk`).
     - **Membaca decorator `@extend_schema`:** Jika ada decorator `@extend_schema`, spectacular akan menggunakan informasi tambahan tersebut untuk melengkapi deskripsi atau contoh payload.

2. *How does providing an interactive Swagger UI interface accelerate collaboration between backend engineers and frontend/mobile developers?*
   - Swagger UI mempermudah kolaborasi karena:
     - **Dokumentasi selalu sinkron:** Karena dibuat langsung dari kode backend, dokumentasi tidak akan ketinggalan zaman saat ada perubahan endpoint atau field.
     - **Bisa langsung diuji (Try It Out):** Developer frontend atau mobile bisa langsung mencoba request API lewat browser, memasukkan token auth, melihat format JSON yang dikirim, dan mengecek format response tanpa harus membuka Postman.
     - **Kontrak data yang jelas:** Tipe data tiap field, batasan validasi, dan status wajib/opsional terlihat jelas, sehingga meminimalkan salah interpretasi data saat membuat model di Flutter atau frontend web.
     - **Mendukung pengerjaan paralel:** Tim frontend bisa langsung membuat mock data atau merancang tampilan berdasarkan spesifikasi API yang sudah tertera di Swagger, meskipun backend masih dalam proses pengembangan.
