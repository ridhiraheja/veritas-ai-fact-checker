import google.generativeai as genai

genai.configure(api_key="AIzaSyAS-BcKkbjxj4UFk0xcSyAGgNpkdg3B7Ho")

for m in genai.list_models():
    print(m.name)