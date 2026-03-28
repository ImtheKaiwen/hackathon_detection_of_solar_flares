// routing to main menu
function index() {
    window.location.href = '/'
}

const btnMainMenu = document.getElementById('index-btn');

btnMainMenu.addEventListener('click', (e) => {
    e.preventDefault()
    index()
})

// register
const btnRegister = document.getElementById('register-btn');

btnRegister.addEventListener('click', async (event) => {
    event.preventDefault(); 

    const name = document.getElementById('name').value;
    const surname = document.getElementById('surname').value;
    const email = document.getElementById('email').value;

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                surname: surname,
                email: email
            })
        });

        const data = await response.json();

        if (data.status == true) {
            alert('Kayıt başarılı bir şekilde tamamlandı');
            window.location.href = '/'; 
        } else {
            alert('Hata: ' + data.message);
            clear_fields()
        }

    } catch (error) {
        console.error('Hata:', error);
        alert('Sunucuya bağlanırken hata oluştu');
        clear_fields()
    }
});


function clear_fields(){
     const name = document.getElementById('name').value = ''
    const surname = document.getElementById('surname').value = ''
    const email = document.getElementById('email').value = ''
}