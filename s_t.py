import os
import time
import glob
import uuid
import streamlit as st
from PIL import Image
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from gtts import gTTS
from googletrans import Translator

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Traductor de Voz",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Crear directorio temporal
os.makedirs("temp", exist_ok=True)

# Limpieza de archivos de audio
def remove_files(days=1):
    mp3_files = glob.glob("temp/*.mp3")
    now = time.time()
    n_days = days * 86400
    for f in mp3_files:
        if os.stat(f).st_mtime < now - n_days:
            try:
                os.remove(f)
            except Exception:
                pass

remove_files(1)

# Inicializar variables de estado
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "translated_text" not in st.session_state:
    st.session_state["translated_text"] = ""
if "audio_path" not in st.session_state:
    st.session_state["audio_path"] = None

# Mapeo de Idiomas
LANGUAGES = {
    "Español 🇪🇸": "es",
    "Inglés 🇺🇸": "en",
    "Japonés 🇯🇵": "ja",
    "Coreano 🇰🇷": "ko",
    "Mandarín 🇨🇳": "zh-cn",
    "Bengalí 🇧🇩": "bn"
}

ACCENTS = {
    "Defecto": "com",
    "Español": "com.mx",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canadá": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za"
}

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎙️ Traductor por Voz")
    st.info(
        "**Instrucciones:**\n"
        "1. Presiona el botón **Escuchar**.\n"
        "2. Habla claramente hacia tu micrófono.\n"
        "3. Revisa el texto capturado.\n"
        "4. Elige los idiomas de origen y destino, y presiona **Traducir**."
    )

# --- HEADER PRINCIPAL ---
st.title("🎙️️ Traductor Inteligente de Voz")
st.caption("Captura tu voz en tiempo real, tradúcela al idioma deseado y escúchala al instante.")
st.divider()

# --- PANEL PRINCIPAL EN DOS COLUMNAS ---
col_left, col_right = st.columns([1, 1], gap="large")

# COLUMNA IZQUIERDA: AUDIO E IMAGEN
with col_left:
    with st.container(border=True):
        st.subheader("1. Captura de Voz")
        
        # Carga opcional de imagen de cabecera si existe
        if os.path.exists("OIG7.jpg"):
            image = Image.open("OIG7.jpg")
            st.image(image, use_container_width=True)
            
        st.write("Presiona el botón e inicia el reconocimiento:")
        
        # Botón Bokeh para reconocimiento de voz
        stt_button = Button(label="🎤 Escuchar Micrófono", width=280, height=50)
        stt_button.js_on_event("button_click", CustomJS(code="""
            var recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'es-ES';
            
            recognition.onresult = function (e) {
                var value = "";
                for (var i = e.resultIndex; i < e.results.length; ++i) {
                    if (e.results[i].isFinal) {
                        value += e.results[i][0].transcript;
                    }
                }
                if (value != "") {
                    document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
                }
            }
            recognition.start();
        """))

        # Captura de evento Bokeh
        result = streamlit_bokeh_events(
            stt_button,
            events="GET_TEXT",
            key="listen",
            refresh_on_update=False,
            override_height=70,
            debounce_time=0
        )

        if result and "GET_TEXT" in result:
            st.session_state["transcript"] = result.get("GET_TEXT")
            st.toast("¡Voz capturada con éxito!", icon="✅")

# COLUMNA DERECHA: CONFIGURACIÓN Y TEXTO
with col_right:
    with st.container(border=True):
        st.subheader("2. Configuración de Entrada")
        
        # Muestra y permite editar la transcripción obtenida
        edited_text = st.text_area(
            "Texto capturado (puedes editarlo si es necesario):",
            value=st.session_state["transcript"],
            height=140,
            placeholder="Haz clic en 'Escuchar Micrófono' y habla..."
        )
        st.session_state["transcript"] = edited_text
        
        c1, c2 = st.columns(2)
        with c1:
            in_lang_label = st.selectbox("Idioma de Entrada", list(LANGUAGES.keys()), index=0)
        with c2:
            out_lang_label = st.selectbox("Idioma de Salida", list(LANGUAGES.keys()), index=1)
            
        accent_label = st.selectbox("Acento de Salida", list(ACCENTS.keys()))

# --- SECCIÓN INFERIOR: TRADUCCIÓN Y AUDIO ---
st.write("")
with st.container(border=True):
    st.subheader("3. Resultado y Reproducción")
    
    btn_translate = st.button("🚀 Traducir & Generar Voz", type="primary", use_container_width=True)
    
    if btn_translate:
        text_to_process = st.session_state["transcript"]
        
        if not text_to_process.strip():
            st.warning("⚠️️ Primero debes hablar al micrófono o escribir un texto arriba.")
        else:
            with st.spinner("Traduciendo y generando el audio..."):
                try:
                    src_code = LANGUAGES[in_lang_label]
                    dest_code = LANGUAGES[out_lang_label]
                    tld_code = ACCENTS[accent_label]
                    
                    # Traducción
                    translator = Translator()
                    translation = translator.translate(text_to_process, src=src_code, dest=dest_code)
                    translated_text = translation.text
                    st.session_state["translated_text"] = translated_text
                    
                    # Generación de Audio
                    file_id = uuid.uuid4().hex[:8]
                    filepath = f"temp/audio_{file_id}.mp3"
                    
                    tts = gTTS(translated_text, lang=dest_code, tld=tld_code, slow=False)
                    tts.save(filepath)
                    st.session_state["audio_path"] = filepath
                    
                    st.toast("¡Traducción completada!", icon="🎉")
                except Exception as e:
                    st.error(f"Ocurrió un error en el procesamiento: {e}")

    # Mostrar resultados si existen
    if st.session_state["translated_text"] or st.session_state["audio_path"]:
        st.divider()
        res_col1, res_col2 = st.columns([1, 1], gap="medium")
        
        with res_col1:
            st.markdown("**Texto Traducido:**")
            st.info(st.session_state["translated_text"])
            
        with res_col2:
            st.markdown("**Reproductor de Voz:**")
            if st.session_state["audio_path"] and os.path.exists(st.session_state["audio_path"]):
                with open(st.session_state["audio_path"], "rb") as f:
                    st.audio(f.read(), format="audio/mp3")       
    



        
    


