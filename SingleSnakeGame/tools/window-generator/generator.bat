@echo off
set codeTemplateBasePath=%cd%
set codeTemplateFilePath=%cd%\\src\\CodeTemplate.js
set time=%date:~0,4%/%date:~5,2%/%date:~8,2%
echo 请输入文件名，如PayWindow
set /p fileName=文件名：
set ruleList=[{\"regular\":\"&.*?&\",\"replaceString\":\"%time%\"},{\"regular\":\"#.*?#\",\"replaceString\":\"%fileName%\"}]
cd ..
cd util
node CodeGenerator.js %fileName% %codeTemplateBasePath% %codeTemplateFilePath% %ruleList%
pause
exit