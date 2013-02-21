# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     01/02/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os
import os.path
from functools import reduce

class keys:
	# workspaceの絶対パス
	WORKSPACE_PATH = "workspace_path"

	# workspaceのdir名
	WORKSPACE = "workspace"

	# 自分で定義した放送局名
	SERVICE = "service"

	# 自分で定義した番組命
	BASE_TITLE = "base_title"


class filenames:
	# 各workspaceのencode設定が格納されたファイル名
	ENC_INFO_FILE = "__encInfo.json"
	# 旧バージョンのencode設定が格納されたファイル名
	DEPRECATE_ENC_INFO_FILE = "__enc.config"
	# encode処理をskipするFLAGファイル名
	ENC_SKIP_FILE = "__skip_encode"

def __get_program_dirlist(service, base_title, root_dir ):
	program_dirlist = os.listdir(os.path.join( root_dir, base_title, service))
	return [{keys.WORKSPACE_PATH: os.path.join(root_dir, base_title, service, x),
				keys.WORKSPACE: x,
				keys.SERVICE: service,
				keys.BASE_TITLE: base_title} for x in program_dirlist]

def __get_service_dirlist(base_title, root_dir):
	service_dirlist = os.listdir(os.path.join(root_dir, base_title))
	program_dirlist = [__get_program_dirlist(x, base_title, root_dir) for x in service_dirlist]
	return reduce(lambda a,b:a+b, program_dirlist)

def get_workspace_list(root_dir):
	base_title_list = os.listdir(root_dir)
	service_dirlist = [__get_service_dirlist(x, root_dir) for x in base_title_list]
	return reduce(lambda a,b:a+b, service_dirlist)
