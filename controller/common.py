import base64
import random

import py7zr
import zipfile
import os
from unrar import rarfile


def encode_base64(source):
    base64_data = base64.b64encode(source)
    s = base64_data.decode()
    return s

def decode_base64(source):
    return base64.b64decode(source)

def fakef_ip(ip):
    ip = str(ip)
    ip_sp = ip.split(".")
    ip_sp[-1] = str(random.randint(1,254))
    fake_ip = ".".join(ip_sp)
    return fake_ip


def unzip_file(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:     
        f = zipfile.ZipFile(zip_src, 'r')
        for file in f.namelist():
            f.extract(file, dst_dir)       
    else:
        print('This is not zip')

def un7z_file(_7z_src, dst_dir):
    r = py7zr.is_7zfile(_7z_src)
    if r:     
        py7zr.unpack_7zarchive(_7z_src, dst_dir)      
    else:
        print('This is not 7z')

def unrar_file(rar_src, dst_dir):
    r = rarfile.is_rarfile(rar_src)
    if r:     
        f = rarfile.RarFile(rar_src)
        for file in f.namelist():
            f.extract(file, dst_dir)  
    else:
        print('This is not rar')

def un7zr(file_path:str, replace:bool=False):
    f_type = file_path.split(".")[-1:][0]
    outdir = file_path+'_files'

    if f_type.lower() in ["zip"]:
        unzip_file(file_path, outdir)
        if replace: os.remove(file_path)
        return outdir

    if f_type.lower() in ["7z"]:
        un7z_file(file_path, outdir)
        if replace: os.remove(file_path)
        return outdir

    if f_type.lower() in ["rar"]:
        unrar_file(file_path, outdir)
        if replace: os.remove(file_path)
        return outdir

    return None


def list_dir(CurPath:str, file_list:list=list()):
    FileList = os.listdir(CurPath)
    for File in FileList:
        SubPath = CurPath+'/'+File       
        if os.path.isdir(SubPath):
            list_dir(SubPath, file_list)
        else:
            file_list.append(SubPath)    
    return file_list


def force_dir_7zr(dir:str='.'):
    files = list_dir(CurPath=dir, file_list=[])
    for f in files:
        r = un7zr(f, True)
        if r: force_dir_7zr(r)








