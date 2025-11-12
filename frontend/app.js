// frontend/app.js

const GATEWAY_URL = "http://127.0.0.1:5000/api";
const USER_ID = 1; // Kita hardcode user ID 1 untuk demo ini

// === Ambil Elemen DOM ===
const userNameSpan = document.getElementById("user-name");
const userAddressSpan = document.getElementById("user-address");
const restoList = document.getElementById("restaurant-list");
const menuList = document.getElementById("menu-list");
const selectedRestoName = document.getElementById("selected-resto-name");
const cartItemDiv = document.getElementById("cart-item");
const orderListBody = document.getElementById("order-list-body");
const createOrderBtn = document.getElementById("createOrderBtn");

// === State Aplikasi ===
let stagedOrder = null; // Menyimpan item yang akan dipesan

// === Fungsi Logika ===

/**
 * FUNGSI UNTUK: user-service
 * Mengambil profil pengguna dan menampilkannya di header.
 */
async function fetchUserProfile(userId) {
    try {
        const response = await fetch(`${GATEWAY_URL}/user-service/users/${userId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const user = await response.json();
        
        userNameSpan.textContent = user.name;
        userAddressSpan.textContent = user.address;
    } catch (error) {
        userNameSpan.textContent = "Gagal memuat";
        userAddressSpan.textContent = "Gagal memuat";
        console.error("Fetch user profile error:", error);
    }
}

/**
 * FUNGSI UNTUK: restaurant-service (Bagian 1)
 * Mengambil dan menampilkan daftar restoran
 */
async function fetchRestaurants() {
    restoList.innerHTML = "<li>Memuat...</li>";
    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const restaurants = await response.json();
        
        restoList.innerHTML = ""; // Kosongkan list
        restaurants.forEach(resto => {
            const li = document.createElement("li");
            li.textContent = `${resto.name} (ID: ${resto.id})`;
            li.addEventListener("click", () => fetchMenu(resto.id, resto.name));
            restoList.appendChild(li);
        });
    } catch (error) {
        restoList.innerHTML = `<li>Gagal memuat: ${error.message}</li>`;
    }
}

/**
 * FUNGSI UNTUK: restaurant-service (Bagian 2)
 * Mengambil dan menampilkan menu dari 1 restoran
 */
async function fetchMenu(restoId, restoName) {
    menuList.innerHTML = "<li>Memuat menu...</li>";
    selectedRestoName.textContent = `Menu untuk: ${restoName}`;
    stagedOrder = null;
    updateCreateOrderButton();

    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants/${restoId}/menu`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const menuItems = await response.json();
        
        menuList.innerHTML = ""; 
        menuItems.forEach(item => {
            const li = document.createElement("li");
            li.textContent = `${item.name} - Rp${item.price}`;
            li.addEventListener("click", () => stageItemForOrder(item));
            menuList.appendChild(li);
        });
    } catch (error) {
        menuList.innerHTML = `<li>Gagal memuat menu: ${error.message}</li>`;
    }
}

/**
 * FUNGSI UNTUK: order-service (Helper)
 * Menyiapkan item untuk dipesan
 */
function stageItemForOrder(menuItem) {
    stagedOrder = {
        menu_id: menuItem.id,
        name: menuItem.name,
        price: menuItem.price,
        quantity: 1 
    };
    cartItemDiv.innerHTML = `<p><strong>${stagedOrder.name}</strong> (Qty: 1)</p>`;
    updateCreateOrderButton();
}

/**
 * FUNGSI UNTUK: order-service (Helper)
 * Mengaktifkan/Menonaktifkan tombol pesan
 */
function updateCreateOrderButton() {
    createOrderBtn.disabled = !stagedOrder;
    if (!stagedOrder) {
        cartItemDiv.innerHTML = "<p>Pilih menu untuk memesan.</p>";
    }
}

/**
 * FUNGSI UNTUK: order-service & driver-service (Visual)
 * Mengambil dan menampilkan riwayat pesanan (user 1)
 */
/**
 * FUNGSI UNTUK: order-service & driver-service (Visual)
 * Mengambil dan menampilkan riwayat pesanan (user 1)
 */
async function fetchOrders(userId) {
    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/user/${userId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const orders = await response.json();

        orderListBody.innerHTML = ""; // Kosongkan tabel
        if (orders.message) { 
            orderListBody.innerHTML = `<tr><td colspan="5">${orders.message}</td></tr>`; // BARU: colspan="5"
            return;
        }

        orders.sort((a, b) => b.order_id - a.order_id); 

        orders.forEach(order => {
            const tr = document.createElement("tr");

            // BARU: Logika untuk status
            let statusClass = '';
            if (order.status === 'PENDING') statusClass = 'status-pending';
            if (order.status === 'CONFIRMED') statusClass = 'status-confirmed';
            if (order.status === 'DELIVERED') statusClass = 'status-delivered';

            let driverId = order.driver_id ? order.driver_id : '-';

            // BARU: Logika untuk tombol Aksi
            let actionCell = '<td>-</td>'; // Default tidak ada aksi

            if (order.status === 'CONFIRMED') {
                // Jika status CONFIRMED, tambahkan tombol "Selesai"
                actionCell = `
                    <td>
                        <button class="complete-btn" onclick="completeOrder(${order.order_id})">
                            Selesai
                        </button>
                    </td>
                `;
            }

            tr.innerHTML = `
                <td>${order.order_id}</td>
                <td>Rp${order.total_price}</td>
                <td class="${statusClass}">${order.status}</td>
                <td>${driverId}</td>
                ${actionCell} `;
            orderListBody.appendChild(tr);
        });
    } catch (error) {
        orderListBody.innerHTML = `<tr><td colspan="5">Gagal memuat riwayat.</td></tr>`; // BARU: colspan="5"
        console.error("Fetch orders error:", error);
    }
}

/**
 * FUNGSI UNTUK: order-service (Aksi)
 * Membuat pesanan baru
 */
async function createOrder() {
    if (!stagedOrder) {
        alert("Silakan pilih menu terlebih dahulu!");
        return;
    }
    createOrderBtn.disabled = true; // Nonaktifkan tombol saat proses

    const orderPayload = {
        "user_id": USER_ID,
        "items": [
            { "menu_id": stagedOrder.menu_id, "quantity": stagedOrder.quantity }
        ]
    };

    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(orderPayload),
        });

        const result = await response.json();
        
        if (!response.ok) {
            alert(`Gagal membuat pesanan: ${result.error || 'Unknown error'}`);
        } else {
            alert(`Pesanan berhasil dibuat! Order ID: ${result.order.order_id}`);
            
            // Muat ulang riwayat agar order 'PENDING' langsung muncul
            fetchOrders(USER_ID); 
            
            // Kosongkan keranjang
            stagedOrder = null;
            updateCreateOrderButton();
        }
    } catch (error) {
        alert(`Gagal membuat pesanan: ${error.message}`);
    }
    
    // Aktifkan lagi tombolnya (walau keranjang sudah kosong)
    createOrderBtn.disabled = !stagedOrder; 
}
/**
 * BARU: Fungsi untuk menyelesaikan pesanan (memanggil backend)
 */
async function completeOrder(orderId) {
    // Konfirmasi sederhana
    if (!confirm(`Apakah Anda yakin ingin menyelesaikan Pesanan ID: ${orderId}?`)) {
        return;
    }

    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/${orderId}/complete`, {
            method: 'PUT',
        });

        const result = await response.json();

        if (!response.ok) {
            alert(`Gagal menyelesaikan pesanan: ${result.error || 'Unknown error'}`);
        } else {
            alert(`Pesanan ${orderId} telah selesai! Driver akan dibebaskan.`);

            // Refresh list pesanan untuk melihat perubahannya
            fetchOrders(USER_ID); 
        }
    } catch (error) {
        alert(`Gagal menghubungi server: ${error.message}`);
    }
}

// === Event Listeners ===
// Muat data awal saat halaman dibuka
document.addEventListener("DOMContentLoaded", () => {
    fetchUserProfile(USER_ID);      // Panggil user-service
    fetchRestaurants();             // Panggil restaurant-service
    fetchOrders(USER_ID);           // Panggil order-service
    updateCreateOrderButton();

    // INI ADALAH BUKTI VISUAL DARI 'driver-service'
    // Kita cek status pesanan setiap 5 detik.
    // Anda akan melihat status 'PENDING' berubah menjadi 'CONFIRMED'
    // setelah driver-service di background selesai bekerja.
    setInterval(() => fetchOrders(USER_ID), 5000); 
});

// Tambahkan event ke tombol
createOrderBtn.addEventListener("click", createOrder);