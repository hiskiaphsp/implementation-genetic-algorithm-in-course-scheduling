from flask import render_template, request, current_app
from werkzeug.utils import secure_filename
import os
from algorithm.schedule_algorithm import ScheduleGenerator

from app import app

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_temporary_upload_folder():
    return os.path.join(current_app.root_path, 'uploads')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Create a temporary upload folder if it doesn't exist
        upload_folder = get_temporary_upload_folder()
        os.makedirs(upload_folder, exist_ok=True)

        # Check if the post request has the file part
        if 'file_matakuliah' not in request.files or 'file_ruangan' not in request.files or 'file_waktu' not in request.files:
            # Handle error as needed
            return render_template('index.html', error="Please upload all required files.")

        file_matakuliah = request.files['file_matakuliah']
        file_ruangan = request.files['file_ruangan']
        file_waktu = request.files['file_waktu']

        # Validate file extensions
        if not allowed_file(file_matakuliah.filename) or not allowed_file(file_ruangan.filename) or not allowed_file(file_waktu.filename):
            # Handle error as needed
            return render_template('index.html', error="Invalid file format. Please upload CSV files only.")

        # Save the uploaded files to a temporary location
        filename_matakuliah = secure_filename(file_matakuliah.filename)
        filename_ruangan = secure_filename(file_ruangan.filename)
        filename_waktu = secure_filename(file_waktu.filename)

        file_matakuliah.save(os.path.join(upload_folder, filename_matakuliah))
        file_ruangan.save(os.path.join(upload_folder, filename_ruangan))
        file_waktu.save(os.path.join(upload_folder, filename_waktu))

        schedule_generator = ScheduleGenerator(
            os.path.join(upload_folder, filename_matakuliah),
            os.path.join(upload_folder, filename_ruangan),
            os.path.join(upload_folder, filename_waktu)
        )

        best_schedule = schedule_generator.genetic_algorithm(population_size=100, generations=50)
        schedule_list = schedule_generator.format_schedule(best_schedule)

        return render_template('index.html', schedule_list=schedule_list)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
