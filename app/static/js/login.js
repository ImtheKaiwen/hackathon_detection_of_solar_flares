const btnRegister = document.getElementById('login');

btnRegister.addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'username': username, 'password': password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Sunucudan olumsuz bir yanıt döndü.");
        }
        return response.json(); 
    })
    .then(result => {
        if (result.status === true) {
            console.log("giriş başarılı! Kullanıcı ID:", result.user_id);
            alert("Giriş başarılı!");
            window.location.href = '/dashboard'; 
        } else {
            console.log("Giriş başarısız:", result.message);
            alert("Giriş işlemi başarısız oldu: " + (result.message || "Bilinmeyen hata"));
        }
    })
    .catch(error => {
        console.error("Bir hata oluştu:", error);
        alert("Sunucuya bağlanılamadı. Lütfen daha sonra tekrar deneyin.");
    });
});