/**
 * Dashboard Grafik Sistemi
 * Canlı güneş verilerini görselleştirmek için
 * Tablo ve Pagination desteğiyle
 */

class DashboardCharts {
  constructor() {
    this.charts = {};
    this.data = null;
    this.selectedFeatures = [];
    this.refreshInterval = null;
    
    // Tablo ayarları
    this.currentPage = 1;
    this.rowsPerPage = 20;
    this.filteredData = [];
    
    this.init();
  }

  async init() {
    console.log(" Dashboard başlatılıyor...");
    this.setupEventListeners();
    await this.loadData();
    this.createCharts();
    this.startAutoRefresh();
  }

  setupEventListeners() {
    // Feature seçim butonu
    const refreshBtn = document.getElementById("refreshDataBtn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this.manualRefresh());
    }

    // Feature checkbox'ları
    document.addEventListener("change", (e) => {
      if (e.target.classList.contains("feature-checkbox")) {
        this.updateCharts();
      }
    });

    // Tablo kontrolleri - event delegation ile
    document.addEventListener("input", (e) => {
      if (e.target.id === "tableSearch") {
        this.filterTableData(e.target.value);
      }
    });

    document.addEventListener("change", (e) => {
      if (e.target.id === "rowsPerPage") {
        this.rowsPerPage = parseInt(e.target.value, 10);
        this.currentPage = 1;
        this.displayTable();
      }
    });

    document.addEventListener("click", (e) => {
      if (e.target.id === "prevBtn") {
        this.previousPage();
      }
      if (e.target.id === "nextBtn") {
        this.nextPage();
      }
    });
  }

  async loadData() {
    try {
      console.log("📡 Veriler çekiliyor...");
      const response = await fetch("/api/clean-data?rows=60&limit_samples=5");
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      this.data = await response.json();
      
      if (this.data.status === "error") {
        console.error("❌ Veri çekme hatası:", this.data.error);
        this.showError(this.data.message || "Veri çekilemedi");
        return false;
      }

      console.log("✅ Veriler başarıyla yüklendi");
      this.updateDataInfo();
      return true;
    } catch (error) {
      console.error("❌ Veri yükleme hatası:", error);
      this.showError(`Bağlantı hatası: ${error.message}`);
      return false;
    }
  }

  updateDataInfo() {
    // İstatistikleri göster
    const totalRows = document.getElementById("totalRows");
    const totalSamples = document.getElementById("totalSamples");
    const lastUpdate = document.getElementById("lastUpdate");

    if (totalRows) totalRows.textContent = this.data.total_rows || 0;
    if (totalSamples) totalSamples.textContent = this.data.samples_by_harpnum?.length || 0;
    if (lastUpdate) lastUpdate.textContent = new Date().toLocaleTimeString("tr-TR");

    // Feature checkbox'larını oluştur
    this.createFeatureCheckboxes();
    
    // Tabloyu oluştur
    this.setupTable();
    this.setupTableData();
  }

  createFeatureCheckboxes() {
    const container = document.getElementById("featureCheckboxContainer");
    if (!container || !this.data.feature_columns) return;

    container.innerHTML = "";
    
    this.data.feature_columns.slice(0, 10).forEach((feature, index) => {
      const label = document.createElement("label");
      label.className = "feature-label";
      
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "feature-checkbox";
      checkbox.value = feature;
      checkbox.checked = index < 3; // İlk 3'ü seç
      
      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(feature));
      
      container.appendChild(label);
    });

    // Seçili feature'ları güncelle
    this.updateSelectedFeatures();
  }

  updateSelectedFeatures() {
    this.selectedFeatures = Array.from(
      document.querySelectorAll(".feature-checkbox:checked")
    ).map((cb) => cb.value);
    
    if (this.selectedFeatures.length === 0) {
      this.selectedFeatures = this.data.feature_columns.slice(0, 3);
    }
  }

  createCharts() {
    if (!this.data?.data || this.data.data.length === 0) {
      this.showError("Grafik çizilecek veri yok");
      return;
    }

    // Zaman serisi grafiği
    this.createTimeSeriesChart();
    
    // Son değerler bar grafiği
    this.createLatestValuesChart();
    
    // İstatistik kartları
    this.createStatisticCards();
    
    // Tabloyu göster
    this.displayTable();
  }

  createTimeSeriesChart() {
    const canvas = document.getElementById("timeSeriesChart");
    if (!canvas) return;

    this.updateSelectedFeatures();

    // Verileri hazırla
    const labels = this.data.data.map((row) => {
      const date = new Date(row.t_rec_dt);
      return date.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
    });

    const datasets = this.selectedFeatures.map((feature, index) => {
      const values = this.data.data.map((row) => parseFloat(row[feature]) || 0);
      
      return {
        label: feature,
        data: values,
        borderColor: this.getColor(index),
        backgroundColor: this.getColor(index, 0.1),
        borderWidth: 2,
        tension: 0.4,
        fill: false,
      };
    });

    // Eski chart'ı sil
    if (this.charts.timeSeries) {
      this.charts.timeSeries.destroy();
    }

    const ctx = canvas.getContext("2d");
    this.charts.timeSeries = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          title: {
            display: true,
            text: " Zaman Serisi Veriler",
            font: { size: 14, weight: "bold" },
            color: "#fff",
          },
          legend: {
            display: true,
            labels: { color: "#fff", font: { size: 12 } },
          },
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 255, 255, 0.1)" },
            ticks: { color: "#fff", maxRotation: 45 },
          },
          y: {
            grid: { color: "rgba(255, 255, 255, 0.1)" },
            ticks: { color: "#fff" },
          },
        },
      },
    });
  }

  createLatestValuesChart() {
    const canvas = document.getElementById("latestValuesChart");
    if (!canvas || !this.data?.data || this.data.data.length === 0) return;

    this.updateSelectedFeatures();
    const lastRow = this.data.data[this.data.data.length - 1];

    const labels = this.selectedFeatures;
    const values = this.selectedFeatures.map((feature) => parseFloat(lastRow[feature]) || 0);

    if (this.charts.latestValues) {
      this.charts.latestValues.destroy();
    }

    const ctx = canvas.getContext("2d");
    this.charts.latestValues = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "En Son Değerler",
            data: values,
            backgroundColor: this.selectedFeatures.map((_, i) => this.getColor(i, 0.7)),
            borderColor: this.selectedFeatures.map((_, i) => this.getColor(i)),
            borderWidth: 2,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          title: {
            display: true,
            text: " En Son Veriler",
            font: { size: 14, weight: "bold" },
            color: "#fff",
          },
          legend: {
            display: true,
            labels: { color: "#fff" },
          },
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 255, 255, 0.1)" },
            ticks: { color: "#fff" },
          },
          y: {
            grid: { color: "rgba(255, 255, 255, 0.1)" },
            ticks: { color: "#fff" },
          },
        },
      },
    });
  }

  createStatisticCards() {
    const container = document.getElementById("statisticCardsContainer");
    if (!container || !this.data?.feature_columns) return;

    container.innerHTML = "";

    // İlk 24 feature'ı al (daha çok veri göstermek için)
    const features = this.data.feature_columns.slice(0, 24);
    let cardsCreated = 0;

    features.forEach((feature) => {
      // 0 olmayan ve NaN olmayan değerleri al (anlamsız veriler filtrelendi)
      const values = this.data.data
        .map((row) => parseFloat(row[feature]))
        .filter((v) => !isNaN(v) && v !== 0); // 0 ve NaN'ı kaldır

      // Eğer anlamlı değer yoksa bu özelliği atla
      if (values.length === 0) return;

      const min = Math.min(...values);
      const max = Math.max(...values);
      const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);
      const latest = values[values.length - 1].toFixed(2);

      const card = document.createElement("div");
      card.className = "stat-card hot-card";
      card.innerHTML = `
        <h4>${feature}</h4>
        <div class="stat-row">
          <span>Son Değer:</span>
          <strong>${latest}</strong>
        </div>
        <div class="stat-row">
          <span>Ortalama:</span>
          <strong>${avg}</strong>
        </div>
        <div class="stat-row">
          <span>Min/Max:</span>
          <strong>${min.toFixed(2)} / ${max.toFixed(2)}</strong>
        </div>
      `;

      container.appendChild(card);
      cardsCreated++;
    });

    // Hiç kart oluşturulamamışsa mesaj göster
    if (cardsCreated === 0) {
      const msg = document.createElement("div");
      msg.style.gridColumn = "1 / -1";
      msg.style.textAlign = "center";
      msg.style.color = "#ffe0c1";
      msg.style.padding = "30px";
      msg.textContent = "ℹ️ Anlamlı veri bulunamadı (0 ve NaN değerler filtrelendi)";
      container.appendChild(msg);
    }
  }

  getColor(index, alpha = 1) {
    const colors = [
      `rgba(255, 122, 0, ${alpha})`,   // Orange (primary)
      `rgba(255, 195, 70, ${alpha})`,   // Light orange
      `rgba(255, 90, 0, ${alpha})`,     // Dark orange
      `rgba(100, 200, 255, ${alpha})`,  // Blue
      `rgba(100, 255, 150, ${alpha})`,  // Green
      `rgba(255, 100, 150, ${alpha})`,  // Pink
      `rgba(200, 150, 255, ${alpha})`,  // Purple
      `rgba(255, 255, 100, ${alpha})`,  // Yellow
    ];
    return colors[index % colors.length];
  }

  updateCharts() {
    if (this.charts.timeSeries) {
      this.createTimeSeriesChart();
    }
    if (this.charts.latestValues) {
      this.createLatestValuesChart();
    }
  }

  async manualRefresh() {
    console.log(" El ile yenileme başlatılıyor...");
    const btn = document.getElementById("refreshDataBtn");
    if (btn) btn.disabled = true;

    const success = await this.loadData();
    if (success) {
      this.createCharts();
      console.log("✅ Veriler yenilendi");
    }

    if (btn) btn.disabled = false;
  }

  startAutoRefresh() {
    // Her 5 dakikada bir otomatik yenile
    this.refreshInterval = setInterval(() => {
      console.log("Otomatik yenileme...");
      this.manualRefresh();
    }, 5 * 60 * 1000);
  }

  showError(message) {
    const errorDiv = document.getElementById("errorMessage");
    if (errorDiv) {
      errorDiv.textContent = `❌ ${message}`;
      errorDiv.style.display = "block";
    } else {
      alert(`❌ Hata: ${message}`);
    }
  }

  // TABLO FONKSİYONLARI
  setupTable() {
    if (!this.data?.feature_columns) return;

    const thead = document.querySelector(".data-table thead tr");
    if (!thead) return;

    // İlk iki th'yi (HARPNUM, Zaman) koru, geri kalanını sil
    while (thead.children.length > 2) {
      thead.removeChild(thead.lastChild);
    }

    // Her feature için ayrı <th> elemanı oluştur
    this.data.feature_columns.slice(0, 15).forEach((feature) => {
      const th = document.createElement("th");
      th.textContent = feature;
      thead.appendChild(th);
    });
  }

  setupTableData() {
    if (!this.data?.data) return;
    this.filteredData = [...this.data.data];
    this.currentPage = 1;
  }

  displayTable() {
    console.log("📋 Tablo gösteriliyor. Feature sütunları:", this.data?.feature_columns?.length);
    
    if (!this.data?.feature_columns) {
      console.warn("⚠️ Feature columns yok!");
      return;
    }

    const tbody = document.getElementById("tableBody");
    if (!tbody) {
      console.error("❌ tableBody elementi bulunamadı!");
      return;
    }

    const startIdx = (this.currentPage - 1) * this.rowsPerPage;
    const endIdx = startIdx + this.rowsPerPage;
    const pageData = this.filteredData.slice(startIdx, endIdx);

    console.log(`Sayfa ${this.currentPage}: ${startIdx}-${endIdx}, ${pageData.length} satır`);

    tbody.innerHTML = "";

    if (pageData.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td colspan="20" style="text-align: center; padding: 20px; color: #ffe0c1;">Eşleşen veri bulunamadı</td>`;
      tbody.appendChild(tr);
      return;
    }

    pageData.forEach((row) => {
      const tr = document.createElement("tr");
      
      // HARPNUM
      const harpnum = row.HARPNUM || "N/A";
      
      // Zaman
      const date = new Date(row.t_rec_dt);
      const timeStr = date.toLocaleTimeString("tr-TR", { 
        year: "2-digit", 
        month: "2-digit", 
        day: "2-digit",
        hour: "2-digit", 
        minute: "2-digit" 
      });

      tr.innerHTML = `<td>${harpnum}</td><td>${timeStr}</td>`;

      // Feature değerleri
      this.data.feature_columns.slice(0, 15).forEach((feature) => {
        const value = row[feature];
        const displayValue = value === null || value === undefined 
          ? "N/A" 
          : parseFloat(value).toFixed(2);
        tr.innerHTML += `<td>${displayValue}</td>`;
      });

      tbody.appendChild(tr);
    });

    // Pagination güncelle
    this.updatePagination();
  }

  updatePagination() {
    const totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);
    const pageInfo = document.getElementById("pageInfo");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    if (pageInfo) {
      pageInfo.textContent = `Sayfa ${this.currentPage} / ${totalPages}`;
    }

    if (prevBtn) {
      prevBtn.disabled = this.currentPage === 1;
    }

    if (nextBtn) {
      nextBtn.disabled = this.currentPage >= totalPages;
    }
  }

  filterTableData(searchTerm) {
    console.log("🔍 Arama başladı:", searchTerm);
    console.log("Mevcut veri:", this.data);
    console.log("Mevcut data.data:", this.data?.data);
    
    if (!this.data?.data || this.data.data.length === 0) {
      console.warn("⚠️ Aranacak veri yok!");
      return;
    }

    const term = searchTerm.toLowerCase();
    console.log("Filtreleme terimi:", term);
    
    this.filteredData = this.data.data.filter((row) => {
      // HARPNUM kontrolü
      if (row.HARPNUM && row.HARPNUM.toString().toLowerCase().includes(term)) {
        return true;
      }
      
      // Zaman kontrolü
      if (row.t_rec_dt && row.t_rec_dt.toLowerCase().includes(term)) {
        return true;
      }
      
      // Tüm değerler içinde ara
      return Object.values(row).some((val) => {
        if (val === null || val === undefined) return false;
        return val.toString().toLowerCase().includes(term);
      });
    });

    console.log("✅ Sonuç sayısı:", this.filteredData.length);
    this.currentPage = 1;
    this.displayTable();
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.displayTable();
    }
  }

  nextPage() {
    const totalPages = Math.ceil(this.filteredData.length / this.rowsPerPage);
    if (this.currentPage < totalPages) {
      this.currentPage++;
      this.displayTable();
    }
  }

  destroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    Object.values(this.charts).forEach((chart) => {
      if (chart) chart.destroy();
    });
  }
}

// Sayfa yüklenince başlat
document.addEventListener("DOMContentLoaded", () => {
  window.dashboardCharts = new DashboardCharts();
});
