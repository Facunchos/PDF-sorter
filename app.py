import os
import re
import uuid
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, send_file, jsonify, request, abort, session
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Carpeta base donde se almacenan las sesiones
BASE_PDF_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')

# Configuración de sesiones
SESSION_LIFETIME = 3 * 24 * 60 * 60  # 3 días en segundos
CLEANUP_INTERVAL = 60 * 60  # Limpiar cada hora

# Caracteres prohibidos en nombres de archivo
FORBIDDEN_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

# Extensiones permitidas para upload
ALLOWED_EXTENSIONS = {'.pdf'}


def get_session_id():
    """Obtiene o crea un ID de sesión único para el usuario."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['created_at'] = time.time()
    
    # Actualizar último acceso
    session['last_access'] = time.time()
    return session['session_id']


def get_user_pdf_folder():
    """Obtiene la carpeta de PDFs específica del usuario."""
    session_id = get_session_id()
    user_folder = os.path.join(BASE_PDF_FOLDER, session_id)
    
    # Crear carpeta si no existe
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    return user_folder


def cleanup_old_sessions():
    """Limpia sesiones inactivas más antiguas que SESSION_LIFETIME."""
    try:
        if not os.path.exists(BASE_PDF_FOLDER):
            return
        
        current_time = time.time()
        for session_dir in os.listdir(BASE_PDF_FOLDER):
            session_path = os.path.join(BASE_PDF_FOLDER, session_dir)
            
            if os.path.isdir(session_path):
                # Verificar si la carpeta es muy antigua
                dir_mtime = os.path.getmtime(session_path)
                if current_time - dir_mtime > SESSION_LIFETIME:
                    import shutil
                    shutil.rmtree(session_path)
                    print(f"Sesión limpiada: {session_dir}")
    except Exception as e:
        print(f"Error en cleanup: {e}")


def start_cleanup_thread():
    """Inicia el hilo de limpieza automática."""
    def cleanup_worker():
        while True:
            cleanup_old_sessions()
            time.sleep(CLEANUP_INTERVAL)
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()


def get_sorted_folder_name(pdf_name):
    """Genera el nombre de la carpeta sorted para un PDF dado."""
    base_name = os.path.splitext(pdf_name)[0]
    return f"{base_name}-sorted"


def get_sorted_folder_path(pdf_name):
    """Obtiene la ruta completa de la carpeta sorted."""
    user_folder = get_user_pdf_folder()
    return os.path.join(user_folder, get_sorted_folder_name(pdf_name))


def sanitize_filename(name):
    """Limpia el nombre de archivo de caracteres prohibidos."""
    return re.sub(FORBIDDEN_CHARS, '', name).strip()


def is_valid_filename(name):
    """Verifica si el nombre de archivo es válido."""
    if not name or name.strip() == '':
        return False, "El nombre no puede estar vacío"
    
    if re.search(FORBIDDEN_CHARS, name):
        return False, "El nombre contiene caracteres prohibidos: < > : \" / \\ | ? *"
    
    if name.startswith('.') or name.endswith('.'):
        return False, "El nombre no puede empezar o terminar con punto"
    
    if len(name) > 200:
        return False, "El nombre es demasiado largo (máximo 200 caracteres)"
    
    return True, ""


@app.route('/')
def index():
    """Página principal con la tabla de PDFs."""
    pdfs = []
    user_folder = get_user_pdf_folder()
    
    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(user_folder, filename)
                try:
                    doc = fitz.open(filepath)
                    page_count = len(doc)
                    doc.close()
                    pdfs.append({
                        'name': filename,
                        'pages': page_count
                    })
                except Exception as e:
                    print(f"Error al abrir {filename}: {e}")
    
    pdfs.sort(key=lambda x: x['name'].lower())
    return render_template('index.html', pdfs=pdfs, session_id=get_session_id())


@app.route('/open/<filename>')
def open_pdf(filename):
    """Sirve el PDF original para abrirlo en el navegador."""
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, mimetype='application/pdf')


@app.route('/download/<filename>')
def download_pdf(filename):
    """Descarga el PDF original."""
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, mimetype='application/pdf', as_attachment=True, download_name=filename)


@app.route('/upload', methods=['POST'])
def upload_pdf():
    """Sube un PDF a la carpeta de PDFs del usuario."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
    
    # Verificar extensión
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'success': False, 'error': 'Solo se permiten archivos PDF'}), 400
    
    # Sanitizar nombre de archivo
    filename = secure_filename(file.filename)
    if not filename:
        filename = 'uploaded.pdf'
    
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    
    # Si ya existe, agregar número
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(filepath):
            filename = f"{base}_{counter}{ext}"
            filepath = os.path.join(user_folder, filename)
            counter += 1
    
    try:
        file.save(filepath)
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_pdf(filename):
    """Elimina un PDF del usuario y opcionalmente su carpeta sorted."""
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'PDF no encontrado'}), 404
    
    data = request.get_json() or {}
    delete_sorted = data.get('delete_sorted', False)
    
    try:
        # Eliminar PDF
        os.remove(filepath)
        
        # Eliminar carpeta sorted si se solicita
        if delete_sorted:
            sorted_folder = get_sorted_folder_path(filename)
            if os.path.exists(sorted_folder):
                import shutil
                shutil.rmtree(sorted_folder)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/page/<filename>/<int:page_num>')
def get_page(filename, page_num):
    """Renderiza una página específica del PDF como imagen PNG."""
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    if not os.path.exists(filepath):
        abort(404)
    
    try:
        doc = fitz.open(filepath)
        if page_num < 1 or page_num > len(doc):
            doc.close()
            abort(404)
        
        page = doc[page_num - 1]  # PyMuPDF usa índices base 0
        
        # Renderizar a mayor resolución para mejor calidad
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img_bytes = BytesIO(pix.tobytes("png"))
        doc.close()
        
        return send_file(img_bytes, mimetype='image/png')
    except Exception as e:
        print(f"Error al renderizar página: {e}")
        abort(500)


@app.route('/page-count/<filename>')
def get_page_count(filename):
    """Obtiene el número total de páginas de un PDF."""
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'PDF no encontrado'}), 404
    
    try:
        doc = fitz.open(filepath)
        count = len(doc)
        doc.close()
        return jsonify({'pages': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/sorter/<filename>')
def sorter(filename):
    """Página del clasificador de páginas."""
    user_folder = get_user_pdf_folder()
    filepath = os.path.join(user_folder, filename)
    if not os.path.exists(filepath):
        abort(404)
    
    start_page = request.args.get('start', 1, type=int)
    
    try:
        doc = fitz.open(filepath)
        total_pages = len(doc)
        doc.close()
    except Exception as e:
        abort(500)
    
    return render_template('sorter.html', 
                         filename=filename, 
                         start_page=start_page,
                         total_pages=total_pages)


@app.route('/list-sorted/<filename>')
def list_sorted(filename):
    """Lista los PDFs en la carpeta sorted correspondiente."""
    sorted_folder = get_sorted_folder_path(filename)
    
    pdfs = []
    if os.path.exists(sorted_folder):
        for f in os.listdir(sorted_folder):
            if f.lower().endswith('.pdf'):
                pdfs.append(f)
    
    pdfs.sort()
    return jsonify({'pdfs': pdfs, 'folder': get_sorted_folder_name(filename)})


@app.route('/check-name/<filename>', methods=['POST'])
def check_name(filename):
    """Verifica si un nombre de PDF ya existe en la carpeta sorted."""
    data = request.get_json()
    name = data.get('name', '')
    
    # Validar nombre
    is_valid, error_msg = is_valid_filename(name)
    if not is_valid:
        return jsonify({'valid': False, 'error': error_msg})
    
    # Agregar extensión si no la tiene
    if not name.lower().endswith('.pdf'):
        name = name + '.pdf'
    
    sorted_folder = get_sorted_folder_path(filename)
    pdf_path = os.path.join(sorted_folder, name)
    
    if os.path.exists(pdf_path):
        return jsonify({'valid': False, 'error': 'Ya existe un PDF con este nombre'})
    
    return jsonify({'valid': True, 'name': name})


@app.route('/create-pdf/<filename>', methods=['POST'])
def create_pdf(filename):
    """Crea un nuevo PDF con la página especificada."""
    data = request.get_json()
    page_num = data.get('page')
    new_name = data.get('name', '')
    
    # Validar nombre
    is_valid, error_msg = is_valid_filename(new_name)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400
    
    # Agregar extensión si no la tiene
    if not new_name.lower().endswith('.pdf'):
        new_name = new_name + '.pdf'
    
    user_folder = get_user_pdf_folder()
    source_path = os.path.join(user_folder, filename)
    sorted_folder = get_sorted_folder_path(filename)
    
    # Crear carpeta sorted si no existe
    if not os.path.exists(sorted_folder):
        os.makedirs(sorted_folder)
    
    new_pdf_path = os.path.join(sorted_folder, new_name)
    
    # Verificar si ya existe
    if os.path.exists(new_pdf_path):
        return jsonify({'success': False, 'error': 'Ya existe un PDF con este nombre'}), 400
    
    try:
        # Abrir PDF fuente y extraer página
        source_doc = fitz.open(source_path)
        new_doc = fitz.open()
        
        new_doc.insert_pdf(source_doc, from_page=page_num-1, to_page=page_num-1)
        new_doc.save(new_pdf_path)
        
        source_doc.close()
        new_doc.close()
        
        return jsonify({
            'success': True, 
            'path': new_pdf_path,
            'name': new_name,
            'folder': get_sorted_folder_name(filename)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/append-to-pdf/<filename>', methods=['POST'])
def append_to_pdf(filename):
    """Agrega una página a un PDF existente en la carpeta sorted."""
    data = request.get_json()
    page_num = data.get('page')
    target_pdf = data.get('target')
    
    user_folder = get_user_pdf_folder()
    source_path = os.path.join(user_folder, filename)
    sorted_folder = get_sorted_folder_path(filename)
    target_path = os.path.join(sorted_folder, target_pdf)
    
    if not os.path.exists(target_path):
        return jsonify({'success': False, 'error': 'PDF destino no encontrado'}), 404
    
    try:
        # Abrir ambos PDFs
        source_doc = fitz.open(source_path)
        target_doc = fitz.open(target_path)
        
        # Agregar página al final
        target_doc.insert_pdf(source_doc, from_page=page_num-1, to_page=page_num-1)
        
        new_page_count = len(target_doc)
        
        # Cerrar documentos antes de guardar
        source_doc.close()
        
        # Guardar en archivo temporal primero
        temp_path = target_path + '.tmp'
        target_doc.save(temp_path)
        target_doc.close()
        
        # Reemplazar el archivo original
        os.replace(temp_path, target_path)
        
        return jsonify({
            'success': True,
            'target': target_pdf,
            'new_page_count': new_page_count
        })
    except Exception as e:
        # Limpiar archivo temporal si existe
        temp_path = target_path + '.tmp'
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Crear carpeta base si no existe
    if not os.path.exists(BASE_PDF_FOLDER):
        os.makedirs(BASE_PDF_FOLDER)
        print(f"Carpeta base 'pdfs' creada en: {BASE_PDF_FOLDER}")
    
    # Iniciar hilo de limpieza
    start_cleanup_thread()
    
    # Usar puerto de Railway o 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    print(f"Carpeta base de PDFs: {BASE_PDF_FOLDER}")
    print(f"Iniciando servidor en puerto {port}")
    print(f"Sistema de sesiones activo - limpieza cada {CLEANUP_INTERVAL//3600} horas")
    app.run(debug=False, host='0.0.0.0', port=port)
