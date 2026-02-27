# fabric.py
import requests
import os
import json

META_URL = "https://meta.fabricmc.net/v2/versions/loader"

def maven_to_path(name: str):
    """Превращает 'group:artifact:version' в путь файла"""
    group, artifact, version = name.split(":")
    return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"

def create_fabric_version(vanilla_json: dict, game_dir: str):
    mc_version = vanilla_json["id"]
    fabric_id = f"{mc_version}-fabric"
    version_dir = os.path.join(game_dir, "versions", fabric_id)

    # 1. Получаем данные Fabric API
    loader_data = requests.get(f"{META_URL}/{mc_version}").json()
    if not loader_data:
        raise Exception(f"Fabric не найден для {mc_version}")

    loader = loader_data[0]["loader"]["version"]
    profile = requests.get(f"{META_URL}/{mc_version}/{loader}/profile/json").json()

    # 2. Создаем объединенный JSON
    merged = vanilla_json.copy()
    merged.update({"id": fabric_id, "mainClass": profile["mainClass"]})

    # 3. Обрабатываем библиотеки
    fabric_libs = []
    for lib in profile.get("libraries", []):
        new_lib = lib.copy()
        # Формируем downloads, если отсутствует
        if not lib.get("downloads", {}).get("artifact"):
            path = maven_to_path(lib["name"])
            new_lib["downloads"] = {"artifact": {"path": path, "url": lib.get("url", "") + path}}
        fabric_libs.append(new_lib)

    merged["libraries"] = fabric_libs + vanilla_json.get("libraries", [])

    # Добавляем аргументы JVM
    if jvm_args := profile.get("arguments", {}).get("jvm"):
        merged.setdefault("arguments", {}).setdefault("jvm", []).extend(jvm_args)

    # 4. Сохраняем результат
    os.makedirs(version_dir, exist_ok=True)
    with open(os.path.join(version_dir, f"{fabric_id}.json"), "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=4)

    print(f"Версия Fabric создана: {fabric_id}")
    return merged

def download_fabric_api(mc_version: str, game_dir: str):
    os.makedirs(mods_dir := os.path.join(game_dir, "mods"), exist_ok=True)
    print("Поиск Fabric API...")

    url = f'https://api.modrinth.com/v2/project/fabric-api/version?game_versions=["{mc_version}"]&loaders=["fabric"]'
    resp = requests.get(url)
    resp.raise_for_status()
    
    versions = resp.json()
    if not versions:
        print("Fabric API не найден.")
        return

    file = versions[0]["files"][0]
    file_path = os.path.join(mods_dir, file["filename"])

    if os.path.exists(file_path):
        print("Fabric API уже установлен.")
        return

    print(f"Загрузка Fabric API: {file['filename']}")
    with open(file_path, "wb") as f:
        f.write(requests.get(file["url"]).content)
    print("Fabric API установлен.")