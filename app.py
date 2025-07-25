from flask import Flask, render_template, request, session, redirect, url_for
import json
import os

app = Flask(__name__)
app.secret_key = 'ThunderTalkToMe3Goreng122' # Ganti dengan kunci rahasia yang kuat untuk produksi

# --- Fungsi-fungsi Logika RIASEC (dari skrip Python sebelumnya) ---
def load_questions(filepath=r'riasec_questions.json'):
    """
    Memuat pertanyaan dari file JSON.
    """
    try:
        # Gunakan os.path.join untuk path yang benar di berbagai OS
        json_path = os.path.join(app.root_path, filepath)
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        return questions
    except FileNotFoundError:
        print(f"Error: File '{json_path}' not found. Pastikan file JSON berada di direktori yang benar.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Tidak dapat mendekode JSON dari '{json_path}'. Mohon periksa format file.")
        return None

def calculate_raw_scores(questions, user_answers):
    """
    Menghitung skor mentah untuk setiap kategori RIASEC (R, I, A, S, E, C).
    """
    raw_scores = {
        'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0
    }

    categorized_questions = {
        'R': [], 'I': [], 'A': [], 'S': [], 'E': [], 'C': []
    }
    for q in questions:
        category_prefix = q['id'][0]
        if category_prefix in categorized_questions:
            categorized_questions[category_prefix].append(q)

    for category, q_list in categorized_questions.items():
        total_category_score = 0
        for q in q_list:
            q_id = q['id']
            if q_id in user_answers:
                answers = user_answers[q_id]
                minat_score = answers.get('Minat', 0)
                confidence_score = answers.get('Kepercayaan Diri', 0)
                frequency_score = answers.get('Frekuensi', 0)
                total_category_score += (minat_score + confidence_score + frequency_score)
        raw_scores[category] = total_category_score
    return raw_scores

def normalize_scores(raw_scores):
    normalized_scores = {}
    min_score_raw = 36
    max_score_raw = 180
    divisor = max_score_raw - min_score_raw

    for category, score in raw_scores.items():
        normalized_score = ((score - min_score_raw) / divisor) * 100
        normalized_scores[category] = round(normalized_score, 1)
    return normalized_scores

def determine_riasec_profile(normalized_scores):
    sorted_scores = sorted(normalized_scores.items(), key=lambda item: item[1], reverse=True)
    
    max_score_category, max_score_value = sorted_scores[0]
    
    second_score_category, second_score_value = None, -1
    if len(sorted_scores) >= 2:
        second_score_category, second_score_value = sorted_scores[1]
    
    third_score_category, third_score_value = None, -1
    if len(sorted_scores) >= 3:
        third_score_category, third_score_value = sorted_scores[2]

    selisih_1_2 = max_score_value - second_score_value if second_score_value != -1 else float('inf')
    selisih_2_3 = second_score_value - third_score_value if third_score_value != -1 else float('inf')

    if max_score_value >= 80 and selisih_1_2 > 20:
        return f"1 Huruf ({max_score_category})"
    elif max_score_value >= 60 and selisih_1_2 > 20 and second_score_value < 50:
        return f"1 Huruf ({max_score_category})"
    elif max_score_value >= 65 and selisih_1_2 <= 20 and selisih_2_3 <= 15 and third_score_value >= 55:
        return f"3 Huruf ({max_score_category}{second_score_category}{third_score_category})"
    elif max_score_value >= 60 and selisih_1_2 <= 15 and second_score_value >= 50:
        return f"2 Huruf ({max_score_category}{second_score_category})"
    else:
        return f"1 Huruf ({max_score_category})"

# --- Rute Aplikasi Flask ---

@app.route('/', methods=['GET', 'POST'])
def index():
    questions = load_questions()
    if not questions:
        return "Gagal memuat pertanyaan. Pastikan riasec_questions.json ada dan formatnya benar.", 500

    num_questions_per_page = 12 # Tentukan berapa pertanyaan per halaman
    
    # Inisialisasi session jika belum ada
    if 'current_page' not in session:
        session['current_page'] = 0
        session['user_answers'] = {}
        session.modified = True # Penting untuk memberitahu Flask session telah diubah

    current_page = session.get('current_page', 0)
    user_answers = session.get('user_answers') # Ambil langsung dari session
    if user_answers is None: # Jika belum ada di session, inisialisasi
        user_answers = {}
        session['user_answers'] = user_answers # Simpan kembali ke session
        session.modified = True

    if request.method == 'POST':
        # Proses jawaban dari halaman saat ini
        for q in questions[current_page * num_questions_per_page : (current_page + 1) * num_questions_per_page]:
            q_id = q['id']
            minat = request.form.get(f'{q_id}_minat', type=int)
            confidence = request.form.get(f'{q_id}_confidence', type=int)
            frequency = request.form.get(f'{q_id}_frequency', type=int)

            # Validasi input (opsional, bisa lebih ketat di sini)
            if all(v is not None and 1 <= v <= 5 for v in [minat, confidence, frequency]):
                user_answers[q_id] = {
                    'Minat': minat,
                    'Kepercayaan Diri': confidence,
                    'Frekuensi': frequency
                }
            else:
                # Handle error: user didn't fill all fields or invalid input
                # Untuk penyederhanaan, kita bisa kembali ke halaman yang sama dengan pesan error
                # Atau menandai pertanyaan yang belum dijawab
                print(f"Validasi gagal untuk {q_id}: Minat={minat}, Confidence={confidence}, Frequency={frequency}")
                return render_template('main.html', 
                                       questions=questions[current_page * num_questions_per_page : (current_page + 1) * num_questions_per_page],
                                       current_page=current_page,
                                       total_pages=(len(questions) + num_questions_per_page - 1) // num_questions_per_page,
                                       error_message="Mohon lengkapi semua jawaban dengan nilai antara 1 dan 5.",
                                       user_answers_session=user_answers) # Kirimkan jawaban yang sudah ada

        session['user_answers'] = user_answers
        session['current_page'] += 1
        session.modified = True

        if session['current_page'] * num_questions_per_page >= len(questions):
            # Semua pertanyaan sudah dijawab, hitung hasil
            return redirect(url_for('results'))
        else:
            # Lanjut ke halaman berikutnya
            return redirect(url_for('index'))

    # Tampilkan pertanyaan untuk halaman saat ini (GET request atau setelah POST)
    start_index = current_page * num_questions_per_page
    end_index = start_index + num_questions_per_page
    questions_to_display = questions[start_index:end_index]

    total_pages = (len(questions) + num_questions_per_page - 1) // num_questions_per_page

    return render_template('main.html', 
                           questions=questions_to_display,
                           current_page=current_page,
                           total_pages=total_pages,
                           user_answers_session=user_answers) # Kirimkan jawaban yang sudah ada (untuk mengisi ulang form jika ada kembali ke halaman)

@app.route('/results')
def results():
    questions = load_questions()
    if not questions:
        return "Gagal memuat pertanyaan.", 500

    user_answers = session.get('user_answers', {})

    if len(user_answers) != len(questions):
        # Jika belum semua pertanyaan dijawab atau sesi hilang
        print("Sesi jawaban tidak lengkap atau hilang, mengarahkan kembali ke awal.")
        session.clear() # Bersihkan sesi
        return redirect(url_for('index'))

    raw_scores = calculate_raw_scores(questions, user_answers)
    normalized_scores = normalize_scores(raw_scores)
    riasec_profile = determine_riasec_profile(normalized_scores)

    sorted_normalized_scores = sorted(normalized_scores.items(), key=lambda item: item[1], reverse=True)

    # Bersihkan sesi setelah menampilkan hasil jika assessment sudah selesai
    session.clear() 

    return render_template('results.html', 
                           raw_scores=raw_scores,
                           normalized_scores=normalized_scores,
                           riasec_profile=riasec_profile,
                           sorted_normalized_scores=sorted_normalized_scores)

@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Untuk menjalankan di lingkungan pengembangan:
    # app.run(debug=True)
    # Untuk menjalankan di lingkungan produksi, Anda mungkin perlu gunicorn atau sejenisnya
    app.run(debug=True, host='0.0.0.0', port=5000)