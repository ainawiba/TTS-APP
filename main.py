from pathlib import Path
from flask import Flask, render_template, request, url_for, flash
from google.cloud import texttospeech
import fitz
import os

from werkzeug.utils import redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['appkey']

directory = os.path.join(app.static_folder, "files")

@app.route('/', methods=['POST','GET'])
def home():

    if request.method == 'POST':
        language = request.form.get("language")
        file = request.files["file"]
        if not file or file.filename == "":
            return "No file selected"

        path = os.path.join(directory,file.filename)
        file.save(path)
        print("Uploaded!")


        # # ---------- READ PDF ----------
        doc = fitz.open(f"./static/files/{file.filename}")
        file_name = file.filename.strip(".pdf")
        print("Number of pages:", len(doc))

        all_text = {}
        page_no = 1

        for page in doc:
            text = page.get_text()
            text = text.replace("\n", " ")
            all_text[page_no] = text
            page_no += 1

        print("Pages extracted:", len(all_text))
        print(all_text)

        # ---------- GOOGLE TTS ----------
        for page_no in all_text:
            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=all_text[page_no])

            if language == "fr":
                voice = texttospeech.VoiceSelectionParams(
                    language_code="fr-FR",
                    name="fr-FR-Neural2-C"
                )
            else:
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-GB",
                    name="en-GB-Neural2-C"
                )



            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,

            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            # except:
            #     flash("API requests failed...")
            #     print("API requests failed...")

            # ---------- MAKE A FOLDER -------

            filepath = Path(f"./static/files/{file_name}")
            folder_name = filepath.stem
            print(folder_name)
            output_dir = Path(app.static_folder) / "files" / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # ---------- SAVE AUDIO ----------
            with open(f"./static/files/{folder_name}/{file_name}_{language}_page_{page_no}.mp3", "wb") as out:
                out.write(response.audio_content)

            print(f"Audio is successfully saved")
            message = "Audio file(s) ready for download :"

            # --------- SHOW AUDIO FILES ------
            files = os.listdir(output_dir)
            #files = [f for f in files if f.endswith(".pdf")]

            return render_template("index.html", files=files, folder=folder_name, message=message)

    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)


