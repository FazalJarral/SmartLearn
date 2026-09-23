import { spawn, spawnSync } from "node:child_process";
import { copyFileSync, existsSync, readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isWindows = process.platform === "win32";
const checkOnly = process.argv.includes("--check");
const includeWorker = process.argv.includes("--worker");

function log(message = "") {
  process.stdout.write(`${message}\n`);
}

function fail(message) {
  process.stderr.write(`\nLocal startup failed: ${message}\n`);
  process.exit(1);
}

function commandResult(command, args, options = {}) {
  return spawnSync(command, args, {
    cwd: projectRoot,
    encoding: "utf8",
    stdio: options.stdio ?? "pipe",
    ...options,
  });
}

function ensureEnvFile(target, example) {
  if (existsSync(target)) return;
  copyFileSync(example, target);
  log(`Created ${path.relative(projectRoot, target)} from its example file.`);
}

function parseEnv(file) {
  const values = new Map();
  for (const rawLine of readFileSync(file, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const separator = line.indexOf("=");
    if (separator < 1) continue;
    values.set(line.slice(0, separator).trim(), line.slice(separator + 1).trim());
  }
  return values;
}

function isMissing(value) {
  return !value || /replace-me|your-|example/i.test(value);
}

function validateEnvironment() {
  const serverFile = path.join(projectRoot, ".env");
  const webFile = path.join(projectRoot, "apps", "web", ".env.local");
  ensureEnvFile(serverFile, path.join(projectRoot, ".env.example"));
  ensureEnvFile(webFile, path.join(projectRoot, "apps", "web", ".env.example"));

  const server = parseEnv(serverFile);
  const web = parseEnv(webFile);
  const missing = [];

  for (const name of ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]) {
    if (isMissing(server.get(name))) missing.push(`.env: ${name}`);
  }
  if (server.get("GENERATION_PROVIDER")?.toLowerCase() === "deepseek" && isMissing(server.get("DEEPSEEK_API_KEY"))) {
    missing.push(".env: DEEPSEEK_API_KEY");
  }
  for (const name of ["VITE_API_BASE_URL", "VITE_SUPABASE_URL", "VITE_SUPABASE_ANON_KEY"]) {
    if (isMissing(web.get(name))) missing.push(`apps/web/.env.local: ${name}`);
  }
  if (web.has("VITE_SUPABASE_SERVICE_ROLE_KEY")) {
    fail("remove VITE_SUPABASE_SERVICE_ROLE_KEY from apps/web/.env.local; service-role keys must remain server-only.");
  }
  if (missing.length) {
    fail(`configure these values, then rerun npm run dev_test:\n  - ${missing.join("\n  - ")}`);
  }
}

function findPython() {
  const candidates = isWindows
    ? [["py", ["-3.12"]], ["python", []]]
    : [["python3", []], ["python", []]];

  for (const [command, prefix] of candidates) {
    const result = commandResult(command, [...prefix, "--version"]);
    if (result.status !== 0) continue;
    const versionText = `${result.stdout ?? ""}${result.stderr ?? ""}`;
    const match = versionText.match(/Python (\d+)\.(\d+)/);
    if (!match) continue;
    const major = Number(match[1]);
    const minor = Number(match[2]);
    if (major > 3 || (major === 3 && minor >= 12)) {
      return { command, prefix, version: versionText.trim() };
    }
  }
  fail("Python 3.12 or newer was not found. Install Python 3.12 and rerun the command.");
}

function runOrFail(command, args, label) {
  log(`\n${label}...`);
  const result = commandResult(command, args, { stdio: "inherit" });
  if (result.status !== 0) fail(`${label} did not complete successfully.`);
}

validateEnvironment();

const npmCommand = process.env.npm_execpath ? process.execPath : (isWindows ? "npm.cmd" : "npm");
const npmPrefix = process.env.npm_execpath ? [process.env.npm_execpath] : [];
const python = findPython();
const venvDirectory = path.join(projectRoot, ".venv");
const venvPython = isWindows
  ? path.join(venvDirectory, "Scripts", "python.exe")
  : path.join(venvDirectory, "bin", "python");
const needsNodeInstall = !existsSync(path.join(projectRoot, "node_modules"));
const needsVenv = !existsSync(venvPython);
let needsPythonInstall = needsVenv;

if (!needsVenv) {
  const imports = commandResult(venvPython, [
    "-c",
    "import fastapi, uvicorn, manim, fitz, app.main, worker.runner",
  ]);
  needsPythonInstall = imports.status !== 0;
}

if (checkOnly) {
  log("Local configuration is valid.");
  log(`Node dependencies: ${needsNodeInstall ? "installation needed" : "ready"}`);
  log(`Python runtime: ${python.version}`);
  log(`Python environment: ${needsPythonInstall ? "installation needed" : "ready"}`);
  process.exit(0);
}

if (needsNodeInstall) runOrFail(npmCommand, [...npmPrefix, "ci"], "Installing Node dependencies");

if (needsVenv) {
  runOrFail(python.command, [...python.prefix, "-m", "venv", venvDirectory], "Creating Python environment");
}
if (needsPythonInstall) {
  runOrFail(venvPython, ["-m", "pip", "install", "--upgrade", "pip"], "Updating pip");
  runOrFail(
    venvPython,
    ["-m", "pip", "install", "-e", "apps/api[dev]", "-e", "apps/worker[dev]"],
    "Installing Python dependencies",
  );
}

log("\nStarting SmartLearn...");
log("Web:      http://localhost:5173");
log("API docs: http://127.0.0.1:8000/api/v1/docs");
log("Press Ctrl+C to stop everything.\n");

const children = [];
let stopping = false;

function start(command, args) {
  const child = spawn(command, args, { cwd: projectRoot, stdio: "inherit" });
  children.push(child);
  child.on("error", (error) => {
    process.stderr.write(`${error.message}\n`);
    stopAll(1);
  });
  child.on("exit", (code, signal) => {
    if (!stopping) {
      process.stderr.write(`A development process stopped (${signal ?? `exit ${code}`}).\n`);
      stopAll(code ?? 1);
    }
  });
}

function stopChild(child) {
  if (!child.pid || child.exitCode !== null) return;
  if (isWindows) {
    spawnSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
  } else {
    child.kill("SIGTERM");
  }
}

function stopAll(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) stopChild(child);
  process.exit(exitCode);
}

process.on("SIGINT", () => stopAll(0));
process.on("SIGTERM", () => stopAll(0));

start(npmCommand, [...npmPrefix, "run", "dev:web"]);
start(venvPython, ["-m", "uvicorn", "app.main:app", "--app-dir", "apps/api", "--reload"]);
if (includeWorker) start(venvPython, ["-m", "worker.runner"]);
