import requests
import os

def download_authlib_injector(authlib_injector_path: str):
    if not os.path.exists(os.path.join(authlib_injector_path, "authlib-injector.jar")):
        print(f"Загрузка authlib-injector")
        with requests.get("https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.7/authlib-injector-1.2.7.jar", stream=True) as r:
            r.raise_for_status()
            with open(os.path.join(authlib_injector_path, "authlib-injector.jar"), "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    return os.path.abspath(os.path.join(authlib_injector_path, "authlib-injector.jar"))

def auth_elyby(username: str, password: str):
    payload = {
        "username": username,
        "password": password,
        "requestUser": True
    }
    headers = {"Content-Type": "application/json"}
 
    try:
        resp = requests.post("https://authserver.ely.by/auth/authenticate", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        token = data["accessToken"]
        uuid = data["selectedProfile"]["id"]
        username = data["selectedProfile"]["name"]
        print(f"{username} ely.by авторизован")
        return {"token": token, "uuid": uuid, "username": username}
    except Exception as e:
        print(f"Ошибка авторизации {username}: {e}")
        return {}

def mc_account(type: str, username: str, password: str = None):
    match type:
        case "local": return {"username": username}
        case "elyby": return auth_elyby(username, password)