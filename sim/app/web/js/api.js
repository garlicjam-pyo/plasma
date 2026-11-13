// 백엔드(server.py)와 주고받는 부분. 화면 코드는 여기 함수만 부른다.

async function request(path, body) {
  const options = body === undefined
    ? { method: "GET" }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  let response;
  try {
    response = await fetch(path, options);
  } catch (err) {
    throw new Error("서버에 연결할 수 없습니다. 터미널에서 python sim/app/server.py 가 실행 중인지 확인하세요.");
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "요청을 처리하지 못했습니다.");
  return data;
}

export const api = {
  meta: () => request("/api/meta"),                      // 조절 범위, 기본값, 챔버 형상
  simulate: (inputs) => request("/api/simulate", inputs), // 직접 조정: 입력 그대로 계산
  control: (inputs) => request("/api/control", inputs),   // 목표로 맞추기: 목표를 만드는 입력 찾기
  reachable: (inputs) => request("/api/reachable", inputs), // 도달 가능 영역
  jacobian: (inputs) => request("/api/jacobian", inputs),   // 제어 민감도 행렬
};
