// frontend/app.js

const GATEWAY_URL = "http://127.0.0.1:5000/api";

// === State Aplikasi ===
let selectedUserId = null;
let selectedUserAddress = "";
let cart = []; // Keranjang belanja
let intervalId = null; // Untuk auto-refresh

// === Ambil Elemen DOM ===
const userNameSpan = document.getElementById("user-name");
const userAddressSpan = document.getElementById("user-address");
const userList = document.getElementById("user-list");

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
 * 1. Muat daftar user di awal
 */
async function fetchAllUsers() {
    userList.innerHTML = "<li>Memuat...</li>";
    try {
        const response = await fetch(`${GATEWAY_URL}/user-service/users`);
        const users = await response.json();
        
        userList.innerHTML = "";
        users.forEach(user => {
            const li = document.createElement("li");
            li.textContent = `${user.name} (ID: ${user.id})`;
            li.dataset.userId = user.id;
            li.dataset.userName = user.name;
            li.dataset.userAddress = user.address;
            
            li.addEventListener("click", () => selectUser(user, li));
            userList.appendChild(li);
        });
    } catch (error) {
        userList.innerHTML = `<li>Gagal memuat user: ${error.message}</li>`;
    }
}

/**
 * 2. Dipanggil saat user diklik (simulasi "Login")
 */
function selectUser(user, clickedLi) {
    selectedUserId = user.id;
    selectedUserAddress = user.address;

    userNameSpan.textContent = user.name;
    userAddressSpan.textContent = user.address;
    
    restaurantPanel.classList.remove("hidden");
    orderPanel.classList.remove("hidden");
    historyPanel.classList.remove("hidden");
    
    cart = [];
    updateCart();
    restaurantDropdown.value = "";
    menuContainer.classList.add("hidden");

    document.querySelectorAll("#user-list li").forEach(li => li.classList.remove("selected"));
    clickedLi.classList.add("selected");

    fetchRestaurants();
    fetchOrders(selectedUserId); 
    
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(() => fetchOrders(selectedUserId), 5000);
}

/**
 * 3. Muat daftar restoran ke dropdown
 */
async function fetchRestaurants() {
    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants`);
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
    menuList.innerHTML = "<li>Memuat menu...</li>";
    menuContainer.classList.remove("hidden");

    try {
        const response = await fetch(`${GATEWAY_URL}/restaurant-service/restaurants/${restoId}/menu`);
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

restaurantDropdown.addEventListener("change", () => {
    const restoId = restaurantDropdown.value;
    if (restoId) {
        fetchMenu(restoId);
    } else {
        menuContainer.classList.add("hidden");
    }
});

/**
 * 5. Logika Keranjang (Add to Cart)
 */
function addToCart(menuId, name, price) {
    const existingItem = cart.find(item => item.menu_id === menuId);
    
    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({
            menu_id: menuId,
            name: name,
            price: price,
            quantity: 1
        });
    }
    updateCart(); // Panggil updateCart untuk me-render ulang
}

/**
 * BARU: Fungsi untuk mengubah jumlah item di keranjang
 */
function updateCartItemQuantity(menuId, newQuantity) {
    const quantity = parseInt(newQuantity);
    
    if (quantity < 1) {
        // Jika jumlah 0 atau kurang, hapus item
        removeFromCart(menuId);
        return;
    }
    
    const item = cart.find(item => item.menu_id === menuId);
    if (item) {
        item.quantity = quantity;
    }
    updateCart(); // Render ulang keranjang & total
}

/**
 * BARU: Fungsi untuk menghapus item dari keranjang
 */
function removeFromCart(menuId) {
    cart = cart.filter(item => item.menu_id !== menuId);
    updateCart(); // Render ulang keranjang & total
}

/**
 * FUNGSI DIPERBARUI: Render ulang tampilan keranjang
 */
function updateCart() {
    cartList.innerHTML = ""; // Kosongkan
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
 * 6. Kirim Pesanan ke Backend
 */
async function createOrder() {
    if (!selectedUserId || cart.length === 0) {
        alert("User belum dipilih atau keranjang kosong!");
        return;
    }

    createOrderBtn.disabled = true;
    createOrderBtn.textContent = "Memproses...";

    const itemsPayload = cart.map(item => ({
        "menu_id": item.menu_id,
        "quantity": item.quantity
    }));

    const orderPayload = {
        "user_id": selectedUserId,
        "items": itemsPayload
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
            fetchOrders(selectedUserId); 
            cart = [];
            updateCart();
        }
    } catch (error) {
        alert(`Gagal membuat pesanan: ${error.message}`);
    }
    
    createOrderBtn.disabled = (cart.length === 0);
    createOrderBtn.textContent = "Kirim Pesanan";
}

createOrderBtn.addEventListener("click", createOrder);

/**
 * 7. Muat Riwayat Pesanan
 */
async function fetchOrders(userId) {
    if (!userId) return; 

    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/user/${userId}`);
        const orders = await response.json();
        
        orderListBody.innerHTML = ""; 
        if (orders.message) { 
            orderListBody.innerHTML = `<tr><td colspan="5">${orders.message}</td></tr>`;
            return;
        }
        
        orders.sort((a, b) => b.order_id - a.order_id); 
        
        orders.forEach(order => {
            const tr = document.createElement("tr");
            let statusClass = '';
            if (order.status === 'PENDING') statusClass = 'status-pending';
            if (order.status === 'CONFIRMED') statusClass = 'status-confirmed';
            if (order.status === 'DELIVERED') statusClass = 'status-delivered';
            
            let driverId = order.driver_id ? order.driver_id : '-';
            
            if (order.status === 'CONFIRMED') {
                actionCell = `<td><button class="complete-btn" onclick="completeOrder(${order.order_id})">Selesai</button></td>`;
            }

            tr.innerHTML = `
                <td>${order.order_id}</td>
                <td>Rp${order.total_price}</td>
                <td class="${statusClass}">${order.status}</td>
                <td>${driverId}</td>
            `;
            orderListBody.appendChild(tr);
        });
    } catch (error) {
        orderListBody.innerHTML = `<tr><td colspan="5">Gagal memuat riwayat.</td></tr>`;
    }
}

/**
 * 8. Selesaikan Pesanan
 */
async function completeOrder(orderId) {
    if (!confirm(`Apakah Anda yakin ingin menyelesaikan Pesanan ID: ${orderId}?`)) return;
    try {
        const response = await fetch(`${GATEWAY_URL}/order-service/orders/${orderId}/complete`, {
            method: 'PUT',
        });
        const result = await response.json();
        if (!response.ok) {
            alert(`Gagal menyelesaikan pesanan: ${result.error || 'Unknown error'}`);
        } else {
            alert(`Pesanan ${orderId} telah selesai! Driver akan dibebaskan.`);
            fetchOrders(selectedUserId); 
        }
    } catch (error) {
        alert(`Gagal menghubungi server: ${error.message}`);
    }
}

// === Muat data awal saat halaman dibuka ===
document.addEventListener("DOMContentLoaded", () => {
    fetchAllUsers(); // Mulai dengan memuat daftar user
});