import os
import json
import argparse
import requests
import subprocess
from zipfile import ZipFile

version_manifest_url = 'https://launchermeta.mojang.com/mc/game/version_manifest.json'
os_name = 'linux'
user_home_dir = os.path.expanduser('~')
launcher_name = 'MCLauncher'
game_dir = f'{user_home_dir}/.{launcher_name}'

def get_versions():
    return requests.get(version_manifest_url).json()['versions']

def download(url, file_path):
    with open(file_path, 'wb') as file:
        response = requests.get(url)
        file.write(response.content)

def download_client_jar(version_filepath):
    version_json_path = f'{version_filepath}.json'
    with open(version_json_path) as file:
        client_jar_path = f'{version_filepath}.jar'
        if not os.path.exists(client_jar_path):
            version_json = json.loads(file.read())
            client_jar_url = version_json['downloads']['client']['url']
            download(client_jar_url, client_jar_path)
            print('downloaded client jar')

def download_libraries(libraries, os_name):
    native_name = f'natives-{os_name}'

    for library in libraries:
        download_obj = library['downloads']
        lib_path = ''
        lib_full_path = ''
        lib_url = ''

        if 'artifact' in download_obj:
            lib_path = download_obj['artifact']['path']
            lib_full_path = f'{game_dir}/libraries/{lib_path}'
            lib_url = download_obj['artifact']['url']
            if not os.path.exists(lib_full_path):
                lib_dir_path = os.path.dirname(lib_full_path)
                if not os.path.exists(lib_dir_path):
                    os.makedirs(lib_dir_path)
                download(lib_url, lib_full_path)

        if 'classifiers' in download_obj:
            classifiers = download_obj['classifiers']
                
            if native_name in classifiers:
                lib_path = classifiers[f'natives-{os_name}']['path']
                lib_full_path = f'{game_dir}/libraries/{lib_path}'
                lib_url = classifiers[f'natives-{os_name}']['url']
                
                if not os.path.exists(lib_full_path):
                    lib_dir_path = os.path.dirname(lib_full_path)
                    if not os.path.exists(lib_dir_path):
                        os.makedirs(lib_dir_path)
                    download(lib_url, lib_full_path)

def download_log_config(libraries):
    lib_path = library['downloads']['artifact']['path']
    lib_full_path = f'{game_dir}/libraries/{lib_path}'

    if not os.path.exists(lib_full_path):
        lib_dir_path = os.path.dirname(lib_full_path)
        if not os.path.exists(lib_dir_path):
            os.makedirs(lib_dir_path)
        lib_url = library['downloads']['artifact']['url']
        download(lib_url, lib_full_path)

def extract_game_natives(version):
    version_json = f'{game_dir}/versions/{version}/{version}.json'
    with open(version_json) as file:
        data = json.loads(file.read())
        libraries = data['libraries']
        native_name = f'natives-{os_name}'
        natives_dir = f'{game_dir}/bin/natives/{version}'

        for library in libraries:
            download_obj = library['downloads']

            if 'classifiers' in download_obj:
                classifiers = download_obj['classifiers']
                
                if native_name in classifiers:
                    native = classifiers[native_name]
                    native_path = native['path']
                    lib_relative_path = f'{game_dir}/libraries/{native_path}'

                    # Create natives dir
                    if not os.path.exists(natives_dir):
                        os.makedirs(natives_dir)

                    # Extract natives
                    if os.path.exists(lib_relative_path):
                        native_archive = ZipFile(lib_relative_path, 'r')
                        [native_archive.extract(file, natives_dir) for file in native_archive.namelist() if file.endswith('.so')]
                        print(f'extracted {lib_relative_path} to {natives_dir}')
                    
def download_version(version):
    # Create version dir
    version_id = version['id']
    version_path = f'{game_dir}/versions/{version_id}'
    
    if not os.path.isdir(version_path):
        os.makedirs(version_path)
        print('created version directory')

    # Download version json
    version_filepath = f'{version_path}/{version_id}'
    version_json_path = f'{version_filepath}.json'
    if not os.path.exists(version_json_path):
        version_json_url = version['url']
        download(version_json_url, version_json_path)
        print('downloaded version json')
    
    # Download version jar
    download_client_jar(version_filepath)
    
    # Download libraries
    with open(version_json_path) as file:
        json_file = json.loads(file.read())
        libraries = json_file['libraries']
        download_libraries(libraries, os_name)

    # Download log config
    with open(version_json_path) as file:
        logging = json.loads(file.read())['logging']['client']['file']
        file_name = logging['id']
        file_url = logging['url']
        
        log_configs_path = f'{game_dir}/assets/log_configs'

        if not os.path.isdir(log_configs_path):
            os.makedirs(log_configs_path)

        log_config_file_path = f'{log_configs_path}/{file_name}'
        if not os.path.exists(log_config_file_path):
            download(file_url, log_config_file_path)
            print('downloaded log config')
    
    # Download asset index file
    with open(version_json_path) as file:
        asset = json.loads(file.read())['assetIndex']
        file_name = asset['id'] + '.json'
        file_url = asset['url']
        
        assets_index_path = f'{game_dir}/assets/indexes'

        if not os.path.isdir(assets_index_path):
            os.makedirs(assets_index_path)

        asset_index_file_path = f'{assets_index_path}/{file_name}'
        if not os.path.exists(asset_index_file_path):
            download(file_url, asset_index_file_path)
            print('downloaded asset index file')

    # Extract natives
    extract_game_natives(version_id)

def get_client_jar_path(version):
    return os.path.abspath(f'{game_dir}/versions/{version}/{version}.jar')

def get_game_libraries(version):
    libs = ''
    version_json = f'{game_dir}/versions/{version}/{version}.json'
    native_name = f'natives-{os_name}'

    with open(version_json) as file:
        data = json.loads(file.read())
        libraries = data['libraries']

        for library in libraries:
            download_obj = library['downloads']

            if 'artifact' in download_obj:
                lib_path = download_obj['artifact']['path']

            if 'classifiers' in download_obj:
                classifiers = download_obj['classifiers']
                if native_name in classifiers:
                    native = classifiers[native_name]
                    lib_path = native['path']
                
            lib_full_path = f'{game_dir}/libraries/{lib_path}'
            lib_abs_path = os.path.abspath(lib_full_path)
            
            index = libs.find(lib_abs_path)
            if index == -1:
                libs += lib_abs_path + ':'
            
    return libs

def get_client_main_class(version):
    version_json = f'{game_dir}/versions/{version}/{version}.json'
    with open(version_json) as file:
        data = json.loads(file.read())
        return data['mainClass']

def get_client_asset_index(version):
    version_json = f'{game_dir}/versions/{version}/{version}.json'
    with open(version_json) as file:
        data = json.loads(file.read())
        return data['assetIndex']['id']

def get_client_log_config_file_path(version):
    version_json = f'{game_dir}/versions/{version}/{version}.json'
    with open(version_json) as file:
        data = json.loads(file.read())
        file_name = data['logging']['client']['file']['id']
        relative_file_path = f'{game_dir}/assets/log_configs/{file_name}'
        abs_path = os.path.abspath(relative_file_path)
        return abs_path

def start_game(version, username, uuid, token, user_type):
    print(f'starting Minecraft {version}\n')

    java_path = 'java'
    java_library_path = os.path.abspath(f'{game_dir}/bin/natives/{version}')
    
    client_jar_path = get_client_jar_path(version)
    client_libraries = f'{get_game_libraries(version)}{client_jar_path}'
    client_main_class = get_client_main_class(version)
    log4j_config_file = get_client_log_config_file_path(version)
    
    assets_dir = f'{game_dir}/assets'
    asset_index = get_client_asset_index(version)

    java_command = [
        java_path,
        f'-Djava.library.path={java_library_path}',
        f'-Dminecraft.client.jar={client_jar_path}',
        '-cp',
        client_libraries,
        '-Xmx2G',
        '-XX:+UnlockExperimentalVMOptions',
        '-XX:+UseG1GC',
        '-XX:G1NewSizePercent=20',
        '-XX:G1ReservePercent=20',
        '-XX:MaxGCPauseMillis=50',
        '-XX:G1HeapRegionSize=32M',
        f'-Dlog4j.configurationFile={log4j_config_file}',
        client_main_class,
        '--username',
        username,
        '--version',
        version,
        '--gameDir',
        game_dir,
        '--assetsDir',
        assets_dir,
        '--assetIndex',
        asset_index,
        '--uuid',
        uuid,
        '--accessToken',
        token,
        '--userType',
        user_type,
        '--userProperties',
        '{}'
    ]
    # print(' '.join(java_command))
    subprocess.run(java_command)
    
def download_and_run(version_name, username, uuid, user_type, token):
    versions = get_versions()
    for version in versions:
        id = version['id']
        if id == version_name:
            download_version(version)
            start_game(id, username, uuid, user_type, token)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Python Minecraft Launcher')

    parser.add_argument('--version', type=str, required=True)
    parser.add_argument('--username', type=str, required=True)
    parser.add_argument('--uuid', type=str, default='0')
    parser.add_argument('--userType', type=str, default='0')
    parser.add_argument('--token', type=str, default='0')

    args = parser.parse_args()
    
    version = args.version
    username = args.username
    uuid = args.uuid
    userType = args.userType
    token = args.token

    # get_game_libraries2(version)
    download_and_run(version, username, uuid, userType, token)