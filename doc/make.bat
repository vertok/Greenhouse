@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=python -m sphinx
)
set SOURCEDIR=source
set BUILDDIR=build

REM Check if Sphinx is installed
%SPHINXBUILD% -h >NUL 2>NUL
if errorlevel 1 (
    echo.
    echo.Error: Sphinx was not found. Make sure you have Sphinx
    echo.installed and that it is in your PATH environment variable.
    echo.
    echo.You can install Sphinx using pip:
    echo.  pip install sphinx
    echo.
    exit /b 1
)

if "%1" == "" goto help

if "%1" == "doc" goto doc

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
if errorlevel 1 (
    echo.
    echo.Error: Sphinx build failed with error code %errorlevel%.
    goto end
)

goto end

:doc
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
if errorlevel 1 (
    echo.
    echo.Error: Sphinx build failed with error code %errorlevel%.
    goto end
)
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
if errorlevel 1 (
    echo.
    echo.Error: Sphinx help failed with error code %errorlevel%.
    goto end
)

goto end

:end
popd
