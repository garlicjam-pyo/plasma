# 독립 제어 GUI 서버 설치·접속 안내

> 2026-11-13 · 주제 3 팀. 독립 제어 GUI(`sim/app/`)를 다른 컴퓨터에서 쓰는 방법.

## 1. 두 가지 사용 방식

다른 컴퓨터에서 쓰는 방법은 두 가지이고, 대부분의 경우 방식 A(그 컴퓨터에 직접 설치)가 맞습니다.

이 프로그램은 두 부분으로 되어 있습니다. 계산을 하는 서버(파이썬)와, 그 결과를 보여 주는 화면(브라우저)입니다. 어느 컴퓨터에서 계산을 돌리고 어느 컴퓨터에서 화면을 여느냐에 따라 방식이 갈립니다.

|  | 방식 A: 각 컴퓨터에 설치 | 방식 B: 한 대에서 켜고 접속 |
| --- | --- | --- |
| 계산이 도는 곳 | 쓰는 사람의 컴퓨터 | 서버를 켠 컴퓨터 한 대 |
| 다른 컴퓨터에 필요한 것 | Python, git, 패키지 설치 | 브라우저만 |
| 네트워크 | 설치할 때만 인터넷 필요. 실행은 오프라인 가능 | 두 컴퓨터가 같은 Wi-Fi나 유선 네트워크에 있어야 함 |
| 맞는 경우 | 팀원이 각자 쓸 때, 장소가 서로 다를 때 | 발표장에서 다른 노트북이나 태블릿으로 보여 줄 때, Python을 설치할 수 없는 기기 |
| 주의 | 컴퓨터마다 업데이트를 따로 받아야 함 | 로그인 절차가 없음. 믿을 수 있는 네트워크에서만 사용 |

아래 2–4절이 방식 A, 5절이 방식 B입니다. 방식 B도 서버를 켜는 컴퓨터에는 방식 A의 설치가 먼저 되어 있어야 합니다.

## 2. 준비물

설치할 컴퓨터에 Python과 git이 있으면 됩니다. 서버 자체는 파이썬 표준 라이브러리만 쓰고, 계산 모델이 numpy와 scipy를 씁니다.

| 항목 | 필요한 것 | 확인 명령 | 없을 때 |
| --- | --- | --- | --- |
| Python | 3.10 이상 | `python --version` (Windows는 `py --version`, macOS·Linux는 `python3 --version`) | python.org 에서 설치. Windows는 설치 화면의 "Add Python to PATH"를 체크 |
| git | 아무 버전 | `git --version` | git-scm.com 에서 설치. 없이 하려면 3절의 ZIP 방법 |
| 브라우저 | Chrome, Edge, Firefox, Safari의 최근 버전 |  |  |
| 패키지 | numpy 1.24 이상, scipy 1.10 이상, matplotlib 3.7 이상 | 3절에서 한 번에 설치 |  |

matplotlib은 GUI가 아니라 그림을 저장하는 스크립트(`sim/run_hybrid.py`)가 씁니다. 같은 목록(`requirements.txt`)에 들어 있어 함께 설치됩니다.

코드는 저장소의 `topic/two-zone-model` 브랜치에 있습니다. `main` 브랜치에는 아직 GUI가 없으므로 브랜치를 바꾸는 단계를 빠뜨리면 안 됩니다.

## 3. 방식 A: 새 컴퓨터에 설치하기

처음 한 번만 하면 되는 절차이고, 네 단계입니다. 코드 받기, 브랜치 바꾸기, 가상환경 만들기, 패키지 설치.

가상환경(`.venv`)을 만드는 이유는 두 가지입니다. 최근의 Ubuntu와 macOS는 시스템 Python에 패키지를 바로 설치하지 못하게 막고, 가상환경 안에 설치하면 다른 프로젝트의 패키지 버전과 충돌하지 않습니다.

### Windows (PowerShell)

```powershell
git clone https://github.com/garlicjam-pyo/plasma.git
cd plasma
git checkout topic/two-zone-model
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`Activate.ps1` 에서 "스크립트를 실행할 수 없다"는 오류가 나면, 같은 창에서 `Set-ExecutionPolicy -Scope Process RemoteSigned` 를 먼저 실행합니다. 이 설정은 그 창을 닫으면 사라집니다.

### macOS

```bash
git clone https://github.com/garlicjam-pyo/plasma.git
cd plasma
git checkout topic/two-zone-model
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Linux, WSL (Ubuntu 기준)

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip

git clone https://github.com/garlicjam-pyo/plasma.git
cd plasma
git checkout topic/two-zone-model
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### git 없이 받기

GitHub 저장소 페이지에서 브랜치를 `topic/two-zone-model` 로 바꾼 뒤 Code → Download ZIP 으로 받아 압축을 풀고, 그 폴더에서 가상환경 만들기부터 이어서 합니다. 이 경우 업데이트는 ZIP을 다시 받아야 합니다.

## 4. 실행, 종료, 정상 동작 확인

`plasma` 폴더에서 가상환경을 켠 뒤 서버를 실행합니다. 터미널을 새로 열 때마다 가상환경을 다시 켜야 합니다.

```bash
cd plasma
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
python sim/app/server.py
```

정상이면 터미널에 아래 줄이 나오고 커서가 멈춥니다. 브라우저가 자동으로 열리며, 안 열리면 주소를 직접 입력합니다.

```
독립 제어 GUI: http://localhost:8765  (끝내려면 Ctrl+C)
```

서버는 이 터미널을 계속 차지합니다. **이 터미널에 다른 명령을 입력하거나 창을 닫으면 서버가 꺼지고**, 브라우저에는 "연결을 거부했습니다"가 납니다. 다른 명령은 터미널을 하나 더 열어 입력합니다. 끝낼 때는 서버 터미널에서 `Ctrl+C` 를 누릅니다.

| 옵션 | 뜻 | 쓰는 경우 |
| --- | --- | --- |
| `--port 8770` | 포트 번호를 바꿈 (기본 8765) | "Address already in use" 오류가 날 때 |
| `--no-browser` | 브라우저를 자동으로 열지 않음 | WSL, 원격 서버처럼 화면이 다른 곳에 있을 때 |
| `--host 0.0.0.0` | 다른 컴퓨터의 접속도 받음 (기본은 이 컴퓨터만) | 5절의 방식 B |

WSL에서는 `python sim/app/server.py --no-browser` 로 켜고, Windows 브라우저에서 `http://localhost:8765` 를 엽니다. `127.0.0.1` 로는 이어지지 않는 경우가 있어 `localhost` 를 씁니다.

### 제대로 설치됐는지 확인하는 세 가지

1. **화면의 기준값.** 처음 열면 300 W, 전류비 1, 위상차 0°, 10 mTorr 로 계산합니다. 오른쪽 위에 "계산 완료"가 뜨고 평균 밀도 5.22, 밀도비 1.268 이 보이면 다른 컴퓨터와 같은 결과입니다.
2. **목표로 맞추기.** 왼쪽 판에서 보라색 표적을 옷은 보라 영역 안의 다른 곳에 끌어다 놓습니다. 1초 안팎에 "목표에 도달했습니다"가 나오면 역문제 풀이가 동작하는 것입니다.
3. **자체 검산.** 새 터미널에서 `python sim/run_hybrid.py check` 를 실행합니다. 약 25초 뒤 11줄이 모두 "통과"로 나와야 합니다.

## 5. 방식 B: 한 컴퓨터에서 켜고 다른 컴퓨터에서 접속하기

서버를 `--host 0.0.0.0` 으로 켜면 같은 네트워크의 다른 컴퓨터가 브라우저만으로 접속할 수 있습니다. 기본값이 "이 컴퓨터만"인 이유는 서버에 로그인 절차가 없기 때문입니다.

### 절차

1. **서버 컴퓨터에서 켜기.**

   ```bash
   python sim/app/server.py --host 0.0.0.0 --no-browser
   ```

   터미널에 `다른 컴퓨터에서: http://192.168.x.x:8765` 같은 줄이 나옵니다. 이것이 다른 컴퓨터에서 열 주소입니다.
2. **서버 컴퓨터의 방화벽에서 8765번 포트 허용하기.** 운영체제별 방법은 아래 표에 있습니다.
3. **다른 컴퓨터의 브라우저에서 그 주소 열기.** 두 컴퓨터가 같은 Wi-Fi 나 같은 유선 네트워크에 있어야 합니다.

| 서버 컴퓨터 | 방화벽 허용 방법 |
| --- | --- |
| Windows | 처음 실행할 때 뜨는 "액세스 허용" 창에서 개인 네트워크를 허용. 창이 안 뜨면 관리자 PowerShell 에서 `New-NetFirewallRule -DisplayName "ICP GUI" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private` |
| macOS | 시스템 설정 → 네트워크 → 방화벽. 처음 실행할 때 뜨는 "들어오는 연결 허용" 창에서 허용 |
| Ubuntu | 방화벽(ufw)을 켜 둔 경우에만 `sudo ufw allow 8765/tcp` |

### 서버를 WSL2 에서 켠 경우

WSL2 는 Windows 안의 가상 네트워크에 있어서, 다른 컴퓨터가 WSL 의 주소에 바로 닿지 못합니다. 두 가지 중 하나를 고릅니다.

- **간단한 쪽: 서버를 Windows 에 직접 설치해 켠다.** 3절의 Windows 절차로 설치한 뒤 PowerShell 에서 `python sim\app\server.py --host 0.0.0.0` 을 실행합니다. WSL 의 설치는 그대로 두어도 됩니다.
- **WSL 에서 계속 켜려면: Windows 가 들어온 접속을 WSL 로 넘기게 한다.** 관리자 PowerShell 에서 아래를 실행합니다.

  ```powershell
  $wsl = (wsl hostname -I).Trim().Split(" ")[0]
  netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8765 connectaddress=$wsl connectport=8765
  New-NetFirewallRule -DisplayName "ICP GUI" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private
  ```

  이때 다른 컴퓨터가 열 주소는 WSL 이 아니라 **Windows 의 주소**입니다(PowerShell 에서 `ipconfig` 의 IPv4 주소). WSL 의 주소는 다시 시작하면 바뀔 수 있어 그때마다 위 명령을 다시 실행해야 합니다. 해제는 `netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8765` 입니다.

### 방화벽을 건드리지 않는 대안: SSH 터널

서버 컴퓨터에 SSH 로 접속할 수 있다면 `--host` 도 방화벽 설정도 필요 없습니다. 서버는 기본값 그대로 켜고, 접속하는 컴퓨터에서 아래를 실행한 뒤 브라우저로 `http://localhost:8765` 를 엽니다.

```bash
ssh -L 8765:127.0.0.1:8765 계정@서버주소
```

접속이 암호화되고 SSH 계정으로 사용자가 가려지므로, 네트워크를 믿기 어려울 때는 이 방법이 맞습니다.

### 주의점

- **로그인이 없습니다.** 주소를 아는 같은 네트워크의 누구나 계산을 시킬 수 있습니다. 집이나 연구실처럼 믿을 수 있는 네트워크에서만 `--host 0.0.0.0` 을 쓰고, 카페 같은 공용 Wi-Fi 에서는 쓰지 마세요. 공유기의 포트 개방으로 인터넷에 직접 내놓는 것도 하지 마세요.
- **계산은 한 번에 하나씩 돕니다.** 여러 사람이 동시에 쓰면 요청이 순서대로 처리됩니다. 운전점 하나는 0.1초 정도라 두세 명까지는 불편이 없고, 각자의 화면 상태는 서로 섞이지 않습니다.
- **학교나 기관의 Wi-Fi 는 기기끼리의 통신을 막아 둔 경우가 있습니다.** 설정이 맞는데도 안 열리면 휴대폰 핫스팟에 두 컴퓨터를 연결하거나 SSH 터널을 씁니다.
- 다 쓰면 서버 터미널에서 `Ctrl+C` 로 끕니다.

## 6. 업데이트 받기

코드가 바뀌면 설치한 컴퓨터마다 아래를 실행하고 서버를 다시 켭니다. 파이썬 코드는 서버를 다시 켜야 반영됩니다.

```bash
cd plasma
git pull
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt  # 패키지 목록이 바뀐 경우에만 실제로 설치됨
python sim/app/server.py
```

브라우저는 새로고침만 하면 됩니다. 서버가 화면 파일을 저장해 두지 말라고 브라우저에 알리므로 옛 화면이 남지 않습니다. 그래도 화면이 이상하면 `Ctrl+Shift+R` (macOS 는 `Cmd+Shift+R`)로 강제 새로고침합니다.

`git pull` 이 "로컬 변경 사항이 덮어쓰인다"며 멈추면 직접 고친 파일이 있는 것입니다. 고친 내용을 보관하려면 `git stash` 후 다시 `git pull` 하고, 필요하면 `git stash pop` 으로 되돌립니다.

## 7. 문제 해결

가장 흔한 원인은 서버가 꺼져 있는 것입니다. 브라우저에 오류가 나면 먼저 서버 터미널에 안내 줄이 남아 있고 커서가 멈춰 있는지 봅니다.

| 증상 | 원인 | 조치 |
| --- | --- | --- |
| 브라우저에 "연결을 거부했습니다" (ERR_CONNECTION_REFUSED) | 서버가 꺼져 있음. 터미널을 닫았거나, 서버 터미널에 다른 명령을 입력함 | 서버를 다시 켜고 그 터미널은 그대로 둠 |
| 서버는 켜져 있는데 WSL 에서만 안 열림 | `127.0.0.1` 이 WSL 로 이어지지 않음 | `http://localhost:8765` 로 열기. 그래도 안 되면 VS Code 의 포트 탭에서 8765 를 전달 |
| `ModuleNotFoundError: No module named 'numpy'` | 가상환경을 켜지 않았거나 패키지를 설치하지 않음 | 가상환경을 켠 뒤 `pip install -r requirements.txt` |
| `error: externally-managed-environment` | 시스템 Python 에 바로 설치하려 함 | 3절대로 가상환경을 만든 뒤 그 안에서 설치 |
| `can't open file ... sim/app/server.py` | `plasma` 폴더 밖에서 실행했거나 브랜치가 `main` | `cd plasma` 후 `git checkout topic/two-zone-model` |
| `Address already in use` | 같은 포트로 켠 서버가 아직 돌고 있음 | 이전 서버를 `Ctrl+C` 로 끄거나 `--port 8770` 으로 실행 |
| `Activate.ps1` 을 실행할 수 없다는 오류 (Windows) | PowerShell 의 스크립트 실행 제한 | `Set-ExecutionPolicy -Scope Process RemoteSigned` 후 다시 |
| 화면이 "서버에 연결하는 중…"에서 멈춤 | `index.html` 파일을 직접 열었거나 주소가 다름 | 파일을 더블클릭하지 말고 서버가 알려 준 주소로 열기 |
| "수렴하지 못함" 표시 | 설치 문제가 아님. 전력이 너무 낮거나 두 코일의 장이 상쇄되어 모델의 방전이 유지되지 않는 조건 | 전력을 올리거나 위상차를 줄임 |
| 목표로 맞추기가 2–8초 걸림 | 정상. 빠른 풀이가 닿지 못해 전류비 전 범위를 훑는 중 | 기다림. 목표가 옷은 보라 영역 밖이면 항상 이 단계를 거침 |
| 다른 컴퓨터에서 접속이 안 됨 (방식 B) | `--host 0.0.0.0` 누락, 방화벽, 서로 다른 네트워크, WSL2 | 아래 순서로 확인 |

방식 B 가 안 될 때는 안쪽부터 바깥쪽으로 확인합니다.

1. 서버 컴퓨터 자신의 브라우저에서 `http://localhost:8765` 가 열리는가. 안 열리면 서버 문제입니다.
2. 서버 터미널에 `다른 컴퓨터에서: http://…` 줄이 있는가. 없으면 `--host 0.0.0.0` 을 빼먹은 것입니다.
3. 서버 컴퓨터 자신의 브라우저에서 그 주소(`http://192.168.x.x:8765`)가 열리는가. 열리는데 다른 컴퓨터에서만 안 되면 방화벽이나 네트워크 문제입니다.
4. 두 컴퓨터의 주소 앞부분(예: `192.168.0.`)이 같은가. 다르면 서로 다른 네트워크입니다.

## 8. 확인된 환경과 확인하지 못한 환경

이 안내의 절차 중 실제로 돌려 본 것은 Linux 와 WSL2 뿐입니다. Windows 직접 설치, macOS, WSL2 의 포트 넘기기는 표준적인 방법을 적은 것이고 이 프로그램으로 시험하지는 못했습니다.

| 환경 | 확인 수준 |
| --- | --- |
| Linux, Python 3.13 | 설치부터 자체 검산, 화면 동작까지 직접 시험 (화면은 Chromium 자동 시험) |
| WSL2 Ubuntu 24.04 + VS Code + Windows 브라우저 | 방식 A 로 실행되는 것을 확인 |
| `--host 0.0.0.0` | Linux 에서 네트워크 주소로 접속되고, 기본값에서는 막히는 것을 확인 |
| Windows 에 직접 설치 (PowerShell) | 시험하지 못함 |
| macOS | 시험하지 못함 |
| WSL2 포트 넘기기(`netsh`), Windows·macOS 방화벽 설정 | 시험하지 못함 |
| Chrome 외의 브라우저 (Firefox, Safari) | 시험하지 못함 |

코드는 운영체제에 기대는 부분 없이 파이썬 표준 라이브러리와 numpy, scipy 만 쓰므로 다른 환경에서도 동작할 것으로 예상합니다. 시험하지 못한 환경에서 막히면 터미널에 찍힌 내용을 그대로 남겨 주세요.
