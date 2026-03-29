from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.utils import is_session_active
import pandas as pd
from pathlib import Path

main_bp = Blueprint("main", __name__)

# SECURE_PAGES = ['dashboard']
# PUBLIC_PAGES = ['login', 'register', 'index']


@main_bp.route("/", methods=['GET'])
def index():
    return render_template("index.html")

@main_bp.route("/dashboard", methods=['GET'])
def dashboard():
    # if is_session_active():
    #     return render_template('dashboard.html')
    # return redirect('/login')
    return render_template('dashboard.html')

@main_bp.route("/info", methods=['GET'])
def info():
    return render_template('info.html')

@main_bp.route('/about', methods=['GET'])
def abouth():
    return render_template('about.html')

@main_bp.route('/api/clean-data', methods=['GET'])
def get_clean_data():
    """
    Temizlenen verilerin sütun adlarını ve son satırlarını döner.
    
    Query params:
    - rows: kaç satır dönsün (default: 10, 0 = tümü)
    - limit_samples: maksimum kaç örnek (batch) dönsün (default: 5)
    """
    try:
        rows = int(request.args.get('rows', 10))
        limit_samples = int(request.args.get('limit_samples', 5))
        
        # Temiz veri CSV dosyasını oku
        data_dir = Path(__file__).resolve().parent.parent / "data" / "clean_data"
        csv_file = data_dir / "data" / "tahmine_hazir_veri.csv"
        
        if not csv_file.exists():
            return jsonify({
                "status": "error",
                "message": "Temiz veri dosyası bulunamadı. Önce pipeline çalıştırın."
            }), 404
        
        # CSV oku
        df = pd.read_csv(csv_file)
        
        # Sütun adlarını al
        columns = df.columns.tolist()
        
        # Eğer rows=0 ise tümünü döndür, aksi takdirde son N satırı
        if rows == 0:
            data_rows = df.to_dict('records')
        else:
            data_rows = df.tail(rows).to_dict('records')
        
        # HARPNUM bazlı gruplayarak örnek al
        if limit_samples > 0:
            grouped = df.groupby('harpnum')
            harpnums = grouped.groups.keys()
            
            samples = []
            for i, harpnum in enumerate(list(harpnums)[:limit_samples]):
                group = grouped.get_group(harpnum)
                samples.append({
                    'harpnum': harpnum,
                    'count': len(group),
                    'latest_data': group.iloc[-1].to_dict()
                })
        else:
            samples = []
        
        return jsonify({
            "status": "success",
            "columns": columns,
            "total_rows": len(df),
            "returned_rows": len(data_rows),
            "data": data_rows,
            "samples_by_harpnum": samples,
            "feature_columns": [c for c in columns if c not in ['harpnum', 't_rec', 'noaa_ars', 't_rec_dt', 'fetched_at_utc']]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500