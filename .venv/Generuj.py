import os
from openai import OpenAI
import requests
import re


if os.name == 'nt':  # For Windows
    clear_command = 'cls'
else:
    clear_command = 'clear'
os.system(clear_command)


# Inicjalizacja klienta OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

if not client.api_key:
    raise ValueError("Nie znaleziono klucza API. Ustaw zmienną środowiskową OPENAI_API_KEY.")



# URL do treści artykułu
article_url = "https://cdn.oxido.pl/hr/Zadanie%20dla%20JJunior%20AI%20Developera%20-%20tresc%20artykulu.txt"

# Pobranie treści artykułu z URL
try:
    response = requests.get(article_url)
    response.raise_for_status()
    article_content = response.text
except requests.exceptions.RequestException as e:
    raise Exception(f"Nie udało się pobrać treści artykułu: {e}")

# Definiowanie wiadomości dla ChatCompletion
messages = [
    {
        "role": "system",
        "content": "Jesteś ekspertem w konwertowaniu polskich artykułów na czysty kod HTML zgodnie z określonymi wytycznymi."
    },
    {
        "role": "user",
        "content": f"""
    Przekonwertuj poniższy polski artykuł na kod HTML, zgodnie z następującymi wytycznymi:

    - Użyj odpowiednich znaczników HTML do strukturyzacji treści.
    - Określ, gdzie obrazy wzbogaciłyby artykuł i wstaw znaczniki <img> z src="image_N.jpg", gdzie N to numer obrazu (np. image_1.jpg).
    - Dodaj atrybut 'alt' do każdego obrazu z szczegółowym opisem, który może być użyty do wygenerowania obrazu.
    - Umieść podpisy pod obrazami, używając odpowiednich znaczników HTML.
    - Nie dołączaj żadnego CSS ani JavaScript.
    - Zwróć tylko treść do umieszczenia między znacznikami <body> i </body>.
    - Nie dołączaj znaczników <html>, <head> ani <body>.
    - Upewnij się, że wszystkie polskie znaki są poprawnie reprezentowane.

    Artykuł:
    {article_content}
    """
    }
]

# Wywołanie API ChatCompletion OpenAI
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Możesz użyć "gpt-4" jeśli masz do niego dostęp
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
    )
except Exception as e:
    raise Exception(f"Żądanie do API OpenAI nie powiodło się: {e}")

# Wyodrębnienie wygenerowanego kodu HTML
html_body_content = response.choices[0].message.content.strip()

# Znalezienie wszystkich atrybutów src obrazów
image_files = re.findall(r'src="([^"]+)"', html_body_content)

# Znalezienie wszystkich tekstów alt obrazów
image_alts = re.findall(r'alt="([^"]+)"', html_body_content)

# Upewnij się, że folder 'images' istnieje
if not os.path.exists('images'):
    os.makedirs('images')

# Generowanie obrazów za pomocą API Obrazów OpenAI i zapisywanie ich lokalnie
for idx, prompt in enumerate(image_alts):
    try:
        image_response = client.images.generate(
            prompt=prompt,
            n=1,
            size="512x512",
        )
        # Pobranie URL obrazu
        image_url = image_response.data[0].url

        # Pobranie obrazu i zapisanie go lokalnie
        img_data = requests.get(image_url).content
        image_filename = f"images/image_{idx+1}.jpg"
        with open(image_filename, 'wb') as handler:
            handler.write(img_data)

        print(f"Obraz '{image_filename}' został zapisany.")
    except Exception as e:
        print(f"Nie udało się wygenerować obrazu dla promptu '{prompt}': {e}")
        # Możesz użyć obrazu zastępczego lub pominąć ten krok

# Aktualizacja ścieżek do obrazów w kodzie HTML
for idx in range(len(image_files)):
    html_body_content = html_body_content.replace(
        image_files[idx],
        f"images/image_{idx+1}.jpg"
    )

# Przygotowanie szablonu HTML z pustą sekcją <body>
template_html = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Szablon Artykułu</title>
    <style>
        /* Stylizacja dla profesjonalnego wyglądu artykułu */
        body {
            font-family: Arial, sans-serif;
            margin: 40px auto;
            max-width: 800px;
            line-height: 1.8;
            color: #333;
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        h1, h2, h3 {
            color: #222;
            text-align: center;
            font-weight: bold;
            margin-top: 20px;
        }

        h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        h2 {
            font-size: 1.6em;
            margin-bottom: 8px;
        }

        h3 {
            font-size: 1.4em;
            margin-bottom: 5px;
        }

        p {
            text-align: justify;
            margin: 10px 0;
        }

        img {
            display: block;
            margin: 15px auto;
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }

        figure {
            margin: 15px 0;
            text-align: center;
        }

        figcaption {
            font-style: italic;
            color: #666;
            margin-top: 5px;
        }

        /* Stylizacja list */
        ul, ol {
            margin: 10px 0 10px 20px;
            padding: 0;
        }

        /* Cytaty blokowe */
        blockquote {
            border-left: 4px solid #ddd;
            margin: 20px 0;
            padding: 10px 20px;
            color: #555;
            background: #f0f0f0;
        }

        /* Stylizacja linków */
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

</body>
</html>"""

# Zapisanie szablonu do pliku 'szablon.html' z kodowaniem UTF-8
with open('szablon.html', 'w', encoding='utf-8') as file:
    file.write(template_html)

# Przygotowanie pełnej treści HTML poprzez wstawienie artykułu do szablonu
full_html = template_html.replace("<body>\n\n</body>", f"<body>\n{html_body_content}\n</body>")

# Zapisanie pełnego podglądu artykułu do pliku 'podglad.html' z kodowaniem UTF-8
with open('podglad.html', 'w', encoding='utf-8') as file:
    file.write(full_html)

print("Szablon został zapisany do szablon.html")
print("Podgląd artykułu został zapisany do podglad.html")
