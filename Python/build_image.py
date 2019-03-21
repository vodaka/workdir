# -*- coding:utf8 -*-

import os
import docker
import threading
from jinja2 import Template
from ruamel import yaml
from handle import read_j2
from handle import read_yml


template_path = os.path.join(os.getcwd(), 'templates')
build_path = os.path.join(os.getcwd(), 'build')
scripts_path = os.path.join(build_path, 'container-scripts')
config_path = os.path.join(os.getcwd(), 'config')


def read_yml(filename):
    """
    Read yaml file which holds values for variables in jinja2 templates, and return python dict 
    """
    filename = os.path.join(config_path, filename)
    print("Read yaml file {}".format(filename))
    with open(filename, 'r') as f:
        data = yaml.safe_load(f.read())
    return data


def read_j2(filename):
    """
    Read jinja2 template and return template object for generating files such as dockerfile , scripts
    """
    template_filename = os.path.join(template_path, filename)
    print("Read jinja file {}".format(template_filename))
    with open(template_filename, 'r') as f:
        template = Template(f.read())
    return template


def gen_dockerfile(data):
    """
    Generate dockerfile for building images
    """
    with open(os.path.join(build_path, 'Dockerfile'), 'w') as f:
        if data['base'] == 'weblogic10_3':
            template = read_j2('dockerfile_10_3.j2')
            sharedir = [value for item in data.get('sharedir', []) for key, value in item.items()]
            conttent = template.render(sharedir=sharedir)
            f.write(conttent)
        elif data['base'] == 'weblogic12_1':
            template = read_j2('dockerfile_12_1.j2')
            sharedir = [value for item in data.get('sharedir', []) for key, value in item.items()]
            conttent = template.render(sharedir=sharedir)
            f.write(conttent)
        else:
            template = read_j2('dockerfile_12_2.j2')
            sharedir = [value for item in data.get('sharedir', []) for key, value in item.items()]
            conttent = template.render(sharedir=sharedir)
            f.write(conttent)
    print("generated dockerfile")


def gen_startall(data):
    """
    Generate starAll.sh script which is used for CMD in dockerfile.
    """
    with open(os.path.join(build_path, 'startAll.sh'), 'w') as f:
        template = read_j2('startAll.j2')
        mount_data = data.get('sharedir', [])
        content = template.render(mount_data=mount_data, data=data)
        f.write(content)
    print("generated startAll.sh")


def gen_py(buildyml, datayml):
    """
    Generate scripts for deploy datasource
    """
    build_data = read_yml(buildyml)
    deploy_data = read_yml(datayml)
    deploy_file = '-'.join(['deploy', '.'.join([build_data['buildargs']['APP_ENV'], 'py'])])
    template = read_j2('deploy.j2')
    with open(os.path.join(scripts_path, deploy_file), 'w') as sf:
        content = template.render(data=deploy_data, build_data=build_data)
        sf.write(content)
    print("generated datasource deploy script")


def log_conf(data):
    """
    Generating weblogic log config scripts.
    """
    with open(os.path.join(scripts_path, 'log_conf.py'), 'w') as f:
        template = read_j2('log_conf_py.j2')
        content = template.render(data=data)
        f.write(content)
    with open(os.path.join(scripts_path, 'log_conf.sh'), 'w') as f:
        template = read_j2('log_conf_sh.j2')
        if data['base'] == 'weblogic10_3':
            dir_name = 'opt'
        else:
            dir_name = 'oracle'
        content = template.render(dir=dir_name)  
        f.write(content)
    print("generated weblogic log configuration scripts")


if __name__ == '__main__':
    data = read_yml('build.yaml')
    t1 = threading.Thread(target=gen_dockerfile, args=(data,))
    t2 = threading.Thread(target=gen_startall, args=(data,))
    t3 = threading.Thread(target=log_conf, args=(data,))
    t4 = threading.Thread(target=gen_py, args=('build.yaml', 'data.yaml'))
    threads = [t1, t2, t3, t4]
    for i in range(4):
        threads[i].start()
    for i in range(4):
        threads[i].join()

    try:
        client = docker.APIClient(base_url='tcp://10.1.197.213:2375')
    except Exception as e:
        print("ERROR: {}".format(e))
    tag = '_'.join([data['buildargs']['APP_ENV'], data['buildargs']['PROJECTNAME'], data['buildargs']['APP_NAME']])
    print(tag)
    for line in client.build(path=build_path, rm=True, tag=tag, dockerfile=os.path.join(build_path, 'Dockerfile'),
                             buildargs=data['buildargs']):
        print(line)
