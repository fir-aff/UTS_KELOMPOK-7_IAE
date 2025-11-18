# Integrated Application Environment for Microservices 🍔

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg?style=flat-square&logo=python&logoColor=white&style=for-the-badge&color=3776AB&style=for-the-badge&margin-right:8px)](https://www.python.org/)
[![HTML](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white&style=for-the-badge&margin-right:8px)](https://www.w3schools.com/html/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black&style=for-the-badge&margin-right:8px)](https://www.javascript.com/)
[![CSS](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white&style=for-the-badge&margin-right:8px)](https://www.w3schools.com/css/)

This repository houses a microservices-based application environment, designed to demonstrate inter-service communication and collaboration. The project is built with Python and likely utilizes frameworks for API development and data management. It includes an API gateway and several core services such as user management, restaurant listings, order processing, and driver services.

## Fitur Utama ✨

*   *API Gateway 🚪*: Centralized entry point for all client requests, routing them to the appropriate microservices.
*   *Service Decomposition 🧩*: Well-defined microservices for User, Restaurant, Order, and Driver management, promoting modularity and scalability.
*   *Data Persistence 💾*: Likely uses a database (e.g., SQLite for User Service) to store and retrieve data.
*   *Inter-Service Communication 📡*: Demonstrates how different microservices interact with each other, likely through HTTP requests.
*   *Scalability & Maintainability ⬆*: Microservices architecture facilitates independent scaling and maintenance of individual components.

## Tech Stack 🛠

*   *Programming Language*: Python 🐍
*   *API Framework*: Likely Flask or FastAPI for building REST APIs.
*   *Database*: SQLite (for User Service), potentially others for different services.
*   *Frontend*: HTML, CSS, and JavaScript for any user interface components.
*   *Other*: API Gateway (implementation details not specified but a key component).

## Instalasi & Menjalankan 🚀

1.  Clone repositori:

    bash
    git clone https://github.com/fir-aff/UTS_KELOMPOK-7_IAE
    

2.  Masuk ke direktori:

    bash
    cd UTS_KELOMPOK-7_IAE
    

3.  Install dependensi (untuk setiap service):

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
    

4.  Jalankan proyek (untuk setiap service - perlu menjalankan beberapa terminal):

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
    

## Cara Berkontribusi 🤝

1.  Fork repositori ini.
2.  Buat branch untuk fitur baru Anda: git checkout -b fitur-baru
3.  Lakukan commit perubahan Anda: git commit -am 'Tambahkan fitur baru'
4.  Push ke branch: git push origin fitur-baru
5.  Buat Pull Request.

## Lisensi 📄

Tidak ada lisensi yang ditentukan.