import os
import shlex, subprocess
from flask import Flask, request, jsonify
import json
import logging

app = Flask(__name__)
app.config['DEBUG'] = True

ARGOCD_BIN_PATH=os.getenv("ARGOCD_BIN_PATH")
ARGOCD_SERVER_HOST=os.getenv("ARGOCD_SERVER_HOST")
ARGOCD_USERNAME=os.getenv("ARGOCD_USERNAME")
ARGOCD_PASSWORD=os.getenv("ARGOCD_PASSWORD")
ARGOCD_APPNAME=os.getenv("ARGOCD_APPNAME")


def extract_path_from_url(url):
    # 分割 URL
    parts = url.split('/')

    # 提取所需部分
    # 假设 URL 格式固定，且需要的部分总是从第四个分段开始到倒数第二个分段结束
    extracted_path = '/'.join(parts[3:])

    return extracted_path

def cmd(*args):
    # 将参数组合成命令
    command = ' '.join(shlex.quote(arg) for arg in args)
    logging.debug(f"run cmd: {command}")
    # 执行命令
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, executable="/bin/sh")
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


@app.route('/api/webhook', methods=['POST'])
def get_webhook():
    logging.debug(f"request data: {request.data}")
    if not request.data:  # 检测是否有数据
        return jsonify('request webhook request failed. data is empty'), 500

    data = request.data.decode('utf-8')
    # 获取到POST过来的数据
    data_json = json.loads(data)
    # get branch
    ref = data_json["ref"]
    branch = ref.split('/')[-1]
    logging.debug(f"get branch is {branch}")
    # get repo
    repo_uri = extract_path_from_url(data_json["repository"]["url"])
    repo_full_url = data_json["repository"]["url"]
    # get directory list
    commits = data_json["commits"]
    dirname_list = set()
    for commit in commits:
        modifieds = commit["modified"]
        for modified in modifieds:
            dirname_list.add(modified.split('/')[0])
    # 先登录
    cmd(f"{ARGOCD_BIN_PATH}", "login", f"{ARGOCD_SERVER_HOST}", "--username", f"{ARGOCD_USERNAME}", "--password",
        f"{ARGOCD_PASSWORD}", "--insecure")
    # 项目路径
    logging.debug(f"get branch={branch}, dirname_list={','.join(dirname_list)}")
    argocd_app_list = cmd(f"{ARGOCD_BIN_PATH}", "app", "list", "-o", "json")
    logging.debug(f"get app list is: {argocd_app_list[:100]}")
    try:
        argocd_app_list_json = json.loads(argocd_app_list)
    except json.JSONDecodeError as e:
        return jsonify(f"argocd_app_list_json JSON 解析错误: {e}"), 500
    sync_app_list = []
    for app in argocd_app_list_json:
        app_repo = extract_path_from_url(app["spec"]["source"]["repoURL"])
        app_dirname = app["spec"]["source"]["path"]
        app_repo_branch = app["spec"]["source"]["targetRevision"]
        app_name = app["metadata"]["name"]
        if app_repo == repo_uri and app_dirname in dirname_list and app_repo_branch == branch:
            logging.info(f"prepare sync app: {app_name}, dirname: {app_dirname}, branch: {branch}, repo: {repo_full_url}")
            sync_app_list.append(app_name)
    if len(sync_app_list) > 0:
        cmd(f"{ARGOCD_BIN_PATH}", "app", "sync", " ".join(sync_app_list))
    else:
        logging.info(f"argocd sync app = {sync_app_list}. nothing to sync")
    return jsonify("success.")


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    app.run(debug=True, port="8080", host="0.0.0.0")
