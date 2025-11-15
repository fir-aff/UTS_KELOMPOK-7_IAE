// frontend/app.js

document.addEventListener("DOMContentLoaded", () => {

    // === 1. KONFIGURASI ENDPOINT ===
    const API_GATEWAY_URL = "http://127.0.0.1:5000/api";
    const USER_SERVICE_API = `${API_GATEWAY_URL}/user-service`;
    const ORDER_SERVICE_API = `${API_GATEWAY_URL}/order-service`;
    const RESTAURANT_SERVICE_API = `${API_GATEWAY_URL}/restaurant-service`;

    // === 2. REFERENSI ELEMEN DOM ===
    const userNameSpan = document.getElementById("user-name");
    const userAddressSpan = document.getElementById("user-address");
    const loginForm = document.getElementById("login-form");
    const loginEmailInput = document.getElementById("login-email");
    const loginPasswordInput = document.getElementById("login-password");
    const loginBtn = document.getElementById("login-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const loginStatus = document.getElementById("login-status");

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

    // === 3. STATE APLIKASI ===
    let cart = []; 
    let historyInterval = null; 

    // === 4. FUNGSI UTILITY (PENTING) ===

    /**
     * Membuat header Authorization jika token ada
     */
    function getAuthHeaders() {
        const token = localStorage.getItem('accessToken');
        if (!token) return { 'Content-Type': 'application/json' };
        
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Wrapper Fetch yang sudah menyertakan Token
     */
    async function fetchWithToken(url, options = {}) {
        const headers = getAuthHeaders();
        const finalOptions = {
            ...options,
            headers: {
                ...headers,
                ...options.headers,
            }
        };

        const response = await fetch(url, finalOptions);

        if (response.status === 401 || response.status === 422) { // 422 = Token tidak valid
            handleLogout();
            loginStatus.textContent = "Sesi Anda habis/tidak valid. Silakan login lagi.";
            throw new Error('Sesi tidak valid');
        }
        
        return response;
    }


    // === 5. FUNGSI LOGIN, LOGOUT, & UI ===

    async function handleLogin(event) {
        event.preventDefault();
        loginStatus.textContent = "Mencoba login...";
        
        try {
            const response = await fetch(`${USER_SERVICE_API}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: loginEmailInput.value,
                    password: loginPasswordInput.value
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Login gagal');
            }
            
            // SUKSES! Simpan token dan user data
            localStorage.setItem('accessToken', data.access_token);
            // Simpan data user dari respons login Anda
            localStorage.setItem('user', JSON.stringify(data.user)); 
            
            await showLoggedInUI(data.user);
            
        } catch (error) {
            loginStatus.textContent = `Error: ${error.message}`;
            console.error("Login error:", error);
        }
    }

    function handleLogout() {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        
        stopHistoryRefresh();
        showLoggedOutUI();
        updateProfileUI(null);

        restaurantDropdown.innerHTML = '<option value="">--Login dulu--</option>';
        menuList.innerHTML = '';
        if (orderListBody) orderListBody.innerHTML = '';
        cart = [];
        renderCart();

        loginStatus.textContent = 'Anda berhasil logout.';
    }
    
    function updateProfileUI(user) {
        if (user) {
            userNameSpan.textContent = user.name;
            userAddressSpan.textContent = user.address || '-';
        } else {
            userNameSpan.textContent = '-Belum Login-';
            userAddressSpan.textContent = '-';
        }
    }

    async function showLoggedInUI(user) {
        updateProfileUI(user);
        
        loginForm.reset();
        loginBtn.classList.add("hidden");
        logoutBtn.classList.remove("hidden");
        loginStatus.textContent = "Login berhasil!";

        restaurantPanel.classList.remove("hidden");
        orderPanel.classList.remove("hidden");
        historyPanel.classList.remove("hidden");
        cartList.innerHTML = "Keranjang kosong";
        
        await fetchRestaurants();
        await fetchOrders(); 
        
        startHistoryRefresh();
    }

    function showLoggedOutUI() {
        loginBtn.classList.remove("hidden");
        logoutBtn.classList.add("hidden");
        restaurantPanel.classList.add("hidden");
        orderPanel.classList.add("hidden");
        historyPanel.classList.add("hidden");
    }

    // === 6. FUNGSI RESTORAN & MENU ===

    async function fetchRestaurants() {
        try {
            // Gunakan fetchWithToken (meskipun endpoint ini tidak dilindungi)
            const response = await fetchWithToken(`${RESTAURANT_SERVICE_API}/restaurants`);
            if (!response.ok) throw new Error('Gagal memuat restoran');
            
            const restaurants = await response.json();
            
            restaurantDropdown.innerHTML = '<option value="">--Pilih Resto--</option>';
            restaurants.forEach(resto => {
                const option = document.createElement("option");
                option.value = resto.id;
                option.textContent = resto.name;
                restaurantDropdown.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    async function fetchMenu(restoId) {
        menuList.innerHTML = "<li>Memuat menu...</li>";
        menuContainer.classList.remove("hidden");
        try {
            // Gunakan fetchWithToken (meskipun endpoint ini tidak dilindungi)
            const response = await fetchWithToken(`${RESTAURANT_SERVICE_API}/restaurants/${restoId}/menu`);
            if (!response.ok) throw new Error('Gagal memuat menu');
            
            const menuItems = await response.json();
            
            menuList.innerHTML = ""; 
            menuItems.forEach(item => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <span>${item.name} - Rp${item.price}</span>
                    <button class="add-to-cart-btn" data-id="${item.id}" data-name="${item.name}" data-price="${item.price}">Tambah</button>
                `;
                li.querySelector('.add-to-cart-btn').addEventListener('click', (e) => {
                    const data = e.target.dataset;
                    addToCart(parseInt(data.id), data.name, parseFloat(data.price));
                });
                menuList.appendChild(li);
            });
        } catch (error) {
            menuList.innerHTML = `<li>Gagal memuat menu: ${error.message}</li>`;
        }
    }
    
    // === 7. FUNGSI KERANJANG (CART) ===

    function addToCart(menuId, name, price) {
        const existingItem = cart.find(item => item.menu_id === menuId);
        if (existingItem) {
            existingItem.quantity++;
        } else {
            cart.push({ menu_id: menuId, name: name, price: price, quantity: 1 });
        }
        renderCart();
    }

    function updateCartItemQuantity(menuId, newQuantity) {
        const quantity = parseInt(newQuantity);
        if (quantity < 1) {
            removeFromCart(menuId);
            return;
        }
        const item = cart.find(item => item.menu_id === menuId);
        if (item) item.quantity = quantity;
        renderCart();
    }

    function removeFromCart(menuId) {
        cart = cart.filter(item => item.menu_id !== menuId);
        renderCart();
    }

    function renderCart() {
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
                        <input type="number" class="cart-quantity-input" min="1" value="${item.quantity}">
                        <button class="remove-btn">Hapus</button>
                    </div>
                `;
                li.querySelector('.cart-quantity-input').addEventListener('change', (e) => {
                    updateCartItemQuantity(item.menu_id, e.target.value);
                });
                li.querySelector('.remove-btn').addEventListener('click', () => {
                    removeFromCart(item.menu_id);
                });
                
                cartList.appendChild(li);
                totalPrice += item.price * item.quantity;
            });
            createOrderBtn.disabled = false;
        }
        cartTotalPriceSpan.textContent = totalPrice;
    }

    // === 8. FUNGSI MEMBUAT PESANAN ===

    async function createOrder() {
        if (cart.length === 0) return;

        createOrderBtn.disabled = true;
        createOrderBtn.textContent = "Memproses...";

        const itemsPayload = cart.map(item => ({
            "menu_id": item.menu_id,
            "quantity": item.quantity
        }));

        try {
            // Gunakan fetchWithToken untuk mengirim token
            const response = await fetchWithToken(`${ORDER_SERVICE_API}/orders`, {
                method: 'POST',
                body: JSON.stringify({ "items": itemsPayload }), 
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Gagal membuat pesanan');
            
            alert(`Pesanan berhasil dibuat! Order ID: ${result.order.order_id}`);
            fetchOrders(); 
            cart = [];
            renderCart();
        
        } catch (error) {
            alert(`Gagal membuat pesanan: ${error.message}`);
        }
        
        createOrderBtn.disabled = (cart.length === 0);
        createOrderBtn.textContent = "Kirim Pesanan";
    }

    // === 9. FUNGSI RIWAYAT PESANAN ===

    function startHistoryRefresh() {
        stopHistoryRefresh(); 
        historyInterval = setInterval(fetchOrders, 5000);
    }

    function stopHistoryRefresh() {
        if (historyInterval) {
            clearInterval(historyInterval);
            historyInterval = null;
        }
    }

    async function fetchOrders() {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            orderListBody.innerHTML = '<tr><td colspan="5">Silakan login untuk melihat riwayat.</td></tr>';
            return;
        }

        try {
            // PERBAIKAN: Panggil endpoint /orders/my-history
            const response = await fetchWithToken(`${ORDER_SERVICE_API}/orders/my-history`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    orderListBody.innerHTML = '<tr><td colspan="5">Belum ada riwayat pesanan.</td></tr>';
                } else {
                    const data = await response.json();
                    throw new Error(data.message || 'Gagal memuat riwayat.');
                }
                return;
            }

            const orders = await response.json();
            orderListBody.innerHTML = ''; 

            if (orders.length === 0 || (orders.message && orders.message.includes("No orders"))) {
                 orderListBody.innerHTML = '<tr><td colspan="5">Belum ada riwayat pesanan.</td></tr>';
                 return;
            }

            orders.forEach(order => {
                const tr = document.createElement("tr");
                let statusClass = '';
                if (order.status === 'PENDING') statusClass = 'status-pending';
                if (order.status === 'CONFIRMED') statusClass = 'status-confirmed';
                if (order.status === 'DELIVERED') statusClass = 'status-delivered';
                
                let driverId = order.driver_id ? order.driver_id : '-';
                let actionCell = '<td>-</td>'; 
                
                if (order.status === 'CONFIRMED') {
                    actionCell = `<td><button class="complete-btn" data-order-id="${order.order_id}">Selesai</button></td>`;
                }

                tr.innerHTML = `
                    <td>${order.order_id}</td>
                    <td>Rp${order.total_price}</td>
                    <td class="${statusClass}">${order.status}</td>
                    <td>${driverId}</td>
                    ${actionCell}
                `;
                
                // BARU: Pasang listener untuk tombol "Selesai"
                if (order.status === 'CONFIRMED') {
                    tr.querySelector('.complete-btn').addEventListener('click', (e) => {
                        completeOrder(e.target.dataset.orderId);
                    });
                }
                orderListBody.appendChild(tr);
            });

        } catch (error) {
            console.error('Error fetch history:', error);
            orderListBody.innerHTML = `<tr><td colspan="5">${error.message}</td></tr>`;
        }
    }

    // BARU: Fungsi untuk Selesaikan Pesanan
    async function completeOrder(orderId) {
        if (!confirm(`Apakah Anda yakin ingin menyelesaikan Pesanan ID: ${orderId}?`)) return;
        try {
            const response = await fetchWithToken(`${ORDER_SERVICE_API}/orders/${orderId}/complete`, {
                method: 'PUT',
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

    // === 10. MULAI APLIKASI ===
    
    // Pasang listener di awal
    loginForm.addEventListener("submit", handleLogin);
    logoutBtn.addEventListener("click", handleLogout);
    restaurantDropdown.addEventListener("change", () => {
        const restoId = restaurantDropdown.value;
        if (restoId) fetchMenu(restoId);
        else menuContainer.classList.add("hidden");
    });
    createOrderBtn.addEventListener("click", createOrder);
    
    // Cek status login saat halaman dimuat
    const token = localStorage.getItem('accessToken');
    const userJson = localStorage.getItem('user');
    
    if (token && userJson) {
        try {
            showLoggedInUI(JSON.parse(userJson));
        } catch (e) {
            handleLogout(); // Hapus data rusak
        }
    } else {
        showLoggedOutUI();
    }
});