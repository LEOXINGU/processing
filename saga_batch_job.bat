set SAGA=C:/PROGRA~1/QGIS3~1.4/apps\saga-ltr
set SAGA_MLB=C:/PROGRA~1/QGIS3~1.4/apps\saga-ltr\modules
PATH=%PATH%;%SAGA%;%SAGA_MLB%
call saga_cmd shapes_lines "Convert Points to Line(s)"  -POINTS "C:/Users/sazon/AppData/Local/Temp/processing_98f221fcfc8148388c63c0fe09a88d31/1843708110e847f8b4aa41fc4647694f/POINTS.shp" -ORDER "fid" -SEPARATE "tipo" -LINES "C:/Users/sazon/AppData/Local/Temp/processing_98f221fcfc8148388c63c0fe09a88d31/573170384908459fbcfe5b65bc7d2292/LINES.shp"
exit