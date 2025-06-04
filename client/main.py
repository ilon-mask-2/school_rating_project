from config import BASE_URL
import requests

response = requests.get(f"{BASE_URL}/admin/student-ratings")