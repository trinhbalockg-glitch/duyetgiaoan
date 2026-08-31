from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import html
from urllib.parse import quote_plus

app = FastAPI()

# Tạo CSDL SQLite tự động khi khởi chạy
def init_db():
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    # Bảng người dùng
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        fullname TEXT,
        role TEXT,
        department TEXT
    )''')
    # Bảng giáo án
    cursor.execute('''CREATE TABLE IF NOT EXISTS lesson_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name TEXT,
        department TEXT,
        week INTEGER,
        subject TEXT,
        file_link TEXT,
        status TEXT,
        feedback TEXT
    )''')
    
    # Thêm dữ liệu mẫu nếu bảng trống
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('gv_toan', 'Nguyễn Văn A', 'Giáo viên', 'Toán'),
            ('tt_toan', 'Trần Văn Trí', 'Tổ trưởng', 'Toán'),
            ('pht_toan', 'Trần Văn Trí', 'Phó Hiệu trưởng', 'Toán'),
            ('gv_van', 'Lê Thị B', 'Giáo viên', 'Văn - GDCD'),
            ('tt_van', 'Ngô Thanh Vũ', 'Tổ trưởng', 'Văn - GDCD')
        ]
        cursor.executemany("INSERT INTO users (username, fullname, role, department) VALUES (?, ?, ?, ?)", sample_users)
        
        # Thêm 1 giáo án mẫu
        cursor.execute("""INSERT INTO lesson_plans (teacher_name, department, week, subject, file_link, status, feedback) 
                          VALUES ('Nguyễn Văn A', 'Toán', 1, 'Toán 10', 'https://drive.google.com', 'Chờ Tổ trưởng duyệt', '')""")
    
    conn.commit()
    conn.close()

init_db()

# --- GIAO DIỆN WEB (HTML/CSS) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Duyệt Giáo Án</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f6f9; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        h2 {{ color: #2c3e50; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #007bff; color: white; }}
        .btn {{ padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; color: white; text-decoration: none; display: inline-block; }}
        .btn-green {{ background-color: #28a745; }}
        .btn-red {{ background-color: #dc3545; }}
        .btn-blue {{ background-color: #007bff; }}
        .status {{ font-weight: bold; padding: 4px 8px; border-radius: 4px; display: inline-block; }}
        .pending {{ background: #fff3cd; color: #856404; }}
        .approved {{ background: #d4edda; color: #155724; }}
        .rejected {{ background: #f8d7da; color: #721c24; }}
        input, select {{ width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


def _status_class(status_text: str) -> str:
    s = (status_text or "").lower()
    if "đã duyệt" in s or "hoàn tất" in s:
        return "approved"
    if "yêu cầu" in s or "trả lại" in s or "chỉnh sửa" in s or "từ chối" in s:
        return "rejected"
    # default: pending (covers "chờ ..." and others)
    return "pending"

@app.get("/", response_class=HTMLResponse)
def index():
    # Use quote_plus for safety when building links
    teacher_link = f"/dashboard?role={quote_plus('Giáo viên')}&user={quote_plus('Nguyễn Văn A')}&dept={quote_plus('Toán')}"
    tt_link = f"/dashboard?role={quote_plus('Tổ trưởng')}&user={quote_plus('Trần Văn Trí')}&dept={quote_plus('Toán')}"
    pht_link = f"/dashboard?role={quote_plus('Phó Hiệu Trưởng')}&user={quote_plus('Trần Văn Trí')}&dept={quote_plus('Toán')}"

    content = f"""
    <h2>HỆ THỐNG DUYỆT GIÁO ÁN DEMO</h2>
    <p>Chọn vai trò để trải nghiệm nhanh:</p>
    <ul>
        <li><a href=\"{teacher_link}\" class=\"btn btn-blue\">Đăng nhập vai trò GIÁO VIÊN (Toán)</a></li>
        <br>
        <li><a href=\"{tt_link}\" class=\"btn btn-blue\">Đăng nhập vai trò TỔ TRƯỞNG (Toán)</a></li>
        <br>
        <li><a href=\"{pht_link}\" class=\"btn btn-blue\">Đăng nhập vai trò PHÓ HIỆU TRƯỞNG (Phụ trách Tổ Toán)</a></li>
    </ul>
    """
    return HTML_LAYOUT.format(content=content)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(role: str, user: str, dept: str):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    # Escape user inputs before rendering into HTML
    esc_user = html.escape(user)
    esc_role = html.escape(role)
    esc_dept = html.escape(dept)

    content = f"<h3>Xin chào: {esc_user} ({esc_role} - Tổ {esc_dept})</h3><a href='/'>← Đăng xuất</a><hr>"
    
    # Form nộp bài cho Giáo viên
    if role == "Giáo viên":
        # Hidden inputs use the original values (server trusts them here), but we still escape when embedding
        content += """
        <h4>Nộp Giáo Án Mới</h4>
        <form action="/submit" method="post">
            <input type="hidden" name="teacher_name" value="{user}">
            <input type="hidden" name="department" value="{dept}">
            <label>Tuần thứ:</label><input type="number" name="week" value="1" required>
            <label>Môn học / Lớp:</label><input type="text" name="subject" placeholder="Ví dụ: Toán 10A1" required>
            <label>Link Google Drive bài dạy:</label><input type="url" name="file_link" placeholder="https://drive.google.com/..." required>
            <button type="submit" class="btn btn-green">Nộp Giáo Án</button>
        </form>
        <hr>
        ".format(user=html.escape(user), dept=html.escape(dept))
        
        cursor.execute("SELECT week, subject, file_link, status, feedback FROM lesson_plans WHERE teacher_name=?", (user,))
    else:
        # Danh sách duyệt cho Tổ trưởng / Ban Giám Hiệu
        cursor.execute("SELECT id, teacher_name, week, subject, file_link, status, feedback FROM lesson_plans WHERE department=?", (dept,))

    rows = cursor.fetchall()
    
    content += "<h4>Danh Sách Giáo Án</h4><table><tr><th>Giáo viên</th><th>Tuần / Môn</th><th>Link File</th><th>Trạng thái</th><th>Ghi chú / Nhận xét</th><th>Thao tác</th></tr>"
    
    for row in rows:
        if role == "Giáo viên":
            week, subject, link, status, feedback = row
            esc_subject = html.escape(str(subject))
            esc_link = html.escape(str(link))
            esc_status = html.escape(str(status))
            esc_feedback = html.escape(str(feedback))
            cls = _status_class(status)
            content += f"<tr><td>{esc_user}</td><td>Tuần {html.escape(str(week))} - {esc_subject}</td><td><a href='{esc_link}' target='_blank'>Xem File</a></td><td><span class='status {cls}'>{esc_status}</span></td><td>{esc_feedback}</td><td>-</td></tr>"
        else:
            plan_id, t_name, week, subject, link, status, feedback = row
            esc_t_name = html.escape(str(t_name))
            esc_subject = html.escape(str(subject))
            esc_link = html.escape(str(link))
            esc_status = html.escape(str(status))
            esc_feedback = html.escape(str(feedback))
            cls = _status_class(status)
            actions = ""
            if (role == "Tổ trưởng" and status == "Chờ Tổ trưởng duyệt") or (role == "Phó Hiệu trưởng" and status == "Chờ PHT duyệt"):
                actions = f"""
                <form action="/review" method="post" style="display:inline;">
                    <input type="hidden" name="plan_id" value="{plan_id}">
                    <input type="hidden" name="role" value="{esc_role}">
                    <input type="hidden" name="user" value="{esc_user}">
                    <input type="hidden" name="dept" value="{esc_dept}">
                    <input type="text" name="feedback" placeholder="Nhập nhận xét..." style="width:120px;">
                    <button type="submit" name="action" value="approve" class="btn btn-green">Duyệt</button>
                    <button type="submit" name="action" value="reject" class="btn btn-red">Trả lại</button>
                </form>
                """.format(plan_id=plan_id, esc_role=esc_role, esc_user=esc_user, esc_dept=esc_dept)
            content += f"<tr><td>{esc_t_name}</td><td>Tuần {html.escape(str(week))} - {esc_subject}</td><td><a href='{esc_link}' target='_blank'>Xem File</a></td><td><span class='status {cls}'>{esc_status}</span></td><td>{esc_feedback}</td><td>{actions}</td></tr>"
            
    content += "</table>"
    conn.close()
    return HTML_LAYOUT.format(content=content)

@app.post("/submit")
def submit_plan(teacher_name: str = Form(...), department: str = Form(...), week: int = Form(...), subject: str = Form(...), file_link: str = Form(...)):
    # Minimal validation: ensure week is positive and file_link is url-encoded in redirect
    if week < 1:
        week = 1

    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO lesson_plans (teacher_name, department, week, subject, file_link, status, feedback) 
                      VALUES (?, ?, ?, ?, ?, 'Chờ Tổ trưởng duyệt', '')""", (teacher_name, department, week, subject, file_link))
    conn.commit()
    conn.close()
    # URL-encode query params in redirect
    return RedirectResponse(url=f"/dashboard?role={quote_plus('Giáo viên')}&user={quote_plus(teacher_name)}&dept={quote_plus(department)}", status_code=303)

@app.post("/review")
def review_plan(plan_id: int = Form(...), role: str = Form(...), user: str = Form(...), dept: str = Form(...), action: str = Form(...), feedback: str = Form("")):
    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()
    
    if action == "approve":
        new_status = "Chờ PHT duyệt" if role == "Tổ trưởng" else "Đã duyệt hoàn tất"
    else:
        new_status = f"Yêu cầu chỉnh sửa (Bởi {role})"
        
    cursor.execute("UPDATE lesson_plans SET status=?, feedback=? WHERE id=?", (new_status, feedback, plan_id))
    conn.commit()
    conn.close()
    # URL-encode query params in redirect
    return RedirectResponse(url=f"/dashboard?role={quote_plus(role)}&user={quote_plus(user)}&dept={quote_plus(dept)}", status_code=303)
