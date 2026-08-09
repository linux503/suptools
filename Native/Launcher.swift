import Foundation
import CoreGraphics
import Darwin

/// Native launcher for SupTools.app (arm64 / x86_64).
///
/// Default: locate bundled resources and spawn system Python for the UI.
/// Extra modes (same binary = com.suptools.app TCC identity):
///   --preflight-screen
///   --request-screen
///   --screencapture <screencapture args...>

func die(_ message: String, code: Int32 = 1) -> Never {
    FileHandle.standardError.write(Data("SupTools: \(message)\n".utf8))
    exit(code)
}

func writeOut(_ s: String) {
    FileHandle.standardOutput.write(Data((s + "\n").utf8))
}

let args = CommandLine.arguments

if args.contains("--preflight-screen") {
    writeOut(CGPreflightScreenCaptureAccess() ? "1" : "0")
    exit(0)
}

if args.contains("--request-screen") {
    let ok = CGRequestScreenCaptureAccess()
    writeOut(ok ? "1" : "0")
    RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.6))
    exit(0)
}

if let idx = args.firstIndex(of: "--screencapture") {
    let forwarded = Array(args.suffix(from: idx + 1))
    if forwarded.isEmpty {
        die("missing screencapture arguments", code: 2)
    }
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
    task.arguments = forwarded
    task.standardInput = FileHandle.standardInput
    task.standardOutput = FileHandle.standardOutput
    task.standardError = FileHandle.standardError

    // Let DispatchSource deliver SIGINT/SIGTERM so we can stop child recordings.
    signal(SIGINT, SIG_IGN)
    signal(SIGTERM, SIG_IGN)
    let sigInt = DispatchSource.makeSignalSource(signal: SIGINT, queue: .global())
    let sigTerm = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .global())
    let stopChild = {
        if task.isRunning {
            task.interrupt()
            DispatchQueue.global().asyncAfter(deadline: .now() + 1.5) {
                if task.isRunning { task.terminate() }
            }
        }
    }
    sigInt.setEventHandler(handler: stopChild)
    sigTerm.setEventHandler(handler: stopChild)
    sigInt.resume()
    sigTerm.resume()

    do {
        try task.run()
        task.waitUntilExit()
        sigInt.cancel()
        sigTerm.cancel()
        exit(task.terminationStatus)
    } catch {
        die("screencapture failed: \(error)")
    }
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

var pythonPathParts = [resources]
if !userSite.isEmpty {
    pythonPathParts.append(userSite)
}
if let existing = ProcessInfo.processInfo.environment["PYTHONPATH"], !existing.isEmpty {
    pythonPathParts.append(existing)
}

var env = ProcessInfo.processInfo.environment
env["PYTHONPATH"] = pythonPathParts.joined(separator: ":")
env["PYTHONUNBUFFERED"] = "1"
env["SUPTOOLS_APP_BUNDLE"] = bundle.bundlePath
env["SYSPULSE_APP_BUNDLE"] = bundle.bundlePath
env["SYSTEMMONIT_APP_BUNDLE"] = bundle.bundlePath
env["TK_SILENCE_DEPRECATION"] = "1"

let logDir = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Logs")
try? FileManager.default.createDirectory(atPath: logDir, withIntermediateDirectories: true)
let errLog = (logDir as NSString).appendingPathComponent("SupTools-stderr.log")
FileManager.default.createFile(atPath: errLog, contents: nil)
let errHandle = FileHandle(forWritingAtPath: errLog) ?? FileHandle.standardError

let pythonCandidates = [
    "/usr/bin/python3",
    "/Library/Developer/CommandLineTools/usr/bin/python3",
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3",
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
