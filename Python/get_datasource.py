import os
import re
import threading
from ruamel import yaml

father_dir, current_dir = os.path.split(os.getcwd())
datasource_path = os.path.join(father_dir, 'container', 'dockerfile')
print(datasource_path)
obj_path = os.listdir(datasource_path)
print(obj_path)
obj_files = {'deploy-test.py', 'deploy-uat.py', 'deploy-deliver.py', 'deploy-dev.py'}


def handle_content(readfile, writefile):
    """
    readfile : file read from 
    writefile: file write into
    """
    with open(readfile, 'r') as fr:

        datasource = []
        item = {}
        for line in fr.readlines():
            if re.match('^ds', line):
                print(line)
                key, value = line.strip().split('="')
                value = value.strip('"')
                print(key, value)
                if len(item):
                    for key1, value1 in item.items():
                        item[key1].update({key: value})
                else:
                    item[value] = {key: value}
                
            else:
                if len(item) == 0:
                    continue
                else:
                    datasource.append(item)
                    item = {}
        print(datasource)
        with open(writefile, 'w') as fw:
            yaml.round_trip_dump(datasource, fw, default_flow_style=False, indent=2)


for path in obj_path:
   project_path = os.path.join(datasource_path, path)
   print(project_path)
   scripts_path = os.path.join(project_path, 'container-scripts')
   print(scripts_path)
   if os.path.exists(scripts_path):  # check container-scripts dir exists or not
       create_files = obj_files.intersection(os.listdir(scripts_path))  # get intersection to get file to read
    #    print(create_files)
       print(os.getcwd())
       os.mkdir(path)

       for file in create_files:
           handle_content(os.path.join(scripts_path, file), os.path.join(os.getcwd(), path, '.'.join([file.split('.')[0], 'yml'])))
        #    print(file)

    #    print(create_files)
    #    os.mkdir(os.path.join(father_dir, current_dir, path))