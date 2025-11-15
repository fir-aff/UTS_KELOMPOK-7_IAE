// frontend/app.js

const GATEWAY_URL = "http://127.0.0.1:5000/api";

// === State Aplikasi ===
let cart = []; // Keranjang belanja
let intervalId = null; // Untuk auto-refresh

// === Ambil Elemen DOM ===
const userNameSpan = document.getElementById("user-name");
const userAddressSpan = document.getElementById("user-address");

// Panel Login
const loginForm = document.getElementById("login-form");
const loginEmailInput = document.getElementById("login-email");
const loginPasswordInput = document.getElementById("login-password");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const loginStatus = document.getElementById("login-status");

// Panel Utama
const restaurantPanel = document.getElementById("restaurant-selection");
const orderPanel = document.getElementById("order-creation");
const historyPanel = document.getElementById("history-section");

const restaurantDropdown = document.getElementById("restaurant-dropdown");
const menuContainer = document.getElementById("menu-container");
const menuList = document.getElementById("menu-list");

const cartList = document.getElementById("cart-list");
const cartTotalPriceSpan = document.getElementById("cart-total-price");
const createOrderBtn = document.getElementById("createOrderBtn");

const orderListBody = document.getElementById("order-list-body");

// === FUNGSI UTAMA ===

/**
 * BARU: Fungsi untuk menangani Login
 */
async function handleLogin(event) {
    event.preventDefault();
    loginStatus.textContent = "Mencoba login...";

    try {
        const response = await fetch(`${GATEWAY_URL}/user-service/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                email: loginEmailInput.value,
                password: loginPasswordInput.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Login gagal');
        }

        // SUKSES! Simpan token di localStorage
        localStorage.setItem('token', data.access_token);

        // Tampilkan UI setelah login
        await showLoggedInUI();

    } catch (error) {
        loginStatus.textContent = `Error: ${error.message}`;
        console.error("Login error:", error);
    }
}

/**
 * BARU: Fungsi untuk menangani Logout
 */
function handleLogout() {
    localStorage.removeItem('token'); // Hapus token

    // Sembunyikan UI
    restaurantPanel.classList.add("hidden");
    orderPanel.classList.add("hidden");
    historyPanel.classList.add("hidden");

    // Reset Header
    userNameSpan.textContent = "-Belum Login-";
    userAddressSpan.textContent = "-";

    // Reset Login Form
    loginForm.reset();
    loginBtn.classList.remove("hidden");
    logoutBtn.classList.add("hidden");
    loginStatus.textContent = "Anda telah logout.";

    // Hentikan auto-refresh
    if (intervalId) clearInterval(intervalId);
}

/**
 * BARU: Menyiapkan header Authorization untuk fetch
 */
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    if (!token) return null; // Tidak ada token

    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

/**
 * BARU: Menjalankan UI setelah login berhasil
 */
async function showLoggedInUI() {
    const headers = getAuthHeaders();
    if (!headers) return; // Seharusnya tidak terjadi

    // 1. Dapatkan data user (dari user-service)
    // Kita perlu endpoint baru di user-service: /auth/me
    // PIVOT: Kita akan gunakan /users/<id> tapi kita tidak tahu ID-nya.
    // SOLUSI: Kita akan panggil endpoint riwayat pesanan, dan di sana
    // kita akan mengambil data user.

    // Tampilkan panel
    restaurantPanel.classList.remove("hidden");
    orderPanel.classList.remove("hidden");
    historyPanel.classList.remove("hidden");

    // Ubah tombol login
    loginBtn.classList.add("hidden");
    logoutBtn.classList.remove("hidden");
    loginStatus.textContent = "Login berhasil!";

    // Muat semua data
    await fetchRestaurants();
    await fetchOrders(); // Fungsi ini akan mengisi header profil

    // Mulai auto-refresh
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(fetchOrders, 5000);
}

/**
 * 3. Muat daftar restoran ke dropdown
 */
async function fetchRestaurants() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants`, { headers });
        const restaurants = await response.json();

        restaurantDropdown.innerHTML = '<option value="">--Pilih Resto--</option>';
        restaurants.forEach(resto => {
            const option = document.createElement("option");
            option.value = resto.id;
            option.textContent = resto.name;
            restaurantDropdown.appendChild(option);
        });
    } catch (error) {
        console.error("Gagal memuat restoran:", error);
    }
}

/**
 * 4. Muat menu saat restoran dipilih
 */
async function fetchMenu(restoId) {
    const headers = getAuthHeaders();
    if (!headers) return;

    menuList.innerHTML = "<li>Memuat menu...</li>";
    menuContainer.classList.remove("hidden");

    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants/${restoId}/menu`, { headers });
        const menuItems = await response.json();

        menuList.innerHTML = ""; 
        menuItems.forEach(item => {
            const li = document.createElement("li");
            li.innerHTML = `
                <span>${item.name} - Rp${item.price}</span>
                <button onclick="addToCart(${item.id}, '${item.name}', ${item.price})">Tambah</button>
            `;
            menuList.appendChild(li);
        });
    } catch (error) {
        menuList.innerHTML = `<li>Gagal memuat menu: ${error.message}</li>`;
    }
}

// (Fungsi keranjang: addToCart, updateCart, dll. TETAP SAMA)
// ... (Salin semua fungsi keranjang dari kode Anda sebelumnya) ...
function addToCart(menuId, name, price) {
    const existingItem = cart.find(item => item.menu_id === menuId);
    if (existingItem) { existingItem.quantity++; } else {
        cart.push({ menu_id: menuId, name: name, price: price, quantity: 1 });
    }
    updateCart();
}
function updateCartItemQuantity(menuId, newQuantity) {
    const quantity = parseInt(newQuantity);
    if (quantity < 1) { removeFromCart(menuId); return; }
    const item = cart.find(item => item.menu_id === menuId);
    if (item) { item.quantity = quantity; }
    updateCart();
}
function removeFromCart(menuId) {
    cart = cart.filter(item => item.menu_id !== menuId);
    updateCart();
}
function updateCart() {
    cartList.innerHTML = "";
    let totalPrice = 0;
    if (cart.length === 0) {
        cartList.innerHTML = "<li>Keranjang kosong</li>";
        createOrderBtn.disabled = true;
    } else {
        cart.forEach(item => {
            const li = document.createElement("li");
            li.innerHTML = `
                <span class="cart-item-name">${item.name} (Rp${item.price})</span>
                <div class="cart-item-controls">
                    <input type="number" min="1" value="${item.quantity}" 
                           onchange="updateCartItemQuantity(${item.menu_id}, this.value)">
                    <button class="remove-btn" onclick="removeFromCart(${item.menu_id})">Hapus</button>
                </div>
            `;
            cartList.appendChild(li);
            totalPrice += item.price * item.quantity;
        });
        createOrderBtn.disabled = false;
    }
    cartTotalPriceSpan.textContent = totalPrice;
}


/**
 * 6. Kirim Pesanan ke Backend (DIUBAH)
 */
async function createOrder() {
    const headers = getAuthHeaders();
    if (!headers || cart.length === 0) {
        alert("Silakan login atau isi keranjang Anda!");
        return;
    }

    createOrderBtn.disabled = true;
    createOrderBtn.textContent = "Memproses...";

    // user_id TIDAK dikirim lagi, backend ambil dari token
    const itemsPayload = cart.map(item => ({
        "menu_id": item.menu_id,
        "quantity": item.quantity
    }));

    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders`, {
            method: 'POST',
            headers: headers, // Kirim token di header
            body: JSON.stringify({ "items": itemsPayload }), // Hanya kirim items
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Gagal membuat pesanan');
        }

        alert(`Pesanan berhasil dibuat! Order ID: ${result.order.order_id}`);

        // BARU: Isi header profil dari data pesanan
        userNameSpan.textContent = result.order.user_name; // Ambil dari response
        // (Kita asumsikan user_service mengisi alamat di user_data)

        fetchOrders(); // Muat ulang riwayat
        cart = [];
        updateCart();

    } catch (error) {
        alert(`Gagal membuat pesanan: ${error.message}`);
    }

    createOrderBtn.disabled = (cart.length === 0);
    createOrderBtn.textContent = "Kirim Pesanan";
}

/**
 * 7. Muat Riwayat Pesanan (DIUBAH)
 */
async function fetchOrders() {
    const headers = getAuthHeaders();
    if (!headers) return; 

    try {
        // Panggil endpoint baru (tanpa ID)
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/user`, { headers });
        if (response.status === 401) { // Token expired
            handleLogout();
            loginStatus.textContent = "Sesi Anda habis. Silakan login lagi.";
            return;
        }
        const orders = await response.json();

        orderListBody.innerHTML = ""; 
        if (orders.message) { 
            orderListBody.innerHTML = `<tr><td colspan="5">${orders.message}</td></tr>`;
            return;
        }

        // (sisa fungsi fetchOrders tetap sama)
        // ...
// ... (Salin sisa fungsi fetchOrders dari kode Anda sebelumnya) ...
    orders.sort((a, b) => b.order_id - a.order_id); 
    orders.forEach(order => {
        const tr = document.createElement("tr");
        let statusClass = '';
        if (order.status === 'PENDING') statusClass = 'status-pending';
        if (order.status === 'CONFIRMED') statusClass = 'status-confirmed';
        if (order.status === 'DELIVERED') statusClass = 'status-delivered';
        let driverId = order.driver_id ? order.driver_id : '-';
        let actionCell = '<td>-</td>'; 
        if (order.status === 'CONFIRMED') {
            actionCell = `<td><button class="complete-btn" onclick="completeOrder(${order.order_id})">Selesai</button></td>`;
        }
        tr.innerHTML = `
            <td>${order.order_id}</td>
            <td>Rp${order.total_price}</td>
            <td class="${statusClass}">${order.status}</td>
            <td>${driverId}</td>
            ${actionCell}
        `;
        orderListBody.appendChild(tr);
    });

} catch (error) {
    orderListBody.innerHTML = `<tr><td colspan="5">Gagal memuat riwayat.</td></tr>`;
}
}


/**
 * 8. Selesaikan Pesanan (DIUBAH)
 */
async function completeOrder(orderId) {
    const headers = getAuthHeaders();
    if (!headers) return;

    if (!confirm(`Apakah Anda yakin ingin menyelesaikan Pesanan ID: ${orderId}?`)) return;
    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/${orderId}/complete`, {
            method: 'PUT',
            headers: headers // Kirim token
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Gagal menyelesaikan pesanan');
        } 

        alert(`Pesanan ${orderId} telah selesai! Driver akan dibebaskan.`);
        fetchOrders(); 

    } catch (error) {
        alert(`Gagal menghubungi server: ${error.message}`);
    }
}

// === Muat data awal saat halaman dibuka ===
document.addEventListener("DOMContentLoaded", () => {
    // Cek apakah user sudah login (token ada di localStorage)
    if (localStorage.getItem('token')) {
        showLoggedInUI();
    }

    // Pasang listener
    loginForm.addEventListener("submit", handleLogin);
    logoutBtn.addEventListener("click", handleLogout);
    restaurantDropdown.addEventListener("change", () => {
        const restoId = restaurantDropdown.value;
        if (restoId) fetchMenu(restoId);
        else menuContainer.classList.add("hidden");
    });
    createOrderBtn.addEventListener("click", createOrder);
});