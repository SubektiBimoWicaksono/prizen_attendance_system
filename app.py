# --- Import library dan modul --- #
import os
import time
from datetime import date, datetime, timedelta

import cv2
import mysql.connector
import numpy as np
import pdfkit
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from PIL import Image

from flask_session import Session

# --- Konfigurasi Flask app --- #
app = Flask(__name__)
app.secret_key = "your_secret_key"

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["DEBUG"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# --- Format Tanggal --- #
hari = date.today().strftime("%A")
tanggal = date.today().strftime("%e %B %Y")  # misal 4 November 2022

# --- Koneksi ke database MySQL --- #
db = mysql.connector.connect(
    host="localhost", user="root", passwd="", database="prizen"
)
cursor = db.cursor()

# Konfigurasi path ke wkhtmltopdf
path_wkhtmltopdf = "static/wkhtmltopdf/bin/wkhtmltopdf.exe"

# Konfigurasi pdfkit
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


# ------- Bagian Fungsi Login ------------------------------------------------------ #


# --- Fungsi Login --- #
def login(username, password):
    cursor.execute(
        """SELECT role FROM user_data WHERE username = %s AND password = %s""",
        (username, password),
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    return None


# --- Fungsi untuk memeriksa apakah pengguna sudah login atau belum --- #
def is_logged_in():
    return "username" in session and "role" in session

def verify_face(img_id, wajah):
    # Fungsi ini seharusnya memverifikasi wajah pengguna dengan wajah yang terdaftar
    # Untuk contoh ini, kita akan mengembalikan True secara default
    # Implementasikan logika verifikasi wajah di sini menggunakan OpenCV atau library lainnya
    return True

# ------- Bagian Fungsi Utama ------------------------------------------------------ #


# --- Klasifikasi wajah --- #
face_detector = cv2.CascadeClassifier("static/haarcascade_frontalface_default.xml")


# --- Fungsi untuk menghasilkan dataset wajah ---#
def generate_dataset(nip):
    def face_cropped(img, faces):
        cropped_faces = []
        for x, y, w, h in faces:
            cropped_face = img[y : y + h, x : x + w]
            cropped_faces.append(cropped_face)
        return cropped_faces

    wCam, hCam = 400, 400

    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    cursor.execute("SELECT ifnull(max(img_id), 0) from img_dataset")
    row = cursor.fetchone()
    img_id = row[0]

    max_imgid = img_id + 10
    count_img = 0

    # Create directory if it doesn't exist
    dataset_dir = os.path.join("static", "dataset")
    os.makedirs(dataset_dir, exist_ok=True)

    while True:
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 8)

        if len(faces) > 0:
            for x, y, w, h in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (19, 57, 189), 2)

            count_img += 1
            img_id += 1
            cropped_faces = face_cropped(img, faces)

            # i == untuk mengiterasi melalui wajah-wajah yang terdeteksi dalam frame kamera
            for i, face in enumerate(cropped_faces):
                face_resized = cv2.resize(face, (100, 100))
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)

                filename = f"{nip}.{img_id}.jpg"
                path = os.path.join(dataset_dir, filename)
                cv2.imwrite(path, face_gray)

                cv2.putText(
                    img,
                    str(count_img) + "/10",
                    (x - 10, y - 10),
                    cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    0.7,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

                cursor.execute(
                    """INSERT INTO `img_dataset` (`img_id`, `wajah`) VALUES (%s, %s)""",
                    (img_id, nip),
                )
                db.commit()

            frame = cv2.imencode(".jpg", img)[1].tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

        if cv2.waitKey(1) == 13 or int(img_id) == int(max_imgid):
            break

    cap.release()
    cv2.destroyAllWindows()


# --- Fungsi untuk memeriksa apakah waktu sekarang berada di antara jam masuk dan jam pulang --- #
def is_within_time_range():
    now = datetime.now()
    current_time = now.time()

    cursor.execute("SELECT * FROM jam_absen WHERE jam_id = %s", (1,))
    result = cursor.fetchone()
    # clock_in = result[1]
    # clock_out = result[2]
    in_min_delta = result[3]
    out_max_delta = result[6]

    # Menghitung waktu pulang berdasarkan jam saat ini
    out_max = (now - out_max_delta).time()
    in_min = (now - in_min_delta).time()

    if current_time >= in_min and current_time <= out_max:
        return True
    return False


def face_recognition():
    def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, lbph):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        wajah = face_detector.detectMultiScale(gray, scaleFactor, minNeighbors)

        koord = []

        for x, y, w, h in wajah:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            id, pred = lbph.predict(gray[y : y + h, x : x + w])
            max = 700
            confidence = int(100 * (1 - pred / max))

            if confidence > 70:
                # Mengambil data pengguna berdasarkan id pegawai yang terdeteksi
                cursor.execute(
                    "SELECT a.wajah, b.nama_pegawai "
                    "FROM img_dataset a "
                    "LEFT JOIN user_data b ON a.wajah = b.nip "
                    "WHERE img_id = %s",
                    (id,),
                )
                row = cursor.fetchone()

                if row is not None:
                    nip = row[0]
                    nama_pegawai = row[1]

                    # Memeriksa apakah absensi pada tanggal tersebut sudah ada
                    query = "SELECT COUNT(*) FROM riwayat_absensi WHERE tgl_absen = %s AND id_pegawai = %s AND id_jam = %s"
                    values = (date.today(), nip, 1)
                    cursor.execute(query, values)
                    record_count = cursor.fetchone()[0]

                    # Jika belum ada absensi pada tanggal tersebut, maka simpan riwayat absensi
                    if record_count == 0:
                        # Maka insert waktu masuk ke db
                        cursor.execute(
                            "INSERT INTO riwayat_absensi (id_jam, tgl_absen, id_pegawai, waktu_masuk, waktu_pulang) VALUES (%s, %s, %s, %s, %s)",
                            (
                                1,
                                str(date.today()),
                                nip,
                                datetime.now().strftime("%H:%M:%S"),
                                "Belum Absen",
                            ),
                        )
                        db.commit()

                        cv2.putText(
                            img,
                            f"{nama_pegawai} | {confidence}%",
                            (x - 10, y - 10),
                            cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            0.7,
                            (255, 255, 255),
                            1,
                            cv2.LINE_AA,
                        )
                        time.sleep(1)

                    else:
                        # Update waktu_pulang ke database
                        cursor.execute(
                            "UPDATE riwayat_absensi SET waktu_pulang = %s WHERE tgl_absen = %s AND id_pegawai = %s AND id_jam = %s",
                            (
                                datetime.now().strftime("%H:%M:%S"),
                                str(date.today()),
                                nip,
                                1,
                            ),
                        )
                        db.commit()

                        cv2.putText(
                            img,
                            # "Anda Sudah Absen"
                            f"{nama_pegawai} | {confidence}%",
                            (x - 10, y - 10),
                            cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            0.7,
                            (255, 255, 255),
                            1,
                            cv2.LINE_AA,
                        )
                else:
                    cv2.putText(
                        img,
                        "Belum ada foto",
                        (x, y - 5),
                        cv2.FONT_HERSHEY_COMPLEX_SMALL,
                        0.7,
                        (255, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )
            else:
                cv2.putText(
                    img,
                    "UNKNOWN",
                    (x, y - 5),
                    cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    0.7,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )

            koord = [x, y, w, h]
        return img, koord


    def recognize(img, lbph, face_detector):
        ## draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, lbph)
        koord = draw_boundary(img, face_detector, 1.3, 8, (19, 57, 189), "Face", lbph)
        return img

    # Membaca model klasifikasi wajah dari file XML
    lbph = cv2.face.LBPHFaceRecognizer_create()
    # lbph.read("static/classifier.xml")
    classifier_file = "static/classifier.xml"

    if os.path.isfile(classifier_file):
        lbph.read(classifier_file)

        wCam, hCam = 400, 400

        cap = cv2.VideoCapture(0)
        cap.set(3, wCam)
        cap.set(4, hCam)

        while True:
            ret, img = cap.read()
            img = recognize(img, lbph, face_detector)

            if is_within_time_range():
                img = recognize(img, lbph, face_detector)
            else:
                cv2.putText(
                    img,
                    "Bukan Waktu Absen",
                    (15, 25),
                    cv2.FONT_HERSHEY_COMPLEX_SMALL,
                    0.7,
                    (19, 57, 189),
                    1,
                    cv2.LINE_AA,
                )

            frame = cv2.imencode(".jpg", img)[1].tobytes()
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
            )

            key = cv2.waitKey(1)
            if key == 27:  # tombol Esc
                break
    else:
        img = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.putText(
            img,
            "Blm ambil foto.",
            (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        frame = cv2.imencode(".jpg", img)[1].tobytes()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")


# ------- Bagian Routing ----------------------------------------------------------- #


# --- Tampilan halaman login --- #
@app.route("/")
def login_page():
    return render_template("login.html")


# --- Proses login --- #
@app.route("/login_submit", methods=["POST"])
def login_submit():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        role = login(username, password)

        if role == "Admin" or role == "Pegawai":
            cursor.execute(
                """SELECT nama_pegawai FROM user_data WHERE username = %s""",
                (username,),
            )
            result = cursor.fetchone()
            if result:
                nama_pegawai = result[0]
                session["username"] = username
                session["role"] = role
                session["nama_pegawai"] = nama_pegawai
                if role == "Admin":
                    return redirect(url_for("dashboard_admin"))
                elif role == "Pegawai":
                    return redirect(url_for("dashboard_pegawai"))
            else:
                flash("Username atau password salah!", "error")  # Tambahkan pesan error
                return redirect(url_for("login_page"))
        else:
            flash("Username atau password salah!", "error")  # Tambahkan pesan error
            return redirect(url_for("login_page"))
    return render_template("login.html")


# --- Logout --- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ------- Bagian Admin ----------------------------------------------------------- #


# --- Tampilan halaman Dashboard Admin --- #
@app.route("/dashboard_admin")
def dashboard_admin():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    # Menghitung total yang sudah face recognition
    cursor.execute(
        """
        SELECT COUNT(*) FROM riwayat_absensi
        WHERE tgl_absen = CURDATE()
        AND id_pegawai IN (
            SELECT wajah FROM img_dataset
            WHERE wajah IN (SELECT nip FROM user_data WHERE role = 'Pegawai')
        )
        """
    )
    total_recognized = cursor.fetchone()[0]

    # Total pegawai
    cursor.execute("SELECT COUNT(*) FROM user_data WHERE role = 'Pegawai'")
    total_pegawai = cursor.fetchone()[0]

    # Menghitung total yang belum melakukan face recognition
    total_unrecognized = total_pegawai - total_recognized

    # Menghitung jumlah surat izin
    cursor.execute("SELECT COUNT(*) FROM data_izin")
    total_surat_izin = cursor.fetchone()[0]

    return render_template(
        "admin/dashboard.html",
        hari=hari,
        tanggal=tanggal,
        total_pegawai=total_pegawai,
        total_recognized=total_recognized,
        total_unrecognized=total_unrecognized,
        total_surat_izin=total_surat_izin,
    )




# --- Tampilan halaman profil --- #
@app.route("/profile")
def profile():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    cursor.execute(
        "SELECT * FROM user_data WHERE username = %s", (session["username"],)
    )
    data = cursor.fetchone()
    id_data = data[0]
    username = data[1]
    password = data[2]
    email = data[3]
    nip = data[4]
    nama = data[5]
    role = data[6]

    session["nama_pegawai"] = nama

    return render_template(
        "admin/profile.html",
        data=data,
        id_data=id_data,
        username=username,
        password=password,
        email=email,
        nip=nip,
        nama=nama,
        role=role,
    )


# --- Tampilan halaman edit profil --- #
@app.route("/edit_profil")
def edit_profil():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    cursor.execute(
        "SELECT * FROM user_data WHERE username = %s", (session["username"],)
    )
    data = cursor.fetchone()
    id_data = data[0]
    username = data[1]
    password = data[2]
    email = data[3]
    nip = data[4]
    nama = data[5]
    role = data[6]

    return render_template(
        "admin/edit_profil.html",
        data=data,
        id_data=id_data,
        username=username,
        password=password,
        email=email,
        nip=nip,
        nama=nama,
        role=role,
    )


# --- Proses edit profil --- #
@app.route("/profil_submit", methods=["POST"])
def profil_submit():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    id_data = request.form.get("id_data")
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    nip = request.form.get("nip")
    nama_pegawai = request.form.get("nama")
    role = request.form.get("role")

    cursor.execute(
        "SELECT username FROM user_data WHERE username = %s AND id_data != %s",
        (username, id_data),
    )
    existing_username = cursor.fetchone()
    if existing_username:
        flash("Username sudah ada yang pakai", "danger")
        return redirect(url_for("edit_user", id_data=id_data))

    cursor.execute(
        """UPDATE `user_data` SET  `username` = %s, `password` = %s, `email` = %s, `nip` = %s, `nama_pegawai` = %s, `role` = %s WHERE `id_data` = %s""",
        (
            username,
            password,
            email,
            nip,
            nama_pegawai,
            role,
            id_data,
        ),
    )
    db.commit()

    session["username"] = username  # Menyimpan username baru ke dalam session

    flash("Data user berhasil diedit!", "success")
    return redirect(url_for("profile"))


# --- Tampilan halaman menu absensi == riwayat absensi --- #
@app.route("/data_absen", methods=["GET", "POST"])
def data_absen():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Ambil data absensi dari database berdasarkan rentang tanggal
        cursor.execute(
            "SELECT a.absen_id, a.tgl_absen, c.nip, c.nama_pegawai, a.id_pegawai, a.waktu_masuk, a.waktu_pulang, b.clock_in, b.clock_out, b.in_min, b.in_max, b.out_min, b.out_max "
            "FROM riwayat_absensi a "
            "INNER JOIN user_data c ON a.id_pegawai = c.nip "
            "INNER JOIN jam_absen b ON a.id_jam = b.jam_id "
            "WHERE a.tgl_absen BETWEEN %s AND %s "
            "ORDER BY a.tgl_absen DESC",
            (start_date, end_date),
        )
        data = cursor.fetchall()

        # Render template tabel riwayat absensi sebagai HTML
        rendered_template = render_template(
            "admin/hasil_filter.html",
            data=data,
        )

        if request.form.get("cetak"):
            curr_time = datetime.now().strftime("%H:%M:%S")
            curr_date = date.today()

            rendered_pdf = render_template(
                "admin/tabel_pdf.html",
                data=data,
                start_date=start_date,
                end_date=end_date,
                curr_time=curr_time,
                curr_date=curr_date,
            )
            pdf = pdfkit.from_string(rendered_pdf, False, configuration=config)

            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers[
                "Content-Disposition"
            ] = "attachment; filename=data_absen.pdf"

            return response

        return rendered_template

    cursor.execute(
        "SELECT a.absen_id, a.tgl_absen, c.nip, c.nama_pegawai, a.id_pegawai, a.waktu_masuk, a.waktu_pulang, b.clock_in, b.clock_out, b.in_min, b.in_max, b.out_min, b.out_max "
        "FROM riwayat_absensi a "
        "INNER JOIN user_data c ON a.id_pegawai = c.nip "
        "INNER JOIN jam_absen b ON a.id_jam = b.jam_id "
        # " WHERE a.tgl_absen = curdate() "
        "ORDER BY a.tgl_absen DESC",
    )
    data = cursor.fetchall()

    cursor.execute("SELECT * FROM jam_absen WHERE jam_id = %s", (1,))
    jam = cursor.fetchone()
    clock_in = jam[1]
    clock_out = jam[2]
    in_min = jam[3]
    in_max = jam[4]
    out_min = jam[5]
    out_max = jam[6]

    return render_template(
        "admin/data_absen.html",
        data=data,
        clock_in=clock_in,
        clock_out=clock_out,
        in_min=in_min,
        in_max=in_max,
        out_min=out_min,
        out_max=out_max,
    )


# --- Tampilan halaman edit jam absen --- #
@app.route("/edit_jam_absen")
def edit_jam_absen():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    cursor.execute("SELECT * FROM jam_absen WHERE jam_id = %s", (1,))
    data = cursor.fetchone()
    jam_id = data[0]
    clock_in = data[1]
    clock_out = data[2]
    in_min = data[3]
    in_max = data[4]
    out_min = data[5]
    out_max = data[6]

    return render_template(
        "admin/edit_jam_absen.html",
        data=data,
        jam_id=jam_id,
        clock_in=clock_in,
        clock_out=clock_out,
        in_min=in_min,
        in_max=in_max,
        out_min=out_min,
        out_max=out_max,
    )


# --- Proses edit jam absen --- #
@app.route("/jam_submit", methods=["POST"])
def jam_submit():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    jam_id = request.form.get("jam_id")
    clock_in = request.form.get("clock_in")
    clock_out = request.form.get("clock_out")
    in_min = request.form.get("in_min")
    in_max = request.form.get("in_max")
    out_min = request.form.get("out_min")
    out_max = request.form.get("out_max")

    cursor.execute(
        """UPDATE `jam_absen` SET  `clock_in` = %s, `clock_out` = %s, `in_min` = %s, `in_max` = %s, `out_min` = %s, `out_max` = %s WHERE `jam_id` = %s""",
        (
            clock_in,
            clock_out,
            in_min,
            in_max,
            out_min,
            out_max,
            1,
        ),
    )
    db.commit()

    flash("Jam absen berhasil diedit!", "success")
    return redirect(url_for("data_absen"))


# --- Tampilan halaman data pengguna --- #
@app.route("/data_user")
def data_user():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    cursor.execute("SELECT * FROM user_data")
    data = cursor.fetchall()

    deleted_message = session.pop(
        "deleted_message", None
    )  # Retrieve the message from the session

    return render_template(
        "admin/data_user.html",
        deleted_message=deleted_message,
        data=data,
    )
    
@app.route("/data_izin")
def data_izin():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    cursor = db.cursor()

    cursor.execute("SELECT izin_id, nama_pegawai, email_izin, keterangan, tanggal_kehadiran, surat_filename FROM data_izin")
    data = cursor.fetchall()

    deleted_message = session.pop("deleted_message", None)  # Retrieve the message from the session

    return render_template(
        "admin/data_izin.html",
        deleted_message=deleted_message,
        data=data,
    )

    
@app.route("/tambah_surat")
def tambah_surat():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    return render_template(
        "pegawai/tambah_surat.html",
    )
    
# --- Tampilan halaman registrasi pengguna --- #
@app.route("/tambah_user")
def tambah_user():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    return render_template(
        "admin/tambah_user.html",
    )

    # --- Proses Tambah surat izin --- #
@app.route("/tambah_izin", methods=["POST"])
def tambah_izin():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    nama_pegawai = request.form.get("nama")
    email = request.form.get("email")
    keterangan = request.form.get("role")  # Mengubah menjadi 'role' sesuai dengan formulir HTML
    tanggal_ketidakhadiran = request.form.get("tanggal_ketidakhadiran")
    surat = request.files["surat"]

    # Lakukan validasi atau operasi lain yang diperlukan
    if not nama_pegawai or not keterangan or not tanggal_ketidakhadiran or not surat:
        flash("Semua field harus diisi!", "danger")
        return redirect(url_for("form_izin"))

    # Direktori penyimpanan surat
    dataizin_dir = os.path.join("static", "dataizin")
    os.makedirs(dataizin_dir, exist_ok=True)
    
    # Simpan surat ke server
    surat_path = os.path.join(dataizin_dir, surat.filename)
    surat.save(surat_path)

    # Pastikan Anda telah mendefinisikan variabel db sebelumnya
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO data_izin (nama_pegawai, email_izin, keterangan, tanggal_kehadiran, surat_filename) VALUES (%s, %s, %s, %s, %s)",
        (
            nama_pegawai,
            email,
            keterangan,
            tanggal_ketidakhadiran,
            surat.filename,
        ),
    )
    db.commit()

    flash("Surat izin berhasil ditambah!", "success")
    return redirect(url_for("tambah_surat"))

# --- Proses registrasi setelah mengisi form registrai --- #
@app.route("/tambah_submit", methods=["POST"])
def tambah_submit():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    nip = request.form.get("nip")
    nama_pegawai = request.form.get("nama")
    role = request.form.get("role")
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    # Cek panjang karakter untuk email, username, dan password
    if len(nip) < 16:
        flash("NIP harus memiliki minimal 16 karakter", "danger")
        return redirect(url_for("tambah_user"))
    elif len(username) < 6:
        flash("Username harus memiliki minimal 6 karakter", "danger")
        return redirect(url_for("tambah_user"))
    elif len(email) < 11:
        flash("Email harus memiliki minimal 11 karakter", "danger")
        return redirect(url_for("tambah_user"))
    elif len(password) < 6:
        flash("Password harus memiliki minimal 6 karakter", "danger")
        return redirect(url_for("tambah_user"))

    cursor.execute(
        "SELECT username FROM user_data WHERE username = %s",
        (username,),
    )
    existing_username = cursor.fetchone()
    if existing_username:
        flash("Username sudah ada yang pakai", "danger")
        return redirect(url_for("tambah_user"))

    cursor.execute(
        "INSERT INTO user_data (nip, nama_pegawai, role, username, password, email) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            nip,
            nama_pegawai,
            role,
            username,
            password,
            email,
        ),
    )
    db.commit()

    flash("Data user berhasil ditambah!", "success")
    return redirect(
        url_for(
            "data_user",
        )
    )


# --- Tampilan halaman edit pengguna --- #
@app.route("/edit_user/<id>")
def edit_user(id):
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    cursor.execute("SELECT * FROM user_data WHERE id_data = %s", (id,))
    data = cursor.fetchone()
    id_data = data[0]
    username = data[1]
    password = data[2]
    email = data[3]
    nip = data[4]
    nama = data[5]
    role = data[6]

    # Admin tidak bisa edit data pegawai yang nama, role, username, & password
    if session["role"] == "Admin" and role != "Pegawai":
        readonly = ""
    else:
        readonly = "readonly"

    return render_template(
        "admin/edit_user.html",
        data=data,
        id_data=id_data,
        username=username,
        password=password,
        email=email,
        nip=nip,
        nama=nama,
        role=role,
        readonly=readonly,
    )


# --- Proses edit data pengguna --- #
@app.route("/edit_submit", methods=["POST"])
def edit_submit():
    if not is_logged_in() or session["role"] != "Admin":
        return redirect(url_for("login_page"))

    id_data = request.form.get("id_data")
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    nip = request.form.get("nip")
    nama_pegawai = request.form.get("nama")
    role = request.form.get("role")

    # Cek panjang karakter untuk email, username, dan password
    if len(username) < 6:
        flash("Username harus memiliki minimal 6 karakter", "danger")
        return redirect(url_for("tambah_user"))
    elif len(email) < 11:
        flash("Email harus memiliki minimal 11 karakter", "danger")
        return redirect(url_for("tambah_user"))
    elif len(password) < 6:
        flash("Password harus memiliki minimal 6 karakter", "danger")
        return redirect(url_for("tambah_user"))

    cursor.execute(
        "SELECT username FROM user_data WHERE username = %s AND id_data != %s",
        (username, id_data),
    )
    existing_username = cursor.fetchone()
    if existing_username:
        flash("Username sudah ada yang pakai", "danger")
        return redirect(url_for("edit_user", id_data=id_data))

    cursor.execute(
        """UPDATE `user_data` SET  `username` = %s, `password` = %s, `email` = %s, `nip` = %s, `nama_pegawai` = %s, `role` = %s WHERE `id_data` = %s""",
        (
            username,
            password,
            email,
            nip,
            nama_pegawai,
            role,
            id_data,
        ),
    )
    db.commit()

    flash("Data user berhasil diedit!", "success")
    return redirect(url_for("data_user"))


# --- Hapus data pengguna --- #
@app.route("/hapus_user/<id>", methods=["POST"])
def hapus_user(id):
    # Mendapatkan id_data atau nip dari user yang akan dihapus
    cursor.execute("SELECT * FROM user_data WHERE id_data = %s", (id,))
    nip = cursor.fetchone()[4]

    # Menghapus data pada tabel riwayat_absensi yang terhubung dengan id_pegawai
    cursor.execute("DELETE FROM riwayat_absensi WHERE id_pegawai = %s", (nip,))
    db.commit()

    # Menghapus data pada tabel img_dataset yang terhubung dengan wajah pegawai
    cursor.execute("DELETE FROM img_dataset WHERE wajah = %s", (nip,))
    db.commit()

    # Menghapus data user pada tabel user_data
    cursor.execute("DELETE FROM user_data WHERE id_data = %s", (id,))
    db.commit()

    flash("Data user berhasil dihapus!", "success")
    session[
        "deleted_message"
    ] = "Data user berhasil dihapus!"  # Store the message in the session

    return jsonify({"message": "Data user berhasil dihapus."}), 200


# ------- Bagian Pegawai ----------------------------------------------------------- #


# --- Tampilan halaman Dashboard Pegawai --- #
@app.route("/dashboard_pegawai")
@app.route(
    "/dashboard_pegawai/<filter_type>"
)  # Tambahkan route dengan parameter filter_type
def dashboard_pegawai(
    filter_type=None,
):  # Tambahkan parameter filter_type dengan nilai default None
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    # Perhitungan total absensi dengan face recognition ---
    today = date.today()
    year = today.year
    month = today.month

    if filter_type == "This Month":
        absensi_query = "SELECT COUNT(*) FROM riwayat_absensi WHERE id_pegawai = (SELECT nip FROM user_data WHERE username = %s) AND YEAR(tgl_absen) = %s AND MONTH(tgl_absen) = %s"
        terlambat_query = "SELECT COUNT(*) FROM riwayat_absensi a INNER JOIN jam_absen b ON a.id_jam = b.jam_id AND a.waktu_masuk > b.in_max WHERE a.id_pegawai = (SELECT nip FROM user_data WHERE username = %s) AND YEAR(a.tgl_absen) = %s AND MONTH(a.tgl_absen) = %s"
        pulang_query = "SELECT COUNT(*) FROM riwayat_absensi a INNER JOIN jam_absen b ON a.id_jam = b.jam_id AND a.waktu_pulang < b.clock_out AND a.waktu_pulang > b.out_min WHERE a.id_pegawai = (SELECT nip FROM user_data WHERE username = %s) AND YEAR(a.tgl_absen) = %s AND MONTH(a.tgl_absen) = %s"
        params = (session["username"], year, month)
    elif filter_type == "This Year":
        absensi_query = "SELECT COUNT(*) FROM riwayat_absensi WHERE id_pegawai = (SELECT nip FROM user_data WHERE username = %s) AND YEAR(tgl_absen) = %s"
        terlambat_query = "SELECT COUNT(*) FROM riwayat_absensi a INNER JOIN jam_absen b ON a.id_jam = b.jam_id AND a.waktu_masuk > b.in_max WHERE a.id_pegawai = (SELECT nip FROM user_data WHERE username = %s) AND YEAR(a.tgl_absen) = %s"
        pulang_query = "SELECT COUNT(*) FROM riwayat_absensi a INNER JOIN jam_absen b ON a.id_jam = b.jam_id AND a.waktu_pulang < b.clock_out AND a.waktu_pulang > b.out_min WHERE a.id_pegawai = (SELECT nip FROM user_data WHERE username = %s) AND YEAR(a.tgl_absen) = %s"
        params = (session["username"], year)
    else:
        absensi_query = "SELECT COUNT(*) FROM riwayat_absensi WHERE id_pegawai = (SELECT nip FROM user_data WHERE username = %s)"
        terlambat_query = "SELECT COUNT(*) FROM riwayat_absensi a INNER JOIN jam_absen b ON a.id_jam = b.jam_id AND a.waktu_masuk > b.in_max WHERE a.id_pegawai = (SELECT nip FROM user_data WHERE username = %s)"
        pulang_query = "SELECT COUNT(*) FROM riwayat_absensi a INNER JOIN jam_absen b ON a.id_jam = b.jam_id AND a.waktu_pulang < b.clock_out AND a.waktu_pulang > b.out_min WHERE a.id_pegawai = (SELECT nip FROM user_data WHERE username = %s)"
        params = (session["username"],)

    cursor.execute(absensi_query, params)
    total_absensi = cursor.fetchone()[0]

    cursor.execute(terlambat_query, params)
    total_terlambat = cursor.fetchone()[0]

    cursor.execute(pulang_query, params)
    total_plg_awal = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM jam_absen WHERE jam_id = %s", (1,))
    data = cursor.fetchone()
    clock_in = data[1]
    clock_out = data[2]

    return render_template(
        "pegawai/dashboard.html",
        hari=hari,
        tanggal=tanggal,
        filter_type=filter_type,
        total_absensi=total_absensi,
        total_terlambat=total_terlambat,
        total_plg_awal=total_plg_awal,
        clock_in=clock_in,
        clock_out=clock_out,
    )


# --- Tampilan halaman profil --- #
@app.route("/profil")
def profil():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    cursor.execute(
        "SELECT * FROM user_data WHERE username = %s", (session["username"],)
    )
    data = cursor.fetchone()
    id_data = data[0]
    username = data[1]
    email = data[3]
    nip = data[4]
    nama = data[5]

    session["nama_pegawai"] = nama

    return render_template(
        "pegawai/profil.html",
        data=data,
        id_data=id_data,
        username=username,
        email=email,
        nip=nip,
        nama=nama,
    )


# --- Tampilan halaman edit profil --- #
@app.route("/edit_profil_peg")
def edit_profil_peg():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    cursor.execute(
        "SELECT * FROM user_data WHERE username = %s", (session["username"],)
    )
    data = cursor.fetchone()
    id_data = data[0]
    username = data[1]
    password = data[2]
    email = data[3]
    nip = data[4]
    nama = data[5]
    role = data[6]

    return render_template(
        "pegawai/edit_profil.html",
        data=data,
        id_data=id_data,
        username=username,
        password=password,
        email=email,
        nip=nip,
        nama=nama,
        role=role,
    )


# --- Proses edit profil --- #
@app.route("/profil_peg_submit", methods=["POST"])
def profil_peg_submit():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    id_data = request.form.get("id_data")
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    nip = request.form.get("nip")
    nama_pegawai = request.form.get("nama")
    role = request.form.get("role")

    # Cek panjang karakter untuk email, username, dan password
    if len(username) < 6:
        flash("Username harus memiliki minimal 6 karakter", "danger")
        return redirect(url_for("edit_profil_peg"))
    elif len(email) < 11:
        flash("Email harus memiliki minimal 11 karakter", "danger")
        return redirect(url_for("edit_profil_peg"))
    elif len(password) < 6:
        flash("Password harus memiliki minimal 6 karakter", "danger")
        return redirect(url_for("edit_profil_peg"))

    cursor.execute(
        "SELECT username FROM user_data WHERE username = %s AND id_data != %s",
        (username, id_data),
    )
    existing_username = cursor.fetchone()
    if existing_username:
        flash("Username sudah ada yang pakai", "danger")
        return redirect(url_for("edit_profil_peg"))

    cursor.execute(
        """UPDATE `user_data` SET  `username` = %s, `password` = %s, `email` = %s, `nip` = %s, `nama_pegawai` = %s, `role` = %s WHERE `id_data` = %s""",
        (
            username,
            password,
            email,
            nip,
            nama_pegawai,
            role,
            id_data,
        ),
    )
    db.commit()

    session["username"] = username  # Menyimpan username baru ke dalam session

    flash("Data Anda berhasil diedit!", "success")
    return redirect(url_for("profil"))


# --- Tampilan halaman menu absensi == riwayat absensi --- #
@app.route("/riwayat_absen", methods=["GET", "POST"])
def riwayat_absen():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Ambil data riwayat absensi dari database berdasarkan id pegawai dan rentang tanggal
        cursor.execute(
            "SELECT a.absen_id, a.tgl_absen, a.waktu_masuk, a.waktu_pulang, b.clock_in, b.clock_out, b.in_min, b.in_max, b.out_min, b.out_max, c.nama_pegawai, c.nip "
            "FROM riwayat_absensi a "
            "INNER JOIN user_data c ON a.id_pegawai = c.nip "
            "INNER JOIN jam_absen b ON a.id_jam = b.jam_id "
            "WHERE c.username = %s AND a.tgl_absen BETWEEN %s AND %s "
            "ORDER BY a.tgl_absen DESC",
            (session["username"], start_date, end_date),
        )
        data = cursor.fetchall()

        # Render template tabel riwayat absensi sebagai HTML
        rendered_template = render_template(
            "pegawai/hasil_filter.html",
            data=data,
        )

        if request.form.get("cetak"):
            # Ambil identitas pegawai
            cursor.execute(
                "SELECT c.nama_pegawai, c.nip "
                "FROM riwayat_absensi a "
                "INNER JOIN user_data c ON a.id_pegawai = c.nip "
                "INNER JOIN jam_absen b ON a.id_jam = b.jam_id "
                "WHERE c.username = %s AND a.tgl_absen BETWEEN %s AND %s "
                "ORDER BY a.tgl_absen DESC",
                (session["username"], start_date, end_date),
            )
            indent = cursor.fetchone()
            nama_pegawai = indent[0]
            nip = indent[1]

            curr_time = datetime.now().strftime("%H:%M:%S")
            curr_date = date.today()

            rendered_pdf = render_template(
                "pegawai/tabel_pdf.html",
                data=data,
                nama_pegawai=nama_pegawai,
                nip=nip,
                start_date=start_date,
                end_date=end_date,
                curr_time=curr_time,
                curr_date=curr_date,
            )
            pdf = pdfkit.from_string(rendered_pdf, False, configuration=config)

            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers[
                "Content-Disposition"
            ] = "attachment; filename=riwayat_absen.pdf"

            return response

        return rendered_template

    # Ambil data riwayat absensi dari database berdasarkan id pegawai
    cursor.execute(
        "SELECT a.absen_id, a.tgl_absen, a.waktu_masuk, a.waktu_pulang, b.clock_in, b.clock_out, b.in_min, b.in_max, b.out_min, b.out_max, c.nama_pegawai, c.nip "
        "FROM riwayat_absensi a "
        "INNER JOIN user_data c ON a.id_pegawai = c.nip "
        "INNER JOIN jam_absen b ON a.id_jam = b.jam_id "
        "WHERE c.username = %s "
        "ORDER BY a.tgl_absen DESC",
        (session["username"],),
    )
    data = cursor.fetchall()

    cursor.execute("SELECT * FROM jam_absen WHERE jam_id = %s", (1,))
    jam = cursor.fetchone()
    clock_in = jam[1]
    clock_out = jam[2]
    in_min = jam[3]
    in_max = jam[4]
    out_min = jam[5]
    out_max = jam[6]

    return render_template(
        "pegawai/riwayat_absen.html",
        data=data,
        clock_in=clock_in,
        clock_out=clock_out,
        in_min=in_min,
        in_max=in_max,
        out_min=out_min,
        out_max=out_max,
    )



# --- Tampilan halaman absen pegawai --- #
@app.route("/absensi", methods=["GET", "POST"])
def absensi():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    if request.method == "POST":
        if verify_face(session["username"]):
            # Lakukan proses presensi
            flash("Presensi berhasil.", "success")
            # Logika untuk mencatat presensi ke database
        else:
            flash("Wajah tidak sesuai dengan pemilik akun.", "danger")

    return render_template(
        "pegawai/absensi.html",
    )


# --- Tampilan kamera face recog. di halaman clock in --- #
@app.route("/kamera_absen")
def kamera_absen():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    # Video streaming route. Put this in the src attribute of an img tag
    return Response(
        face_recognition(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# --- Tampilan halaman dataset pegawai --- #
@app.route("/dataset")
def dataset():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    cursor.execute(
        "SELECT * FROM user_data WHERE username = %s", (session["username"],)
    )
    nip = cursor.fetchone()[4]
    session["nip"] = nip  # untuk pemanggilan pada kamera_train.html

    cursor.execute(
        "SELECT a.img_id, a.wajah "
        "FROM img_dataset a "
        "INNER JOIN user_data b ON a.wajah = b.nip "
        "WHERE b.username = %s",
        (session["username"],),
    )
    rows = cursor.fetchall()
    image_paths = []

    for row in rows:
        img_id = row[0]
        nip = row[1]  # nip = wajah
        # folder_path = "dataset/" + nip + "." + str(img_id) + ".jpg"
        folder_path = url_for("static", filename=f"dataset/{nip}.{img_id}.jpg")
        image_paths.append(folder_path)

    return render_template(
        "pegawai/dataset.html",
        image_paths=image_paths,
    )


# --- Tampilan halaman training pegawai --- #
@app.route("/kamera_train")
def kamera_train():
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    return render_template(
        "pegawai/kamera_train.html",
    )


# --- Tampilan kamera untuk mengambil dataset wajah --- #
@app.route("/video_train/<nip>")
def video_train(nip):
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    return Response(
        generate_dataset(nip), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# --- Training klasifikasi wajah dengan LBPH ---#
@app.route("/training_classifier/<nip>")
def training_classifier(nip):
    if not is_logged_in() or session["role"] != "Pegawai":
        return redirect(url_for("login_page"))

    dataset_dir = "static/dataset"

    path = [os.path.join(dataset_dir, file) for file in os.listdir(dataset_dir)]
    faces = []
    ids = []

    for image in path:
        img = Image.open(image).convert("L")
        imageNp = np.array(img, "uint8")
        id = int(os.path.split(image)[1].split(".")[1])

        faces.append(imageNp)
        ids.append(id)
    ids = np.array(ids)

    # Membuat objek LBPH dan mengatur parameter
    # lbph = cv2.face.LBPHFaceRecognizer_create()
    lbph = cv2.face.LBPHFaceRecognizer_create(
        radius=1, grid_x=8, grid_y=8, threshold=210
    )

    # Melakukan training dengan wajah-wajah yang telah dikumpulkan
    lbph.train(faces, ids)

    # Menyimpan model klasifikasi wajah
    lbph.write("static/classifier.xml")

    return redirect(url_for("dataset", nip=session["nip"]))


# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=5000, debug=True)
if __name__ == "__main__":
    app.run()
