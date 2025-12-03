(function ($) {
  'use strict';

  // data background
  $('[data-background]').each(function () {
    $(this).css({
      'background-image': 'url(' + $(this).data('background') + ')'
    });
  });

  // collapse
  $('.collapse').on('shown.bs.collapse', function () {
    $(this).parent().find('.ti-plus').removeClass('ti-plus').addClass('ti-minus');
  }).on('hidden.bs.collapse', function () {
    $(this).parent().find('.ti-minus').removeClass('ti-minus').addClass('ti-plus');
  });

  // match height
  $('.match-height').matchHeight({
    byRow: true,
    property: 'height',
    target: null,
    remove: false
  });

  // tooltip
  $('[data-toggle="tooltip"]').tooltip({
    delay: { "show": 0, "hide": 0 },
    animation: false
  });

})(jQuery);

// ===== 로그인 모달 관련 =====

// 0. 백엔드 API 기본 주소
const API_BASE = ""; // 현재 도메인 사용

// 1. 로그인 상태 (localStorage)
const AUTH_KEY = "isLoggedIn";
let isLoggedIn = false;

// localStorage에서 상태 읽기
(function loadAuthState() {
  try {
    const saved = localStorage.getItem(AUTH_KEY);
    isLoggedIn = saved === "true";
  } catch (e) {
    isLoggedIn = false;
  }
})();

// 전역 DOM 참조 (나중에 채움)
let loginModal;
let openLoginBtn;
let closeBtn;
let tabs;
let panels;
let loginForm;
let signupForm;
let messageEl;
let googleBtn;
let kakaoBtn;


// 2. UI에 로그인 상태 반영
function applyAuthStateToUI() {
  // 모든 로그인 버튼(헤더 등)을 찾아서 처리
  const openLoginBtns = document.querySelectorAll(".login-open-btn");
  if (!openLoginBtns.length) return;

  openLoginBtns.forEach(btn => {
    if (isLoggedIn) {
      btn.textContent = "로그아웃";
      btn.classList.add("logged-in");
      if (loginModal) loginModal.classList.add("hidden");
    } else {
      btn.textContent = "Sign in";
      btn.classList.remove("logged-in");
    }
  });
}

function setAuthState(loggedIn) {
  isLoggedIn = loggedIn;
  try {
    localStorage.setItem(AUTH_KEY, loggedIn ? "true" : "false");
  } catch (e) {
    console.warn("localStorage 사용 불가:", e);
  }
  applyAuthStateToUI();
}


// 3. login.html 조각 로드
async function loadLoginFragment() {
  try {
    const res = await fetch("/login_fragment");
    if (!res.ok) {
      console.error("login_fragment 로드 실패:", res.status);
      return;
    }
    const html = await res.text();
    console.log("login_fragment loaded");
    document.body.insertAdjacentHTML("beforeend", html);
  } catch (e) {
    console.error("login_fragment fetch 에러:", e);
  }
}


// 4. 모달/이벤트 초기화
function showPanel(panelId) {
  if (!panels) return;
  panels.forEach((p) => p.classList.remove("active"));
  const target = document.getElementById(panelId);
  if (target) target.classList.add("active");
}

function initLoginUI() {
  console.log("initLoginUI started");
  // 공통 헤더 로그인 버튼 (각 페이지에 있음)
  // querySelectorAll로 변경하여 여러 버튼 대응 가능하게 함
  const openLoginBtns = document.querySelectorAll(".login-open-btn");
  console.log("Found login buttons:", openLoginBtns.length);

  // 방금 insert된 모달 내부 요소들
  loginModal = document.getElementById("login-modal");
  closeBtn = document.querySelector(".auth-close");
  tabs = document.querySelectorAll(".auth-tab"); // 탭은 없지만 혹시 몰라 수정
  panels = document.querySelectorAll(".auth-panel");
  loginForm = document.getElementById("login-form");
  signupForm = document.getElementById("signup-form");
  messageEl = document.getElementById("auth-message");
  naverBtn = document.getElementById("naver-login-btn");
  kakaoBtn = document.getElementById("kakao-login-btn");

  const emailSignupLink = document.getElementById("go-signup-link");
  const backToLoginLink = document.getElementById("back-to-login-link");

  // 현재 저장된 로그인 상태를 버튼/모달에 반영
  applyAuthStateToUI();

  // --- 상단 로그인 / 로그아웃 버튼 ---
  if (openLoginBtns.length > 0) {
    openLoginBtns.forEach(btn => {
      btn.addEventListener("click", (e) => {
        console.log("Login button clicked");
        e.preventDefault(); // 링크 이동 방지

        // 이미 로그인된 상태면 → 로그아웃 처리
        if (btn.classList.contains("logged-in")) {
          setAuthState(false);      // 버튼 '로그인' 으로 변경
          if (messageEl) messageEl.textContent = "";
          return;
        }

        // 로그인 안 된 상태면 → 모달 오픈
        if (loginModal) {
          loginModal.classList.remove("hidden");
          if (messageEl) {
            messageEl.textContent = "";
            messageEl.style.color = "#ef4444";
          }
        }
      });
    });
  }

  // --- 모달 X 버튼 ---
  if (closeBtn && loginModal) {
    closeBtn.addEventListener("click", () => {
      loginModal.classList.add("hidden");
    });
  }

  // --- 배경 클릭 시 모달 닫기 ---
  if (loginModal) {
    loginModal.addEventListener("click", (e) => {
      if (e.target === loginModal) {
        loginModal.classList.add("hidden");
      }
    });
  }

  // --- 탭 전환 (로그인 / 회원가입) ---
  if (tabs && panels) {
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.target;
        tabs.forEach((t) => t.classList.remove("active"));
        panels.forEach((p) => p.classList.remove("active"));

        tab.classList.add("active");
        const panel = document.getElementById(target);
        if (panel) panel.classList.add("active");

        if (messageEl) messageEl.textContent = "";
      });
    });
  }

  // --- "이메일로 회원가입" 클릭 시 회원가입 패널로 전환 ---
  if (emailSignupLink) {
    emailSignupLink.addEventListener("click", () => {
      showPanel("signup-panel");
      if (messageEl) messageEl.textContent = "";
    });
  }

  // --- "로그인 화면으로 돌아가기" 클릭 시 로그인 패널로 전환 ---
  if (backToLoginLink) {
    backToLoginLink.addEventListener("click", () => {
      showPanel("login-panel");
      if (messageEl) messageEl.textContent = "";
    });
  }

  // --- 로그인 폼 submit ---
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (messageEl) {
        messageEl.textContent = "";
        messageEl.style.color = "#ef4444";
      }

      const formData = new FormData(loginForm);
      const payload = {
        email: formData.get("email"),
        password: formData.get("password"),
      };

      try {
        const res = await fetch(`${API_BASE}/api/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (res.ok) {
          if (messageEl) {
            messageEl.style.color = "#16a34a";
            messageEl.textContent = data.message || "로그인 성공";
          }
          setAuthState(true); // 로그인 상태로 전환 + 모달 닫기
          setTimeout(() => {
            if (loginModal) loginModal.classList.add("hidden");
          }, 1000);
        } else {
          if (messageEl) {
            messageEl.style.color = "#ef4444";
            messageEl.textContent =
              data.detail || data.message || "로그인 실패";
          }
        }
      } catch (err) {
        console.error(err);
        if (messageEl) {
          messageEl.style.color = "#ef4444";
          messageEl.textContent = "서버와 통신 중 오류가 발생했습니다.";
        }
      }
    });
  }

  // --- 회원가입 폼 submit ---
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (messageEl) {
        messageEl.textContent = "";
        messageEl.style.color = "#ef4444";
      }

      const formData = new FormData(signupForm);
      const pwd = formData.get("password");
      const pwd2 = formData.get("password_confirm");

      if (pwd !== pwd2) {
        if (messageEl) {
          messageEl.textContent = "비밀번호가 서로 다릅니다.";
        }
        return;
      }

      const payload = {
        email: formData.get("email"),
        password: pwd,
      };

      try {
        const res = await fetch(`${API_BASE}/api/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (res.ok) {
          if (messageEl) {
            messageEl.style.color = "#16a34a";
            messageEl.textContent =
              data.message || "회원가입 성공. 이제 로그인 해 주세요.";
          }
          // 회원가입 성공 시 로그인 패널로 이동
          setTimeout(() => {
            showPanel("login-panel");
            if (messageEl) messageEl.textContent = "회원가입 성공! 로그인 해주세요.";
          }, 1500);
        } else {
          if (messageEl) {
            messageEl.style.color = "#ef4444";
            messageEl.textContent =
              data.detail || data.message || "회원가입 실패";
          }
        }
      } catch (err) {
        console.error(err);
        if (messageEl) {
          messageEl.style.color = "#ef4444";
          messageEl.textContent = "서버와 통신 중 오류가 발생했습니다.";
        }
      }
    });
  }

  // --- 소셜 로그인 (더미) ---
  if (naverBtn) {
    naverBtn.addEventListener("click", () => {
      alert("네이버 로그인 기능은 준비 중입니다.");
    });
  }
  if (kakaoBtn) {
    kakaoBtn.addEventListener("click", () => {
      alert("카카오 로그인 기능은 준비 중입니다.");
    });
  }
}


// 5. 페이지 로드 시 실행
document.addEventListener("DOMContentLoaded", async () => {
  // 1) login.html 조각을 body에 붙이고
  await loadLoginFragment();
  // 2) 그 다음 DOM 요소들을 찾아서 이벤트 연결
  initLoginUI();
});