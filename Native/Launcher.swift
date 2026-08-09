import Foundation

/// Native launcher for SupTools.app (arm64 / x86_64).
/// Locates bundled resources, sets PYTHONPATH (bundle first), and execs system Python.

func die(_ message: String, code: Int32 = 1) -> Never {
    FileHandle.standardError.write(Data("SupTools: \(message)\n".utf8))
    exit(code)
}

let bundle = Bundle.main
guard let resourceURL = bundle.resourceURL else {
    die("missing Resources")
}

let resources = resourceURL.path
let userSite: String = {
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
    task.arguments = ["-c", "import site; print(site.getusersitepackages())"]
    let pipe = Pipe()
    task.standardOutput = pipe
    task.standardError = FileHandle.nullDevice
    do {
        try task.run()
        task.waitUntilExit()
    } catch {
        return ""
    }
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    return String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
}()

// Bundle Resources MUST come first so the app never imports a stale package.
var pythonPathParts = [resources]
if !userSite.isEmpty {
    pythonPathParts.append(userSite)
}
if let existing = ProcessInfo.processInfo.environment["PYTHONPATH"], !existing.isEmpty {
    pythonPathParts.append(existing)
}
let pythonPath = pythonPathParts.joined(separator: ":")

var env = ProcessInfo.processInfo.environment
env["PYTHONPATH"] = pythonPath
env["PYTHONUNBUFFERED"] = "1"
env["SUPTOOLS_APP_BUNDLE"] = bundle.bundlePath
env["SYSPULSE_APP_BUNDLE"] = bundle.bundlePath // legacy env alias
env["SYSTEMMONIT_APP_BUNDLE"] = bundle.bundlePath // legacy env alias
env["TK_SILENCE_DEPRECATION"] = "1"

let logDir = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Logs")
try? FileManager.default.createDirectory(atPath: logDir, withIntermediateDirectories: true)
let errLog = (logDir as NSString).appendingPathComponent("SupTools-stderr.log")
FileManager.default.createFile(atPath: errLog, contents: nil)
let errHandle = FileHandle(forWritingAtPath: errLog) ?? FileHandle.standardError

// Prefer system Python (universal). Then Homebrew paths for each chip.
let pythonCandidates = [
    "/usr/bin/python3",
    "/Library/Developer/CommandLineTools/usr/bin/python3",
    "/opt/homebrew/bin/python3",      // Apple Silicon Homebrew
    "/usr/local/bin/python3",         // Intel Homebrew
]

guard let python = pythonCandidates.first(where: { FileManager.default.isExecutableFile(atPath: $0) }) else {
    die("未找到 python3。请安装「命令行工具」或 Homebrew Python 后重试。")
}

let task = Process()
task.executableURL = URL(fileURLWithPath: python)
task.arguments = ["-m", "systemmonit_launcher"]
task.environment = env
task.currentDirectoryURL = resourceURL
task.standardInput = FileHandle.standardInput
task.standardOutput = FileHandle.standardOutput
task.standardError = errHandle

do {
    try task.run()
    task.waitUntilExit()
    exit(task.terminationStatus)
} catch {
    die("failed to start: \(error)")
}
