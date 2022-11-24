"""Provide functions to use read or write

Available storage types are :
- S3 (path are preffixed with `s3://`)
- CEPH (path are preffixed with `ceph://`)
- FILE (path are preffixed with `file://`, but it is the default paths' interpretation)

According to functions, all storage types are not necessarily available.

Using S3 storage requires environment variables :
- ROK4_S3_KEY
- ROK4_S3_SECRETKEY
- ROK4_S3_URL

Using S3 storage requires environment variables :
- ROK4_CEPH_CONFFILE
- ROK4_CEPH_USERNAME
- ROK4_CEPH_CLUSTERNAME
"""

import boto3
from boto3.s3.transfer import TransferConfig
config = TransferConfig(multipart_chunksize=65536)
import tempfile
import re
import os
import rados
import hashlib
from typing import Dict, List, Tuple
from enum import Enum
from shutil import copyfile

from rok4.Exceptions import *

class StorageType(Enum):
    FILE = "file://"
    S3 = "s3://"
    CEPH = "ceph://"

__S3_CLIENT = None
def __get_s3_client() -> 'boto3.client':
    """Get the S3 client

    Create it if not already done

    Raises:
        MissingEnvironmentError: Missing S3 storage informations
        StorageError: S3 client configuration issue

    Returns:
        boto3.client: S3 client
    """    
    global __S3_CLIENT

    if __S3_CLIENT is None:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id = os.environ["ROK4_S3_KEY"],
                aws_secret_access_key = os.environ["ROK4_S3_SECRETKEY"],
                endpoint_url = os.environ["ROK4_S3_URL"]
            )
        except KeyError as e:
            raise MissingEnvironmentError(e)
        except Exception as e:
            raise StorageError("S3", e)
    
    return s3_client

__CEPH_CLIENT = None
__CEPH_IOCTXS = dict()
def __get_ceph_ioctx(pool: str) -> 'rados.Ioctx':
    """Get the CEPH IO context

    Create it (client and context) if not already done

    Args:
        pool (str): CEPH pool's name

    Raises:
        MissingEnvironmentError: Missing CEPH storage informations
        StorageError: CEPH IO context configuration issue

    Returns:
        rados.Ioctx: IO ceph context
    """    
    global __CEPH_CLIENT, __CEPH_IOCTXS

    if __CEPH_CLIENT is None:
        try:
            __CEPH_CLIENT = rados.Rados(
                conffile = os.environ["ROK4_CEPH_CONFFILE"],
                clustername = os.environ["ROK4_CEPH_CLUSTERNAME"],
                name = os.environ["ROK4_CEPH_USERNAME"]
            )

            __CEPH_CLIENT.connect()
            
        except KeyError as e:
            raise MissingEnvironmentError(e)
        except Exception as e:
            raise StorageError("CEPH", e)

    if pool not in __CEPH_IOCTXS:
        try:
            __CEPH_IOCTXS[pool] = __CEPH_CLIENT.open_ioctx(pool)
        except Exception as e:
            raise StorageError("CEPH", e)
    
    return __CEPH_IOCTXS[pool]

__OBJECT_SYMLINK_SIGNATURE = "SYMLINK#"

def get_infos_from_path(path: str) -> Tuple[StorageType, str, str, str]:
    """Extract storage type, the unprefixed path, the container and the basename from path (Default: FILE storage)

    For a FILE storage, the tray is the directory and the basename is the file name.
    
    For an object storage (CEPH or S3), the tray is the bucket or the pool and the basename is the object name.

    Args:
        path (str): path to analyse

    Returns:
        Tuple[StorageType, str]: storage type and cleaned path (storage prefix removed)
    """

    if path.startswith("s3://"):
        bucket_name, object_name = path[5:].split("/", 1)
        return StorageType.S3, path[5:], bucket_name, object_name
    elif path.startswith("ceph://"):
        pool_name, object_name = path[7:].split("/", 1)
        return StorageType.CEPH, path[7:], pool_name, object_name
    elif path.startswith("file://"):
        return StorageType.FILE, path[7:], os.path.dirname(path[7:]), os.path.basename(path[7:])
    else:
        return StorageType.FILE, path, os.path.dirname(path), os.path.basename(path)


#def get_path_from_infos(storage_type: StorageType, tray: str, base_name: str) -> str:
def get_path_from_infos(storage_type: StorageType, *args) -> str:
    return f"{storage_type.value}{os.path.join(*args)}"


def hash_file(path: str) -> str:
    """Process MD5 sum of the provided file

    Args:
        path (str): path to file

    Returns:
        str: hexadeimal MD5 sum
    """

    checker = hashlib.md5()

    with open(path,'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(65536)
            checker.update(chunk)

    return checker.hexdigest()

def get_data_str(path: str) -> str:
    """Load data into a string

    Args:
        path (str): path to data

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue

    Returns:
        str: Data content
    """

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        
        s3_client = __get_s3_client()

        try:
            with tempfile.NamedTemporaryFile("w+b") as f:
                s3_client.download_fileobj(tray_name, base_name, f)
                f.seek(0)
                data = f.read().decode('utf-8')
                f.close()
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            size, mtime = ioctx.stat(base_name)
            data = ioctx.read(base_name, size).decode('utf-8')
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:

        try:
            f = open(path)
            data = f.read()
            f.close()
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to read string data")

    return data


def put_data_str(data: str, path: str) -> None:
    """Store string data into a file or an object

    UTF-8 encoding is used for bytes conversion

    Args:
        data (str): data to write
        path (str): destination path, where to write data

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage write issue
    """

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        
        s3_client = __get_s3_client()

        try:
            s3_client.put_object(
                Body = data.encode('utf-8'),
                Bucket = tray_name,
                Key = base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            ioctx.write_full(base_name, data.encode('utf-8'))
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:

        try:
            f = open(path, 'w')
            f.write(data)
            f.close()
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to write string data")


def get_size(path: str) -> int:
    """Get size of file or object

    Args:
        path (str): path of file/object whom size is asked

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue

    Returns:
        int: file/object size, in bytes
    """

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        
        s3_client = __get_s3_client()

        try:
            size = s3_client.head_object(Bucket=tray_name, Key=base_name)["ContentLength"].strip('"')
            return size
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:

        ioctx = __get_ceph_ioctx(tray_name)

        try:
            size, mtime = ioctx.stat(base_name)
            return size
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:

        try:
            file_stats = os.stat(path)
            return file_stats.st_size
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to get size")


def remove(path: str) -> None:
    """Remove the file/object

    Args:
        path (str): path of file/object to remove

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage removal issue
    """

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        
        s3_client = __get_s3_client()

        try:
            s3_client.delete_object(
                Bucket=tray_name,
                Key=base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:

        ioctx = __get_ceph_ioctx(tray_name)

        try:
            ioctx.remove_object(base_name)
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:

        try:
            os.remove(path)
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to remove things")

def copy(from_path: str, to_path: str, from_md5: str = None) -> None:
    """Copy a file or object to a file or object place. If MD5 sum is provided, it is compared to sum after the copy.

    Args:
        from_path (str): source file/object path, to copy
        to_path (str): destination file/object path
        from_md5 (str, optional): MD5 sum, re-processed after copy and controlled. Defaults to None.

    Raises:
        StorageError: Unhandled copy or copy issue
        MissingEnvironmentError: Missing object storage informations
    """

    from_type, from_path, from_tray, from_base_name  = get_infos_from_path(from_path)
    to_type, to_path, to_tray, to_base_name  = get_infos_from_path(to_path)

    # Réalisation de la copie, selon les types de stockage
    if from_type == StorageType.FILE and to_type == StorageType.FILE :
        
        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)

            copyfile(from_path, to_path)

            if from_md5 is not None :
                to_md5 = hash_file(to_path)
                if to_md5 != from_md5:
                    raise StorageError(f"FILE", f"Invalid MD5 sum control for copy file {from_path} to {to_path} : {from_md5} != {to_md5}")

        except Exception as e:
            raise StorageError(f"FILE", f"Cannot copy file {from_path} to {to_path} : {e}")

    elif from_type == StorageType.S3 and to_type == StorageType.FILE :

        s3_client = __get_s3_client()

        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)

            s3_client.download_file(from_tray, from_base_name, to_path)

            if from_md5 is not None :
                to_md5 = hash_file(to_path)
                if to_md5 != from_md5:
                    raise StorageError(f"S3 and FILE", f"Invalid MD5 sum control for copy S3 object {from_path} to file {to_path} : {from_md5} != {to_md5}")

        except Exception as e:
            raise StorageError(f"S3 and FILE", f"Cannot copy S3 object {from_path} to file {to_path} : {e}")

    elif from_type == StorageType.FILE and to_type == StorageType.S3 :

        s3_client = __get_s3_client()
        
        try:
            s3_client.upload_file(from_path, to_tray, to_base_name, Config=config)

            if from_md5 is not None :
                to_md5 = s3_client.head_object(Bucket=to_bucket, Key=to_object)["ETag"].strip('"')
                if to_md5 != from_md5:
                    raise StorageError(f"FILE and S3", f"Invalid MD5 sum control for copy file {from_path} to S3 object {to_path} : {from_md5} != {to_md5}")
        except Exception as e:
            raise StorageError(f"FILE and S3", f"Cannot copy file {from_path} to S3 object {to_path} : {e}")

    elif from_type == StorageType.S3 and to_type == StorageType.S3 :

        s3_client = __get_s3_client()

        try:
            s3_client.copy(
                {
                    'Bucket': from_tray,
                    'Key': from_base_name
                }, 
                to_tray, to_base_name
            )

            if from_md5 is not None :
                to_md5 = s3_client.head_object(Bucket=to_tray, Key=to_base_name)["ETag"].strip('"')
                if to_md5 != from_md5:
                    raise StorageError(f"S3", f"Invalid MD5 sum control for copy S3 object {from_path} to {to_path} : {from_md5} != {to_md5}")
        except Exception as e:
            raise StorageError(f"S3", f"Cannot copy S3 object {from_path} to {to_path} : {e}")
        

    elif from_type == StorageType.CEPH and to_type == StorageType.FILE :

        ioctx = __get_ceph_ioctx(from_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:

            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)
            f = open(to_path, 'wb')

            offset = 0
            size = 0

            while True:
                chunk = ioctx.read(from_base_name, 65536, offset)
                size = len(chunk)
                offset += size
                f.write(chunk)

                if from_md5 is not None:
                    checker.update(chunk)

                if size < 65536:
                    break

            f.close()

            if from_md5 is not None and from_md5 != checker.hexdigest():
                raise StorageError(f"CEPH and FILE", f"Invalid MD5 sum control for copy CEPH object {from_path} to file {to_path} : {from_md5} != {checker.hexdigest()}")

        except Exception as e:
            raise StorageError(f"CEPH and FILE", f"Cannot copy CEPH object {from_path} to file {to_path} : {e}")


    elif from_type == StorageType.FILE and to_type == StorageType.CEPH :

        ioctx = __get_ceph_ioctx(to_tray)
        
        if from_md5 is not None:
            checker = hashlib.md5()

        try:
            f = open(from_path, 'rb')

            offset = 0
            size = 0

            while True:

                chunk = f.read(65536)
                size = len(chunk)
                ioctx.write(to_base_name, chunk, offset)
                offset += size

                if from_md5 is not None:
                    checker.update(chunk)

                if size < 65536:
                    break

            f.close()

            if from_md5 is not None and from_md5 != checker.hexdigest():
                raise StorageError(f"FILE and CEPH", f"Invalid MD5 sum control for copy file {from_path} to CEPH object {to_path} : {from_md5} != {checker.hexdigest()}")

        except Exception as e:
            raise StorageError(f"FILE and CEPH", f"Cannot copy file {from_path} to CEPH object {to_path} : {e}")


    elif from_type == StorageType.CEPH and to_type == StorageType.CEPH :

        from_ioctx = __get_ceph_ioctx(from_tray)
        to_ioctx = __get_ceph_ioctx(to_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:

            offset = 0
            size = 0

            while True:
                chunk = from_ioctx.read(from_base_name, 65536, offset)
                size = len(chunk)
                to_ioctx.write(to_base_name, chunk, offset)
                offset += size

                if md5 is not None:
                    checker.update(chunk)

                if size < 65536:
                    break

            if md5 is not None and md5 != checker.hexdigest():
                raise StorageError(f"FILE and CEPH", f"Invalid MD5 sum control for copy CEPH object {from_path} to {to_path} : {md5} != {checker.hexdigest()}")

        except Exception as e:
            raise StorageError(f"CEPH", f"Cannot copy CEPH object {from_path} to {to_path} : {e}")


    else:
        raise StorageError(f"{from_type.name} and {to_type.name}", f"Cannot copy from {from_type.name} to {to_type.name}")



def link(target_path: str, link_path: str, hard: bool = False) -> None:
    """Create a symbolic link

    Args:
        target_path (str): file/object to link
        link_path (str): link to create
        hard (bool, optional): hard link rather than symbolic. Only for FILE storage. Defaults to False.

    Raises:
        StorageError: Unhandled link or link issue
        MissingEnvironmentError: Missing object storage informations
    """

    target_type, target_path, target_tray, target_base_name  = get_infos_from_path(target_path)
    link_type, link_path, link_tray, link_base_name  = get_infos_from_path(link_path)

    if target_type != link_type:
        raise StorageError(f"{target_type.name} and {link_type.name}", f"Cannot make link between two different storage types")

    if hard and target_type != StorageType.FILE:
        raise StorageError(target_type.name, "Hard link is available only for FILE storage")

    # Réalisation du lien, selon les types de stockage
    if target_type == StorageType.S3:
        
        s3_client = __get_s3_client()

        try:
            s3_client.put_object(
                Body = f"{__OBJECT_SYMLINK_SIGNATURE}{target_path}".encode('utf-8'),
                Bucket = link_tray,
                Key = link_base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif target_type == StorageType.CEPH:
        
        ioctx = __get_ceph_ioctx(link_tray)

        try:
            ioctx.write_full(link_base_name, f"{__OBJECT_SYMLINK_SIGNATURE}{target_path}".encode('utf-8'))
        except Exception as e:
            raise StorageError("CEPH", e)

    elif target_type == StorageType.FILE:

        try:
            if hard:
                os.link(target_path, link_path)
            else:
                os.symlink(target_path, link_path)
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to make link")
