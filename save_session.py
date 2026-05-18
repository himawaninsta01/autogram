from instagrapi import Client
import json

USERNAME = "superchronos.ai"
PASSWORD = input("Masukkan password Instagram: ")

print("\n⏳ Login ke Instagram...")
cl = Client()

try:
    cl.login(USERNAME, PASSWORD)
    cl.dump_settings("session.json")
    print("✅ Session berhasil disimpan ke session.json")
    print("   Lanjut ke Langkah 3: upload isi session.json ke GitHub Secrets")
except Exception as e:
    print(f"❌ Login gagal: {e}")