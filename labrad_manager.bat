:: This file may have to be tweaked for your specific PC. Just consider it a starting point. 
start cmd /k manager\scalabrad-0.8.3\bin\labrad.bat
start cmd /k manager\scalabrad-web-server-2.0.5\bin\labrad-web.bat
start chrome /new-window http://localhost:7667
call conda.bat activate dioptric
call python -m labrad.node