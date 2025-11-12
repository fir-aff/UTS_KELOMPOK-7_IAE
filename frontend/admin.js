// frontend/admin.js

const GATEWAY_URL = "http://127.0.0.1:5000/api";

// === DEKLARASI Variabel DOM ===
let driverListBody, orderListBody, restoListBody, userListBody;

// Panel Menu (Bawah)
let menuPanel, menuPanelTitle, menuListBody, menuForm;
let menuIdInput, menuRestoIdInput, menuNameInput, menuPriceInput, menuSubmitBtn, menuCancelBtn;

// =========================================================================
//  LOGIKA PANEL MENU (Full-Width Bawah)
// =========================================================================

/**
 * Membuka panel menu dan memuat datanya.
 */
async function openMenuPanel(restoId, restoName) {
    menuPanel.classList.remove("hidden");
    menuPanelTitle.textContent = `Mengelola Menu untuk: ${restoName}`;
    menuRestoIdInput.value = restoId; 
    cancelEditMenu(); 
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
            delBtn.addEventListener("click", () => handleDeleteMenu(menu.id, restoId));
            tdAksi.appendChild(delBtn);
            
            tr.appendChild(tdAksi);
            menuListBody.appendChild(tr);
        });
    } catch (error) {
        menuListBody.innerHTML = `<tr><td colspan="4">Gagal memuat menu: ${error.message}</td></tr>`;
    }
}

/**
 * Menyiapkan form menu untuk mode 'Edit'
 */
function prepareMenuEdit(menu) {
    menuIdInput.value = menu.id;
    menuNameInput.value = menu.name;
    menuPriceInput.value = menu.price;
    menuSubmitBtn.textContent = "Simpan Perubahan";
    menuSubmitBtn.classList.remove("green");
    menuCancelBtn.classList.remove("hidden");
}

/**
 * Mengembalikan form menu ke mode 'Tambah Baru'
 */
function cancelEditMenu() {
    menuForm.reset(); 
    menuIdInput.value = ""; 
    menuSubmitBtn.textContent = "Tambah Menu";
    menuSubmitBtn.classList.add("green");
    menuCancelBtn.classList.add("hidden");
    // ID resto jangan di-reset
}

/**
 * Menangani submit form menu (Tambah atau Edit)
 */
async function handleMenuFormSubmit(event) {
    event.preventDefault();
    
    const menuId = menuIdInput.value;
    const restoId = menuRestoIdInput.value;
    const name = menuNameInput.value;
    const price = menuPriceInput.value;
    
    let url = `${GATEWAY_URL}/restaurant-service/`;
    let method = menuId ? 'PUT' : 'POST';
    url += menuId ? `menu/${menuId}` : `restaurants/${restoId}/menu`;
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, price })
        });
        
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Gagal menyimpan menu');

        alert(`Sukses: ${result.message}`);
        cancelEditMenu(); 
        fetchMenuList(restoId); 
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

/**
 * Menangani Hapus (Delete) untuk Menu
 */
async function handleDeleteMenu(menuId, restoId) {
    if (!confirm(`Apakah Anda yakin ingin menghapus Menu ID: ${menuId}?`)) return;

    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/menu/${menuId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Gagal menghapus menu');

        alert(`Sukses: ${result.message}`);
        fetchMenuList(restoId); 
        
    } catch (error) {
        alert(`Error: ${error.message}`);
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
            const statusClass = driver.status === 'available' ? 'status-available' : 'status-on_trip';
            
            let actionButton = '-';
            if (driver.status === 'on_trip') {
                actionButton = `<button class="action-btn green" onclick="makeDriverAvailable(${driver.id})">Set Available</button>`;
            }

            tr.innerHTML = `
                <td>${driver.id}</td>
                <td>${driver.name}</td>
                <td class="${statusClass}">${driver.status.toUpperCase()}</td>
                <td>${actionButton}</td>
            `;
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

            tr.innerHTML = `
                <td>${resto.id}</td>
                <td>${resto.name}</td>
                <td>${resto.address}</td>
            `;
            
            const tdAksi = document.createElement("td");
            
            // Tombol Manage Menu (Pemicu Master-Detail)
            const menuBtn = document.createElement("button");
            menuBtn.className = "action-btn blue";
            menuBtn.textContent = "Manage Menu";
            menuBtn.addEventListener("click", () => openMenuPanel(resto.id, resto.name));
            tdAksi.appendChild(menuBtn);
            
            // Tombol Edit/Hapus Resto sudah dihapus
            
            tr.appendChild(tdAksi);
            restoListBody.appendChild(tr);
        });
    } catch (error) {
        restoListBody.innerHTML = `<tr><td colspan="4">Gagal memuat: ${error.message}</td></tr>`;
    }
}

// === 4. Logika untuk User Service ===
async function fetchAllUsers() {
    userListBody.innerHTML = '<tr><td colspan="4">Memuat...</td></tr>'; // Kolom 4
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
            tr.innerHTML = `
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td>${user.address}</td>
            `;
            // Tidak ada kolom Aksi
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
    menuForm = document.getElementById("menu-form");
    menuIdInput = document.getElementById("menu-id-input");
    menuRestoIdInput = document.getElementById("menu-resto-id-input");
    menuNameInput = document.getElementById("menu-name");
    menuPriceInput = document.getElementById("menu-price");
    menuSubmitBtn = document.getElementById("menu-submit-btn");
    menuCancelBtn = document.getElementById("menu-cancel-btn");
    menuForm.addEventListener("submit", handleMenuFormSubmit);
    menuCancelBtn.addEventListener("click", cancelEditMenu);
    
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