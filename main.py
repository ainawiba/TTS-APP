import re
from pathlib import Path
from flask import Flask, render_template, request, url_for, flash
from google.cloud import texttospeech
from google.api_core.exceptions import GoogleAPIError
import fitz
import os
from moviepy import AudioFileClip, concatenate_audioclips, AudioClip

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['appkey']

@app.route('/', methods=['POST','GET'])
def home():
    directory = os.path.join(app.static_folder, "files")
    audio_list = []
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
        file_name = Path(file.filename).stem
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

        # ---------- MAKE A FOLDER -------

        filepath = Path(f"./static/files/{file_name}")
        folder_name = filepath.stem
        print(folder_name)
        output_dir = Path(app.static_folder) / "files" / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)

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

            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            except GoogleAPIError(Exception) as e:
                print("FULL ERROR:", repr(e))
                flash("API requests failed...")
                print("API requests failed...")
            else:
                # ---------- SAVE AUDIO ----------
                with open(f"{output_dir}/audio_{page_no}.mp3", "wb") as out:
                    out.write(response.audio_content)

                print(f"Audio saved to {output_dir}/audio_{page_no}.mp3")
                new_audio = output_dir/f"audio_{page_no}.mp3"
                audio_list.append(new_audio)

        # --------- MERGE AUDIO FILES ------
        # list of mp3 files
        audio_sorted = sorted(audio_list, key=lambda f: int(re.findall(r'\d+', f.stem)[0]))
        # re.findall() searches a string for all matches of a pattern and returns a list of matches
        print(audio_sorted)

        # Create 1-second silent clip (duration=1)
        silence = AudioClip(lambda t: 0, duration=1, fps=44100)

        # Load audio clips
        audio_files = [AudioFileClip(audio) for audio in audio_sorted]
        print(audio_files)
        audio_silence_list = []
        for file in audio_files:
            audio_silence_list.append(file)
            audio_silence_list.append(silence)

        # Concatenate all clips
        final_audio = concatenate_audioclips(audio_silence_list)

        # Export merged audio
        audio_filename = f"{file_name}_{language}.mp3"
        audio_path = Path(output_dir) / audio_filename
        final_audio.write_audiofile(str(audio_path))

        # --------- SHOW AUDIO FILES ------
        if audio_path is None:
            message = "No Audio file(s) found"

        else:
            message = "Audio file(s) ready for download :"


        return render_template("index.html", file=audio_filename, folder=folder_name, message=message)

    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)


