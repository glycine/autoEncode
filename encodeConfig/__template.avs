PluginDir = "C:\Software\AviSynth\plugins\"
SourceDir = "${WORK_DIR}\"
LoadPlugin( PluginDir + "LoadPluginEx.dll")
LoadPlugin( PluginDir + "warpsharp.dll")
LoadPlugin( PluginDir + "IT.dll")
LoadPlugin( PluginDir + "ColorYUY2_for_25.dll")
LoadPlugin( PluginDir + "itvfr.auf")
LoadAviUtlinputPlugin( PluginDir + "m2v.vfp", "MPEG2VIDEO")

MPEG2VIDEO( SourceDir + "${BASE_FILENAME}.m2v")
AudioDub( last, WavSource( SourceDir + "${BASE_FILENAME}.wav"))

AssumeFrameBased().ComplementParity()
#IT( fps=30, ref="TOP", blend=false )
#Trim( , ) ++ Trim( , ) ++ Trim( , ) ++ Trim( , )
#ITVFR( ref="TOP", diMODE=0, Debug=false)

Crop( ${CROP_WIDTH}, 0, -${CROP_WIDTH}, 0)
#ConvertToYUY2()
#Lanczos3Resize( , )
ConvertToYV12()
