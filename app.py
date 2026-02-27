# main.py
import os
from launcher_tool import *
from elyby import *
import fabric

GAME_PATH = "minecraft"

os.makedirs(GAME_PATH, exist_ok=True)

#old_alpha-rd-132211
version = "release-1.21.11"
#version = "old_alpha-rd-132211"
#version = "old_alpha-inf-20100618"
#version = "snapshot-26.1-snapshot-10"
#version = "snapshot-25w14craftmine"
#version = "old_alpha-a1.2.6"
#version = "old_alpha-rd-161348"

USE_FABRIC = True

versions = get_versions()

ver_id = version.split('-', 1)[1]
version_json = get_version_json(versions[version])

if USE_FABRIC:
    version_json = fabric.create_fabric_version(version_json, GAME_PATH)
    fabric.download_fabric_api(ver_id, GAME_PATH)

libraries = version_json["libraries"]
assets = version_json["assetIndex"]
java_version = int(version_json.get("javaVersion", {}).get("majorVersion", 8))


class_path = download_libraries(libraries, os.path.join(GAME_PATH, "libraries"))
authlib_injector_path = download_authlib_injector(os.path.join(GAME_PATH, "libraries"))
download_assets(assets, os.path.join(GAME_PATH, "assets"))
client_jar = download_client(ver_id, version_json, os.path.join(GAME_PATH, "versions"))
class_path.append(client_jar)

download_natives(version_json, os.path.join(GAME_PATH, "versions", ver_id))

download_jre(java_version, jre_path="jre")

launch(
    search_java_path(java_version, "jre", debug=True),
    version_json,
    GAME_PATH,
    class_path,
    4096,
    authlib_injector_path,
    auth_params=mc_account("local", "Sas"),
    )
