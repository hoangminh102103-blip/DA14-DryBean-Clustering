@echo off
echo ===================================================
echo   CAI DAT MOI TRUONG DU AN DA14-DryBean
echo ===================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python tren may. Vui long cai dat Python truoc!
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/3] Dang tao moi truong ao .venv ...
    python -m venv .venv
) else (
    echo [1/3] Moi truong ao .venv da ton tai, chuyen sang buoc cai thu vien.
)

echo [2/3] Dang kich hoat .venv va nang cap pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo [3/3] Dang tai va cai dat thu vien tu requirements.txt...
pip install -r requirements.txt

echo ===================================================
echo   CAI DAT THANH CONG!
echo   De bat moi truong trong Terminal, chay lenh:
echo   .venv\Scripts\activate
echo ===================================================
pause