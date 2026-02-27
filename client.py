import launcher_tool
from launcher_tool import *
from elyby import *
from tui import *
import fabric

GAME_PATH = "minecraft"

def start_minecraft(version: str, ram_mb: int = 4096, profile: dict = {}, modloader: str = None, debug: bool = False):
    versions = get_versions()

    ver_id = version.split('-', 1)[1]
    version_json = get_version_json(versions[version])

    if modloader == "fabric":
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
        search_java_path(java_version, "jre", debug),
        version_json,
        GAME_PATH,
        class_path,
        ram_mb,
        authlib_injector_path,
        auth_params=profile,
    )

home_screen(get_versions(), launcher_tool.PLATFORM)

profile = mc_account("local", "Sas")
start_minecraft("release-1.21.11", profile=profile, debug=False, modloader="fabric")
input()