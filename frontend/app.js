const API = "http://127.0.0.1:8000";
const $ = (selector) => document.querySelector(selector);
const projectSelect = $("#project-select");
const artifactList = $("#artifact-list");
const versionList = $("#version-list");
const messageBox = $("#message");
let projects = [];
let artifacts = [];
let selectedArtifactId = null;

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API}${path}`, options);
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`HTTP ${response.status}: ${body}`);
    }
    if (response.status === 204) return null;
    return response.json();
}
function showMessage(message, isError = false) {
    messageBox.textContent = message;
    messageBox.classList.toggle("error", isError);
}
function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
}
function makeButton(label, callback) {
    const button = makeElement("button", "small-button", label);
    button.type = "button";
    button.addEventListener("click", callback);
    return button;
}
function currentProjectId() { return projectSelect.value; }

async function loadProjects(preferredId = null) {
    projects = await apiRequest("/projects/");
    projectSelect.replaceChildren();
    if (projects.length === 0) {
        projectSelect.append(new Option("Nenhum projeto — crie um", ""));
    } else {
        projectSelect.append(new Option("Selecione um projeto", ""));
        for (const project of projects) {
            projectSelect.append(new Option(project.name, String(project.id)));
        }
        const nextId = preferredId ?? currentProjectId();
        if (nextId && projects.some(p => String(p.id) === String(nextId))) {
            projectSelect.value = String(nextId);
        } else {
            projectSelect.value = String(projects[0].id);
        }
    }
    updateProjectStat();
    await loadArtifacts();
}
function updateProjectStat() {
    const project = projects.find(p => String(p.id) === currentProjectId());
    $("#selected-project-stat").textContent = project ? project.name : "Nenhum";
}
async function loadArtifacts() {
    const projectId = currentProjectId();
    artifacts = [];
    selectedArtifactId = null;
    versionList.replaceChildren(makeElement("p", "empty-state", "Selecione “Histórico” em um artefato."));
    $("#history-description").textContent = "Selecione “Histórico” em um artefato para consultar as versões.";
    if (!projectId) {
        artifactList.replaceChildren(makeElement("p", "empty-state", "Crie ou selecione um projeto primeiro."));
        $("#artifact-count").textContent = "0";
        updateProjectStat();
        return;
    }
    artifacts = await apiRequest(`/projects/${projectId}/artifacts/`);
    $("#artifact-count").textContent = String(artifacts.length);
    updateProjectStat();
    artifactList.replaceChildren();
    if (artifacts.length === 0) {
        artifactList.append(makeElement("p", "empty-state", "Nenhum artefato enviado ainda."));
        return;
    }
    for (const artifact of artifacts) {
        const row = makeElement("div", "artifact-row");
        const info = makeElement("div", "file-info");
        const icon = makeElement("div", "file-icon", artifact.artifact_type || "ARQ.");
        const details = makeElement("div");
        details.append(
            makeElement("div", "file-name", artifact.name),
            makeElement("div", "file-meta", `${artifact.artifact_type} · Versão atual ${artifact.version}`)
        );
        info.append(icon, details);
        const actions = makeElement("div", "actions");
        actions.append(
            makeButton("Baixar", () => downloadArtifact(artifact.id)),
            makeButton("Histórico", () => loadVersions(artifact.id)),
            makeButton("Nova versão", () => chooseNewVersion(artifact.id))
        );
        row.append(info, actions);
        artifactList.append(row);
    }
}
async function downloadArtifact(artifactId) {
    const projectId = currentProjectId();
    if (!projectId) return;
    window.location.href = `${API}/projects/${projectId}/artifacts/${artifactId}/download`;
}
async function loadVersions(artifactId) {
    const projectId = currentProjectId();
    selectedArtifactId = artifactId;
    versionList.replaceChildren(makeElement("p", "empty-state", "Carregando histórico…"));
    try {
        const versions = await apiRequest(`/projects/${projectId}/artifacts/${artifactId}/versions`);
        versionList.replaceChildren();
        const artifact = artifacts.find(item => item.id === artifactId);
        $("#history-description").textContent = `Histórico de versões: ${artifact?.name ?? `artefato ${artifactId}`}`;
        if (versions.length === 0) {
            versionList.append(makeElement("p", "empty-state", "Nenhum registro de versão encontrado."));
            return;
        }
        for (const version of versions) {
            const row = makeElement("div", "version-row");
            const info = makeElement("div", "file-info");
            const icon = makeElement("div", "file-icon", `V${version.version_number}`);
            const details = makeElement("div");
            details.append(
                makeElement("div", "file-name", `Versão ${version.version_number}`),
                makeElement("div", "file-meta", `Criada em: ${version.created_at ? new Date(version.created_at).toLocaleString("pt-BR") : "Data indisponível"}`)
            );
            info.append(icon, details);
            row.append(info);
            versionList.append(row);
        }
    } catch (error) {
        showMessage(error.message, true);
        versionList.replaceChildren(makeElement("p", "empty-state", "Não foi possível carregar o histórico."));
    }
}
function chooseNewVersion(artifactId) {
    const projectId = currentProjectId();
    if (!projectId) return;
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".pdf,.md,.markdown,.png,.jpg,.jpeg";
    input.addEventListener("change", async () => {
        const file = input.files?.[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);
        try {
            await apiRequest(`/projects/${projectId}/artifacts/${artifactId}/versions`, {
                method: "POST",
                body: formData
            });
            showMessage("Nova versão enviada com sucesso.");
            await loadArtifacts();
            await loadVersions(artifactId);
        } catch (error) {
            showMessage(error.message, true);
        }
    });
    input.click();
}
$("#project-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = $("#project-name").value.trim();
    const description = $("#project-description").value.trim();
    if (!name) {
        showMessage("Informe o nome do projeto.", true);
        return;
    }
    try {
        const project = await apiRequest("/projects/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, description: description || null})
        });
        $("#project-form").reset();
        await loadProjects(project.id);
        showMessage(`Projeto "${project.name}" criado.`);
    } catch (error) {
        showMessage(error.message, true);
    }
});
$("#upload-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const projectId = currentProjectId();
    const file = $("#artifact-file").files[0];
    if (!projectId) {
        showMessage("Crie ou selecione um projeto primeiro.", true);
        return;
    }
    if (!file) {
        showMessage("Escolha um arquivo para enviar.", true);
        return;
    }
    const formData = new FormData();
    formData.append("file", file);
    try {
        await apiRequest(`/projects/${projectId}/artifacts/`, {
            method: "POST",
            body: formData
        });
        $("#upload-form").reset();
        $("#selected-file-name").textContent = "Nenhum arquivo selecionado";
        await loadArtifacts();
        showMessage(`Arquivo "${file.name}" enviado com sucesso.`);
    } catch (error) {
        showMessage(error.message, true);
    }
});
$("#artifact-file").addEventListener("change", () => {
    const file = $("#artifact-file").files?.[0];
    $("#selected-file-name").textContent = file ? file.name : "Nenhum arquivo selecionado";
});
projectSelect.addEventListener("change", async () => {
    try {
        await loadArtifacts();
        showMessage("");
    } catch (error) {
        showMessage(error.message, true);
    }
});
$("#refresh-artifacts").addEventListener("click", async () => {
    try {
        await loadArtifacts();
        showMessage("Lista de artefatos atualizada.");
    } catch (error) {
        showMessage(error.message, true);
    }
});

const themeToggle = $("#theme-toggle");
themeToggle.addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme !== "dark";
    root.dataset.theme = dark ? "dark" : "light";
    $("#theme-icon").textContent = dark ? "☀" : "☾";
    $("#theme-label").textContent = dark ? "Modo claro" : "Modo escuro";
});

async function initialize() {
    try {
        await apiRequest("/health");
        $("#api-status").textContent = "Online";
        await loadProjects();
        showMessage("Conectado ao Artifact Service.");
    } catch (error) {
        $("#api-status").textContent = "Offline";
        showMessage(`Não foi possível conectar à API. Confira se o FastAPI está rodando. ${error.message}`, true);
    }
}
initialize();
