(() => {
  "use strict";

  const TOKEN_KEY = "ruang_session_token";
  const authView = document.querySelector("#auth-view");
  const dashboardView = document.querySelector("#dashboard-view");
  const loginPanel = document.querySelector("#login-panel");
  const registerPanel = document.querySelector("#register-panel");
  const loginForm = document.querySelector("#login-form");
  const registerForm = document.querySelector("#register-form");
  const loginMessage = document.querySelector("#login-message");
  const registerMessage = document.querySelector("#register-message");
  const stepSections = [...document.querySelectorAll(".register-step")];
  const fileInputs = [...document.querySelectorAll(".upload-card input[type=file]")];
  let currentStep = 1;
  let toastTimeout;

  const documentLabels = {
    ktp: "Kartu Tanda Penduduk",
    supporting_doc: "Dokumen pendukung",
    selfie_video: "Video selfie",
  };

  async function request(path, options = {}) {
    const token = sessionStorage.getItem(TOKEN_KEY);
    const headers = new Headers(options.headers || {});
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(path, { ...options, headers });
    const contentType = response.headers.get("content-type") || "";
    const body = contentType.includes("application/json") ? await response.json() : null;
    if (!response.ok) {
      if (response.status === 401 && token) clearSession();
      const message = response.status === 413
        ? "Total ukuran unggahan melebihi batas 60 MB."
        : body?.error || "Tidak dapat menghubungi layanan. Coba lagi.";
      const error = new Error(message);
      error.status = response.status;
      error.fields = body?.fields || {};
      throw error;
    }
    return { response, body };
  }

  function setMessage(element, text = "", type = "error") {
    element.textContent = text;
    element.classList.toggle("success", type === "success");
    element.classList.toggle("visible", Boolean(text));
  }

  function setBusy(button, busy, busyText = "Memproses...") {
    if (busy) {
      button.dataset.originalText = button.querySelector("span")?.textContent || button.textContent;
      button.disabled = true;
      const label = button.querySelector("span");
      if (label) label.textContent = busyText;
    } else {
      button.disabled = false;
      const label = button.querySelector("span");
      if (label && button.dataset.originalText) label.textContent = button.dataset.originalText;
    }
  }

  function showAuth(mode) {
    authView.classList.remove("hidden");
    dashboardView.classList.add("hidden");
    document.querySelector("#top-navigation").classList.remove("hidden");
    document.querySelector("#register-cta").classList.remove("hidden");
    document.querySelector("#logout-button").classList.add("hidden");
    const isRegister = mode === "register";
    loginPanel.classList.toggle("hidden", isRegister);
    registerPanel.classList.toggle("hidden", !isRegister);
    document.querySelector("#login-tab").classList.toggle("active", !isRegister);
    document.querySelector("#register-tab").classList.toggle("active", isRegister);
    document.querySelector("#login-tab").setAttribute("aria-selected", String(!isRegister));
    document.querySelector("#register-tab").setAttribute("aria-selected", String(isRegister));
    if (isRegister) renderStep(1);
  }

  function renderStep(step) {
    currentStep = step;
    stepSections.forEach((section) => section.classList.toggle("hidden", Number(section.dataset.step) !== step));
    document.querySelector("#step-caption").innerHTML = `LANGKAH 0${step} <span class="caption-muted">/ 03</span>`;
    document.querySelector("#step-name").textContent = ["Data diri", "Dokumen", "Keamanan"][step - 1];
    document.querySelector("#progress-fill").style.width = `${(step / 3) * 100}%`;
    document.querySelectorAll("[data-step-label]").forEach((label) => {
      const labelStep = Number(label.dataset.stepLabel);
      label.classList.toggle("current", labelStep === step);
      label.classList.toggle("completed", labelStep < step);
    });
    document.querySelector("#back-button").classList.toggle("hidden", step === 1);
    document.querySelector("#next-button").classList.toggle("hidden", step === 3);
    document.querySelector("#submit-register").classList.toggle("hidden", step !== 3);
    setMessage(registerMessage);
  }

  function validateStep(step) {
    const section = stepSections[step - 1];
    const inputs = [...section.querySelectorAll("input, textarea")];
    for (const input of inputs) {
      if (!input.checkValidity()) {
        input.reportValidity();
        return false;
      }
    }
    if (step === 1) {
      const dob = new Date(`${document.querySelector("#date_of_birth").value}T00:00:00`);
      const today = new Date();
      const age = today.getFullYear() - dob.getFullYear() - (
        today.getMonth() < dob.getMonth() ||
        (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate()) ? 1 : 0
      );
      if (!Number.isFinite(dob.getTime()) || age < 17) {
        const field = document.querySelector("#date_of_birth");
        field.setCustomValidity("Usia minimal 17 tahun.");
        field.reportValidity();
        field.setCustomValidity("");
        return false;
      }
    }
    return true;
  }

  function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    loginForm.elements.password.value = "";
    showAuth("login");
  }

  function formatRupiah(amount) {
    return new Intl.NumberFormat("id-ID").format(amount);
  }

  function formatDate(value) {
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? "—" : new Intl.DateTimeFormat("id-ID", {
      day: "numeric", month: "long", year: "numeric",
    }).format(date);
  }

  function showToast(message, isError = false) {
    const toast = document.querySelector("#toast");
    toast.textContent = message;
    toast.classList.toggle("toast-error", isError);
    toast.classList.add("visible");
    window.clearTimeout(toastTimeout);
    toastTimeout = window.setTimeout(() => toast.classList.remove("visible"), 2800);
  }

  function renderDocuments(documents) {
    const list = document.querySelector("#document-list");
    list.replaceChildren();
    document.querySelector("#document-count").textContent = `${documents.length} dokumen`;
    if (!documents.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Belum ada dokumen yang tersimpan.";
      list.append(empty);
      return;
    }
    documents.forEach((documentInfo) => {
      const item = document.createElement("article");
      item.className = "document-row";
      const info = document.createElement("div");
      info.className = "document-info";
      const icon = document.createElement("span");
      icon.className = `document-icon document-${documentInfo.kind}`;
      icon.textContent = documentInfo.kind === "selfie_video" ? "VID" : documentInfo.kind === "ktp" ? "ID" : "DOC";
      const detail = document.createElement("div");
      detail.className = "document-detail";
      const title = document.createElement("strong");
      title.textContent = documentLabels[documentInfo.kind] || "Dokumen";
      const metadata = document.createElement("span");
      metadata.textContent = `${documentInfo.download_name} · ${formatBytes(documentInfo.size)}`;
      detail.append(title, metadata);
      info.append(icon, detail);
      const download = document.createElement("button");
      download.className = "download-button";
      download.type = "button";
      download.innerHTML = '<span>Unduh</span><span aria-hidden="true">↓</span>';
      download.addEventListener("click", () => downloadDocument(documentInfo, download));
      item.append(info, download);
      list.append(item);
    });
  }

  function formatBytes(size) {
    if (!Number.isFinite(size) || size <= 0) return "0 KB";
    return size < 1024 * 1024
      ? `${Math.max(1, Math.round(size / 1024))} KB`
      : `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function downloadDocument(documentInfo, button) {
    button.disabled = true;
    try {
      const { response } = await request(`/api/me/documents/${encodeURIComponent(documentInfo.kind)}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = documentInfo.download_name;
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      showToast("Dokumen berhasil diunduh dan diverifikasi.");
    } catch (error) {
      showToast(error.message, true);
    } finally {
      button.disabled = false;
    }
  }

  async function loadDashboard() {
    const { body } = await request("/api/me");
    const profile = body.profile;
    document.querySelector("#customer-name").textContent = profile.full_name.split(" ")[0];
    document.querySelector("#profile-name").textContent = profile.full_name;
    document.querySelector("#profile-email").textContent = profile.email;
    document.querySelector("#profile-phone").textContent = profile.phone;
    document.querySelector("#profile-dob").textContent = formatDate(profile.date_of_birth);
    document.querySelector("#profile-address").textContent = profile.address;
    document.querySelector("#profile-nik").textContent = `••••••••••••${profile.nik.slice(-4)}`;
    document.querySelector("#account-number").textContent = body.account.number.replace(/(\d{4})(?=\d)/g, "$1 ");
    document.querySelector("#account-balance").textContent = formatRupiah(body.account.balance);
    document.querySelector("#today-date").textContent = new Intl.DateTimeFormat("id-ID", {
      weekday: "long", day: "numeric", month: "long",
    }).format(new Date());
    renderDocuments(body.documents || []);
    authView.classList.add("hidden");
    dashboardView.classList.remove("hidden");
    document.querySelector("#top-navigation").classList.add("hidden");
    document.querySelector("#register-cta").classList.add("hidden");
    document.querySelector("#logout-button").classList.remove("hidden");
  }

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(loginMessage);
    if (!loginForm.reportValidity()) return;
    const button = loginForm.querySelector('button[type="submit"]');
    setBusy(button, true);
    try {
      const { body } = await request("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: loginForm.elements.email.value.trim(),
          password: loginForm.elements.password.value,
        }),
      });
      sessionStorage.setItem(TOKEN_KEY, body.token);
      loginForm.reset();
      await loadDashboard();
    } catch (error) {
      setMessage(loginMessage, error.message);
    } finally {
      setBusy(button, false);
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(registerMessage);
    if (currentStep !== 3 || !validateStep(3)) return;
    const button = document.querySelector("#submit-register");
    setBusy(button, true, "Mendaftarkan...");
    try {
      const registeredEmail = registerForm.elements.email.value.trim();
      const { body } = await request("/api/register", {
        method: "POST",
        body: new FormData(registerForm),
      });
      registerForm.reset();
      fileInputs.forEach((input) => {
        document.querySelector(`[data-file-name="${input.name}"]`).textContent = ({
          ktp: "Pilih file KTP",
          supporting_doc: "Pilih dokumen",
          selfie_video: "Pilih video selfie",
        })[input.name];
      });
      renderStep(1);
      showAuth("login");
      loginForm.elements.email.value = registeredEmail;
      loginForm.elements.password.value = "";
      setMessage(loginMessage, `${body.message}. Nomor rekening: ${body.account_number}`, "success");
      loginPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      if (Object.keys(error.fields || {}).length) {
        const [fieldName, message] = Object.entries(error.fields)[0];
        setMessage(registerMessage, `${message}${Object.keys(error.fields).length > 1 ? ` (${Object.keys(error.fields).length} masalah ditemukan)` : ""}`);
        if (stepForField(fieldName) !== currentStep) renderStep(stepForField(fieldName));
      } else {
        setMessage(registerMessage, error.message);
      }
    } finally {
      setBusy(button, false);
    }
  });

  function stepForField(name) {
    if (["ktp", "supporting_doc", "selfie_video"].includes(name)) return 2;
    if (["password", "consent_pdp"].includes(name)) return 3;
    return 1;
  }

  document.querySelector("#next-button").addEventListener("click", () => {
    if (validateStep(currentStep)) renderStep(currentStep + 1);
  });
  document.querySelector("#back-button").addEventListener("click", () => renderStep(currentStep - 1));
  document.querySelector("#login-tab").addEventListener("click", () => showAuth("login"));
  document.querySelector("#register-tab").addEventListener("click", () => showAuth("register"));
  document.querySelectorAll("[data-show-register]:not(#register-cta)").forEach((button) => {
    button.addEventListener("click", () => showAuth("register"));
  });
  document.querySelector("#register-cta").addEventListener("click", () => {
    showAuth("register");
    window.requestAnimationFrame(() => {
      registerPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  document.querySelectorAll("[data-show-login]").forEach((button) => button.addEventListener("click", () => showAuth("login")));
  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.togglePassword);
      const visible = input.type === "password";
      input.type = visible ? "text" : "password";
      button.textContent = visible ? "Sembunyi" : "Lihat";
      button.setAttribute("aria-label", visible ? "Sembunyikan kata sandi" : "Tampilkan kata sandi");
    });
  });
  fileInputs.forEach((input) => input.addEventListener("change", () => {
    const label = document.querySelector(`[data-file-name="${input.name}"]`);
    label.textContent = input.files[0]?.name || ({
      ktp: "Pilih file KTP",
      supporting_doc: "Pilih dokumen",
      selfie_video: "Pilih video selfie",
    })[input.name];
    label.classList.toggle("selected", Boolean(input.files[0]));
  }));
  document.querySelector("#copy-account").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(document.querySelector("#account-number").textContent.replace(/\s/g, ""));
      showToast("Nomor rekening disalin.");
    } catch {
      showToast("Nomor rekening tidak dapat disalin di browser ini.", true);
    }
  });
  document.querySelector("#logout-button").addEventListener("click", async () => {
    try {
      await request("/api/logout", { method: "POST" });
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showToast("Sesi sudah berakhir.");
      } else {
        showToast(error.message, true);
      }
      return;
    }
    clearSession();
    showToast("Kamu berhasil keluar.");
  });

  if (sessionStorage.getItem(TOKEN_KEY)) {
    loadDashboard().catch((error) => {
      clearSession();
      if (error.status !== 401) setMessage(loginMessage, error.message);
    });
  }
})();
