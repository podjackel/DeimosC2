@REM Execution Flow:
@REM   Parse Token from package.json
@REM   Derive variables
@REM   IF `docker` arg is supplied, build using docker
@REM     Check for docker executable
@REM     Delete old `deimosc2_vue` images
@REM     Delete old frontend files from Go Server and local `dist` directory
@REM     Build `deimosc2_vue` Docker Image
@REM     Start `deimosc2_vue` container
@REM     Copy frontend build from container
@REM     Kill container
@REM     Copy frontend file from `dist` directory to Deimos Go Server
@REM   ELSE build with NPM
@REM     Check for NPM executable
@REM     execute `npm run build`
@REM     Delete old frontend files from Go Server and local `dist` directory
@REM     Copy frontend file from `dist` directory to Deimos Go Server

@ECHO OFF

@REM Extract version number
FOR /F "tokens=*" %%a in ('findstr /RC:"version.*[0-9]\.[0-9]\.[0-9]" .\frontend\package.json') do SET OUTPUT=%%a
SET VERSION=%OUTPUT:~12,-2%
SET IMAGE=deimosc2_vue:%VERSION%
SET NAME=deimos-build

IF "%1"=="docker" (
    ECHO ** Docker Building Version %VERSION%
    @REM Checking for Docker executable
    where /q docker.exe || ECHO "** Warning: Docker command not found" && EXIT /b 1
    
    FOR /f "tokens=*" %%i IN ('docker images --format "{{.ID}}" %IMAGE%') DO (
        ECHO ** Notice: Deleting old images
        docker rmi %%i
    )

    CALL :DELETE_FRONTEND

    ECHO ** Building %NAME% from %IMAGE%...
    docker build -t %IMAGE% -f .\DockerFrontend .
    
    ECHO ** Starting container %NAME%...
    docker run --rm --detach --name %NAME% %IMAGE%

    ECHO ** Copying from container %NAME%...
    docker cp %NAME%:/app/dist ./frontend/dist

    ECHO ** Killing container %NAME%...
    docker kill %NAME%

    CALL :COPY_FRONTEND

    EXIT /b 0
) ELSE (
    @REM Checking for NPM
    WHERE /q npm.exe || ECHO "** Warning: NPM command not found" && EXIT /b 1

    ECHO ** NPM Building Version %VERSION%
    ECHO Building Frontend...
    call npm run build

    :DELETE_FRONTEND
    :COPY_FRONTEND
)

EXIT

:DELETE_FRONTEND
    echo ** Deleting old files...
    del /S /Q .\resources\frontend\static\*
    del /S /Q .\frontend\dist\*
    EXIT /b

:COPY_FRONTEND
    echo Copying Frontend to Deimos Server...
    xcopy .\frontend\dist\* .\resources\frontend\static\ /Y /S /Q
    EXIT /b