const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const mainNav = document.getElementById("mainNav");

if (mobileMenuBtn && mainNav) {
  mobileMenuBtn.addEventListener("click", () => {
    mainNav.classList.toggle("open");
  });
}

function goBack() {
  window.history.back();
}

const loginForm = document.getElementById("loginForm");
const formMessage = document.getElementById("formMessage");

if (loginForm) {
  loginForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const firstName = document.getElementById("firstName").value.trim();
    
    const lastName = document.getElementById("lastName").value.trim();
    const email = document.getElementById("email").value.trim();

    if (!firstName || !lastName || !email) {
      formMessage.textContent = "Lütfen tüm alanları doldurun.";
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {
      formMessage.textContent = "Lütfen geçerli bir e-posta adresi girin.";
      return;
    }

    localStorage.setItem("solarUserFirstName", firstName);
    localStorage.setItem("solarUserLastName", lastName);
    localStorage.setItem("solarUserEmail", email);

    formMessage.textContent = "Giriş başarılı! Panele yönlendiriliyorsunuz...";

    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 1200);
  });
}

const userName = document.getElementById("userName");
const userEmail = document.getElementById("userEmail");

if (userName && userEmail) {
  const firstName = localStorage.getItem("solarUserFirstName");
  const lastName = localStorage.getItem("solarUserLastName");
  const email = localStorage.getItem("solarUserEmail");

  if (firstName && lastName) {
    userName.textContent = `${firstName} ${lastName}`;
  }

  if (email) {
    userEmail.textContent = email;
  }
}