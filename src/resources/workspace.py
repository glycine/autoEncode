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

import os.path
import re
import sys
from functools import reduce

class keys:
	# workspaceの絶対パス
	WORKSPACE_PATH = "workspace_path"
	# workspaceのdir名
	WORKSPACE = "workspace"
	# 自分で定義した放送局名
	SERVICE = "service"
	# 自分で定義した番組名
	BASE_TITLE = "base_title"
	# demux後の各種ファイルのベース名
	BASE_NAME = "base_name"
	# IEPG由来の名前
	IEPG_NAME = "iepg_name"
	# フラグを除去したIEPG_NAME
	PLAIN_IEPG_NAME = "plain_iepg_name"
	# フラグリスト
	FLAGS = "flags"
	# 字幕のフラグ
	VALID_SUB_TITLE = "valid_sub_title"
	# 二ヶ国語のフラグ
	VALID_MULTI_LANGUAGE = "valid_multi_language"
	# 複数音声ストリームのフラグ
	VALID_MULTI_SOUND_STREAM = "valid_multi_sound_stream"
	# 5.1ch音声のフラグ
	VALID_SURROUND = "valid_surround"

class consts:
	# 文字列分離
	SPLIT_CHAR = "_"
	# 元のソースが入ったディレクトリ
	SOURCE_DIRNAME = "source"
	# tsファイルの拡張子
	TS_EXT = ".ts"
	# 番組情報ファイルの拡張子
	INFO_EXT = ".program.txt"

class filenames:
	# 各workspaceのencode設定が格納されたファイル名
	ENC_INFO_FILE = "__encInfo.json"
	# 旧バージョンのencode設定が格納されたファイル名
	DEPRECATE_ENC_INFO_FILE = "__enc.config"
	# encode処理をskipするFLAGファイル名
	ENC_SKIP_FILE = "__skip_encode"

def __get_base_name( workspace ):
	tokens = workspace.split(consts.SPLIT_CHAR)
	return tokens[0] + consts.SPLIT_CHAR + tokens[1]

def __get_iepg_name( workspace_path ):
	info_filenamelist = [x for x in os.listdir( workspace_path )
						if os.path.isfile( os.path.join( workspace_path, x))
							and x.endswith( consts.INFO_EXT)]

	if len( info_filenamelist ) < 1:
		return
	tokens = info_filenamelist[0].split( consts.SPLIT_CHAR )
	return tokens[0]

def __analyze_iepg_name( iepg_name ):
	if not iepg_name:
		return {keys.PLAIN_IEPG_NAME: "",
			keys.FLAGS:
				{keys.VALID_SUB_TITLE: False,
				keys.VALID_MULTI_LANGUAGE: False,
				keys.VALID_MULTI_SOUND_STREAM: False,
				keys.VALID_SURROUND: False}}
	r = re.compile(r"\[.+?\]")
	matches = r.findall(iepg_name)
	flag_removed_iepg_name = re.sub( r"\[.+?\]", "", iepg_name)
	## flagを探す
	## 判別に利用するFlag
	# [字]: 字幕がある
	# [二]: 二ヶ国語放送
	# [多]: 複数音声ストリーム
	# [SS]: サラウンド
	## 無視するフラグ
	# [S]: ステレオ
	# [無]: 無料
	# [新]: 新番組
	# [終]: 最終回
	# [デ]: 番組連動データ放送
	# [HV]: ハイビジョン？
	sub_title = False
	if "[字]" in matches:
		sub_title = True
	multi_language = False
	if "[二]" in matches:
		multi_language = True
	multi_sound_stream = False
	if "[多]" in matches:
		multi_sound_stream = True
	surround = False
	if "[SS]" in matches:
		surround = True
	return {keys.PLAIN_IEPG_NAME: flag_removed_iepg_name,
			keys.FLAGS: {keys.VALID_SUB_TITLE: sub_title,
						keys.VALID_MULTI_LANGUAGE: multi_language,
						keys.VALID_MULTI_SOUND_STREAM: multi_sound_stream,
						keys.VALID_SURROUND: surround}}

def __get_program_dirlist(service, base_title, root_dir ):
	program_dirlist = [x for x in os.listdir(os.path.join( root_dir, base_title, service))
						if os.path.isdir( os.path.join( root_dir, base_title, service, x))]
	result =  [{keys.WORKSPACE_PATH: os.path.join(root_dir, base_title, service, x),
				keys.WORKSPACE: x,
				keys.SERVICE: service,
				keys.BASE_TITLE: base_title,
				keys.BASE_NAME: __get_base_name( x )} for x in program_dirlist]
	[x.update( {keys.IEPG_NAME: __get_iepg_name( x[keys.WORKSPACE_PATH] )}) for x
			in result]
	[x.update( __analyze_iepg_name( x[keys.IEPG_NAME] )) for x
		in result]
	return result

def __get_service_dirlist(base_title, root_dir):
	service_dirlist = [x for x in os.listdir(os.path.join(root_dir, base_title))
						if os.path.isdir( os.path.join( root_dir, base_title, x))]
	program_dirlist = [__get_program_dirlist(x, base_title, root_dir) for x in service_dirlist]
	return reduce(lambda a,b:a+b, program_dirlist)

def get_workspace_list(root_dir):
	base_title_list = [x for x in os.listdir(root_dir)
						if os.path.isdir( os.path.join( root_dir, x))]
	service_dirlist = [__get_service_dirlist(x, root_dir) for x in base_title_list]
	return reduce(lambda a,b:a+b, service_dirlist)

def main():
	if len(sys.argv) < 2:
		print( "Usage: ${exec} root_dir")
		sys.exit()
	print( sys.argv[1])
	print( get_workspace_list( sys.argv[1]))

if __name__ == "__main__":
	main()
