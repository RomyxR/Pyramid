# main.py
import os
from launcher_tool import *
from pirates_tool import *

GAME_PATH = "minecraft"

os.makedirs(GAME_PATH, exist_ok=True)

# old_alpha-rd-132211
#version = "release-1.21.11"
#version = "old_alpha-rd-132211"
#version = "old_alpha-inf-20100618"
version = "snapshot-26.1-snapshot-9"

versions = get_versions()

print(get_versions())


ver_id = version.split('-', 1)[1]
version_json = get_version_json(versions[version])
libraries = version_json["libraries"]
assets = version_json["assetIndex"]
java_version = int(version_json.get("javaVersion", {}).get("majorVersion", 8))

class_path = download_libraries(libraries, libraries_path=f"{GAME_PATH}/libraries")

download_assets(assets, assets_path=f"{GAME_PATH}/assets")
client_jar = download_client(ver_id, version_json, f"{GAME_PATH}/versions/")
download_natives(version_json, rf"{GAME_PATH}/versions/{ver_id}")

class_path.append(client_jar)

download_jre(java_version)
launch(search_java_path(java_version, "jre"), "Romyx_SVRT", version_json, GAME_PATH, class_path, 4096)
