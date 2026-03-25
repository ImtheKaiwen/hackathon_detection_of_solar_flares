const btnRegister = document.getElementById('register');

btnRegister.addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'username': username, 'email': email, 'password': password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Sunucudan olumsuz bir yanıt döndü.");
        }
        return response.json(); 
    })
    .then(result => {
        if (result.status === true) {
            console.log("Kayıt başarılı! Kullanıcı ID:", result.user_id);
            alert("Kayıt başarılı!");
            window.location.href = '/login'; 
        } else {
            console.log("Kayıt başarısız:", result.message);
            alert("Kayıt işlemi başarısız oldu: " + (result.message || "Bilinmeyen hata"));
        }
    })
    .catch(error => {
        console.error("Bir hata oluştu:", error);
        alert("Sunucuya bağlanılamadı. Lütfen daha sonra tekrar deneyin.");
    });
});