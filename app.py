from flask import Flask, render_template, request, jsonify, session, redirect
import pyodbc
import pymssql
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"  # Needed for session management

DB_CONFIGS = {
    "DB1": {
        # "DRIVER": "{SQL Server}",
        "SERVER": "115.78.235.164",
        "DATABASE": "EduManUni_CamauVKC",
        "UID": "vkc",
        "PWD": "daotaoVKC123"
    },
    "DB2": {
        # "DRIVER": "{SQL Server}",
        "SERVER": "115.78.235.164",
        "DATABASE": "Daotao_CamauVKC",
        "UID": "vkc",
        "PWD": "daotaoVKC123"
    }
}

# Get database connection based on session's current_db_key
def get_db_connection():
    current_db_key = session.get('current_db_key', 'DB1')  # Default to DB1 if not set
    cfg = DB_CONFIGS[current_db_key]
    conn = pymssql.connect(
        server = cfg['SERVER'],
        user = cfg['UID'],
        password = cfg['PWD'],
        database = cfg['DATABASE'],
        port = 1433
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_db = request.form.get('db_select')
        if selected_db in DB_CONFIGS:
            session['current_db_key'] = selected_db
        return redirect('/')

    current_db_key = session.get('current_db_key', 'DB1')
    conn = get_db_connection()
    cur = conn.cursor(as_dict=True)

    if current_db_key == 'DB2':
        cur.execute("SELECT MaL, Tenlop FROM Lop WHERE Ma_L_GDNN <> ''")
    else:
        cur.execute("SELECT MaL, Tenlop FROM Lop")

    lop_list = cur.fetchall()
    conn.close()
    return render_template("index.html", lop_list=lop_list, current_db_key=current_db_key)


@app.route('/api/get_sinhvien', methods=['GET'])
def api_get_sinhvien():
    malop = request.args.get('MaL')
    current_db_key = session.get('current_db_key', 'DB1')
    conn = get_db_connection()
    cur = conn.cursor(as_dict=True)

    if current_db_key == 'DB2':  # DB cũ
        cur.execute("""
            SELECT MaSV, Holot, Ten, CNTN AS Totnghiep, Sohieu, Sovaoso, DTBHT AS DTBTLBon, Ngayky
            FROM Sinhvien
            WHERE MaL = %s
            ORDER BY Ten, Holot
        """, (malop,))
    else:  # DB mới
        cur.execute("""
            SELECT MaSV, Holot, Ten, Totnghiep, Sohieu, Sovaoso, DTBTLBon, Ngayky
            FROM Sinhvien
            WHERE MaL = %s AND Tinhtrang IN (0,3)
            ORDER BY Ten, Holot
        """, (malop,))

    sv_list = [
        {
            "Maso": r["MaSV"],
            "Holot": r["Holot"],
            "Ten": r["Ten"],
            "Totnghiep": r["Totnghiep"],
            "Sohieu": r["Sohieu"] or "",
            "Sovaoso": r["Sovaoso"] or "",
            "DTBTLBon": r["DTBTLBon"],
            "Ngayky": r["Ngayky"].strftime("%d/%m/%Y") if r["Ngayky"] else None
        }
        for r in cur.fetchall()
    ]
    conn.close()
    return jsonify(sv_list)


@app.route('/api/update_totnghiep', methods=['POST'])
def api_update_totnghiep():
    data = request.json    
    masv_list = data.get("masv_list", [])
    malop = data.get('MaL')
    ma_qdtn = data.get('MaQDTN')
    
    if not malop or not ma_qdtn:
        return jsonify({"status": "error", "message": "Thiếu thông tin lớp hoặc quyết định"}), 400

    current_db_key = session.get('current_db_key', 'DB1')
    conn = get_db_connection()
    cur = conn.cursor(as_dict=True)

    # Lấy quyết định
    cur.execute("SELECT Nguoiky, Ngayky FROM QuyetdinhTN WHERE MaQDTN = %s", (ma_qdtn,))
    qd = cur.fetchone()
    if not qd:
        return jsonify({"status": "error", "message": "Không tìm thấy quyết định"}), 404

    nguoiky = qd["Nguoiky"]
    ngayky = qd["Ngayky"]

    cur = conn.cursor()  # update không cần as_dict
    for masv in masv_list:
        sohieu = masv.get("Sohieu") or None
        sovaoso = masv.get("Sovaoso") or None

        if current_db_key == 'DB2':  # DB cũ
            cur.execute("""
                UPDATE Sinhvien
                SET CNTN = 1,
                    MaQDTN = %s,
                    Nguoiky = %s,
                    Ngayky = %s,
                    Sohieu = %s,
                    Sovaoso = %s
                WHERE MaSV = %s
            """, (ma_qdtn, nguoiky, ngayky, sohieu, sovaoso, masv["Maso"]))
        else:  # DB mới
            cur.execute("""
                UPDATE Sinhvien
                SET Totnghiep = 1,
                    Tinhtrang = 3,
                    MaQDTN = %s,
                    Nguoiky = %s,
                    Ngayky = %s,
                    Sohieu = %s,
                    Sovaoso = %s
                WHERE MaSV = %s
            """, (ma_qdtn, nguoiky, ngayky, sohieu, sovaoso, masv["Maso"]))

    conn.commit()
    conn.close()
    return jsonify({"status": "success"})


@app.route('/api/quyetdinhtn')
def api_quyetdinhtn():
    current_db_key = session.get('current_db_key', 'DB1')
    conn = get_db_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT MaQDTN, So, Nguoiky, Ngayky, Noidung FROM QuyetdinhTN")
    rows = cur.fetchall()
    result = []
    for r in rows:
        result.append({
            "MaQDTN": r["MaQDTN"],
            "So": r["So"],
            "Nguoiky": r["Nguoiky"],
            "Ngayky": r["Ngayky"].strftime("%d/%m/%Y") if r["Ngayky"] else None,
            "Noidung": r["Noidung"]
        })
    conn.close()
    return jsonify(result)  


if __name__ == '__main__':
    app.run(debug=True)
