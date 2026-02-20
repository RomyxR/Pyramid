# launcher_tool.py
import sys
import requests
import json
import os
from tqdm import tqdm
import json
import subprocess
import zipfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from pirates_tool import  *

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
RESOURCES_URL = "https://resources.download.minecraft.net"

def get_manifest():
        resp = requests.get(MANIFEST_URL)
        resp.raise_for_status()
        return resp.json()["versions"]

def get_version_json(url: str):
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()

def get_versions():
    return {f"{i['type']}-{i['id']}": i["url"] for i in get_manifest()}

def search_java_path(version: int, path: str):
    platform_map = {"win32": "windows", "linux": "linux"}
    platform = platform_map.get(sys.platform, sys.platform)
    
    jre_root = os.path.join(path, f"jre{version}-{platform}")
    folder_name = os.listdir(jre_root)[0]
    bin_dir = os.path.join(jre_root, folder_name, "bin")

    if platform == "windows": java_app = "java.exe"
    else: java_app = "java"
    
    return os.path.abspath(os.path.join(bin_dir, java_app))

def download_jre(jdk_version: int = 25, arch: str = "x64", jre_path: str = "jre"):
    platform_map = {"win32": "windows", "linux": "linux"}
    platform = platform_map.get(sys.platform, sys.platform)
    target_dir = os.path.join(jre_path, f"jre{jdk_version}-{platform}")

    if os.path.exists(target_dir): return
    
    link = f"https://api.adoptium.net/v3/binary/latest/{jdk_version}/ga/{platform}/{arch}/jre/hotspot/normal/eclipse"

    file_format = "zip" if platform == "windows" else "tar.gz"
    file_name = f"jre{jdk_version}-{platform}.{file_format}"

    with requests.get(link, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        with open(file_name, "wb") as f, tqdm(
            desc=file_name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                size = f.write(chunk)
                bar.update(size)

    shutil.unpack_archive(file_name, os.path.join(jre_path, file_name.rsplit(".", 2)[0]))
    os.remove(file_name)

def download_client(version_id: str, version_json: dict, versions_path: str):
    print(f"Загрузка клиента {version_id}")
    
    jar_dir = os.path.join(versions_path, version_id)
    os.makedirs(jar_dir, exist_ok=True)
    
    jar_path = os.path.join(jar_dir, f"{version_id}.jar")
    json_path = os.path.join(jar_dir, f"{version_id}.json")

    if not os.path.exists(jar_path):
        url = version_json["downloads"]["client"]["url"]
        with open(jar_path, "wb") as f:
            f.write(requests.get(url).content)
        print("Клиент скачан")

    if not os.path.exists(json_path):
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(version_json, f, indent=4)
        print("JSON сохранен")
        
    return os.path.abspath(jar_path)


def download_assets(assets_index, assets_path):
    # Качаем индекс
    idx_path = os.path.join(assets_path, "indexes", f"{assets_index['id']}.json")
    os.makedirs(os.path.dirname(idx_path), exist_ok=True)
    r = requests.get(assets_index["url"])
    with open(idx_path, "wb") as f: f.write(r.content)
    
    objects = json.load(open(idx_path, "r", encoding='utf-8')).get("objects", {})
    session = requests.Session() # Ускоряет за счет переиспользования соединений

    def worker(info):
        h = info["hash"]
        path = os.path.join(assets_path, "objects", h[:2], h)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            res = session.get(f"{RESOURCES_URL}/{h[:2]}/{h}")
            with open(path, "wb") as f: f.write(res.content)

    with ThreadPoolExecutor(max_workers=32) as pool:
        list(tqdm(pool.map(worker, objects.values()), total=len(objects), desc="Assets"))

def download_libraries(libraries: list, libraries_path: str):
    classpath = []
    for lib in tqdm(libraries, desc="Libraries"):
        art = lib.get("downloads", {}).get("artifact")
        if not art: 
            continue

        path = os.path.join(libraries_path, art["path"])
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(requests.get(art["url"]).content)
        
        classpath.append(os.path.abspath(path))
    
    return classpath

def download_natives(version_json: dict, versions_path: str) -> str:
    natives_dir = os.path.join(versions_path, "natives")
    os.makedirs(natives_dir, exist_ok=True)
    
    libraries_root = os.path.abspath("libraries")
    platform_map = {"win32": "windows", "linux": "linux"}
    platform = platform_map.get(sys.platform, sys.platform)

    for lib in version_json.get("libraries", []):
        natives_map = lib.get("natives", {})
        if platform not in natives_map:
            continue
            
        native_key = natives_map[platform]

        art = lib.get("downloads", {}).get("classifiers", {}).get(native_key)
        if not art:
            continue

        native_jar_path = os.path.join(libraries_root, art["path"])

        if not os.path.exists(native_jar_path):
            os.makedirs(os.path.dirname(native_jar_path), exist_ok=True)
            print(f"Загрузка нативного архива: {native_key}")
            with open(native_jar_path, "wb") as f:
                f.write(requests.get(art["url"]).content)

        exclude_rules = lib.get("extract", {}).get("exclude", [])
        with zipfile.ZipFile(native_jar_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if any(file_name.startswith(rule) for rule in exclude_rules):
                    continue
                zip_ref.extract(file_name, natives_dir)

    print(f"Нативы извлечены в {natives_dir}")
    return os.path.abspath(natives_dir)


def launch(java_path: str, username: str, version_json: dict, game_dir: str, classpath_list: list, ram_mb: int = 4096):
    
    # Подготовка путей
    game_dir = os.path.abspath(game_dir)
    assets_dir = os.path.join(game_dir, "assets")
    versions_path = os.path.join(game_dir, "versions")
    
    version_id = version_json["id"]
    natives_dir = os.path.join(versions_path, version_id, "natives")
    
    # Проверка наличия natives
    if not os.path.exists(natives_dir):
        print(f"Папка natives не найдена: {natives_dir}")
        return

    # Словарь замен
    replacements = {
        "${auth_player_name}": username,
        "${version_name}": version_id,
        "${game_directory}": game_dir,
        "${assets_root}": assets_dir,
        "${assets_index_name}": version_json.get("assets", "legacy"),
        "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
        "${auth_access_token}": "0",
        "${user_type}": "mojang",
        "${version_type}": version_json.get("type", "release"),
        "${classpath}": os.pathsep.join(classpath_list),
        "${natives_directory}": natives_dir,#.replace('\\', '/'),
        "${launcher_name}": "PyramidLauncher",
        "${launcher_version}": "1.0"
    }

    def apply_replacements(text):
        for key, val in replacements.items():
            text = text.replace(key, str(val))
        return text

    def parse_args(args_source):
        out = []
        for arg in args_source:
            if isinstance(arg, str):
                processed = arg
                for key, val in replacements.items():
                    processed = processed.replace(key, val)
                out.append(processed)
        return out
    
    # СТАРЫЕ ВЕРСИИ
    if "minecraftArguments" in version_json:
        raw_args = version_json.get("minecraftArguments", "")
        if not raw_args:
            print("Не найдены аргументы запуска.")
            return

        final_game_args = apply_replacements(raw_args)
        
        cmd = [
            java_path,
            f"-Djava.library.path={replacements['${natives_directory}']}",
            f"-Xmx{ram_mb}M",
            "-cp", replacements["${classpath}"],
            version_json["mainClass"]
        ]
        cmd.extend(final_game_args.split())
        print(f"Запуск {version_id} | RAM: {ram_mb}MB")

    # НОВЫЕ ВЕРСИИ
    elif "arguments" in version_json:
        jvm_args = version_json.get("arguments", {}).get("jvm", [])
        game_args = version_json.get("arguments", {}).get("game", [])

        if not jvm_args:
            cmd = [java_path, f"-Xmx{ram_mb}M", "-cp", replacements["${classpath}"]]
        else:
            cmd = [java_path] + parse_args(jvm_args)
            
            # Проверяем, нет ли уже установки памяти в аргументах игры
            has_ram = any("-Xmx" in arg for arg in cmd)
            if not has_ram:
                cmd.insert(1, f"-Xmx{ram_mb}M") # Вставляем нашу память

        cmd.append(version_json["mainClass"])
        cmd.extend(parse_args(game_args))
        print(f"Запуск {version_id}")
        print(f"RAM: {ram_mb}MB")
    else:
        print("Неизвестный формат версии JSON.")
        return
    # Запуск
    subprocess.run(cmd, cwd=game_dir, encoding='utf-8', errors='replace')