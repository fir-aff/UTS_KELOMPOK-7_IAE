# Integrated Application Environment for Microservices 🍔

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg?style=flat-square&logo=python&logoColor=white&style=for-the-badge&color=3776AB&style=for-the-badge&margin-right:8px)](https://www.python.org/)
[![HTML](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white&style=for-the-badge&margin-right:8px)](https://www.w3schools.com/html/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black&style=for-the-badge&margin-right:8px)](https://www.javascript.com/)
[![CSS](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white&style=for-the-badge&margin-right:8px)](https://www.w3schools.com/css/)

This repository houses a microservices-based application environment, designed to demonstrate inter-service communication and collaboration. The project is built with Python and likely utilizes frameworks for API development and data management. It includes an API gateway and several core services such as user management, restaurant listings, order processing, and driver services.

## Anggota Kelompok & Peran 👥

Berikut adalah pembagian tugas dan tanggung jawab untuk setiap layanan dalam sistem ini:

| Nama Anggota | NIM | Peran / Tanggung Jawab | Layanan (Service) |
| :--- | :--- | :--- | :--- |
| **MUHAMMAD DEVARA** | 102022300345 | **Project Manager & Architect** | `driver-service` & Arsitektur Umum |
| **FIRMAN ZUHDI AFFANDI** | 102022300382 | **Backend Developer** | `order-service` (Logic Inti) |
| **FARIS KHANSA FAYZI** | 102022300415 | **Backend & Gateway Lead** | `user-service` & `api-gateway` |
| **ZHAFRAN AHMAD ZAIDAN** | 102022300437 | **Frontend & Backend Dev** | `restaurant-service` & Frontend Integration |

## Fitur Utama ✨

*   *API Gateway 🚪*: Centralized entry point for all client requests, routing them to the appropriate microservices.
*   *Service Decomposition 🧩*: Well-defined microservices for User, Restaurant, Order, and Driver management, promoting modularity and scalability.
*   *Data Persistence 💾*: Likely uses a database (e.g., SQLite for User Service) to store and retrieve data.
*   *Inter-Service Communication 📡*: Demonstrates how different microservices interact with each other, likely through HTTP requests.
*   *Scalability & Maintainability ⬆*: Microservices architecture facilitates independent scaling and maintenance of individual components.

## Arsitektur Sistem 🏗️

Sistem ini menggunakan pola arsitektur Microservices dengan Database per Service. Klien tidak mengakses layanan secara langsung, melainkan melalui **API Gateway**.

**Alur Data:** `Client (Frontend)` → `API Gateway` → `Microservices` → `Database`

```mermaid
graph TD
    subgraph Client Side
        User["Frontend User<br/>(index.html)"]
        Admin["Frontend Admin<br/>(admin.html)"]
    end

    subgraph Gateway Layer
        Gateway["API Gateway<br/>Port: 5000"]
    end

    subgraph Service Layer
        US["User Service<br/>Port: 5001"]
        RS["Restaurant Service<br/>Port: 5002"]
        OS["Order Service<br/>Port: 5003"]
        DS["Driver Service<br/>Port: 5004"]
    end

    subgraph Data Layer
        DB1[("MySQL:<br/>user_service_db")]
        DB2[("MySQL:<br/>restaurant_service_db")]
        DB3[("MySQL:<br/>order_service_db")]
        DB4[("MySQL:<br/>driver_service_db")]
    end

    %% Flow Request
    User --> Gateway
    Admin --> Gateway
    
    Gateway --> US
    Gateway --> RS
    Gateway --> OS
    Gateway --> DS

    %% Inter-service Communication
    OS -.->|Validasi User| US
    OS -.->|Validasi Menu| RS
    OS -.->|Request Driver| DS
    DS -.->|Update Status| OS

    %% Database Connection
    US --- DB1
    RS --- DB2
    OS --- DB3
    DS --- DB4

## Tech Stack 🛠

*   *Programming Language*: Python 🐍
*   *API Framework*: Likely Flask or FastAPI for building REST APIs.
*   *Database*: SQLite (for User Service), potentially others for different services.
*   *Frontend*: HTML, CSS, and JavaScript for any user interface components.
*   *Other*: API Gateway (implementation details not specified but a key component).
*   *Tools*: Postman (Testing), Git

## Instalasi & Menjalankan 🚀

1. Persiapan Database (MySQL)

    Pastikan MySQL Server (XAMPP/Laragon) sudah berjalan. Buat 4 database kosong berikut:

    * user_service_db
    * restaurant_service_db
    * order_service_db
    * driver_service_db

2.  Clone repositori:

    bash
    git clone https://github.com/fir-aff/UTS_KELOMPOK-7_IAE
    

3.  Masuk ke direktori:

    bash
    cd UTS_KELOMPOK-7_IAE
    

4.  Install dependensi (untuk setiap service):

    bash
    cd api-gateway
    pip install -r requirements.txt
    cd ..

    cd driver-service
    pip install -r requirements.txt
    cd ..

    cd order-service
    pip install -r requirements.txt
    cd ..

    cd restaurant-service
    pip install -r requirements.txt
    cd ..

    cd user-service
    pip install -r requirements.txt
    cd ..
    

5.  Jalankan proyek (untuk setiap service - perlu menjalankan beberapa terminal):

    bash
    cd api-gateway
    .\venv\Scripts\activate
    python app.py
    cd ..

    cd driver-service
    .\venv\Scripts\activate
    python app.py
    cd ..

    cd order-service
    .\venv\Scripts\activate
    python app.py
    cd ..

    cd restaurant-service
    .\venv\Scripts\activate
    python app.py
    cd ..

    cd user-service
    .\venv\Scripts\activate
    python app.py
    cd ..

6. Menjalankan Frontend
    Buka folder frontend.

    Klik kanan pada file index.html -> Open with Live Server (atau buka langsung di browser).

    Untuk panel admin, buka file admin.html.
    

## Cara Berkontribusi 🤝

1.  Fork repositori ini.
2.  Buat branch untuk fitur baru Anda: git checkout -b fitur-baru
3.  Lakukan commit perubahan Anda: git commit -am 'Tambahkan fitur baru'
4.  Push ke branch: git push origin fitur-baru
5.  Buat Pull Request.

## Ringkasan Endpoint API 🔗

Semua request dari frontend harus melalui API Gateway: http://127.0.0.1:5000/api/{service-name}/{endpoint}.

Berikut adalah endpoint kunci. Dokumentasi lengkap tersedia di folder docs/api/ atau via Postman Collection.

👤 User Service

| Method | Endpoint | Deskripsi | 
| :--- | :--- | :--- |
| **POST** | /users/register | **Mendaftarkan pengguna baru** | 
| **POST** | /auth/login | **Login pengguna (Return User Object)** | 
| **GET** | /users | **Mendapatkan semua list user (Admin)** |

🍽️ Restaurant Service

| Method | Endpoint | Deskripsi | 
| :--- | :--- | :--- |
| **POST** | /users/register | **Mendaftarkan pengguna baru** | 
| **POST** | /auth/login | **Login pengguna (Return User Object)** | 
| **GET** | /users | **Mendapatkan semua list user (Admin)** |

📦 Order Service

| Method | Endpoint | Deskripsi | 
| :--- | :--- | :--- |
| **POST** | /users/register | **Mendaftarkan pengguna baru** | 
| **POST** | /auth/login | **Login pengguna (Return User Object)** | 
| **GET** | /users | **Mendapatkan semua list user (Admin)** |

🛵 Driver Service

| Method | Endpoint | Deskripsi | 
| :--- | :--- | :--- |
| **POST** | /users/register | **Mendaftarkan pengguna baru** | 
| **POST** | /auth/login | **Login pengguna (Return User Object)** | 
| **GET** | /users | **Mendapatkan semua list user (Admin)** |

## Konfigurasi Environment (ENV)

Proyek ini menggunakan konfigurasi langsung pada app.py untuk kemudahan demonstrasi akademik.

Database URI: mysql+pymysql://root:@127.0.0.1/[nama_db]

Default user: root

Default password: (kosong)

Host: 127.0.0.1

Jika password MySQL Anda berbeda, silakan ubah string koneksi di setiap file app.py pada masing-masing service.
