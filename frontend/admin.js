// frontend/admin.js

const GATEWAY_URL = "http://127.0.0.1:5000/api";

// === DEKLARASI Variabel DOM ===
let driverListBody, orderListBody, restoListBody, userListBody;

// Panel Menu (Bawah)
let menuPanel, menuPanelTitle, menuListBody, menuRestoIdInput;

// Modal
let modal, modalTitle, modalFormBody, modalItemId, modalServiceType;


// =========================================================================
//  LOGIKA PANEL MENU (Full-Width Bawah)
// =========================================================================

/**
 * Membuka panel menu dan memuat datanya.
 */
async function openMenuPanel(restoId, restoName) {
    menuPanel.classList.remove("hidden");
    menuPanelTitle.textContent = `Mengelola Menu untuk: ${restoName}`;
    
    // Simpan restoId di hidden input di dalam panel
    menuRestoIdInput.value = restoId; 
    
    await fetchMenuList(restoId);
    // Scroll ke panel menu
    menuPanel.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Memuat daftar menu untuk 1 restoran di dalam panel menu
 */
async function fetchMenuList(restoId) {
    menuListBody.innerHTML = '<tr><td colspan="4">Memuat menu...</td></tr>';
    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants/${restoId}/menu`);
        const menus = await response.json();
        menuListBody.innerHTML = "";
        
        if (!menus || menus.length === 0) {
            menuListBody.innerHTML = '<tr><td colspan="4">Belum ada menu.</td></tr>';
            return;
        }

        menus.forEach(menu => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${menu.id}</td><td>${menu.name}</td><td>Rp${menu.price}</td>`;
            
            const tdAksi = document.createElement("td");
            
            const editBtn = document.createElement("button");
            editBtn.className = "action-btn";
            editBtn.textContent = "Edit";
            editBtn.addEventListener("click", () => prepareMenuEdit(menu));
            tdAksi.appendChild(editBtn);

            const delBtn = document.createElement("button");
            delBtn.className = "action-btn red";
            delBtn.textContent = "Hapus";
            // Panggil fungsi handleDelete generik
            delBtn.addEventListener("click", () => handleDelete('menu', menu.id));
            tdAksi.appendChild(delBtn);
            
            tr.appendChild(tdAksi);
            menuListBody.appendChild(tr);
        });
    } catch (error) {
        menuListBody.innerHTML = `<tr><td colspan="4">Gagal memuat menu: ${error.message}</td></tr>`;
    }
}

/**
 * Menyiapkan form menu untuk mode 'Edit' (memanggil modal)
 */
function prepareMenuEdit(menu) {
    openForm('menu', menu);
}

// =========================================================================
//  LOGIKA CRUD GENERIC (UNTUK DRIVER, USER, RESTO, MENU) via MODAL
// =========================================================================

/**
 * Wrapper function untuk me-refresh daftar menu
 * menggunakan restoId yang tersimpan di hidden input
 */
function refreshCurrentMenuList() {
    const restoId = menuRestoIdInput.value;
    if (restoId) {
        fetchMenuList(restoId);
    } else {
        console.error("Tidak dapat refresh menu, restoId tidak ditemukan.");
    }
}

/**
 * Menutup modal edit
 */
function closeEditModal() {
    if(modal) modal.classList.remove("show");
}

/**
 * Membuka dan menyiapkan modal form untuk Edit (PUT) atau Tambah (POST)
 */
function openForm(serviceType, data) {
    if (!modal) {
        console.error("Modal DOM elements not initialized!");
        return;
    }

    let htmlFields = ''; 
    let title = '';
    const isEdit = data && data.id; // True jika Edit, false jika Tambah

    // 1. Buat field form dan judul berdasarkan serviceType
    switch (serviceType) {
        case 'menu':
            title = isEdit ? 'Edit Menu' : 'Tambah Menu Baru';
            htmlFields = `
                <div class="form-group">
                    <label for="menu-name">Nama Menu</label>
                    <input type="text" id="menu-name" name="name" value="${isEdit ? data.name : ''}" required>
                </div>
                <div class="form-group">
                    <label for="menu-price">Harga (Rp)</label>
                    <input type="number" id="menu-price" name="price" value="${isEdit ? data.price : ''}" required>
                </div>
            `;
            break;

        case 'driver':
            title = isEdit ? 'Edit Driver' : 'Tambah Driver Baru';
            htmlFields = `
                <div class="form-group">
                    <label for="driver-name">Nama Driver</label>
                    <input type="text" id="driver-name" name="name" value="${isEdit ? data.name : ''}" required>
                </div>
            `;
            break;
        
        case 'restaurant':
            title = isEdit ? 'Edit Restoran' : 'Tambah Restoran Baru';
            htmlFields = `
                <div class="form-group">
                    <label for="resto-name">Nama Restoran</label>
                    <input type="text" id="resto-name" name="name" value="${isEdit ? data.name : ''}" required>
                </div>
                <div class="form-group">
                    <label for="resto-address">Alamat Restoran</label>
                    <input type="text" id="resto-address" name="address" value="${isEdit ? data.address : ''}" required>
                </div>
            `;
            break;

        case 'user':
            title = isEdit ? 'Edit User' : 'Tambah User Baru';
            htmlFields = `
                <div class="form-group">
                    <label for="user-name">Nama User</label>
                    <input type="text" id="user-name" name="name" value="${isEdit ? data.name : ''}" required>
                </div>
                <div class="form-group">
                    <label for="user-email">Email</label>
                    <input type="email" id="user-email" name="email" value="${isEdit ? data.email : ''}" required>
                </div>
                <div class="form-group">
                    <label for="user-address">Alamat</label>
                    <input type="text" id="user-address" name="address" value="${isEdit ? data.address : ''}" required>
                </div>
            `;
            break;
        
        default:
            alert('Error: Tipe service tidak dikenal.');
            return;
    }

    // 2. Isi konten modal
    const titleText = isEdit ? `${title} (ID: ${data.id})` : title;
    modalTitle.textContent = titleText;
    modalFormBody.innerHTML = htmlFields;
    
    // Set ID hanya jika mode Edit, kosongkan jika mode Tambah
    modalItemId.value = isEdit ? data.id : '';
    modalServiceType.value = serviceType;
    
    // 3. Tampilkan modal
    modal.classList.add("show");
}

/**
 * Mengirim request (PUT atau POST) dari Modal Form ke API
 */
async function sendModalFormRequest(url, method, payload, serviceName, refreshFunction) {
    try {
        const response = await fetch(url, {
            method: method, // Gunakan 'POST' atau 'PUT'
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        const action = (method.toUpperCase() === 'POST') ? 'dibuat' : 'diupdate';
        
        if (!response.ok) throw new Error(result.error || `Gagal ${action} ${serviceName}`);

        alert(`Sukses: ${serviceName} telah ${action}.`);
        refreshFunction(); // Muat ulang data tabel yang relevan
        closeEditModal(); // Tutup modal setelah sukses

    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

/**
 * Menangani submit dari form modal (saat tombol "Simpan Perubahan" diklik)
 */
async function handleModalFormSubmit(event) {
    event.preventDefault(); // Mencegah form reload halaman
    
    const id = modalItemId.value; // ID item (kosong jika 'Tambah Baru')
    const serviceType = modalServiceType.value;
    
    const formData = new FormData(event.target);
    const payload = Object.fromEntries(formData.entries());

    let url = `${GATEWAY_URL}`;
    let method = ''; // Akan kita tentukan
    let refreshFunction;
    let serviceName = '';

    switch (serviceType) {
        case 'menu':
            serviceName = 'Menu';
            refreshFunction = refreshCurrentMenuList;
            if (id) {
                url += `/restaurant-service/menu/${id}`;
                method = 'PUT';
            } else {
                const restoId = menuRestoIdInput.value;
                if (!restoId) {
                    alert("Error: restoId tidak ditemukan."); return;
                }
                url += `/restaurant-service/restaurants/${restoId}/menu`;
                method = 'POST';
            }
            break;

        case 'driver':
            serviceName = 'Driver';
            refreshFunction = fetchAllDrivers;
            if (id) {
                url += `/driver-service/drivers/${id}`;
                method = 'PUT';
            } else {
                url += `/driver-service/drivers`; // Endpoint untuk Tambah Driver
                method = 'POST';
            }
            break;
        
        case 'restaurant':
            serviceName = 'Restoran';
            refreshFunction = fetchAllRestaurants;
            if (id) {
                url += `/restaurant-service/restaurants/${id}`;
                method = 'PUT';
            } else {
                url += `/restaurant-service/restaurants`; // Endpoint untuk Tambah Resto
                method = 'POST';
            }
            break;

        case 'user':
            serviceName = 'User';
            refreshFunction = fetchAllUsers;
            if (id) {
                url += `/user-service/users/${id}`;
                method = 'PUT';
            } else {
                url += `/user-service/users`; // Endpoint untuk Tambah User
                method = 'POST';
            }
            break;
        
        default:
            alert('Error: Tipe service tidak dikenal.');
            return;
    }

    // Panggil fungsi yang sudah digeneralisasi
    await sendModalFormRequest(url, method, payload, serviceName, refreshFunction);
}

/**
 * Menangani Hapus (Delete) generik untuk SEMUA service
 */
async function handleDelete(serviceType, id) {
    let serviceName = '';
    let url = `${GATEWAY_URL}`;
    let refreshFunction;

    // Tentukan URL endpoint dan fungsi refresh berdasarkan serviceType
    switch (serviceType) {
        case 'menu':
            serviceName = 'Menu';
            url += `/restaurant-service/menu/${id}`;
            refreshFunction = refreshCurrentMenuList;
            break;
        case 'driver':
            serviceName = 'Driver';
            url += `/driver-service/drivers/${id}`;
            refreshFunction = fetchAllDrivers;
            break;
        case 'restaurant':
            serviceName = 'Restoran';
            url += `/restaurant-service/restaurants/${id}`;
            refreshFunction = fetchAllRestaurants;
            break;
        case 'user':
            serviceName = 'User';
            url += `/user-service/users/${id}`;
            refreshFunction = fetchAllUsers;
            break;
        default:
            alert('Error: Tipe service tidak dikenal.');
            return;
    }

    if (!confirm(`Apakah Anda yakin ingin menghapus ${serviceName} ID: ${id}?`)) return;

    try {
        const response = await fetch(url, { method: 'DELETE' });
        // Jika endpoint mengembalikan 204 No Content (sukses tanpa body)
        if (response.status === 204) {
             // No content, sukses
        } else {
             // Jika endpoint mengembalikan JSON (seperti pesan error)
             const result = await response.json();
             if (!response.ok) throw new Error(result.error || `Gagal menghapus ${serviceName}`);
        }
        
        alert(`Sukses: ${serviceName} (ID: ${id}) telah dihapus.`);
        refreshFunction(); // Muat ulang data tabel yang relevan

    } catch (error) {
        alert(`Error saat menghapus: ${error.message}`);
    }
}


// =========================================================================
//  FUNGSI READ (Panel Grid 2x2)
// =========================================================================

// === 1. Logika untuk Driver Service ===
async function fetchAllDrivers() {
    driverListBody.innerHTML = '<tr><td colspan="4">Memuat...</td></tr>';
    try {
        const response = await fetch(`${GATEWAY_URL}/driver-service/drivers`);
        const drivers = await response.json();
        driverListBody.innerHTML = "";
        if (!drivers || drivers.length === 0) {
            driverListBody.innerHTML = '<tr><td colspan="4">Tidak ada driver.</td></tr>';
            return;
        }

        drivers.forEach(driver => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${driver.id}</td><td>${driver.name}</td><td class="${driver.status === 'available' ? 'status-available' : 'status-on_trip'}">${driver.status.toUpperCase()}</td>`;
            const tdAksi = document.createElement("td");

            if (driver.status === 'on_trip') {
                const statusBtn = document.createElement("button");
                statusBtn.className = "action-btn green";
                statusBtn.textContent = "Set Available";
                statusBtn.addEventListener("click", () => makeDriverAvailable(driver.id));
                tdAksi.appendChild(statusBtn);
            }
            
            const editBtn = document.createElement("button");
            editBtn.className = "action-btn";
            editBtn.textContent = "Edit";
            editBtn.addEventListener("click", () => openForm('driver', driver));
            tdAksi.appendChild(editBtn);

            const delBtn = document.createElement("button");
            delBtn.className = "action-btn red";
            delBtn.textContent = "Hapus";
            delBtn.addEventListener("click", () => handleDelete('driver', driver.id));
            tdAksi.appendChild(delBtn);

            tr.appendChild(tdAksi);
            driverListBody.appendChild(tr);
        });
    } catch (error) {
        driverListBody.innerHTML = `<tr><td colspan="4">Gagal memuat: ${error.message}</td></tr>`;
    }
}

async function makeDriverAvailable(driverId) {
    if (!confirm(`Yakin ingin mengubah status Driver ID ${driverId} menjadi 'available'?`)) return;
    try {
        const response = await fetch(`${GATEWAY_URL}/driver-service/drivers/${driverId}/status`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ "status": "available" })
        });
        if (!response.ok) throw new Error('Gagal update status');
        alert('Status driver berhasil di-update!');
        fetchAllDrivers();
        fetchAllOrders();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// === 2. Logika untuk Order Service ===
async function fetchAllOrders() {
    orderListBody.innerHTML = '<tr><td colspan="6">Memuat...</td></tr>';
    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders`);
        const orders = await response.json();
        orderListBody.innerHTML = "";
        if (!orders || orders.length === 0) {
            orderListBody.innerHTML = '<tr><td colspan="6">Tidak ada pesanan.</td></tr>';
            return;
        }

        orders.forEach(order => {
            const tr = document.createElement("tr");
            let statusClass = `status-${order.status.toLowerCase()}`;
            
            let actionCellHTML = '<td>-</td>'; // Default
            if (order.status === 'CONFIRMED') {
                actionCellHTML = `<td><button class="action-btn green" data-order-id="${order.order_id}">Selesaikan</button></td>`;
            }

            tr.innerHTML = `
                <td>${order.order_id}</td>
                <td>${order.user_id}</td>
                <td>Rp${order.total_price}</td>
                <td class="${statusClass}">${order.status}</td>
                <td>${order.driver_id || '-'}</td>
                ${actionCellHTML}
            `;
            
            if (order.status === 'CONFIRMED') {
                tr.querySelector('.action-btn.green').addEventListener('click', () => completeOrder(order.order_id));
            }
            
            orderListBody.appendChild(tr);
        });
    } catch (error) {
        orderListBody.innerHTML = `<tr><td colspan="6">Gagal memuat: ${error.message}</td></tr>`;
    }
}

async function completeOrder(orderId) {
    if (!confirm(`Yakin ingin menyelesaikan Pesanan ID: ${orderId}?`)) return;
    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/${orderId}/complete`, { method: 'PUT' });
        if (!response.ok) throw new Error('Gagal menyelesaikan pesanan');
        alert(`Pesanan ${orderId} telah selesai!`);
        fetchAllOrders();
        fetchAllDrivers();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// === 3. Logika untuk Restaurant Service ===
async function fetchAllRestaurants() {
    restoListBody.innerHTML = '<tr><td colspan="4">Memuat...</td></tr>';
    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants`);
        const restos = await response.json();
        restoListBody.innerHTML = "";
        if (!restos || restos.length === 0) {
            restoListBody.innerHTML = '<tr><td colspan="4">Tidak ada restoran.</td></tr>';
            return;
        }

        restos.forEach(resto => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${resto.id}</td><td>${resto.name}</td><td>${resto.address}</td>`;
            
            const tdAksi = document.createElement("td");
            
            // Tombol Manage Menu (Pemicu Master-Detail)
            const menuBtn = document.createElement("button");
            menuBtn.className = "action-btn blue";
            menuBtn.textContent = "Manage Menu";
            menuBtn.addEventListener("click", () => openMenuPanel(resto.id, resto.name));
            tdAksi.appendChild(menuBtn);

            // Tombol Edit Resto (Menggunakan Modal)
            const editBtn = document.createElement("button");
            editBtn.className = "action-btn";
            editBtn.textContent = "Edit";
            editBtn.addEventListener("click", () => openForm('restaurant', resto));
            tdAksi.appendChild(editBtn);

            // Tombol Hapus Resto (Menggunakan Modal)
            const delBtn = document.createElement("button");
            delBtn.className = "action-btn red";
            delBtn.textContent = "Hapus";
            delBtn.addEventListener("click", () => handleDelete('restaurant', resto.id));
            tdAksi.appendChild(delBtn);
            
            tr.appendChild(tdAksi);
            restoListBody.appendChild(tr);
        });
    } catch (error) {
        restoListBody.innerHTML = `<tr><td colspan="4">Gagal memuat: ${error.message}</td></tr>`;
    }
}

// === 4. Logika untuk User Service ===
async function fetchAllUsers() {
    userListBody.innerHTML = '<tr><td colspan="4">Memuat...</td></tr>'; 
    try {
        const response = await fetch(`${GATEWAY_URL}/user-service/users`);
        const users = await response.json();
        userListBody.innerHTML = "";
        if (!users || users.length === 0) {
            userListBody.innerHTML = '<tr><td colspan="4">Tidak ada user.</td></tr>';
            return;
        }
        
        users.forEach(user => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${user.id}</td><td>${user.name}</td><td>${user.email}</td><td>${user.address}</td>`;

            const tdAksi = document.createElement("td");
            
            const editBtn = document.createElement("button");
            editBtn.className = "action-btn";
            editBtn.textContent = "Edit";
            editBtn.addEventListener("click", () => openForm('user', user));
            tdAksi.appendChild(editBtn);

            const delBtn = document.createElement("button");
            delBtn.className = "action-btn red";
            delBtn.textContent = "Hapus";
            delBtn.addEventListener("click", () => handleDelete('user', user.id));
            tdAksi.appendChild(delBtn);
            
            tr.appendChild(tdAksi);
            userListBody.appendChild(tr);
        });
    } catch (error) {
        userListBody.innerHTML = `<tr><td colspan="4">Gagal memuat: ${error.message}</td></tr>`;
    }
}


// === Muat semua data saat halaman dibuka ===
document.addEventListener("DOMContentLoaded", () => {
    
    // --- Inisialisasi DOM untuk Panel Menu ---
    menuPanel = document.getElementById("menu-panel");
    menuPanelTitle = document.getElementById("menu-panel-title");
    menuListBody = document.getElementById("menu-list-body");
    // Hanya simpan referensi ke input hidden, bukan form
    menuRestoIdInput = document.getElementById("menu-resto-id-input"); 

    // --- Inisialisasi DOM untuk Modal Edit ---
    modal = document.getElementById("edit-modal");
    modalTitle = document.getElementById("modal-title");
    modalFormBody = document.getElementById("modal-form-body");
    modalItemId = document.getElementById("modal-item-id");
    modalServiceType = document.getElementById("modal-service-type");
    
    // --- Pasang listener untuk Modal ---
    document.getElementById("modal-form").addEventListener("submit", handleModalFormSubmit);
    document.getElementById("modal-close-btn").addEventListener("click", closeEditModal);
    
    // Menutup modal jika user mengklik di luar area konten (latar belakang)
    modal.addEventListener("click", (event) => {
        if (event.target === modal) { // Jika yang diklik adalah overlay-nya
            closeEditModal();
        }
    });

    // --- Pasang listener untuk Tombol "Tambah Menu Baru" ---
    document.getElementById("add-menu-btn").addEventListener("click", () => {
        // Ambil restoId saat ini dari hidden input di panel
        const restoId = menuRestoIdInput.value;
        if (!restoId) {
            alert("Error: Tidak dapat menemukan ID Restoran untuk menambah menu.");
            return;
        }
        // Panggil openForm untuk 'menu' tapi tanpa data (hanya objek kosong)
        openForm('menu', {}); 
    });

    // --- Pasang listener untuk Tombol "Tambah" di Panel Grid ---
    document.getElementById("add-driver-btn").addEventListener("click", () => {
        openForm('driver', {}); // Panggil modal 'driver' dengan data kosong
    });
    
    document.getElementById("add-resto-btn").addEventListener("click", () => {
        openForm('restaurant', {}); // Panggil modal 'restaurant' dengan data kosong
    });
    
    document.getElementById("add-user-btn").addEventListener("click", () => {
        openForm('user', {}); // Panggil modal 'user' dengan data kosong
    });
    
    // --- Inisialisasi DOM untuk Tabel Grid ---
    driverListBody = document.getElementById("driver-list-body");
    orderListBody = document.getElementById("order-list-body");
    restoListBody = document.getElementById("resto-list-body");
    userListBody = document.getElementById("user-list-body");

    // --- Pasang listener untuk tombol refresh ---
    document.getElementById("refreshDriversBtn").addEventListener("click", fetchAllDrivers);
    document.getElementById("refreshOrdersBtn").addEventListener("click", fetchAllOrders);
    document.getElementById("refreshRestosBtn").addEventListener("click", fetchAllRestaurants);
    document.getElementById("refreshUsersBtn").addEventListener("click", fetchAllUsers);
    
    // --- Muat data awal ---
    fetchAllDrivers();
    fetchAllOrders();
    fetchAllRestaurants();
    fetchAllUsers();
});