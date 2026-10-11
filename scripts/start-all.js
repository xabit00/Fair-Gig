const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const env = { ...process.env, ...readEnv(path.join(root, ".env")) };
const npm = process.platform === "win32" ? "npm.cmd" : "npm";

function readEnv(file) {
  if (!fs.existsSync(file)) return {};
  return Object.fromEntries(
    fs.readFileSync(file, "utf8")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        return [line.slice(0, separator), line.slice(separator + 1).replace(/^['"]|['"]$/g, "")];
      }),
  );
}

function pythonFor(service) {
  const executable = process.platform === "win32"
    ? path.join(root, service, ".venv", "Scripts", "python.exe")
    : path.join(root, service, ".venv", "bin", "python");
  return fs.existsSync(executable) ? executable : "python";
}

const definitions = [
  ["auth", "auth-service", pythonFor("auth-service"), ["-m", "uvicorn", "app.main:app", "--reload", "--port", "8001"]],
  ["earnings", "earnings-service", pythonFor("earnings-service"), ["-m", "uvicorn", "app.main:app", "--reload", "--port", "8002"]],
  ["anomaly", "anomaly-service", pythonFor("anomaly-service"), ["-m", "uvicorn", "app.main:app", "--reload", "--port", "8003"]],
  ["grievance", "grievance-service", npm, ["start"]],
  ["analytics", "analytics-service", pythonFor("analytics-service"), ["-m", "uvicorn", "app.main:app", "--reload", "--port", "8005"]],
  ["certificate", "certificate-service", npm, ["start"]],
  ["frontend", "frontend", npm, ["run", "dev"]],
];

const children = definitions.map(([name, directory, command, args]) => {
  const child = spawn(command, args, {
    cwd: path.join(root, directory),
    env,
    stdio: "inherit",
    shell: false,
  });
  child.on("error", (error) => console.error(`[${name}] ${error.message}`));
  child.on("exit", (code) => {
    if (code && code !== 0) console.error(`[${name}] exited with code ${code}`);
  });
  return child;
});

function stop() {
  for (const child of children) {
    if (!child.killed) child.kill("SIGTERM");
  }
  setTimeout(() => process.exit(0), 500);
}

process.on("SIGINT", stop);
process.on("SIGTERM", stop);

